"""PR-015/S01: bounded devforge_direct_codex contract, policy and readiness."""
from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from sentinelx_core.executor import HandlerError
from sentinelx_core.handlers import build_registry
from sentinelx_core.handlers.basic import make_capabilities_handler
from sentinelx_core.handlers.devforge_runtime import make_devforge_runtime_provider
from sentinelx_core.handlers.direct_codex import (
    _FORBIDDEN_FIELDS,
    CONTRACT_ID,
    ENDPOINT_NAME,
    EXECUTE_TASK_ACTION,
    FEATURE_ID,
    make_devforge_direct_codex_provider,
)
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


def test_execution_fails_closed_until_containment_is_proven(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A verified proof is still the admission boundary.

    With no proof present the provider-owned lifecycle attempts to establish
    it; here the physical proof cannot even be attempted (no protected sibling
    exists), so the lifecycle must fail closed by itself — no caller-owned
    prove_containment call — and before any transport bootstrap or Codex
    mutation.
    """
    provider = make_devforge_direct_codex_provider(_admitted_policy(tmp_path))
    monkeypatch.setattr(
        "sentinelx_core.handlers.direct_codex._negative_target", lambda _workspace: None
    )
    with pytest.raises(HandlerError) as exc:
        _run(provider.call, _context(), EXECUTE_TASK_ACTION, _valid_params())
    assert exc.value.code == "direct_codex_execution_unavailable"
    # The proof failed BEFORE any repository/checkout mutation.
    assert list((tmp_path / "devforge-workspaces").rglob(".git")) == []


def test_verified_stale_proof_is_not_reused_across_workspaces(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A verified proof bound to another workspace/identity never authorizes
    execution: the provider re-proves for the current derived workspace."""
    provider = make_devforge_direct_codex_provider(_admitted_policy(tmp_path))
    provider._containment_proof = {
        "verified": True,
        "binding": {
            "repository": "git://github.com/other/repo",
            "task_id": "PR-OTHER",
            "run_id": "other-run",
            "attempt_id": "other-attempt",
            "slice_id": "S99",
            "workspace_digest": "not-this-workspace",
        },
    }
    reproof_tasks: list[str] = []

    async def _fake_prove(*, repository: Any, semantic: Any, timeout: Any = None) -> Any:
        reproof_tasks.append(semantic.task_id)
        return {"verified": False, "negative_probe": {"attempted": False}}

    monkeypatch.setattr(provider, "prove_containment", _fake_prove)
    with pytest.raises(HandlerError) as exc:
        _run(provider.call, _context(), EXECUTE_TASK_ACTION, _valid_params())
    assert exc.value.code == "direct_codex_execution_unavailable"
    # The stale proof did not authorize: a fresh provider-owned proof run was
    # attempted for the exact requested Task identity.
    assert reproof_tasks == ["PR-015-direct-codex-development-host-invocation-bridge-v1"]


def test_matching_bound_proof_is_reused_without_reproving(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A verified proof bound to the exact current workspace/Task identity is
    reused; the provider never re-proves (or re-runs fixtures) needlessly."""
    from sentinelx_core.direct_codex_workspace import derive_workspace
    from sentinelx_core.mutation_placement import RepositoryIdentity, SemanticIdentity

    provider = make_devforge_direct_codex_provider(_admitted_policy(tmp_path))
    repository = RepositoryIdentity(vcs="git", authority="github.com", path="o/r")
    semantic = SemanticIdentity(
        project_id="sentinelx-cloud-core",
        task_id="PR-015",
        run_id="run-1",
        attempt_id="attempt-1",
        slice_id="S04",
    )
    workspace = derive_workspace(provider._policy.direct_codex, repository, semantic)
    provider._containment_proof = {
        "verified": True,
        "real_sandbox_setup": {"codex_workspace_write_setup": True},
        "transport_context": {
            "kind": "user_scoped_git_v1",
            "probe_attempted": True,
            "verified": True,
            "non_interactive": True,
            "credential_material_exposed": False,
        },
        "binding": provider._proof_binding(repository, semantic, workspace),
    }

    def _fail(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("a bound proof must be reused, not re-proven")

    monkeypatch.setattr(provider, "prove_containment", _fail)
    proof = asyncio.run(
        provider._ensure_containment_proof(
            repository=repository, semantic=semantic, workspace=workspace
        )
    )
    assert proof["verified"] is True


def test_proof_binding_rejects_identity_and_verification_mismatch(tmp_path: Path) -> None:
    from sentinelx_core.direct_codex_workspace import derive_workspace
    from sentinelx_core.mutation_placement import RepositoryIdentity, SemanticIdentity

    provider = make_devforge_direct_codex_provider(_admitted_policy(tmp_path))
    repository = RepositoryIdentity(vcs="git", authority="github.com", path="o/r")
    semantic = SemanticIdentity(
        project_id="sentinelx-cloud-core",
        task_id="PR-015",
        run_id="run-1",
        attempt_id="attempt-1",
        slice_id="S04",
    )
    workspace = derive_workspace(provider._policy.direct_codex, repository, semantic)
    binding = provider._proof_binding(repository, semantic, workspace)

    bound = {
        "repository": repository,
        "semantic": semantic,
        "workspace": workspace,
    }
    # Same workspace digest but a different Task identity is not a match.
    assert (
        provider._proof_is_bound_to(
            {"verified": True, "binding": dict(binding, task_id="PR-016")}, **bound
        )
        is False
    )
    # An unverified proof never binds, even with a matching binding block.
    assert (
        provider._proof_is_bound_to({"verified": False, "binding": dict(binding)}, **bound)
        is False
    )
    # A proof without a binding block (legacy shape) never binds.
    assert provider._proof_is_bound_to({"verified": True}, **bound) is False
    # The exact binding matches only with both mandatory physical proofs.
    complete = {
        "verified": True,
        "binding": binding,
        "real_sandbox_setup": {"codex_workspace_write_setup": True},
        "transport_context": {
            "kind": "user_scoped_git_v1",
            "probe_attempted": True,
            "verified": True,
            "non_interactive": True,
            "credential_material_exposed": False,
        },
    }
    assert provider._proof_is_bound_to(complete, **bound) is True


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
    assert projection["proof"] == {
        "attempted": False,
        "disposition": "not_attempted",
    }
    assert projection["transport_context"] == {
        "kind": "user_scoped_git_v1",
        "probe_attempted": False,
        "verified": False,
        "non_interactive": True,
        "credential_material_exposed": False,
    }


@pytest.mark.asyncio
async def test_git_context_probe_uses_fixed_non_network_transport_argv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = make_devforge_direct_codex_provider(_admitted_policy(tmp_path))
    calls: list[tuple[Path, tuple[str, ...], float]] = []

    async def _transport(root: Path, *args: str, timeout: float):
        calls.append((root, args, timeout))
        return 0, b"git version fixture", b""

    monkeypatch.setattr("sentinelx_core.direct_codex_transport.transport_git", _transport)
    workspace = tmp_path / "devforge-workspaces" / "derived"
    workspace.mkdir()
    result = await provider._probe_transport_context(
        SimpleNamespace(path=workspace), 300.0
    )

    assert calls == [(workspace, ("--version",), 30.0)]
    assert result == {
        "kind": "user_scoped_git_v1",
        "probe_attempted": True,
        "verified": True,
        "non_interactive": True,
        "credential_material_exposed": False,
    }
    assert str(workspace) not in repr(result)
    assert "git version fixture" not in repr(result)


@pytest.mark.asyncio
async def test_git_context_probe_failure_is_sanitized_and_cause_aware(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = make_devforge_direct_codex_provider(_admitted_policy(tmp_path))

    async def _transport(root: Path, *args: str, timeout: float):
        return 9, b"private stdout", b"private path and credential"

    monkeypatch.setattr("sentinelx_core.direct_codex_transport.transport_git", _transport)
    workspace = tmp_path / "devforge-workspaces" / "derived-failure"
    workspace.mkdir()
    result = await provider._probe_transport_context(SimpleNamespace(path=workspace), 10.0)

    assert result["probe_attempted"] is True
    assert result["verified"] is False
    assert result["failure_class"] == "direct_codex_git_context_probe_failed"
    assert "private" not in repr(result)
    assert str(workspace) not in repr(result)


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
