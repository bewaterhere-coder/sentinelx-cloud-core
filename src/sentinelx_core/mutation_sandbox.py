"""Platform-neutral scoped mutation sandbox contracts.

S04 fixes Windows V1 to a real AppContainer + exact workspace ACL + Job Object
boundary. Other platforms deliberately report unavailable rather than silently
falling back to an ordinary token, command filtering or path checks.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentinelx_core.mutation_audit import MutationAuditStart
    from sentinelx_core.mutation_placement import RepositoryIdentity, SemanticIdentity
    from sentinelx_core.mutation_scope import MutationScopeRecord, MutationScopeStore
    from sentinelx_core.policy import MutationExecutionPolicy


class HostMutationSandboxError(RuntimeError):
    code = "HostMutationSandboxError"


class HostMutationSandboxUnavailable(HostMutationSandboxError):
    code = "HostMutationSandboxUnavailable"


class HostMutationSandboxBindingMismatch(HostMutationSandboxError):
    code = "HostMutationSandboxBindingMismatch"


class HostMutationSandboxPathViolation(HostMutationSandboxError):
    code = "HostMutationSandboxPathViolation"


class HostMutationSandboxAclViolation(HostMutationSandboxError):
    code = "HostMutationSandboxAclViolation"


class HostMutationSandboxContainmentFailed(HostMutationSandboxError):
    code = "HostMutationSandboxContainmentFailed"


class HostMutationSandboxResidualAuthority(HostMutationSandboxError):
    code = "HostMutationSandboxResidualAuthority"


@dataclass(frozen=True)
class ActivatedMutationSandbox:
    scope_id: str
    generation: int
    workspace_id: str
    unique_lease_key: str
    workspace: Path
    sandbox_identity: str
    appcontainer_name: str
    broker_identity: str


@dataclass(frozen=True)
class SandboxClosureEvidence:
    sandbox_identity: str | None
    active_job_ids: tuple[str, ...] = ()
    active_process_ids: tuple[str, ...] = ()
    sandbox_write_authority_present: bool = False


def build_mutation_sandbox(
    *,
    policy: MutationExecutionPolicy,
    scope_store: MutationScopeStore,
    repository: RepositoryIdentity,
    semantic: SemanticIdentity,
    provider_protected_roots: tuple[Path, ...] = (),
):
    """Return the only V1 sandbox implementation, or fail closed."""
    if sys.platform != "win32":
        raise HostMutationSandboxUnavailable(
            "host_mutation_sandbox_v1 is unavailable: Windows AppContainer enforcement is required"
        )
    from sentinelx_core.windows_mutation_sandbox import WindowsMutationSandbox

    return WindowsMutationSandbox(
        policy=policy,
        scope_store=scope_store,
        repository=repository,
        semantic=semantic,
        provider_protected_roots=provider_protected_roots,
    )


def assert_audit_scope_binding(
    start: MutationAuditStart, record: MutationScopeRecord
) -> None:
    """Bind the S03 durable START to the exact S02 provider-owned lease."""
    binding = start.binding
    if (
        binding.scope_id != record.scope_id
        or binding.scope_generation != record.generation
        or binding.workspace_id != record.workspace_id
        or binding.unique_lease_key != record.unique_lease_key
    ):
        raise HostMutationSandboxBindingMismatch(
            "durable OPERATION_STARTED does not bind the exact current mutation scope"
        )
