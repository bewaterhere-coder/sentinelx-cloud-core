"""PR-014 S02 — materialization receipt/retry semantics and orchestration seams (D6/D9)."""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from sentinelx_core.devforge_workspace_materialization import (
    DevforgeMaterializationReceiptStore,
    MaterializationConflict,
    MaterializationReceiptCorrupt,
    MaterializationRequest,
    MATERIALIZE_OPERATION_CLASS,
    MATERIALIZATION_STATE,
    _attempt_key,
    _canonical_source_url,
    _workspace_git_readback,
)
from sentinelx_core.devforge_workspace_source import (
    SourceIdentityMismatch,
    validate_source_binding,
)
from sentinelx_core.mutation_placement import RepositoryIdentity, SemanticIdentity
from sentinelx_core.policy import MutationExecutionPolicy

REPOSITORY = RepositoryIdentity(
    vcs="git",
    authority="github.com",
    path="bewaterhere-coder/sentinelx-cloud-core",
)
SEMANTIC = SemanticIdentity(
    project_id="sentinelx-cloud-core",
    task_id="PR-014-devforge-execution-workspace-materialization-bridge-v1",
    run_id="run-s02",
    attempt_id="attempt-1",
    slice_id="S02",
)


def _request(**overrides) -> MaterializationRequest:
    fields = {
        "repository": REPOSITORY,
        "semantic": SEMANTIC,
        "expected_ref": "refs/heads/task/devforge-execution-workspace-materialization-bridge-v1",
        "expected_commit": "a" * 40,
        "request_id": "req-s02",
    }
    fields.update(overrides)
    return MaterializationRequest(**fields)


def test_operation_class_is_provider_fixed() -> None:
    assert MATERIALIZE_OPERATION_CLASS == "devforge_execution_workspace_materialize"
    assert MATERIALIZATION_STATE == "handoff_ready"


def test_attempt_key_is_stable_for_same_identity_and_differs_otherwise() -> None:
    key = _attempt_key(REPOSITORY, SEMANTIC)
    assert key == _attempt_key(REPOSITORY, SEMANTIC)
    other = _attempt_key(REPOSITORY, replace(SEMANTIC, attempt_id="attempt-2"))
    assert other != key


def test_receipt_store_is_durable_with_readback(tmp_path: Path) -> None:
    store = DevforgeMaterializationReceiptStore(tmp_path / "state")
    receipt = {"policy": "p", "state": MATERIALIZATION_STATE, "receipt_id": "dmr_1"}
    persisted = store.put_with_readback("attempt-key", receipt)
    assert persisted == receipt
    assert store.get("attempt-key") == receipt
    assert store.get("missing") is None


def test_receipt_store_refuses_corrupt_store(tmp_path: Path) -> None:
    root = tmp_path / "state"
    store = DevforgeMaterializationReceiptStore(root)
    (store.root / "receipts.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(MaterializationReceiptCorrupt):
        store.get("attempt-key")


def test_canonical_source_url_is_admitted_identity_only() -> None:
    assert _canonical_source_url(REPOSITORY) == REPOSITORY.canonical


def test_request_binding_is_validated_fail_closed(tmp_path: Path) -> None:
    request = _request()
    validate_source_binding(request.expected_ref, request.expected_commit)
    with pytest.raises(SourceIdentityMismatch):
        validate_source_binding(request.expected_ref, "abc123")


def test_workspace_git_readback_rejects_wrong_head(tmp_path, monkeypatch) -> None:
    from sentinelx_core import user_git

    calls: list[tuple] = []

    async def fake_run(root, *args, timeout, env=None):
        del timeout, env
        calls.append(args)
        if args[:2] == ("rev-parse", "--show-toplevel"):
            return 0, str(root).encode(), b""
        if args[:1] == ("rev-parse",):
            return 0, (args[1] if args[1] != "HEAD" else "b" * 40).encode(), b""
        if args[:1] == ("branch",):
            return 0, b"main", b""
        if args[:2] == ("remote", "get-url"):
            return 0, b"https://github.com/bewaterhere-coder/sentinelx-cloud-core", b""
        if args[:1] == ("status",):
            return 0, b"", b""
        return 1, b"", b"unexpected"

    monkeypatch.setattr(user_git, "run_user_scoped_git", fake_run)
    workspace = tmp_path / "ws"
    workspace.mkdir()
    import asyncio

    with pytest.raises(Exception) as excinfo:
        asyncio.run(
            _workspace_git_readback(
                workspace,
                expected_commit="a" * 40,
                logical_branch="main",
                origin_url=REPOSITORY.canonical,
            )
        )
    assert "HEAD" in str(excinfo.value) or "readback" in str(excinfo.value).lower()
    assert calls  # the readback actually exercised the user-scoped transport


def test_materialization_requires_windows(tmp_path: Path, monkeypatch) -> None:
    import sys

    from sentinelx_core.devforge_workspace_materialization import (
        DevforgeMaterializationError,
        run_devforge_workspace_materialization,
    )

    monkeypatch.setattr(sys, "platform", "linux")
    mutation_policy = MutationExecutionPolicy(
        configured=True,
        scoped_mutation_enabled=True,
        workspace_root=tmp_path,
        protected_roots=(tmp_path,),
        scope_ttl_seconds=600,
        evidence_retention_days=7,
    )
    with pytest.raises(DevforgeMaterializationError):
        import asyncio

        asyncio.run(
            run_devforge_workspace_materialization(
                mutation_policy,
                mutation_policy,
                tmp_path / "state",
                _request(),
            )
        )
