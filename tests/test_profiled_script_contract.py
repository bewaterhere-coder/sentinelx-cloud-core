from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import pytest

from sentinelx_core.executor import HandlerError
from sentinelx_core.handlers.scoped_script import make_profiled_script_run_handler
from sentinelx_core.policy import MutationExecutionPolicy, Policy
from sentinelx_core.request_context import RequestContext


def _run(handler, context, payload):
    return asyncio.run(handler(context, payload))


def test_configured_mutation_requires_profile_with_bounded_contract_details(tmp_path: Path) -> None:
    mutation_policy = MutationExecutionPolicy(configured=True, operator_unrestricted_enabled=False)
    policy = Policy(mutation_execution=mutation_policy, upload_base=tmp_path / "uploads")
    handler = make_profiled_script_run_handler(
        policy,
        policy.upload_base,
        mutation_state_root=tmp_path / "state",
    )
    context = RequestContext("req-missing-profile", "script_run", None, datetime.now(UTC))

    with pytest.raises(HandlerError) as captured:
        _run(
            handler,
            context,
            {"interpreter": "python3", "content": "print('must not run')"},
        )

    assert captured.value.code == "execution_profile_required"
    assert captured.value.details == {
        "required_argument": "execution_profile",
        "feature": "script_run_execution_profile_v1",
        "supported_profiles": ["scoped_mutation"],
    }


def test_unknown_profile_remains_rejected(tmp_path: Path) -> None:
    mutation_policy = MutationExecutionPolicy(configured=True)
    policy = Policy(mutation_execution=mutation_policy, upload_base=tmp_path / "uploads")
    handler = make_profiled_script_run_handler(
        policy,
        policy.upload_base,
        mutation_state_root=tmp_path / "state",
    )
    context = RequestContext("req-unknown-profile", "script_run", None, datetime.now(UTC))

    with pytest.raises(HandlerError) as captured:
        _run(
            handler,
            context,
            {
                "execution_profile": "safe-ish",
                "interpreter": "python3",
                "content": "print('must not run')",
            },
        )

    assert captured.value.code == "invalid_payload"
    assert "unsupported execution_profile" in str(captured.value)
