"""Provider-owned deterministic placement evidence for scoped mutation.

This module does not create directories or mutation authority. It derives and
revalidates the exact future workspace binding that later scope/sandbox slices
will seal and enforce.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit
from typing import Iterable

from sentinelx_core.policy import MutationExecutionPolicy


PLACEMENT_RULES_VERSION = 1
BINDING_MISMATCH_CODE = "HostMutationScopeBindingMismatch"


def _digest(value: object) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _short(value: str) -> str:
    return value[:16]


def _path_text(path: Path) -> str:
    return str(path.resolve(strict=False))


@dataclass(frozen=True)
class RepositoryIdentity:
    vcs: str
    authority: str
    path: str

    @property
    def canonical(self) -> str:
        vcs = self.vcs.strip().lower()
        raw_authority = self.authority.strip().replace("\\", "/")
        path = self.path.strip().replace("\\", "/").strip("/")
        if path.lower().endswith(".git"):
            path = path[:-4]

        if not vcs or not raw_authority or not path:
            raise ValueError("repository identity requires vcs, authority and path")

        parsed = urlsplit(raw_authority if "://" in raw_authority else f"//{raw_authority}")
        hostname = parsed.hostname
        if not hostname:
            raise ValueError("repository identity authority requires a hostname")
        try:
            port = parsed.port
        except ValueError as exc:
            raise ValueError("repository identity authority contains an invalid port") from exc

        host = hostname.lower()
        if ":" in host:
            host = f"[{host}]"
        authority = f"{host}:{port}" if port is not None else host

        path_parts = tuple(part for part in path.split("/") if part)
        if any(part in {".", ".."} for part in path_parts):
            raise ValueError("repository identity path contains traversal segments")
        path = "/".join(path_parts)
        if not path:
            raise ValueError("repository identity requires vcs, authority and path")

        return f"{vcs}://{authority}/{path}"


@dataclass(frozen=True)
class SemanticIdentity:
    project_id: str
    task_id: str
    run_id: str
    attempt_id: str
    slice_id: str | None = None

    @property
    def canonical(self) -> tuple[str, ...]:
        values = (
            self.project_id.strip(),
            self.task_id.strip(),
            self.run_id.strip(),
            self.attempt_id.strip(),
        )
        if not all(values):
            raise ValueError("semantic identity fields must be non-empty")
        return (*values, self.slice_id.strip() if self.slice_id else "")


@dataclass(frozen=True)
class PlacementGenerationState:
    policy_digest: str
    generation: int

    def evolve(self, current_policy_digest: str) -> "PlacementGenerationState":
        if self.policy_digest == current_policy_digest:
            return self
        return PlacementGenerationState(
            policy_digest=current_policy_digest,
            generation=self.generation + 1,
        )


@dataclass(frozen=True)
class PlacementEvidence:
    placement_ref: str
    generation: int
    policy_digest: str
    exact_future_workspace: Path
    exact_workspace_digest: str
    repository_identity_digest: str
    semantic_identity_digest: str
    protected_inventory_digest: str

    @property
    def generation_state(self) -> PlacementGenerationState:
        return PlacementGenerationState(self.policy_digest, self.generation)


class HostMutationScopeBindingMismatch(RuntimeError):
    code = BINDING_MISMATCH_CODE

    def __init__(self, message: str = "provider-owned mutation placement binding changed") -> None:
        super().__init__(message)


def placement_policy_digest(policy: MutationExecutionPolicy) -> str:
    return _digest(
        {
            "rules_version": PLACEMENT_RULES_VERSION,
            "workspace_root": _path_text(policy.workspace_root) if policy.workspace_root else None,
            "protected_roots": sorted(_path_text(p) for p in policy.protected_roots),
            "runtime_read_roots": sorted(_path_text(p) for p in policy.runtime_read_roots),
            "runtime_session_object_read_enabled": policy.runtime_session_object_read_enabled,
            "runtime_acl_timeout_seconds": policy.runtime_acl_timeout_seconds,
        }
    )


def _protected_inventory(
    policy: MutationExecutionPolicy,
    *,
    provider_protected_roots: Iterable[Path] = (),
) -> tuple[str, ...]:
    roots: set[str] = {_path_text(p) for p in policy.protected_roots}
    roots.update(_path_text(p) for p in provider_protected_roots)
    if policy.workspace_root is not None:
        root = policy.workspace_root.resolve(strict=False)
        roots.add(str(root))
        # Parent delete/rename authority can remove the whole workspace root.
        if root.parent != root:
            roots.add(str(root.parent))
    return tuple(sorted(roots))


def resolve_placement(
    policy: MutationExecutionPolicy,
    repository: RepositoryIdentity,
    semantic: SemanticIdentity,
    *,
    generation_state: PlacementGenerationState | None = None,
    provider_protected_roots: Iterable[Path] = (),
) -> PlacementEvidence:
    """Derive a future workspace without accepting caller path authority."""
    if not policy.configured or not policy.scoped_mutation_enabled:
        raise RuntimeError("HostMutationPlacementUnavailable: scoped mutation policy is not enabled")
    if policy.workspace_root is None:
        raise RuntimeError("HostMutationPlacementUnavailable: workspace_root is not configured")

    policy_digest = placement_policy_digest(policy)
    state = (
        PlacementGenerationState(policy_digest, 1)
        if generation_state is None
        else generation_state.evolve(policy_digest)
    )

    repo_digest = _digest(repository.canonical)
    semantic_digest = _digest(semantic.canonical)
    root = policy.workspace_root.resolve(strict=False)
    workspace = (root / _short(repo_digest) / _short(semantic_digest)).resolve(strict=False)
    if workspace == root or not workspace.is_relative_to(root):
        raise HostMutationScopeBindingMismatch("derived workspace escaped provider workspace_root")

    workspace_digest = _digest(_path_text(workspace))
    inventory_digest = _digest(
        _protected_inventory(policy, provider_protected_roots=provider_protected_roots)
    )
    placement_ref = (
        f"mutation-placement:{_short(repo_digest)}:{_short(semantic_digest)}:g{state.generation}"
    )
    return PlacementEvidence(
        placement_ref=placement_ref,
        generation=state.generation,
        policy_digest=policy_digest,
        exact_future_workspace=workspace,
        exact_workspace_digest=workspace_digest,
        repository_identity_digest=repo_digest,
        semantic_identity_digest=semantic_digest,
        protected_inventory_digest=inventory_digest,
    )


def revalidate_placement(
    expected: PlacementEvidence,
    policy: MutationExecutionPolicy,
    repository: RepositoryIdentity,
    semantic: SemanticIdentity,
    *,
    provider_protected_roots: Iterable[Path] = (),
) -> PlacementEvidence:
    """Recompute current provider placement and fail closed on any drift."""
    current = resolve_placement(
        policy,
        repository,
        semantic,
        generation_state=expected.generation_state,
        provider_protected_roots=provider_protected_roots,
    )
    sealed = (
        "placement_ref",
        "generation",
        "policy_digest",
        "exact_future_workspace",
        "exact_workspace_digest",
        "repository_identity_digest",
        "semantic_identity_digest",
        "protected_inventory_digest",
    )
    if any(getattr(current, field) != getattr(expected, field) for field in sealed):
        raise HostMutationScopeBindingMismatch()
    return current


def unique_mutation_lease_key(
    *,
    repository_digest: str,
    semantic: SemanticIdentity,
    placement_generation: int,
    exact_workspace_digest: str,
) -> str:
    """Canonical S02 lease identity for one exact Run/Attempt[/Slice] placement.

    Project/task remain sealed in the scope's semantic digest, while lease
    uniqueness deliberately keys the execution identities required by the
    reviewed contract: repository + run + attempt + optional slice + placement
    generation + exact workspace digest.
    """
    values = semantic.canonical
    run_id = values[2]
    attempt_id = values[3]
    slice_id = values[4]
    if placement_generation <= 0:
        raise ValueError("placement_generation must be positive")
    if not repository_digest or not exact_workspace_digest:
        raise ValueError("lease key requires repository and workspace digests")
    return _digest(
        {
            "repository_identity_digest": repository_digest,
            "run_id": run_id,
            "attempt_id": attempt_id,
            "slice_id": slice_id,
            "placement_generation": placement_generation,
            "exact_workspace_digest": exact_workspace_digest,
        }
    )
