"""Bounded Agent-owned ``devforge_runtime`` local_api provider.

S06 owns endpoint identity, lifecycle composition, and policy admission only.
The scoped execution adapter is an optional seam that S07 wires to the
existing profiled script handler; S06 never introduces a second executor.
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from sentinelx_core.executor import HandlerError
from sentinelx_core.policy import Policy
from sentinelx_core.request_context import RequestContext

ENDPOINT_NAME = "devforge_runtime"
CONTRACT_ID = "devforge_runtime"
CONTRACT_REVISION = 1

LifecycleService = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]
ProfiledScriptHandler = Callable[[RequestContext, dict[str, Any]], Awaitable[dict[str, Any]]]
ScopedExecuteAdapter = Callable[[RequestContext, dict[str, Any]], Awaitable[dict[str, Any]]]

_EXECUTE_SCOPED_ALLOWED = frozenset(
    {
        "scope_ref",
        "repository",
        "lineage",
        "execution_profile",
        "interpreter",
        "content",
        "args",
        "cwd",
        "env",
        "timeout",
        "verification",
    }
)
_EXECUTE_SCOPED_REQUIRED = frozenset(
    {"scope_ref", "repository", "lineage", "execution_profile", "interpreter", "content"}
)
_EXECUTE_SCOPED_RESULT_FIELDS = (
    "ok",
    "interpreter",
    "returncode",
    "timed_out",
    "output",
    "execution_profile",
    "audit_operation_id",
    "mutation_scope_ref",
    "terminal_state",
)
_VERIFICATION_FIELDS = frozenset(
    {
        "profile",
        "source_id",
        "source_manifest_sha256",
        "source_revision",
        "capsule_id",
        "package_lock_sha256",
    }
)
_VERIFICATION_RESULT_FIELDS = (
    "profile_id",
    "profile_revision",
    "source_repository_digest",
    "source_revision",
    "source_manifest_digest",
    "toolchain_kind",
    "toolchain_digest",
    "launcher_digest",
    "capsule_id",
    "capsule_revision",
    "capsule_payload_digest",
    "expected_package_lock_sha256",
    "network_mode",
    "resource_limits_digest",
    "source_id",
    "verified_package_lock_sha256",
    "offline",
)

_LIFECYCLE_ACTIONS = {
    "provision_scope": "provision",
    "revalidate_scope": "revalidate",
    "inspect_scope": "inspect",
    "terminalize_scope": "terminalize",
}

_REPOSITORY_SCHEMA = {
    "type": "object",
    "required": ["vcs", "authority", "path"],
    "additionalProperties": False,
    "properties": {
        "vcs": {"type": "string"},
        "authority": {"type": "string"},
        "path": {"type": "string"},
    },
}
_LINEAGE_SCHEMA = {
    "type": "object",
    "required": ["project_id", "task_id", "run_id", "attempt_id"],
    "additionalProperties": False,
    "properties": {
        "project_id": {"type": "string"},
        "task_id": {"type": "string"},
        "run_id": {"type": "string"},
        "attempt_id": {"type": "string"},
        "slice_id": {"type": "string"},
    },
}
_SCOPE_REF_SCHEMA = {
    "type": "object",
    "required": ["scope_id", "generation"],
    "additionalProperties": False,
    "properties": {
        "scope_id": {"type": "string"},
        "generation": {"type": "integer", "minimum": 1},
    },
}
_VERIFICATION_SCHEMA = {
    "type": "object",
    "required": [
        "profile",
        "source_id",
        "source_manifest_sha256",
        "source_revision",
        "capsule_id",
        "package_lock_sha256",
    ],
    "additionalProperties": False,
    "properties": {
        "profile": {"type": "string"},
        "source_id": {"type": "string"},
        "source_manifest_sha256": {
            "type": "string",
            "pattern": "^[0-9a-f]{64}$",
        },
        "source_revision": {"type": "string", "minLength": 1},
        "capsule_id": {"type": "string"},
        "package_lock_sha256": {
            "type": "string",
            "pattern": "^[0-9a-f]{64}$",
        },
    },
}


def _schema(required: list[str], properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "required": required,
        "additionalProperties": False,
        "properties": properties,
    }


_ACTION_SCHEMAS = {
    "provision_scope": _schema(
        ["purpose", "repository", "lineage"],
        {
            "purpose": {"const": "scoped_script"},
            "repository": _REPOSITORY_SCHEMA,
            "lineage": _LINEAGE_SCHEMA,
        },
    ),
    "revalidate_scope": _schema(
        ["scope_ref", "repository", "lineage"],
        {
            "scope_ref": _SCOPE_REF_SCHEMA,
            "repository": _REPOSITORY_SCHEMA,
            "lineage": _LINEAGE_SCHEMA,
        },
    ),
    "inspect_scope": _schema(
        ["scope_ref", "repository", "lineage"],
        {
            "scope_ref": _SCOPE_REF_SCHEMA,
            "repository": _REPOSITORY_SCHEMA,
            "lineage": _LINEAGE_SCHEMA,
        },
    ),
    "terminalize_scope": _schema(
        ["scope_ref", "repository", "lineage"],
        {
            "scope_ref": _SCOPE_REF_SCHEMA,
            "repository": _REPOSITORY_SCHEMA,
            "lineage": _LINEAGE_SCHEMA,
        },
    ),
    # S07 provides the real adapter; S06 only freezes admission/schema semantics.
    "execute_scoped": _schema(
        ["scope_ref", "repository", "lineage", "execution_profile", "interpreter", "content"],
        {
            "scope_ref": _SCOPE_REF_SCHEMA,
            "repository": _REPOSITORY_SCHEMA,
            "lineage": _LINEAGE_SCHEMA,
            "execution_profile": {"type": "string", "const": "scoped_mutation"},
            "interpreter": {"enum": ["python3", "powershell", "pwsh"]},
            "content": {"type": "string"},
            "args": {"type": "array", "items": {"type": "string"}},
            "cwd": {"type": "string"},
            "env": {"type": "object", "additionalProperties": {"type": "string"}},
            "timeout": {"type": "integer"},
            "verification": _VERIFICATION_SCHEMA,
        },
    ),
}


def _strict_mapping(
    params: dict[str, Any],
    name: str,
    *,
    allowed: frozenset[str],
    required: frozenset[str],
) -> dict[str, Any]:
    value = params.get(name)
    if not isinstance(value, dict):
        raise HandlerError("invalid_payload", f"{name} must be an object")
    extras = sorted(set(value) - allowed)
    if extras:
        raise HandlerError("invalid_payload", f"unsupported {name} fields: {extras}")
    missing = sorted(required - set(value))
    if missing:
        raise HandlerError("invalid_payload", f"missing {name} fields: {missing}")
    return dict(value)


def make_devforge_execute_scoped_adapter(
    profiled_script_handler: ProfiledScriptHandler,
) -> ScopedExecuteAdapter:
    """Adapt bounded local_api params onto the one canonical scoped executor."""

    async def execute_scoped(
        context: RequestContext,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(context, RequestContext):
            raise HandlerError(
                "HostMutationAuditLineageInvalid",
                "execute_scoped requires transport RequestContext",
            )
        if not isinstance(params, dict):
            raise HandlerError("invalid_payload", "execute_scoped params must be an object")

        extras = sorted(set(params) - _EXECUTE_SCOPED_ALLOWED)
        if extras:
            raise HandlerError("invalid_payload", f"unsupported execute_scoped fields: {extras}")
        missing = sorted(_EXECUTE_SCOPED_REQUIRED - set(params))
        if missing:
            raise HandlerError("invalid_payload", f"missing execute_scoped fields: {missing}")

        execution_profile = params["execution_profile"]
        if not isinstance(execution_profile, str):
            raise HandlerError("invalid_payload", "execution_profile must be a string")
        if execution_profile != "scoped_mutation":
            raise HandlerError(
                "invalid_payload",
                f"unsupported execution_profile: {execution_profile}",
            )

        scope_ref = _strict_mapping(
            params,
            "scope_ref",
            allowed=frozenset({"scope_id", "generation"}),
            required=frozenset({"scope_id", "generation"}),
        )
        repository = _strict_mapping(
            params,
            "repository",
            allowed=frozenset({"vcs", "authority", "path"}),
            required=frozenset({"vcs", "authority", "path"}),
        )
        lineage = _strict_mapping(
            params,
            "lineage",
            allowed=frozenset({"project_id", "task_id", "run_id", "attempt_id", "slice_id"}),
            required=frozenset({"project_id", "task_id", "run_id", "attempt_id"}),
        )
        verification: dict[str, Any] | None = None
        if "verification" in params:
            verification = _strict_mapping(
                params,
                "verification",
                allowed=_VERIFICATION_FIELDS,
                required=_VERIFICATION_FIELDS,
            )
            for name, value in verification.items():
                if not isinstance(value, str) or not value.strip():
                    raise HandlerError(
                        "invalid_payload",
                        f"verification.{name} must be a non-empty string",
                    )

        payload: dict[str, Any] = {
            "execution_profile": execution_profile,
            "cleanup": True,
            "mutation": {"scope_ref": scope_ref},
            "repository": repository,
            "lineage": lineage,
            "interpreter": params["interpreter"],
            "content": params["content"],
        }
        for name in ("args", "cwd", "env", "timeout"):
            if name in params:
                payload[name] = params[name]
        if verification is not None:
            payload["verification"] = verification

        result = await profiled_script_handler(context, payload)
        if not isinstance(result, dict):
            raise HandlerError(
                "scoped_mutation_failed",
                "scoped executor returned an invalid result",
            )
        if result.get("execution_profile") != execution_profile:
            raise HandlerError(
                "scoped_mutation_failed",
                "scoped executor returned an unexpected execution profile",
            )

        projected = {
            key: result[key]
            for key in _EXECUTE_SCOPED_RESULT_FIELDS
            if key in result
        }
        if "verification" in result:
            evidence = result["verification"]
            if not isinstance(evidence, dict):
                raise HandlerError(
                    "scoped_mutation_failed",
                    "scoped executor returned invalid verification evidence",
                )
            projected["verification"] = {
                key: evidence[key]
                for key in _VERIFICATION_RESULT_FIELDS
                if key in evidence
            }
        return projected

    return execute_scoped


class DevforgeRuntimeProvider:
    """Policy-filtered builtin endpoint provider with no independent authority."""

    name = ENDPOINT_NAME

    def __init__(
        self,
        policy: Policy,
        lifecycle_service: LifecycleService,
        *,
        execute_scoped_adapter: ScopedExecuteAdapter | None = None,
    ) -> None:
        self._policy = policy
        self._lifecycle = lifecycle_service
        self._execute_scoped = execute_scoped_adapter

    @property
    def host_opted_in(self) -> bool:
        mutation = self._policy.mutation_execution
        return mutation.configured and mutation.scoped_mutation_enabled

    def available_actions(self) -> tuple[str, ...]:
        if not self.host_opted_in:
            return ()
        actions: list[str] = []
        if "mutation_scope" not in self._policy.disabled_ops:
            actions.extend(_LIFECYCLE_ACTIONS)
        if self._execute_scoped is not None and "script_run" not in self._policy.disabled_ops:
            actions.append("execute_scoped")
        return tuple(actions)

    def list_entry(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "protocol": "builtin",
            "transport": "agent",
            "action_count": len(self.available_actions()),
            "provider_kind": "builtin",
            "contract_id": CONTRACT_ID,
            "contract_revision": CONTRACT_REVISION,
        }

    def describe(self) -> dict[str, Any]:
        actions = self.available_actions()
        if not actions:
            raise HandlerError(
                "endpoint_not_available",
                "devforge_runtime has no policy-admitted actions on this host",
            )
        return {
            "ok": True,
            "operation": "describe",
            "endpoint": self.name,
            "provider_kind": "builtin",
            "contract_id": CONTRACT_ID,
            "contract_revision": CONTRACT_REVISION,
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
        if not self.host_opted_in:
            raise HandlerError(
                "endpoint_not_available",
                "devforge_runtime requires explicit scoped mutation Host policy opt-in",
            )
        if "action" in params:
            raise HandlerError("invalid_payload", "params.action is transport-owned")

        if action in _LIFECYCLE_ACTIONS:
            if "mutation_scope" in self._policy.disabled_ops:
                raise HandlerError(
                    "operation_disabled",
                    "mutation_scope is disabled by Host policy",
                )
            payload = dict(params)
            payload["action"] = _LIFECYCLE_ACTIONS[action]
            return await self._lifecycle(payload)

        if action == "execute_scoped":
            if "script_run" in self._policy.disabled_ops:
                raise HandlerError("operation_disabled", "script_run is disabled by Host policy")
            if self._execute_scoped is None:
                raise HandlerError(
                    "endpoint_not_available",
                    "execute_scoped adapter is not active on this Agent build",
                )
            return await self._execute_scoped(context, params)

        raise HandlerError("unknown_action", f"unknown devforge_runtime action: {action}")


def make_devforge_runtime_provider(
    policy: Policy,
    lifecycle_service: LifecycleService,
    *,
    execute_scoped_adapter: ScopedExecuteAdapter | None = None,
) -> DevforgeRuntimeProvider:
    return DevforgeRuntimeProvider(
        policy,
        lifecycle_service,
        execute_scoped_adapter=execute_scoped_adapter,
    )
