"""PR-014 S02 — provider-owned source role, identity, and capsule (D1-D4)."""
from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path

import pytest

from sentinelx_core import devforge_workspace_source as source
from sentinelx_core.mutation_placement import RepositoryIdentity
from sentinelx_core.policy import LocationSpec, Policy

REPOSITORY = RepositoryIdentity(
    vcs="git",
    authority="github.com",
    path="bewaterhere-coder/sentinelx-cloud-core",
)


def _git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
    )
    return proc.stdout.decode("utf-8", "replace").strip()


def _host_policy(host_root: Path) -> Policy:
    return Policy(
        locations={"devforge_workspace_root": LocationSpec(path=str(host_root))},
    )


def _source_repo(host_root: Path) -> tuple[Path, str]:
    repo = host_root / "repos" / "bewaterhere-coder" / "sentinelx-cloud-core"
    repo.mkdir(parents=True)
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "docs").mkdir()
    (repo / "docs" / "readme.md").write_text("hello\n", encoding="utf-8")
    nested = repo / "src" / "pkg"
    nested.mkdir(parents=True)
    (nested / "mod.py").write_text("VALUE = 1\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "seed")
    _git(
        repo,
        "remote",
        "add",
        "origin",
        "https://github.com/bewaterhere-coder/sentinelx-cloud-core.git",
    )
    return repo, _git(repo, "rev-parse", "HEAD")


@pytest.fixture()
def fake_remote(monkeypatch):
    """Offline ls-remote proof backed by the local object store.

    Network Git is an Acceptance physical concern; unit tests prove the
    identity-verification logic with a locally resolved ref advertisement.
    """

    async def fake_run_user_scoped_git(root, *args, timeout, env=None):
        del timeout, env
        if args[:2] == ("ls-remote", "origin"):
            ref = args[2]
            logical = ref[len("refs/heads/"):]
            sha = _git(root, "rev-parse", logical)
            return 0, f"{sha}\t{ref}\n".encode("utf-8"), b""
        proc = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True
        )
        return proc.returncode, proc.stdout, proc.stderr

    from sentinelx_core import user_git

    monkeypatch.setattr(user_git, "run_user_scoped_git", fake_run_user_scoped_git)


def test_role_is_host_derived_path_free_and_verified(tmp_path, fake_remote) -> None:
    host_root = tmp_path / "host"
    repo, head = _source_repo(host_root)
    policy = _host_policy(host_root)

    role = asyncio.run(source.resolve_canonical_source_role(policy, REPOSITORY))
    assert Path(role.checkout_root) == repo.resolve()
    assert role.branch == "main"
    assert role.head_commit == head
    assert role.clean is True
    assert role.repository == REPOSITORY.canonical


def test_role_fails_closed_when_location_missing(tmp_path) -> None:
    with pytest.raises(source.SourceRoleUnavailable):
        asyncio.run(source.resolve_canonical_source_role(Policy.empty(), REPOSITORY))


def test_role_fails_closed_when_checkout_missing(tmp_path) -> None:
    with pytest.raises(source.SourceRoleUnavailable):
        asyncio.run(source.resolve_canonical_source_role(_host_policy(tmp_path), REPOSITORY))


def test_role_fails_closed_on_dirty_tree(tmp_path, fake_remote) -> None:
    host_root = tmp_path / "host"
    repo, _head = _source_repo(host_root)
    (repo / "docs" / "readme.md").write_text("dirty\n", encoding="utf-8")
    with pytest.raises(source.SourceRoleUnavailable):
        asyncio.run(source.resolve_canonical_source_role(_host_policy(host_root), REPOSITORY))


def test_role_fails_closed_on_non_canonical_branch(tmp_path, fake_remote) -> None:
    host_root = tmp_path / "host"
    repo, _head = _source_repo(host_root)
    _git(repo, "checkout", "-b", "feature")
    with pytest.raises(source.SourceRoleUnavailable):
        asyncio.run(source.resolve_canonical_source_role(_host_policy(host_root), REPOSITORY))


def test_role_fails_closed_on_foreign_origin(tmp_path, fake_remote) -> None:
    host_root = tmp_path / "host"
    repo, _head = _source_repo(host_root)
    _git(repo, "remote", "set-url", "origin", "https://github.com/other/repo.git")
    with pytest.raises(source.SourceRoleUnavailable):
        asyncio.run(source.resolve_canonical_source_role(_host_policy(host_root), REPOSITORY))


def test_source_binding_validation_fails_closed() -> None:
    source.validate_source_binding(
        "refs/heads/task/devforge-execution-workspace-materialization-bridge-v1",
        "a" * 40,
    )
    for ref, commit in (
        ("main", "a" * 40),
        ("refs/heads//main", "a" * 40),
        ("refs/heads/../../x", "a" * 40),
        ("refs/heads/main", "abc123"),
        ("refs/heads/main", "A" * 40),
        ("refs/tags/v1", "a" * 40),
        ("", ""),
    ):
        with pytest.raises(source.SourceIdentityMismatch):
            source.validate_source_binding(ref, commit)


def test_verify_source_identity_binds_remote_and_local(tmp_path, fake_remote) -> None:
    host_root = tmp_path / "host"
    repo, head = _source_repo(host_root)
    role = asyncio.run(source.resolve_canonical_source_role(_host_policy(host_root), REPOSITORY))

    logical, object_format = asyncio.run(source.verify_source_identity(
        role, "refs/heads/main", head
    )
    )
    assert logical == "main"
    assert object_format == "sha1"

    other = ("a" * 39 + "b") if head[-1] != "b" else ("a" * 39 + "c")
    with pytest.raises(source.SourceIdentityMismatch):
        asyncio.run(source.verify_source_identity(role, "refs/heads/main", other))


def test_capsule_is_durable_digest_sealed_and_reused(tmp_path, fake_remote) -> None:
    import asyncio

    host_root = tmp_path / "host"
    state_root = tmp_path / "state"
    state_root.mkdir()
    repo, head = _source_repo(host_root)
    role = asyncio.run(source.resolve_canonical_source_role(_host_policy(host_root), REPOSITORY))

    capsule = asyncio.run(
        source.build_source_capsule(state_root, role, "refs/heads/main", head)
    )
    assert capsule.expected_commit == head
    assert capsule.logical_branch == "main"
    assert capsule.file_count == 2
    assert capsule.total_bytes > 0
    manifest = json.loads((capsule.root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["manifest_digest"] == capsule.manifest_digest
    assert manifest["origin_url"] == REPOSITORY.canonical
    assert {entry["path"] for entry in manifest["entries"]} == {
        "docs/readme.md",
        "src/pkg/mod.py",
    }
    for entry in manifest["entries"]:
        assert entry["mode"] in source.ALLOWED_TREE_MODES
    assert (capsule.root / "objects" / head[:2] / head[2:]).exists()

    reused = asyncio.run(
        source.build_source_capsule(state_root, role, "refs/heads/main", head)
    )
    assert reused.capsule_id == capsule.capsule_id
    assert reused.manifest_digest == capsule.manifest_digest
    assert reused.created_at == capsule.created_at


def test_capsule_rejects_unsupported_tree_entries(tmp_path, fake_remote) -> None:
    for path, is_absolute in (("D:/abs/path", True), ("../escape", False), ("a//b", False)):
        with pytest.raises(source.SourceCapsuleError):
            source._safe_worktree_path(path)
    with pytest.raises(source.SourceCapsuleError):
        source._safe_worktree_path("/abs/path")
    with pytest.raises(source.SourceCapsuleError):
        source._safe_worktree_path("a/../b")


def test_origin_identity_normalization() -> None:
    assert source.normalize_origin_identity(
        "https://github.com/bewaterhere-coder/sentinelx-cloud-core.git"
    ) == ("github.com", "bewaterhere-coder/sentinelx-cloud-core")
    assert source.normalize_origin_identity(
        "git@github.com:bewaterhere-coder/sentinelx-cloud-core.git"
    ) == ("github.com", "bewaterhere-coder/sentinelx-cloud-core")
    with pytest.raises(source.SourceIdentityMismatch):
        source.normalize_origin_identity("https://github.com/only-owner")
