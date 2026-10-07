"""Durable provider-owned mutation-scope lease authority.

S02 owns logical scope identity, uniqueness and lifecycle only. OS sandbox/SID,
ACL and Job enforcement are later slices; this store already carries reserved
runtime-binding fields so terminalization can fail closed once those slices
populate them.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import threading
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sentinelx_core.mutation_placement import (
    HostMutationScopeBindingMismatch,
    PlacementEvidence,
    PlacementGenerationState,
    RepositoryIdentity,
    SemanticIdentity,
    placement_policy_digest,
    resolve_placement,
    revalidate_placement,
    unique_mutation_lease_key,
)
from sentinelx_core.policy import MutationExecutionPolicy

STORE_VERSION = 1
NON_TERMINAL_STATES = frozenset({"provisioned", "active"})
TERMINAL_STATES = frozenset({"terminal", "revoked", "expired"})
SCOPED_SCRIPT_OPERATION_CLASS = "scoped_script"


class HostMutationScopeError(RuntimeError):
    code = "HostMutationScopeError"


class HostMutationScopeConflict(HostMutationScopeError):
    code = "HostMutationScopeConflict"


class HostMutationScopeNotCurrent(HostMutationScopeError):
    code = "HostMutationScopeNotCurrent"


class HostMutationScopeCorrupt(HostMutationScopeError):
    code = "HostMutationScopeCorrupt"


class HostMutationScopeOperationNotAllowed(HostMutationScopeError):
    code = "HostMutationScopeOperationNotAllowed"


class HostMutationScopeTerminalizationFailed(HostMutationScopeError):
    code = "HostMutationScopeTerminalizationFailed"


class HostMutationScopeStillActive(HostMutationScopeTerminalizationFailed):
    code = "HostMutationScopeStillActive"


class HostMutationResidualAuthorityDetected(HostMutationScopeTerminalizationFailed):
    code = "HostMutationResidualAuthorityDetected"


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _digest(value: object) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _opaque(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(18)}"


def _attempt_key(repository_digest: str, semantic: SemanticIdentity) -> str:
    """Stable guard preventing a completed Attempt from minting new authority."""
    project_id, task_id, run_id, attempt_id, slice_id = semantic.canonical
    return _digest(
        {
            "repository_identity_digest": repository_digest,
            "project_id": project_id,
            "task_id": task_id,
            "run_id": run_id,
            "attempt_id": attempt_id,
            "slice_id": slice_id,
        }
    )


@dataclass(frozen=True)
class MutationScopeRecord:
    workspace_id: str
    scope_id: str
    generation: int
    unique_lease_key: str
    attempt_key: str
    state: str

    project_id: str
    task_id: str
    run_id: str
    attempt_id: str
    slice_id: str | None
    semantic_identity_digest: str
    repository_identity_digest: str

    placement_ref: str
    placement_generation: int
    policy_digest: str
    exact_workspace: str
    exact_workspace_digest: str
    protected_inventory_digest: str

    allowed_operation_classes: tuple[str, ...]
    issued_at: str
    expires_at: str
    scope_digest: str

    # Reserved for S04/S05. They are intentionally part of the durable
    # authority record now so terminalization can never ignore later bindings.
    sandbox_identity: str | None = None
    active_job_ids: tuple[str, ...] = ()
    active_process_ids: tuple[str, ...] = ()
    sandbox_write_authority_present: bool = False
    runtime_read_authority_roots: tuple[str, ...] = ()
    terminalized_at: str | None = None

    @property
    def current(self) -> bool:
        return self.state in NON_TERMINAL_STATES

    @property
    def terminal(self) -> bool:
        return self.state in TERMINAL_STATES

    def immutable_digest_payload(self) -> dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "scope_id": self.scope_id,
            "generation": self.generation,
            "unique_lease_key": self.unique_lease_key,
            "attempt_key": self.attempt_key,
            "project_id": self.project_id,
            "task_id": self.task_id,
            "run_id": self.run_id,
            "attempt_id": self.attempt_id,
            "slice_id": self.slice_id,
            "semantic_identity_digest": self.semantic_identity_digest,
            "repository_identity_digest": self.repository_identity_digest,
            "placement_ref": self.placement_ref,
            "placement_generation": self.placement_generation,
            "policy_digest": self.policy_digest,
            "exact_workspace": self.exact_workspace,
            "exact_workspace_digest": self.exact_workspace_digest,
            "protected_inventory_digest": self.protected_inventory_digest,
            "allowed_operation_classes": list(self.allowed_operation_classes),
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
        }

    def verify_digest(self) -> None:
        if _digest(self.immutable_digest_payload()) != self.scope_digest:
            raise HostMutationScopeCorrupt(
                f"scope {self.scope_id} immutable authority digest mismatch"
            )

    def to_json(self) -> dict[str, Any]:
        result = asdict(self)
        result["allowed_operation_classes"] = list(self.allowed_operation_classes)
        result["active_job_ids"] = list(self.active_job_ids)
        result["active_process_ids"] = list(self.active_process_ids)
        result["runtime_read_authority_roots"] = list(self.runtime_read_authority_roots)
        return result

    @classmethod
    def from_json(cls, value: dict[str, Any]) -> "MutationScopeRecord":
        try:
            payload = dict(value)
            payload["allowed_operation_classes"] = tuple(payload.get("allowed_operation_classes") or ())
            payload["active_job_ids"] = tuple(payload.get("active_job_ids") or ())
            payload["active_process_ids"] = tuple(payload.get("active_process_ids") or ())
            payload["runtime_read_authority_roots"] = tuple(
                payload.get("runtime_read_authority_roots") or ()
            )
            record = cls(**payload)
        except (KeyError, TypeError, ValueError) as exc:
            raise HostMutationScopeCorrupt(f"invalid scope record: {exc}") from exc
        record.verify_digest()
        if record.state not in NON_TERMINAL_STATES | TERMINAL_STATES:
            raise HostMutationScopeCorrupt(
                f"scope {record.scope_id} has invalid state {record.state!r}"
            )
        return record


@dataclass(frozen=True)
class MutationRuntimeClosure:
    """Authoritative OS cleanup read-back consumed by terminalization."""

    sandbox_identity: str | None
    active_job_ids: tuple[str, ...] = ()
    active_process_ids: tuple[str, ...] = ()
    sandbox_write_authority_present: bool = False
    runtime_read_authority_roots: tuple[str, ...] = ()


_LOCKS_GUARD = threading.Lock()
_LOCAL_LOCKS: dict[str, threading.RLock] = {}


def _local_lock_for(path: Path) -> threading.RLock:
    key = str(path.resolve(strict=False)).casefold()
    with _LOCKS_GUARD:
        return _LOCAL_LOCKS.setdefault(key, threading.RLock())


@contextmanager
def _exclusive_file_lock(path: Path) -> Iterator[None]:
    """Cross-process lock plus an in-process thread lock for one authority store."""
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
    """Best available directory durability; Windows cannot fsync directories normally."""
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


class MutationScopeStore:
    """Authoritative transaction boundary for scope + lease + workspace indexes."""

    def __init__(self, state_root: Path) -> None:
        self.root = state_root.resolve(strict=False) / "mutation-scopes"
        self.root.mkdir(parents=True, exist_ok=True)
        self._state_path = self.root / "authority.json"
        self._lock_path = self.root / "authority.lock"

    @staticmethod
    def _empty_state() -> dict[str, Any]:
        return {
            "version": STORE_VERSION,
            "scopes": {},
            "leases": {},
            "attempts": {},
            "workspaces": {},
            "placement_generation": None,
        }

    def _load_state(self) -> dict[str, Any]:
        if not self._state_path.exists():
            return self._empty_state()
        try:
            state = json.loads(self._state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise HostMutationScopeCorrupt(f"cannot read mutation authority store: {exc}") from exc
        if not isinstance(state, dict) or state.get("version") != STORE_VERSION:
            raise HostMutationScopeCorrupt("unsupported or malformed mutation authority store")
        for field in ("scopes", "leases", "attempts", "workspaces"):
            if not isinstance(state.get(field), dict):
                raise HostMutationScopeCorrupt(f"authority store field {field!r} is malformed")
        generation = state.get("placement_generation")
        if generation is not None:
            if not isinstance(generation, dict):
                raise HostMutationScopeCorrupt("placement_generation is malformed")
            if not isinstance(generation.get("policy_digest"), str):
                raise HostMutationScopeCorrupt("placement_generation policy_digest is malformed")
            if not isinstance(generation.get("generation"), int) or generation["generation"] <= 0:
                raise HostMutationScopeCorrupt("placement_generation generation is malformed")
        return state

    def _durable_write_state(self, state: dict[str, Any]) -> None:
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
    def _record(state: dict[str, Any], scope_id: str) -> MutationScopeRecord:
        raw = state["scopes"].get(scope_id)
        if raw is None:
            raise HostMutationScopeNotCurrent(f"unknown mutation scope {scope_id}")
        if not isinstance(raw, dict):
            raise HostMutationScopeCorrupt(f"scope entry {scope_id} is malformed")
        record = MutationScopeRecord.from_json(raw)
        if record.scope_id != scope_id:
            raise HostMutationScopeCorrupt("scope index key/id mismatch")
        return record

    @staticmethod
    def _put_record(state: dict[str, Any], record: MutationScopeRecord) -> None:
        state["scopes"][record.scope_id] = record.to_json()

    @staticmethod
    def _normalize_operation_classes(values: Sequence[str]) -> tuple[str, ...]:
        result = tuple(sorted({str(value).strip() for value in values if str(value).strip()}))
        if not result:
            raise ValueError("allowed_operation_classes must not be empty")
        return result

    @staticmethod
    def _placement_generation_state(
        state: dict[str, Any], policy: MutationExecutionPolicy
    ) -> tuple[PlacementGenerationState, bool]:
        current_digest = placement_policy_digest(policy)
        raw = state.get("placement_generation")
        if raw is None:
            current = PlacementGenerationState(current_digest, 1)
            state["placement_generation"] = {
                "policy_digest": current.policy_digest,
                "generation": current.generation,
            }
            return current, True
        previous = PlacementGenerationState(
            policy_digest=str(raw["policy_digest"]),
            generation=int(raw["generation"]),
        )
        current = previous.evolve(current_digest)
        if current != previous:
            state["placement_generation"] = {
                "policy_digest": current.policy_digest,
                "generation": current.generation,
            }
            return current, True
        return current, False

    @staticmethod
    def _assert_index_binding(
        state: dict[str, Any], record: MutationScopeRecord, *, expected_lease: str
    ) -> None:
        lease_scope = state["leases"].get(expected_lease)
        if lease_scope != record.scope_id:
            raise HostMutationScopeConflict("unique lease index does not map to exact current scope")
        attempt_scope = state["attempts"].get(record.attempt_key)
        if attempt_scope != record.scope_id:
            raise HostMutationScopeConflict("Attempt index does not map to exact current scope")
        workspace = state["workspaces"].get(record.exact_workspace_digest)
        if not isinstance(workspace, dict):
            raise HostMutationScopeConflict("exact workspace reverse index is missing")
        if workspace.get("scope_id") != record.scope_id or workspace.get("lease_key") != expected_lease:
            raise HostMutationScopeConflict("exact workspace reverse index binding mismatch")

    @staticmethod
    def _assert_no_competing_nonterminal(
        state: dict[str, Any], current: MutationScopeRecord
    ) -> None:
        for scope_id, raw in state["scopes"].items():
            if scope_id == current.scope_id or not isinstance(raw, dict):
                continue
            other = MutationScopeRecord.from_json(raw)
            if not other.current:
                continue
            if other.unique_lease_key == current.unique_lease_key:
                raise HostMutationScopeConflict("competing non-terminal scope for unique lease")
            if other.exact_workspace_digest == current.exact_workspace_digest:
                raise HostMutationScopeConflict("competing non-terminal lease for exact workspace")

    @staticmethod
    def _mark_expired_if_needed(record: MutationScopeRecord, *, now: datetime) -> MutationScopeRecord:
        if record.current and _parse_time(record.expires_at) <= now:
            return replace(record, state="expired", terminalized_at=_iso(now))
        return record

    def _revalidate_locked(
        self,
        state: dict[str, Any],
        record: MutationScopeRecord,
        policy: MutationExecutionPolicy,
        repository: RepositoryIdentity,
        semantic: SemanticIdentity,
        *,
        provider_protected_roots: Sequence[Path] = (),
        now: datetime,
    ) -> tuple[MutationScopeRecord, bool]:
        record.verify_digest()
        expired = self._mark_expired_if_needed(record, now=now)
        changed = expired != record
        record = expired
        if changed:
            self._put_record(state, record)
        if not record.current:
            raise HostMutationScopeNotCurrent(
                f"scope {record.scope_id} is {record.state}; authority cannot be reactivated"
            )

        current_generation, generation_changed = self._placement_generation_state(state, policy)
        if generation_changed:
            # Placement generation is Host-global durable authority, not a
            # property reconstructed from whichever stale scope was presented.
            self._durable_write_state(state)
        if (
            record.placement_generation != current_generation.generation
            or record.policy_digest != current_generation.policy_digest
        ):
            raise HostMutationScopeBindingMismatch(
                "scope placement generation is not the current Host generation"
            )

        expected_attempt = _attempt_key(record.repository_identity_digest, semantic)
        if expected_attempt != record.attempt_key:
            raise HostMutationScopeBindingMismatch("Attempt identity no longer matches scope")

        expected_key = unique_mutation_lease_key(
            repository_digest=record.repository_identity_digest,
            semantic=semantic,
            placement_generation=record.placement_generation,
            exact_workspace_digest=record.exact_workspace_digest,
        )
        if expected_key != record.unique_lease_key:
            raise HostMutationScopeBindingMismatch("unique lease key no longer matches semantic binding")

        self._assert_index_binding(state, record, expected_lease=expected_key)
        self._assert_no_competing_nonterminal(state, record)

        if (
            record.project_id != semantic.project_id.strip()
            or record.task_id != semantic.task_id.strip()
            or record.run_id != semantic.run_id.strip()
            or record.attempt_id != semantic.attempt_id.strip()
            or (record.slice_id or "") != (semantic.slice_id.strip() if semantic.slice_id else "")
        ):
            raise HostMutationScopeBindingMismatch("semantic lineage mismatch")

        placement = PlacementEvidence(
            placement_ref=record.placement_ref,
            generation=record.placement_generation,
            policy_digest=record.policy_digest,
            exact_future_workspace=Path(record.exact_workspace),
            exact_workspace_digest=record.exact_workspace_digest,
            repository_identity_digest=record.repository_identity_digest,
            semantic_identity_digest=record.semantic_identity_digest,
            protected_inventory_digest=record.protected_inventory_digest,
        )
        revalidate_placement(
            placement,
            policy,
            repository,
            semantic,
            provider_protected_roots=provider_protected_roots,
        )
        return record, changed

    def provision_scope(
        self,
        policy: MutationExecutionPolicy,
        repository: RepositoryIdentity,
        semantic: SemanticIdentity,
        *,
        allowed_operation_classes: Sequence[str],
        provider_protected_roots: Sequence[Path] = (),
        now: datetime | None = None,
    ) -> MutationScopeRecord:
        """Atomically mint or idempotently return the exact current Attempt scope."""
        now = now or _utcnow()
        operations = self._normalize_operation_classes(allowed_operation_classes)

        with _exclusive_file_lock(self._lock_path):
            state = self._load_state()
            generation_state, generation_changed = self._placement_generation_state(state, policy)
            placement = resolve_placement(
                policy,
                repository,
                semantic,
                generation_state=generation_state,
                provider_protected_roots=provider_protected_roots,
            )
            attempt_key = _attempt_key(placement.repository_identity_digest, semantic)
            lease_key = unique_mutation_lease_key(
                repository_digest=placement.repository_identity_digest,
                semantic=semantic,
                placement_generation=placement.generation,
                exact_workspace_digest=placement.exact_workspace_digest,
            )

            authority_root = self.root.resolve(strict=False)
            exact_workspace = placement.exact_future_workspace.resolve(strict=False)
            if (
                authority_root == exact_workspace
                or authority_root.is_relative_to(exact_workspace)
                or exact_workspace.is_relative_to(authority_root)
            ):
                if generation_changed:
                    self._durable_write_state(state)
                raise HostMutationScopeConflict(
                    "provider authority store overlaps exact writable workspace"
                )

            # Attempt is a stronger no-reactivation guard than the lease key:
            # policy/placement drift can legitimately change generation/key, but
            # must never let the same completed Attempt mint fresh authority.
            attempt_scope_id = state["attempts"].get(attempt_key)
            if attempt_scope_id is not None:
                if not isinstance(attempt_scope_id, str):
                    raise HostMutationScopeCorrupt("Attempt index contains non-string scope id")
                existing = self._record(state, attempt_scope_id)
                if existing.attempt_key != attempt_key:
                    raise HostMutationScopeConflict("Attempt index key/scope binding mismatch")
                if (
                    existing.unique_lease_key != lease_key
                    or existing.exact_workspace_digest != placement.exact_workspace_digest
                    or existing.repository_identity_digest != placement.repository_identity_digest
                    or existing.semantic_identity_digest != placement.semantic_identity_digest
                    or existing.placement_generation != placement.generation
                    or existing.policy_digest != placement.policy_digest
                ):
                    if generation_changed:
                        self._durable_write_state(state)
                    raise HostMutationScopeBindingMismatch(
                        "same Attempt resolved to different provider placement authority"
                    )
                try:
                    validated, changed = self._revalidate_locked(
                        state,
                        existing,
                        policy,
                        repository,
                        semantic,
                        provider_protected_roots=provider_protected_roots,
                        now=now,
                    )
                except HostMutationScopeNotCurrent:
                    if generation_changed or state["scopes"].get(existing.scope_id) != existing.to_json():
                        self._durable_write_state(state)
                    raise
                if validated.allowed_operation_classes != operations:
                    raise HostMutationScopeConflict(
                        "same Attempt retry requested a different operation-class authority"
                    )
                if changed or generation_changed:
                    self._durable_write_state(state)
                return validated

            existing_scope_id = state["leases"].get(lease_key)
            if existing_scope_id is not None:
                # A lease without the Attempt index is not safe to repair by guess.
                if generation_changed:
                    self._durable_write_state(state)
                raise HostMutationScopeConflict(
                    "unique lease exists without authoritative Attempt binding"
                )

            workspace_entry = state["workspaces"].get(placement.exact_workspace_digest)
            if workspace_entry is not None:
                if not isinstance(workspace_entry, dict):
                    raise HostMutationScopeCorrupt("workspace reverse index entry is malformed")
                if workspace_entry.get("lease_key") != lease_key:
                    raise HostMutationScopeConflict(
                        "exact workspace is already sealed to a different mutation lease"
                    )
                raise HostMutationScopeConflict(
                    "workspace reverse index exists without its authoritative lease index"
                )

            scope_id = _opaque("mss")
            workspace_id = _opaque("msw")
            issued_at = _iso(now)
            expires_at = _iso(now + timedelta(seconds=policy.scope_ttl_seconds))
            draft = MutationScopeRecord(
                workspace_id=workspace_id,
                scope_id=scope_id,
                generation=1,
                unique_lease_key=lease_key,
                attempt_key=attempt_key,
                state="provisioned",
                project_id=semantic.project_id.strip(),
                task_id=semantic.task_id.strip(),
                run_id=semantic.run_id.strip(),
                attempt_id=semantic.attempt_id.strip(),
                slice_id=semantic.slice_id.strip() if semantic.slice_id else None,
                semantic_identity_digest=placement.semantic_identity_digest,
                repository_identity_digest=placement.repository_identity_digest,
                placement_ref=placement.placement_ref,
                placement_generation=placement.generation,
                policy_digest=placement.policy_digest,
                exact_workspace=str(placement.exact_future_workspace),
                exact_workspace_digest=placement.exact_workspace_digest,
                protected_inventory_digest=placement.protected_inventory_digest,
                allowed_operation_classes=operations,
                issued_at=issued_at,
                expires_at=expires_at,
                scope_digest="",
            )
            record = replace(draft, scope_digest=_digest(draft.immutable_digest_payload()))

            # One authority.json replace is the transaction commit for the record and
            # both indexes. A process crash before replace publishes none of them.
            state["scopes"][scope_id] = record.to_json()
            state["leases"][lease_key] = scope_id
            state["attempts"][attempt_key] = scope_id
            state["workspaces"][placement.exact_workspace_digest] = {
                "lease_key": lease_key,
                "scope_id": scope_id,
            }
            self._assert_index_binding(state, record, expected_lease=lease_key)
            self._assert_no_competing_nonterminal(state, record)
            self._durable_write_state(state)

            # Authoritative read-back before returning minted authority.
            persisted = self._load_state()
            confirmed = self._record(persisted, scope_id)
            self._assert_index_binding(persisted, confirmed, expected_lease=lease_key)
            return confirmed

    def revalidate_scope(
        self,
        scope_id: str,
        generation: int,
        policy: MutationExecutionPolicy,
        repository: RepositoryIdentity,
        semantic: SemanticIdentity,
        *,
        provider_protected_roots: Sequence[Path] = (),
        now: datetime | None = None,
    ) -> MutationScopeRecord:
        now = now or _utcnow()
        with _exclusive_file_lock(self._lock_path):
            state = self._load_state()
            record = self._record(state, scope_id)
            if record.generation != generation:
                raise HostMutationScopeNotCurrent("scope generation is not current")
            try:
                validated, changed = self._revalidate_locked(
                    state,
                    record,
                    policy,
                    repository,
                    semantic,
                    provider_protected_roots=provider_protected_roots,
                    now=now,
                )
            except HostMutationScopeNotCurrent:
                if state["scopes"].get(record.scope_id) != record.to_json():
                    self._durable_write_state(state)
                raise
            if changed:
                self._durable_write_state(state)
            return validated

    def revalidate_scope_for_operation(
        self,
        scope_id: str,
        generation: int,
        policy: MutationExecutionPolicy,
        repository: RepositoryIdentity,
        semantic: SemanticIdentity,
        *,
        required_operation_class: str,
        provider_protected_roots: Sequence[Path] = (),
        now: datetime | None = None,
    ) -> MutationScopeRecord:
        """Revalidate exact authority and require one provider-owned operation class."""
        operation_class = str(required_operation_class).strip()
        if not operation_class:
            raise ValueError("required_operation_class must be a non-empty string")
        record = self.revalidate_scope(
            scope_id,
            generation,
            policy,
            repository,
            semantic,
            provider_protected_roots=provider_protected_roots,
            now=now,
        )
        if operation_class not in record.allowed_operation_classes:
            raise HostMutationScopeOperationNotAllowed(
                f"scope {scope_id} does not authorize operation class {operation_class!r}"
            )
        return record

    def reserve_sandbox_identity(
        self,
        scope_id: str,
        generation: int,
        sandbox_identity: str,
    ) -> MutationScopeRecord:
        """Durably reserve one sandbox SID before any workspace ACL broadening.

        ``sandbox_write_authority_present`` is set pessimistically *before* the
        OS ACL is changed. A crash between reservation and ACL installation can
        therefore never make terminalization assume there is no residual SID.
        """
        if not isinstance(sandbox_identity, str) or not sandbox_identity.strip():
            raise ValueError("sandbox_identity must be a non-empty string")
        sandbox_identity = sandbox_identity.strip()
        with _exclusive_file_lock(self._lock_path):
            state = self._load_state()
            record = self._record(state, scope_id)
            if record.generation != generation or not record.current:
                raise HostMutationScopeNotCurrent("scope generation/state is not current")
            self._assert_index_binding(state, record, expected_lease=record.unique_lease_key)
            self._assert_no_competing_nonterminal(state, record)
            if record.sandbox_identity not in (None, sandbox_identity):
                raise HostMutationScopeConflict(
                    "scope is already reserved to a different sandbox identity"
                )
            updated = replace(
                record,
                state="active",
                sandbox_identity=sandbox_identity,
                sandbox_write_authority_present=True,
            )
            self._put_record(state, updated)
            self._durable_write_state(state)
            confirmed = self._record(self._load_state(), scope_id)
            if (
                confirmed.sandbox_identity != sandbox_identity
                or not confirmed.sandbox_write_authority_present
            ):
                raise HostMutationScopeCorrupt("sandbox identity reservation read-back failed")
            return confirmed

    def bind_runtime_process(
        self,
        scope_id: str,
        generation: int,
        sandbox_identity: str,
        *,
        job_id: str,
        process_id: int,
    ) -> MutationScopeRecord:
        """Durably bind the still-suspended Job/root process to the lease."""
        if not job_id or process_id <= 0:
            raise ValueError("job_id and positive process_id are required")
        with _exclusive_file_lock(self._lock_path):
            state = self._load_state()
            record = self._record(state, scope_id)
            if record.generation != generation or not record.current:
                raise HostMutationScopeNotCurrent("scope generation/state is not current")
            if (
                record.sandbox_identity != sandbox_identity
                or not record.sandbox_write_authority_present
            ):
                raise HostMutationScopeConflict("runtime process does not match active sandbox authority")
            self._assert_index_binding(state, record, expected_lease=record.unique_lease_key)
            self._assert_no_competing_nonterminal(state, record)
            jobs = tuple(sorted(set(record.active_job_ids) | {str(job_id)}))
            processes = tuple(sorted(set(record.active_process_ids) | {str(process_id)}))
            updated = replace(record, active_job_ids=jobs, active_process_ids=processes)
            self._put_record(state, updated)
            self._durable_write_state(state)
            return self._record(self._load_state(), scope_id)

    def release_runtime_process(
        self,
        scope_id: str,
        generation: int,
        *,
        job_id: str,
        process_id: int,
    ) -> MutationScopeRecord:
        """Remove a Job/PID binding only after OS read-back proves it quiescent."""
        with _exclusive_file_lock(self._lock_path):
            state = self._load_state()
            record = self._record(state, scope_id)
            if record.generation != generation:
                raise HostMutationScopeNotCurrent("scope generation is not current")
            jobs = tuple(value for value in record.active_job_ids if value != str(job_id))
            processes = tuple(
                value for value in record.active_process_ids if value != str(process_id)
            )
            updated = replace(record, active_job_ids=jobs, active_process_ids=processes)
            self._put_record(state, updated)
            self._durable_write_state(state)
            return self._record(self._load_state(), scope_id)

    def reserve_runtime_read_authority(
        self,
        scope_id: str,
        generation: int,
        sandbox_identity: str,
        runtime_root: str,
    ) -> MutationScopeRecord:
        """Pessimistically record one runtime-root SID authority before ACL grant."""
        if not isinstance(runtime_root, str) or not runtime_root.strip():
            raise ValueError("runtime_root must be a non-empty string")
        runtime_root = runtime_root.strip()
        with _exclusive_file_lock(self._lock_path):
            state = self._load_state()
            record = self._record(state, scope_id)
            if record.generation != generation or record.state != "active":
                raise HostMutationScopeNotCurrent(
                    "runtime-read authority can only be reserved on the active scope generation"
                )
            if (
                record.sandbox_identity != sandbox_identity
                or not record.sandbox_write_authority_present
            ):
                raise HostMutationScopeConflict(
                    "runtime-read authority does not match active sandbox identity"
                )
            roots = list(record.runtime_read_authority_roots)
            if not any(value.casefold() == runtime_root.casefold() for value in roots):
                roots.append(runtime_root)
            updated = replace(
                record,
                runtime_read_authority_roots=tuple(
                    sorted(roots, key=str.casefold)
                ),
            )
            self._put_record(state, updated)
            self._durable_write_state(state)
            confirmed = self._record(self._load_state(), scope_id)
            if not any(
                value.casefold() == runtime_root.casefold()
                for value in confirmed.runtime_read_authority_roots
            ):
                raise HostMutationScopeCorrupt(
                    "runtime-read authority reservation read-back failed"
                )
            return confirmed

    def clear_runtime_read_authority(
        self,
        scope_id: str,
        generation: int,
        sandbox_identity: str,
        runtime_root: str,
    ) -> MutationScopeRecord:
        """Clear one exact runtime-root marker only after OS SID-removal read-back."""
        if not isinstance(runtime_root, str) or not runtime_root.strip():
            raise ValueError("runtime_root must be a non-empty string")
        runtime_root = runtime_root.strip()
        with _exclusive_file_lock(self._lock_path):
            state = self._load_state()
            record = self._record(state, scope_id)
            if record.generation != generation:
                raise HostMutationScopeNotCurrent("scope generation is not current")
            if record.state == "terminal":
                raise HostMutationScopeNotCurrent(
                    "terminal scope cannot clear runtime-read authority"
                )
            if record.sandbox_identity != sandbox_identity:
                raise HostMutationScopeConflict(
                    "runtime-read cleanup identity mismatch"
                )
            remaining = tuple(
                value
                for value in record.runtime_read_authority_roots
                if value.casefold() != runtime_root.casefold()
            )
            updated = replace(record, runtime_read_authority_roots=remaining)
            self._put_record(state, updated)
            self._durable_write_state(state)
            confirmed = self._record(self._load_state(), scope_id)
            if any(
                value.casefold() == runtime_root.casefold()
                for value in confirmed.runtime_read_authority_roots
            ):
                raise HostMutationScopeCorrupt(
                    "runtime-read authority cleanup read-back failed"
                )
            return confirmed

    def clear_sandbox_write_authority(
        self,
        scope_id: str,
        generation: int,
        sandbox_identity: str,
    ) -> MutationScopeRecord:
        """Record ACL/profile cleanup after no Job/process binding remains."""
        with _exclusive_file_lock(self._lock_path):
            state = self._load_state()
            record = self._record(state, scope_id)
            if record.generation != generation:
                raise HostMutationScopeNotCurrent("scope generation is not current")
            if record.sandbox_identity != sandbox_identity:
                raise HostMutationScopeConflict("sandbox cleanup identity mismatch")
            if record.active_job_ids or record.active_process_ids:
                raise HostMutationScopeStillActive(
                    "cannot clear sandbox write authority while Job/process bindings remain"
                )
            updated = replace(record, sandbox_write_authority_present=False)
            self._put_record(state, updated)
            self._durable_write_state(state)
            return self._record(self._load_state(), scope_id)

    def revoke_scope(self, scope_id: str, generation: int) -> MutationScopeRecord:
        """Fail closed after sandbox bootstrap failure; the Attempt cannot reactivate."""
        with _exclusive_file_lock(self._lock_path):
            state = self._load_state()
            record = self._record(state, scope_id)
            if record.generation != generation:
                raise HostMutationScopeNotCurrent("scope generation is not current")
            if record.state == "terminal":
                return record
            revoked = replace(record, state="revoked")
            self._put_record(state, revoked)
            self._durable_write_state(state)
            return self._record(self._load_state(), scope_id)

    def terminalize_scope(
        self,
        scope_id: str,
        generation: int,
        policy: MutationExecutionPolicy,
        repository: RepositoryIdentity,
        semantic: SemanticIdentity,
        *,
        provider_protected_roots: Sequence[Path] = (),
        runtime_cleanup: Callable[[MutationScopeRecord], MutationRuntimeClosure] | None = None,
        now: datetime | None = None,
    ) -> MutationScopeRecord:
        """Revoke admission, close OS authority, then durably mark terminal.

        Runtime cleanup is deliberately two-phase. The lease is first persisted
        as ``revoked`` under the authority lock, which prevents any new spawn.
        Only then may OS cleanup run. A crash/failure during cleanup therefore
        leaves a durable fail-closed revoked scope with residual authority still
        recorded instead of publishing a false terminal success.
        """
        now = now or _utcnow()
        cleanup_record: MutationScopeRecord | None = None

        def validate_sealed_binding(state: dict[str, Any], record: MutationScopeRecord) -> str:
            if record.generation != generation:
                raise HostMutationScopeNotCurrent("scope generation is not current")
            if record.state == "terminal":
                raise HostMutationScopeNotCurrent("scope is already terminal")
            record.verify_digest()
            if record.repository_identity_digest != _digest(repository.canonical):
                raise HostMutationScopeBindingMismatch("repository identity mismatch")
            expected_attempt = _attempt_key(record.repository_identity_digest, semantic)
            if expected_attempt != record.attempt_key:
                raise HostMutationScopeBindingMismatch("Attempt identity mismatch")
            expected_lease = unique_mutation_lease_key(
                repository_digest=record.repository_identity_digest,
                semantic=semantic,
                placement_generation=record.placement_generation,
                exact_workspace_digest=record.exact_workspace_digest,
            )
            if expected_lease != record.unique_lease_key:
                raise HostMutationScopeBindingMismatch("sealed unique lease identity mismatch")
            if (
                record.project_id != semantic.project_id.strip()
                or record.task_id != semantic.task_id.strip()
                or record.run_id != semantic.run_id.strip()
                or record.attempt_id != semantic.attempt_id.strip()
                or (record.slice_id or "")
                != (semantic.slice_id.strip() if semantic.slice_id else "")
            ):
                raise HostMutationScopeBindingMismatch("semantic lineage mismatch")
            self._assert_index_binding(state, record, expected_lease=expected_lease)
            self._assert_no_competing_nonterminal(state, record)
            return expected_lease

        with _exclusive_file_lock(self._lock_path):
            state = self._load_state()
            record = self._record(state, scope_id)

            # Advance Host-global placement generation if policy drifted, while
            # cleaning the exact OLD sealed binding. Cleanup must remain possible
            # even when normal mutation admission has become stale.
            _, generation_changed = self._placement_generation_state(state, policy)
            expected_lease = validate_sealed_binding(state, record)
            if generation_changed:
                self._durable_write_state(state)

            has_runtime_authority = bool(
                record.active_job_ids
                or record.active_process_ids
                or record.sandbox_write_authority_present
                or record.runtime_read_authority_roots
            )
            if has_runtime_authority:
                if runtime_cleanup is None:
                    if record.active_job_ids or record.active_process_ids:
                        raise HostMutationScopeStillActive(
                            "bound Job/process authority remains; terminalization requires OS cleanup"
                        )
                    raise HostMutationResidualAuthorityDetected(
                        "sandbox/runtime-read authority remains; terminalization requires OS cleanup"
                    )
                cleanup_record = replace(record, state="revoked")
                self._put_record(state, cleanup_record)
                self._durable_write_state(state)
                persisted = self._record(self._load_state(), scope_id)
                if persisted.state != "revoked":
                    raise HostMutationScopeTerminalizationFailed(
                        "pre-cleanup admission revocation did not persist"
                    )
                cleanup_record = persisted
            else:
                terminal = replace(record, state="terminal", terminalized_at=_iso(now))
                self._put_record(state, terminal)
                self._durable_write_state(state)
                persisted = self._load_state()
                confirmed = self._record(persisted, scope_id)
                if confirmed.state != "terminal":
                    raise HostMutationScopeTerminalizationFailed(
                        "authoritative read-back did not observe terminal state"
                    )
                self._assert_index_binding(
                    persisted, confirmed, expected_lease=expected_lease
                )
                return confirmed

        assert cleanup_record is not None and runtime_cleanup is not None
        closure = runtime_cleanup(cleanup_record)
        if not isinstance(closure, MutationRuntimeClosure):
            raise HostMutationScopeTerminalizationFailed(
                "runtime cleanup did not return authoritative closure evidence"
            )
        if closure.sandbox_identity != cleanup_record.sandbox_identity:
            raise HostMutationScopeTerminalizationFailed(
                "runtime cleanup sandbox identity does not match sealed scope"
            )
        if closure.active_job_ids or closure.active_process_ids:
            raise HostMutationScopeStillActive(
                "runtime cleanup still reports active Job/process authority"
            )
        if closure.sandbox_write_authority_present:
            raise HostMutationResidualAuthorityDetected(
                "runtime cleanup still reports sandbox write authority"
            )
        if closure.runtime_read_authority_roots:
            raise HostMutationResidualAuthorityDetected(
                "runtime cleanup still reports runtime-read authority"
            )

        with _exclusive_file_lock(self._lock_path):
            state = self._load_state()
            record = self._record(state, scope_id)
            expected_lease = validate_sealed_binding(state, record)
            if record.state != "revoked":
                raise HostMutationScopeTerminalizationFailed(
                    "scope changed state while OS cleanup was in progress"
                )
            if record.scope_digest != cleanup_record.scope_digest:
                raise HostMutationScopeTerminalizationFailed(
                    "sealed scope identity changed while OS cleanup was in progress"
                )
            terminal = replace(
                record,
                state="terminal",
                active_job_ids=closure.active_job_ids,
                active_process_ids=closure.active_process_ids,
                sandbox_write_authority_present=closure.sandbox_write_authority_present,
                runtime_read_authority_roots=closure.runtime_read_authority_roots,
                terminalized_at=_iso(now),
            )
            self._put_record(state, terminal)
            self._durable_write_state(state)

            persisted = self._load_state()
            confirmed = self._record(persisted, scope_id)
            if (
                confirmed.state != "terminal"
                or confirmed.active_job_ids
                or confirmed.active_process_ids
                or confirmed.sandbox_write_authority_present
                or confirmed.runtime_read_authority_roots
            ):
                raise HostMutationScopeTerminalizationFailed(
                    "authoritative read-back did not prove terminal residual-authority closure"
                )
            self._assert_index_binding(
                persisted, confirmed, expected_lease=expected_lease
            )
            for other_id, raw in persisted["scopes"].items():
                if other_id == confirmed.scope_id or not isinstance(raw, dict):
                    continue
                other = MutationScopeRecord.from_json(raw)
                if other.current and (
                    other.unique_lease_key == confirmed.unique_lease_key
                    or other.exact_workspace_digest == confirmed.exact_workspace_digest
                ):
                    raise HostMutationScopeTerminalizationFailed(
                        "competing authority remained after terminalization"
                    )
            return confirmed

    def read_scope(self, scope_id: str) -> MutationScopeRecord:
        """Read authoritative state without changing lifecycle state."""
        with _exclusive_file_lock(self._lock_path):
            return self._record(self._load_state(), scope_id)

    def read_bound_scope(
        self,
        scope_id: str,
        generation: int,
        repository: RepositoryIdentity,
        semantic: SemanticIdentity,
    ) -> MutationScopeRecord:
        """Read exact current/terminal authority without mutating lifecycle state."""
        with _exclusive_file_lock(self._lock_path):
            record = self._record(self._load_state(), scope_id)
            if record.generation != generation:
                raise HostMutationScopeNotCurrent("scope generation is not current")
            if record.repository_identity_digest != _digest(repository.canonical):
                raise HostMutationScopeBindingMismatch("repository identity mismatch")
            if record.semantic_identity_digest != _digest(semantic.canonical):
                raise HostMutationScopeBindingMismatch("semantic identity mismatch")
            if (
                record.project_id != semantic.project_id.strip()
                or record.task_id != semantic.task_id.strip()
                or record.run_id != semantic.run_id.strip()
                or record.attempt_id != semantic.attempt_id.strip()
                or (record.slice_id or "")
                != (semantic.slice_id.strip() if semantic.slice_id else "")
            ):
                raise HostMutationScopeBindingMismatch("semantic lineage mismatch")
            expected_attempt = _attempt_key(record.repository_identity_digest, semantic)
            if record.attempt_key != expected_attempt:
                raise HostMutationScopeBindingMismatch("Attempt identity mismatch")
            return record
