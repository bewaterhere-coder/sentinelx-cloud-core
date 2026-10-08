"""Fixed canonical transport bootstrap for the direct-Codex host (PR-015/S02).

D7 requires the direct host to obtain the *existing* canonical PR branch before
invoking Codex, with a CAS-style remote head admission and an independent
execution checkout. This module never accepts caller Git argv, never overrides
a remote URL, never creates a replacement branch or PR, and never runs
``git worktree add`` against a canonical checkout (that would mutate canonical
``.git/worktrees`` metadata).
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sentinelx_core.direct_codex_workspace import (
    DirectCodexWorkspace,
    DirectCodexWorkspaceError,
    ensure_outside_canonical,
)
from sentinelx_core.mutation_placement import RepositoryIdentity, SemanticIdentity
from sentinelx_core.policy import DirectCodexPolicy
from sentinelx_core.user_git import (
    UserScopedGitError,
    classify_result,
    run_user_scoped_git,
)

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

# Provider-owned execution-state location. It sits beside the derived
# implementation checkout (never inside it), so nothing the provider writes for
# inspection, canonicalization or recovery can enter the candidate commit.
STATE_DIR_NAME = ".devforge-state"
SNAPSHOT_VERSION = 1
_ATTRIBUTES_FILE_NAME = "attributes-empty"
_EMPTY_CONFIG_NAME = "empty-config"
_HOOKS_DIR_NAME = "hooks"
_INSPECTION_INDEX_NAME = "inspection-index"
_SNAPSHOT_FILE_NAME = "canonicalization-snapshot.json"

# Closed schema for the allowlisted safe checkout-normalization scalars.
_SCALAR_SCHEMA: dict[str, frozenset[str]] = {
    "core.autocrlf": frozenset({"", "true", "false", "input"}),
    "core.eol": frozenset({"", "native", "lf", "crlf"}),
    "core.safecrlf": frozenset({"", "true", "false", "warn"}),
}
_CHECK_ROUNDTRIP_ENCODING = "core.checkroundtripencoding"
_WTE_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:\-]*$")
_GITATTRIBUTES_NAME = ".gitattributes"
_ATTR_CHUNK = 128


async def transport_git(
    root: Path,
    *args: str,
    timeout: float,
    env: Mapping[str, str] | None = None,
) -> tuple[int, bytes, bytes]:
    """Run fixed Git argv, converting an unavailable user context into a
    fail-closed direct-Codex transport error. There is no shell fallback.

    ``env`` accepts only the provider-owned keys in ``GIT_ENV_ALLOWLIST`` so the
    persistence broker can use a provider-owned index and a frozen commit
    identity without the primitive becoming a generic environment surface.
    """
    try:
        return await run_user_scoped_git(root, *args, timeout=timeout, env=env)
    except UserScopedGitError as exc:
        raise DirectCodexTransportError(
            "direct_codex_git_context_unavailable", str(exc)
        ) from exc


class DirectCodexTransportError(RuntimeError):
    """Fail-closed error for direct-Codex transport bootstrap."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class DirectCodexCanonicalizationError(DirectCodexTransportError):
    """Fail-closed error for provider-owned canonicalization authority.

    Every subclass of ``DirectCodexTransportError`` is caught by the handler at
    the same boundary; the distinct class exists so focused tests can assert the
    exact canonicalization failure without string matching.
    """


@dataclass(frozen=True)
class ProviderState:
    """Provider-owned execution-state paths for one derived workspace.

    ``empty_attributes``/``empty_config``/``hooks`` are the provider-owned
    neutralization targets used for every local materialization operation;
    ``inspection_index`` is a provider-owned index seeded from the expected tree
    (never the Codex-owned index); ``snapshot`` is the persisted pre-checkout
    canonicalization snapshot.
    """

    directory: Path
    empty_attributes: Path
    empty_config: Path
    hooks: Path
    inspection_index: Path
    snapshot: Path
    journal: Path
    candidate_index: Path


def provider_state(workspace: DirectCodexWorkspace) -> ProviderState:
    directory = Path(workspace.root) / STATE_DIR_NAME / workspace.workspace_digest
    return ProviderState(
        directory=directory,
        empty_attributes=directory / _ATTRIBUTES_FILE_NAME,
        empty_config=directory / _EMPTY_CONFIG_NAME,
        hooks=directory / _HOOKS_DIR_NAME,
        inspection_index=directory / _INSPECTION_INDEX_NAME,
        snapshot=directory / _SNAPSHOT_FILE_NAME,
        journal=directory / "persistence-journal.json",
        candidate_index=directory / "candidate-index",
    )


def ensure_provider_state(workspace: DirectCodexWorkspace) -> ProviderState:
    """Create the provider-owned state locations (idempotent)."""
    state = provider_state(workspace)
    state.directory.mkdir(parents=True, exist_ok=True)
    state.empty_attributes.write_bytes(b"")
    state.empty_config.write_bytes(b"")
    state.hooks.mkdir(parents=True, exist_ok=True)
    return state


def materialization_env(state: ProviderState) -> dict[str, str]:
    """Provider-owned clamps that exclude ambient Git materialization authority.

    System/global config and system attributes are neutralized and global
    attributes are redirected to the provider-owned empty file; the frozen safe
    scalars are replayed as explicit ``-c`` config so supported clean semantics
    survive the exclusion.
    """
    return {
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": str(state.empty_config),
        "GIT_CONFIG_SYSTEM": str(state.empty_config),
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_LITERAL_PATHSPECS": "1",
    }


def materialization_clamps(snapshot: CanonicalizationSnapshot | None, state: ProviderState) -> list[str]:
    """Fixed provider-owned ``-c`` clamps for local materialization/persistence."""
    clamps = [
        "-c",
        f"core.attributesFile={state.empty_attributes}",
        "-c",
        f"core.hooksPath={state.hooks}",
        "-c",
        "core.fsmonitor=false",
        "-c",
        "submodule.recurse=false",
        "-c",
        "commit.gpgsign=false",
        "-c",
        "tag.gpgsign=false",
        "-c",
        "core.pager=cat",
    ]
    if snapshot is not None:
        for key in sorted(snapshot.scalars):
            value = snapshot.scalars[key]
            if value:
                clamps += ["-c", f"{key}={value}"]
    return clamps


@dataclass(frozen=True)
class CanonicalizationSnapshot:
    """Frozen provider-owned checkout/clean canonicalization authority."""

    version: int
    scalars: dict[str, str]
    info_attributes_empty: bool
    expected_attribute_digest: str
    versioned_gitattributes_digest: str
    expected_remote_sha: str
    inspection_index_digest: str
    digest: str

    def body(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "scalars": dict(self.scalars),
            "info_attributes_empty": self.info_attributes_empty,
            "expected_attribute_digest": self.expected_attribute_digest,
            "versioned_gitattributes_digest": self.versioned_gitattributes_digest,
            "expected_remote_sha": self.expected_remote_sha,
            "inspection_index_digest": self.inspection_index_digest,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.body()
        payload["digest"] = self.digest
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> CanonicalizationSnapshot:
        return cls(
            version=int(payload["version"]),
            scalars={str(key): str(value) for key, value in dict(payload["scalars"]).items()},
            info_attributes_empty=bool(payload["info_attributes_empty"]),
            expected_attribute_digest=str(payload["expected_attribute_digest"]),
            versioned_gitattributes_digest=str(payload["versioned_gitattributes_digest"]),
            expected_remote_sha=str(payload["expected_remote_sha"]),
            inspection_index_digest=str(payload["inspection_index_digest"]),
            digest=str(payload["digest"]),
        )


def snapshot_digest(body: Mapping[str, Any]) -> str:
    encoded = json.dumps(dict(body), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TransportBootstrap:
    workspace: Path
    repository: str
    remote_url: str
    branch: str
    expected_remote_sha: str
    remote_head: str
    local_head: str
    actual_branch: str
    canonical_roots: tuple[str, ...]
    canonical_checkout_mutated: bool
    git_worktree_add_used: bool
    independent_checkout: bool
    created_checkout: bool
    state: ProviderState | None = None
    snapshot: CanonicalizationSnapshot | None = None
    snapshot_reused: bool = False


def remote_url_for(repository: RepositoryIdentity) -> str:
    """Provider-derived canonical remote URL. Caller data never supplies it."""
    return f"https://{repository.canonical.split('://', 1)[1]}.git"


def _parse_remote_head(stdout: bytes, branch: str) -> str | None:
    for line in stdout.decode("utf-8", errors="replace").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1] in (f"refs/heads/{branch}", branch):
            candidate = parts[0].strip()
            if _SHA_RE.match(candidate):
                return candidate
    return None


async def read_remote_head(
    *,
    cwd: Path,
    repository: RepositoryIdentity,
    branch: str,
    timeout: float,
) -> str:
    code, stdout, stderr = await transport_git(
        cwd, "ls-remote", "--heads", remote_url_for(repository), branch, timeout=timeout
    )
    if code != 0:
        reason = classify_result(code, stderr) or "GitRemoteFailed"
        raise DirectCodexTransportError(
            "direct_codex_remote_read_failed",
            f"cannot read the canonical remote branch head: {reason}",
        )
    head = _parse_remote_head(stdout, branch)
    if head is None:
        raise DirectCodexTransportError(
            "direct_codex_remote_branch_missing",
            f"canonical remote branch is not present: {branch}",
        )
    return head


async def _canonical_heads(roots: Iterable[Path], timeout: float) -> dict[str, str]:
    heads: dict[str, str] = {}
    for root in roots:
        path = Path(root)
        if not (path / ".git").exists():
            continue
        code, stdout, _stderr = await transport_git(
            path, "rev-parse", "HEAD", timeout=timeout
        )
        if code == 0:
            heads[str(path)] = stdout.decode("utf-8", errors="replace").strip()
    return heads


def _decode(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def validate_relative_path(path: str) -> None:
    """Fail closed on repository-metadata mutation or any path that escapes."""
    if not path or path.startswith("/") or "\\" in path:
        raise DirectCodexCanonicalizationError(
            "direct_codex_path_escape", f"path is not a clean repository-relative path: {path!r}"
        )
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise DirectCodexCanonicalizationError(
            "direct_codex_path_escape", f"path contains an unsafe component: {path!r}"
        )
    if ".git" in parts:
        raise DirectCodexCanonicalizationError(
            "direct_codex_repository_metadata_mutation",
            f"path targets repository metadata: {path!r}",
        )


async def _config_scalar(cwd: Path, key: str, budget: float) -> str:
    code, stdout, _stderr = await transport_git(cwd, "config", "--get", key, timeout=budget)
    if code != 0:
        return ""
    return _decode(stdout).strip()


def _normalize_scalars(raw: Mapping[str, str]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for key, allowed in _SCALAR_SCHEMA.items():
        value = str(raw.get(key, "")).strip().lower()
        if value not in allowed:
            raise DirectCodexCanonicalizationError(
                "direct_codex_unsupported_normalization_value",
                f"unsupported value for {key}: {raw.get(key)!r}",
            )
        normalized[key] = value
    wte = str(raw.get(_CHECK_ROUNDTRIP_ENCODING, "")).strip()
    for token in (part.strip() for part in wte.split(",")):
        if token and not _WTE_TOKEN_RE.match(token):
            raise DirectCodexCanonicalizationError(
                "direct_codex_unsupported_normalization_value",
                f"unsupported value for {_CHECK_ROUNDTRIP_ENCODING}: {wte!r}",
            )
    normalized[_CHECK_ROUNDTRIP_ENCODING] = wte
    return normalized


async def read_normalization_scalars(cwd: Path, budget: float) -> dict[str, str]:
    """Read the allowlisted effective checkout-normalization scalars.

    Read before any clamp so the *effective* (system + global + local) value is
    what gets frozen and later replayed.
    """
    raw = {key: await _config_scalar(cwd, key, budget) for key in _SCALAR_SCHEMA}
    raw[_CHECK_ROUNDTRIP_ENCODING] = await _config_scalar(cwd, _CHECK_ROUNDTRIP_ENCODING, budget)
    return _normalize_scalars(raw)


def _parse_tree_entries(stdout: bytes) -> list[tuple[str, str, str, str]]:
    entries: list[tuple[str, str, str, str]] = []
    for record in _decode(stdout).split("\0"):
        if not record or "\t" not in record:
            continue
        meta, _, path = record.partition("\t")
        fields = meta.split()
        if len(fields) != 3:
            continue
        entries.append((fields[0], fields[1], fields[2], path))
    return entries


async def _tree_entries(
    cwd: Path, sha: str, budget: float
) -> list[tuple[str, str, str, str]]:
    code, stdout, _stderr = await transport_git(
        cwd, "ls-tree", "-r", "-z", sha, timeout=budget
    )
    if code != 0:
        raise DirectCodexCanonicalizationError(
            "direct_codex_expected_tree_unavailable",
            f"cannot enumerate the admitted parent tree {sha}",
        )
    return _parse_tree_entries(stdout)


def info_attributes_empty(workspace: DirectCodexWorkspace) -> bool:
    path = Path(workspace.path) / ".git" / "info" / "attributes"
    if not path.exists():
        return True
    try:
        return not path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return False


async def seed_inspection_index(
    cwd: Path, state: ProviderState, sha: str, budget: float
) -> str:
    """Seed the provider-owned inspection index from the exact admitted parent.

    The index file is provider-owned and lives outside the implementation
    checkout; it is never the Codex-owned index.
    """
    env = materialization_env(state)
    env["GIT_INDEX_FILE"] = str(state.inspection_index)
    if state.inspection_index.exists():
        state.inspection_index.unlink()
    code, _stdout, stderr = await transport_git(
        cwd, "read-tree", sha, timeout=budget, env=env
    )
    if code != 0:
        raise DirectCodexCanonicalizationError(
            "direct_codex_inspection_index_failed",
            f"cannot seed the provider inspection index: {_decode(stderr).strip()[:200]}",
        )
    code, stdout, _stderr = await transport_git(
        cwd, "ls-files", "-s", "-z", timeout=budget, env=env
    )
    if code != 0:
        raise DirectCodexCanonicalizationError(
            "direct_codex_inspection_index_failed", "cannot read the provider inspection index"
        )
    return hashlib.sha256(stdout).hexdigest()


async def inspect_effective_attributes(
    cwd: Path, state: ProviderState, budget: float
) -> tuple[list[str], str]:
    """Resolve effective attributes from the inspection index without executing
    any filter. Returns the sorted normalized lines and their digest."""
    env = materialization_env(state)
    env["GIT_INDEX_FILE"] = str(state.inspection_index)
    code, stdout, _stderr = await transport_git(
        cwd, "ls-files", "-z", timeout=budget, env=env
    )
    if code != 0:
        raise DirectCodexCanonicalizationError(
            "direct_codex_attribute_inspection_failed", "cannot list the inspection index"
        )
    paths = [path for path in _decode(stdout).split("\0") if path]
    lines: list[str] = []
    for start in range(0, len(paths), _ATTR_CHUNK):
        chunk = paths[start : start + _ATTR_CHUNK]
        code, stdout, stderr = await transport_git(
            cwd,
            *materialization_clamps(None, state),
            "check-attr",
            "--cached",
            "--all",
            "--",
            *chunk,
            timeout=budget,
            env=env,
        )
        if code != 0:
            raise DirectCodexCanonicalizationError(
                "direct_codex_attribute_inspection_failed",
                f"check-attr failed: {_decode(stderr).strip()[:200]}",
            )
        for line in _decode(stdout).splitlines():
            if line.strip():
                lines.append(line.strip())
    normalized = sorted(set(lines))
    digest = hashlib.sha256("\n".join(normalized).encode("utf-8")).hexdigest()
    return normalized, digest


def reject_custom_filters(lines: Sequence[str]) -> None:
    """Fail closed on any effective custom filter assignment on a tracked path."""
    for line in lines:
        parts = line.rsplit(": ", 2)
        if len(parts) != 3:
            continue
        attr, value = parts[1], parts[2]
        if attr == "filter" and value not in ("unset", "unspecified"):
            raise DirectCodexCanonicalizationError(
                "direct_codex_unsupported_filter_attribute",
                f"effective filter attribute is not supported: {line}",
            )


def _versioned_gitattributes_digest(
    entries: Sequence[tuple[str, str, str, str]]
) -> tuple[str, tuple[str, ...]]:
    versioned = [
        (path, sha)
        for mode, kind, sha, path in entries
        if kind == "blob" and path.split("/")[-1] == _GITATTRIBUTES_NAME
    ]
    body = "\n".join(f"{path}\t{sha}" for path, sha in sorted(versioned))
    return hashlib.sha256(body.encode("utf-8")).hexdigest(), tuple(
        path for path, _ in versioned
    )


def read_persisted_snapshot(state: ProviderState) -> CanonicalizationSnapshot | None:
    if not state.snapshot.is_file():
        return None
    try:
        payload = json.loads(state.snapshot.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    try:
        return CanonicalizationSnapshot.from_dict(payload)
    except (KeyError, TypeError, ValueError):
        return None


def _verify_snapshot(snapshot: CanonicalizationSnapshot) -> None:
    if snapshot.digest != snapshot_digest(snapshot.body()):
        raise DirectCodexCanonicalizationError(
            "direct_codex_snapshot_readback_mismatch",
            "the persisted canonicalization snapshot digest does not match its content",
        )


def persist_snapshot(state: ProviderState, snapshot: CanonicalizationSnapshot) -> CanonicalizationSnapshot:
    """Atomically persist and read back the snapshot before checkout proceeds."""
    _verify_snapshot(snapshot)
    tmp = state.snapshot.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(snapshot.to_dict(), sort_keys=True), encoding="utf-8")
    tmp.replace(state.snapshot)
    readback = read_persisted_snapshot(state)
    if readback is None or readback != snapshot:
        raise DirectCodexCanonicalizationError(
            "direct_codex_snapshot_readback_mismatch",
            "the persisted canonicalization snapshot did not read back identically",
        )
    return readback


async def capture_canonicalization_snapshot(
    workspace: DirectCodexWorkspace,
    state: ProviderState,
    expected_remote_sha: str,
    budget: float,
) -> CanonicalizationSnapshot:
    """Capture and durably bind the pre-checkout canonicalization authority."""
    cwd = Path(workspace.path)
    scalars = await read_normalization_scalars(cwd, budget)
    if not info_attributes_empty(workspace):
        raise DirectCodexCanonicalizationError(
            "direct_codex_info_attributes_not_empty",
            ".git/info/attributes must be absent or empty before checkout",
        )
    entries = await _tree_entries(cwd, expected_remote_sha, budget)
    index_digest = await seed_inspection_index(cwd, state, expected_remote_sha, budget)
    lines, attribute_digest = await inspect_effective_attributes(cwd, state, budget)
    reject_custom_filters(lines)
    versioned_digest, _paths = _versioned_gitattributes_digest(entries)
    body = {
        "version": SNAPSHOT_VERSION,
        "scalars": scalars,
        "info_attributes_empty": True,
        "expected_attribute_digest": attribute_digest,
        "versioned_gitattributes_digest": versioned_digest,
        "expected_remote_sha": expected_remote_sha,
        "inspection_index_digest": index_digest,
    }
    snapshot = CanonicalizationSnapshot(
        version=SNAPSHOT_VERSION,
        scalars=scalars,
        info_attributes_empty=True,
        expected_attribute_digest=attribute_digest,
        versioned_gitattributes_digest=versioned_digest,
        expected_remote_sha=expected_remote_sha,
        inspection_index_digest=index_digest,
        digest=snapshot_digest(body),
    )
    return persist_snapshot(state, snapshot)


async def revalidate_canonicalization(
    workspace: DirectCodexWorkspace,
    state: ProviderState,
    persisted: CanonicalizationSnapshot,
    budget: float,
) -> CanonicalizationSnapshot:
    """Re-prove the frozen pre-checkout authority after the direct host ran.

    Re-reads the effective scalars, re-seeds the provider inspection index and
    re-resolves the expected-tree attributes. Any drift (including a non-empty
    ``.git/info/attributes``) fails closed before candidate construction.
    """
    _verify_snapshot(persisted)
    cwd = Path(workspace.path)
    if not info_attributes_empty(workspace):
        raise DirectCodexCanonicalizationError(
            "direct_codex_info_attributes_not_empty",
            ".git/info/attributes is not absent/empty after the direct host ran",
        )
    scalars = await read_normalization_scalars(cwd, budget)
    if scalars != persisted.scalars:
        raise DirectCodexCanonicalizationError(
            "direct_codex_snapshot_drift",
            "checkout-normalization scalars drifted between checkout and persistence",
        )
    index_digest = await seed_inspection_index(cwd, state, persisted.expected_remote_sha, budget)
    if index_digest != persisted.inspection_index_digest:
        raise DirectCodexCanonicalizationError(
            "direct_codex_snapshot_drift",
            "the admitted parent tree projection drifted after checkout",
        )
    lines, attribute_digest = await inspect_effective_attributes(cwd, state, budget)
    reject_custom_filters(lines)
    if attribute_digest != persisted.expected_attribute_digest:
        raise DirectCodexCanonicalizationError(
            "direct_codex_snapshot_drift",
            "the expected-tree attribute projection drifted after checkout",
        )
    return persisted


async def bootstrap_execution_checkout(
    *,
    policy: DirectCodexPolicy,
    workspace: DirectCodexWorkspace,
    repository: RepositoryIdentity,
    semantic: SemanticIdentity,
    branch: str,
    expected_remote_sha: str,
    canonical_roots: Iterable[Path] = (),
    timeout: float | None = None,
) -> TransportBootstrap:
    """Create or refresh the independent execution checkout at the exact head."""
    if not _SHA_RE.match(expected_remote_sha):
        raise DirectCodexTransportError(
            "direct_codex_transport_invalid", "expected_remote_sha must be a 40-hex object id"
        )
    if not branch.strip() or branch.strip() != branch:
        raise DirectCodexTransportError(
            "direct_codex_transport_invalid", "branch must be an exact non-padded branch name"
        )

    checked_roots = ensure_outside_canonical(workspace, canonical_roots)
    budget = float(timeout if timeout is not None else policy.timeout_seconds)
    remote_url = remote_url_for(repository)
    parent = workspace.path.parent
    parent.mkdir(parents=True, exist_ok=True)

    before_heads = await _canonical_heads(canonical_roots, budget)

    remote_head = await read_remote_head(
        cwd=parent, repository=repository, branch=branch, timeout=budget
    )
    if remote_head != expected_remote_sha:
        raise DirectCodexTransportError(
            "direct_codex_remote_head_mismatch",
            "canonical remote branch head does not match expected_remote_sha; "
            "no direct-Codex mutation is permitted",
        )

    # Phase A — authenticated object acquisition only (no worktree).
    created = False
    if not (workspace.path / ".git").exists():
        # The direct-Codex containment proof derives and empties this exact
        # directory before the transport bootstrap, so an existing but empty
        # derived workspace is still a valid independent-checkout target.
        if workspace.path.exists() and any(workspace.path.iterdir()):
            raise DirectCodexTransportError(
                "direct_codex_workspace_occupied",
                "the derived execution workspace exists but is not an independent checkout",
            )
        code, _out, stderr = await transport_git(
            parent,
            "clone",
            "--no-checkout",
            "--branch",
            branch,
            remote_url,
            workspace.path.name,
            timeout=budget,
        )
        if code != 0:
            reason = classify_result(code, stderr) or "GitRemoteFailed"
            raise DirectCodexTransportError(
                "direct_codex_clone_failed", f"cannot create the independent checkout: {reason}"
            )
        created = True
    else:
        code, _out, stderr = await transport_git(
            workspace.path, "fetch", "--no-tags", "--force", "origin", branch, timeout=budget
        )
        if code != 0:
            reason = classify_result(code, stderr) or "GitRemoteFailed"
            raise DirectCodexTransportError(
                "direct_codex_fetch_failed", f"cannot refresh the independent checkout: {reason}"
            )

    code, _out, _stderr = await transport_git(
        workspace.path, "cat-file", "-e", f"{expected_remote_sha}^{{commit}}", timeout=budget
    )
    if code != 0:
        raise DirectCodexTransportError(
            "direct_codex_expected_object_missing",
            "the admitted canonical commit is not present in the independent checkout",
        )

    state = ensure_provider_state(workspace)

    # Phase B — freeze the provider canonicalization authority BEFORE checkout.
    # Reuse the exact persisted snapshot when this attempt was already
    # materialized under it; otherwise capture and durably bind a fresh one.
    existing = read_persisted_snapshot(state)
    snapshot_reused = False
    if (
        existing is not None
        and existing.expected_remote_sha == expected_remote_sha
        and (workspace.path / ".git" / "HEAD").exists()
    ):
        head_check, head_out, _err = await transport_git(
            workspace.path, "rev-parse", "HEAD", timeout=budget
        )
        if head_check == 0 and _decode(head_out).strip() == expected_remote_sha:
            _verify_snapshot(existing)
            snapshot = existing
            snapshot_reused = True
    if not snapshot_reused:
        snapshot = await capture_canonicalization_snapshot(
            workspace, state, expected_remote_sha, budget
        )

    # Phase C — provider-clamped checkout using the frozen snapshot.
    clamps = materialization_clamps(snapshot, state)
    env = materialization_env(state)
    code, _out, stderr = await transport_git(
        workspace.path,
        *clamps,
        "checkout",
        "--force",
        "-B",
        branch,
        expected_remote_sha,
        timeout=budget,
        env=env,
    )
    if code != 0:
        reason = classify_result(code, stderr) or "GitTransportFailed"
        raise DirectCodexTransportError(
            "direct_codex_checkout_failed", f"cannot check out the canonical branch: {reason}"
        )

    code, stdout, stderr = await transport_git(
        workspace.path, "rev-parse", "HEAD", timeout=budget
    )
    if code != 0:
        raise DirectCodexTransportError(
            "direct_codex_head_read_failed", "cannot read the execution checkout head"
        )
    local_head = stdout.decode("utf-8", errors="replace").strip()
    if local_head != expected_remote_sha:
        raise DirectCodexTransportError(
            "direct_codex_local_head_mismatch",
            "execution checkout head does not match the admitted canonical head",
        )

    code, stdout, _stderr = await transport_git(
        workspace.path, "rev-parse", "--abbrev-ref", "HEAD", timeout=budget
    )
    actual_branch = stdout.decode("utf-8", errors="replace").strip()

    after_heads = await _canonical_heads(canonical_roots, budget)
    canonical_mutated = before_heads != after_heads

    return TransportBootstrap(
        workspace=workspace.path,
        repository=repository.canonical,
        remote_url=remote_url,
        branch=branch,
        expected_remote_sha=expected_remote_sha,
        remote_head=remote_head,
        local_head=local_head,
        actual_branch=actual_branch,
        canonical_roots=checked_roots,
        canonical_checkout_mutated=canonical_mutated,
        git_worktree_add_used=False,
        independent_checkout=True,
        created_checkout=created,
        state=state,
        snapshot=snapshot,
        snapshot_reused=snapshot_reused,
    )


def workspace_error_code(exc: DirectCodexWorkspaceError) -> str:
    return exc.code
