"""Provider-owned DevForge execution-workspace placement evidence.

This module is deliberately placement-only.  It never creates the execution
workspace, never acquires repository source, and never grants filesystem
mutation authority.  Its job is to turn the current Host DevForge workspace
binding plus semantic execution identity into durable evidence that can be
sealed by the existing mutation-scope authority.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import threading
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator, Sequence
from urllib.parse import urlsplit

from sentinelx_core.mutation_placement import (
    HostMutationScopeBindingMismatch,
    PlacementEvidence,
    RepositoryIdentity,
    SemanticIdentity,
)
from sentinelx_core.policy import MutationExecutionPolicy, Policy

PLACEMENT_POLICY = "host-workspace-layout-repository-placement-v1"
PLACEMENT_KIND = "devforge_execution_workspace_v1"
PLACEMENT_STATE = "PlacementResolved"
PLACEMENT_OPERATION = "execution_workspace"
PLACEMENT_ROLE = "execution_root"
STORE_VERSION = 1


class DevforgeWorkspacePlacementError(RuntimeError):
    code = "WorkspacePlacementBlocked"


class WorkspacePlacementMismatch(DevforgeWorkspacePlacementError):
    code = "WorkspacePlacementMismatch"


class WorkspacePlacementEscape(DevforgeWorkspacePlacementError):
    code = "WorkspacePlacementEscape"


class WorkspacePlacementStale(DevforgeWorkspacePlacementError):
    code = "WorkspacePlacementStale"


class WorkspacePlacementCorrupt(DevforgeWorkspacePlacementError):
    code = "WorkspacePlacementCorrupt"


def _digest(value: object) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _path_text(path: Path) -> str:
    return str(path.resolve(strict=False))


def _iso_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(_path_text(left)) == os.path.normcase(_path_text(right))


def _overlap(left: Path, right: Path) -> bool:
    left = left.resolve(strict=False)
    right = right.resolve(strict=False)
    return left == right or left.is_relative_to(right) or right.is_relative_to(left)


_INVALID_WINDOWS_SEGMENT = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _safe_segment(value: str, field_name: str) -> str:
    text = str(value or "").strip()
    if not text or text in {".", ".."}:
        raise DevforgeWorkspacePlacementError(f"{field_name} must be one non-empty path segment")
    if _INVALID_WINDOWS_SEGMENT.search(text) or "/" in text or "\\" in text:
        raise DevforgeWorkspacePlacementError(f"{field_name} contains path syntax")
    if text.endswith((".", " ")):
        raise DevforgeWorkspacePlacementError(f"{field_name} has an unsafe trailing character")
    return text


def _repository_segments(repository: RepositoryIdentity) -> tuple[str, str]:
    parsed = urlsplit(repository.canonical)
    parts = tuple(part for part in parsed.path.split("/") if part)
    if len(parts) != 2:
        raise DevforgeWorkspacePlacementError(
            "DevForge V1 repository identity must resolve to exactly owner/repository"
        )
    return _safe_segment(parts[0], "repository.owner"), _safe_segment(
        parts[1], "repository.name"
    )


def _host_roots(policy: Policy) -> tuple[Path, Path]:
    location = policy.locations.get("devforge_workspace_root")
    if location is None:
        raise DevforgeWorkspacePlacementError(
            "locations.devforge_workspace_root is not configured"
        )
    text = str(location.path or "").strip()
    if not text:
        raise DevforgeWorkspacePlacementError(
            "locations.devforge_workspace_root is empty"
        )
    root = Path(text).expanduser()
    if not root.is_absolute():
        raise DevforgeWorkspacePlacementError(
            "locations.devforge_workspace_root must be absolute"
        )
    try:
        workspace_root = root.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise DevforgeWorkspacePlacementError(
            f"locations.devforge_workspace_root cannot be canonicalized: {exc}"
        ) from exc
    execution_root = (workspace_root / "workspaces").resolve(strict=False)
    if execution_root == workspace_root or not execution_root.is_relative_to(workspace_root):
        raise WorkspacePlacementEscape("derived execution_root escaped Host workspace_root")
    return workspace_root, execution_root


def _protected_inventory(
    host_policy: Policy,
    *,
    provider_protected_roots: Sequence[Path] = (),
) -> tuple[str, ...]:
    roots = {_path_text(path) for path in host_policy.mutation_execution.protected_roots}
    roots.update(_path_text(path) for path in provider_protected_roots)
    roots.update(_path_text(spec.root) for spec in host_policy.mutation_execution.canonical_repositories)
    return tuple(sorted(roots, key=str.casefold))


def _assert_protected_separation(
    execution_root: Path,
    exact_workspace: Path,
    inventory: Sequence[str],
) -> None:
    for raw in inventory:
        protected = Path(raw).resolve(strict=False)
        if _overlap(execution_root, protected) or _overlap(exact_workspace, protected):
            raise WorkspacePlacementEscape(
                "DevForge execution placement overlaps a protected/canonical root"
            )


@dataclass(frozen=True)
class DevforgeWorkspacePlacementReceipt:
    receipt_id: str
    policy: str
    state: str
    operation: str
    repository: str
    repository_identity_digest: str
    semantic_identity_digest: str
    placement_role: str
    workspace_root_digest: str
    execution_root_digest: str
    target_path: str
    target_digest: str
    protected_inventory_digest: str
    placement_compliant: bool
    binding_generation: int
    binding_digest: str
    issued_at: str

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, value: dict[str, Any]) -> "DevforgeWorkspacePlacementReceipt":
        try:
            receipt = cls(**value)
        except (TypeError, ValueError) as exc:
            raise WorkspacePlacementCorrupt(f"invalid placement receipt: {exc}") from exc
        if (
            receipt.policy != PLACEMENT_POLICY
            or receipt.state != PLACEMENT_STATE
            or receipt.operation != PLACEMENT_OPERATION
            or receipt.placement_role != PLACEMENT_ROLE
            or not receipt.placement_compliant
            or receipt.binding_generation <= 0
        ):
            raise WorkspacePlacementCorrupt("placement receipt has invalid fixed semantics")
        return receipt


_LOCAL_LOCKS_GUARD = threading.Lock()
_LOCAL_LOCKS: dict[str, threading.RLock] = {}


def _local_lock(path: Path) -> threading.RLock:
    key = str(path.resolve(strict=False)).casefold()
    with _LOCAL_LOCKS_GUARD:
        return _LOCAL_LOCKS.setdefault(key, threading.RLock())


@contextmanager
def _exclusive_file_lock(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _local_lock(path):
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


class DevforgeWorkspacePlacementReceiptStore:
    """Durable evidence-only Placement Receipt store.

    This store never grants mutation authority.  Its result must be handed to
    MutationScopeStore separately, after the durable receipt is read back.
    """

    def __init__(self, state_root: Path) -> None:
        self.root = state_root.resolve(strict=False) / "devforge-workspace-placement"
        self.root.mkdir(parents=True, exist_ok=True)
        self._state_path = self.root / "receipts.json"
        self._lock_path = self.root / "receipts.lock"

    @staticmethod
    def _empty_state() -> dict[str, Any]:
        return {"version": STORE_VERSION, "binding": None, "receipts": {}}

    def _load(self) -> dict[str, Any]:
        if not self._state_path.exists():
            return self._empty_state()
        try:
            state = json.loads(self._state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise WorkspacePlacementCorrupt(f"cannot read placement receipt store: {exc}") from exc
        if not isinstance(state, dict) or state.get("version") != STORE_VERSION:
            raise WorkspacePlacementCorrupt("unsupported placement receipt store")
        if not isinstance(state.get("receipts"), dict):
            raise WorkspacePlacementCorrupt("placement receipt index is malformed")
        binding = state.get("binding")
        if binding is not None and (
            not isinstance(binding, dict)
            or not isinstance(binding.get("digest"), str)
            or not isinstance(binding.get("generation"), int)
            or binding["generation"] <= 0
        ):
            raise WorkspacePlacementCorrupt("placement binding generation is malformed")
        return state

    def _write(self, state: dict[str, Any]) -> None:
        body = json.dumps(state, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"
        temp = self.root / f".receipts.{secrets.token_hex(8)}.tmp"
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
    def _attempt_key(repository: RepositoryIdentity, semantic: SemanticIdentity) -> str:
        return _digest(
            {
                "repository": repository.canonical,
                "semantic": semantic.canonical,
            }
        )

    @staticmethod
    def _binding_digest(
        workspace_root: Path,
        execution_root: Path,
        protected_inventory: Sequence[str],
    ) -> str:
        return _digest(
            {
                "policy": PLACEMENT_POLICY,
                "kind": PLACEMENT_KIND,
                "workspace_root": _path_text(workspace_root),
                "execution_root": _path_text(execution_root),
                "protected_inventory": list(protected_inventory),
            }
        )

    def resolve_and_retain(
        self,
        host_policy: Policy,
        repository: RepositoryIdentity,
        semantic: SemanticIdentity,
        *,
        provider_protected_roots: Sequence[Path] = (),
        placement_expectation: str | Path | None = None,
    ) -> "DevforgeSandboxRootBinding":
        workspace_root, execution_root = _host_roots(host_policy)
        owner, repository_name = _repository_segments(repository)
        scope_segment = _safe_segment(semantic.task_id, "lineage.task_id")
        attempt_segment = _safe_segment(semantic.attempt_id, "lineage.attempt_id")
        exact_workspace = (
            execution_root / owner / repository_name / scope_segment / attempt_segment
        ).resolve(strict=False)
        if exact_workspace == execution_root or not exact_workspace.is_relative_to(execution_root):
            raise WorkspacePlacementEscape("derived execution workspace escaped execution_root")

        inventory = _protected_inventory(
            host_policy, provider_protected_roots=provider_protected_roots
        )
        _assert_protected_separation(execution_root, exact_workspace, inventory)

        if placement_expectation is not None:
            expected = Path(str(placement_expectation)).expanduser().resolve(strict=False)
            if not _same_path(expected, exact_workspace):
                raise WorkspacePlacementMismatch(
                    "caller/DevForge placement evidence differs from Host-derived placement"
                )

        repo_digest = _digest(repository.canonical)
        semantic_digest = _digest(semantic.canonical)
        target_digest = _digest(_path_text(exact_workspace))
        protected_digest = _digest(inventory)
        binding_digest = self._binding_digest(workspace_root, execution_root, inventory)
        attempt_key = self._attempt_key(repository, semantic)

        with _exclusive_file_lock(self._lock_path):
            state = self._load()
            raw_binding = state.get("binding")
            if raw_binding is None:
                generation = 1
                state["binding"] = {"digest": binding_digest, "generation": generation}
            else:
                generation = int(raw_binding["generation"])
                if raw_binding["digest"] != binding_digest:
                    generation += 1
                    state["binding"] = {"digest": binding_digest, "generation": generation}

            existing_raw = state["receipts"].get(attempt_key)
            if existing_raw is not None:
                if not isinstance(existing_raw, dict):
                    raise WorkspacePlacementCorrupt("placement receipt entry is malformed")
                existing = DevforgeWorkspacePlacementReceipt.from_json(existing_raw)
                if (
                    existing.binding_digest != binding_digest
                    or existing.binding_generation != generation
                    or existing.repository_identity_digest != repo_digest
                    or existing.semantic_identity_digest != semantic_digest
                    or existing.target_digest != target_digest
                    or not _same_path(Path(existing.target_path), exact_workspace)
                ):
                    self._write(state)
                    raise WorkspacePlacementStale(
                        "same Attempt placement receipt no longer matches current Host binding"
                    )
                receipt = existing
            else:
                receipt = DevforgeWorkspacePlacementReceipt(
                    receipt_id=f"dpr_{secrets.token_urlsafe(18)}",
                    policy=PLACEMENT_POLICY,
                    state=PLACEMENT_STATE,
                    operation=PLACEMENT_OPERATION,
                    repository=repository.canonical,
                    repository_identity_digest=repo_digest,
                    semantic_identity_digest=semantic_digest,
                    placement_role=PLACEMENT_ROLE,
                    workspace_root_digest=_digest(_path_text(workspace_root)),
                    execution_root_digest=_digest(_path_text(execution_root)),
                    target_path=_path_text(exact_workspace),
                    target_digest=target_digest,
                    protected_inventory_digest=protected_digest,
                    placement_compliant=True,
                    binding_generation=generation,
                    binding_digest=binding_digest,
                    issued_at=_iso_now(),
                )
                state["receipts"][attempt_key] = receipt.to_json()
                self._write(state)

            # Required authoritative read-back before any scope admission.
            persisted = self._load()
            confirmed_raw = persisted["receipts"].get(attempt_key)
            if not isinstance(confirmed_raw, dict):
                raise WorkspacePlacementCorrupt("placement receipt read-back is missing")
            confirmed = DevforgeWorkspacePlacementReceipt.from_json(confirmed_raw)
            if confirmed != receipt:
                raise WorkspacePlacementCorrupt("placement receipt read-back changed")

        return DevforgeSandboxRootBinding(
            receipt=receipt,
            workspace_root=workspace_root,
            execution_root=execution_root,
            exact_workspace=exact_workspace,
            protected_inventory=tuple(inventory),
            host_policy=host_policy,
            receipt_store=self,
        )

    def read_receipt(self, receipt_id: str) -> DevforgeWorkspacePlacementReceipt:
        with _exclusive_file_lock(self._lock_path):
            state = self._load()
            for raw in state["receipts"].values():
                if isinstance(raw, dict) and raw.get("receipt_id") == receipt_id:
                    return DevforgeWorkspacePlacementReceipt.from_json(raw)
        raise WorkspacePlacementCorrupt("unknown placement receipt")


@dataclass(frozen=True)
class DevforgeSandboxRootBinding:
    """Provider-private root binding and MutationScopeStore placement strategy."""

    receipt: DevforgeWorkspacePlacementReceipt
    workspace_root: Path
    execution_root: Path
    exact_workspace: Path
    protected_inventory: tuple[str, ...]
    host_policy: Policy = field(compare=False, repr=False)
    receipt_store: DevforgeWorkspacePlacementReceiptStore = field(compare=False, repr=False)

    @property
    def placement_kind(self) -> str:
        return PLACEMENT_KIND

    @property
    def placement_receipt_ref(self) -> str:
        return self.receipt.receipt_id

    @property
    def sandbox_root_digest(self) -> str:
        return self.receipt.execution_root_digest

    def _evidence(self, repository: RepositoryIdentity, semantic: SemanticIdentity) -> PlacementEvidence:
        if self.receipt.repository_identity_digest != _digest(repository.canonical):
            raise HostMutationScopeBindingMismatch("DevForge receipt repository identity mismatch")
        if self.receipt.semantic_identity_digest != _digest(semantic.canonical):
            raise HostMutationScopeBindingMismatch("DevForge receipt semantic identity mismatch")
        if not _same_path(Path(self.receipt.target_path), self.exact_workspace):
            raise HostMutationScopeBindingMismatch("DevForge receipt target path mismatch")
        return PlacementEvidence(
            placement_ref=f"devforge-placement:{self.receipt.receipt_id}:g{self.receipt.binding_generation}",
            generation=self.receipt.binding_generation,
            policy_digest=self.receipt.binding_digest,
            exact_future_workspace=self.exact_workspace,
            exact_workspace_digest=self.receipt.target_digest,
            repository_identity_digest=self.receipt.repository_identity_digest,
            semantic_identity_digest=self.receipt.semantic_identity_digest,
            protected_inventory_digest=self.receipt.protected_inventory_digest,
        )

    def resolve(
        self,
        policy: MutationExecutionPolicy,
        repository: RepositoryIdentity,
        semantic: SemanticIdentity,
        *,
        provider_protected_roots: Sequence[Path] = (),
    ) -> PlacementEvidence:
        del policy
        current = self.receipt_store.resolve_and_retain(
            self.host_policy,
            repository,
            semantic,
            provider_protected_roots=provider_protected_roots,
            placement_expectation=self.exact_workspace,
        )
        if current.receipt.receipt_id != self.receipt.receipt_id:
            raise HostMutationScopeBindingMismatch("DevForge placement receipt identity changed")
        if current.sandbox_root_digest != self.sandbox_root_digest:
            raise HostMutationScopeBindingMismatch("DevForge sandbox root binding changed")
        return self._evidence(repository, semantic)

    def revalidate(
        self,
        expected: PlacementEvidence,
        policy: MutationExecutionPolicy,
        repository: RepositoryIdentity,
        semantic: SemanticIdentity,
        *,
        provider_protected_roots: Sequence[Path] = (),
    ) -> PlacementEvidence:
        current = self.resolve(
            policy,
            repository,
            semantic,
            provider_protected_roots=provider_protected_roots,
        )
        sealed = (
            "placement_ref",
            "generation",
            "policy_digest",
            "exact_future_workspace",
            "exact_workspace_digest",
            "repository_identity_digest",
            "semantic_identity_digest",
            "protected_inventory_digest",
        )
        if any(getattr(current, name) != getattr(expected, name) for name in sealed):
            raise HostMutationScopeBindingMismatch(
                "DevForge provider placement no longer matches sealed scope authority"
            )
        return current
