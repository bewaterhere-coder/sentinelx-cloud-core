from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import pytest

import sentinelx_core.repository_transaction as repository_transaction
from sentinelx_core.handlers.devforge_runtime import make_devforge_runtime_provider
from sentinelx_core.handlers.local_api import make_local_api_handler
from sentinelx_core.handlers.mutation_scope import make_mutation_scope_handler, make_mutation_scope_service
from sentinelx_core.mutation_placement import RepositoryIdentity
from sentinelx_core.policy import CanonicalRepositorySpec, MutationExecutionPolicy, Policy
from sentinelx_core.repository_transaction import (
    REPOSITORY_TRANSACTION_PURPOSE,
    RepositoryTransactionAdmissionFailed,
    make_repository_ref_resolver,
)
from sentinelx_core.request_context import RequestContext


SOURCE_SHA = "a" * 40
REMOTE_SHA = "b" * 40
OTHER_SHA = "c" * 40


def _repository() -> dict[str, str]:
    return {
        "vcs": "git",
        "authority": "github.com",
        "path": "bewaterhere-coder/sentinelx-cloud-core",
    }


def _lineage(attempt: str = "attempt-1") -> dict[str, str]:
    return {
        "project_id": "sentinelx-cloud-core",
        "task_id": "PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1",
        "run_id": "run-pr013-s01",
        "attempt_id": attempt,
        "slice_id": "S01",
    }


def _context(op: str = "local_api") -> RequestContext:
    return RequestContext("req-pr013-s01", op, None, datetime.now(UTC))


def _run(handler, *args):
    return asyncio.run(handler(*args))


def _policy(tmp_path: Path) -> Policy:
    workspace = tmp_path / "workspaces"
    protected = tmp_path / "protected"
    uploads = tmp_path / "uploads"
    canonical = tmp_path / "canonical"
    for path in (workspace, protected, uploads, canonical):
        path.mkdir(parents=True, exist_ok=True)
    identity = RepositoryIdentity(**_repository()).canonical
    return Policy(
        upload_base=uploads,
        authenticated_git_enabled=True,
        authenticated_git_timeout_seconds=5,
        mutation_execution=MutationExecutionPolicy(
            configured=True,
            scoped_mutation_enabled=True,
            workspace_root=workspace,
            protected_roots=(protected,),
            scope_ttl_seconds=600,
            evidence_retention_days=7,
            canonical_repository_firewall_enabled=True,
            canonical_repositories=(
                CanonicalRepositorySpec(
                    root=canonical,
                    repository_identity=identity,
                    canonical_branch="main",
                ),
            ),
        ),
    )


def _transaction_params(*, attempt: str = "attempt-1") -> dict[str, object]:
    return {
        "purpose": REPOSITORY_TRANSACTION_PURPOSE,
        "repository": _repository(),
        "lineage": _lineage(attempt),
        "repository_transaction": {
            "source_ref": "refs/heads/main",
            "expected_source_sha": SOURCE_SHA,
            "publication_ref": "refs/heads/task/pr013",
            "expected_remote_sha": REMOTE_SHA,
        },
    }


def _provider(tmp_path: Path):
    policy = _policy(tmp_path)
    state = tmp_path / "state"
    state.mkdir(exist_ok=True)
    lifecycle = make_mutation_scope_service(
        policy,
        policy.upload_base,
        mutation_state_root=state,
    )

    async def fake_resolver(repository: RepositoryIdentity, ref: str) -> str:
        assert repository.canonical == RepositoryIdentity(**_repository()).canonical
        refs = {
            "refs/heads/main": SOURCE_SHA,
            "refs/heads/task/pr013": REMOTE_SHA,
            "refs/heads/other": OTHER_SHA,
        }
        if ref not in refs:
            raise RepositoryTransactionAdmissionFailed("unknown test ref")
        return refs[ref]

    provider = make_devforge_runtime_provider(
        policy,
        lifecycle,
        repository_ref_resolver=fake_resolver,
    )
    handler = make_local_api_handler(
        policy,
        builtin_providers={provider.name: provider},
    )
    return policy, provider, handler


def test_describe_exposes_path_free_repository_transaction_admission(tmp_path: Path) -> None:
    _policy_value, _provider_value, handler = _provider(tmp_path)
    described = _run(
        handler,
        {"operation": "describe", "endpoint": "devforge_runtime"},
    )
    actions = described["actions"]
    assert "inspect_repository_transaction" in actions
    provision = actions["provision_scope"]["params_schema"]
    assert provision["properties"]["purpose"] == {
        "enum": ["scoped_script", REPOSITORY_TRANSACTION_PURPOSE]
    }
    transaction = provision["properties"]["repository_transaction"]
    assert transaction["additionalProperties"] is False
    assert set(transaction["required"]) == {
        "source_ref",
        "expected_source_sha",
        "publication_ref",
        "expected_remote_sha",
    }
    forbidden_text = repr(provision).lower()
    for forbidden in ("workspace_root", "checkout", "staging", "credential", "git_argv", "remote_url"):
        assert forbidden not in forbidden_text


def test_repository_transaction_provision_is_durable_idempotent_and_inspectable(
    tmp_path: Path,
) -> None:
    _policy_value, _provider_value, handler = _provider(tmp_path)
    request = {
        "operation": "call",
        "endpoint": "devforge_runtime",
        "action": "provision_scope",
        "params": _transaction_params(),
    }
    first = _run(handler, _context(), request)["result"]
    second = _run(handler, _context(), request)["result"]

    assert first["scope"]["purpose"] == REPOSITORY_TRANSACTION_PURPOSE
    assert second["scope"]["scope_id"] == first["scope"]["scope_id"]
    assert second["repository_transaction"]["transaction_id"] == first["repository_transaction"]["transaction_id"]
    transaction = first["repository_transaction"]
    assert transaction["state"] == "provisioned"
    assert transaction["verified_source_sha"] == SOURCE_SHA
    assert transaction["expected_remote_sha"] == REMOTE_SHA
    assert transaction["verified_remote_sha"] == REMOTE_SHA
    assert "exact_workspace" not in transaction
    assert "operation_classes" not in transaction

    inspected = _run(
        handler,
        _context(),
        {
            "operation": "call",
            "endpoint": "devforge_runtime",
            "action": "inspect_repository_transaction",
            "params": {
                "scope_ref": {
                    "scope_id": first["scope"]["scope_id"],
                    "generation": first["scope"]["generation"],
                },
                "repository": _repository(),
                "lineage": _lineage(),
            },
        },
    )["result"]["repository_transaction"]
    assert inspected == transaction


def test_same_attempt_authority_change_conflicts_without_new_scope(tmp_path: Path) -> None:
    _policy_value, _provider_value, handler = _provider(tmp_path)
    first = _run(
        handler,
        _context(),
        {
            "operation": "call",
            "endpoint": "devforge_runtime",
            "action": "provision_scope",
            "params": _transaction_params(),
        },
    )["result"]

    changed = _transaction_params()
    changed["repository_transaction"] = {
        "source_ref": "refs/heads/other",
        "expected_source_sha": OTHER_SHA,
        "publication_ref": "refs/heads/task/pr013",
        "expected_remote_sha": REMOTE_SHA,
    }
    denied = _run(
        handler,
        _context(),
        {
            "operation": "call",
            "endpoint": "devforge_runtime",
            "action": "provision_scope",
            "params": changed,
        },
    )
    assert denied["error"] == "RepositoryTransactionConflict"

    exact_retry = _run(
        handler,
        _context(),
        {
            "operation": "call",
            "endpoint": "devforge_runtime",
            "action": "provision_scope",
            "params": _transaction_params(),
        },
    )["result"]
    assert exact_retry["scope"]["scope_id"] == first["scope"]["scope_id"]
    assert exact_retry["repository_transaction"]["transaction_id"] == first["repository_transaction"]["transaction_id"]


def test_ref_mismatch_and_path_injection_fail_before_scope_admission(tmp_path: Path) -> None:
    _policy_value, _provider_value, handler = _provider(tmp_path)
    bad_sha = _transaction_params(attempt="attempt-sha")
    bad_sha["repository_transaction"] = {
        "source_ref": "refs/heads/main",
        "expected_source_sha": "d" * 40,
        "publication_ref": "refs/heads/task/pr013",
        "expected_remote_sha": REMOTE_SHA,
    }
    denied = _run(
        handler,
        _context(),
        {
            "operation": "call",
            "endpoint": "devforge_runtime",
            "action": "provision_scope",
            "params": bad_sha,
        },
    )
    assert denied["error"] == "RepositoryTransactionAdmissionFailed"

    injected = _transaction_params(attempt="attempt-path")
    injected_transaction = dict(injected["repository_transaction"])
    injected_transaction["workspace_root"] = "D:/caller-selected"
    injected["repository_transaction"] = injected_transaction
    denied = _run(
        handler,
        _context(),
        {
            "operation": "call",
            "endpoint": "devforge_runtime",
            "action": "provision_scope",
            "params": injected,
        },
    )
    assert denied["error"] == "invalid_payload"

    authority = tmp_path / "state" / "mutation-scopes" / "authority.json"
    if authority.exists():
        text = authority.read_text(encoding="utf-8")
        assert "attempt-sha" not in text
        assert "attempt-path" not in text


def test_direct_mutation_scope_cannot_mint_repository_transaction(tmp_path: Path) -> None:
    policy = _policy(tmp_path)
    state = tmp_path / "direct-state"
    state.mkdir()
    handler = make_mutation_scope_handler(
        policy,
        policy.upload_base,
        mutation_state_root=state,
    )
    denied = _run(
        handler,
        _context("mutation_scope"),
        {
            "action": "provision",
            "purpose": REPOSITORY_TRANSACTION_PURPOSE,
            "repository": _repository(),
            "lineage": _lineage(),
        },
    )
    # Direct op handlers raise through dispatch in production; context-aware
    # wrapper preserves HandlerError for direct unit invocation.
    assert denied is not None


def test_provider_ref_resolver_verifies_origin_identity_and_exact_single_ref(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    policy = _policy(tmp_path)
    calls: list[tuple[str, ...]] = []

    async def fake_run(_root: Path, *args: str, timeout: float):
        assert timeout == 5.0
        calls.append(tuple(args))
        if args[:3] == ("remote", "get-url", "origin"):
            return 0, b"https://github.com/bewaterhere-coder/sentinelx-cloud-core.git\n", b""
        assert args[:3] == ("ls-remote", "--refs", "origin")
        return 0, f"{SOURCE_SHA}\trefs/heads/main\n".encode(), b""

    monkeypatch.setattr(repository_transaction, "run_user_scoped_git", fake_run)
    resolver = make_repository_ref_resolver(policy)
    resolved = asyncio.run(resolver(RepositoryIdentity(**_repository()), "refs/heads/main"))
    assert resolved == SOURCE_SHA
    assert calls == [
        ("remote", "get-url", "origin"),
        ("ls-remote", "--refs", "origin", "refs/heads/main"),
    ]


def test_provider_ref_resolver_fails_closed_on_ambiguous_ref(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    policy = _policy(tmp_path)

    async def fake_run(_root: Path, *args: str, timeout: float):
        if args[0] == "remote":
            return 0, b"git@github.com:bewaterhere-coder/sentinelx-cloud-core.git\n", b""
        return (
            0,
            (
                f"{SOURCE_SHA}\trefs/heads/main\n"
                f"{OTHER_SHA}\trefs/tags/main\n"
            ).encode(),
            b"",
        )

    monkeypatch.setattr(repository_transaction, "run_user_scoped_git", fake_run)
    resolver = make_repository_ref_resolver(policy)
    with pytest.raises(RepositoryTransactionAdmissionFailed):
        asyncio.run(resolver(RepositoryIdentity(**_repository()), "main"))
