"""Fixed canonical transport bootstrap for the direct-Codex host (PR-015/S02).

D7 requires the direct host to obtain the *existing* canonical PR branch before
invoking Codex, with a CAS-style remote head admission and an independent
execution checkout. This module never accepts caller Git argv, never overrides
a remote URL, never creates a replacement branch or PR, and never runs
``git worktree add`` against a canonical checkout (that would mutate canonical
``.git/worktrees`` metadata).
"""
from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from sentinelx_core.direct_codex_workspace import (
    DirectCodexWorkspace,
    DirectCodexWorkspaceError,
    ensure_outside_canonical,
)
from sentinelx_core.mutation_placement import RepositoryIdentity, SemanticIdentity
from sentinelx_core.policy import DirectCodexPolicy
from sentinelx_core.user_git import (
    UserScopedGitError,
    classify_result,
    run_user_scoped_git,
)

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


async def transport_git(root: Path, *args: str, timeout: float) -> tuple[int, bytes, bytes]:
    """Run fixed Git argv, converting an unavailable user context into a
    fail-closed direct-Codex transport error. There is no shell fallback."""
    try:
        return await run_user_scoped_git(root, *args, timeout=timeout)
    except UserScopedGitError as exc:
        raise DirectCodexTransportError(
            "direct_codex_git_context_unavailable", str(exc)
        ) from exc


class DirectCodexTransportError(RuntimeError):
    """Fail-closed error for direct-Codex transport bootstrap."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class TransportBootstrap:
    workspace: Path
    repository: str
    remote_url: str
    branch: str
    expected_remote_sha: str
    remote_head: str
    local_head: str
    actual_branch: str
    canonical_roots: tuple[str, ...]
    canonical_checkout_mutated: bool
    git_worktree_add_used: bool
    independent_checkout: bool
    created_checkout: bool


def remote_url_for(repository: RepositoryIdentity) -> str:
    """Provider-derived canonical remote URL. Caller data never supplies it."""
    return f"https://{repository.canonical.split('://', 1)[1]}.git"


def _parse_remote_head(stdout: bytes, branch: str) -> str | None:
    for line in stdout.decode("utf-8", errors="replace").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1] in (f"refs/heads/{branch}", branch):
            candidate = parts[0].strip()
            if _SHA_RE.match(candidate):
                return candidate
    return None


async def read_remote_head(
    *,
    cwd: Path,
    repository: RepositoryIdentity,
    branch: str,
    timeout: float,
) -> str:
    code, stdout, stderr = await transport_git(
        cwd, "ls-remote", "--heads", remote_url_for(repository), branch, timeout=timeout
    )
    if code != 0:
        reason = classify_result(code, stderr) or "GitRemoteFailed"
        raise DirectCodexTransportError(
            "direct_codex_remote_read_failed",
            f"cannot read the canonical remote branch head: {reason}",
        )
    head = _parse_remote_head(stdout, branch)
    if head is None:
        raise DirectCodexTransportError(
            "direct_codex_remote_branch_missing",
            f"canonical remote branch is not present: {branch}",
        )
    return head


async def _canonical_heads(roots: Iterable[Path], timeout: float) -> dict[str, str]:
    heads: dict[str, str] = {}
    for root in roots:
        path = Path(root)
        if not (path / ".git").exists():
            continue
        code, stdout, _stderr = await transport_git(
            path, "rev-parse", "HEAD", timeout=timeout
        )
        if code == 0:
            heads[str(path)] = stdout.decode("utf-8", errors="replace").strip()
    return heads


async def bootstrap_execution_checkout(
    *,
    policy: DirectCodexPolicy,
    workspace: DirectCodexWorkspace,
    repository: RepositoryIdentity,
    semantic: SemanticIdentity,
    branch: str,
    expected_remote_sha: str,
    canonical_roots: Iterable[Path] = (),
    timeout: float | None = None,
) -> TransportBootstrap:
    """Create or refresh the independent execution checkout at the exact head."""
    if not _SHA_RE.match(expected_remote_sha):
        raise DirectCodexTransportError(
            "direct_codex_transport_invalid", "expected_remote_sha must be a 40-hex object id"
        )
    if not branch.strip() or branch.strip() != branch:
        raise DirectCodexTransportError(
            "direct_codex_transport_invalid", "branch must be an exact non-padded branch name"
        )

    checked_roots = ensure_outside_canonical(workspace, canonical_roots)
    budget = float(timeout if timeout is not None else policy.timeout_seconds)
    remote_url = remote_url_for(repository)
    parent = workspace.path.parent
    parent.mkdir(parents=True, exist_ok=True)

    before_heads = await _canonical_heads(canonical_roots, budget)

    remote_head = await read_remote_head(
        cwd=parent, repository=repository, branch=branch, timeout=budget
    )
    if remote_head != expected_remote_sha:
        raise DirectCodexTransportError(
            "direct_codex_remote_head_mismatch",
            "canonical remote branch head does not match expected_remote_sha; "
            "no direct-Codex mutation is permitted",
        )

    created = False
    if not (workspace.path / ".git").exists():
        # The direct-Codex containment proof derives and empties this exact
        # directory before the transport bootstrap, so an existing but empty
        # derived workspace is still a valid independent-checkout target.
        if workspace.path.exists() and any(workspace.path.iterdir()):
            raise DirectCodexTransportError(
                "direct_codex_workspace_occupied",
                "the derived execution workspace exists but is not an independent checkout",
            )
        code, _out, stderr = await transport_git(
            parent,
            "clone",
            "--no-checkout",
            "--branch",
            branch,
            remote_url,
            workspace.path.name,
            timeout=budget,
        )
        if code != 0:
            reason = classify_result(code, stderr) or "GitRemoteFailed"
            raise DirectCodexTransportError(
                "direct_codex_clone_failed", f"cannot create the independent checkout: {reason}"
            )
        created = True
    else:
        code, _out, stderr = await transport_git(
            workspace.path, "fetch", "--no-tags", "--force", "origin", branch, timeout=budget
        )
        if code != 0:
            reason = classify_result(code, stderr) or "GitRemoteFailed"
            raise DirectCodexTransportError(
                "direct_codex_fetch_failed", f"cannot refresh the independent checkout: {reason}"
            )

    code, _out, stderr = await transport_git(
        workspace.path, "checkout", "--force", "-B", branch, expected_remote_sha, timeout=budget
    )
    if code != 0:
        reason = classify_result(code, stderr) or "GitTransportFailed"
        raise DirectCodexTransportError(
            "direct_codex_checkout_failed", f"cannot check out the canonical branch: {reason}"
        )

    code, stdout, stderr = await transport_git(
        workspace.path, "rev-parse", "HEAD", timeout=budget
    )
    if code != 0:
        raise DirectCodexTransportError(
            "direct_codex_head_read_failed", "cannot read the execution checkout head"
        )
    local_head = stdout.decode("utf-8", errors="replace").strip()
    if local_head != expected_remote_sha:
        raise DirectCodexTransportError(
            "direct_codex_local_head_mismatch",
            "execution checkout head does not match the admitted canonical head",
        )

    code, stdout, _stderr = await transport_git(
        workspace.path, "rev-parse", "--abbrev-ref", "HEAD", timeout=budget
    )
    actual_branch = stdout.decode("utf-8", errors="replace").strip()

    after_heads = await _canonical_heads(canonical_roots, budget)
    canonical_mutated = before_heads != after_heads

    return TransportBootstrap(
        workspace=workspace.path,
        repository=repository.canonical,
        remote_url=remote_url,
        branch=branch,
        expected_remote_sha=expected_remote_sha,
        remote_head=remote_head,
        local_head=local_head,
        actual_branch=actual_branch,
        canonical_roots=checked_roots,
        canonical_checkout_mutated=canonical_mutated,
        git_worktree_add_used=False,
        independent_checkout=True,
        created_checkout=created,
    )


def workspace_error_code(exc: DirectCodexWorkspaceError) -> str:
    return exc.code
