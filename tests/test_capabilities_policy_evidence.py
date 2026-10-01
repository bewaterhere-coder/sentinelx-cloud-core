"""capabilities must evidence the operator's decisions, not only their effect.

ops_supported is the permitted set: a disabled op is simply not in it. But that
alone cannot tell an auditor WHY something is absent -- an old agent that never
had the op and a current one where it was deliberately turned off look
identical from outside. Requested by an operator running a governance audit who
needed to evidence the difference rather than infer it.
"""

from __future__ import annotations

import dataclasses

import pytest

from sentinelx_core.handlers import build_registry
from sentinelx_core.policy import MutationExecutionPolicy, Policy


def _policy(**kw) -> Policy:
    return dataclasses.replace(Policy.empty(), **kw)


async def _caps(policy: Policy) -> dict:
    return await build_registry(policy=policy)["capabilities"]({})


async def test_a_default_host_reports_nothing_disabled():
    caps = await _caps(_policy())
    assert caps["disabled_ops"] == []
    assert caps["exec_strict"] is False


async def test_a_disabled_op_is_named_in_capabilities():
    caps = await _caps(_policy(disabled_ops=frozenset({"script_run"})))
    assert caps["disabled_ops"] == ["script_run"]


async def test_and_is_absent_from_the_permitted_set():
    """Both halves: named as disabled, and genuinely not offered."""
    caps = await _caps(_policy(disabled_ops=frozenset({"script_run"})))
    assert "script_run" not in caps["ops_supported"]


async def test_the_two_fields_disagree_for_a_reason():
    """An auditor can tell a deliberate removal from an agent that never had it."""
    off = await _caps(_policy(disabled_ops=frozenset({"script_run"})))
    on = await _caps(_policy())
    assert "script_run" in on["ops_supported"]
    assert "script_run" not in off["ops_supported"]
    assert off["disabled_ops"] and not on["disabled_ops"]


async def test_a_name_that_matches_nothing_is_still_reported():
    """A typo in a deny list otherwise reads as protection never applied."""
    caps = await _caps(_policy(disabled_ops=frozenset({"scriptrun"})))
    assert caps["disabled_ops"] == ["scriptrun"]


async def test_strict_mode_is_visible_without_reading_config_yaml():
    caps = await _caps(_policy(exec_strict=True))
    assert caps["exec_strict"] is True


async def test_the_list_is_sorted_for_a_stable_diff():
    caps = await _caps(_policy(disabled_ops=frozenset({"git", "exec", "edit"})))
    assert caps["disabled_ops"] == ["edit", "exec", "git"]


async def test_profiled_script_contract_is_machine_readable_without_claiming_readiness():
    caps = await _caps(_policy())
    feature = caps["execution_features"]["host_runtime.script_run_execution_profile_v1"]

    assert feature["available"] is True
    assert feature["operation"] == "script_run"
    assert feature["profile_argument"] == "execution_profile"
    assert feature["supported_profiles"] == ["scoped_mutation"]
    assert feature["scoped_mutation_required_input"] == [
        "mutation.scope_ref.scope_id",
        "mutation.scope_ref.generation",
        "lineage.project_id",
        "lineage.task_id",
        "lineage.run_id",
        "lineage.attempt_id",
        "lineage.slice_id?",
        "repository.vcs",
        "repository.authority",
        "repository.path",
    ]
    assert "available" in feature["profile_readiness"]["scoped_mutation"]
    assert feature["hub_projection"]["external"] is True


async def test_operator_unrestricted_is_advertised_only_after_explicit_policy_opt_in():
    off = await _caps(_policy(mutation_execution=MutationExecutionPolicy(configured=True)))
    on = await _caps(
        _policy(
            mutation_execution=MutationExecutionPolicy(
                configured=True,
                operator_unrestricted_enabled=True,
            )
        )
    )

    off_feature = off["execution_features"]["host_runtime.script_run_execution_profile_v1"]
    on_feature = on["execution_features"]["host_runtime.script_run_execution_profile_v1"]
    assert "operator_unrestricted" not in off_feature["supported_profiles"]
    assert "operator_unrestricted" in on_feature["supported_profiles"]
    assert off_feature["profile_readiness"]["operator_unrestricted"]["available"] is False
    assert on_feature["profile_readiness"]["operator_unrestricted"]["available"] is True
    assert on_feature["profile_readiness"]["operator_unrestricted"]["safe_fallback"] is False
