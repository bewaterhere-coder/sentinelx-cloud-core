from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from sentinelx_core.handlers.devforge_runtime import make_devforge_runtime_provider
from sentinelx_core.mutation_placement import RepositoryIdentity, SemanticIdentity
from sentinelx_core.mutation_scope import MutationScopeStore
from sentinelx_core.policy import CanonicalRepositorySpec, MutationExecutionPolicy, Policy
from sentinelx_core.repository_materialization import (
    CONTROL_NAMESPACE,
    RepositoryMaterializationConflict,
    RepositoryMaterializationService,
    RepositorySourceCorrupt,
    RepositorySourceSnapshotStore,
    RepositorySourceUnsafe,
    _dacl_entries,
    _safe_source_path,
    _safe_symlink_target,
)
from sentinelx_core.repository_materialization_runtime import (
    RuntimeRepositorySourceSnapshotStore,
    make_runtime_repository_materialization_provider,
)
from sentinelx_core.repository_transaction import RepositoryTransactionStore
from sentinelx_core.request_context import RequestContext


SOURCE_SHA = "a" * 40
REMOTE_SHA = "b" * 40


def _repository() -> RepositoryIdentity:
    return RepositoryIdentity(
        vcs="git",
        authority="github.com",
        path="bewaterhere-coder/sentinelx-cloud-core",
    )


def _semantic(attempt: str = "attempt-s02") -> SemanticIdentity:
    return SemanticIdentity(
        project_id="sentinelx-cloud-core",
        task_id="PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1",
        run_id="run-pr013-s02",
        attempt_id=attempt,
        slice_id="S02",
    )


def _context() -> RequestContext:
    return RequestContext("req-pr013-s02", "local_api", None, datetime.now(UTC))


def _policy(tmp_path: Path, *, physical_windows: bool = False) -> tuple[Policy, Path]:
    workspace = tmp_path / "workspaces"
    protected = tmp_path / "protected"
    uploads = tmp_path / "uploads"
    canonical = tmp_path / "canonical"
    state = tmp_path / "state"
    for path in (workspace, protected, uploads, canonical, state):
        path.mkdir(parents=True, exist_ok=True)
    runtime_roots: tuple[Path, ...] = ()
    if physical_windows:
        runtime_roots = (Path(sys.executable).resolve().parent,)
    policy = Policy(
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
    )
    return policy, state


def _scope_and_transaction(
    policy: Policy,
    state: Path,
    *,
    attempt: str = "attempt-s02",
):
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


def test_path_contract_rejects_windows_escape_and_control_namespace() -> None:
    assert _safe_source_path("src/a.txt") == "src/a.txt"
    for value in (
        "../escape.txt",
        "/absolute.txt",
        "C:drive.txt",
        "src/stream:ads",
        "COM1.txt",
        f"{CONTROL_NAMESPACE}/payload.py",
        "src/trailing. ",
    ):
        with pytest.raises(RepositorySourceUnsafe):
            _safe_source_path(value)

    assert _safe_symlink_target("docs/link", "../src/a.txt") == "../src/a.txt"
    with pytest.raises(RepositorySourceUnsafe):
        _safe_symlink_target("link", "../outside")
    with pytest.raises(RepositorySourceUnsafe):
        _safe_symlink_target("docs/link", r"C:\\outside")


def test_snapshot_is_sealed_path_free_and_detects_tamper(tmp_path: Path) -> None:
    store = RepositorySourceSnapshotStore(tmp_path / "state")
    snapshot = store.seal(
        transaction_id="rtx_unit_fixture",
        source_sha=SOURCE_SHA,
        entries=[
            ("src", "directory", "040000", None),
            ("src/a.txt", "file", "100644", b"hello\n"),
            ("link", "symlink", "120000", "src/a.txt"),
        ],
    )
    projected = snapshot.project()
    assert projected["source_sha"] == SOURCE_SHA
    assert projected["entry_count"] == 3
    assert "root" not in repr(projected).lower()
    assert "path" not in repr(projected).lower()

    loaded = store.load_verified("rtx_unit_fixture", expected_source_sha=SOURCE_SHA)
    assert loaded.tree_digest == snapshot.tree_digest

    file_path = snapshot.content_root / "src" / "a.txt"
    try:
        file_path.chmod(0o666)
    except OSError:
        pass
    file_path.write_bytes(b"tampered\n")
    with pytest.raises(RepositorySourceCorrupt):
        store.load_verified("rtx_unit_fixture", expected_source_sha=SOURCE_SHA)


def test_runtime_snapshot_missing_is_cache_miss_not_corrupt(tmp_path: Path) -> None:
    store = RuntimeRepositorySourceSnapshotStore(tmp_path / "state")
    with pytest.raises(FileNotFoundError):
        store.load_verified("rtx_missing_fixture", expected_source_sha=SOURCE_SHA)


def test_describe_adds_only_path_free_materialization_action(tmp_path: Path) -> None:
    policy, state = _policy(tmp_path)

    async def lifecycle(_payload):
        return {"ok": True}

    async def resolver(_repository: RepositoryIdentity, ref: str) -> str:
        return SOURCE_SHA if ref == "refs/heads/main" else REMOTE_SHA

    base = make_devforge_runtime_provider(
        policy,
        lifecycle,
        repository_transaction_store=RepositoryTransactionStore(state),
        repository_ref_resolver=resolver,
    )
    provider = make_runtime_repository_materialization_provider(base, policy)
    described = provider.describe()
    assert "materialize_repository" in described["actions"]
    schema = described["actions"]["materialize_repository"]["params_schema"]
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {"scope_ref", "repository", "lineage"}
    text = repr(schema).lower()
    for forbidden in (
        "workspace",
        "snapshot",
        "cache",
        "staging",
        "remote_url",
        "git_argv",
        "credential",
        "operation_class",
        "sandbox_identity",
    ):
        assert forbidden not in text


@pytest.mark.skipif(sys.platform != "win32", reason="Windows AppContainer materializer only")
def test_physical_windows_materializer_writes_repository_bytes_and_closes_authority(
    tmp_path: Path,
) -> None:
    policy, state = _policy(tmp_path, physical_windows=True)
    repository, semantic, scope_store, scope, transaction_store, transaction = (
        _scope_and_transaction(policy, state)
    )
    snapshot_store = RuntimeRepositorySourceSnapshotStore(state)

    class FakeBroker:
        async def acquire(self, observed_repository, observed_transaction):
            assert observed_repository.canonical == repository.canonical
            assert observed_transaction.transaction_id == transaction.transaction_id
            try:
                return snapshot_store.load_verified(
                    transaction.transaction_id,
                    expected_source_sha=SOURCE_SHA,
                )
            except FileNotFoundError:
                return snapshot_store.seal(
                    transaction_id=transaction.transaction_id,
                    source_sha=SOURCE_SHA,
                    entries=[
                        ("src", "directory", "040000", None),
                        ("src/a.txt", "file", "100644", b"materialized-by-appcontainer\n"),
                        ("README.md", "file", "100644", b"fixture\n"),
                    ],
                )

    async def resolver(_repository: RepositoryIdentity, _ref: str) -> str:
        return SOURCE_SHA

    service = RepositoryMaterializationService(
        policy=policy,
        transaction_store=transaction_store,
        ref_resolver=resolver,
        state_root=state,
        source_broker=FakeBroker(),
    )
    service.snapshot_store = snapshot_store

    result = asyncio.run(
        service.materialize(
            _context(),
            repository,
            semantic,
            scope_id=scope.scope_id,
            generation=scope.generation,
        )
    )
    assert result["repository_transaction"]["state"] == "materialized"
    evidence = result["materialization"]
    assert evidence["job_contained"] is True
    assert evidence["process_tree_quiescent"] is True
    assert evidence["snapshot_read_authority_removed"] is True
    assert evidence["workspace_write_authority_removed"] is True
    assert evidence["canonical_checkout_mutated"] is False

    workspace = Path(scope.exact_workspace)
    assert (workspace / "src" / "a.txt").read_bytes() == b"materialized-by-appcontainer\n"
    assert (workspace / "README.md").read_bytes() == b"fixture\n"
    assert (workspace / CONTROL_NAMESPACE / "materialization-result.json").is_file()

    current = scope_store.read_scope(scope.scope_id)
    assert current.current is True
    assert current.state == "active"
    assert current.active_job_ids == ()
    assert current.active_process_ids == ()
    assert current.sandbox_write_authority_present is False
    assert all(
        not sid.startswith("S-1-15-2-")
        for sid, _mask, _flags in _dacl_entries(workspace)
    )
    snapshot = snapshot_store.load_verified(
        transaction.transaction_id,
        expected_source_sha=SOURCE_SHA,
    )
    assert all(
        not sid.startswith("S-1-15-2-")
        for sid, _mask, _flags in _dacl_entries(snapshot._root)
    )

    persisted = transaction_store.inspect(
        repository,
        semantic,
        scope_id=scope.scope_id,
        generation=scope.generation,
    )
    assert persisted.state == "materialized"
    assert persisted.materialization_evidence is not None

    events = [
        json.loads(line)
        for line in (state / "mutation-audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    operation_events = [
        event for event in events if event.get("operation_id") == evidence["audit_operation_id"]
    ]
    assert [event["event"] for event in operation_events] == [
        "OPERATION_STARTED",
        "PROCESS_SPAWNED",
        "OPERATION_FINISHED",
    ]
    assert operation_events[-1]["operation_scope_terminal"] is False

    retry = asyncio.run(
        service.materialize(
            _context(),
            repository,
            semantic,
            scope_id=scope.scope_id,
            generation=scope.generation,
        )
    )
    assert retry["idempotent"] is True
    assert retry["repository_transaction"]["state"] == "materialized"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows AppContainer materializer only")
def test_terminal_scope_cannot_be_materialized_or_reactivated(tmp_path: Path) -> None:
    policy, state = _policy(tmp_path, physical_windows=True)
    repository, semantic, scope_store, scope, transaction_store, _transaction = (
        _scope_and_transaction(policy, state, attempt="attempt-terminal")
    )
    terminal = scope_store.terminalize_scope(
        scope.scope_id,
        scope.generation,
        policy.mutation_execution,
        repository,
        semantic,
        provider_protected_roots=(state.resolve(strict=False),),
    )
    assert terminal.state == "terminal"

    class NeverBroker:
        async def acquire(self, *_args):
            raise AssertionError("source acquisition must not run for terminal scope")

    async def resolver(_repository: RepositoryIdentity, _ref: str) -> str:
        return SOURCE_SHA

    service = RepositoryMaterializationService(
        policy=policy,
        transaction_store=transaction_store,
        ref_resolver=resolver,
        state_root=state,
        source_broker=NeverBroker(),
    )
    with pytest.raises(Exception):
        asyncio.run(
            service.materialize(
                _context(),
                repository,
                semantic,
                scope_id=scope.scope_id,
                generation=scope.generation,
            )
        )
    assert not Path(scope.exact_workspace).exists()
