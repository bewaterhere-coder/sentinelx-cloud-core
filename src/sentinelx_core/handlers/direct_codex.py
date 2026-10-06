"""Bounded Agent-owned ``devforge_direct_codex`` local_api provider.

PR-015/S01 owns the provider contract, Host policy admission, closed action
schema and the repository-effect/readiness projection only. Workspace
bootstrap, Codex package discovery and the bounded process execution path are
S02; the live direct-Codex recovery proof is S03. Until that containment is
proven, ``execute_task`` is deliberately advertised as an unproven process
mutation and every invocation fails closed.

Nothing here widens generic ``exec`` or ``script_run``: the action schema is
closed and provider-owned values (executable, sandbox settings, workspace
placement, timeout and result limits) are never caller data.
"""
from __future__ import annotations

import platform
from typing import Any

from sentinelx_core.executor import HandlerError
from sentinelx_core.operation_registry import (
    FirewallCoverage,
    OperationEffectResolution,
    RepositoryEffect,
)
from sentinelx_core.policy import Policy
from sentinelx_core.request_context import RequestContext

ENDPOINT_NAME = "devforge_direct_codex"
CONTRACT_ID = "devforge_direct_codex"
CONTRACT_REVISION = 1
FEATURE_ID = "development_host.direct_codex_v1"

EXECUTE_TASK_ACTION = "execute_task"

# Fields that would transfer execution authority from the provider to the
# caller. The JSON schemas below are already closed; this list is defence in
# depth so a future schema edit cannot silently reintroduce a caller-owned
# executable, prompt, working directory or credential.
_FORBIDDEN_FIELDS = frozenset(
    {
        "executable",
        "executable_path",
        "argv",
        "args",
        "command",
        "command_line",
        "shell",
        "cwd",
        "workspace",
        "workspace_path",
        "workspace_root",
        "env",
        "environment",
        "prompt",
        "system_prompt",
        "instructions",
        "model",
        "reasoning_effort",
        "sandbox",
        "sandbox_mode",
        "approval",
        "approval_policy",
        "dangerously_bypass",
        "yolo",
        "credential",
        "credentials",
        "token",
        "secret",
        "replacement_transport",
        "remote_url",
    }
)

_STRING = {"type": "string", "minLength": 1}

_REPOSITORY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["vcs", "authority", "path"],
    "additionalProperties": False,
    "properties": {
        "vcs": _STRING,
        "authority": _STRING,
        "path": _STRING,
    },
}
_LINEAGE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["project_id", "task_id", "run_id", "attempt_id"],
    "additionalProperties": False,
    "properties": {
        "project_id": _STRING,
        "task_id": _STRING,
        "run_id": _STRING,
        "attempt_id": _STRING,
        "slice_id": _STRING,
    },
}
_DEVELOPMENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["action", "requirement_ref", "plan_ref"],
    "additionalProperties": False,
    "properties": {
        "action": {"enum": ["implementation", "fixing"]},
        "requirement_ref": _STRING,
        "plan_ref": _STRING,
        "findings_ref": _STRING,
    },
}
_TRANSPORT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["type", "pr_number", "branch", "expected_remote_sha"],
    "additionalProperties": False,
    "properties": {
        "type": {"const": "github-pr"},
        "pr_number": {"type": "integer", "minimum": 1},
        "branch": _STRING,
        "expected_remote_sha": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
    },
}
_EXECUTE_TASK_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["repository", "lineage", "development", "transport"],
    "additionalProperties": False,
    "properties": {
        "repository": _REPOSITORY_SCHEMA,
        "lineage": _LINEAGE_SCHEMA,
        "development": _DEVELOPMENT_SCHEMA,
        "transport": _TRANSPORT_SCHEMA,
    },
}

_ACTION_SCHEMAS = {EXECUTE_TASK_ACTION: _EXECUTE_TASK_SCHEMA}

_NESTED_SPECS = (
    ("repository", _REPOSITORY_SCHEMA),
    ("lineage", _LINEAGE_SCHEMA),
    ("development", _DEVELOPMENT_SCHEMA),
    ("transport", _TRANSPORT_SCHEMA),
)


def _reject_forbidden_fields(node: Any, prefix: str = "") -> None:
    """Fail closed on any caller-owned execution-authority field."""
    if isinstance(node, dict):
        for key, value in node.items():
            name = str(key)
            if name in _FORBIDDEN_FIELDS:
                raise HandlerError("invalid_payload", f"unsupported field: {prefix}{name}")
            _reject_forbidden_fields(value, f"{prefix}{name}.")
    elif isinstance(node, (list, tuple)):
        for index, value in enumerate(node):
            _reject_forbidden_fields(value, f"{prefix}[{index}].")


def _require_object(params: dict[str, Any], name: str) -> dict[str, Any]:
    value = params.get(name)
    if not isinstance(value, dict):
        raise HandlerError("invalid_payload", f"{name} must be an object")
    return value


def validate_execute_task_params(params: Any) -> dict[str, Any]:
    """Validate the closed ``execute_task`` payload without executing anything."""
    if not isinstance(params, dict):
        raise HandlerError("invalid_payload", "execute_task params must be an object")

    extras = sorted(set(params) - set(_EXECUTE_TASK_SCHEMA["properties"]))
    if extras:
        raise HandlerError("invalid_payload", f"unsupported execute_task fields: {extras}")
    missing = sorted(set(_EXECUTE_TASK_SCHEMA["required"]) - set(params))
    if missing:
        raise HandlerError("invalid_payload", f"missing execute_task fields: {missing}")

    _reject_forbidden_fields(params)

    for name, schema in _NESTED_SPECS:
        block = _require_object(params, name)
        extras = sorted(set(block) - set(schema["properties"]))
        if extras:
            raise HandlerError("invalid_payload", f"unsupported {name} fields: {extras}")
        missing = sorted(set(schema["required"]) - set(block))
        if missing:
            raise HandlerError("invalid_payload", f"missing {name} fields: {missing}")

    lineage = params["lineage"]
    for name in ("project_id", "task_id", "run_id", "attempt_id"):
        if not str(lineage.get(name) or "").strip():
            raise HandlerError("invalid_payload", f"lineage.{name} must be a non-empty string")

    development = params["development"]
    if development["action"] not in ("implementation", "fixing"):
        raise HandlerError(
            "invalid_payload", f"unsupported development.action: {development['action']}"
        )

    transport = params["transport"]
    if transport["type"] != "github-pr":
        raise HandlerError("invalid_payload", "transport.type must be github-pr")
    if not isinstance(transport["pr_number"], int) or isinstance(transport["pr_number"], bool):
        raise HandlerError("invalid_payload", "transport.pr_number must be an integer")

    return dict(params)


class DevforgeDirectCodexProvider:
    """Policy-admitted builtin direct-Codex contract with no execution path."""

    name = ENDPOINT_NAME

    def __init__(
        self,
        policy: Policy,
        *,
        platform_name: str | None = None,
    ) -> None:
        self._policy = policy
        self._platform_name = platform_name or platform.system()

    # -- admission ---------------------------------------------------------
    @property
    def admission_reasons(self) -> tuple[str, ...]:
        """Policy/platform prerequisites owned by the Host, never by a caller."""
        return self._policy.direct_codex.missing_prerequisites(
            platform_name=self._platform_name
        )

    def available_actions(self) -> tuple[str, ...]:
        if self.admission_reasons:
            return ()
        if "local_api" in self._policy.disabled_ops:
            return ()
        return (EXECUTE_TASK_ACTION,)

    # -- effect / readiness projection ------------------------------------
    def repository_effect(self, action: str) -> OperationEffectResolution:
        if action == EXECUTE_TASK_ACTION:
            # A direct development host is an external process. It is a
            # process mutation and stays UNPROVEN until S02 proves the exact
            # workspace/canonical-checkout containment, so provider-wide
            # effective-surface readiness cannot become true through it.
            return OperationEffectResolution(
                RepositoryEffect.PROCESS_MUTATION,
                FirewallCoverage.UNPROVEN,
                reason="direct_codex_containment_unproven",
            )
        return OperationEffectResolution(
            RepositoryEffect.UNKNOWN,
            FirewallCoverage.UNPROVEN,
            reason="unknown_direct_codex_action",
        )

    def readiness(self) -> dict[str, Any]:
        """Provider-owned readiness projection for ``FEATURE_ID``."""
        reasons = list(self.admission_reasons)
        if not reasons and not self.available_actions():
            reasons.append("local_api_disabled")
        if not reasons:
            # Contract is admitted, but the physical containment proof is S02.
            reasons.append("direct_codex_containment_unproven")
        return {
            "available": False,
            "verified": False,
            "contract_id": CONTRACT_ID,
            "contract_revision": CONTRACT_REVISION,
            "reason": reasons[0] if reasons else None,
            "uncovered_classes": list(dict.fromkeys(reasons)),
        }

    # -- local_api surface -------------------------------------------------
    def list_entry(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "protocol": "builtin",
            "transport": "agent",
            "action_count": len(self.available_actions()),
            "provider_kind": "builtin",
            "contract_id": CONTRACT_ID,
            "contract_revision": CONTRACT_REVISION,
            "feature_id": FEATURE_ID,
        }

    def describe(self) -> dict[str, Any]:
        actions = self.available_actions()
        if not actions:
            raise HandlerError(
                "endpoint_not_available",
                "devforge_direct_codex requires explicit direct-codex Host policy opt-in",
            )
        return {
            "ok": True,
            "operation": "describe",
            "endpoint": self.name,
            "provider_kind": "builtin",
            "contract_id": CONTRACT_ID,
            "contract_revision": CONTRACT_REVISION,
            "feature_id": FEATURE_ID,
            "readiness": self.readiness(),
            "actions": {
                action: {
                    "description": f"Bounded {action} action",
                    "params": list(_ACTION_SCHEMAS[action]["required"]),
                    "params_schema": _ACTION_SCHEMAS[action],
                }
                for action in actions
            },
        }

    async def call(
        self,
        context: RequestContext,
        action: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(context, RequestContext):
            raise HandlerError(
                "invalid_payload",
                "devforge_direct_codex requires transport RequestContext",
            )
        if self.admission_reasons:
            raise HandlerError(
                "endpoint_not_available",
                "devforge_direct_codex requires explicit direct-codex Host policy opt-in",
            )
        if "local_api" in self._policy.disabled_ops:
            raise HandlerError("operation_disabled", "local_api is disabled by Host policy")
        if action != EXECUTE_TASK_ACTION:
            raise HandlerError("unknown_action", f"unknown devforge_direct_codex action: {action}")
        if "action" in params:
            raise HandlerError("invalid_payload", "params.action is transport-owned")

        validate_execute_task_params(params)

        # S01 delivers the contract only. Execution requires the S02 workspace
        # bootstrap, verified Codex chain and proven process containment; until
        # then every invocation fails closed rather than falling back to a
        # generic shell or unrestricted path.
        raise HandlerError(
            "direct_codex_execution_unavailable",
            "devforge_direct_codex.execute_task is contract-only in this build: "
            "direct-Codex workspace bootstrap and containment proof are not delivered",
        )


def make_devforge_direct_codex_provider(
    policy: Policy,
    *,
    platform_name: str | None = None,
) -> DevforgeDirectCodexProvider:
    return DevforgeDirectCodexProvider(policy, platform_name=platform_name)
