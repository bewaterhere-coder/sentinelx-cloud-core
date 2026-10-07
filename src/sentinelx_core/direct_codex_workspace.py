"""Provider-owned direct-Codex execution workspace derivation (PR-015/S02).

D6 requires the direct-host workspace to be derived from the Host-owned
DevForge execution root plus repository and Task/Run/Attempt/Slice identity.
A caller never supplies a workspace path: ``devforge_direct_codex.execute_task``
has no ``workspace``/``cwd`` field, and this module refuses any derived path
that leaves the configured root or intersects a canonical checkout.
"""
from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from sentinelx_core.mutation_placement import RepositoryIdentity, SemanticIdentity
from sentinelx_core.policy import DirectCodexPolicy

WORKSPACE_RULES_VERSION = 1


class DirectCodexWorkspaceError(RuntimeError):
    """Fail-closed error for direct-Codex workspace derivation."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class DirectCodexWorkspace:
    root: Path
    path: Path
    repository_digest: str
    semantic_digest: str
    workspace_digest: str

    @property
    def relative_name(self) -> str:
        return self.path.name


def _digest(value: object) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _short(value: str) -> str:
    return value[:16]


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(str(path)))


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        common = os.path.commonpath([str(path).casefold(), str(root).casefold()])
    except ValueError:
        return False
    return common == str(root).casefold()


def _paths_overlap(left: Path, right: Path) -> bool:
    return (
        left == right
        or _is_relative_to(left, right)
        or _is_relative_to(right, left)
    )


def derive_workspace(
    policy: DirectCodexPolicy,
    repository: RepositoryIdentity,
    semantic: SemanticIdentity,
) -> DirectCodexWorkspace:
    """Derive the exact future execution workspace from provider-owned inputs."""
    if not policy.configured or not policy.enabled:
        raise DirectCodexWorkspaceError(
            "direct_codex_workspace_unavailable", "direct-codex Host policy is not admitted"
        )
    if policy.workspace_root is None:
        raise DirectCodexWorkspaceError(
            "direct_codex_workspace_root_missing", "direct_codex.workspace_root is not configured"
        )

    root = _absolute(policy.workspace_root)
    repository_digest = _digest(repository.canonical)
    semantic_digest = _digest(semantic.canonical)
    # Two bounded digest segments: identity enters the path, caller text never does.
    path = _absolute(root / _short(repository_digest) / _short(semantic_digest))
    if path == root or not _is_relative_to(path, root):
        raise DirectCodexWorkspaceError(
            "direct_codex_workspace_escape",
            "derived direct-codex workspace escaped the provider workspace root",
        )
    return DirectCodexWorkspace(
        root=root,
        path=path,
        repository_digest=repository_digest,
        semantic_digest=semantic_digest,
        workspace_digest=_digest(str(path)),
    )


def revalidate_workspace(
    expected: DirectCodexWorkspace,
    policy: DirectCodexPolicy,
    repository: RepositoryIdentity,
    semantic: SemanticIdentity,
) -> DirectCodexWorkspace:
    """Recompute the workspace and fail closed on any binding drift."""
    current = derive_workspace(policy, repository, semantic)
    sealed = (
        "root",
        "path",
        "repository_digest",
        "semantic_digest",
        "workspace_digest",
    )
    if any(getattr(current, field) != getattr(expected, field) for field in sealed):
        raise DirectCodexWorkspaceError(
            "direct_codex_workspace_binding_mismatch",
            "direct-codex workspace binding changed between derivation and use",
        )
    return current


def ensure_outside_canonical(
    workspace: DirectCodexWorkspace,
    canonical_roots: Iterable[Path],
) -> tuple[str, ...]:
    """Refuse any workspace that intersects a Host-owned canonical checkout."""
    checked: list[str] = []
    for raw in canonical_roots:
        root = _absolute(Path(str(raw)))
        checked.append(str(root))
        if _paths_overlap(workspace.path, root):
            raise DirectCodexWorkspaceError(
                "direct_codex_workspace_intersects_canonical",
                "derived direct-codex workspace intersects a canonical repository checkout",
            )
    return tuple(sorted(checked))
