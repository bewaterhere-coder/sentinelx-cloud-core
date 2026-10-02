from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from sentinelx_core.handlers.scoped_script import _authority
from sentinelx_core.mutation_placement import (
    RepositoryIdentity,
    SemanticIdentity,
    resolve_placement,
)
from sentinelx_core.mutation_scope import MutationScopeStore
from sentinelx_core.policy import MutationExecutionPolicy
from sentinelx_core import windows_mutation_sandbox


LEGACY_CANONICAL = "git://github.com/bewaterhere-coder/sentinelx-cloud-core"
LEGACY_DIGEST = hashlib.sha256(LEGACY_CANONICAL.encode("utf-8")).hexdigest()


def _policy(tmp_path: Path) -> MutationExecutionPolicy:
    return MutationExecutionPolicy(
        configured=True,
        scoped_mutation_enabled=True,
        workspace_root=tmp_path / "workspaces",
        protected_roots=(tmp_path / "protected",),
    )


def _repository() -> RepositoryIdentity:
    return RepositoryIdentity(
        vcs="git",
        authority="github.com",
        path="bewaterhere-coder/sentinelx-cloud-core",
    )


def _semantic() -> SemanticIdentity:
    return SemanticIdentity(
        project_id="sentinelx-cloud-core",
        task_id="PR-010-canonical-repository-mutation-firewall-v1",
        run_id="compatibility",
        attempt_id="1",
        slice_id="S01",
    )


def test_legacy_repository_identity_and_digest_remain_stable(tmp_path: Path) -> None:
    repository = _repository()
    assert repository.canonical == LEGACY_CANONICAL

    placement = resolve_placement(_policy(tmp_path), repository, _semantic())
    assert placement.repository_identity_digest == LEGACY_DIGEST


def test_scope_binding_revalidates_without_repository_digest_drift(tmp_path: Path) -> None:
    policy = _policy(tmp_path)
    repository = _repository()
    semantic = _semantic()
    store = MutationScopeStore(tmp_path / "provider-state")

    record = store.provision_scope(
        policy,
        repository,
        semantic,
        allowed_operation_classes=("scoped_mutation",),
    )
    original_scope_digest = record.scope_digest

    assert record.repository_identity_digest == LEGACY_DIGEST
    current = store.revalidate_scope(
        record.scope_id,
        record.generation,
        policy,
        repository,
        semantic,
    )
    assert current.repository_identity_digest == LEGACY_DIGEST
    assert current.scope_digest == original_scope_digest


def test_scoped_script_authority_uses_same_repository_identity_semantic() -> None:
    payload = {
        "mutation": {
            "scope_ref": {"scope_id": "scope-compatibility", "generation": 1},
        },
        "lineage": {
            "project_id": "sentinelx-cloud-core",
            "task_id": "PR-010-canonical-repository-mutation-firewall-v1",
            "run_id": "compatibility",
            "attempt_id": "1",
            "slice_id": "S01",
        },
        "repository": {
            "vcs": "git",
            "authority": "github.com",
            "path": "bewaterhere-coder/sentinelx-cloud-core",
        },
    }

    _scope_id, _generation, _lineage, repository, semantic = _authority(payload)
    assert repository.canonical == LEGACY_CANONICAL
    assert semantic.canonical == _semantic().canonical


def test_repository_identity_strips_credentials_preserves_port_and_normalizes_git_suffix() -> None:
    repository = RepositoryIdentity(
        vcs="GIT",
        authority="https://user:secret@GitHub.com:443/ignored",
        path="owner/repo.GIT",
    )
    assert repository.canonical == "git://github.com:443/owner/repo"


@pytest.mark.parametrize(
    ("authority", "path"),
    [
        ("github.com:not-a-port", "owner/repo"),
        ("github.com", "owner/../repo"),
        ("github.com", "owner/./repo"),
    ],
)
def test_repository_identity_invalid_port_or_traversal_fails_closed(
    authority: str, path: str
) -> None:
    with pytest.raises(ValueError):
        _ = RepositoryIdentity(vcs="git", authority=authority, path=path).canonical


def test_windows_sandbox_consumes_the_shared_repository_identity_class() -> None:
    assert windows_mutation_sandbox.RepositoryIdentity is RepositoryIdentity
