"""Bounded Agent-owned ``devforge_runtime`` local_api provider.

S06 owns endpoint identity, lifecycle composition, and policy admission only.
The scoped execution adapter is an optional seam that S07 wires to the
existing profiled script handler; S06 never introduces a second executor.
PR-014 S02 adds the closed, path-free ``materialize_workspace`` action whose
authority semantics live entirely inside
``devforge_workspace_materialization``.
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from sentinelx_core.executor import HandlerError
from sentinelx_core.operation_registry import (
    FirewallCoverage,
    OperationEffectResolution,
    RepositoryEffect,
)
from sentinelx_core.policy import Policy
from sentinelx_core.request_context import RequestContext

ENDPOINT_NAME = "devforge_runtime"
CONTRACT_ID = "devforge_runtime"
CONTRACT_REVISION = 2

LifecycleService = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]
ProfiledScriptHandler = Callable[[RequestContext, dict[str, Any]], Awaitable[dict[str, Any]]]
ScopedExecuteAdapter = Callable[[RequestContext, dict[str, Any]], Awaitable[dict[str, Any]]]
MaterializeAdapter = Callable[[RequestContext, dict[str, Any]], Awaitable[dict[str, Any]]]

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
_SOURCE_BINDING_SCHEMA = {
    "type": "object",
    "required": ["expected_ref", "expected_commit"],
    "additionalProperties": False,
    "properties": {
        "expected_ref": {
            "type": "string",
            "pattern": r"^refs/heads/[A-Za-z0-9][A-Za-z0-9._/-]*$",
        },
        "expected_commit": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
    },
}
# D8: closed, path-free request schema.  Every caller-selected host path,
# remote URL, credential or authority field is refused by
# additionalProperties: False and, for defense in depth, by the explicit
# denylist checked in the adapter before anything else runs.
_MATERIALIZE_FORBIDDEN_FIELDS = (
    "dest",
    "target_path",
    "workspace_path",
    "checkout_path",
    "worktree_path",
    "cache_path",
    "staging_path",
    "remote_url",
    "credential",
    "token",
    "ssh_key",
    "sid",
    "acl",
    "allowed_write_roots",
    "protected_roots",
    "operation_classes",
    "executable",
    "argv",
)


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
        },
    ),
    # PR-014 S02: path-free, source-bounded materialization request.  Only
    # semantic repository/lineage/workspace-purpose/source-binding fields and
    # an optional comparison-only placement expectation are admitted.
    "materialize_workspace": _schema(
        ["workspace_purpose", "repository", "lineage", "source_binding"],
        {
            "workspace_purpose": {"type": "string", "minLength": 1, "maxLength": 64},
            "repository": _REPOSITORY_SCHEMA,
            "lineage": _LINEAGE_SCHEMA,
            "source_binding": _SOURCE_BINDING_SCHEMA,
            "placement_expectation": {"type": "string", "maxLength": 260},
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

        return {
            key: result[key]
            for key in _EXECUTE_SCOPED_RESULT_FIELDS
            if key in result
        }

    return execute_scoped


_MATERIALIZE_ALLOWED = frozenset(
    {"workspace_purpose", "repository", "lineage", "source_binding", "placement_expectation"}
)
_MATERIALIZE_REQUIRED = frozenset(
    {"workspace_purpose", "repository", "lineage", "source_binding"}
)


def make_devforge_materialize_adapter(
    materialization_runner: Callable[
        [RequestContext, dict[str, Any]], Awaitable[dict[str, Any]]
    ],
) -> MaterializeAdapter:
    """Admit one closed, path-free materialize_workspace request (D8)."""

    async def materialize_workspace(
        context: RequestContext,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(context, RequestContext):
            raise HandlerError(
                "HostMutationAuditLineageInvalid",
                "materialize_workspace requires transport RequestContext",
            )
        if not isinstance(params, dict):
            raise HandlerError("invalid_payload", "materialize_workspace params must be an object")

        for forbidden in _MATERIALIZE_FORBIDDEN_FIELDS:
            if forbidden in params:
                raise HandlerError(
                    "invalid_payload",
                    f"materialize_workspace never accepts caller authority field: {forbidden}",
                )
        extras = sorted(set(params) - _MATERIALIZE_ALLOWED)
        if extras:
            raise HandlerError("invalid_payload", f"unsupported materialize_workspace fields: {extras}")
        missing = sorted(_MATERIALIZE_REQUIRED - set(params))
        if missing:
            raise HandlerError("invalid_payload", f"missing materialize_workspace fields: {missing}")

        workspace_purpose = params["workspace_purpose"]
        if (
            not isinstance(workspace_purpose, str)
            or not workspace_purpose.strip()
            or len(workspace_purpose) > 64
        ):
            raise HandlerError("invalid_payload", "workspace_purpose must be a bounded string")
        placement_expectation = params.get("placement_expectation")
        if placement_expectation is not None and (
            not isinstance(placement_expectation, str) or not placement_expectation.strip()
        ):
            raise HandlerError(
                "invalid_payload", "placement_expectation must be a comparison-only string"
            )

        source_binding = _strict_mapping(
            params,
            "source_binding",
            allowed=frozenset({"expected_ref", "expected_commit"}),
            required=frozenset({"expected_ref", "expected_commit"}),
        )
        expected_ref = source_binding["expected_ref"]
        expected_commit = source_binding["expected_commit"]
        if not isinstance(expected_ref, str) or not expected_ref.startswith("refs/heads/"):
            raise HandlerError("invalid_payload", "expected_ref must be refs/heads/<logical>")
        logical = expected_ref[len("refs/heads/"):]
        if (
            not logical
            or ".." in logical
            or logical.startswith("/")
            or logical.endswith("/")
            or any(part in ("", ".", "..") for part in logical.split("/"))
        ):
            raise HandlerError(
                "invalid_payload", "expected_ref logical branch is not a safe V1 branch"
            )
        if (
            not isinstance(expected_commit, str)
            or len(expected_commit) != 40
            or any(char not in "0123456789abcdef" for char in expected_commit)
        ):
            raise HandlerError("invalid_payload", "expected_commit must be a full sha1")
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

        return await materialization_runner(
            context,
            {
                "workspace_purpose": workspace_purpose,
                "repository": repository,
                "lineage": lineage,
                "source_binding": source_binding,
                "placement_expectation": placement_expectation,
            },
        )

    return materialize_workspace


class DevforgeRuntimeProvider:
    """Policy-filtered builtin endpoint provider with no independent authority."""

    name = ENDPOINT_NAME

    def __init__(
        self,
        policy: Policy,
        lifecycle_service: LifecycleService,
        *,
        execute_scoped_adapter: ScopedExecuteAdapter | None = None,
        materialize_adapter: MaterializeAdapter | None = None,
    ) -> None:
        self._policy = policy
        self._lifecycle = lifecycle_service
        self._execute_scoped = execute_scoped_adapter
        self._materialize = materialize_adapter

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
        if self._materialize is not None and "mutation_scope" not in self._policy.disabled_ops:
            actions.append("materialize_workspace")
        return tuple(actions)

    def repository_effect(self, action: str) -> "OperationEffectResolution":
        """Deterministic repository-effect metadata for every effective action.

        Lifecycle actions never touch a repository checkout, exactly like the
        ``mutation_scope`` op.  ``execute_scoped`` reaches the physically
        contained scoped-mutation path.  ``materialize_workspace`` spawns the
        contained materializer through the same S01 scope/sandbox path; its
        coverage stays fail-closed (UNKNOWN/UNPROVEN) unless the adapter is
        active and the Host opted in, so the firewall never treats an
        unavailable seed as proven.
        """
        if action in _LIFECYCLE_ACTIONS:
            return OperationEffectResolution(
                RepositoryEffect.NON_REPOSITORY_MUTATION,
                FirewallCoverage.NOT_REQUIRED,
            )
        if action == "execute_scoped":
            if not self.host_opted_in:
                return OperationEffectResolution(
                    RepositoryEffect.UNKNOWN,
                    FirewallCoverage.UNPROVEN,
                    reason="scoped_mutation_profile_unavailable",
                )
            return OperationEffectResolution(
                RepositoryEffect.PROCESS_MUTATION,
                FirewallCoverage.PROVEN,
            )
        if action == "materialize_workspace":
            if not self.host_opted_in or self._materialize is None:
                return OperationEffectResolution(
                    RepositoryEffect.UNKNOWN,
                    FirewallCoverage.UNPROVEN,
                    reason="materialize_workspace_seed_unavailable",
                )
            return OperationEffectResolution(
                RepositoryEffect.PROCESS_MUTATION,
                FirewallCoverage.PROVEN,
            )
        return OperationEffectResolution(
            RepositoryEffect.UNKNOWN,
            FirewallCoverage.UNPROVEN,
            reason="unknown_devforge_runtime_action",
        )

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

        if action == "materialize_workspace":
            if "mutation_scope" in self._policy.disabled_ops:
                raise HandlerError(
                    "operation_disabled",
                    "mutation_scope is disabled by Host policy",
                )
            if self._materialize is None:
                raise HandlerError(
                    "endpoint_not_available",
                    "materialize_workspace adapter is not active on this Agent build",
                )
            return await self._materialize(context, params)

        raise HandlerError("unknown_action", f"unknown devforge_runtime action: {action}")


def make_devforge_runtime_provider(
    policy: Policy,
    lifecycle_service: LifecycleService,
    *,
    execute_scoped_adapter: ScopedExecuteAdapter | None = None,
    materialize_adapter: MaterializeAdapter | None = None,
) -> DevforgeRuntimeProvider:
    return DevforgeRuntimeProvider(
        policy,
        lifecycle_service,
        execute_scoped_adapter=execute_scoped_adapter,
        materialize_adapter=materialize_adapter,
    )


def make_devforge_workspace_materialization_runner(
    policy: Policy,
    *,
    config_path: Path | None = None,
    upload_base: Path | None = None,
    mutation_state_root: Path | None = None,
) -> MaterializeAdapter:
    """Compose the one canonical S02 materialization orchestrator.

    The runner owns only glue: state-root derivation matches the existing
    scoped-mutation handlers, request/lineage identities are converted to the
    provider-sealed MaterializationRequest, and every domain failure maps to
    a stable HandlerError code.  All authority semantics stay inside
    devforge_workspace_materialization.
    """
    from sentinelx_core.devforge_workspace_materialization import (
        DevforgeMaterializationError,
        MaterializationConflict,
        MaterializationNotVerified,
        MaterializationRequest,
        run_devforge_workspace_materialization,
    )
    from sentinelx_core.devforge_workspace_source import DevforgeSourceError
    from sentinelx_core.mutation_placement import RepositoryIdentity, SemanticIdentity

    fallback_base = upload_base if upload_base is not None else Path.cwd()
    state_root = (
        mutation_state_root.resolve(strict=False)
        if mutation_state_root is not None
        else (
            (config_path.parent if config_path is not None else fallback_base.parent) / "state"
        ).resolve(strict=False)
    )
    mutation_policy = policy.mutation_execution

    async def runner(
        context: RequestContext,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        repository = RepositoryIdentity(**payload["repository"])
        lineage = payload["lineage"]
        semantic = SemanticIdentity(
            project_id=lineage["project_id"],
            task_id=lineage["task_id"],
            run_id=lineage["run_id"],
            attempt_id=lineage["attempt_id"],
            slice_id=lineage.get("slice_id"),
        )
        source_binding = payload["source_binding"]
        request = MaterializationRequest(
            repository=repository,
            semantic=semantic,
            expected_ref=source_binding["expected_ref"],
            expected_commit=source_binding["expected_commit"],
            request_id=context.request_id,
            placement_expectation=payload.get("placement_expectation"),
        )
        try:
            receipt = await run_devforge_workspace_materialization(
                mutation_policy,
                policy,
                state_root,
                request,
            )
        except MaterializationConflict as exc:
            raise HandlerError(str(exc.code), str(exc)) from exc
        except MaterializationNotVerified as exc:
            raise HandlerError(str(exc.code), str(exc)) from exc
        except DevforgeSourceError as exc:
            raise HandlerError(str(exc.code), str(exc)) from exc
        except DevforgeMaterializationError as exc:
            raise HandlerError(str(exc.code), str(exc)) from exc
        return {
            "ok": True,
            "state": receipt["state"],
            "receipt_id": receipt["receipt_id"],
            "workspace": receipt["workspace"],
            "source": receipt["source"],
            "materializer": receipt["materializer"],
            "git_readback": receipt["git_readback"],
            "handoff_probe": receipt["handoff_probe"],
            "authority": receipt["authority"],
        }

    return runner
