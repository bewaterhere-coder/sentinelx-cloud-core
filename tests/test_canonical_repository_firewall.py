from __future__ import annotations

from pathlib import Path

import pytest

from sentinelx_core.canonical_repository_firewall import (
    CanonicalRepositoryFirewall,
    CanonicalRepositoryFirewallDisposition,
)
from sentinelx_core.policy import Policy


BLOCKED = CanonicalRepositoryFirewallDisposition.CANONICAL_REPOSITORY_MUTATION_BLOCKED
ALLOWED = CanonicalRepositoryFirewallDisposition.ALLOWED_NON_CANONICAL_TARGET
INDETERMINATE = (
    CanonicalRepositoryFirewallDisposition.HOST_CANONICAL_MUTATION_FIREWALL_INDETERMINATE
)


def _repo_entry(root: Path, *, path: str = "owner/repo.git") -> dict[str, object]:
    return {
        "root": str(root),
        "repository": {
            "vcs": "git",
            "authority": "https://token@github.com:443",
            "path": path,
        },
        "canonical_branch": "main",
    }


def _policy(
    canonical_root: Path,
    *,
    workspace_root: Path | None = None,
    file_ops_root: Path | None = None,
) -> Policy:
    mutation_execution: dict[str, object] = {
        "canonical_repository_firewall_enabled": True,
        "canonical_repositories": [_repo_entry(canonical_root)],
    }
    if workspace_root is not None:
        mutation_execution["workspace_root"] = str(workspace_root)
    data: dict[str, object] = {"mutation_execution": mutation_execution}
    if file_ops_root is not None:
        data["file_ops"] = {
            "paths": [{"path": str(file_ops_root), "access": "rw"}]
        }
    return Policy.from_dict(data)


def test_inventory_is_host_owned_and_repository_identity_drops_credentials(
    tmp_path: Path,
) -> None:
    canonical = tmp_path / "repos" / "owner" / "repo"
    policy = _policy(canonical)

    mutation = policy.mutation_execution
    assert mutation.canonical_repository_inventory_ready is True
    assert mutation.canonical_repository_inventory_valid is True
    assert len(mutation.canonical_repositories) == 1
    spec = mutation.canonical_repositories[0]
    assert spec.root == canonical.resolve(strict=False)
    assert spec.repository_identity == "git://github.com/owner/repo"
    assert spec.canonical_branch == "main"
    assert spec.provenance == "operator_config"


def test_exact_root_and_descendant_are_blocked(tmp_path: Path) -> None:
    canonical = tmp_path / "canonical"
    firewall = CanonicalRepositoryFirewall(_policy(canonical).mutation_execution)

    assert firewall.classify_write_target(canonical).disposition is BLOCKED
    decision = firewall.classify_write_target(canonical / "src" / "file.py")
    assert decision.disposition is BLOCKED
    assert decision.repository_identity == "git://github.com/owner/repo"


def test_parent_mutation_intersecting_checkout_is_blocked(tmp_path: Path) -> None:
    canonical = tmp_path / "repos" / "repo"
    firewall = CanonicalRepositoryFirewall(_policy(canonical).mutation_execution)

    assert firewall.classify_write_target(canonical.parent).disposition is BLOCKED


def test_traversal_is_canonicalized_before_classification(tmp_path: Path) -> None:
    canonical = tmp_path / "canonical"
    outside = tmp_path / "workspace"
    firewall = CanonicalRepositoryFirewall(_policy(canonical).mutation_execution)

    target = outside / ".." / "canonical" / "tracked.txt"
    assert firewall.classify_write_target(target).disposition is BLOCKED


def test_symlink_into_canonical_checkout_is_blocked(tmp_path: Path) -> None:
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    tracked = canonical / "tracked.txt"
    tracked.write_text("tracked")
    link = tmp_path / "link-to-tracked"
    try:
        link.symlink_to(tracked)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable on this platform")

    firewall = CanonicalRepositoryFirewall(_policy(canonical).mutation_execution)
    assert firewall.classify_write_target(link).disposition is BLOCKED


def test_broad_parent_file_ops_rw_never_overrides_canonical_role(
    tmp_path: Path,
) -> None:
    canonical = tmp_path / "repos" / "repo"
    policy = _policy(canonical, file_ops_root=tmp_path)
    target = canonical / "README.md"

    assert policy.resolve_path(str(target), need_write=True) == target.resolve(strict=False)
    firewall = CanonicalRepositoryFirewall(policy.mutation_execution)
    assert firewall.classify_write_target(target).disposition is BLOCKED


def test_same_repository_execution_workspace_remains_noncanonical(
    tmp_path: Path,
) -> None:
    canonical = tmp_path / "source" / "repo"
    workspace = tmp_path / "workspaces" / "repo" / "attempt-1"
    policy = _policy(canonical, workspace_root=tmp_path / "workspaces")
    firewall = CanonicalRepositoryFirewall(policy.mutation_execution)

    decision = firewall.classify_write_target(workspace / "src" / "file.py")
    assert decision.disposition is ALLOWED


def test_duplicate_inventory_root_makes_readiness_false(tmp_path: Path) -> None:
    canonical = tmp_path / "canonical"
    policy = Policy.from_dict(
        {
            "mutation_execution": {
                "canonical_repository_firewall_enabled": True,
                "canonical_repositories": [
                    _repo_entry(canonical),
                    _repo_entry(canonical, path="owner/other-repo"),
                ],
            }
        }
    )

    mutation = policy.mutation_execution
    assert mutation.canonical_repository_inventory_valid is False
    assert "canonical_repository_duplicate_root" in mutation.canonical_repository_inventory_diagnostics
    firewall = CanonicalRepositoryFirewall(mutation)
    assert firewall.classify_write_target(canonical / "x").disposition is INDETERMINATE


def test_overlapping_inventory_roots_fail_closed(tmp_path: Path) -> None:
    parent = tmp_path / "repos"
    child = parent / "repo"
    policy = Policy.from_dict(
        {
            "mutation_execution": {
                "canonical_repository_firewall_enabled": True,
                "canonical_repositories": [
                    _repo_entry(parent, path="owner/repos"),
                    _repo_entry(child),
                ],
            }
        }
    )

    mutation = policy.mutation_execution
    assert mutation.canonical_repository_inventory_valid is False
    assert "canonical_repository_roots_overlap" in mutation.canonical_repository_inventory_diagnostics


def test_inventory_overlapping_execution_workspace_fails_closed(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspaces"
    canonical = workspace_root / "repo"
    policy = _policy(canonical, workspace_root=workspace_root)

    mutation = policy.mutation_execution
    assert mutation.canonical_repository_inventory_valid is False
    assert (
        "canonical_repository_overlaps_workspace_root"
        in mutation.canonical_repository_inventory_diagnostics
    )


def test_disabled_or_empty_inventory_is_indeterminate(tmp_path: Path) -> None:
    disabled = Policy.from_dict(
        {
            "mutation_execution": {
                "canonical_repository_firewall_enabled": False,
                "canonical_repositories": [_repo_entry(tmp_path / "canonical")],
            }
        }
    )
    disabled_firewall = CanonicalRepositoryFirewall(disabled.mutation_execution)
    assert disabled_firewall.readiness.ready is False
    assert disabled_firewall.classify_write_target(tmp_path / "x").disposition is INDETERMINATE

    empty = Policy.from_dict(
        {"mutation_execution": {"canonical_repository_firewall_enabled": True}}
    )
    empty_firewall = CanonicalRepositoryFirewall(empty.mutation_execution)
    assert empty_firewall.readiness.ready is False
    assert empty_firewall.classify_write_target(tmp_path / "x").disposition is INDETERMINATE


def test_relative_target_is_indeterminate(tmp_path: Path) -> None:
    firewall = CanonicalRepositoryFirewall(
        _policy(tmp_path / "canonical").mutation_execution
    )
    decision = firewall.classify_write_target(Path("relative/path"))
    assert decision.disposition is INDETERMINATE
    assert decision.reason == "target_not_absolute"


def test_caller_cannot_supply_inventory_override(tmp_path: Path) -> None:
    firewall = CanonicalRepositoryFirewall(
        _policy(tmp_path / "canonical").mutation_execution
    )
    with pytest.raises(TypeError):
        firewall.classify_write_target(  # type: ignore[call-arg]
            tmp_path / "other",
            canonical_repositories=(),
        )
