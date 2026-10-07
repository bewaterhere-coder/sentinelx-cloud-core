from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from sentinelx_core.mutation_placement import (
    HostMutationScopeBindingMismatch,
    RepositoryIdentity,
    SemanticIdentity,
    placement_policy_digest,
)
from sentinelx_core.mutation_scope import (
    SCOPED_SCRIPT_OPERATION_CLASS,
    SessionObjectReadBinding,
    HostMutationScopeConflict,
    HostMutationScopeNotCurrent,
    HostMutationScopeOperationNotAllowed,
    MutationScopeStore,
)
from sentinelx_core.policy import MutationExecutionPolicy


def _authority(tmp_path: Path, *, attempt_id: str = "attempt-1"):
    workspace_root = tmp_path / "workspaces"
    protected_root = tmp_path / "protected"
    state_root = tmp_path / "provider-state"
    for path in (workspace_root, protected_root, state_root):
        path.mkdir(parents=True, exist_ok=True)
    policy = MutationExecutionPolicy(
        configured=True,
        scoped_mutation_enabled=True,
        workspace_root=workspace_root,
        protected_roots=(protected_root,),
        scope_ttl_seconds=600,
        evidence_retention_days=7,
        operator_unrestricted_enabled=False,
    )
    repository = RepositoryIdentity(
        vcs="git",
        authority="github.com",
        path="bewaterhere-coder/sentinelx-cloud-core",
    )
    semantic = SemanticIdentity(
        project_id="sentinelx-cloud-core",
        task_id="PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1",
        run_id="s01",
        attempt_id=attempt_id,
        slice_id="S01",
    )
    return MutationScopeStore(state_root), policy, repository, semantic, state_root


def _provision(
    store,
    policy,
    repository,
    semantic,
    state_root,
    *,
    classes=(SCOPED_SCRIPT_OPERATION_CLASS,),
):
    return store.provision_scope(
        policy,
        repository,
        semantic,
        allowed_operation_classes=classes,
        provider_protected_roots=(state_root.resolve(),),
    )


def test_operation_aware_revalidation_requires_durable_class(tmp_path: Path) -> None:
    store, policy, repository, semantic, state_root = _authority(tmp_path)
    record = _provision(store, policy, repository, semantic, state_root)
    admitted = store.revalidate_scope_for_operation(
        record.scope_id,
        record.generation,
        policy,
        repository,
        semantic,
        required_operation_class=SCOPED_SCRIPT_OPERATION_CLASS,
        provider_protected_roots=(state_root.resolve(),),
    )
    assert admitted.scope_id == record.scope_id

    denied_store, denied_policy, denied_repo, denied_semantic, denied_state = _authority(
        tmp_path / "denied", attempt_id="attempt-denied"
    )
    denied = _provision(
        denied_store,
        denied_policy,
        denied_repo,
        denied_semantic,
        denied_state,
        classes=("different_operation",),
    )
    with pytest.raises(HostMutationScopeOperationNotAllowed):
        denied_store.revalidate_scope_for_operation(
            denied.scope_id,
            denied.generation,
            denied_policy,
            denied_repo,
            denied_semantic,
            required_operation_class=SCOPED_SCRIPT_OPERATION_CLASS,
            provider_protected_roots=(denied_state.resolve(),),
        )
    assert denied_store.read_scope(denied.scope_id).state == "provisioned"
    assert not Path(denied.exact_workspace).exists()


def test_same_attempt_retry_cannot_broaden_operation_classes(tmp_path: Path) -> None:
    store, policy, repository, semantic, state_root = _authority(tmp_path)
    _provision(store, policy, repository, semantic, state_root)
    with pytest.raises(HostMutationScopeConflict):
        _provision(
            store,
            policy,
            repository,
            semantic,
            state_root,
            classes=(SCOPED_SCRIPT_OPERATION_CLASS, "extra_authority"),
        )


def test_bound_read_requires_exact_generation_repository_and_lineage(tmp_path: Path) -> None:
    store, policy, repository, semantic, state_root = _authority(tmp_path)
    record = _provision(store, policy, repository, semantic, state_root)
    assert store.read_bound_scope(record.scope_id, record.generation, repository, semantic) == record

    with pytest.raises(HostMutationScopeNotCurrent):
        store.read_bound_scope(record.scope_id, record.generation + 1, repository, semantic)

    wrong_repository = RepositoryIdentity(
        vcs="git", authority="github.com", path="bewaterhere-coder/other"
    )
    with pytest.raises(HostMutationScopeBindingMismatch):
        store.read_bound_scope(record.scope_id, record.generation, wrong_repository, semantic)

    wrong_semantic = SemanticIdentity(
        project_id=semantic.project_id,
        task_id=semantic.task_id,
        run_id=semantic.run_id,
        attempt_id="other-attempt",
        slice_id=semantic.slice_id,
    )
    with pytest.raises(HostMutationScopeBindingMismatch):
        store.read_bound_scope(record.scope_id, record.generation, repository, wrong_semantic)


def test_terminal_bound_read_is_pure_and_non_reactivating(tmp_path: Path) -> None:
    store, policy, repository, semantic, state_root = _authority(tmp_path)
    record = _provision(store, policy, repository, semantic, state_root)
    terminal = store.terminalize_scope(
        record.scope_id,
        record.generation,
        policy,
        repository,
        semantic,
        provider_protected_roots=(state_root.resolve(),),
    )
    assert terminal.state == "terminal"
    first = store.read_bound_scope(record.scope_id, record.generation, repository, semantic)
    second = store.read_bound_scope(record.scope_id, record.generation, repository, semantic)
    assert first.state == "terminal"
    assert second == first



def test_runtime_acl_timeout_participates_in_policy_digest(tmp_path: Path) -> None:
    _store, policy, _repository, _semantic, _state_root = _authority(tmp_path)
    changed = replace(
        policy,
        runtime_acl_timeout_seconds=policy.runtime_acl_timeout_seconds + 1,
    )
    assert placement_policy_digest(changed) != placement_policy_digest(policy)


def _session_binding() -> SessionObjectReadBinding:
    return SessionObjectReadBinding(
        cleanup_required=True,
        session_id=0,
        window_station_identity="session:0/window-station:Service-0x0-3e7$",
        desktop_identity=(
            "session:0/window-station:Service-0x0-3e7$/desktop:Default"
        ),
        window_station_mask=0x00020103,
        desktop_mask=0x00020041,
    )


def test_runtime_session_object_policy_participates_in_policy_digest(
    tmp_path: Path,
) -> None:
    _store, policy, _repository, _semantic, _state_root = _authority(tmp_path)
    changed = replace(policy, runtime_session_object_read_enabled=True)
    assert placement_policy_digest(changed) != placement_policy_digest(policy)


def test_session_object_binding_is_durable_restart_readable_and_exactly_clearable(
    tmp_path: Path,
) -> None:
    store, policy, repository, semantic, state_root = _authority(tmp_path)
    record = _provision(store, policy, repository, semantic, state_root)
    active = store.reserve_sandbox_identity(
        record.scope_id, record.generation, "S-1-15-2-42"
    )
    binding = _session_binding()

    reserved = store.reserve_session_object_read_binding(
        active.scope_id, active.generation, active.sandbox_identity, binding
    )
    assert reserved.session_object_read_binding == binding

    restarted = MutationScopeStore(state_root)
    read_back = restarted.read_scope(active.scope_id)
    assert read_back.session_object_read_binding == binding

    cleared = restarted.clear_session_object_read_binding(
        active.scope_id, active.generation, active.sandbox_identity, binding
    )
    assert cleared.session_object_read_binding is None


def test_session_object_binding_blocks_store_only_terminalization(
    tmp_path: Path,
) -> None:
    from sentinelx_core.mutation_scope import HostMutationResidualAuthorityDetected

    store, policy, repository, semantic, state_root = _authority(tmp_path)
    record = _provision(store, policy, repository, semantic, state_root)
    active = store.reserve_sandbox_identity(
        record.scope_id, record.generation, "S-1-15-2-43"
    )
    binding = _session_binding()
    store.reserve_session_object_read_binding(
        active.scope_id, active.generation, active.sandbox_identity, binding
    )
    store.clear_sandbox_write_authority(
        active.scope_id, active.generation, active.sandbox_identity
    )

    with pytest.raises(HostMutationResidualAuthorityDetected):
        store.terminalize_scope(
            active.scope_id,
            active.generation,
            policy,
            repository,
            semantic,
            provider_protected_roots=(state_root.resolve(),),
        )

    current = store.read_scope(active.scope_id)
    assert current.session_object_read_binding == binding
    assert current.state == "active"
