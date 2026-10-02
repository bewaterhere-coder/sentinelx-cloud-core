from __future__ import annotations

import dataclasses

from sentinelx_core.handlers import build_registry
from sentinelx_core.operation_registry import (
    FirewallCoverage,
    RepositoryEffect,
    build_effect_registry,
)
from sentinelx_core.policy import Policy


async def _noop(_payload):
    return {"ok": True}


def _policy(**kw) -> Policy:
    return dataclasses.replace(Policy.empty(), **kw)


def test_effect_accounting_is_bound_to_effective_dispatch_keys() -> None:
    dispatch = build_registry(policy=_policy())
    effects = build_effect_registry(dispatch, _policy())

    assert set(effects) == set(dispatch)
    assert effects.registration("file_export_init").exposure.value == "internal"
    assert effects.firewall_readiness.ready is False
    assert any(reason.startswith("exec:") for reason in effects.firewall_readiness.reasons)
    assert any(reason.startswith("script_run:") for reason in effects.firewall_readiness.reasons)


def test_future_unclassified_model_facing_operation_fails_readiness() -> None:
    policy = _policy()
    dispatch = build_registry(policy=policy)
    dispatch["future_repository_tool"] = _noop

    effects = build_effect_registry(dispatch, policy)

    assert effects.resolve_effect("future_repository_tool").effect is RepositoryEffect.UNKNOWN
    assert any(
        reason.startswith("future_repository_tool:")
        for reason in effects.firewall_readiness.reasons
    )


def test_disabled_operation_is_removed_before_effect_accounting() -> None:
    policy = _policy(disabled_ops=frozenset({"script_run"}))
    dispatch = build_registry(policy=policy)
    effects = build_effect_registry(dispatch, policy)

    assert "script_run" not in dispatch
    assert effects.registration("script_run") is None
    assert not any(reason.startswith("script_run:") for reason in effects.firewall_readiness.reasons)


def test_git_selector_effects_are_bounded_and_unknown_fails_closed() -> None:
    policy = _policy()
    effects = build_effect_registry(build_registry(policy=policy), policy)

    assert effects.resolve_effect("git", {"operation": "diff"}).effect is RepositoryEffect.READ_ONLY
    assert effects.resolve_effect("git", {"operation": "apply_patch"}).coverage is FirewallCoverage.PROVEN
    assert effects.resolve_effect(
        "git", {"operation": "apply_patch", "dry_run": True}
    ).effect is RepositoryEffect.READ_ONLY
    unknown = effects.resolve_effect("git", {"operation": "checkout"})
    assert unknown.effect is RepositoryEffect.UNKNOWN
    assert unknown.reason == "unknown_git_selector"


def _local_api_policy(effect: str | None) -> Policy:
    action = {"method": "repo.inspect"}
    if effect is not None:
        action["repository_effect"] = effect
    return Policy.from_dict(
        {
            "local_apis": {
                "fixture": {
                    "transport": "unix",
                    "protocol": "jsonrpc",
                    "path": "/tmp/fixture.sock",
                    "actions": {"inspect": action},
                }
            }
        }
    )


def test_configured_local_api_action_without_effect_metadata_is_unknown() -> None:
    policy = _local_api_policy(None)
    effects = build_effect_registry(build_registry(policy=policy), policy)

    resolved = effects.resolve_effect(
        "local_api",
        {"operation": "call", "endpoint": "fixture", "action": "inspect"},
    )
    assert resolved.effect is RepositoryEffect.UNKNOWN
    assert resolved.reason == "external_local_api_effect_unknown"
    assert any("local_api/fixture/inspect" in reason for reason in effects.firewall_readiness.reasons)


def test_explicit_read_only_local_api_action_does_not_require_firewall_coverage() -> None:
    policy = _local_api_policy("read_only")
    effects = build_effect_registry(build_registry(policy=policy), policy)

    resolved = effects.resolve_effect(
        "local_api",
        {"operation": "call", "endpoint": "fixture", "action": "inspect"},
    )
    assert resolved.effect is RepositoryEffect.READ_ONLY
    assert resolved.coverage is FirewallCoverage.NOT_REQUIRED
    assert not any("local_api/fixture/inspect" in reason for reason in effects.firewall_readiness.reasons)


def test_external_mutation_declaration_cannot_self_assert_coverage() -> None:
    policy = _local_api_policy("structured_mutation")
    effects = build_effect_registry(build_registry(policy=policy), policy)

    resolved = effects.resolve_effect(
        "local_api",
        {"operation": "call", "endpoint": "fixture", "action": "inspect"},
    )
    assert resolved.effect is RepositoryEffect.STRUCTURED_MUTATION
    assert resolved.coverage is FirewallCoverage.UNPROVEN
    assert any("local_api/fixture/inspect" in reason for reason in effects.firewall_readiness.reasons)


def test_builtin_without_provider_owned_effect_metadata_is_unknown() -> None:
    class Provider:
        def available_actions(self):
            return ("execute_scoped",)

    policy = _policy()
    effects = build_effect_registry(
        {"local_api": _noop},
        policy,
        builtin_local_api_providers={"devforge_runtime": Provider()},
    )

    resolved = effects.resolve_effect(
        "local_api",
        {
            "operation": "call",
            "endpoint": "devforge_runtime",
            "action": "execute_scoped",
        },
    )
    assert resolved.effect is RepositoryEffect.UNKNOWN
    assert resolved.reason == "builtin_effect_metadata_unavailable"
    assert any(
        "local_api/devforge_runtime/execute_scoped" in reason
        for reason in effects.firewall_readiness.reasons
    )
