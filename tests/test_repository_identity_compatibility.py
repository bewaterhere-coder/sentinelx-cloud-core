from __future__ import annotations

import sys
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
from sentinelx_core.windows_mutation_sandbox import WindowsMutationSandbox


LEGACY_CANONICAL = "git://github.com/bewaterhere-coder/sentinelx-cloud-core"
# Existing mutation-placement digest for the normal provider repository identity.
# _digest() JSON-encodes strings before SHA-256; pinning the value detects drift.
LEGACY_DIGEST = "4fab8923f2df571ace78e59890aa5e0077470857a5c02c120f5fdad6b645bbd0"


def _policy(tmp_path: Path) -> MutationExecutionPolicy:
    workspace_root = tmp_path / "workspaces"
    protected = tmp_path / "protected"
    workspace_root.mkdir(parents=True, exist_ok=True)
    protected.mkdir(parents=True, exist_ok=True)
    return MutationExecutionPolicy(
        configured=True,
        scoped_mutation_enabled=True,
        workspace_root=workspace_root,
        protected_roots=(protected,),
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


def test_existing_repository_identity_and_placement_digest_remain_stable(tmp_path: Path) -> None:
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


@pytest.mark.skipif(sys.platform != "win32", reason="Windows sandbox identity consumer")
def test_windows_sandbox_revalidates_same_repository_digest(tmp_path: Path) -> None:
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

    sandbox = WindowsMutationSandbox(
        policy=policy,
        scope_store=store,
        repository=repository,
        semantic=semantic,
    )
    current = sandbox._revalidate(record.scope_id, record.generation)
    assert current.repository_identity_digest == LEGACY_DIGEST
    assert current.scope_digest == record.scope_digest
