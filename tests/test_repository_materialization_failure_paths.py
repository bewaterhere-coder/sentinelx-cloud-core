from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from sentinelx_core.mutation_placement import RepositoryIdentity, SemanticIdentity
from sentinelx_core.mutation_scope import MutationScopeStore
from sentinelx_core.policy import CanonicalRepositorySpec, MutationExecutionPolicy, Policy
from sentinelx_core.repository_materialization import (
    GitRepositorySourceBroker,
    RepositoryMaterializationConflict,
    RepositoryMaterializationService,
)
from sentinelx_core.repository_materialization_runtime import RuntimeRepositorySourceSnapshotStore
from sentinelx_core.repository_transaction import RepositoryTransactionStore
from sentinelx_core.request_context import RequestContext


SOURCE_SHA = "a" * 40
REMOTE_SHA = "b" * 40
DRIFT_SHA = "c" * 40


def _repository() -> RepositoryIdentity:
    return RepositoryIdentity(
        vcs="git",
        authority="github.com",
        path="bewaterhere-coder/sentinelx-cloud-core",
    )


def _semantic(attempt: str = "attempt-s02-negative") -> SemanticIdentity:
    return SemanticIdentity(
        project_id="sentinelx-cloud-core",
        task_id="PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1",
        run_id="run-pr013-s02-negative",
        attempt_id=attempt,
        slice_id="S02",
    )


def _policy(tmp_path: Path) -> tuple[Policy, Path]:
    workspace = tmp_path / "workspaces"
    protected = tmp_path / "protected"
    uploads = tmp_path / "uploads"
    canonical = tmp_path / "canonical"
    state = tmp_path / "state"
    for path in (workspace, protected, uploads, canonical, state):
        path.mkdir(parents=True, exist_ok=True)
    runtime_roots = (Path(sys.executable).resolve().parent,) if sys.platform == "win32" else ()
    return (
        Policy(
            upload_base=uploads,
            authenticated_git_enabled=True,
            authenticated_git_timeout_seconds=15,
            mutation_execution=MutationExecutionPolicy(
                configured=True,
                scoped_mutation_enabled=True,
                workspace_root=workspace,
                protected_roots=(protected,),
                runtime_read_roots=runtime_roots,
                scope_ttl_seconds=600,
                evidence_retention_days=7,
                canonical_repository_firewall_enabled=True,
                canonical_repositories=(
                    CanonicalRepositorySpec(
                        root=canonical,
                        repository_identity=_repository().canonical,
                        canonical_branch="main",
                    ),
                ),
            ),
        ),
        state,
    )


def _authority(policy: Policy, state: Path, *, attempt: str = "attempt-s02-negative"):
    repository = _repository()
    semantic = _semantic(attempt)
    scope_store = MutationScopeStore(state)
    scope = scope_store.provision_scope(
        policy.mutation_execution,
        repository,
        semantic,
        allowed_operation_classes=(
            "repository_materialize",
            "repository_execute",
            "repository_publish",
        ),
        provider_protected_roots=(state.resolve(strict=False),),
    )
    transaction_store = RepositoryTransactionStore(state)
    transaction = transaction_store.provision(
        repository,
        semantic,
        scope={
            "scope_id": scope.scope_id,
            "generation": scope.generation,
            "workspace_id": scope.workspace_id,
            "scope_digest": scope.scope_digest,
        },
        source_ref="refs/heads/main",
        expected_source_sha=SOURCE_SHA,
        verified_source_sha=SOURCE_SHA,
        publication_ref="refs/heads/task/pr013",
        expected_remote_sha=REMOTE_SHA,
        verified_remote_sha=REMOTE_SHA,
    )
    return repository, semantic, scope_store, scope, transaction_store, transaction


def _context() -> RequestContext:
    return RequestContext("req-pr013-s02-negative", "local_api", None, datetime.now(UTC))


def test_source_broker_re_resolves_ref_and_fails_before_fetch_on_sha_drift(tmp_path: Path) -> None:
    policy, state = _policy(tmp_path)
    repository, _semantic_id, _scope_store, _scope, _tx_store, transaction = _authority(
        policy, state, attempt="attempt-source-drift"
    )
    snapshot_store = RuntimeRepositorySourceSnapshotStore(state)
    resolver_calls: list[str] = []

    async def drifted_resolver(observed_repository: RepositoryIdentity, ref: str) -> str:
        assert observed_repository.canonical == repository.canonical
        resolver_calls.append(ref)
        return DRIFT_SHA

    broker = GitRepositorySourceBroker(
        policy=policy,
        state_root=state,
        snapshot_store=snapshot_store,
        ref_resolver=drifted_resolver,
    )
    with pytest.raises(RepositoryMaterializationConflict, match="source ref moved"):
        asyncio.run(broker.acquire(repository, transaction))
    assert resolver_calls == ["refs/heads/main"]
    assert list(broker.staging_root.iterdir()) == []


@pytest.mark.skipif(sys.platform != "win32", reason="S02 service is Windows AppContainer only")
def test_foreign_lineage_fails_before_source_acquisition(tmp_path: Path) -> None:
    policy, state = _policy(tmp_path)
    repository, _semantic_id, _scope_store, scope, transaction_store, _transaction = _authority(
        policy, state, attempt="attempt-owner"
    )

    class NeverBroker:
        async def acquire(self, *_args):
            raise AssertionError("foreign lineage must fail before source acquisition")

    async def resolver(_repository: RepositoryIdentity, _ref: str) -> str:
        return SOURCE_SHA

    service = RepositoryMaterializationService(
        policy=policy,
        transaction_store=transaction_store,
        ref_resolver=resolver,
        state_root=state,
        source_broker=NeverBroker(),
    )
    foreign = _semantic("attempt-foreign")
    with pytest.raises(Exception):
        asyncio.run(
            service.materialize(
                _context(),
                repository,
                foreign,
                scope_id=scope.scope_id,
                generation=scope.generation,
            )
        )
    assert not Path(scope.exact_workspace).exists()


@pytest.mark.skipif(sys.platform != "win32", reason="S02 service is Windows AppContainer only")
def test_source_acquisition_failure_revokes_scope_and_terminalizes_transaction(tmp_path: Path) -> None:
    policy, state = _policy(tmp_path)
    repository, semantic, scope_store, scope, transaction_store, transaction = _authority(
        policy, state, attempt="attempt-acquire-failure"
    )

    class FailingBroker:
        async def acquire(self, *_args):
            raise RepositoryMaterializationConflict("fixture source authority drift")

    async def resolver(_repository: RepositoryIdentity, _ref: str) -> str:
        return SOURCE_SHA

    service = RepositoryMaterializationService(
        policy=policy,
        transaction_store=transaction_store,
        ref_resolver=resolver,
        state_root=state,
        source_broker=FailingBroker(),
    )
    with pytest.raises(RepositoryMaterializationConflict, match="fixture source authority drift"):
        asyncio.run(
            service.materialize(
                _context(),
                repository,
                semantic,
                scope_id=scope.scope_id,
                generation=scope.generation,
            )
        )
    current_scope = scope_store.read_scope(scope.scope_id)
    assert current_scope.state == "revoked"
    assert current_scope.active_job_ids == ()
    assert current_scope.active_process_ids == ()
    assert current_scope.sandbox_write_authority_present is False
    persisted = transaction_store.inspect(
        repository,
        semantic,
        scope_id=scope.scope_id,
        generation=scope.generation,
        require_current_scope=False,
    )
    assert persisted.transaction_id == transaction.transaction_id
    assert persisted.state == "terminal"
    assert persisted.materialization_evidence is not None
    assert persisted.materialization_evidence["published"] is False
    assert not Path(scope.exact_workspace).exists()
