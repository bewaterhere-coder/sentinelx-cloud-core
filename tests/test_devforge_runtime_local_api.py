from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from sentinelx_core.executor import HandlerError
from sentinelx_core.handlers import build_registry
from sentinelx_core.handlers.devforge_runtime import (
    make_devforge_execute_scoped_adapter,
    make_devforge_runtime_provider,
)
from sentinelx_core.handlers.local_api import make_local_api_handler
from sentinelx_core.handlers.mutation_scope import make_mutation_scope_service
from sentinelx_core.policy import (
    LocalApiAction,
    LocalApiEndpoint,
    MutationExecutionPolicy,
    Policy,
)
from sentinelx_core.request_context import RequestContext


def _policy(tmp_path: Path, disabled: frozenset[str] = frozenset()) -> Policy:
    workspace = tmp_path / "workspaces"
    protected = tmp_path / "protected"
    uploads = tmp_path / "uploads"
    for path in (workspace, protected, uploads):
        path.mkdir(parents=True, exist_ok=True)
    return Policy(
        disabled_ops=disabled,
        upload_base=uploads,
        mutation_execution=MutationExecutionPolicy(
            configured=True,
            scoped_mutation_enabled=True,
            workspace_root=workspace,
            protected_roots=(protected,),
            scope_ttl_seconds=600,
            evidence_retention_days=7,
        ),
    )


def _context() -> RequestContext:
    return RequestContext("req-s06", "local_api", None, datetime.now(UTC))


def _repository() -> dict[str, str]:
    return {
        "vcs": "git",
        "authority": "github.com",
        "path": "bewaterhere-coder/sentinelx-cloud-core",
    }


def _lineage() -> dict[str, str]:
    return {
        "project_id": "sentinelx-cloud-core",
        "task_id": "PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1",
        "run_id": "s06",
        "attempt_id": "attempt-1",
        "slice_id": "S06",
    }


def _run(handler, *args):
    return asyncio.run(handler(*args))


def test_no_policy_no_external_keeps_local_api_unregistered() -> None:
    assert "local_api" not in build_registry(policy=Policy.empty())


def test_eligible_host_lists_bounded_builtin(tmp_path: Path) -> None:
    registry = build_registry(policy=_policy(tmp_path))
    listed = _run(registry["local_api"], {"operation": "list"})
    entry = next(
        item for item in listed["endpoints"] if item["name"] == "devforge_runtime"
    )
    assert entry["provider_kind"] == "builtin"
    assert entry["contract_revision"] == 1

    described = _run(
        registry["local_api"],
        {"operation": "describe", "endpoint": "devforge_runtime"},
    )
    assert described["contract_id"] == "devforge_runtime"
    assert set(described["actions"]) == {
        "provision_scope",
        "revalidate_scope",
        "inspect_scope",
        "terminalize_scope",
        "execute_scoped",
    }


def test_builtin_lifecycle_reuses_canonical_service(tmp_path: Path) -> None:
    handler = build_registry(policy=_policy(tmp_path))["local_api"]
    provisioned = _run(
        handler,
        _context(),
        {
            "operation": "call",
            "endpoint": "devforge_runtime",
            "action": "provision_scope",
            "params": {
                "purpose": "scoped_script",
                "repository": _repository(),
                "lineage": _lineage(),
            },
        },
    )
    scope = provisioned["result"]["scope"]

    inspected = _run(
        handler,
        _context(),
        {
            "operation": "call",
            "endpoint": "devforge_runtime",
            "action": "inspect_scope",
            "params": {
                "scope_ref": {
                    "scope_id": scope["scope_id"],
                    "generation": scope["generation"],
                },
                "repository": _repository(),
                "lineage": _lineage(),
            },
        },
    )
    assert inspected["result"]["scope"]["scope_digest"] == scope["scope_digest"]


def test_disabled_mutation_scope_hides_and_denies_lifecycle(tmp_path: Path) -> None:
    policy = _policy(tmp_path, frozenset({"mutation_scope"}))
    state = tmp_path / "state"
    state.mkdir()
    provider = make_devforge_runtime_provider(
        policy,
        make_mutation_scope_service(
            policy,
            policy.upload_base,
            mutation_state_root=state,
        ),
    )
    handler = make_local_api_handler(
        policy,
        builtin_providers={provider.name: provider},
    )
    listed = _run(handler, {"operation": "list"})
    assert not any(
        item["name"] == "devforge_runtime" for item in listed["endpoints"]
    )

    denied = _run(
        handler,
        _context(),
        {
            "operation": "call",
            "endpoint": "devforge_runtime",
            "action": "provision_scope",
            "params": {
                "purpose": "scoped_script",
                "repository": _repository(),
                "lineage": _lineage(),
            },
        },
    )
    assert denied["error"] == "operation_disabled"


def test_disabled_script_run_filters_optional_execute_adapter(tmp_path: Path) -> None:
    policy = _policy(tmp_path, frozenset({"script_run"}))
    state = tmp_path / "state"
    state.mkdir()

    async def fake_execute(_context, _params):
        return {"unexpected": True}

    provider = make_devforge_runtime_provider(
        policy,
        make_mutation_scope_service(
            policy,
            policy.upload_base,
            mutation_state_root=state,
        ),
        execute_scoped_adapter=fake_execute,
    )
    handler = make_local_api_handler(
        policy,
        builtin_providers={provider.name: provider},
    )
    described = _run(
        handler,
        {"operation": "describe", "endpoint": "devforge_runtime"},
    )
    assert "execute_scoped" not in described["actions"]

    denied = _run(
        handler,
        _context(),
        {
            "operation": "call",
            "endpoint": "devforge_runtime",
            "action": "execute_scoped",
            "params": {},
        },
    )
    assert denied["error"] == "operation_disabled"


def test_external_name_collision_preserves_external(tmp_path: Path, caplog) -> None:
    base = _policy(tmp_path)
    external = LocalApiEndpoint(
        name="devforge_runtime",
        transport="unix",
        path="/tmp/external.sock",
        protocol="jsonrpc",
        actions={"external.echo": LocalApiAction(method="external.echo")},
    )
    policy = replace(base, local_apis={external.name: external})
    state = tmp_path / "state"
    state.mkdir()
    provider = make_devforge_runtime_provider(
        policy,
        make_mutation_scope_service(
            policy,
            policy.upload_base,
            mutation_state_root=state,
        ),
    )
    with caplog.at_level("WARNING"):
        handler = make_local_api_handler(
            policy,
            builtin_providers={provider.name: provider},
        )

    described = _run(
        handler,
        {"operation": "describe", "endpoint": "devforge_runtime"},
    )
    assert described["protocol"] == "jsonrpc"
    assert set(described["actions"]) == {"external.echo"}
    assert "provider_kind" not in described
    assert any(
        record.getMessage() == "builtin_local_api_name_conflict"
        for record in caplog.records
    )


def test_disabled_local_api_removes_outer_op(tmp_path: Path) -> None:
    policy = _policy(tmp_path, frozenset({"local_api"}))
    assert "local_api" not in build_registry(policy=policy)


def _execute_params() -> dict[str, object]:
    return {
        "scope_ref": {"scope_id": "scope-s07", "generation": 1},
        "repository": _repository(),
        "lineage": {**_lineage(), "run_id": "s07", "slice_id": "S07"},
        "interpreter": "python3",
        "content": "print('s07')",
        "args": ["arg"],
        "cwd": ".",
        "env": {"SAFE_VALUE": "1"},
        "timeout": 30,
    }


def test_execute_scoped_adapter_injects_fixed_authority_and_projects_result() -> None:
    captured: dict[str, object] = {}

    async def fake_profiled(context, payload):
        captured["context"] = context
        captured["payload"] = payload
        return {
            "ok": True,
            "interpreter": "python3",
            "sudo": False,
            "cwd": "D:/provider/private/workspace",
            "cleanup": True,
            "execution_profile": "scoped_mutation",
            "command": ["D:/provider/private/python.exe", "script.py"],
            "output": "s07",
            "returncode": 0,
            "mutation_scope_ref": {"scope_id": "scope-s07", "generation": 1},
            "audit_operation_id": "audit-s07",
            "terminal_state": "terminal",
            "script_path": "D:/provider/private/workspace/script.py",
            "workdir": "D:/provider/private/workspace",
            "future_debug_path": "D:/provider/private/future",
            "unexpected": "drop-me",
        }

    adapter = make_devforge_execute_scoped_adapter(fake_profiled)
    context = _context()
    result = _run(adapter, context, _execute_params())
    payload = captured["payload"]

    assert captured["context"] is context
    assert isinstance(payload, dict)
    assert payload["execution_profile"] == "scoped_mutation"
    assert payload["cleanup"] is True
    assert payload["mutation"] == {
        "scope_ref": {"scope_id": "scope-s07", "generation": 1}
    }
    assert set(result) == {
        "ok",
        "interpreter",
        "returncode",
        "output",
        "execution_profile",
        "audit_operation_id",
        "mutation_scope_ref",
        "terminal_state",
    }
    assert "cwd" not in result
    assert "command" not in result
    assert "script_path" not in result
    assert "workdir" not in result
    assert "future_debug_path" not in result
    assert "unexpected" not in result


def test_execute_scoped_adapter_rejects_caller_authority_overrides() -> None:
    called = False

    async def fake_profiled(_context, _payload):
        nonlocal called
        called = True
        return {"execution_profile": "scoped_mutation"}

    adapter = make_devforge_execute_scoped_adapter(fake_profiled)
    context = _context()
    cases = [
        ("cleanup", False),
        ("execution_profile", "operator_unrestricted"),
        ("workspace_id", "caller-workspace"),
        ("operation_classes", ["anything"]),
    ]
    for field, value in cases:
        params = _execute_params()
        params[field] = value
        try:
            _run(adapter, context, params)
        except HandlerError as exc:
            assert exc.code == "invalid_payload"
        else:
            raise AssertionError(f"caller authority field {field} was accepted")

    nested = _execute_params()
    scope_ref = dict(nested["scope_ref"])
    scope_ref["workspace_id"] = "caller-workspace"
    nested["scope_ref"] = scope_ref
    try:
        _run(adapter, context, nested)
    except HandlerError as exc:
        assert exc.code == "invalid_payload"
    else:
        raise AssertionError("nested caller authority field was accepted")

    assert called is False
