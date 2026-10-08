"""Deterministic direct-Codex handoff compiler (PR-015/S02, D8).

The Codex input is generated from canonical structured fields only. A caller
never supplies a prompt: the ``execute_task`` schema has no ``prompt``,
``instructions`` or ``model`` field, so the instruction text below is the only
thing the development host can receive.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

HANDOFF_VERSION = 1
HANDOFF_RELATIVE_PATH = ".devforge/direct-codex-handoff.md"
MAX_HANDOFF_CHARS = 8000

_TEMPLATE = """# DevForge direct development host handoff (deterministic)

You are executing exactly one DevForge development slice inside an isolated
execution checkout. Work only inside this workspace.

## Identity
- task_id: {task_id}
- run_id: {run_id}
- attempt_id: {attempt_id}
- slice_id: {slice_id}
- development action: {action}

## Canonical artifacts (read them inside this workspace)
- requirement: {requirement_ref}
- plan: {plan_ref}
{findings_line}
## Canonical transport
- type: github-pr
- pr_number: {pr_number}
- branch: {branch}
- expected_remote_sha: {expected_remote_sha}

## Hard boundaries
- complete at most this one slice; do not start the successor slice
- do not create a replacement branch or pull request
- do not migrate or rewrite the canonical transport
- do not change the requirement or the approved plan
- do not grant yourself acceptance, completion or merge authority
- do not widen permissions, write scopes or credentials
- do not use provider fallback; fail closed instead

## Required outcome
- implement only the authorized scope of {slice_id}
- keep every change inside the exact branch above
- finish with a bounded summary of changed files and verification commands
"""


@dataclass(frozen=True)
class DirectCodexHandoff:
    version: int
    text: str
    digest: str
    relative_path: str


def compile_handoff(
    *,
    task_id: str,
    run_id: str,
    attempt_id: str,
    slice_id: str | None,
    action: str,
    requirement_ref: str,
    plan_ref: str,
    findings_ref: str | None,
    pr_number: int,
    branch: str,
    expected_remote_sha: str,
) -> DirectCodexHandoff:
    """Compile the bounded instruction text from canonical structured fields."""
    findings_line = (
        f"- acceptance findings: {findings_ref}\n" if findings_ref else ""
    )
    text = _TEMPLATE.format(
        task_id=task_id,
        run_id=run_id,
        attempt_id=attempt_id,
        slice_id=slice_id or "",
        action=action,
        requirement_ref=requirement_ref,
        plan_ref=plan_ref,
        findings_line=findings_line,
        pr_number=pr_number,
        branch=branch,
        expected_remote_sha=expected_remote_sha,
    )
    if len(text) > MAX_HANDOFF_CHARS:
        text = text[:MAX_HANDOFF_CHARS]
    return DirectCodexHandoff(
        version=HANDOFF_VERSION,
        text=text,
        digest=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        relative_path=HANDOFF_RELATIVE_PATH,
    )


def write_handoff(workspace: Path, handoff: DirectCodexHandoff) -> Path:
    """Persist the handoff inside the execution workspace for audit."""
    target = Path(workspace) / handoff.relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(handoff.text, encoding="utf-8")
    return target
