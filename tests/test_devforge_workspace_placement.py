from __future__ import annotations

import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from sentinelx_core.devforge_workspace_materialization import (
    DevforgeMutationScopeStore,
    DevforgeWindowsMutationSandbox,
)
from sentinelx_core.devforge_workspace_placement import (
    DevforgeWorkspacePlacementError,
    DevforgeWorkspacePlacementReceiptStore,
    WorkspacePlacementMismatch,
    WorkspacePlacementStale,
)
from sentinelx_core.mutation_audit import (
    MutationAuditBinding,
    MutationAuditJournal,
    MutationAuthorityEvidence,
    MutationProcessIntent,
)
from sentinelx_core.mutation_placement import (
    HostMutationScopeBindingMismatch,
    RepositoryIdentity,
    SemanticIdentity,
)
from sentinelx_core.policy import LocationSpec, MutationExecutionPolicy, Policy
from sentinelx_core.request_context import MutationLineage, RequestContext
from sentinelx_core.windows_mutation_sandbox import (
    _set_exact_acl,
    final_executable_path,
    requested_mutation_identity,
)


def _fixture(
    tmp_path: Path,
    *,
    task_id: str = "PR-014-devforge-execution-workspace-materialization-bridge-v1",
    attempt_id: str = "1",
    host_root: Path | None = None,
):
    host_root = host_root or (tmp_path / "host")
    legacy_root = tmp_path / "legacy-mutation-workspaces"
    protected_root = host_root / "repositories"
    state_root = tmp_path / "provider-state"
    for path in (host_root, host_root / "workspaces", legacy_root, protected_root, state_root):
        path.mkdir(parents=True, exist_ok=True)

    mutation_policy = MutationExecutionPolicy(
        configured=True,
        scoped_mutation_enabled=True,
        workspace_root=legacy_root,
        protected_roots=(protected_root,),
        runtime_read_roots=(),
        scope_ttl_seconds=600,
        evidence_retention_days=7,
        operator_unrestricted_enabled=False,
    )
    host_policy = Policy(
        mutation_execution=mutation_policy,
        locations={"devforge_workspace_root": LocationSpec(path=str(host_root))},
    )
    repository = RepositoryIdentity(
        vcs="git",
        authority="github.com",
        path="bewaterhere-coder/sentinelx-cloud-core",
    )
    semantic = SemanticIdentity(
        project_id="sentinelx-cloud-core",
        task_id=task_id,
        run_id="run-s01",
        attempt_id=attempt_id,
        slice_id="S01",
    )
    receipt_store = DevforgeWorkspacePlacementReceiptStore(state_root)
    scope_store = DevforgeMutationScopeStore(state_root)
    return (
        host_policy,
        mutation_policy,
        repository,
        semantic,
        receipt_store,
        scope_store,
        state_root,
        protected_root,
        legacy_root,
        host_root,
    )


def _binding(fx):
    host_policy, _mutation, repository, semantic, receipt_store, *_rest = fx
    return receipt_store.resolve_and_retain(host_policy, repository, semantic)


def test_devforge_placement_receipt_is_durable_before_scope_and_path_is_exact(tmp_path: Path) -> None:
    fx = _fixture(tmp_path)
    (
        _host_policy,
        mutation_policy,
        repository,
        semantic,
        receipt_store,
        scope_store,
        state_root,
        _protected,
        legacy_root,
        host_root,
    ) = fx

    binding = _binding(fx)
    expected = (
        host_root
        / "workspaces"
        / "bewaterhere-coder"
        / "sentinelx-cloud-core"
        / semantic.task_id
        / semantic.attempt_id
    ).resolve(strict=False)
    assert binding.exact_workspace == expected
    assert binding.execution_root == (host_root / "workspaces").resolve(strict=False)
    assert not binding.exact_workspace.exists(), "placement resolution must not materialize"
    assert not str(binding.exact_workspace).casefold().startswith(str(legacy_root).casefold())

    # Receipt read-back is observable before the scope authority store is touched.
    persisted = receipt_store.read_receipt(binding.placement_receipt_ref)
    assert persisted.target_path == str(expected)
    assert persisted.placement_compliant is True
    assert not (state_root / "mutation-scopes" / "authority.json").exists()

    record = scope_store.provision_devforge_scope(
        mutation_policy,
        repository,
        semantic,
        binding,
        allowed_operation_classes=("scoped_script",),
        provider_protected_roots=(state_root.resolve(),),
    )
    assert Path(record.exact_workspace) == expected
    assert record.placement_ref.startswith(
        f"devforge-placement:{binding.placement_receipt_ref}:"
    )
    assert record.exact_workspace_digest == binding.receipt.target_digest
    assert not expected.exists(), "scope provisioning alone must not create the workspace"


def test_same_attempt_receipt_and_scope_retry_converge_without_new_authority(tmp_path: Path) -> None:
    fx = _fixture(tmp_path)
    _host, mutation, repository, semantic, receipts, scopes, state_root, *_ = fx
    first_binding = _binding(fx)
    second_binding = _binding(fx)
    assert second_binding.placement_receipt_ref == first_binding.placement_receipt_ref
    assert second_binding.receipt == first_binding.receipt

    first = scopes.provision_devforge_scope(
        mutation,
        repository,
        semantic,
        first_binding,
        allowed_operation_classes=("scoped_script",),
        provider_protected_roots=(state_root.resolve(),),
    )
    second = scopes.provision_devforge_scope(
        mutation,
        repository,
        semantic,
        second_binding,
        allowed_operation_classes=("scoped_script",),
        provider_protected_roots=(state_root.resolve(),),
    )
    assert second == first


def test_caller_placement_expectation_cannot_retarget_provider_authority(tmp_path: Path) -> None:
    fx = _fixture(tmp_path)
    host_policy, _mutation, repository, semantic, receipts, _scopes, state_root, *_ = fx
    attacker_path = tmp_path / "caller-selected"
    with pytest.raises(WorkspacePlacementMismatch):
        receipts.resolve_and_retain(
            host_policy,
            repository,
            semantic,
            placement_expectation=attacker_path,
        )
    assert not attacker_path.exists()
    assert not (state_root / "mutation-scopes" / "authority.json").exists()


@pytest.mark.parametrize(
    "task_id",
    ["..", "../escape", "x/y", "x\\y", "unsafe:drive"],
)
def test_semantic_path_injection_is_rejected_before_receipt_or_scope(
    tmp_path: Path, task_id: str
) -> None:
    fx = _fixture(tmp_path, task_id=task_id)
    _host, _mutation, repository, semantic, receipts, _scopes, state_root, *_ = fx
    with pytest.raises(DevforgeWorkspacePlacementError):
        receipts.resolve_and_retain(fx[0], repository, semantic)
    assert not (state_root / "mutation-scopes" / "authority.json").exists()


def test_host_binding_drift_invalidates_same_attempt_receipt(tmp_path: Path) -> None:
    fx = _fixture(tmp_path, host_root=tmp_path / "host-a")
    host_a, mutation, repository, semantic, receipts, scopes, state_root, *_ = fx
    binding_a = receipts.resolve_and_retain(host_a, repository, semantic)
    record = scopes.provision_devforge_scope(
        mutation,
        repository,
        semantic,
        binding_a,
        allowed_operation_classes=("scoped_script",),
        provider_protected_roots=(state_root.resolve(),),
    )

    host_b_root = tmp_path / "host-b"
    (host_b_root / "workspaces").mkdir(parents=True)
    host_b = Policy(
        mutation_execution=mutation,
        locations={"devforge_workspace_root": LocationSpec(path=str(host_b_root))},
    )
    with pytest.raises(WorkspacePlacementStale):
        receipts.resolve_and_retain(host_b, repository, semantic)
    assert Path(record.exact_workspace) == binding_a.exact_workspace
    assert not (host_b_root / "workspaces" / "bewaterhere-coder").exists()


def test_wrong_provider_root_binding_cannot_revalidate_existing_scope(tmp_path: Path) -> None:
    fx = _fixture(tmp_path)
    _host, mutation, repository, semantic, receipts, scopes, state_root, *_ = fx
    binding = _binding(fx)
    record = scopes.provision_devforge_scope(
        mutation,
        repository,
        semantic,
        binding,
        allowed_operation_classes=("scoped_script",),
        provider_protected_roots=(state_root.resolve(),),
    )

    other_root = tmp_path / "other-host"
    (other_root / "workspaces").mkdir(parents=True)
    other_policy = Policy(
        mutation_execution=mutation,
        locations={"devforge_workspace_root": LocationSpec(path=str(other_root))},
    )
    other_receipts = DevforgeWorkspacePlacementReceiptStore(tmp_path / "other-state")
    other_binding = other_receipts.resolve_and_retain(other_policy, repository, semantic)
    with pytest.raises(HostMutationScopeBindingMismatch):
        scopes.revalidate_devforge_scope(
            record.scope_id,
            record.generation,
            mutation,
            repository,
            semantic,
            other_binding,
            provider_protected_roots=(state_root.resolve(),),
        )


def test_legacy_scope_placement_remains_independent_and_revalidates(tmp_path: Path) -> None:
    fx = _fixture(tmp_path)
    _host, mutation, repository, semantic, _receipts, scopes, state_root, _protected, legacy_root, *_ = fx
    binding = _binding(fx)
    devforge = scopes.provision_devforge_scope(
        mutation,
        repository,
        semantic,
        binding,
        allowed_operation_classes=("scoped_script",),
        provider_protected_roots=(state_root.resolve(),),
    )

    legacy_semantic = SemanticIdentity(
        project_id=semantic.project_id,
        task_id=semantic.task_id,
        run_id="legacy-run",
        attempt_id="legacy-attempt",
        slice_id="S01",
    )
    legacy = scopes.provision_scope(
        mutation,
        repository,
        legacy_semantic,
        allowed_operation_classes=("scoped_script",),
        provider_protected_roots=(state_root.resolve(),),
    )
    assert legacy.placement_ref.startswith("mutation-placement:")
    assert Path(legacy.exact_workspace).resolve(strict=False).is_relative_to(
        legacy_root.resolve(strict=False)
    )
    assert Path(devforge.exact_workspace).resolve(strict=False).is_relative_to(
        binding.execution_root
    )
    assert scopes.revalidate_scope(
        legacy.scope_id,
        legacy.generation,
        mutation,
        repository,
        legacy_semantic,
        provider_protected_roots=(state_root.resolve(),),
    ) == legacy


@pytest.mark.skipif(sys.platform != "win32", reason="Windows AppContainer only")
def test_windows_devforge_root_is_physically_confined_from_canonical_sibling(tmp_path: Path) -> None:
    fx = _fixture(tmp_path)
    (
        _host,
        mutation,
        repository,
        semantic,
        _receipts,
        scopes,
        state_root,
        protected_root,
        legacy_root,
        _host_root,
    ) = fx
    binding = _binding(fx)
    record = scopes.provision_devforge_scope(
        mutation,
        repository,
        semantic,
        binding,
        allowed_operation_classes=("scoped_script",),
        provider_protected_roots=(state_root.resolve(),),
    )
    assert not Path(record.exact_workspace).exists()
    assert not Path(record.exact_workspace).resolve(strict=False).is_relative_to(
        legacy_root.resolve(strict=False)
    )

    sandbox = DevforgeWindowsMutationSandbox(
        policy=mutation,
        scope_store=scopes,
        repository=repository,
        semantic=semantic,
        binding=binding,
        provider_protected_roots=(state_root.resolve(),),
    )

    canonical_sibling = protected_root / "bewaterhere-coder" / "sentinelx-cloud-core"
    canonical_sibling.mkdir(parents=True, exist_ok=True)
    secret = canonical_sibling / "secret.txt"
    secret.write_text("must-not-be-readable", encoding="utf-8")
    # Make the negative deterministic: only the broker keeps authority here.
    _set_exact_acl(canonical_sibling, sandbox.broker_sid, None)

    audit = MutationAuditJournal(state_root / "audit", evidence_retention_days=7)
    context = RequestContext(
        request_id="pr014-s01-windows-root",
        op="script_run",
        opaque_ref="pr014-s01",
        received_at=datetime.now(UTC),
    )
    lineage = MutationLineage.from_mapping(
        {
            "project_id": semantic.project_id,
            "task_id": semantic.task_id,
            "run_id": semantic.run_id,
            "attempt_id": semantic.attempt_id,
            "slice_id": semantic.slice_id,
        }
    )
    retained = audit.evidence.retain(b"PR-014 S01 DevForge root confinement fixture\n")
    audit_binding = MutationAuditBinding.from_context(
        context,
        lineage,
        scope_id=record.scope_id,
        scope_generation=record.generation,
        workspace_id=record.workspace_id,
        unique_lease_key=record.unique_lease_key,
    )
    cmd = Path(shutil.which("cmd.exe") or r"C:\Windows\System32\cmd.exe")
    authority = MutationAuthorityEvidence(
        scope_digest=record.scope_digest,
        exact_workspace_digest=record.exact_workspace_digest,
        protected_inventory_digest=record.protected_inventory_digest,
        policy_digest=record.policy_digest,
        repository_identity_digest=record.repository_identity_digest,
        semantic_identity_digest=record.semantic_identity_digest,
    )
    intent = MutationProcessIntent(
        interpreter="cmd.exe",
        argv=(str(cmd),),
        executable_final_path=final_executable_path(cmd),
        cwd_final_path=record.exact_workspace,
    )
    start = audit.begin(
        audit_binding,
        retained,
        authority=authority,
        process_intent=intent,
        requested_identity=requested_mutation_identity(record.unique_lease_key),
    )
    activation = sandbox.activate(record, start)
    inside = activation.workspace / "inside.txt"
    leak = activation.workspace / "leak.txt"
    visible = activation.workspace / "visible.txt"
    escaped = canonical_sibling / "escape.txt"
    command = (
        "echo inside>inside.txt & "
        f'if exist "{secret}" echo visible>visible.txt & '
        f'copy /y "{secret}" leak.txt >nul 2>nul & '
        f'echo escaped>"{escaped}"'
    )
    process = sandbox.spawn(
        activation,
        audit=audit,
        audit_start=start,
        argv=["cmd.exe", "/d", "/c", command],
    )
    assert process.wait(10)
    assert inside.exists()
    assert not visible.exists(), "sandbox enumerated/read canonical sibling visibility"
    assert not leak.exists(), "sandbox read canonical sibling content"
    assert not escaped.exists(), "sandbox wrote canonical sibling"
    assert secret.read_text(encoding="utf-8") == "must-not-be-readable"

    terminal = sandbox.terminalize(record.scope_id, record.generation)
    assert terminal.state == "terminal"
    assert terminal.active_job_ids == ()
    assert terminal.active_process_ids == ()
    assert terminal.sandbox_write_authority_present is False
