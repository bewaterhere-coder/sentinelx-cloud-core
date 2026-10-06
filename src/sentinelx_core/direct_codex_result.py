"""Bounded direct-Codex result and receipt normalization (PR-015/S02, D10/D11).

The bridge never approves Acceptance or completion. It reports what the direct
development host actually did, whether the exact canonical transport still
matches, and whether the work was persisted to the canonical branch. A local
only, unpersisted run is reported as incomplete rather than as success.
"""
from __future__ import annotations

import json
from typing import Any

from sentinelx_core.direct_codex_transport import TransportBootstrap
from sentinelx_core.user_process import UserProcessResult

RECEIPT_VERSION = 1

_REQUIRED_RECEIPT_FIELDS = (
    "execution",
    "workspace",
    "transport",
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
) -> dict[str, Any]:
    """Build the bounded provider result from verified execution evidence."""
    lineage = params["lineage"]
    transport = params["transport"]
    development = params["development"]

    exit_disposition = (
        "timeout" if process.timed_out else ("completed" if process.returncode == 0 else "failed")
    )
    published = local_head != bootstrap.expected_remote_sha
    consistent = actual_branch == bootstrap.branch and remote_head_readback == local_head
    persisted = published and consistent
    structured = _extract_structured(process.stdout)
    receipt_valid = bool(
        exit_disposition == "completed"
        and consistent
        and persisted
        and process.process_tree_closed
        and process.job_contained
    )

    payload: dict[str, Any] = {
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
    if not receipt_valid:
        payload["receipt"]["incomplete_reason"] = (
            "implementation_not_persisted"
            if exit_disposition == "completed" and not persisted
            else f"direct_codex_execution_{exit_disposition}"
        )
    return payload


def validate_receipt(payload: Any, *, task_id: str, slice_id: str | None) -> tuple[bool, ...]:
    """Validate a direct/Codex receipt shape and its exact identity echo."""
    if not isinstance(payload, dict):
        return (False, "receipt_not_object")
    missing = [field for field in _REQUIRED_RECEIPT_FIELDS if field not in payload]
    if missing:
        return (False, f"receipt_missing_fields:{','.join(missing)}")
    execution = payload.get("execution")
    if not isinstance(execution, dict):
        return (False, "receipt_execution_invalid")
    if execution.get("provider") != "direct" or execution.get("adapter") != "codex":
        return (False, "receipt_provider_mismatch")
    if execution.get("task_id") != task_id:
        return (False, "receipt_task_mismatch")
    if (execution.get("slice_id") or None) != (slice_id or None):
        return (False, "receipt_slice_mismatch")
    transport = payload.get("transport")
    if not isinstance(transport, dict) or transport.get("consistent") is not True:
        return (False, "receipt_transport_inconsistent")
    if transport.get("replacement_transport_created") is not False:
        return (False, "receipt_replacement_transport")
    workspace = payload.get("workspace")
    if not isinstance(workspace, dict) or workspace.get("isolated") is not True:
        return (False, "receipt_workspace_not_isolated")
    if workspace.get("canonical_checkout_mutated") is not False:
        return (False, "receipt_canonical_checkout_mutated")
    receipt = payload.get("receipt")
    if not isinstance(receipt, dict) or receipt.get("valid") is not True:
        return (False, "receipt_not_valid")
    return (True, "ok")
