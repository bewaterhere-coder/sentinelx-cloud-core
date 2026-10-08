"""Bounded direct-Codex result and receipt normalization (PR-015/S02, D10/D11).

The bridge never approves Acceptance or completion. It reports what the direct
development host actually did, whether the exact canonical transport still
matches, and whether the work was persisted to the canonical branch. A local
only, unpersisted run is reported as incomplete rather than as success.
"""
from __future__ import annotations

import json
from typing import Any

from sentinelx_core.direct_codex_persistence import (
    PERSISTENCE_MODE,
    PersistenceOutcome,
)
from sentinelx_core.direct_codex_transport import TransportBootstrap
from sentinelx_core.mutation_placement import RepositoryIdentity
from sentinelx_core.user_process import UserProcessResult

RECEIPT_VERSION = 2

_REQUIRED_RECEIPT_FIELDS = (
    "execution",
    "workspace",
    "transport",
    "persistence",
    "verification",
    "receipt",
)


def _bounded_summary(text: str, limit: int = 2000) -> str:
    cleaned = text.strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit] + "\n...[truncated]"


def _extract_structured(stdout: str) -> dict[str, Any] | None:
    """Accept structured Codex output when the installed CLI emits it."""
    for line in reversed(stdout.strip().splitlines()):
        candidate = line.strip()
        if not candidate.startswith("{"):
            continue
        try:
            payload = json.loads(candidate)
        except ValueError:
            continue
        if isinstance(payload, dict):
            return payload
    return None


def normalize_result(
    *,
    params: dict[str, Any],
    bootstrap: TransportBootstrap,
    process: UserProcessResult,
    handoff_digest: str,
    actual_branch: str,
    local_head: str,
    remote_head_readback: str,
    persistence: PersistenceOutcome | None,
) -> dict[str, Any]:
    """Build the bounded provider result from verified execution evidence.

    A valid persisted success now additionally requires provider-owned
    persistence evidence (PR-015/S04): the exact candidate commit, an ordinary
    fast-forward publish and a remote readback equal to the candidate. A verified
    no-change outcome is reported distinctly and is not a persisted success.
    """
    lineage = params["lineage"]
    transport = params["transport"]
    development = params["development"]
    repository = RepositoryIdentity(
        vcs=str(params["repository"]["vcs"]),
        authority=str(params["repository"]["authority"]),
        path=str(params["repository"]["path"]),
    )

    exit_disposition = (
        "timeout" if process.timed_out else ("completed" if process.returncode == 0 else "failed")
    )
    consistent = actual_branch == bootstrap.branch and remote_head_readback == local_head
    persistence_block = persistence.to_dict() if persistence is not None else None
    persisted = bool(
        persistence is not None
        and persistence.status == "persisted"
        and persistence.published
        and persistence.consistent
        and remote_head_readback == persistence.candidate_commit
    )
    published = persisted and consistent
    structured = _extract_structured(process.stdout)
    receipt_valid = bool(
        exit_disposition == "completed"
        and consistent
        and persisted
        and process.process_tree_closed
        and process.job_contained
    )

    payload: dict[str, Any] = {
        "repository": repository.canonical,
        "execution": {
            "provider": "direct",
            "adapter": "codex",
            "task_id": lineage["task_id"],
            "run_id": lineage["run_id"],
            "attempt_id": lineage["attempt_id"],
            "slice_id": lineage.get("slice_id"),
            "action": development["action"],
            "exit_disposition": exit_disposition,
            "returncode": process.returncode,
            "process_tree_closed": process.process_tree_closed,
            "job_contained": process.job_contained,
            "execution_context": process.execution_context,
            "handoff_digest": handoff_digest,
        },
        "workspace": {
            "isolated": True,
            "independent_checkout": bootstrap.independent_checkout,
            "canonical_checkout_mutated": bootstrap.canonical_checkout_mutated,
            "git_worktree_add_used": bootstrap.git_worktree_add_used,
            "path": str(bootstrap.workspace),
        },
        "transport": {
            "canonical_pr": transport["pr_number"],
            "canonical_branch": bootstrap.branch,
            "actual_branch": actual_branch,
            "expected_remote_sha": bootstrap.expected_remote_sha,
            "local_head": local_head,
            "remote_head_readback": remote_head_readback,
            "consistent": consistent,
            "published": published,
            "replacement_transport_created": False,
        },
        "verification": {
            "summary": _bounded_summary(process.stdout),
            "stderr": _bounded_summary(process.stderr),
            "structured": structured is not None,
        },
        "receipt": {
            "version": RECEIPT_VERSION,
            "valid": receipt_valid,
            "persisted": persisted,
            "acceptance_claim": False,
            "completion_claim": False,
            "provider_fallback_used": False,
        },
    }
    if persistence_block is not None:
        payload["persistence"] = persistence_block
    if not receipt_valid:
        if exit_disposition != "completed":
            payload["receipt"]["incomplete_reason"] = (
                f"direct_codex_execution_{exit_disposition}"
            )
        elif persistence is not None and persistence.status == "no_change":
            payload["receipt"]["incomplete_reason"] = "no_eligible_change"
        else:
            payload["receipt"]["incomplete_reason"] = "implementation_not_persisted"
    return payload


def validate_receipt(
    payload: Any,
    *,
    task_id: str,
    run_id: str,
    attempt_id: str,
    slice_id: str | None,
    canonical_pr: int,
    canonical_repository: str,
) -> tuple[bool, ...]:
    """Validate a direct/Codex receipt shape and its exact identity echo.

    The receipt must echo the exact Task/Run/Attempt/Slice identity that was
    admitted and the exact canonical repository and PR. A receipt whose
    actual branch differs from the canonical branch is transport drift and
    fails closed even when it claims to be consistent.
    """
    if not isinstance(payload, dict):
        return (False, "receipt_not_object")
    missing = [field for field in _REQUIRED_RECEIPT_FIELDS if field not in payload]
    if missing:
        return (False, f"receipt_missing_fields:{','.join(missing)}")
    if payload.get("repository") != canonical_repository:
        return (False, "receipt_repository_mismatch")
    execution = payload.get("execution")
    if not isinstance(execution, dict):
        return (False, "receipt_execution_invalid")
    if execution.get("provider") != "direct" or execution.get("adapter") != "codex":
        return (False, "receipt_provider_mismatch")
    if execution.get("task_id") != task_id:
        return (False, "receipt_task_mismatch")
    if execution.get("run_id") != run_id:
        return (False, "receipt_run_mismatch")
    if execution.get("attempt_id") != attempt_id:
        return (False, "receipt_attempt_mismatch")
    if (execution.get("slice_id") or None) != (slice_id or None):
        return (False, "receipt_slice_mismatch")
    transport = payload.get("transport")
    if not isinstance(transport, dict) or transport.get("consistent") is not True:
        return (False, "receipt_transport_inconsistent")
    if transport.get("canonical_pr") != canonical_pr:
        return (False, "receipt_pr_mismatch")
    if transport.get("canonical_branch") != transport.get("actual_branch"):
        return (False, "receipt_branch_mismatch")
    if transport.get("replacement_transport_created") is not False:
        return (False, "receipt_replacement_transport")
    persistence = payload.get("persistence")
    if not isinstance(persistence, dict):
        return (False, "receipt_persistence_invalid")
    if persistence.get("mode") != PERSISTENCE_MODE:
        return (False, "receipt_persistence_mode_invalid")
    if persistence.get("status") != "persisted" or persistence.get("published") is not True:
        return (False, "receipt_not_persisted")
    candidate = persistence.get("candidate_commit")
    if not candidate or candidate != transport.get("local_head"):
        return (False, "receipt_candidate_mismatch")
    if transport.get("remote_head_readback") != candidate:
        return (False, "receipt_readback_mismatch")
    if persistence.get("base_head") != transport.get("expected_remote_sha"):
        return (False, "receipt_base_head_mismatch")
    workspace = payload.get("workspace")
    if not isinstance(workspace, dict) or workspace.get("isolated") is not True:
        return (False, "receipt_workspace_not_isolated")
    if workspace.get("canonical_checkout_mutated") is not False:
        return (False, "receipt_canonical_checkout_mutated")
    receipt = payload.get("receipt")
    if not isinstance(receipt, dict) or receipt.get("valid") is not True:
        return (False, "receipt_not_valid")
    return (True, "ok")
