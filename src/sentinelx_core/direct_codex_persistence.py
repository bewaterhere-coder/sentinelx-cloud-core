"""Provider-owned deterministic persistence & canonical publish closure.

PR-015/S04 adds the missing persistence owner for the direct/Codex bridge. The
installed Codex Development Host performs bounded edits inside the isolated
checkout but does not create a Git commit (Acceptance R1's real-host finding), so
the bounded ``devforge_direct_codex`` provider owns deterministic local
persistence and ordinary canonical publication of the exact checkout changes.

Boundary rules enforced here:

- the Codex-owned Git index is never candidate authority: the candidate is built
  from a provider-owned temporary index seeded from the exact admitted parent;
- no caller Git argv, pathspec, commit message, author, timestamp, remote URL or
  branch is accepted; every commit-SHA input is frozen in a provider-owned
  recovery journal before the candidate object exists;
- publication is an ordinary fast-forward push to the exact canonical branch and
  force/force-with-lease are never used;
- after any uncertain externally visible push the provider performs readback only
  and never issues a hidden automatic second push;
- provider control/evidence artifacts are excluded from the implementation
  commit and every path is validated as a clean repository-relative path.

The persistence role does not change execution identity: the receipt still
reports ``provider: direct`` / ``adapter: codex`` / ``host: Codex`` with
SentinelX as the bounded transport/persistence broker.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sentinelx_core.direct_codex_transport import (
    CanonicalizationSnapshot,
    DirectCodexTransportError,
    ProviderState,
    TransportBootstrap,
    ensure_provider_state,
    materialization_clamps,
    materialization_env,
    read_persisted_snapshot,
    read_remote_head,
    revalidate_canonicalization,
    transport_git,
    validate_relative_path,
)
from sentinelx_core.direct_codex_workspace import DirectCodexWorkspace
from sentinelx_core.mutation_placement import RepositoryIdentity, SemanticIdentity

PERSISTENCE_VERSION = 1
SERIALIZATION_VERSION = 1
PERSISTENCE_MODE = "provider_owned_commit_on_publish"

FIXED_IDENT_NAME = "SentinelX Direct Codex"
FIXED_IDENT_EMAIL = "direct-codex@sentinelx.invalid"
TIMEZONE = "+0000"

STATE_PREPARED = "prepared"
STATE_TREE_READY = "tree_ready"
STATE_CANDIDATE_READY = "candidate_ready"
STATE_LOCAL_REF_READY = "local_ref_ready"
STATE_PUBLISH_INTENT = "publish_intent"
STATE_PUBLISHED = "published"

# Provider-owned artifacts that must never enter the implementation commit. They
# live under the derived checkout because the handoff is written there for audit.
PROVIDER_OWNED_TOP_LEVEL = frozenset({".devforge", ".devforge-state"})
GITATTRIBUTES_NAME = ".gitattributes"
MAX_STAGE_PATHS_PER_CALL = 128
_ALLOWED_MODES = frozenset({"100644", "100755", "120000"})
_GITLINK_MODE = "160000"
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class DirectCodexPersistenceError(DirectCodexTransportError):
    """Fail-closed error for provider-owned persistence/publication."""


@dataclass(frozen=True)
class PersistenceOutcome:
    """Bounded persistence evidence carried into the direct/Codex receipt."""

    mode: str
    status: str
    base_head: str
    eligible_change_count: int
    changed_paths_digest: str
    candidate_commit: str | None
    commit_provenance_digest: str | None
    published: bool
    remote_head_readback: str
    consistent: bool
    actual_branch: str
    local_head: str
    snapshot_digest: str | None = None
    state: str | None = None
    error_code: str | None = None
    detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "status": self.status,
            "base_head": self.base_head,
            "eligible_change_count": self.eligible_change_count,
            "changed_paths_digest": self.changed_paths_digest,
            "candidate_commit": self.candidate_commit,
            "commit_provenance_digest": self.commit_provenance_digest,
            "published": self.published,
            "remote_head_readback": self.remote_head_readback,
            "consistent": self.consistent,
            "actual_branch": self.actual_branch,
            "local_head": self.local_head,
            "snapshot_digest": self.snapshot_digest,
            "state": self.state,
            "error_code": self.error_code,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class CommitIdentity:
    author_name: str
    author_email: str
    committer_name: str
    committer_email: str
    author_date_utc_seconds: int
    committer_date_utc_seconds: int
    timezone: str
    message_digest: str
    serialization_version: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "author_name": self.author_name,
            "author_email": self.author_email,
            "committer_name": self.committer_name,
            "committer_email": self.committer_email,
            "author_date_utc_seconds": self.author_date_utc_seconds,
            "committer_date_utc_seconds": self.committer_date_utc_seconds,
            "timezone": self.timezone,
            "message_digest": self.message_digest,
            "serialization_version": self.serialization_version,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> CommitIdentity:
        return cls(
            author_name=str(payload["author_name"]),
            author_email=str(payload["author_email"]),
            committer_name=str(payload["committer_name"]),
            committer_email=str(payload["committer_email"]),
            author_date_utc_seconds=int(payload["author_date_utc_seconds"]),
            committer_date_utc_seconds=int(payload["committer_date_utc_seconds"]),
            timezone=str(payload["timezone"]),
            message_digest=str(payload["message_digest"]),
            serialization_version=int(payload["serialization_version"]),
        )

    def git_env(self) -> dict[str, str]:
        return {
            "GIT_AUTHOR_NAME": self.author_name,
            "GIT_AUTHOR_EMAIL": self.author_email,
            "GIT_COMMITTER_NAME": self.committer_name,
            "GIT_COMMITTER_EMAIL": self.committer_email,
            "GIT_AUTHOR_DATE": f"{self.author_date_utc_seconds} {self.timezone}",
            "GIT_COMMITTER_DATE": f"{self.committer_date_utc_seconds} {self.timezone}",
        }


@dataclass
class PersistenceJournal:
    """Provider-owned recovery journal, stored outside the candidate set."""

    identity: dict[str, Any]
    transport: dict[str, Any]
    clean_semantics: dict[str, Any]
    commit_identity: CommitIdentity
    message: str
    state: str = STATE_PREPARED
    candidate_tree_sha: str | None = None
    eligible_paths_digest: str | None = None
    eligible_change_count: int | None = None
    candidate_commit_sha: str | None = None
    version: int = PERSISTENCE_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "state": self.state,
            "identity": dict(self.identity),
            "transport": dict(self.transport),
            "clean_semantics": dict(self.clean_semantics),
            "commit_identity": self.commit_identity.to_dict(),
            "message": self.message,
            "candidate_tree_sha": self.candidate_tree_sha,
            "eligible_paths_digest": self.eligible_paths_digest,
            "eligible_change_count": self.eligible_change_count,
            "candidate_commit_sha": self.candidate_commit_sha,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> PersistenceJournal:
        return cls(
            identity=dict(payload["identity"]),
            transport=dict(payload["transport"]),
            clean_semantics=dict(payload["clean_semantics"]),
            commit_identity=CommitIdentity.from_dict(payload["commit_identity"]),
            message=str(payload["message"]),
            state=str(payload["state"]),
            candidate_tree_sha=payload.get("candidate_tree_sha"),
            eligible_paths_digest=payload.get("eligible_paths_digest"),
            eligible_change_count=payload.get("eligible_change_count"),
            candidate_commit_sha=payload.get("candidate_commit_sha"),
            version=int(payload.get("version", PERSISTENCE_VERSION)),
        )


@dataclass(frozen=True)
class WorktreeDelta:
    modified: tuple[str, ...]
    deleted: tuple[str, ...]
    added: tuple[str, ...]
    digest: str

    @property
    def paths(self) -> tuple[str, ...]:
        return tuple(sorted(set(self.modified) | set(self.deleted) | set(self.added)))

    @property
    def count(self) -> int:
        return len(self.paths)


def _decode(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def _digest_lines(lines: Sequence[str]) -> str:
    body = "\n".join(sorted(lines))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _provider_owned(path: str) -> bool:
    top = path.split("/", 1)[0]
    return top in PROVIDER_OWNED_TOP_LEVEL


def reject_unsupported_mode(path: str, old_mode: str, new_mode: str, status: str) -> None:
    """Fail closed on gitlink/submodule mutation or an unsupported mode change."""
    if _GITLINK_MODE in (old_mode, new_mode):
        raise DirectCodexPersistenceError(
            "direct_codex_unsupported_gitlink_mutation",
            f"gitlink/submodule mutation is not supported: {path!r}",
        )
    if (
        status[:1] == "T"
        or (old_mode not in _ALLOWED_MODES and old_mode != "000000")
        or (new_mode not in _ALLOWED_MODES and new_mode != "000000")
    ):
        raise DirectCodexPersistenceError(
            "direct_codex_unsupported_mode_change",
            f"unsupported path mode change for {path!r}: {old_mode}->{new_mode}",
        )


def commit_message(
    *, task_id: str, run_id: str, attempt_id: str, slice_id: str | None
) -> str:
    """Deterministic provider-owned commit message carrying exact lineage."""
    lines = [
        "SentinelX direct/Codex provider-owned implementation persistence",
        "",
        f"task_id: {task_id}",
        f"run_id: {run_id}",
        f"attempt_id: {attempt_id}",
        f"slice_id: {slice_id or ''}",
        "",
        "provider: direct",
        "adapter: codex",
    ]
    return "\n".join(lines) + "\n"


def _read_journal(state: ProviderState) -> PersistenceJournal | None:
    if not state.journal.is_file():
        return None
    try:
        payload = json.loads(state.journal.read_text(encoding="utf-8"))
        return PersistenceJournal.from_dict(payload)
    except (OSError, ValueError, KeyError, TypeError):
        raise DirectCodexPersistenceError(
            "direct_codex_recovery_journal_invalid",
            "the provider recovery journal is unreadable or malformed",
        ) from None


def _write_journal(state: ProviderState, journal: PersistenceJournal) -> PersistenceJournal:
    tmp = state.journal.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(journal.to_dict(), sort_keys=True), encoding="utf-8")
    tmp.replace(state.journal)
    readback = _read_journal(state)
    if readback is None or readback.to_dict() != journal.to_dict():
        raise DirectCodexPersistenceError(
            "direct_codex_recovery_journal_readback_mismatch",
            "the provider recovery journal did not read back identically",
        )
    return readback


async def _rev_parse(cwd: Path, revision: str, budget: float) -> str:
    code, stdout, _stderr = await transport_git(cwd, "rev-parse", revision, timeout=budget)
    if code != 0:
        raise DirectCodexPersistenceError(
            "direct_codex_revision_unavailable", f"cannot resolve {revision} in the checkout"
        )
    return _decode(stdout).strip()


async def _inventory(cwd: Path, expected_sha: str, budget: float) -> WorktreeDelta:
    """Derive the eligible worktree delta from the checkout, not the index.

    ``diff-index <expected_sha>`` compares the *worktree* with the admitted parent
    tree, so a Codex-staged-but-unwritten index entry can never become an
    eligible change; untracked files are enumerated separately with the standard
    ignore rules.
    """
    code, stdout, _stderr = await transport_git(
        cwd,
        "--literal-pathspecs",
        "ls-files",
        "-u",
        "-z",
        "--",
        timeout=budget,
    )
    if code != 0:
        raise DirectCodexPersistenceError(
            "direct_codex_inventory_failed", "cannot inspect the checkout index state"
        )
    if _decode(stdout).strip("\0").strip():
        raise DirectCodexPersistenceError(
            "direct_codex_unmerged_state", "the checkout index contains unmerged entries"
        )

    code, stdout, stderr = await transport_git(
        cwd,
        "--literal-pathspecs",
        "diff-index",
        "--raw",
        "-z",
        "--no-renames",
        expected_sha,
        "--",
        timeout=budget,
    )
    if code != 0:
        raise DirectCodexPersistenceError(
            "direct_codex_inventory_failed",
            f"cannot diff the worktree against the admitted parent: {_decode(stderr).strip()[:200]}",
        )
    tokens = _decode(stdout).split("\0")
    modified: list[str] = []
    deleted: list[str] = []
    index = 0
    while index + 1 < len(tokens):
        header, path = tokens[index], tokens[index + 1]
        index += 2
        if not header.startswith(":"):
            continue
        fields = header[1:].split()
        if len(fields) < 5:
            continue
        old_mode, new_mode, _old_sha, _new_sha, status = fields[:5]
        reject_unsupported_mode(path, old_mode, new_mode, status)
        if status[0] == "D":
            deleted.append(path)
        else:
            modified.append(path)

    code, stdout, _stderr = await transport_git(
        cwd,
        "--literal-pathspecs",
        "ls-files",
        "--others",
        "--exclude-standard",
        "-z",
        "--",
        timeout=budget,
    )
    if code != 0:
        raise DirectCodexPersistenceError(
            "direct_codex_inventory_failed", "cannot enumerate untracked checkout files"
        )
    added = [path for path in _decode(stdout).split("\0") if path]

    def _eligible(paths: list[str]) -> list[str]:
        kept: list[str] = []
        for path in paths:
            validate_relative_path(path)
            if _provider_owned(path):
                # Provider control/evidence artifacts (for example the written
                # handoff) are never part of the implementation commit.
                continue
            if path.split("/")[-1] == GITATTRIBUTES_NAME:
                raise DirectCodexPersistenceError(
                    "direct_codex_unsupported_attribute_mutation",
                    "a versioned .gitattributes change is not supported by V1 persistence",
                )
            kept.append(path)
        return sorted(set(kept))

    eligible_modified = _eligible(modified)
    eligible_deleted = _eligible(deleted)
    eligible_added = _eligible(added)
    unique = sorted(set(eligible_modified) | set(eligible_deleted) | set(eligible_added))
    return WorktreeDelta(
        modified=tuple(eligible_modified),
        deleted=tuple(eligible_deleted),
        added=tuple(eligible_added),
        digest=_digest_lines(unique),
    )


async def _write_tree(
    cwd: Path,
    expected_sha: str,
    delta: WorktreeDelta,
    state: ProviderState,
    snapshot: CanonicalizationSnapshot,
    budget: float,
) -> str:
    """Build the candidate tree in a provider-owned temporary index."""
    env = materialization_env(state)
    env["GIT_INDEX_FILE"] = str(state.candidate_index)
    clamps = materialization_clamps(snapshot, state)
    if state.candidate_index.exists():
        state.candidate_index.unlink()
    code, _stdout, stderr = await transport_git(
        cwd, "read-tree", expected_sha, timeout=budget, env=env
    )
    if code != 0:
        raise DirectCodexPersistenceError(
            "direct_codex_candidate_index_failed",
            f"cannot seed the candidate index: {_decode(stderr).strip()[:200]}",
        )
    paths = list(delta.paths)
    for start in range(0, len(paths), MAX_STAGE_PATHS_PER_CALL):
        chunk = paths[start : start + MAX_STAGE_PATHS_PER_CALL]
        code, _stdout, stderr = await transport_git(
            cwd, *clamps, "add", "-A", "--", *chunk, timeout=budget, env=env
        )
        if code != 0:
            raise DirectCodexPersistenceError(
                "direct_codex_candidate_stage_failed",
                f"cannot stage eligible paths: {_decode(stderr).strip()[:200]}",
            )
    code, stdout, stderr = await transport_git(
        cwd, "write-tree", timeout=budget, env=env
    )
    if code != 0:
        raise DirectCodexPersistenceError(
            "direct_codex_candidate_tree_failed",
            f"cannot write the candidate tree: {_decode(stderr).strip()[:200]}",
        )
    tree = _decode(stdout).strip()
    if not _SHA_RE.match(tree):
        raise DirectCodexPersistenceError(
            "direct_codex_candidate_tree_failed", "write-tree did not return an object id"
        )
    await _verify_candidate_tree(cwd, expected_sha, tree, delta, budget)
    return tree


async def _verify_candidate_tree(
    cwd: Path,
    expected_sha: str,
    tree: str,
    delta: WorktreeDelta,
    budget: float,
) -> None:
    """Require candidate tree == parent tree + exactly the eligible delta."""
    code, stdout, _stderr = await transport_git(
        cwd,
        "diff-tree",
        "-r",
        "--name-only",
        "-z",
        "--no-renames",
        expected_sha,
        tree,
        timeout=budget,
    )
    if code != 0:
        raise DirectCodexPersistenceError(
            "direct_codex_candidate_verification_failed", "cannot verify the candidate tree"
        )
    changed = {path for path in _decode(stdout).split("\0") if path}
    if changed != set(delta.paths):
        raise DirectCodexPersistenceError(
            "direct_codex_candidate_tree_mismatch",
            "the candidate tree does not equal the admitted parent plus the "
            "validated eligible delta",
        )


async def _commit_tree(
    cwd: Path,
    tree: str,
    parent: str,
    identity: CommitIdentity,
    message: str,
    state: ProviderState,
    snapshot: CanonicalizationSnapshot,
    budget: float,
) -> str:
    env = materialization_env(state)
    env.update(identity.git_env())
    code, stdout, stderr = await transport_git(
        cwd,
        *materialization_clamps(snapshot, state),
        "commit-tree",
        tree,
        "-p",
        parent,
        "-m",
        message,
        timeout=budget,
        env=env,
    )
    if code != 0:
        raise DirectCodexPersistenceError(
            "direct_codex_commit_failed",
            f"cannot create the provider candidate commit: {_decode(stderr).strip()[:200]}",
        )
    candidate = _decode(stdout).strip()
    if not _SHA_RE.match(candidate):
        raise DirectCodexPersistenceError(
            "direct_codex_commit_failed", "commit-tree did not return an object id"
        )
    return candidate


async def _verify_candidate_object(
    cwd: Path, candidate: str, tree: str, parent: str, budget: float
) -> None:
    code, stdout, _stderr = await transport_git(
        cwd, "rev-parse", f"{candidate}^{{tree}}", timeout=budget
    )
    if code != 0 or _decode(stdout).strip() != tree:
        raise DirectCodexPersistenceError(
            "direct_codex_candidate_object_mismatch", "candidate tree does not match"
        )
    code, stdout, _stderr = await transport_git(
        cwd, "rev-parse", f"{candidate}^", timeout=budget
    )
    if code != 0 or _decode(stdout).strip() != parent:
        raise DirectCodexPersistenceError(
            "direct_codex_candidate_object_mismatch", "candidate parent does not match"
        )


def _new_identity(task_id: str, run_id: str, attempt_id: str, slice_id: str | None, now: int) -> CommitIdentity:
    message = commit_message(
        task_id=task_id, run_id=run_id, attempt_id=attempt_id, slice_id=slice_id
    )
    return CommitIdentity(
        author_name=FIXED_IDENT_NAME,
        author_email=FIXED_IDENT_EMAIL,
        committer_name=FIXED_IDENT_NAME,
        committer_email=FIXED_IDENT_EMAIL,
        author_date_utc_seconds=now,
        committer_date_utc_seconds=now,
        timezone=TIMEZONE,
        message_digest=hashlib.sha256(message.encode("utf-8")).hexdigest(),
        serialization_version=SERIALIZATION_VERSION,
    )


def _provenance_digest(
    identity: CommitIdentity, candidate: str, message: str, base_head: str
) -> str:
    body = json.dumps(
        {
            "candidate": candidate,
            "base_head": base_head,
            "commit_identity": identity.to_dict(),
            "message": message,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _journal_identity(
    repository: RepositoryIdentity,
    semantic: SemanticIdentity,
) -> dict[str, Any]:
    return {
        "repository": repository.canonical,
        "task_id": semantic.task_id,
        "run_id": semantic.run_id,
        "attempt_id": semantic.attempt_id,
        "slice_id": semantic.slice_id,
    }


def _journal_matches(
    journal: PersistenceJournal,
    repository: RepositoryIdentity,
    semantic: SemanticIdentity,
    canonical_pr: int,
    branch: str,
    expected_sha: str,
) -> bool:
    if journal.identity != _journal_identity(repository, semantic):
        return False
    transport = journal.transport
    return (
        transport.get("canonical_pr") == canonical_pr
        and transport.get("canonical_branch") == branch
        and transport.get("expected_remote_sha") == expected_sha
    )


async def persist_implementation(
    *,
    workspace: DirectCodexWorkspace,
    bootstrap: TransportBootstrap,
    repository: RepositoryIdentity,
    semantic: SemanticIdentity,
    canonical_pr: int,
    branch: str,
    expected_remote_sha: str,
    timeout: float,
    clock: Any = None,
) -> PersistenceOutcome:
    """Owner of deterministic persistence and canonical publication.

    Returns a bounded outcome; a dirty/unpersisted result is never reported as
    successful canonical execution, and a verified no-change outcome is distinct
    from persisted implementation.
    """
    now = int((clock or time.time)())
    state = bootstrap.state or ensure_provider_state(workspace)
    snapshot = bootstrap.snapshot or read_persisted_snapshot(state)
    if snapshot is None:
        raise DirectCodexPersistenceError(
            "direct_codex_snapshot_missing",
            "no persisted pre-checkout canonicalization snapshot is available",
        )
    cwd = Path(workspace.path)
    budget = float(timeout)

    journal = _read_journal(state)
    if journal is not None and not _journal_matches(
        journal, repository, semantic, canonical_pr, branch, expected_remote_sha
    ):
        raise DirectCodexPersistenceError(
            "direct_codex_recovery_journal_identity_mismatch",
            "the provider recovery journal is bound to a different attempt or transport",
        )

    # Recovery: an already published/uncertain attempt is resolved by remote
    # readback alone and never creates a second candidate or hidden re-push.
    if journal is not None and journal.state == STATE_PUBLISHED:
        return await _recover_published(
            state, journal, cwd, repository, branch, expected_remote_sha, budget
        )
    if journal is not None and journal.state == STATE_PUBLISH_INTENT:
        return await _recover_publish_intent(
            state, journal, cwd, repository, branch, expected_remote_sha, budget
        )

    # D13 — revalidate exact identity/transport and the frozen clean authority.
    local_head = await _rev_parse(cwd, "HEAD", budget)
    if local_head != expected_remote_sha:
        raise DirectCodexPersistenceError(
            "direct_codex_local_head_unexpected",
            "the execution checkout head is not the admitted expected head; the "
            "direct host must not own the canonical transport",
        )
    actual_branch = _decode(
        (
            await transport_git(cwd, "rev-parse", "--abbrev-ref", "HEAD", timeout=budget)
        )[1]
    ).strip()
    if actual_branch != branch:
        raise DirectCodexPersistenceError(
            "direct_codex_actual_branch_drift",
            "the execution checkout is not on the exact canonical branch",
        )
    await revalidate_canonicalization(workspace, state, snapshot, budget)

    remote_before = await read_remote_head(
        cwd=cwd, repository=repository, branch=branch, timeout=budget
    )
    if remote_before != expected_remote_sha:
        raise DirectCodexPersistenceError(
            "direct_codex_transport_drift",
            "the canonical remote branch moved before persistence; no publish is permitted",
        )

    delta = await _inventory(cwd, expected_remote_sha, budget)

    if journal is None:
        commit_identity = _new_identity(
            semantic.task_id, semantic.run_id, semantic.attempt_id, semantic.slice_id, now
        )
        message = commit_message(
            task_id=semantic.task_id,
            run_id=semantic.run_id,
            attempt_id=semantic.attempt_id,
            slice_id=semantic.slice_id,
        )
        journal = PersistenceJournal(
            identity=_journal_identity(repository, semantic),
            transport={
                "canonical_pr": canonical_pr,
                "canonical_branch": branch,
                "expected_remote_sha": expected_remote_sha,
            },
            clean_semantics={
                "pre_checkout_snapshot_digest": snapshot.digest,
                "expected_attribute_snapshot_digest": snapshot.expected_attribute_digest,
                "checkout_materialized_under_snapshot": True,
                "info_attributes_empty": True,
                "versioned_gitattributes_unchanged": True,
            },
            commit_identity=commit_identity,
            message=message,
        )
        journal.eligible_change_count = delta.count
        journal.eligible_paths_digest = delta.digest
        journal = _write_journal(state, journal)
    else:
        if journal.clean_semantics.get("pre_checkout_snapshot_digest") != snapshot.digest:
            raise DirectCodexPersistenceError(
                "direct_codex_snapshot_drift",
                "the recovery journal was prepared under a different canonicalization snapshot",
            )

    commit_identity = journal.commit_identity
    message = journal.message
    if hashlib.sha256(message.encode("utf-8")).hexdigest() != commit_identity.message_digest:
        raise DirectCodexPersistenceError(
            "direct_codex_recovery_journal_invalid", "the recovery journal message digest drifted"
        )

    if delta.count == 0:
        # A verified no-change outcome never manufactures an empty commit.
        journal.state = STATE_PREPARED
        journal.eligible_change_count = 0
        journal.eligible_paths_digest = delta.digest
        _write_journal(state, journal)
        return PersistenceOutcome(
            mode=PERSISTENCE_MODE,
            status="no_change",
            base_head=expected_remote_sha,
            eligible_change_count=0,
            changed_paths_digest=delta.digest,
            candidate_commit=None,
            commit_provenance_digest=None,
            published=False,
            remote_head_readback=remote_before,
            consistent=False,
            actual_branch=actual_branch,
            local_head=local_head,
            snapshot_digest=snapshot.digest,
            state=STATE_PREPARED,
        )

    # D14 — candidate tree in a provider-owned temporary index.
    if journal.state == STATE_PREPARED or journal.candidate_tree_sha is None:
        tree = await _write_tree(cwd, expected_remote_sha, delta, state, snapshot, budget)
        journal.candidate_tree_sha = tree
        journal.eligible_paths_digest = delta.digest
        journal.eligible_change_count = delta.count
        journal.state = STATE_TREE_READY
        journal = _write_journal(state, journal)
    else:
        tree = journal.candidate_tree_sha
        await _verify_candidate_tree(cwd, expected_remote_sha, tree, delta, budget)

    # Freeze all commit-SHA inputs before the candidate object exists.
    if journal.candidate_commit_sha is None:
        candidate = await _commit_tree(
            cwd, tree, expected_remote_sha, commit_identity, message, state, snapshot, budget
        )
        await _verify_candidate_object(cwd, candidate, tree, expected_remote_sha, budget)
        journal.candidate_commit_sha = candidate
        journal.state = STATE_CANDIDATE_READY
        journal = _write_journal(state, journal)
    else:
        candidate = journal.candidate_commit_sha
        await _verify_candidate_object(cwd, candidate, tree, expected_remote_sha, budget)

    # Provider-owned local candidate ref (CAS on the admitted parent).
    code, _stdout, stderr = await transport_git(
        cwd,
        "update-ref",
        f"refs/heads/{branch}",
        candidate,
        expected_remote_sha,
        timeout=budget,
    )
    if code != 0:
        raise DirectCodexPersistenceError(
            "direct_codex_local_ref_failed",
            f"cannot move the provider local candidate ref: {_decode(stderr).strip()[:200]}",
        )
    journal.state = STATE_LOCAL_REF_READY
    journal = _write_journal(state, journal)

    # D17 — CAS-style ordinary fast-forward publication.
    remote_now = await read_remote_head(
        cwd=cwd, repository=repository, branch=branch, timeout=budget
    )
    if remote_now != expected_remote_sha:
        raise DirectCodexPersistenceError(
            "direct_codex_transport_drift",
            "the canonical remote branch moved before publish; no push is permitted",
        )
    journal.state = STATE_PUBLISH_INTENT
    journal = _write_journal(state, journal)

    # The push reuses the active-user credential context, so it is NOT run under
    # the materialization clamp that excludes global config; only local hooks are
    # denied so nothing repository-controlled can execute through persistence.
    code, _stdout, stderr = await transport_git(
        cwd,
        "-c",
        f"core.hooksPath={state.hooks}",
        "push",
        "origin",
        f"{candidate}:refs/heads/{branch}",
        timeout=budget,
    )
    if code != 0:
        return PersistenceOutcome(
            mode=PERSISTENCE_MODE,
            status="publication_failed",
            base_head=expected_remote_sha,
            eligible_change_count=delta.count,
            changed_paths_digest=delta.digest,
            candidate_commit=candidate,
            commit_provenance_digest=_provenance_digest(
                commit_identity, candidate, message, expected_remote_sha
            ),
            published=False,
            remote_head_readback=remote_now,
            consistent=False,
            actual_branch=actual_branch,
            local_head=candidate,
            snapshot_digest=snapshot.digest,
            state=STATE_PUBLISH_INTENT,
            error_code="direct_codex_publish_failed",
            detail=_decode(stderr).strip()[:200] or None,
        )

    remote_after = await read_remote_head(
        cwd=cwd, repository=repository, branch=branch, timeout=budget
    )
    if remote_after != candidate:
        # Uncertain externally visible publication: readback decides, never a
        # hidden automatic second push.
        status = (
            "publication_uncertain_or_not_observed"
            if remote_after == expected_remote_sha
            else "transport_drift"
        )
        return PersistenceOutcome(
            mode=PERSISTENCE_MODE,
            status=status,
            base_head=expected_remote_sha,
            eligible_change_count=delta.count,
            changed_paths_digest=delta.digest,
            candidate_commit=candidate,
            commit_provenance_digest=_provenance_digest(
                commit_identity, candidate, message, expected_remote_sha
            ),
            published=False,
            remote_head_readback=remote_after,
            consistent=False,
            actual_branch=actual_branch,
            local_head=candidate,
            snapshot_digest=snapshot.digest,
            state=STATE_PUBLISH_INTENT,
            error_code="direct_codex_publication_uncertain",
        )

    journal.state = STATE_PUBLISHED
    _write_journal(state, journal)
    return PersistenceOutcome(
        mode=PERSISTENCE_MODE,
        status="persisted",
        base_head=expected_remote_sha,
        eligible_change_count=delta.count,
        changed_paths_digest=delta.digest,
        candidate_commit=candidate,
        commit_provenance_digest=_provenance_digest(
            commit_identity, candidate, message, expected_remote_sha
        ),
        published=True,
        remote_head_readback=remote_after,
        consistent=True,
        actual_branch=actual_branch,
        local_head=candidate,
        snapshot_digest=snapshot.digest,
        state=STATE_PUBLISHED,
    )


async def _recover_published(
    state: ProviderState,
    journal: PersistenceJournal,
    cwd: Path,
    repository: RepositoryIdentity,
    branch: str,
    expected_remote_sha: str,
    budget: float,
) -> PersistenceOutcome:
    """An already published attempt: verify remote, never create a second commit."""
    candidate = journal.candidate_commit_sha
    if not candidate:
        raise DirectCodexPersistenceError(
            "direct_codex_recovery_journal_invalid", "published state without a candidate commit"
        )
    remote = await read_remote_head(
        cwd=cwd, repository=repository, branch=branch, timeout=budget
    )
    if remote != candidate:
        raise DirectCodexPersistenceError(
            "direct_codex_transport_drift",
            "the published candidate is no longer the canonical remote head",
        )
    actual_branch = _decode(
        (await transport_git(cwd, "rev-parse", "--abbrev-ref", "HEAD", timeout=budget))[1]
    ).strip()
    return PersistenceOutcome(
        mode=PERSISTENCE_MODE,
        status="persisted",
        base_head=str(journal.transport.get("expected_remote_sha")),
        eligible_change_count=int(journal.eligible_change_count or 0),
        changed_paths_digest=str(journal.eligible_paths_digest or ""),
        candidate_commit=candidate,
        commit_provenance_digest=_provenance_digest(
            journal.commit_identity, candidate, journal.message, expected_remote_sha
        ),
        published=True,
        remote_head_readback=remote,
        consistent=actual_branch == branch,
        actual_branch=actual_branch,
        local_head=candidate,
        snapshot_digest=str(journal.clean_semantics.get("pre_checkout_snapshot_digest")),
        state=STATE_PUBLISHED,
    )


async def _recover_publish_intent(
    state: ProviderState,
    journal: PersistenceJournal,
    cwd: Path,
    repository: RepositoryIdentity,
    branch: str,
    expected_remote_sha: str,
    budget: float,
) -> PersistenceOutcome:
    """Readback only after an uncertain push; never a hidden automatic re-push."""
    candidate = journal.candidate_commit_sha or ""
    remote = await read_remote_head(
        cwd=cwd, repository=repository, branch=branch, timeout=budget
    )
    actual_branch = _decode(
        (await transport_git(cwd, "rev-parse", "--abbrev-ref", "HEAD", timeout=budget))[1]
    ).strip()
    if remote == candidate and candidate:
        journal.state = STATE_PUBLISHED
        _write_journal(state, journal)
        return PersistenceOutcome(
            mode=PERSISTENCE_MODE,
            status="persisted",
            base_head=expected_remote_sha,
            eligible_change_count=int(journal.eligible_change_count or 0),
            changed_paths_digest=str(journal.eligible_paths_digest or ""),
            candidate_commit=candidate,
            commit_provenance_digest=_provenance_digest(
                journal.commit_identity, candidate, journal.message, expected_remote_sha
            ),
            published=True,
            remote_head_readback=remote,
            consistent=actual_branch == branch,
            actual_branch=actual_branch,
            local_head=candidate,
            snapshot_digest=str(journal.clean_semantics.get("pre_checkout_snapshot_digest")),
            state=STATE_PUBLISHED,
        )
    if remote == expected_remote_sha:
        return PersistenceOutcome(
            mode=PERSISTENCE_MODE,
            status="publication_uncertain_or_not_observed",
            base_head=expected_remote_sha,
            eligible_change_count=int(journal.eligible_change_count or 0),
            changed_paths_digest=str(journal.eligible_paths_digest or ""),
            candidate_commit=candidate or None,
            commit_provenance_digest=(
                _provenance_digest(
                    journal.commit_identity, candidate, journal.message, expected_remote_sha
                )
                if candidate
                else None
            ),
            published=False,
            remote_head_readback=remote,
            consistent=False,
            actual_branch=actual_branch,
            local_head=candidate,
            snapshot_digest=str(journal.clean_semantics.get("pre_checkout_snapshot_digest")),
            state=STATE_PUBLISH_INTENT,
            error_code="direct_codex_publication_uncertain",
        )
    raise DirectCodexPersistenceError(
        "direct_codex_transport_drift",
        "the canonical remote branch moved to an unexpected head after an uncertain publish",
    )
