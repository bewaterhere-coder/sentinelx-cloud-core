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
