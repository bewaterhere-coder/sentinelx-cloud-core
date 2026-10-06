"""PR-015/S01: bounded devforge_direct_codex contract, policy and readiness."""
from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from sentinelx_core.executor import HandlerError
from sentinelx_core.handlers import build_registry
from sentinelx_core.handlers.basic import make_capabilities_handler
from sentinelx_core.handlers.devforge_runtime import make_devforge_runtime_provider
from sentinelx_core.handlers.direct_codex import (
    CONTRACT_ID,
    ENDPOINT_NAME,
    EXECUTE_TASK_ACTION,
    FEATURE_ID,
    _FORBIDDEN_FIELDS,
    make_devforge_direct_codex_provider,
)
from sentinelx_core.handlers.local_api import make_local_api_handler
from sentinelx_core.operation_registry import (
    FirewallCoverage,
    RepositoryEffect,
    canonical_repository_mutation_firewall_feature,
    canonical_repository_mutation_firewall_readiness,
    make_local_api_effect_inventory,
)
from sentinelx_core.policy import DirectCodexPolicy, MutationExecutionPolicy, Policy
from sentinelx_core.request_context import RequestContext


def _context() -> RequestContext:
    return RequestContext("req-s01", "local_api", None, datetime.now(UTC))


def _admitted_policy(tmp_path: Path, **overrides: Any) -> Policy:
    workspace = tmp_path / "devforge-workspaces"
    workspace.mkdir(parents=True, exist_ok=True)
    direct_codex = DirectCodexPolicy(
        configured=True,
        enabled=True,
        workspace_root=workspace,
        supported_platform="windows",
        timeout_seconds=60,
        max_result_bytes=4096,
    )
    if overrides:
        direct_codex = replace(direct_codex, **overrides)
    return Policy(
        upload_base=tmp_path / "uploads",
        mutation_execution=MutationExecutionPolicy(configured=True, scoped_mutation_enabled=True),
        direct_codex=direct_codex,
    )


def _repository() -> dict[str, str]:
    return {"vcs": "git", "authority": "github.com", "path": "bewaterhere-coder/sentinelx-cloud-core"}


def _lineage() -> dict[str, str]:
    return {
        "project_id": "sentinelx-cloud-core",
        "task_id": "PR-015-direct-codex-development-host-invocation-bridge-v1",
        "run_id": "run-1",
        "attempt_id": "attempt-1",
        "slice_id": "S01",
    }


def _valid_params() -> dict[str, Any]:
    return {
        "repository": _repository(),
        "lineage": _lineage(),
        "development": {
            "action": "implementation",
            "requirement_ref": "docs/requirements/PR-015.md",
            "plan_ref": "docs/plans/PR-015-plan.md",
        },
        "transport": {
            "type": "github-pr",
            "pr_number": 15,
            "branch": "task/direct-codex-development-host-invocation-bridge-v1",
            "expected_remote_sha": "0" * 40,
        },
    }


def _run(handler, *args):
    return asyncio.run(handler(*args))


def _flatten_property_names(node: Any) -> set[str]:
    names: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            names.add(str(key))
            names |= _flatten_property_names(value)
    elif isinstance(node, list):
        for value in node:
            names |= _flatten_property_names(value)
    return names


# ── provider absence without Host policy opt-in ──────────────────────────


def test_provider_absent_when_policy_opt_in_is_absent(tmp_path: Path) -> None:
    provider = make_devforge_direct_codex_provider(Policy(upload_base=tmp_path))
    assert provider.available_actions() == ()
    with pytest.raises(HandlerError) as exc:
        provider.describe()
    assert exc.value.code == "endpoint_not_available"


def test_local_api_op_absent_when_no_builtin_is_admitted(tmp_path: Path) -> None:
    registry = build_registry(policy=Policy(upload_base=tmp_path))
    assert "local_api" not in registry


# ── closed action schema ────────────────────────────────────────────────


def test_describe_exposes_only_bounded_closed_fields(tmp_path: Path) -> None:
    provider = make_devforge_direct_codex_provider(_admitted_policy(tmp_path))
    described = provider.describe()
    schema = described["actions"][EXECUTE_TASK_ACTION]["params_schema"]

    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {"repository", "lineage", "development", "transport"}
    assert _flatten_property_names(schema) & _FORBIDDEN_FIELDS == set()

    for block in ("repository", "lineage", "development", "transport"):
        assert schema["properties"][block]["additionalProperties"] is False


@pytest.mark.parametrize("field", sorted(_FORBIDDEN_FIELDS))
def test_execute_task_rejects_caller_execution_fields(tmp_path: Path, field: str) -> None:
    provider = make_devforge_direct_codex_provider(_admitted_policy(tmp_path))
    params = _valid_params()
    params[field] = "caller-owned"
    with pytest.raises(HandlerError) as exc:
        _run(provider.call, _context(), EXECUTE_TASK_ACTION, params)
    assert exc.value.code == "invalid_payload"


def test_execute_task_rejects_extra_nested_fields(tmp_path: Path) -> None:
    provider = make_devforge_direct_codex_provider(_admitted_policy(tmp_path))
    params = _valid_params()
    params["transport"]["remote_url"] = "git@github.com:example/repo.git"
    with pytest.raises(HandlerError) as exc:
        _run(provider.call, _context(), EXECUTE_TASK_ACTION, params)
    assert exc.value.code == "invalid_payload"


def test_execute_task_rejects_missing_required_blocks(tmp_path: Path) -> None:
    provider = make_devforge_direct_codex_provider(_admitted_policy(tmp_path))
    params = _valid_params()
    del params["lineage"]
    with pytest.raises(HandlerError) as exc:
        _run(provider.call, _context(), EXECUTE_TASK_ACTION, params)
    assert exc.value.code == "invalid_payload"


def test_execution_fails_closed_until_containment_is_proven(tmp_path: Path) -> None:
    provider = make_devforge_direct_codex_provider(_admitted_policy(tmp_path))
    with pytest.raises(HandlerError) as exc:
        _run(provider.call, _context(), EXECUTE_TASK_ACTION, _valid_params())
    assert exc.value.code == "direct_codex_execution_unavailable"


# ── effect / readiness projection ───────────────────────────────────────


def test_execute_task_is_process_mutation_without_proven_containment(tmp_path: Path) -> None:
    provider = make_devforge_direct_codex_provider(_admitted_policy(tmp_path))
    resolution = provider.repository_effect(EXECUTE_TASK_ACTION)

    assert resolution.effect is RepositoryEffect.PROCESS_MUTATION
    assert resolution.coverage is FirewallCoverage.UNPROVEN

    policy = _admitted_policy(tmp_path)
    readiness = canonical_repository_mutation_firewall_readiness(
        {"local_api": lambda payload: {}},
        policy,
        builtin_local_api_providers={ENDPOINT_NAME: provider},
        platform_name="Windows",
    )
    assert readiness.effective_surface_ready is False
    assert any("direct_codex_containment_unproven" in reason for reason in readiness.reasons)


def test_readiness_projection_is_false_until_live_prerequisites(tmp_path: Path) -> None:
    provider = make_devforge_direct_codex_provider(_admitted_policy(tmp_path))
    projection = provider.readiness()

    assert projection["available"] is False
    assert projection["verified"] is False
    assert projection["contract_id"] == CONTRACT_ID
    assert projection["reason"] == "direct_codex_containment_unproven"


def test_same_builtin_map_feeds_dispatch_and_firewall_projection(tmp_path: Path) -> None:
    policy = _admitted_policy(tmp_path)
    dispatch = build_registry(policy=policy)
    assert "local_api" in dispatch

    listed = _run(dispatch["local_api"], {"operation": "list"})
    names = {entry["name"] for entry in listed["endpoints"]}
    assert ENDPOINT_NAME in names

    handler = make_capabilities_handler(
        policy,
        ops_supported=lambda: dispatch.keys(),
        canonical_firewall_feature=lambda: canonical_repository_mutation_firewall_feature(
            dispatch, policy, platform_name="Windows"
        ),
        direct_codex_feature=lambda: make_devforge_direct_codex_provider(policy).readiness(),
    )
    capabilities = _run(handler, {})
    assert capabilities["execution_features"][FEATURE_ID]["contract_id"] == CONTRACT_ID


def test_devforge_runtime_effect_metadata_is_deterministic(tmp_path: Path) -> None:
    enabled = make_devforge_runtime_provider(
        Policy(
            upload_base=tmp_path,
            mutation_execution=MutationExecutionPolicy(
                configured=True, scoped_mutation_enabled=True
            ),
        ),
        lambda payload: {},
    )
    assert enabled.repository_effect("provision_scope").effect is (
        RepositoryEffect.NON_REPOSITORY_MUTATION
    )
    assert enabled.repository_effect("provision_scope").coverage is FirewallCoverage.NOT_REQUIRED
    assert enabled.repository_effect("execute_scoped").effect is RepositoryEffect.PROCESS_MUTATION
    assert enabled.repository_effect("execute_scoped").coverage is FirewallCoverage.PROVEN
    assert enabled.repository_effect("unknown_action").effect is RepositoryEffect.UNKNOWN

    disabled = make_devforge_runtime_provider(Policy(upload_base=tmp_path), lambda payload: {})
    assert disabled.repository_effect("execute_scoped").effect is RepositoryEffect.UNKNOWN


def test_future_process_builtin_without_metadata_fails_closed(tmp_path: Path) -> None:
    class _FutureProcessBuiltin:
        name = "future_process_builtin"

        def available_actions(self) -> tuple[str, ...]:
            return ("future_process_action",)

    policy = Policy(upload_base=tmp_path)
    inventory = make_local_api_effect_inventory(
        policy, builtin_providers={_FutureProcessBuiltin.name: _FutureProcessBuiltin()}
    )
    resolutions = tuple(inventory())

    assert resolutions
    assert any(
        resolution.effect is RepositoryEffect.UNKNOWN
        and resolution.selector == "future_process_builtin/future_process_action"
        and resolution.reason == "builtin_effect_metadata_unavailable"
        for resolution in resolutions
    )

    readiness = canonical_repository_mutation_firewall_readiness(
        {"local_api": lambda payload: {}},
        policy,
        builtin_local_api_providers={_FutureProcessBuiltin.name: _FutureProcessBuiltin()},
        platform_name="Windows",
    )
    assert readiness.effective_surface_ready is False


def test_generic_exec_remains_unproven_process_mutation(tmp_path: Path) -> None:
    policy = _admitted_policy(tmp_path)
    dispatch = build_registry(policy=policy)
    assert "exec" in dispatch

    readiness = canonical_repository_mutation_firewall_readiness(
        dispatch, policy, platform_name="Windows"
    )
    assert readiness.effective_surface_ready is False


# ── policy-owned admission ──────────────────────────────────────────────


def test_policy_parses_direct_codex_block(tmp_path: Path) -> None:
    workspace = tmp_path / "root"
    workspace.mkdir(parents=True, exist_ok=True)
    policy = Policy.from_dict(
        {
            "direct_codex": {
                "enabled": True,
                "workspace_root": str(workspace),
                "supported_platform": "windows",
                "timeout_seconds": 900,
                "max_result_bytes": 2048,
            }
        }
    )

    assert policy.direct_codex.configured is True
    assert policy.direct_codex.enabled is True
    assert policy.direct_codex.workspace_root == workspace.resolve()
    assert policy.direct_codex.missing_prerequisites(platform_name="Windows") == ()


def test_policy_admission_is_platform_and_opt_in_owned(tmp_path: Path) -> None:
    provider = make_devforge_direct_codex_provider(
        _admitted_policy(tmp_path), platform_name="Linux"
    )
    assert "direct_codex_unsupported_platform" in provider.admission_reasons
    assert provider.available_actions() == ()

    missing_root = make_devforge_direct_codex_provider(
        _admitted_policy(tmp_path, workspace_root=None)
    )
    assert "direct_codex_workspace_root_missing" in missing_root.admission_reasons

    disabled = make_devforge_direct_codex_provider(_admitted_policy(tmp_path, enabled=False))
    assert "direct_codex_disabled" in disabled.admission_reasons


def test_disabled_local_api_op_removes_the_contract(tmp_path: Path) -> None:
    policy = _admitted_policy(tmp_path)
    policy.disabled_ops = frozenset({"local_api"})
    registry = build_registry(policy=policy)

    assert "local_api" not in registry
