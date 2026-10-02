from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import pytest

from sentinelx_core.executor import HandlerError
from sentinelx_core.handlers.mutation_scope import make_mutation_scope_handler
from sentinelx_core.mutation_scope import MutationScopeStore
from sentinelx_core.policy import MutationExecutionPolicy, Policy
from sentinelx_core.request_context import RequestContext


def _fixture(tmp_path: Path):
    workspace_root = tmp_path / "workspaces"
    state_root = tmp_path / "provider-state"
    upload_base = tmp_path / "uploads"
    protected_root = tmp_path / "protected"
    for path in (workspace_root, state_root, upload_base, protected_root):
        path.mkdir(parents=True, exist_ok=True)

    mutation_policy = MutationExecutionPolicy(
        configured=True,
        scoped_mutation_enabled=True,
        workspace_root=workspace_root,
        protected_roots=(protected_root,),
        scope_ttl_seconds=600,
        evidence_retention_days=7,
        operator_unrestricted_enabled=False,
    )
    policy = Policy(mutation_execution=mutation_policy, upload_base=upload_base)
    handler = make_mutation_scope_handler(
        policy,
        upload_base,
        mutation_state_root=state_root,
    )
    context = RequestContext(
        request_id="req-s02",
        op="mutation_scope",
        opaque_ref="operator-correlation",
        received_at=datetime.now(UTC),
    )
    repository = {
        "vcs": "git",
        "authority": "github.com",
        "path": "bewaterhere-coder/sentinelx-cloud-core",
    }
    lineage = {
        "project_id": "sentinelx-cloud-core",
        "task_id": "PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1",
        "run_id": "s02",
        "attempt_id": "attempt-1",
        "slice_id": "S02",
    }
    return handler, context, repository, lineage, state_root


def _call(handler, context, payload):
    return asyncio.run(handler(context, payload))


def _provision(handler, context, repository, lineage):
    return _call(
        handler,
        context,
        {
            "action": "provision",
            "purpose": "scoped_script",
            "repository": repository,
            "lineage": lineage,
        },
    )


def _bound_payload(action, scope, repository, lineage):
    return {
        "action": action,
        "scope_ref": {
            "scope_id": scope["scope_id"],
            "generation": scope["generation"],
        },
        "repository": repository,
        "lineage": lineage,
    }


def test_lifecycle_provision_revalidate_inspect_terminalize_is_bounded(tmp_path: Path) -> None:
    handler, context, repository, lineage, _state_root = _fixture(tmp_path)
    provisioned = _provision(handler, context, repository, lineage)
    scope = provisioned["scope"]
    assert provisioned["action"] == "provision"
    assert scope["state"] == "provisioned"
    assert scope["purpose"] == "scoped_script"
    assert "allowed_operation_classes" not in scope
    assert "exact_workspace" not in scope
    assert "protected_roots" not in scope

    revalidated = _call(handler, context, _bound_payload("revalidate", scope, repository, lineage))
    assert revalidated["scope"]["scope_id"] == scope["scope_id"]
    assert revalidated["scope"]["state"] == "provisioned"

    inspected = _call(handler, context, _bound_payload("inspect", scope, repository, lineage))
    assert inspected["scope"] == revalidated["scope"]

    terminalized = _call(handler, context, _bound_payload("terminalize", scope, repository, lineage))
    assert terminalized["scope"]["state"] == "terminal"
    assert terminalized["scope"]["terminalized_at"]

    final_read = _call(handler, context, _bound_payload("inspect", scope, repository, lineage))
    assert final_read["scope"]["state"] == "terminal"
    assert final_read["scope"]["scope_digest"] == scope["scope_digest"]


def test_duplicate_provision_is_idempotent_and_cannot_broaden_authority(tmp_path: Path) -> None:
    handler, context, repository, lineage, _state_root = _fixture(tmp_path)
    first = _provision(handler, context, repository, lineage)
    second = _provision(handler, context, repository, lineage)
    assert second["scope"] == first["scope"]

    broadened = {
        "action": "provision",
        "purpose": "scoped_script",
        "repository": repository,
        "lineage": lineage,
        "allowed_operation_classes": ["scoped_script", "anything"],
    }
    with pytest.raises(HandlerError) as exc_info:
        _call(handler, context, broadened)
    assert exc_info.value.code == "invalid_payload"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("workspace_id", "caller-workspace"),
        ("workspace_root", "D:/caller"),
        ("protected_roots", ["D:/"]),
        ("required_operation_class", "scoped_script"),
        ("placement_ref", "caller-placement"),
        ("sandbox_identity", "caller-sid"),
        ("scope_digest", "caller-digest"),
        ("request_id", "caller-request"),
        ("opaque_ref", "caller-opaque"),
    ],
)
def test_authority_shaped_or_transport_override_fields_fail_closed(
    tmp_path: Path, field: str, value: object
) -> None:
    handler, context, repository, lineage, _state_root = _fixture(tmp_path)
    payload = {
        "action": "provision",
        "purpose": "scoped_script",
        "repository": repository,
        "lineage": lineage,
        field: value,
    }
    with pytest.raises(HandlerError) as exc_info:
        _call(handler, context, payload)
    assert exc_info.value.code == "invalid_payload"


def test_unknown_purpose_and_nested_authority_fields_fail_closed(tmp_path: Path) -> None:
    handler, context, repository, lineage, _state_root = _fixture(tmp_path)
    with pytest.raises(HandlerError) as exc_info:
        _call(
            handler,
            context,
            {
                "action": "provision",
                "purpose": "generic_shell",
                "repository": repository,
                "lineage": lineage,
            },
        )
    assert exc_info.value.code == "invalid_payload"

    bad_repository = dict(repository)
    bad_repository["workspace_path"] = "D:/caller"
    with pytest.raises(HandlerError) as nested_exc:
        _call(
            handler,
            context,
            {
                "action": "provision",
                "purpose": "scoped_script",
                "repository": bad_repository,
                "lineage": lineage,
            },
        )
    assert nested_exc.value.code == "invalid_payload"


def test_bound_actions_require_exact_repository_and_full_lineage(tmp_path: Path) -> None:
    handler, context, repository, lineage, _state_root = _fixture(tmp_path)
    scope = _provision(handler, context, repository, lineage)["scope"]

    wrong_repository = dict(repository)
    wrong_repository["path"] = "bewaterhere-coder/other"
    with pytest.raises(HandlerError) as repo_exc:
        _call(handler, context, _bound_payload("inspect", scope, wrong_repository, lineage))
    assert repo_exc.value.code == "HostMutationScopeBindingMismatch"

    wrong_lineage = dict(lineage)
    wrong_lineage["attempt_id"] = "different-attempt"
    with pytest.raises(HandlerError) as lineage_exc:
        _call(handler, context, _bound_payload("inspect", scope, repository, wrong_lineage))
    assert lineage_exc.value.code == "HostMutationScopeBindingMismatch"

    wrong_generation = _bound_payload("inspect", scope, repository, lineage)
    wrong_generation["scope_ref"] = dict(wrong_generation["scope_ref"])
    wrong_generation["scope_ref"]["generation"] += 1
    with pytest.raises(HandlerError) as generation_exc:
        _call(handler, context, wrong_generation)
    assert generation_exc.value.code == "HostMutationScopeNotCurrent"


def test_external_terminalize_does_not_kill_or_fabricate_active_runtime_closure(tmp_path: Path) -> None:
    handler, context, repository, lineage, state_root = _fixture(tmp_path)
    scope = _provision(handler, context, repository, lineage)["scope"]
    store = MutationScopeStore(state_root)
    store.reserve_sandbox_identity(
        scope["scope_id"],
        scope["generation"],
        "S-1-15-2-test-s02",
    )

    with pytest.raises(HandlerError) as exc_info:
        _call(handler, context, _bound_payload("terminalize", scope, repository, lineage))
    assert exc_info.value.code == "HostMutationResidualAuthorityDetected"

    authoritative = store.read_scope(scope["scope_id"])
    assert authoritative.state == "active"
    assert authoritative.sandbox_write_authority_present is True


def test_transport_context_cannot_be_replaced_by_payload(tmp_path: Path) -> None:
    handler, context, repository, lineage, _state_root = _fixture(tmp_path)
    wrong_context = RequestContext(
        request_id=context.request_id,
        op="script_run",
        opaque_ref=context.opaque_ref,
        received_at=context.received_at,
    )
    with pytest.raises(HandlerError) as exc_info:
        _provision(handler, wrong_context, repository, lineage)
    assert exc_info.value.code == "invalid_payload"
