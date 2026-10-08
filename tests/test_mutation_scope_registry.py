from __future__ import annotations

import asyncio

from sentinelx_core.client import _parse_agent_message
from sentinelx_core.handlers import build_registry
from sentinelx_core.policy import Policy


def _call(handler, payload):
    return asyncio.run(handler(payload))


def test_mutation_scope_is_registered_by_default() -> None:
    registry = build_registry(policy=Policy.empty())
    assert "mutation_scope" in registry


def test_capabilities_derive_mutation_scope_from_registry_without_claiming_readiness() -> None:
    registry = build_registry(policy=Policy.empty())
    capabilities = _call(registry["capabilities"], {})

    assert capabilities["ops_supported"] == sorted(registry)
    assert "mutation_scope" in capabilities["ops_supported"]
    summary = _call(registry["capabilities"], {"detail": "summary"})
    assert set(summary["ops_supported"]) == set(registry)
    readiness = capabilities["execution_features"]["host_mutation_sandbox_v1"]
    assert readiness["available"] is False


def test_help_explains_dispatchability_is_not_mutation_readiness() -> None:
    registry = build_registry(policy=Policy.empty())
    result = _call(registry["help"], {"topic": "operations"})

    text = result["navigation"]["mutation_scope"]
    assert "dispatchability does not imply" in text
    assert "host_mutation_sandbox_v1" in text


def test_disabled_mutation_scope_is_unadvertised_and_hidden_from_help() -> None:
    policy = Policy.from_dict({"disabled_ops": ["mutation_scope"]})
    registry = build_registry(policy=policy)
    capabilities = _call(registry["capabilities"], {})
    help_result = _call(registry["help"], {"topic": "operations"})

    assert "mutation_scope" not in registry
    assert "mutation_scope" not in capabilities["ops_supported"]
    assert "mutation_scope" in capabilities["disabled_ops"]
    assert "mutation_scope" not in help_result["navigation"]


def test_executor_returns_unsupported_op_when_mutation_scope_is_disabled(tmp_path) -> None:
    from sentinelx_core.executor import Executor

    config = tmp_path / "config.yaml"
    config.write_text("allowed_commands: []\ndisabled_ops: [mutation_scope]\n", encoding="utf-8")
    executor = Executor(config_path=config)

    request = _parse_agent_message(
        {
            "type": "request",
            "id": "s03-disabled",
            "op": "mutation_scope",
            "payload": {"action": "inspect"},
        }
    )
    result = asyncio.run(executor.dispatch(request))
    assert result["ok"] is False
    assert result["error"]["code"] == "unsupported_op"


def test_unknown_wire_op_reaches_executor_and_returns_unsupported_op(tmp_path) -> None:
    from sentinelx_core.executor import Executor

    config = tmp_path / "config.yaml"
    config.write_text("allowed_commands: []\n", encoding="utf-8")
    executor = Executor(config_path=config)
    request = _parse_agent_message(
        {
            "type": "request",
            "id": "s03-future-op",
            "op": "future_registry_operation",
            "payload": {},
        }
    )

    result = asyncio.run(executor.dispatch(request))
    assert result["ok"] is False
    assert result["error"]["code"] == "unsupported_op"


def test_registry_contract_contains_no_dedicated_hub_tool_identity() -> None:
    registry = build_registry(policy=Policy.empty())
    assert "mutation_scope" in registry
    assert "sentinel_mutation_scope" not in registry
    assert "mcp_mutation_scope" not in registry
