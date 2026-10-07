"""DevForge placement-to-scope/sandbox bridge primitives.

S01 intentionally stops before repository materialization.  This module reuses
MutationScopeStore's one durable authority file and WindowsMutationSandbox's
one AppContainer/Job implementation; it only supplies the DevForge-specific
placement/root admission that those canonical primitives do not yet know.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from typing import Sequence

import sentinelx_core.mutation_scope as _scope
from sentinelx_core.devforge_workspace_placement import (
    DevforgeSandboxRootBinding,
    PLACEMENT_KIND,
)
from sentinelx_core.mutation_placement import (
    HostMutationScopeBindingMismatch,
    PlacementEvidence,
    RepositoryIdentity,
    SemanticIdentity,
    unique_mutation_lease_key,
)
from sentinelx_core.mutation_scope import (
    HostMutationScopeConflict,
    HostMutationScopeCorrupt,
    HostMutationScopeNotCurrent,
    MutationScopeRecord,
    MutationScopeStore,
)
from sentinelx_core.policy import MutationExecutionPolicy
from sentinelx_core.windows_mutation_sandbox import WindowsMutationSandbox


def _devforge_policy_digest(binding: DevforgeSandboxRootBinding) -> str:
    """Seal placement kind + receipt/root binding into the existing policy slot."""
    return _scope._digest(
        {
            "placement_kind": PLACEMENT_KIND,
            "placement_receipt_ref": binding.placement_receipt_ref,
            "host_binding_digest": binding.receipt.binding_digest,
            "sandbox_root_digest": binding.sandbox_root_digest,
        }
    )


def _scope_placement(
    binding: DevforgeSandboxRootBinding,
    policy: MutationExecutionPolicy,
    repository: RepositoryIdentity,
    semantic: SemanticIdentity,
    *,
    provider_protected_roots: Sequence[Path],
) -> PlacementEvidence:
    evidence = binding.resolve(
        policy,
        repository,
        semantic,
        provider_protected_roots=provider_protected_roots,
    )
    # MutationScopeRecord has one canonical policy_digest field.  For the
    # DevForge strategy it seals the provider-only root/receipt identity rather
    # than the legacy mutation_execution.workspace_root policy digest.
    return replace(evidence, policy_digest=_devforge_policy_digest(binding))


class DevforgeMutationScopeStore(MutationScopeStore):
    """DevForge admission seam over the existing MutationScopeStore authority.

    The underlying authority.json, Attempt/lease/workspace indexes, runtime
    bindings, terminalization and corruption checks remain exactly the same.
    There is no second scope database or second lifecycle authority.
    """

    @staticmethod
    def _assert_devforge_binding(
        record: MutationScopeRecord,
        binding: DevforgeSandboxRootBinding,
    ) -> None:
        expected_prefix = f"devforge-placement:{binding.placement_receipt_ref}:"
        if not record.placement_ref.startswith(expected_prefix):
            raise HostMutationScopeBindingMismatch(
                "scope is not sealed to the supplied DevForge Placement Receipt"
            )
        if record.policy_digest != _devforge_policy_digest(binding):
            raise HostMutationScopeBindingMismatch(
                "scope DevForge sandbox-root/receipt binding changed"
            )
        if record.exact_workspace_digest != binding.receipt.target_digest:
            raise HostMutationScopeBindingMismatch("scope DevForge workspace digest changed")
        if Path(record.exact_workspace).resolve(strict=False) != binding.exact_workspace.resolve(
            strict=False
        ):
            raise HostMutationScopeBindingMismatch("scope DevForge exact workspace changed")

    def _revalidate_devforge_locked(
        self,
        state: dict,
        record: MutationScopeRecord,
        policy: MutationExecutionPolicy,
        repository: RepositoryIdentity,
        semantic: SemanticIdentity,
        binding: DevforgeSandboxRootBinding,
        *,
        provider_protected_roots: Sequence[Path],
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

        self._assert_devforge_binding(record, binding)
        expected_attempt = _scope._attempt_key(record.repository_identity_digest, semantic)
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
            or (record.slice_id or "")
            != (semantic.slice_id.strip() if semantic.slice_id else "")
        ):
            raise HostMutationScopeBindingMismatch("semantic lineage mismatch")

        sealed = PlacementEvidence(
            placement_ref=record.placement_ref,
            generation=record.placement_generation,
            policy_digest=binding.receipt.binding_digest,
            exact_future_workspace=Path(record.exact_workspace),
            exact_workspace_digest=record.exact_workspace_digest,
            repository_identity_digest=record.repository_identity_digest,
            semantic_identity_digest=record.semantic_identity_digest,
            protected_inventory_digest=record.protected_inventory_digest,
        )
        current = binding.revalidate(
            sealed,
            policy,
            repository,
            semantic,
            provider_protected_roots=provider_protected_roots,
        )
        if replace(current, policy_digest=_devforge_policy_digest(binding)).policy_digest != record.policy_digest:
            raise HostMutationScopeBindingMismatch("DevForge placement authority digest changed")
        return record, changed

    def provision_devforge_scope(
        self,
        policy: MutationExecutionPolicy,
        repository: RepositoryIdentity,
        semantic: SemanticIdentity,
        binding: DevforgeSandboxRootBinding,
        *,
        allowed_operation_classes: Sequence[str],
        provider_protected_roots: Sequence[Path] = (),
        now: datetime | None = None,
    ) -> MutationScopeRecord:
        """Mint one scope only after the provider Placement Receipt was read back."""
        now = now or _scope._utcnow()
        operations = self._normalize_operation_classes(allowed_operation_classes)
        placement = _scope_placement(
            binding,
            policy,
            repository,
            semantic,
            provider_protected_roots=provider_protected_roots,
        )
        attempt_key = _scope._attempt_key(placement.repository_identity_digest, semantic)
        lease_key = unique_mutation_lease_key(
            repository_digest=placement.repository_identity_digest,
            semantic=semantic,
            placement_generation=placement.generation,
            exact_workspace_digest=placement.exact_workspace_digest,
        )

        with _scope._exclusive_file_lock(self._lock_path):
            state = self._load_state()
            authority_root = self.root.resolve(strict=False)
            exact_workspace = placement.exact_future_workspace.resolve(strict=False)
            if (
                authority_root == exact_workspace
                or authority_root.is_relative_to(exact_workspace)
                or exact_workspace.is_relative_to(authority_root)
            ):
                raise HostMutationScopeConflict(
                    "provider authority store overlaps exact writable workspace"
                )

            attempt_scope_id = state["attempts"].get(attempt_key)
            if attempt_scope_id is not None:
                if not isinstance(attempt_scope_id, str):
                    raise HostMutationScopeCorrupt("Attempt index contains non-string scope id")
                existing = self._record(state, attempt_scope_id)
                self._assert_devforge_binding(existing, binding)
                if (
                    existing.unique_lease_key != lease_key
                    or existing.exact_workspace_digest != placement.exact_workspace_digest
                    or existing.repository_identity_digest != placement.repository_identity_digest
                    or existing.semantic_identity_digest != placement.semantic_identity_digest
                    or existing.placement_generation != placement.generation
                    or existing.policy_digest != placement.policy_digest
                ):
                    raise HostMutationScopeBindingMismatch(
                        "same Attempt resolved to different DevForge placement authority"
                    )
                try:
                    validated, changed = self._revalidate_devforge_locked(
                        state,
                        existing,
                        policy,
                        repository,
                        semantic,
                        binding,
                        provider_protected_roots=provider_protected_roots,
                        now=now,
                    )
                except HostMutationScopeNotCurrent:
                    if state["scopes"].get(existing.scope_id) != existing.to_json():
                        self._durable_write_state(state)
                    raise
                if validated.allowed_operation_classes != operations:
                    raise HostMutationScopeConflict(
                        "same Attempt retry requested a different operation-class authority"
                    )
                if changed:
                    self._durable_write_state(state)
                return validated

            if state["leases"].get(lease_key) is not None:
                raise HostMutationScopeConflict(
                    "unique lease exists without authoritative Attempt binding"
                )
            workspace_entry = state["workspaces"].get(placement.exact_workspace_digest)
            if workspace_entry is not None:
                if not isinstance(workspace_entry, dict):
                    raise HostMutationScopeCorrupt("workspace reverse index entry is malformed")
                raise HostMutationScopeConflict(
                    "exact DevForge workspace is already sealed to mutation authority"
                )

            scope_id = _scope._opaque("mss")
            workspace_id = _scope._opaque("msw")
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
                issued_at=_scope._iso(now),
                expires_at=_scope._iso(now + timedelta(seconds=policy.scope_ttl_seconds)),
                scope_digest="",
            )
            record = replace(draft, scope_digest=_scope._digest(draft.immutable_digest_payload()))
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

            persisted = self._load_state()
            confirmed = self._record(persisted, scope_id)
            self._assert_index_binding(persisted, confirmed, expected_lease=lease_key)
            self._assert_devforge_binding(confirmed, binding)
            return confirmed

    def revalidate_devforge_scope(
        self,
        scope_id: str,
        generation: int,
        policy: MutationExecutionPolicy,
        repository: RepositoryIdentity,
        semantic: SemanticIdentity,
        binding: DevforgeSandboxRootBinding,
        *,
        provider_protected_roots: Sequence[Path] = (),
        now: datetime | None = None,
    ) -> MutationScopeRecord:
        now = now or _scope._utcnow()
        with _scope._exclusive_file_lock(self._lock_path):
            state = self._load_state()
            record = self._record(state, scope_id)
            if record.generation != generation:
                raise HostMutationScopeNotCurrent("scope generation is not current")
            try:
                validated, changed = self._revalidate_devforge_locked(
                    state,
                    record,
                    policy,
                    repository,
                    semantic,
                    binding,
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


class DevforgeWindowsMutationSandbox(WindowsMutationSandbox):
    """Existing Windows sandbox with one provider-selected DevForge root view."""

    def __init__(
        self,
        *,
        policy: MutationExecutionPolicy,
        scope_store: DevforgeMutationScopeStore,
        repository: RepositoryIdentity,
        semantic: SemanticIdentity,
        binding: DevforgeSandboxRootBinding,
        provider_protected_roots: Sequence[Path] = (),
    ) -> None:
        # This is an internal immutable policy view, not a Host config rewrite.
        # All AppContainer/ACL/Job code remains the canonical implementation;
        # only workspace_root is replaced by the already-admitted provider root.
        self._base_mutation_policy = policy
        sandbox_policy = replace(policy, workspace_root=binding.execution_root)
        self.devforge_binding = binding
        super().__init__(
            policy=sandbox_policy,
            scope_store=scope_store,
            repository=repository,
            semantic=semantic,
            provider_protected_roots=provider_protected_roots,
        )

    @property
    def devforge_scope_store(self) -> DevforgeMutationScopeStore:
        store = self.scope_store
        if not isinstance(store, DevforgeMutationScopeStore):
            raise HostMutationScopeBindingMismatch("DevForge sandbox lost its scope-store type")
        return store

    def _revalidate(self, scope_id: str, generation: int) -> MutationScopeRecord:
        return self.devforge_scope_store.revalidate_devforge_scope(
            scope_id,
            generation,
            self.policy,
            self.repository,
            self.semantic,
            self.devforge_binding,
            provider_protected_roots=self.provider_protected_roots,
        )

    def terminalize(self, scope_id: str, generation: int) -> MutationScopeRecord:
        # Prove current DevForge placement, then close runtime authority through
        # the one canonical scope terminalizer.  Passing the original legacy
        # mutation policy keeps its Host-global placement generation untouched;
        # _cleanup_runtime still uses the provider-selected sandbox policy view.
        self._revalidate(scope_id, generation)
        return self.devforge_scope_store.terminalize_scope(
            scope_id,
            generation,
            self._base_mutation_policy,
            self.repository,
            self.semantic,
            provider_protected_roots=self.provider_protected_roots,
            runtime_cleanup=self._cleanup_runtime,
        )


# ---------------------------------------------------------------------------
# PR-014 S02 — runtime materialization flow (Plan R5 D6/D7/D9).
#
# The bootstrap seed persistence route (repository projection) is intentionally
# separate from this runtime behavior: materialize_workspace is only what the
# activated candidate is allowed to do on the Host.
# ---------------------------------------------------------------------------

import asyncio  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import secrets  # noqa: E402
import sys  # noqa: E402
from dataclasses import dataclass  # noqa: E402

from sentinelx_core.devforge_workspace_placement import (  # noqa: E402
    DevforgeWorkspacePlacementReceiptStore,
)
from sentinelx_core.devforge_workspace_materializer import (  # noqa: E402
    MATERIALIZER_RESULT_NAME,
    MATERIALIZER_SCRIPT_NAME,
    MaterializerError,
    build_materializer_worker,
    parse_worker_result,
)
from sentinelx_core.devforge_workspace_source import (  # noqa: E402
    DevforgeSourceError,
    SourceCapsule,
    SourceRoleBinding,
    build_source_capsule,
    resolve_canonical_source_role,
    validate_source_binding,
)
from sentinelx_core.mutation_audit import (  # noqa: E402
    ForensicScriptEvidence,
    MutationAuditBinding,
    MutationAuditJournal,
    MutationAuditStart,
    MutationAuthorityEvidence,
    MutationFinishClosureEvidence,
    MutationProcessIntent,
)
from sentinelx_core.request_context import MutationLineage  # noqa: E402

MATERIALIZE_OPERATION_CLASS = "devforge_execution_workspace_materialize"
MATERIALIZATION_POLICY = "devforge-execution-workspace-materialization-v1"
MATERIALIZATION_STATE = "handoff_ready"
MATERIALIZATION_TIMEOUT_SECONDS = 300


class DevforgeMaterializationError(RuntimeError):
    code = "WorkspaceMaterializationBlocked"


class MaterializationConflict(DevforgeMaterializationError):
    code = "WorkspaceMaterializationConflict"


class MaterializationNotVerified(DevforgeMaterializationError):
    code = "WorkspaceMaterializationNotVerified"


class MaterializationNotHandoffReady(MaterializationNotVerified):
    code = "WorkspaceMaterializationNotHandoffReady"


class MaterializationReceiptCorrupt(DevforgeMaterializationError):
    code = "WorkspaceMaterializationReceiptCorrupt"


def _attempt_key(repository: RepositoryIdentity, semantic: SemanticIdentity) -> str:
    return _scope._digest(
        {"repository": repository.canonical, "semantic": semantic.canonical}
    )


class DevforgeMaterializationReceiptStore:
    """Durable same-Attempt materialization receipt store (D9)."""

    STORE_VERSION = 1

    def __init__(self, state_root: Path) -> None:
        self.root = state_root.resolve(strict=False) / "devforge-workspace-materialization"
        self.root.mkdir(parents=True, exist_ok=True)
        self._state_path = self.root / "receipts.json"
        self._lock_path = self.root / "receipts.lock"

    def _empty_state(self) -> dict[str, Any]:
        return {"version": self.STORE_VERSION, "receipts": {}}

    def _load(self) -> dict[str, Any]:
        if not self._state_path.exists():
            return self._empty_state()
        try:
            state = json.loads(self._state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise MaterializationReceiptCorrupt(
                f"cannot read materialization receipt store: {exc}"
            ) from exc
        if not isinstance(state, dict) or state.get("version") != self.STORE_VERSION:
            raise MaterializationReceiptCorrupt("unsupported materialization receipt store")
        if not isinstance(state.get("receipts"), dict):
            raise MaterializationReceiptCorrupt("materialization receipt index is malformed")
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
        finally:
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass

    def get(self, attempt_key: str) -> dict[str, Any] | None:
        with _scope._exclusive_file_lock(self._lock_path):
            return self._load()["receipts"].get(attempt_key)

    def put_with_readback(self, attempt_key: str, receipt: dict[str, Any]) -> dict[str, Any]:
        with _scope._exclusive_file_lock(self._lock_path):
            state = self._load()
            state["receipts"][attempt_key] = receipt
            self._write(state)
            persisted = self._load()["receipts"].get(attempt_key)
            if persisted != receipt:
                raise MaterializationReceiptCorrupt("materialization receipt read-back changed")
            return persisted


def _canonical_source_url(repository: RepositoryIdentity) -> str:
    """Origin URL for the materialized workspace: the admitted identity only."""
    return repository.canonical


async def _workspace_git_readback(
    workspace: Path,
    *,
    expected_commit: str,
    logical_branch: str,
    origin_url: str,
) -> dict[str, str]:
    """Exact Git readback (D5) using the existing user-scoped Git transport."""
    from sentinelx_core import user_git
    from sentinelx_core.devforge_workspace_source import normalize_origin_identity

    async def run_git(*args: str) -> str:
        returncode, out, err = await user_git.run_user_scoped_git(
            workspace, *args, timeout=60.0
        )
        if returncode != 0:
            raise MaterializationNotVerified(
                f"workspace git {' '.join(args[:2])} failed: "
                f"{user_git.classify_result(returncode, err) or f'exit {returncode}'}"
            )
        return out.decode("utf-8", "replace").strip()

    toplevel = await run_git("rev-parse", "--show-toplevel")
    if os.path.normcase(Path(toplevel).resolve(strict=False)) != os.path.normcase(
        workspace.resolve(strict=False)
    ):
        raise MaterializationNotVerified("workspace toplevel is not the exact workspace")
    head = (await run_git("rev-parse", "HEAD")).lower()
    if head != expected_commit:
        raise MaterializationNotVerified("workspace HEAD is not the expected commit")
    branch = await run_git("branch", "--show-current")
    if branch != logical_branch:
        raise MaterializationNotVerified("workspace branch is not the admitted logical branch")
    origin = await run_git("remote", "get-url", "origin")
    if normalize_origin_identity(origin) != normalize_origin_identity(origin_url):
        raise MaterializationNotVerified("workspace origin does not normalize to the admitted repository")
    status = await run_git("status", "--porcelain")
    if status:
        raise MaterializationNotVerified("materialized workspace is not git-clean")
    return {
        "toplevel": toplevel,
        "head": head,
        "branch": branch,
        "origin": origin,
        "status": status,
    }


def _restore_host_inheritance(workspace: Path, appcontainer_sid: str) -> bool:
    """D7 bounded handoff: re-enable Host-derived inheritance, prove no AC SID.

    Workspace-local only: no caller SID/ACL input, no ancestor/root widening.
    Returns True when the restored DACL reads back without any AppContainer ACE.
    """
    if os.name != "nt":
        raise MaterializationNotHandoffReady("handoff transition requires Windows")
    import ctypes

    from sentinelx_core.windows_mutation_sandbox import (
        DACL_SECURITY_INFORMATION,
        SE_FILE_OBJECT,
        _assert_no_foreign_appcontainer_sid,
    )

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    advapi32.SetNamedSecurityInfoW.argtypes = [
        ctypes.c_wchar_p,
        ctypes.c_int,
        ctypes.c_uint32,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]
    advapi32.SetNamedSecurityInfoW.restype = ctypes.c_uint32
    # Without the PROTECTED flag this restores inheritance from the Host-owned
    # execution-root ancestry; no ACE content is supplied by anyone.
    error = advapi32.SetNamedSecurityInfoW(
        str(workspace), SE_FILE_OBJECT, DACL_SECURITY_INFORMATION, None, None, None, None
    )
    if error != 0:
        raise MaterializationNotHandoffReady(
            f"handoff inheritance restore failed with Windows error {error}"
        )
    try:
        _assert_no_foreign_appcontainer_sid(workspace)
    except Exception as exc:  # noqa: BLE001
        raise MaterializationNotHandoffReady(
            f"handoff DACL read-back failed: {exc}"
        ) from exc
    return True


def _closure_evidence(
    terminal: MutationScopeRecord, process: object | None
) -> MutationFinishClosureEvidence:
    job_handle_closed = True
    job_active_process_count = 0
    if process is not None:
        job_handle_closed = bool(getattr(process, "job_handle_closed", True))
        job_active_process_count = int(getattr(process, "active_process_count", 0) or 0)
    return MutationFinishClosureEvidence(
        scope_state=terminal.state,
        scope_digest=terminal.scope_digest,
        protected_inventory_digest=terminal.protected_inventory_digest,
        sandbox_identity=terminal.sandbox_identity,
        job_binding=(terminal.active_job_ids or (None,))[0] if terminal.active_job_ids else None,
        root_pid=None,
        job_handle_closed=job_handle_closed,
        job_active_process_count=job_active_process_count,
        active_job_ids=tuple(terminal.active_job_ids or ()),
        active_process_ids=tuple(terminal.active_process_ids or ()),
        sandbox_write_authority_present=terminal.sandbox_write_authority_present,
        process_tree_quiescent=(
            job_handle_closed
            and job_active_process_count == 0
            and not terminal.active_job_ids
            and not terminal.active_process_ids
        ),
        terminalized_at=terminal.terminalized_at or "",
    )


@dataclass(frozen=True)
class MaterializationRequest:
    """Provider-sealed materialization input derived from one local_api call."""

    repository: RepositoryIdentity
    semantic: SemanticIdentity
    expected_ref: str
    expected_commit: str
    request_id: str
    placement_expectation: str | None = None
    timeout_seconds: float = MATERIALIZATION_TIMEOUT_SECONDS


async def run_devforge_workspace_materialization(
    mutation_policy: MutationExecutionPolicy,
    host_policy: Policy,
    state_root: Path,
    request: MaterializationRequest,
) -> dict[str, Any]:
    """One bounded D6-ordered materialization with D9 retry semantics."""
    if sys.platform != "win32":
        raise DevforgeMaterializationError("materialize_workspace V1 requires Windows")
    validate_source_binding(request.expected_ref, request.expected_commit)

    attempt_key = _attempt_key(request.repository, request.semantic)
    receipts = DevforgeMaterializationReceiptStore(state_root)
    existing = receipts.get(attempt_key)
    placement_store = DevforgeWorkspacePlacementReceiptStore(state_root)

    if existing is not None:
        identity = existing.get("identity", {})
        same = (
            identity.get("repository") == request.repository.canonical
            and identity.get("semantic_digest")
            == _scope._digest(request.semantic.canonical)
            and identity.get("expected_ref") == request.expected_ref
            and identity.get("expected_commit") == request.expected_commit
            and identity.get("workspace_purpose") == request.placement_expectation
        )
        if not same:
            raise MaterializationConflict(
                "same Attempt materialization identity changed; replay is forbidden"
            )
        if existing.get("state") != MATERIALIZATION_STATE:
            raise MaterializationConflict(
                "previous materialization for this Attempt did not complete; "
                "cleanup must be proven before another attempt"
            )
        # Verified complete workspace: read back, return same evidence, no replay.
        workspace = Path(existing["workspace"]["target_path"])
        await _workspace_git_readback(
            workspace,
            expected_commit=request.expected_commit,
            logical_branch=existing["source"]["logical_branch"],
            origin_url=_canonical_source_url(request.repository),
        )
        return dict(existing)

    # D6 order: placement receipt -> source capsule -> scope -> START -> ...
    binding = placement_store.resolve_and_retain(
        host_policy,
        request.repository,
        request.semantic,
        provider_protected_roots=(state_root.resolve(strict=False),),
        placement_expectation=request.placement_expectation,
    )
    role = await resolve_canonical_source_role(host_policy, request.repository)
    capsule = await build_source_capsule(
        state_root, role, request.expected_ref, request.expected_commit
    )

    scope_store = DevforgeMutationScopeStore(state_root)
    protected_roots = (state_root.resolve(strict=False),)
    record = scope_store.provision_devforge_scope(
        mutation_policy,
        request.repository,
        request.semantic,
        binding,
        allowed_operation_classes=[MATERIALIZE_OPERATION_CLASS],
        provider_protected_roots=protected_roots,
    )
    record = scope_store.revalidate_devforge_scope(
        record.scope_id,
        record.generation,
        mutation_policy,
        request.repository,
        request.semantic,
        binding,
        provider_protected_roots=protected_roots,
    )

    audit = MutationAuditJournal(
        state_root,
        evidence_retention_days=mutation_policy.evidence_retention_days,
    )
    worker_bytes = build_materializer_worker()
    evidence: ForensicScriptEvidence = await asyncio.to_thread(
        audit.evidence.retain, worker_bytes
    )

    planned_workspace = Path(record.exact_workspace)
    script_path = planned_workspace / MATERIALIZER_SCRIPT_NAME
    argv = [sys.executable, "-I", str(script_path), str(capsule.root)]
    process_intent = MutationProcessIntent(
        interpreter="python3",
        argv=tuple(argv),
        executable_final_path=final_executable_path(Path(sys.executable)),
        cwd_final_path=str(planned_workspace),
    )
    from sentinelx_core.windows_mutation_sandbox import requested_mutation_identity

    lineage = MutationLineage(
        project_id=request.semantic.project_id,
        task_id=request.semantic.task_id,
        run_id=request.semantic.run_id,
        attempt_id=request.semantic.attempt_id,
        slice_id=request.semantic.slice_id,
    )
    audit_binding = MutationAuditBinding(
        request_id=request.request_id,
        op="devforge_runtime.materialize_workspace",
        opaque_ref=None,
        lineage=lineage,
        scope_id=record.scope_id,
        scope_generation=record.generation,
        workspace_id=record.workspace_id,
        unique_lease_key=record.unique_lease_key,
    )
    authority = MutationAuthorityEvidence(
        scope_digest=record.scope_digest,
        exact_workspace_digest=record.exact_workspace_digest,
        protected_inventory_digest=record.protected_inventory_digest,
        policy_digest=record.policy_digest,
        repository_identity_digest=record.repository_identity_digest,
        semantic_identity_digest=record.semantic_identity_digest,
    )
    start = audit.begin(
        audit_binding,
        evidence,
        authority=authority,
        process_intent=process_intent,
        requested_identity=requested_mutation_identity(record.unique_lease_key),
    )

    sandbox = DevforgeWindowsMutationSandbox(
        # Provider-owned immutable policy view: capsule read grant is added to
        # the exact existing runtime-read seam; nothing else changes.
        policy=replace(
            mutation_policy,
            workspace_root=binding.execution_root,
            runtime_read_roots=(
                *mutation_policy.runtime_read_roots,
                capsule.root.resolve(strict=False),
            ),
        ),
        scope_store=scope_store,
        repository=request.repository,
        semantic=request.semantic,
        binding=binding,
        provider_protected_roots=protected_roots,
    )

    process = None
    terminalized = False
    finished = False
    started = False
    try:
        activation = sandbox.activate(record, start)
        started = True
        if Path(activation.workspace) != planned_workspace:
            raise MaterializationNotVerified(
                "activated workspace differs from the sealed placement"
            )
        await asyncio.to_thread(audit.evidence.materialize_verified, evidence, script_path)
        process = sandbox.spawn(
            activation,
            audit=audit,
            audit_start=start,
            argv=argv,
            cwd=planned_workspace,
            env={},
        )
        done = await asyncio.to_thread(process.wait, float(request.timeout_seconds))
        if not done:
            process.terminate()
            raise MaterializationNotVerified("materializer exceeded the bounded timeout")
        result_path = planned_workspace / MATERIALIZER_RESULT_NAME
        if not result_path.exists():
            raise MaterializationNotVerified("materializer did not produce a result")
        worker_result = parse_worker_result(result_path.read_bytes())

        git_readback = await _workspace_git_readback(
            planned_workspace,
            expected_commit=request.expected_commit,
            logical_branch=capsule.logical_branch,
            origin_url=_canonical_source_url(request.repository),
        )

        terminal = sandbox.terminalize(record.scope_id, record.generation)
        terminalized = True
        audit.finish(
            start,
            status="succeeded",
            closure=_closure_evidence(terminal, process),
            returncode=0,
        )
        finished = True

        # D7: restore the Host-derived workspace ACL state after the Job
        # closed, then prove user-level Development Host access with the same
        # user-scoped Git readback as the V1 probe.
        try:
            _restore_host_inheritance(planned_workspace, activation.sandbox_identity)
            handoff_probe = await _workspace_git_readback(
                planned_workspace,
                expected_commit=request.expected_commit,
                logical_branch=capsule.logical_branch,
                origin_url=_canonical_source_url(request.repository),
            )
        except DevforgeMaterializationError:
            raise
        handoff_ready = True

        receipt: dict[str, Any] = {
            "policy": MATERIALIZATION_POLICY,
            "state": MATERIALIZATION_STATE if handoff_ready else "materialized",
            "receipt_id": f"dmr_{secrets.token_urlsafe(18)}",
            "identity": {
                "repository": request.repository.canonical,
                "repository_identity_digest": record.repository_identity_digest,
                "semantic": request.semantic.canonical,
                "semantic_digest": _scope._digest(request.semantic.canonical),
                "expected_ref": request.expected_ref,
                "expected_commit": request.expected_commit,
                "workspace_purpose": request.placement_expectation,
            },
            "source": {
                "role_policy": "devforge-execution-workspace-source-v1",
                "logical_branch": capsule.logical_branch,
                "object_format": capsule.object_format,
                "capsule_id": capsule.capsule_id,
                "capsule_manifest_digest": capsule.manifest_digest,
                "source_head_verified": role.head_commit,
            },
            "workspace": {
                "placement_receipt_ref": binding.receipt.receipt_id,
                "target_path": str(planned_workspace),
                "target_digest": binding.receipt.target_digest,
            },
            "authority": {
                "scope_id": record.scope_id,
                "scope_generation": record.generation,
                "audit_operation_id": start.operation_id,
                "operation_class": MATERIALIZE_OPERATION_CLASS,
            },
            "materializer": {
                "file_count": worker_result["file_count"],
                "total_bytes": worker_result["total_bytes"],
                "manifest_digest": worker_result["manifest_digest"],
            },
            "git_readback": git_readback,
            "handoff_probe": {
                "ok": handoff_ready,
                "readback": handoff_probe,
            },
            "completed_at": role.verified_at,
        }
        persisted = receipts.put_with_readback(attempt_key, receipt)
        return dict(persisted)
    except DevforgeMaterializationError:
        if not terminalized and started:
            try:
                terminal = sandbox.terminalize(record.scope_id, record.generation)
                terminalized = True
                if not finished:
                    audit.finish(
                        start,
                        status="failed",
                        closure=_closure_evidence(terminal, process),
                        error_code="WorkspaceMaterializationBlocked",
                    )
                    finished = True
            except (RuntimeError, OSError, ValueError):
                terminalized = False
        raise
    finally:
        if not terminalized and started:
            try:
                sandbox.terminalize(record.scope_id, record.generation)
            except (RuntimeError, OSError, ValueError):
                pass
