"""Security-critical write-ahead mutation audit and forensic script evidence.

Unlike ``local_audit`` this module is fail-closed. A scoped mutation may not
materialize a workspace or spawn untrusted code until OPERATION_STARTED is
persisted and flushed. PROCESS_SPAWNED is likewise committed while the child is
still suspended; callers must terminate rather than resume on audit failure.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import threading
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sentinelx_core.request_context import MutationLineage, RequestContext

JOURNAL_VERSION = 1
EVENT_STARTED = "OPERATION_STARTED"
EVENT_SPAWNED = "PROCESS_SPAWNED"
EVENT_FINISHED = "OPERATION_FINISHED"
FINISH_STATES = frozenset({"succeeded", "failed", "timeout", "cancelled"})


class MutationAuditError(RuntimeError):
    code = "MutationAuditError"


class MutationAuditDurabilityError(MutationAuditError):
    code = "MutationAuditDurabilityError"


class MutationEvidenceError(MutationAuditError):
    code = "MutationEvidenceError"


class MutationAuditIdentityMismatch(MutationAuditError):
    code = "MutationAuditIdentityMismatch"


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_digest(value: object) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return _sha256(body.encode("utf-8"))


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


_LOCKS_GUARD = threading.Lock()
_LOCAL_LOCKS: dict[str, threading.RLock] = {}


def _local_lock_for(path: Path) -> threading.RLock:
    key = str(path.resolve(strict=False)).casefold()
    with _LOCKS_GUARD:
        return _LOCAL_LOCKS.setdefault(key, threading.RLock())


@contextmanager
def _exclusive_file_lock(path: Path) -> Iterator[None]:
    """Serialize journal/evidence metadata across threads and processes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with _local_lock_for(path):
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


@dataclass(frozen=True)
class ForensicScriptEvidence:
    artifact_ref: str
    sha256: str
    size_bytes: int
    created_at: str
    retained_until: str
    _artifact_path: Path

    def audit_dict(self) -> dict[str, Any]:
        """Public journal projection: never expose the broker filesystem path."""
        return {
            "artifact_ref": self.artifact_ref,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "created_at": self.created_at,
            "retained_until": self.retained_until,
        }


@dataclass(frozen=True)
class MutationAuditBinding:
    request_id: str
    op: str
    opaque_ref: str | None
    lineage: MutationLineage
    scope_id: str
    scope_generation: int
    workspace_id: str
    unique_lease_key: str
    job_id: str | None = None

    @classmethod
    def from_context(
        cls,
        context: RequestContext,
        lineage: MutationLineage,
        *,
        scope_id: str,
        scope_generation: int,
        workspace_id: str,
        unique_lease_key: str,
        job_id: str | None = None,
    ) -> MutationAuditBinding:
        if scope_generation <= 0:
            raise ValueError("scope_generation must be positive")
        for field, value in (
            ("scope_id", scope_id),
            ("workspace_id", workspace_id),
            ("unique_lease_key", unique_lease_key),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be a non-empty string")
        return cls(
            request_id=context.request_id,
            op=context.op,
            opaque_ref=context.opaque_ref,
            lineage=lineage,
            scope_id=scope_id.strip(),
            scope_generation=scope_generation,
            workspace_id=workspace_id.strip(),
            unique_lease_key=unique_lease_key.strip(),
            job_id=job_id.strip() if isinstance(job_id, str) and job_id.strip() else None,
        )

    def audit_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "op": self.op,
            "opaque_ref": self.opaque_ref,
            "lineage": self.lineage.to_audit_dict(),
            "scope_id": self.scope_id,
            "scope_generation": self.scope_generation,
            "workspace_id": self.workspace_id,
            "unique_lease_key": self.unique_lease_key,
            "job_id": self.job_id,
        }

    @property
    def digest(self) -> str:
        return _canonical_digest(self.audit_dict())


@dataclass(frozen=True)
class MutationAuditStart:
    operation_id: str
    event_ref: str
    binding: MutationAuditBinding
    binding_digest: str
    evidence: ForensicScriptEvidence
    started_at: str

    def background_identity(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "binding_digest": self.binding_digest,
            "request_id": self.binding.request_id,
            "scope_id": self.binding.scope_id,
            "scope_generation": self.binding.scope_generation,
            "workspace_id": self.binding.workspace_id,
            "semantic_digest": self.binding.lineage.digest,
            "job_id": self.binding.job_id,
        }


@dataclass(frozen=True)
class MutationAuditSpawn:
    operation_id: str
    event_ref: str
    pid: int
    job_binding: str
    recorded_at: str


class ForensicEvidenceStore:
    """Broker-only retained script bytes with durable hash/read-back verification."""

    def __init__(self, state_root: Path, *, retention_days: int) -> None:
        if retention_days <= 0:
            raise ValueError("retention_days must be positive")
        self.root = state_root.resolve(strict=False) / "mutation-evidence"
        self.root.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days
        self._lock_path = self.root / "evidence.lock"
        try:
            self.root.chmod(0o700)
        except OSError:
            pass

    def retain(self, exact_bytes: bytes, *, now: datetime | None = None) -> ForensicScriptEvidence:
        if not isinstance(exact_bytes, bytes) or not exact_bytes:
            raise MutationEvidenceError("forensic script bytes must be non-empty")
        now = now or _utcnow()
        digest = _sha256(exact_bytes)
        token = secrets.token_hex(12)
        artifact_name = f"{digest[:20]}-{token}.script"
        artifact_path = self.root / artifact_name
        retained_until = now + timedelta(days=self.retention_days)

        with _exclusive_file_lock(self._lock_path):
            temp = self.root / f".{artifact_name}.{secrets.token_hex(6)}.tmp"
            try:
                with temp.open("xb") as handle:
                    handle.write(exact_bytes)
                    handle.flush()
                    os.fsync(handle.fileno())
                try:
                    temp.chmod(0o600)
                except OSError:
                    pass
                os.replace(temp, artifact_path)
                _fsync_directory(self.root)
            except Exception as exc:
                try:
                    temp.unlink(missing_ok=True)
                except OSError:
                    pass
                raise MutationEvidenceError(f"cannot persist forensic script evidence: {exc}") from exc

            try:
                persisted = artifact_path.read_bytes()
            except OSError as exc:
                raise MutationEvidenceError(f"cannot read back forensic script evidence: {exc}") from exc
            if _sha256(persisted) != digest or persisted != exact_bytes:
                raise MutationEvidenceError("forensic script evidence read-back hash mismatch")

        return ForensicScriptEvidence(
            artifact_ref=f"mutation-evidence:{artifact_name}",
            sha256=digest,
            size_bytes=len(exact_bytes),
            created_at=_iso(now),
            retained_until=_iso(retained_until),
            _artifact_path=artifact_path,
        )

    def read_verified(self, evidence: ForensicScriptEvidence) -> bytes:
        if not evidence._artifact_path.is_relative_to(self.root):
            raise MutationEvidenceError("forensic artifact escaped evidence root")
        try:
            data = evidence._artifact_path.read_bytes()
        except OSError as exc:
            raise MutationEvidenceError(f"cannot read retained forensic artifact: {exc}") from exc
        if len(data) != evidence.size_bytes or _sha256(data) != evidence.sha256:
            raise MutationEvidenceError("retained forensic artifact no longer matches sealed hash")
        return data

    def materialize_verified(self, evidence: ForensicScriptEvidence, destination: Path) -> str:
        """Copy exact retained bytes into an already-created trusted workspace."""
        data = self.read_verified(evidence)
        destination = destination.resolve(strict=False)
        if not destination.parent.exists():
            raise MutationEvidenceError("trusted execution workspace must exist before materialization")
        try:
            with destination.open("xb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
        except Exception as exc:
            raise MutationEvidenceError(f"cannot materialize retained script evidence: {exc}") from exc
        if _sha256(destination.read_bytes()) != evidence.sha256:
            raise MutationEvidenceError("materialized script hash mismatch")
        return evidence.sha256

    def prune_expired(self, *, now: datetime | None = None) -> int:
        """Delete only artifacts older than the configured retention window."""
        now = now or _utcnow()
        cutoff = now - timedelta(days=self.retention_days)
        removed = 0
        with _exclusive_file_lock(self._lock_path):
            for path in self.root.glob("*.script"):
                try:
                    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
                    if modified < cutoff:
                        path.unlink()
                        removed += 1
                except OSError:
                    continue
            if removed:
                _fsync_directory(self.root)
        return removed


class MutationAuditJournal:
    """Append-only fail-closed mutation lifecycle journal."""

    def __init__(self, state_root: Path, *, evidence_retention_days: int = 30) -> None:
        self.root = state_root.resolve(strict=False) / "mutation-audit"
        self.root.mkdir(parents=True, exist_ok=True)
        self.journal_path = self.root / "journal.jsonl"
        self._lock_path = self.root / "journal.lock"
        self.evidence = ForensicEvidenceStore(
            state_root, retention_days=evidence_retention_days
        )
        try:
            self.root.chmod(0o700)
        except OSError:
            pass

    def _durable_append(self, event: Mapping[str, Any]) -> None:
        line = (json.dumps(event, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")
        try:
            with _exclusive_file_lock(self._lock_path):
                with self.journal_path.open("ab") as handle:
                    handle.write(line)
                    handle.flush()
                    os.fsync(handle.fileno())
                _fsync_directory(self.root)
        except Exception as exc:
            raise MutationAuditDurabilityError(f"mutation audit durable append failed: {exc}") from exc

    def begin(
        self,
        binding: MutationAuditBinding,
        evidence: ForensicScriptEvidence,
        *,
        now: datetime | None = None,
    ) -> MutationAuditStart:
        now = now or _utcnow()
        # START may reference only evidence that is already durably retained and
        # whose exact bytes still match the sealed hash.
        self.evidence.read_verified(evidence)
        operation_id = f"mao_{secrets.token_urlsafe(18)}"
        event_ref = f"mutation-audit:{operation_id}:start"
        event = {
            "version": JOURNAL_VERSION,
            "event": EVENT_STARTED,
            "event_ref": event_ref,
            "operation_id": operation_id,
            "timestamp": _iso(now),
            "binding": binding.audit_dict(),
            "binding_digest": binding.digest,
            "script_evidence": evidence.audit_dict(),
        }
        self._durable_append(event)
        return MutationAuditStart(
            operation_id=operation_id,
            event_ref=event_ref,
            binding=binding,
            binding_digest=binding.digest,
            evidence=evidence,
            started_at=_iso(now),
        )

    def _assert_start_identity(self, start: MutationAuditStart) -> None:
        if start.binding.digest != start.binding_digest:
            raise MutationAuditIdentityMismatch("mutation audit binding digest changed after START")
        if start.evidence.sha256 != _sha256(self.evidence.read_verified(start.evidence)):
            raise MutationAuditIdentityMismatch("forensic evidence changed after START")

    def record_spawn(
        self,
        start: MutationAuditStart,
        *,
        pid: int,
        job_binding: str,
        sandbox_identity: str | None = None,
        now: datetime | None = None,
    ) -> MutationAuditSpawn:
        self._assert_start_identity(start)
        if pid <= 0:
            raise ValueError("pid must be positive")
        if not job_binding or not job_binding.strip():
            raise ValueError("job_binding must be non-empty")
        now = now or _utcnow()
        event_ref = f"mutation-audit:{start.operation_id}:spawn"
        self._durable_append(
            {
                "version": JOURNAL_VERSION,
                "event": EVENT_SPAWNED,
                "event_ref": event_ref,
                "operation_id": start.operation_id,
                "timestamp": _iso(now),
                "binding_digest": start.binding_digest,
                "pid": pid,
                "job_binding": job_binding,
                "sandbox_identity": sandbox_identity,
            }
        )
        return MutationAuditSpawn(
            operation_id=start.operation_id,
            event_ref=event_ref,
            pid=pid,
            job_binding=job_binding,
            recorded_at=_iso(now),
        )

    def commit_spawn_before_resume(
        self,
        start: MutationAuditStart,
        *,
        pid: int,
        job_binding: str,
        sandbox_identity: str | None,
        terminate_suspended: Callable[[], None],
        resume_suspended: Callable[[], None],
    ) -> MutationAuditSpawn:
        """Persist SPAWN before the first untrusted instruction can execute."""
        try:
            spawn = self.record_spawn(
                start,
                pid=pid,
                job_binding=job_binding,
                sandbox_identity=sandbox_identity,
            )
        except Exception:
            terminate_suspended()
            raise
        resume_suspended()
        return spawn

    def finish(
        self,
        start: MutationAuditStart,
        *,
        status: str,
        returncode: int | None = None,
        error_code: str | None = None,
        now: datetime | None = None,
    ) -> str:
        self._assert_start_identity(start)
        if status not in FINISH_STATES:
            raise ValueError(f"invalid mutation finish status: {status}")
        now = now or _utcnow()
        event_ref = f"mutation-audit:{start.operation_id}:finish:{secrets.token_hex(4)}"
        self._durable_append(
            {
                "version": JOURNAL_VERSION,
                "event": EVENT_FINISHED,
                "event_ref": event_ref,
                "operation_id": start.operation_id,
                "timestamp": _iso(now),
                "binding_digest": start.binding_digest,
                "status": status,
                "returncode": returncode,
                "error_code": error_code,
            }
        )
        return event_ref

    def read_events(self, operation_id: str | None = None) -> list[dict[str, Any]]:
        """Test/operator seam. Malformed lines fail closed rather than disappearing."""
        if not self.journal_path.exists():
            return []
        events: list[dict[str, Any]] = []
        for line in self.journal_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise MutationAuditDurabilityError("mutation audit journal is corrupt") from exc
            if operation_id is None or event.get("operation_id") == operation_id:
                events.append(event)
        return events
