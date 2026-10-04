from __future__ import annotations

import dataclasses

from sentinelx_core.operation_registry import (
    FirewallCoverage,
    OperationEffectResolution,
    RepositoryEffect,
    build_effect_registry,
)
from sentinelx_core.handlers import build_registry
from sentinelx_core.policy import MutationExecutionPolicy, Policy


async def _noop(_payload):
    return {"ok": True}


def _scoped_policy(*, operator_unrestricted: bool = False) -> Policy:
    mutation = MutationExecutionPolicy(
        configured=True,
        scoped_mutation_enabled=True,
        operator_unrestricted_enabled=operator_unrestricted,
    )
    return dataclasses.replace(
        Policy.empty(),
        mutation_execution=mutation,
        disabled_ops=frozenset({"exec"}),
    )


def test_legacy_process_surfaces_cannot_coexist_with_readiness_true() -> None:
    policy = dataclasses.replace(Policy.empty(), disabled_ops=frozenset({"exec"}))
    effects = build_effect_registry(build_registry(policy=policy), policy)

    legacy = effects.resolve_effect("script_run", {})
    assert legacy.effect is RepositoryEffect.PROCESS_MUTATION
    assert legacy.coverage is FirewallCoverage.UNPROVEN
    assert legacy.reason == "legacy_unprofiled_process_uncontained"
    assert effects.firewall_readiness.ready is False
    assert any("script_run/legacy_unprofiled" in reason for reason in effects.firewall_readiness.reasons)


def test_scoped_only_script_run_is_proven_process_coverage() -> None:
    policy = _scoped_policy()
    effects = build_effect_registry(build_registry(policy=policy), policy)

    scoped = effects.resolve_effect(
        "script_run", {"execution_profile": "scoped_mutation"}
    )
    assert scoped.effect is RepositoryEffect.PROCESS_MUTATION
    assert scoped.coverage is FirewallCoverage.PROVEN
    assert effects.firewall_readiness.ready is True

    missing = effects.resolve_effect("script_run", {})
    assert missing.effect is RepositoryEffect.UNKNOWN
    assert missing.reason == "execution_profile_required"


def test_operator_unrestricted_opt_in_keeps_process_readiness_false() -> None:
    policy = _scoped_policy(operator_unrestricted=True)
    effects = build_effect_registry(build_registry(policy=policy), policy)

    unrestricted = effects.resolve_effect(
        "script_run", {"execution_profile": "operator_unrestricted"}
    )
    assert unrestricted.effect is RepositoryEffect.PROCESS_MUTATION
    assert unrestricted.coverage is FirewallCoverage.UNPROVEN
    assert unrestricted.reason == "operator_unrestricted_process_uncontained"
    assert effects.firewall_readiness.ready is False
    assert any("script_run/operator_unrestricted" in reason for reason in effects.firewall_readiness.reasons)


def test_disabled_operator_unrestricted_profile_cannot_claim_safe_effect() -> None:
    policy = _scoped_policy()
    effects = build_effect_registry(build_registry(policy=policy), policy)

    resolved = effects.resolve_effect(
        "script_run", {"execution_profile": "operator_unrestricted"}
    )
    assert resolved.effect is RepositoryEffect.UNKNOWN
    assert resolved.reason == "operator_unrestricted_disabled"


def test_provider_owned_builtin_effect_metadata_composes_scoped_coverage() -> None:
    class Provider:
        def available_actions(self):
            return ("inspect_scope", "execute_scoped")

        def repository_effect(self, action: str):
            if action == "inspect_scope":
                return OperationEffectResolution(
                    RepositoryEffect.READ_ONLY,
                    selector=action,
                )
            if action == "execute_scoped":
                return OperationEffectResolution(
                    RepositoryEffect.PROCESS_MUTATION,
                    FirewallCoverage.PROVEN,
                    selector=action,
                )
            raise KeyError(action)

    policy = Policy.empty()
    effects = build_effect_registry(
        {"local_api": _noop},
        policy,
        builtin_local_api_providers={"devforge_runtime": Provider()},
    )

    scoped = effects.resolve_effect(
        "local_api",
        {
            "operation": "call",
            "endpoint": "devforge_runtime",
            "action": "execute_scoped",
        },
    )
    assert scoped.effect is RepositoryEffect.PROCESS_MUTATION
    assert scoped.coverage is FirewallCoverage.PROVEN
    assert effects.firewall_readiness.ready is True


def test_generic_exec_remains_unproven_even_when_scoped_script_is_ready() -> None:
    mutation = MutationExecutionPolicy(configured=True, scoped_mutation_enabled=True)
    policy = dataclasses.replace(Policy.empty(), mutation_execution=mutation)
    effects = build_effect_registry(build_registry(policy=policy), policy)

    direct = effects.resolve_effect("exec", {"command": "git status"})
    assert direct.effect is RepositoryEffect.PROCESS_MUTATION
    assert direct.coverage is FirewallCoverage.UNPROVEN
    assert effects.firewall_readiness.ready is False
    assert any(reason.startswith("exec:") for reason in effects.firewall_readiness.reasons)
