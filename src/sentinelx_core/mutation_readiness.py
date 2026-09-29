"""Runtime self-check for scoped mutation capability advertisement.

Capability advertisement is fail-closed: Windows/API presence alone is not
enough.  A successful probe exercises the durable scope/audit stores, an exact
AppContainer workspace ACL, suspended Job-contained spawn, runtime execution,
and terminal residual-authority closure against a disposable provider-owned
workspace.  Successful results are cached for the life of the agent process.
"""
from __future__ import annotations

import logging
import os
import secrets
import sys
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sentinelx_core.mutation_audit import (
    MutationAuditBinding,
    MutationAuditJournal,
    MutationAuthorityEvidence,
    MutationFinishClosureEvidence,
    MutationProcessIntent,
)
from sentinelx_core.mutation_placement import RepositoryIdentity, SemanticIdentity
from sentinelx_core.mutation_sandbox import build_mutation_sandbox
from sentinelx_core.mutation_scope import MutationScopeStore
from sentinelx_core.policy import MutationExecutionPolicy
from sentinelx_core.request_context import MutationLineage, RequestContext
from sentinelx_core.windows_mutation_sandbox import (
    final_executable_path,
    requested_mutation_identity,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MutationRuntimeReadiness:
    available: bool
    reason: str
    checks: dict[str, bool]

    def feature(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "verified": self.available,
            "platform": "windows_appcontainer_v1",
            "self_check": "verified" if self.available else "unavailable",
            "reason": self.reason,
            "checks": dict(self.checks),
        }


_CACHE_LOCK = threading.Lock()
_CACHE: dict[tuple[object, ...], MutationRuntimeReadiness] = {}


def _cache_key(policy: MutationExecutionPolicy, state_root: Path) -> tuple[object, ...]:
    return (
        str(state_root.resolve(strict=False)).casefold(),
        policy.configured,
        policy.scoped_mutation_enabled,
        str(policy.workspace_root).casefold() if policy.workspace_root else None,
        tuple(str(path).casefold() for path in policy.protected_roots),
        tuple(str(path).casefold() for path in policy.runtime_read_roots),
        policy.scope_ttl_seconds,
        policy.evidence_retention_days,
    )


def _probe_environment(workspace: Path) -> dict[str, str]:
    profile = workspace / ".readiness-profile"
    local = profile / "AppData" / "Local"
    roaming = profile / "AppData" / "Roaming"
    local.mkdir(parents=True, exist_ok=True)
    roaming.mkdir(parents=True, exist_ok=True)
    text = str(profile)
    return {
        "SystemRoot": os.environ.get("SystemRoot", r"C:\Windows"),
        "WINDIR": os.environ.get("WINDIR", r"C:\Windows"),
        "TEMP": str(workspace),
        "TMP": str(workspace),
        "HOME": text,
        "USERPROFILE": text,
        "HOMEDRIVE": workspace.drive or os.environ.get("SystemDrive", "C:"),
        "HOMEPATH": text[2:] if len(text) >= 2 and text[1:2] == ":" else text,
        "APPDATA": str(roaming),
        "LOCALAPPDATA": str(local),
        "PYTHONIOENCODING": "utf-8",
    }


def _unavailable(reason: str, checks: dict[str, bool]) -> MutationRuntimeReadiness:
    return MutationRuntimeReadiness(False, reason, checks)


def _probe_once(
    policy: MutationExecutionPolicy,
    state_root: Path,
) -> MutationRuntimeReadiness:
    checks: dict[str, bool] = {
        "windows": False,
        "policy_enabled": False,
        "placement_store": False,
        "scope_store": False,
        "audit_durable_flush": False,
        "evidence_store": False,
        "appcontainer_acl": False,
        "runtime_read_execute": False,
        "job_no_breakaway": False,
        "suspended_spawn_audit_before_resume": False,
        "terminal_non_active": False,
        "residual_authority_absent": False,
    }
    if sys.platform != "win32":
        return _unavailable("Windows AppContainer enforcement is required", checks)
    from sentinelx_core.windows_mutation_sandbox import windows_sandbox_primitives_available

    checks["windows"] = True
    if not policy.configured or not policy.scoped_mutation_enabled or policy.workspace_root is None:
        return _unavailable("scoped mutation policy/workspace_root is not enabled", checks)
    checks["policy_enabled"] = True

    primitives, detail = windows_sandbox_primitives_available()
    if not primitives:
        return _unavailable(detail, checks)
    workspace_root = policy.workspace_root.resolve(strict=False)
    if not workspace_root.exists() or not workspace_root.is_dir():
        return _unavailable("provider workspace_root is unavailable", checks)
    for runtime_root in policy.runtime_read_roots:
        if not runtime_root.exists() or not runtime_root.is_dir():
            return _unavailable(f"runtime_read_root is unavailable: {runtime_root}", checks)

    state_root = state_root.resolve(strict=False)
    state_root.mkdir(parents=True, exist_ok=True)
    store = MutationScopeStore(state_root)
    token = secrets.token_hex(10)
    repository = RepositoryIdentity(
        vcs="git", authority="sentinelx.local", path="runtime-readiness-probe"
    )
    semantic = SemanticIdentity(
        project_id="sentinelx-runtime",
        task_id="host-mutation-readiness",
        run_id=f"probe-{token}",
        attempt_id=f"attempt-{token}",
        slice_id="readiness",
    )
    lineage = MutationLineage(
        project_id=semantic.project_id,
        task_id=semantic.task_id,
        run_id=semantic.run_id,
        attempt_id=semantic.attempt_id,
        slice_id=semantic.slice_id,
    )
    protected = (state_root,)
    record = None
    sandbox = None
    terminalized = False
    try:
        record = store.provision_scope(
            policy,
            repository,
            semantic,
            allowed_operation_classes=("workspace_materialize", "scoped_mutation"),
            provider_protected_roots=protected,
        )
        checks["placement_store"] = True
        checks["scope_store"] = True

        audit = MutationAuditJournal(
            state_root, evidence_retention_days=policy.evidence_retention_days
        )
        script_bytes = (
            b"from pathlib import Path\n"
            b"Path('SELF_CHECK_OK').write_text('ok', encoding='utf-8')\n"
        )
        evidence = audit.evidence.retain(script_bytes)
        checks["evidence_store"] = audit.evidence.read_verified(evidence) == script_bytes
        context = RequestContext(
            request_id=f"readiness-{token}",
            op="script_run",
            opaque_ref="runtime-readiness",
            received_at=datetime.now(UTC),
        )
        binding = MutationAuditBinding.from_context(
            context,
            lineage,
            scope_id=record.scope_id,
            scope_generation=record.generation,
            workspace_id=record.workspace_id,
            unique_lease_key=record.unique_lease_key,
        )
        python = Path(sys.executable)
        if python.name.casefold() == "pythonw.exe":
            python = python.with_name("python.exe")
        planned_workspace = Path(record.exact_workspace)
        script_path = planned_workspace / "readiness_probe.py"
        intent = MutationProcessIntent(
            interpreter="python3",
            argv=(str(python), str(script_path)),
            executable_final_path=final_executable_path(python),
            cwd_final_path=str(planned_workspace),
        )
        authority = MutationAuthorityEvidence(
            scope_digest=record.scope_digest,
            exact_workspace_digest=record.exact_workspace_digest,
            protected_inventory_digest=record.protected_inventory_digest,
            policy_digest=record.policy_digest,
            repository_identity_digest=record.repository_identity_digest,
            semantic_identity_digest=record.semantic_identity_digest,
        )
        start = audit.begin(
            binding, evidence, authority=authority, process_intent=intent,
            requested_identity=requested_mutation_identity(record.unique_lease_key),
        )
        checks["audit_durable_flush"] = True

        sandbox = build_mutation_sandbox(
            policy=policy,
            scope_store=store,
            repository=repository,
            semantic=semantic,
            provider_protected_roots=protected,
        )
        activation = sandbox.activate(record, start)
        checks["appcontainer_acl"] = bool(activation.sandbox_identity)
        if activation.workspace != planned_workspace:
            raise RuntimeError("readiness workspace differs from sealed START intent")
        audit.evidence.materialize_verified(evidence, script_path)

        process = sandbox.spawn(
            activation,
            audit=audit,
            audit_start=start,
            argv=[str(python), str(script_path)],
            cwd=activation.workspace,
            env=_probe_environment(activation.workspace),
        )
        checks["job_no_breakaway"] = process.contained and not process.breakaway_allowed
        checks["suspended_spawn_audit_before_resume"] = True
        if not process.wait(20.0):
            process.terminate()
            raise RuntimeError("readiness probe process timed out")
        marker = activation.workspace / "SELF_CHECK_OK"
        if marker.read_text(encoding="utf-8") != "ok":
            raise RuntimeError("sandbox runtime write/read-back self-check failed")
        checks["runtime_read_execute"] = True
        terminal = sandbox.terminalize(record.scope_id, record.generation)
        terminalized = True
        closure = MutationFinishClosureEvidence(
            scope_state=terminal.state,
            scope_digest=terminal.scope_digest,
            protected_inventory_digest=terminal.protected_inventory_digest,
            sandbox_identity=terminal.sandbox_identity,
            job_binding=process.job_ref,
            root_pid=process.pid,
            job_handle_closed=process.job_handle_closed,
            job_active_process_count=process.active_process_count,
            active_job_ids=terminal.active_job_ids,
            active_process_ids=terminal.active_process_ids,
            sandbox_write_authority_present=terminal.sandbox_write_authority_present,
            process_tree_quiescent=not terminal.active_job_ids and not terminal.active_process_ids,
            terminalized_at=terminal.terminalized_at or "",
        )
        audit.finish(start, status="succeeded", closure=closure, returncode=0)
        events = [event.get("event") for event in audit.read_events(start.operation_id)]
        if events != ["OPERATION_STARTED", "PROCESS_SPAWNED", "OPERATION_FINISHED"]:
            raise RuntimeError(f"unexpected readiness audit lifecycle: {events}")

        checks["terminal_non_active"] = terminal.state == "terminal"
        checks["residual_authority_absent"] = (
            not terminal.active_job_ids
            and not terminal.active_process_ids
            and not terminal.sandbox_write_authority_present
        )
        if not all(checks.values()):
            return _unavailable("one or more mutation runtime self-checks failed", checks)
        return MutationRuntimeReadiness(
            True,
            "real Windows AppContainer/ACL/Job/audit/scope self-check passed",
            checks,
        )
    except Exception as exc:  # noqa: BLE001 - readiness must fail closed on any probe defect.
        return _unavailable(f"{type(exc).__name__}: {exc}", checks)
    finally:
        if record is not None and not terminalized:
            try:
                if sandbox is not None:
                    sandbox.terminalize(record.scope_id, record.generation)
                else:
                    store.terminalize_scope(
                        record.scope_id,
                        record.generation,
                        policy,
                        repository,
                        semantic,
                        provider_protected_roots=protected,
                    )
            except Exception as cleanup_exc:  # noqa: BLE001 - cleanup evidence is advisory here.
                logger.warning("mutation readiness cleanup could not prove closure: %s", cleanup_exc)


def probe_mutation_runtime(
    policy: MutationExecutionPolicy,
    state_root: Path,
    *,
    force: bool = False,
) -> MutationRuntimeReadiness:
    """Return cached full runtime readiness; failures never advertise capability."""
    key = _cache_key(policy, state_root)
    with _CACHE_LOCK:
        if not force and key in _CACHE:
            return _CACHE[key]
        result = _probe_once(policy, state_root)
        _CACHE[key] = result
        return result
