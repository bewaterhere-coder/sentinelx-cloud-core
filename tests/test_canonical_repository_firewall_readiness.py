from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from sentinelx_core.executor import Executor
from sentinelx_core.handlers import build_registry
from sentinelx_core.handlers.basic import make_capabilities_handler
from sentinelx_core.operation_registry import (
    CANONICAL_REPOSITORY_MUTATION_FIREWALL_CAPABILITY,
    canonical_repository_mutation_firewall_feature,
    canonical_repository_mutation_firewall_readiness,
)
from sentinelx_core.policy import Policy


async def _noop(_payload):
    return {"ok": True}


def _repo_entry(root: Path) -> dict[str, object]:
    return {
        "root": str(root),
        "repository": {
            "vcs": "git",
            "authority": "github.com",
            "path": "owner/repo",
        },
        "canonical_branch": "main",
    }


def _policy(
    tmp_path: Path,
    *,
    firewall_enabled: bool = True,
    local_apis: dict[str, object] | None = None,
) -> Policy:
    data: dict[str, object] = {
        "disabled_ops": ["exec", "script_run"],
        "mutation_execution": {
            "canonical_repository_firewall_enabled": firewall_enabled,
            "canonical_repositories": [_repo_entry(tmp_path / "canonical")],
        },
    }
    if local_apis is not None:
        data["local_apis"] = local_apis
    return Policy.from_dict(data)


def test_complete_windows_effective_surface_is_ready(tmp_path: Path) -> None:
    policy = _policy(tmp_path)
    dispatch = build_registry(policy=policy)
    readiness = canonical_repository_mutation_firewall_readiness(
        dispatch, policy, platform_name="Windows"
    )
    assert readiness.ready is True
    assert readiness.inventory_ready is True
    assert readiness.effective_surface_ready is True
    assert readiness.platform_supported is True
    assert readiness.reasons == ()


def test_policy_disabled_preserves_ops_but_not_capability(tmp_path: Path) -> None:
    policy = _policy(tmp_path, firewall_enabled=False)
    dispatch = build_registry(policy=policy)
    readiness = canonical_repository_mutation_firewall_readiness(
        dispatch, policy, platform_name="Windows"
    )
    assert "edit" in dispatch
    assert readiness.ready is False
    assert "canonical_repository_firewall_disabled" in readiness.reasons


def test_non_windows_platform_remains_unavailable(tmp_path: Path) -> None:
    policy = _policy(tmp_path)
    readiness = canonical_repository_mutation_firewall_readiness(
        build_registry(policy=policy), policy, platform_name="Linux"
    )
    assert readiness.ready is False
    assert readiness.platform_supported is False
    assert "unsupported_platform" in readiness.reasons


def test_future_unknown_effect_removes_capability(tmp_path: Path) -> None:
    policy = _policy(tmp_path)
    dispatch = build_registry(policy=policy)
    dispatch["future_repository_tool"] = _noop
    readiness = canonical_repository_mutation_firewall_readiness(
        dispatch, policy, platform_name="Windows"
    )
    assert readiness.ready is False
    assert "future_repository_tool:unknown" in readiness.reasons


def _external_local_api(effect: str | None) -> dict[str, object]:
    action: dict[str, object] = {"method": "repo.inspect"}
    if effect is not None:
        action["repository_effect"] = effect
    return {
        "secret-endpoint": {
            "transport": "unix",
            "protocol": "jsonrpc",
            "path": "/tmp/secret.sock",
            "actions": {"sensitive-action": action},
        }
    }


def test_unknown_local_api_is_unavailable_without_leaking_selector(
    tmp_path: Path,
) -> None:
    policy = _policy(tmp_path, local_apis=_external_local_api(None))
    readiness = canonical_repository_mutation_firewall_readiness(
        build_registry(policy=policy), policy, platform_name="Windows"
    )
    assert readiness.ready is False
    assert "local_api:external_local_api_effect_unknown" in readiness.reasons
    diagnostic = " ".join(readiness.reasons)
    assert "secret-endpoint" not in diagnostic
    assert "sensitive-action" not in diagnostic
    assert "/tmp/secret.sock" not in diagnostic


def test_explicit_read_only_local_api_is_compatible_with_readiness(
    tmp_path: Path,
) -> None:
    policy = _policy(tmp_path, local_apis=_external_local_api("read_only"))
    readiness = canonical_repository_mutation_firewall_readiness(
        build_registry(policy=policy), policy, platform_name="Windows"
    )
    assert readiness.ready is True


@pytest.mark.asyncio
async def test_capabilities_projects_same_core_readiness(tmp_path: Path) -> None:
    policy = _policy(tmp_path)
    dispatch = build_registry(policy=policy)
    handler = make_capabilities_handler(
        policy,
        ops_supported=lambda: dispatch.keys(),
        canonical_firewall_feature=lambda: canonical_repository_mutation_firewall_feature(
            dispatch, policy, platform_name="Windows"
        ),
    )
    result = await handler({"detail": "full"})
    feature = result["execution_features"][
        CANONICAL_REPOSITORY_MUTATION_FIREWALL_CAPABILITY
    ]
    assert feature["available"] is True
    assert feature["verified"] is True
    assert "host_mutation_sandbox_v1" in result["execution_features"]


def test_executor_hello_capability_projection_is_conditional(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg = tmp_path / "config.yaml"
    policy_data: dict[str, object] = {
        "disabled_ops": ["exec", "script_run"],
        "mutation_execution": {
            "canonical_repository_firewall_enabled": True,
            "canonical_repositories": [_repo_entry(tmp_path / "canonical")],
        },
    }
    cfg.write_text(yaml.safe_dump(policy_data), encoding="utf-8")
    monkeypatch.setattr(
        "sentinelx_core.operation_registry.platform.system", lambda: "Windows"
    )
    assert (
        CANONICAL_REPOSITORY_MUTATION_FIREWALL_CAPABILITY
        in Executor(cfg).capability_names()
    )
    monkeypatch.setattr(
        "sentinelx_core.operation_registry.platform.system", lambda: "Darwin"
    )
    assert (
        CANONICAL_REPOSITORY_MUTATION_FIREWALL_CAPABILITY
        not in Executor(cfg).capability_names()
    )
