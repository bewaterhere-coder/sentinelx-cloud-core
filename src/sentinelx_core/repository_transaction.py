"""Provider-owned repository transaction admission and durable state.

This module owns only the S01 control-plane foundation: exact repository/ref
admission, durable transaction identity, and path-free projections. It does not
materialize source bytes, execute repository code, or publish Git objects.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import threading
from collections.abc import Awaitable, Callable, Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from sentinelx_core.mutation_placement import RepositoryIdentity, SemanticIdentity
from sentinelx_core.policy import Policy
from sentinelx_core.user_git import (
    UserScopedGitError,
    classify_result,
    redact_git_output,
    run_user_scoped_git,
)

STORE_VERSION = 1
REPOSITORY_TRANSACTION_PURPOSE = "repository_transaction_v1"
REPOSITORY_TRANSACTION_OPERATION_CLASSES = (
    "repository_execute",
    "repository_materialize",
    "repository_publish",
)
REPOSITORY_TRANSACTION_STATES = frozenset(
    {
        "provisioned",
        "materializing",
        "materialized",
        "executing",
        "executed",
        "publication_freezing",
        "publication_pending",
        "publishing",
        "publication_uncertain",
        "published",
        "terminal",
        "revoked",
        "expired",
    }
)
_SHA_RE = re.compile(r"^[0-9a-fA-F]{40,64}$")
_LOCKS_GUARD = threading.Lock()
_LOCAL_LOCKS: dict[str, threading.RLock] = {}


class RepositoryTransactionError(RuntimeError):
    code = "RepositoryTransactionError"


class RepositoryTransactionConflict(RepositoryTransactionError):
    code = "RepositoryTransactionConflict"


class RepositoryTransactionNotFound(RepositoryTransactionError):
    code = "RepositoryTransactionNotFound"


class RepositoryTransactionBindingMismatch(RepositoryTransactionError):
    code = "RepositoryTransactionBindingMismatch"


class RepositoryTransactionCorrupt(RepositoryTransactionError):
    code = "RepositoryTransactionCorrupt"


class RepositoryTransactionAdmissionFailed(RepositoryTransactionError):
    code = "RepositoryTransactionAdmissionFailed"


RepositoryRefResolver = Callable[[RepositoryIdentity, str], Awaitable[str]]


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _digest(value: object) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _opaque(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(18)}"


def validate_full_commit_sha(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not _SHA_RE.fullmatch(value.strip()):
        raise RepositoryTransactionAdmissionFailed(
            f"{field} must be a full hexadecimal commit SHA"
        )
    return value.strip().lower()


def validate_git_ref(value: object, *, field: str, publication: bool = False) -> str:
    if not isinstance(value, str):
        raise RepositoryTransactionAdmissionFailed(f"{field} must be a string")
    ref = value.strip()
    if not ref or len(ref) > 512:
        raise RepositoryTransactionAdmissionFailed(f"{field} is empty or too long")
    if ref.startswith("-") or any(ord(ch) < 32 or ch.isspace() for ch in ref):
        raise RepositoryTransactionAdmissionFailed(f"{field} contains unsafe characters")
    if any(token in ref for token in ("..", "@{", "\\", "~", "^", ":", "?", "*", "[")):
        raise RepositoryTransactionAdmissionFailed(f"{field} is not a bounded Git ref")
    if publication and not ref.startswith("refs/heads/"):
        raise RepositoryTransactionAdmissionFailed(
            f"{field} must be an exact refs/heads/<branch> ref"
        )
    return ref


def _repository_digest(repository: RepositoryIdentity) -> str:
    return _digest(repository.canonical)


def _semantic_digest(semantic: SemanticIdentity) -> str:
    return _digest(semantic.canonical)


def _attempt_key(repository: RepositoryIdentity, semantic: SemanticIdentity) -> str:
    return _digest(
        {
            "repository": repository.canonical,
            "semantic": list(semantic.canonical),
        }
    )


def _remote_repository_identity(remote_url: str) -> str:
    text = remote_url.strip()
    if not text:
        raise RepositoryTransactionAdmissionFailed("origin remote URL is empty")
    if "://" in text:
        parsed = urlsplit(text)
        if not parsed.hostname:
            raise RepositoryTransactionAdmissionFailed("origin remote URL has no hostname")
        return RepositoryIdentity(
            vcs="git",
            authority=parsed.hostname,
            path=parsed.path.strip("/"),
        ).canonical

    # Git's common scp-like SSH form: git@github.com:owner/repository.git
    host_part, sep, path_part = text.partition(":")
    if not sep or not path_part:
        raise RepositoryTransactionAdmissionFailed("origin remote URL is not a supported Git URL")
    host = host_part.rsplit("@", 1)[-1].strip()
    return RepositoryIdentity(vcs="git", authority=host, path=path_part).canonical


def _local_lock_for(path: Path) -> threading.RLock:
    key = str(path.resolve(strict=False)).casefold()
    with _LOCKS_GUARD:
        return _LOCAL_LOCKS.setdefault(key, threading.RLock())


@contextmanager
def _exclusive_file_lock(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    local = _local_lock_for(path)
    with local:
        with path.open("a+b") as handle:
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"0")
                handle.flush()
                os.fsync(handle.fileno())
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
                try:
                    yield
                finally:
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


@dataclass(frozen=True)
class RepositoryTransactionRecord:
    transaction_id: str
    state: str
    attempt_key: str
    repository_identity_digest: str
    semantic_identity_digest: str
    project_id: str
    task_id: str
    run_id: str
    attempt_id: str
    slice_id: str | None
    scope_id: str
    scope_generation: int
    workspace_id: str
    scope_digest: str
    source_ref: str
    expected_source_sha: str
    verified_source_sha: str
    publication_ref: str
    expected_remote_sha: str
    verified_remote_sha: str
    sealed_inputs_digest: str
    created_at: str
    updated_at: str
    materialization_evidence: dict[str, Any] | None = None
    execution_evidence: dict[str, Any] | None = None
    publication_evidence: dict[str, Any] | None = None

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, value: dict[str, Any]) -> "RepositoryTransactionRecord":
        try:
            record = cls(**dict(value))
        except (TypeError, ValueError) as exc:
            raise RepositoryTransactionCorrupt(f"invalid transaction record: {exc}") from exc
        if record.state not in REPOSITORY_TRANSACTION_STATES:
            raise RepositoryTransactionCorrupt(
                f"transaction {record.transaction_id} has invalid state {record.state!r}"
            )
        return record

    def project(self) -> dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "state": self.state,
            "repository_identity_digest": self.repository_identity_digest,
            "semantic_identity_digest": self.semantic_identity_digest,
            "scope_ref": {
                "scope_id": self.scope_id,
                "generation": self.scope_generation,
            },
            "workspace_id": self.workspace_id,
            "source_ref": self.source_ref,
            "verified_source_sha": self.verified_source_sha,
            "publication_ref": self.publication_ref,
            "expected_remote_sha": self.expected_remote_sha,
            "verified_remote_sha": self.verified_remote_sha,
            "sealed_inputs_digest": self.sealed_inputs_digest,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class RepositoryTransactionStore:
    """Durable one-transaction-per-Attempt repository authority store."""

    def __init__(self, state_root: Path) -> None:
        self.root = state_root.resolve(strict=False) / "repository-transactions"
        self._state_path = self.root / "authority.json"
        self._lock_path = self.root / "authority.lock"

    @staticmethod
    def _empty_state() -> dict[str, Any]:
        return {"version": STORE_VERSION, "transactions": {}, "attempts": {}, "scopes": {}}

    def _load_state(self) -> dict[str, Any]:
        if not self._state_path.exists():
            return self._empty_state()
        try:
            state = json.loads(self._state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise RepositoryTransactionCorrupt(
                f"cannot read repository transaction store: {exc}"
            ) from exc
        if not isinstance(state, dict) or state.get("version") != STORE_VERSION:
            raise RepositoryTransactionCorrupt("unsupported repository transaction store")
        for field in ("transactions", "attempts", "scopes"):
            if not isinstance(state.get(field), dict):
                raise RepositoryTransactionCorrupt(
                    f"repository transaction store field {field!r} is malformed"
                )
        return state

    def _durable_write_state(self, state: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        body = json.dumps(state, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"
        temp = self.root / f".authority.{secrets.token_hex(8)}.tmp"
        try:
            with temp.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(body)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, self._state_path)
            _fsync_directory(self.root)
        finally:
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass

    @staticmethod
    def _record(state: dict[str, Any], transaction_id: str) -> RepositoryTransactionRecord:
        raw = state["transactions"].get(transaction_id)
        if not isinstance(raw, dict):
            raise RepositoryTransactionNotFound(
                f"unknown repository transaction {transaction_id}"
            )
        record = RepositoryTransactionRecord.from_json(raw)
        if record.transaction_id != transaction_id:
            raise RepositoryTransactionCorrupt("transaction index key/id mismatch")
        return record

    def provision(
        self,
        repository: RepositoryIdentity,
        semantic: SemanticIdentity,
        *,
        scope: dict[str, Any],
        source_ref: str,
        expected_source_sha: str,
        verified_source_sha: str,
        publication_ref: str,
        expected_remote_sha: str,
        verified_remote_sha: str,
        now: datetime | None = None,
    ) -> RepositoryTransactionRecord:
        now = now or _utcnow()
        repository_digest = _repository_digest(repository)
        semantic_digest = _semantic_digest(semantic)
        attempt_key = _attempt_key(repository, semantic)
        scope_id = str(scope.get("scope_id") or "").strip()
        workspace_id = str(scope.get("workspace_id") or "").strip()
        scope_digest = str(scope.get("scope_digest") or "").strip()
        scope_generation = scope.get("generation")
        if (
            not scope_id
            or not workspace_id
            or not scope_digest
            or isinstance(scope_generation, bool)
            or not isinstance(scope_generation, int)
            or scope_generation <= 0
        ):
            raise RepositoryTransactionBindingMismatch(
                "repository transaction requires a complete provider-owned scope binding"
            )

        sealed = {
            "repository_identity_digest": repository_digest,
            "semantic_identity_digest": semantic_digest,
            "scope_id": scope_id,
            "scope_generation": scope_generation,
            "workspace_id": workspace_id,
            "scope_digest": scope_digest,
            "source_ref": source_ref,
            "expected_source_sha": expected_source_sha,
            "verified_source_sha": verified_source_sha,
            "publication_ref": publication_ref,
            "expected_remote_sha": expected_remote_sha,
            "verified_remote_sha": verified_remote_sha,
            "operation_classes": list(REPOSITORY_TRANSACTION_OPERATION_CLASSES),
        }
        sealed_digest = _digest(sealed)

        with _exclusive_file_lock(self._lock_path):
            state = self._load_state()
            existing_id = state["attempts"].get(attempt_key)
            if existing_id is not None:
                if not isinstance(existing_id, str):
                    raise RepositoryTransactionCorrupt("Attempt index is malformed")
                existing = self._record(state, existing_id)
                if existing.sealed_inputs_digest != sealed_digest:
                    raise RepositoryTransactionConflict(
                        "same Attempt retry changed sealed repository transaction authority"
                    )
                if state["scopes"].get(scope_id) != existing.transaction_id:
                    raise RepositoryTransactionConflict(
                        "scope index does not map to the existing repository transaction"
                    )
                return existing

            scope_existing = state["scopes"].get(scope_id)
            if scope_existing is not None:
                raise RepositoryTransactionConflict(
                    "mutation scope is already bound to another repository transaction"
                )

            transaction_id = _opaque("rtx")
            created = _iso(now)
            record = RepositoryTransactionRecord(
                transaction_id=transaction_id,
                state="provisioned",
                attempt_key=attempt_key,
                repository_identity_digest=repository_digest,
                semantic_identity_digest=semantic_digest,
                project_id=semantic.project_id.strip(),
                task_id=semantic.task_id.strip(),
                run_id=semantic.run_id.strip(),
                attempt_id=semantic.attempt_id.strip(),
                slice_id=semantic.slice_id.strip() if semantic.slice_id else None,
                scope_id=scope_id,
                scope_generation=scope_generation,
                workspace_id=workspace_id,
                scope_digest=scope_digest,
                source_ref=source_ref,
                expected_source_sha=expected_source_sha,
                verified_source_sha=verified_source_sha,
                publication_ref=publication_ref,
                expected_remote_sha=expected_remote_sha,
                verified_remote_sha=verified_remote_sha,
                sealed_inputs_digest=sealed_digest,
                created_at=created,
                updated_at=created,
            )
            state["transactions"][transaction_id] = record.to_json()
            state["attempts"][attempt_key] = transaction_id
            state["scopes"][scope_id] = transaction_id
            self._durable_write_state(state)

            persisted = self._load_state()
            confirmed = self._record(persisted, transaction_id)
            if persisted["attempts"].get(attempt_key) != transaction_id:
                raise RepositoryTransactionCorrupt("Attempt readback mismatch")
            if persisted["scopes"].get(scope_id) != transaction_id:
                raise RepositoryTransactionCorrupt("scope readback mismatch")
            return confirmed

    def inspect(
        self,
        repository: RepositoryIdentity,
        semantic: SemanticIdentity,
        *,
        scope_id: str,
        generation: int,
    ) -> RepositoryTransactionRecord:
        with _exclusive_file_lock(self._lock_path):
            state = self._load_state()
            transaction_id = state["scopes"].get(scope_id)
            if not isinstance(transaction_id, str):
                raise RepositoryTransactionNotFound(
                    f"no repository transaction is bound to scope {scope_id}"
                )
            record = self._record(state, transaction_id)
            if record.scope_generation != generation:
                raise RepositoryTransactionBindingMismatch(
                    "repository transaction scope generation mismatch"
                )
            if record.repository_identity_digest != _repository_digest(repository):
                raise RepositoryTransactionBindingMismatch(
                    "repository transaction repository identity mismatch"
                )
            if record.semantic_identity_digest != _semantic_digest(semantic):
                raise RepositoryTransactionBindingMismatch(
                    "repository transaction semantic lineage mismatch"
                )
            return record


def make_repository_ref_resolver(policy: Policy) -> RepositoryRefResolver:
    """Build a read-only provider-owned ref resolver from canonical inventory."""

    async def resolve(repository: RepositoryIdentity, ref: str) -> str:
        bounded_ref = validate_git_ref(ref, field="repository ref")
        if not policy.authenticated_git_enabled:
            raise RepositoryTransactionAdmissionFailed(
                "user-scoped Git execution is not enabled by Host policy"
            )
        mutation = policy.mutation_execution
        matches = [
            spec
            for spec in mutation.canonical_repositories
            if spec.repository_identity == repository.canonical
        ]
        if len(matches) != 1:
            raise RepositoryTransactionAdmissionFailed(
                "repository identity is absent or ambiguous in Host canonical inventory"
            )
        spec = matches[0]
        timeout = float(policy.authenticated_git_timeout_seconds)
        try:
            rc, stdout, stderr = await run_user_scoped_git(
                spec.root,
                "remote",
                "get-url",
                "origin",
                timeout=timeout,
            )
        except UserScopedGitError as exc:
            raise RepositoryTransactionAdmissionFailed(str(exc)) from exc
        reason = classify_result(rc, stderr)
        if reason is not None:
            detail = redact_git_output(stderr.decode("utf-8", "replace")).strip()
            raise RepositoryTransactionAdmissionFailed(
                f"origin identity probe failed ({reason}): {detail}"
            )
        remote_lines = [line.strip() for line in stdout.decode("utf-8", "replace").splitlines() if line.strip()]
        if len(remote_lines) != 1:
            raise RepositoryTransactionAdmissionFailed(
                "origin identity probe returned an ambiguous result"
            )
        if _remote_repository_identity(remote_lines[0]) != repository.canonical:
            raise RepositoryTransactionAdmissionFailed(
                "origin remote identity does not match admitted repository"
            )

        try:
            rc, stdout, stderr = await run_user_scoped_git(
                spec.root,
                "ls-remote",
                "--refs",
                "origin",
                bounded_ref,
                timeout=timeout,
            )
        except UserScopedGitError as exc:
            raise RepositoryTransactionAdmissionFailed(str(exc)) from exc
        reason = classify_result(rc, stderr)
        if reason is not None:
            detail = redact_git_output(stderr.decode("utf-8", "replace")).strip()
            raise RepositoryTransactionAdmissionFailed(
                f"remote ref probe failed ({reason}): {detail}"
            )
        resolved: list[str] = []
        for line in stdout.decode("utf-8", "replace").splitlines():
            parts = line.split("\t", 1)
            if len(parts) != 2:
                continue
            sha, _resolved_ref = parts
            if _SHA_RE.fullmatch(sha.strip()):
                resolved.append(sha.strip().lower())
        if len(resolved) != 1:
            raise RepositoryTransactionAdmissionFailed(
                "repository ref did not resolve to exactly one full commit SHA"
            )
        return resolved[0]

    return resolve
