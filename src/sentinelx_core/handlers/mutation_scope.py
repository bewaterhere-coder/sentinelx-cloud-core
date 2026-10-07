"""Provider-owned mutation scope lifecycle handler.

This handler exposes bounded lifecycle actions over the existing
``MutationScopeStore``. It never executes user code, never accepts caller-owned
operation-class authority, and never creates a second scope ledger.
"""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from sentinelx_core.executor import HandlerError
from sentinelx_core.mutation_placement import (
    HostMutationScopeBindingMismatch,
    RepositoryIdentity,
    SemanticIdentity,
)
from sentinelx_core.mutation_scope import (
    SCOPED_SCRIPT_OPERATION_CLASS,
    HostMutationScopeError,
    MutationScopeRecord,
    MutationScopeStore,
)
from sentinelx_core.mutation_sandbox import (
    HostMutationSandboxError,
    build_mutation_sandbox,
)
from sentinelx_core.policy import Policy
from sentinelx_core.request_context import MutationLineage, RequestContext, context_aware

_PURPOSE_SCOPED_SCRIPT = "scoped_script"
_ACTIONS = frozenset({"provision", "revalidate", "inspect", "terminalize"})
_COMMON_KEYS = frozenset({"action", "repository", "lineage"})
_PROVISION_KEYS = _COMMON_KEYS | {"purpose"}
_BOUND_KEYS = _COMMON_KEYS | {"scope_ref"}
_REPOSITORY_KEYS = frozenset({"vcs", "authority", "path"})
_LINEAGE_KEYS = frozenset({"project_id", "task_id", "run_id", "attempt_id", "slice_id"})
_SCOPE_REF_KEYS = frozenset({"scope_id", "generation"})


def _strict_mapping(
    value: object,
    *,
    name: str,
    allowed: frozenset[str],
    required: frozenset[str],
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise HandlerError("invalid_payload", f"{name} must be a mapping")
    keys = set(value.keys())
    non_string = [key for key in keys if not isinstance(key, str)]
    if non_string:
        raise HandlerError("invalid_payload", f"{name} keys must be strings")
    unknown = sorted(keys - allowed)
    if unknown:
        raise HandlerError(
            "invalid_payload",
            f"{name} contains forbidden or unsupported fields: {', '.join(unknown)}",
        )
    missing = sorted(required - keys)
    if missing:
        raise HandlerError("invalid_payload", f"{name} is missing required fields: {', '.join(missing)}")
    return value


def _parse_repository(payload: Mapping[str, Any]) -> RepositoryIdentity:
    raw = _strict_mapping(
        payload.get("repository"),
        name="repository",
        allowed=_REPOSITORY_KEYS,
        required=_REPOSITORY_KEYS,
    )
    if not all(isinstance(raw.get(field), str) and str(raw[field]).strip() for field in _REPOSITORY_KEYS):
        raise HandlerError("invalid_payload", "repository requires non-empty vcs, authority and path")
    try:
        repository = RepositoryIdentity(
            vcs=str(raw["vcs"]),
            authority=str(raw["authority"]),
            path=str(raw["path"]),
        )
        _ = repository.canonical
        return repository
    except ValueError as exc:
        raise HandlerError("invalid_payload", str(exc)) from exc


def _parse_semantic(payload: Mapping[str, Any]) -> SemanticIdentity:
    raw = _strict_mapping(
        payload.get("lineage"),
        name="lineage",
        allowed=_LINEAGE_KEYS,
        required=frozenset({"project_id", "task_id", "run_id", "attempt_id"}),
    )
    try:
        lineage = MutationLineage.from_mapping(raw)
    except ValueError as exc:
        raise HandlerError("HostMutationAuditLineageInvalid", str(exc)) from exc
    return SemanticIdentity(
        project_id=lineage.project_id,
        task_id=lineage.task_id,
        run_id=lineage.run_id,
        attempt_id=lineage.attempt_id,
        slice_id=lineage.slice_id,
    )


def _parse_scope_ref(payload: Mapping[str, Any]) -> tuple[str, int]:
    raw = _strict_mapping(
        payload.get("scope_ref"),
        name="scope_ref",
        allowed=_SCOPE_REF_KEYS,
        required=_SCOPE_REF_KEYS,
    )
    scope_id = raw.get("scope_id")
    generation = raw.get("generation")
    if not isinstance(scope_id, str) or not scope_id.strip():
        raise HandlerError("invalid_payload", "scope_ref.scope_id must be a non-empty string")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation <= 0:
        raise HandlerError("invalid_payload", "scope_ref.generation must be a positive integer")
    return scope_id.strip(), generation


def _project(record: MutationScopeRecord) -> dict[str, Any]:
    purpose = (
        _PURPOSE_SCOPED_SCRIPT
        if SCOPED_SCRIPT_OPERATION_CLASS in record.allowed_operation_classes
        else None
    )
    return {
        "scope_id": record.scope_id,
        "generation": record.generation,
        "workspace_id": record.workspace_id,
        "state": record.state,
        "issued_at": record.issued_at,
        "expires_at": record.expires_at,
        "terminalized_at": record.terminalized_at,
        "scope_digest": record.scope_digest,
        "exact_workspace_digest": record.exact_workspace_digest,
        "protected_inventory_digest": record.protected_inventory_digest,
        "repository_identity_digest": record.repository_identity_digest,
        "semantic_identity_digest": record.semantic_identity_digest,
        "purpose": purpose,
    }


def _store_error(exc: Exception) -> HandlerError:
    code = str(getattr(exc, "code", type(exc).__name__))
    return HandlerError(code, str(exc))


def make_mutation_scope_service(
    policy: Policy,
    upload_base: Path,
    *,
    config_path: Path | None = None,
    mutation_state_root: Path | None = None,
):
    """Canonical lifecycle service shared by bounded transport adapters."""
    state_root = (
        mutation_state_root.resolve(strict=False)
        if mutation_state_root is not None
        else ((config_path.parent if config_path is not None else upload_base.parent) / "state").resolve(strict=False)
    )

    async def service(payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise HandlerError("invalid_payload", "mutation_scope payload must be a mapping")
        action = payload.get("action")
        if not isinstance(action, str) or action not in _ACTIONS:
            raise HandlerError("invalid_payload", "mutation_scope.action must be one of provision, revalidate, inspect, terminalize")
        allowed_top = _PROVISION_KEYS if action == "provision" else _BOUND_KEYS
        _strict_mapping(payload, name="payload", allowed=allowed_top, required=allowed_top)
        mutation_policy = policy.mutation_execution
        if not mutation_policy.configured or not mutation_policy.scoped_mutation_enabled:
            raise HandlerError("HostMutationSandboxUnavailable", "scoped mutation lifecycle is not enabled by Host policy")
        repository = _parse_repository(payload)
        semantic = _parse_semantic(payload)
        store = MutationScopeStore(state_root)
        protected = (state_root.resolve(strict=False),)
        try:
            if action == "provision":
                if payload.get("purpose") != _PURPOSE_SCOPED_SCRIPT:
                    raise HandlerError("invalid_payload", "mutation_scope provision supports only purpose=scoped_script")
                record = store.provision_scope(
                    mutation_policy,
                    repository,
                    semantic,
                    allowed_operation_classes=(SCOPED_SCRIPT_OPERATION_CLASS,),
                    provider_protected_roots=protected,
                )
            else:
                scope_id, generation = _parse_scope_ref(payload)
                if action == "revalidate":
                    record = store.revalidate_scope_for_operation(
                        scope_id,
                        generation,
                        mutation_policy,
                        repository,
                        semantic,
                        required_operation_class=SCOPED_SCRIPT_OPERATION_CLASS,
                        provider_protected_roots=protected,
                    )
                elif action == "inspect":
                    record = store.read_bound_scope(scope_id, generation, repository, semantic)
                else:
                    current = store.read_bound_scope(
                        scope_id,
                        generation,
                        repository,
                        semantic,
                    )
                    has_runtime_authority = bool(
                        current.active_job_ids
                        or current.active_process_ids
                        or current.sandbox_write_authority_present
                        or current.runtime_read_authority_roots
                        or current.session_object_read_binding is not None
                    )
                    if has_runtime_authority:
                        # Reuse the one canonical Windows sandbox cleanup path.
                        # Durable residual authority must never be cleared by a
                        # store-only terminalization that cannot prove OS closure.
                        sandbox = build_mutation_sandbox(
                            policy=mutation_policy,
                            scope_store=store,
                            repository=repository,
                            semantic=semantic,
                            provider_protected_roots=protected,
                        )
                        record = sandbox.terminalize(scope_id, generation)
                    else:
                        record = store.terminalize_scope(
                            scope_id,
                            generation,
                            mutation_policy,
                            repository,
                            semantic,
                            provider_protected_roots=protected,
                        )
        except HandlerError:
            raise
        except (
            HostMutationScopeError,
            HostMutationScopeBindingMismatch,
            HostMutationSandboxError,
        ) as exc:
            raise _store_error(exc) from exc
        except ValueError as exc:
            raise HandlerError("invalid_payload", str(exc)) from exc
        return {"action": action, "scope": _project(record)}

    return service


def make_mutation_scope_handler(
    policy: Policy,
    upload_base: Path,
    *,
    config_path: Path | None = None,
    mutation_state_root: Path | None = None,
    lifecycle_service=None,
):
    """Build the direct mutation_scope transport adapter."""
    service = lifecycle_service or make_mutation_scope_service(
        policy,
        upload_base,
        config_path=config_path,
        mutation_state_root=mutation_state_root,
    )

    @context_aware
    async def handle(context: RequestContext, payload: dict[str, Any]) -> dict[str, Any]:
        if context.op != "mutation_scope":
            raise HandlerError("invalid_payload", "transport operation does not match mutation_scope")
        return await service(payload)

    return handle
