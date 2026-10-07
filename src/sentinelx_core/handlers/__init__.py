"""Op handlers: one async function per `op`.

Each handler takes a payload dict and returns a result dict (or raises HandlerError).

The registry binds handlers to the Policy at startup. Handlers that need
configuration (allowed commands, allowed services, upload_base) are built via
factories that close over the policy; stateless handlers (ping, state) are
referenced directly.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from sentinelx_core.handlers.basic import (
    handle_ping,
    handle_state,
    make_capabilities_handler,
    make_help_handler,
    make_read_audit_handler,
)
from sentinelx_core.handlers.devforge_runtime import (
    make_devforge_execute_scoped_adapter,
    make_devforge_materialize_adapter,
    make_devforge_runtime_provider,
    make_devforge_workspace_materialization_runner,
)
from sentinelx_core.handlers.edit import (
    make_edit_handler,
    make_edit_upload_complete_handler,
    make_edit_upload_file_handler,
    make_edit_upload_init_handler,
)
from sentinelx_core.handlers.exec import make_exec_handler
from sentinelx_core.handlers.file_export import (
    make_file_export_chunk_handler,
    make_file_export_complete_handler,
    make_file_export_init_handler,
)
from sentinelx_core.handlers.fileops import (
    make_list_handler,
    make_read_handler,
    make_search_handler,
)
from sentinelx_core.handlers.fsmutate import (
    make_chmod_handler,
    make_chown_handler,
    make_copy_handler,
    make_delete_handler,
    make_move_handler,
)
from sentinelx_core.handlers.git_ops import make_git_handler
from sentinelx_core.handlers.mutation_scope import (
    make_mutation_scope_handler,
    make_mutation_scope_service,
)
from sentinelx_core.handlers.project_snapshot import make_project_snapshot_handler
from sentinelx_core.handlers.scoped_script import make_profiled_script_run_handler
from sentinelx_core.handlers.service import make_restart_handler, make_service_handler
from sentinelx_core.handlers.upload import (
    make_upload_chunk_handler,
    make_upload_complete_handler,
    make_upload_file_handler,
    make_upload_init_handler,
)
from sentinelx_core.operation_registry import (
    canonical_repository_mutation_firewall_feature,
)
from sentinelx_core.policy import Policy

Handler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


# Ops an operator cannot switch off. Without these the hub cannot learn what a
# host is, tell whether it is alive, or explain itself -- an agent that answers
# nothing is worse than one that is absent, because it still holds a slot and
# still looks connected. `help` stays for the same reason: the one op that can
# explain why another is missing must not be the one that is missing.
logger = logging.getLogger(__name__)

UNDISABLEABLE_OPS = frozenset({"ping", "capabilities", "state", "help"})


def build_registry(
    config_path: Path | None = None,
    policy: Policy | None = None,
) -> dict[str, Handler]:
    """Build the op → handler registry from a Policy.

    Provide either `config_path` (loaded with Policy.from_file) or `policy`
    directly (useful in tests).
    """
    if policy is None:
        if config_path is None:
            policy = Policy.empty()
        else:
            policy = Policy.from_file(config_path)

    # Make platform guidance backend-aware (issue #7): a per-user Scheduled Task
    # install (backend=task) must be described as a task, not a WinSW service, so
    # the restart op / log paths / host wording the agent emits are correct. The
    # agent's own service entry is keyed by platform_guidance.SERVICE_KEY. We also
    # pin the guidance's config path to the agent's ACTUAL --config file, so a
    # per-user install points the operator at %LOCALAPPDATA%\SentinelX (its only
    # rw config) rather than the C:\ProgramData service default.
    from sentinelx_core import platform_guidance as _pg
    _self_svc = policy.services.get(_pg.SERVICE_KEY)
    _pg.set_backend(getattr(_self_svc, "backend", "service") if _self_svc else "service")
    _pg.set_config_path(config_path)

    upload_base = policy.upload_base
    mutation_scope_service = make_mutation_scope_service(policy, upload_base, config_path=config_path)
    profiled_script_run = make_profiled_script_run_handler(
        policy,
        upload_base,
        config_path=config_path,
    )
    devforge_runtime = make_devforge_runtime_provider(
        policy,
        mutation_scope_service,
        execute_scoped_adapter=make_devforge_execute_scoped_adapter(profiled_script_run),
        materialize_adapter=make_devforge_materialize_adapter(
            make_devforge_workspace_materialization_runner(
                policy,
                config_path=config_path,
                upload_base=upload_base,
            )
        ),
    )

    registry: dict[str, Handler] = {
        # Read-only / introspection
        "ping": handle_ping,
        # "capabilities" is attached after this dict is built, so it can
        # close over the finished registry and derive ops_supported from
        # it (see the end of this function).
        "help": make_help_handler(policy),
        "state": handle_state,

        # Command execution
        "exec": make_exec_handler(policy),
        "service": make_service_handler(policy),
        "restart": make_restart_handler(policy),
        "script_run": profiled_script_run,
        "mutation_scope": make_mutation_scope_handler(
            policy,
            upload_base,
            config_path=config_path,
            lifecycle_service=mutation_scope_service,
        ),

        # File editing
        "edit": make_edit_handler(policy, upload_base),
        "edit_upload_init": make_edit_upload_init_handler(upload_base),
        "edit_upload_file": make_edit_upload_file_handler(upload_base),
        "edit_upload_complete": make_edit_upload_complete_handler(policy, upload_base),

        # File uploads
        "upload_file": make_upload_file_handler(policy, upload_base),
        "upload_init": make_upload_init_handler(upload_base, policy),
        "upload_chunk": make_upload_chunk_handler(upload_base),
        "upload_complete": make_upload_complete_handler(policy, upload_base),

        # Cross-host file transfer (source side, INTERNAL — driven by the Hub's
        # sentinel_transfer_file coordinator, not a model-visible tool). The
        # destination side reuses upload_init/upload_complete + a binary ingest
        # path on the client (executor.ingest_transfer_chunk).
        "file_export_init": make_file_export_init_handler(policy),
        "file_export_chunk": make_file_export_chunk_handler(policy),
        "file_export_complete": make_file_export_complete_handler(),

        # Read-only filesystem primitives (Story 6)
        "read": make_read_handler(policy),
        "list": make_list_handler(policy),
        "search": make_search_handler(policy),
        "project_snapshot": make_project_snapshot_handler(policy),

        # Structured Git ops (sentinel_git): diff (read) + apply_patch (rw).
        # Quarantined here; nothing git-specific bleeds into edit/agnostic core.
        "git": make_git_handler(policy),

        # Local audit log (Story C) — read-only, returns recent on-host
        # audit entries (op + payload). No policy arg: it only reads the
        # agent's own audit file, not arbitrary paths.
        "read_audit": make_read_audit_handler(),

        # Mutating filesystem ops — every path gated at access: rw
        # (unified r/rw model). See handlers/fsmutate.py.
        "move": make_move_handler(policy),
        "copy": make_copy_handler(policy),
        "delete": make_delete_handler(policy),
        "chmod": make_chmod_handler(policy),
        "chown": make_chown_handler(policy),
    }

    # The registry is the single source of truth for what this agent can
    # dispatch, so capabilities.ops_supported is DERIVED from it rather than
    # hand-maintained. The lambda is evaluated at request time, when the dict
    # (including "capabilities" itself) is complete. Hand-maintaining it
    # drifted twice -- move/copy/delete/chmod/chown, then file_export_* and
    # project_snapshot (issue #32) -- so a new op is now advertised the
    # moment it is registered here, and nothing else needs touching.
    def _canonical_firewall_feature() -> dict[str, Any]:
        return canonical_repository_mutation_firewall_feature(registry, policy)

    registry["capabilities"] = make_capabilities_handler(
        policy,
        config_path,
        ops_supported=lambda: registry.keys(),
        upload_base=upload_base,
        canonical_firewall_feature=_canonical_firewall_feature,
    )

    # Reuse the existing local_api envelope for configured external endpoints
    # and for a policy-admitted builtin provider. External name collisions keep
    # the configured endpoint authoritative.
    if policy.local_apis or devforge_runtime.available_actions():
        from sentinelx_core.handlers.local_api import make_local_api_handler

        registry["local_api"] = make_local_api_handler(
            policy,
            builtin_providers={devforge_runtime.name: devforge_runtime},
        )

    # Switched-off ops are removed here, at the end, so this is the last word
    # regardless of how a handler got in. Removal rather than a guard inside
    # each handler: capabilities derives ops_supported from these keys and
    # dispatch answers unsupported_op for anything absent, so one deletion
    # makes the op invisible AND unreachable with no second path to keep in
    # step. A guard would have to be remembered in every handler, and forgotten
    # in one.
    if policy.disabled_ops:
        refused = policy.disabled_ops & UNDISABLEABLE_OPS
        if refused:
            logger.warning(
                "policy_undisableable_ops",
                extra={
                    "requested": sorted(refused),
                    "reason": (
                        "these ops are how the hub learns what this host is and "
                        "whether it is alive; an agent that cannot answer a thing "
                        "still holds a slot and still looks connected"
                    ),
                },
            )
        removed = sorted((policy.disabled_ops & registry.keys()) - UNDISABLEABLE_OPS)
        for op in removed:
            del registry[op]
        unknown = sorted(policy.disabled_ops - set(registry) - UNDISABLEABLE_OPS - set(removed))
        logger.info(
            "policy_disabled_ops",
            extra={
                "removed": removed,
                # A name this agent never had is almost always a typo, and a
                # typo in the deny list reads as protection that is not there.
                "not_recognised": unknown,
            },
        )

    return registry
