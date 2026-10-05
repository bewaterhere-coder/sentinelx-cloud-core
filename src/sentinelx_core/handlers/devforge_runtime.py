"""Bounded Agent-owned ``devforge_runtime`` local_api provider.

The provider composes existing Host-owned scope/execution authority. Repository
transaction admission adds no Host path, Git argv, credential, or operation-
class authority to callers.
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from sentinelx_core.executor import HandlerError
from sentinelx_core.mutation_placement import RepositoryIdentity, SemanticIdentity
from sentinelx_core.policy import Policy
from sentinelx_core.repository_transaction import (
    REPOSITORY_TRANSACTION_PURPOSE,
    RepositoryRefResolver,
    RepositoryTransactionAdmissionFailed,
    RepositoryTransactionError,
    RepositoryTransactionStore,
    make_repository_ref_resolver,
    validate_full_commit_sha,
    validate_git_ref,
)
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
_REPOSITORY_TRANSACTION_SCHEMA = {
    "type": "object",
    "required": [
        "source_ref",
        "expected_source_sha",
        "publication_ref",
        "expected_remote_sha",
    ],
    "additionalProperties": False,
    "properties": {
        "source_ref": {"type": "string"},
        "expected_source_sha": {"type": "string"},
        "publication_ref": {"type": "string", "pattern": "^refs/heads/"},
        "expected_remote_sha": {"type": "string"},
    },
}


def _schema(required: list[str], properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "required": required,
        "additionalProperties": False,
        "properties": properties,
    }


def _provision_scope_schema(repository_ready: bool) -> dict[str, Any]:
    if not repository_ready:
        return _schema(
            ["purpose", "repository", "lineage"],
            {
                "purpose": {"const": "scoped_script"},
                "repository": _REPOSITORY_SCHEMA,
                "lineage": _LINEAGE_SCHEMA,
            },
        )
    schema = _schema(
        ["purpose", "repository", "lineage"],
        {
            "purpose": {"enum": ["scoped_script", REPOSITORY_TRANSACTION_PURPOSE]},
            "repository": _REPOSITORY_SCHEMA,
            "lineage": _LINEAGE_SCHEMA,
            "repository_transaction": _REPOSITORY_TRANSACTION_SCHEMA,
        },
    )
    schema["allOf"] = [
        {
            "if": {"properties": {"purpose": {"const": REPOSITORY_TRANSACTION_PURPOSE}}},
            "then": {"required": ["repository_transaction"]},
        }
    ]
    return schema


_ACTION_SCHEMAS = {
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
    "inspect_repository_transaction": _schema(
        ["scope_ref", "repository", "lineage"],
        {
            "scope_ref": _SCOPE_REF_SCHEMA,
            "repository": _REPOSITORY_SCHEMA,
            "lineage": _LINEAGE_SCHEMA,
        },
    ),
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


def _repository_identity(params: dict[str, Any]) -> tuple[dict[str, Any], RepositoryIdentity]:
    raw = _strict_mapping(
        params,
        "repository",
        allowed=frozenset({"vcs", "authority", "path"}),
        required=frozenset({"vcs", "authority", "path"}),
    )
    try:
        identity = RepositoryIdentity(
            vcs=str(raw["vcs"]),
            authority=str(raw["authority"]),
            path=str(raw["path"]),
        )
        _ = identity.canonical
    except ValueError as exc:
        raise HandlerError("invalid_payload", str(exc)) from exc
    return raw, identity


def _semantic_identity(params: dict[str, Any]) -> tuple[dict[str, Any], SemanticIdentity]:
    raw = _strict_mapping(
        params,
        "lineage",
        allowed=frozenset({"project_id", "task_id", "run_id", "attempt_id", "slice_id"}),
        required=frozenset({"project_id", "task_id", "run_id", "attempt_id"}),
    )
    try:
        identity = SemanticIdentity(
            project_id=str(raw["project_id"]),
            task_id=str(raw["task_id"]),
            run_id=str(raw["run_id"]),
            attempt_id=str(raw["attempt_id"]),
            slice_id=str(raw["slice_id"]) if raw.get("slice_id") is not None else None,
        )
        _ = identity.canonical
    except ValueError as exc:
        raise HandlerError("HostMutationAuditLineageInvalid", str(exc)) from exc
    return raw, identity


def _scope_ref(params: dict[str, Any]) -> dict[str, Any]:
    raw = _strict_mapping(
        params,
        "scope_ref",
        allowed=frozenset({"scope_id", "generation"}),
        required=frozenset({"scope_id", "generation"}),
    )
    scope_id = raw.get("scope_id")
    generation = raw.get("generation")
    if not isinstance(scope_id, str) or not scope_id.strip():
        raise HandlerError("invalid_payload", "scope_ref.scope_id must be a non-empty string")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation <= 0:
        raise HandlerError("invalid_payload", "scope_ref.generation must be a positive integer")
    return {"scope_id": scope_id.strip(), "generation": generation}


def _transaction_error(exc: RepositoryTransactionError) -> HandlerError:
    return HandlerError(str(getattr(exc, "code", type(exc).__name__)), str(exc))


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

        scope_ref = _scope_ref(params)
        repository, _repository_identity_value = _repository_identity(params)
        lineage, _semantic_identity_value = _semantic_identity(params)

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


class DevforgeRuntimeProvider:
    """Policy-filtered builtin endpoint provider with no independent authority."""

    name = ENDPOINT_NAME

    def __init__(
        self,
        policy: Policy,
        lifecycle_service: LifecycleService,
        *,
        execute_scoped_adapter: ScopedExecuteAdapter | None = None,
        repository_transaction_store: RepositoryTransactionStore | None = None,
        repository_ref_resolver: RepositoryRefResolver | None = None,
    ) -> None:
        self._policy = policy
        self._lifecycle = lifecycle_service
        self._execute_scoped = execute_scoped_adapter
        state_root = (policy.upload_base.parent / "state").resolve(strict=False)
        self._repository_transactions = repository_transaction_store or RepositoryTransactionStore(
            state_root
        )
        self._repository_ref_resolver = repository_ref_resolver or make_repository_ref_resolver(
            policy
        )

    @property
    def host_opted_in(self) -> bool:
        mutation = self._policy.mutation_execution
        return mutation.configured and mutation.scoped_mutation_enabled

    @property
    def repository_transactions_ready(self) -> bool:
        mutation = self._policy.mutation_execution
        return (
            self.host_opted_in
            and self._policy.authenticated_git_enabled
            and mutation.canonical_repository_inventory_ready
        )

    def available_actions(self) -> tuple[str, ...]:
        if not self.host_opted_in:
            return ()
        actions: list[str] = []
        if "mutation_scope" not in self._policy.disabled_ops:
            actions.extend(_LIFECYCLE_ACTIONS)
            if self.repository_transactions_ready:
                actions.append("inspect_repository_transaction")
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

    def _action_schema(self, action: str) -> dict[str, Any]:
        if action == "provision_scope":
            return _provision_scope_schema(self.repository_transactions_ready)
        return _ACTION_SCHEMAS[action]

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
                    "params": list(self._action_schema(action)["required"]),
                    "params_schema": self._action_schema(action),
                }
                for action in actions
            },
        }

    async def _provision_repository_transaction(self, params: dict[str, Any]) -> dict[str, Any]:
        if not self.repository_transactions_ready:
            raise HandlerError(
                "RepositoryTransactionUnavailable",
                "repository transaction admission requires canonical inventory and user-scoped Git",
            )
        allowed_top = frozenset({"purpose", "repository", "lineage", "repository_transaction"})
        extras = sorted(set(params) - allowed_top)
        if extras:
            raise HandlerError("invalid_payload", f"unsupported provision_scope fields: {extras}")
        repository, repository_identity = _repository_identity(params)
        lineage, semantic_identity = _semantic_identity(params)
        raw = _strict_mapping(
            params,
            "repository_transaction",
            allowed=frozenset(
                {"source_ref", "expected_source_sha", "publication_ref", "expected_remote_sha"}
            ),
            required=frozenset(
                {"source_ref", "expected_source_sha", "publication_ref", "expected_remote_sha"}
            ),
        )
        try:
            source_ref = validate_git_ref(raw["source_ref"], field="source_ref")
            expected_source_sha = validate_full_commit_sha(
                raw["expected_source_sha"], field="expected_source_sha"
            )
            publication_ref = validate_git_ref(
                raw["publication_ref"], field="publication_ref", publication=True
            )
            expected_remote_sha = validate_full_commit_sha(
                raw["expected_remote_sha"], field="expected_remote_sha"
            )
            verified_source_sha = await self._repository_ref_resolver(
                repository_identity, source_ref
            )
            verified_remote_sha = await self._repository_ref_resolver(
                repository_identity, publication_ref
            )
            if verified_source_sha.lower() != expected_source_sha:
                raise RepositoryTransactionAdmissionFailed(
                    "source_ref does not resolve to expected_source_sha"
                )
            if verified_remote_sha.lower() != expected_remote_sha:
                raise RepositoryTransactionAdmissionFailed(
                    "publication_ref does not resolve to expected_remote_sha"
                )
        except RepositoryTransactionError as exc:
            raise _transaction_error(exc) from exc

        scope_result = await self._lifecycle(
            {
                "action": "provision",
                "purpose": REPOSITORY_TRANSACTION_PURPOSE,
                "repository": repository,
                "lineage": lineage,
            }
        )
        scope = scope_result.get("scope") if isinstance(scope_result, dict) else None
        if not isinstance(scope, dict):
            raise HandlerError(
                "RepositoryTransactionBindingMismatch",
                "scope provider returned no repository transaction scope binding",
            )
        try:
            record = self._repository_transactions.provision(
                repository_identity,
                semantic_identity,
                scope=scope,
                source_ref=source_ref,
                expected_source_sha=expected_source_sha,
                verified_source_sha=verified_source_sha,
                publication_ref=publication_ref,
                expected_remote_sha=expected_remote_sha,
                verified_remote_sha=verified_remote_sha,
            )
        except RepositoryTransactionError as exc:
            raise _transaction_error(exc) from exc

        result = dict(scope_result)
        result["repository_transaction"] = record.project()
        return result

    async def _inspect_repository_transaction(self, params: dict[str, Any]) -> dict[str, Any]:
        if not self.repository_transactions_ready:
            raise HandlerError(
                "RepositoryTransactionUnavailable",
                "repository transaction inspection is not admitted by Host policy",
            )
        extras = sorted(set(params) - {"scope_ref", "repository", "lineage"})
        if extras:
            raise HandlerError("invalid_payload", f"unsupported inspect fields: {extras}")
        scope = _scope_ref(params)
        _repository, repository_identity = _repository_identity(params)
        _lineage, semantic_identity = _semantic_identity(params)
        try:
            record = self._repository_transactions.inspect(
                repository_identity,
                semantic_identity,
                scope_id=scope["scope_id"],
                generation=scope["generation"],
            )
        except RepositoryTransactionError as exc:
            raise _transaction_error(exc) from exc
        return {
            "action": "inspect_repository_transaction",
            "repository_transaction": record.project(),
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
        if not isinstance(params, dict):
            raise HandlerError("invalid_payload", "devforge_runtime params must be an object")
        if "action" in params:
            raise HandlerError("invalid_payload", "params.action is transport-owned")

        if action == "provision_scope" and params.get("purpose") == REPOSITORY_TRANSACTION_PURPOSE:
            if "mutation_scope" in self._policy.disabled_ops:
                raise HandlerError("operation_disabled", "mutation_scope is disabled by Host policy")
            return await self._provision_repository_transaction(params)

        if action in _LIFECYCLE_ACTIONS:
            if "mutation_scope" in self._policy.disabled_ops:
                raise HandlerError(
                    "operation_disabled",
                    "mutation_scope is disabled by Host policy",
                )
            if action == "provision_scope" and "repository_transaction" in params:
                raise HandlerError(
                    "invalid_payload",
                    "repository_transaction is valid only with purpose=repository_transaction_v1",
                )
            payload = dict(params)
            payload["action"] = _LIFECYCLE_ACTIONS[action]
            return await self._lifecycle(payload)

        if action == "inspect_repository_transaction":
            if "mutation_scope" in self._policy.disabled_ops:
                raise HandlerError("operation_disabled", "mutation_scope is disabled by Host policy")
            return await self._inspect_repository_transaction(params)

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
    repository_transaction_store: RepositoryTransactionStore | None = None,
    repository_ref_resolver: RepositoryRefResolver | None = None,
) -> DevforgeRuntimeProvider:
    return DevforgeRuntimeProvider(
        policy,
        lifecycle_service,
        execute_scoped_adapter=execute_scoped_adapter,
        repository_transaction_store=repository_transaction_store,
        repository_ref_resolver=repository_ref_resolver,
    )
