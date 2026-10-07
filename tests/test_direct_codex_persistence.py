"""PR-015/S04: provider-owned deterministic persistence & canonical publish.

Focused coverage for the pre-checkout canonicalization authority, the
provider-owned candidate index/commit, the recovery journal and the ordinary
fast-forward publication with independent remote readback. Everything runs
against real local Git fixtures through the fixed provider Git argv; the
Windows active-user runner is substituted exactly as the S02/S03 harness does.
"""
from __future__ import annotations

import asyncio
import os
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import Any, ClassVar

import pytest

from sentinelx_core import direct_codex_persistence as persistence_module
from sentinelx_core import direct_codex_transport as transport_module
from sentinelx_core.direct_codex_persistence import (
    PERSISTENCE_MODE,
    STATE_CANDIDATE_READY,
    STATE_PREPARED,
    STATE_PUBLISH_INTENT,
    STATE_PUBLISHED,
    STATE_TREE_READY,
    DirectCodexPersistenceError,
    persist_implementation,
)
from sentinelx_core.direct_codex_transport import (
    DirectCodexCanonicalizationError,
    bootstrap_execution_checkout,
    capture_canonicalization_snapshot,
    ensure_provider_state,
    materialization_clamps,
    materialization_env,
    provider_state,
    read_persisted_snapshot,
    validate_relative_path,
)
from sentinelx_core.direct_codex_workspace import derive_workspace
from sentinelx_core.mutation_placement import RepositoryIdentity, SemanticIdentity
from sentinelx_core.policy import DirectCodexPolicy

_GIT = "git"
BRANCH = "task/bridge"
_DEFAULT_GITATTRIBUTES = "*.txt text eol=crlf\n*.bin -text\n"
_DEFAULT_FILES: dict[str, bytes] = {
    "README.md": b"# header\n",
    "note.txt": b"hello\n",
    "data.bin": b"\x00\x01binary\r\n\x02",
}


# ── fixtures / helpers ────────────────────────────────────────────────────


def _git_run(
    root: Path | None,
    args: tuple[str, ...],
    *,
    env: dict[str, str] | None = None,
    stdin: bytes | None = None,
) -> tuple[int, bytes, bytes]:
    full = dict(os.environ)
    if env:
        full.update(env)
    proc = subprocess.run(
        [_GIT, *args],
        cwd=str(root) if root else None,
        capture_output=True,
        env=full,
        input=stdin,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _git_ok(
    root: Path | None,
    *args: str,
    env: dict[str, str] | None = None,
    stdin: bytes | None = None,
) -> bytes:
    code, out, err = _git_run(root, args, env=env, stdin=stdin)
    assert code == 0, f"git {' '.join(args)} failed: {err.decode(errors='replace')}"
    return out


async def _fake_git(
    root: Path, *args: str, timeout: float, env: dict[str, str] | None = None
) -> tuple[int, bytes, bytes]:
    return await asyncio.to_thread(_git_run, Path(root), tuple(args), env=env)


def _repository() -> RepositoryIdentity:
    return RepositoryIdentity(
        vcs="git", authority="github.com", path="bewaterhere-coder/sentinelx-cloud-core"
    )


def _semantic(attempt: str = "attempt-1", slice_id: str = "S04") -> SemanticIdentity:
    return SemanticIdentity(
        project_id="sentinelx-cloud-core",
        task_id="PR-015-direct-codex-development-host-invocation-bridge-v1",
        run_id="run-1",
        attempt_id=attempt,
        slice_id=slice_id,
    )


def _build_remote(
    tmp_path: Path,
    files: dict[str, bytes],
    *,
    gitattributes: str | None = _DEFAULT_GITATTRIBUTES,
) -> tuple[Path, str]:
    source = tmp_path / "source"
    source.mkdir()
    _git_ok(source, "init", "-q", ".")
    _git_ok(source, "checkout", "-q", "-b", BRANCH)
    _git_ok(source, "config", "user.email", "t@example.com")
    _git_ok(source, "config", "user.name", "test")
    if gitattributes is not None:
        (source / ".gitattributes").write_text(gitattributes, encoding="ascii")
    for name, body in files.items():
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
    _git_ok(source, "add", "-A")
    _git_ok(source, "commit", "-q", "-m", "base")
    head = _git_ok(source, "rev-parse", "HEAD").decode().strip()
    bare = tmp_path / "remote.git"
    _git_ok(None, "clone", "-q", "--bare", "--no-hardlinks", str(source), str(bare))
    return bare, head


def _policy(tmp_path: Path, **overrides: Any) -> DirectCodexPolicy:
    root = tmp_path / "devforge-workspaces"
    root.mkdir(parents=True, exist_ok=True)
    policy = DirectCodexPolicy(
        configured=True,
        enabled=True,
        workspace_root=root,
        supported_platform="windows",
        timeout_seconds=120,
        max_result_bytes=8192,
    )
    return replace(policy, **overrides) if overrides else policy


async def _bootstrap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    files: dict[str, bytes] | None = None,
    gitattributes: str | None = _DEFAULT_GITATTRIBUTES,
    canonical_roots: tuple[Path, ...] = (),
    attempt: str = "attempt-1",
) -> tuple[Any, Path, str, DirectCodexPolicy, Any]:
    monkeypatch.setattr(transport_module, "run_user_scoped_git", _fake_git)
    bare, head = _build_remote(
        tmp_path, files or dict(_DEFAULT_FILES), gitattributes=gitattributes
    )
    monkeypatch.setattr(transport_module, "remote_url_for", lambda _r: str(bare))
    policy = _policy(tmp_path)
    workspace = derive_workspace(policy, _repository(), _semantic(attempt))
    bootstrap = await bootstrap_execution_checkout(
        policy=policy,
        workspace=workspace,
        repository=_repository(),
        semantic=_semantic(attempt),
        branch=BRANCH,
        expected_remote_sha=head,
        canonical_roots=canonical_roots,
    )
    return bootstrap, bare, head, policy, workspace


async def _persist(
    bootstrap: Any,
    workspace: Any,
    head: str,
    *,
    attempt: str = "attempt-1",
    clock: Any = None,
) -> Any:
    return await persist_implementation(
        workspace=workspace,
        bootstrap=bootstrap,
        repository=_repository(),
        semantic=_semantic(attempt),
        canonical_pr=15,
        branch=BRANCH,
        expected_remote_sha=head,
        timeout=120.0,
        clock=clock,
    )


def _blob(ws: Path, revision: str) -> bytes:
    return _git_ok(ws, "cat-file", "blob", revision)


def _tree_paths(ws: Path, revision: str) -> list[str]:
    return _git_ok(ws, "ls-tree", "-r", "--name-only", revision).decode().split()


def _changed_paths(ws: Path, old: str, new: str) -> set[str]:
    out = _git_ok(ws, "diff-tree", "-r", "--name-only", "--no-renames", old, new).decode()
    return {line for line in out.split() if line}


def _remote_rev(bare: Path, ref: str) -> str:
    return _git_ok(bare, "rev-parse", ref).decode().strip()


def _remote_commit_count(bare: Path, ref: str) -> int:
    return int(_git_ok(bare, "rev-list", "--count", ref).decode().strip())


# ── pre-checkout canonicalization authority (D12.1 Phase A/B/C) ───────────


@pytest.mark.asyncio
async def test_snapshot_is_bound_and_read_back_before_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bootstrap, _bare, head, _policy_obj, workspace = await _bootstrap(tmp_path, monkeypatch)

    snapshot = bootstrap.snapshot
    assert snapshot is not None
    assert bootstrap.snapshot_reused is False
    assert snapshot.expected_remote_sha == head
    assert set(snapshot.scalars) == {
        "core.autocrlf",
        "core.eol",
        "core.safecrlf",
        "core.checkroundtripencoding",
    }
    assert snapshot.info_attributes_empty is True
    assert snapshot.inspection_index_digest
    assert (bootstrap.workspace / "README.md").is_file()

    state = provider_state(workspace)
    persisted = read_persisted_snapshot(state)
    assert persisted == snapshot
    assert state.directory.is_dir()
    assert not str(state.directory).startswith(str(bootstrap.workspace))
    assert state.inspection_index.is_file()


@pytest.mark.asyncio
async def test_snapshot_is_reused_for_the_same_attempt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first, _bare, head, policy, workspace = await _bootstrap(tmp_path, monkeypatch)
    monkeypatch.setattr(transport_module, "run_user_scoped_git", _fake_git)

    second = await bootstrap_execution_checkout(
        policy=policy,
        workspace=workspace,
        repository=_repository(),
        semantic=_semantic(),
        branch=BRANCH,
        expected_remote_sha=head,
    )
    assert second.snapshot_reused is True
    assert second.snapshot == first.snapshot


@pytest.mark.asyncio
async def test_custom_filter_on_tracked_path_is_rejected_before_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A marker filter must never run: rejection happens before materialization."""
    marker = tmp_path / "filter-marker.txt"
    global_cfg = tmp_path / "global-config"
    global_cfg.write_text(
        f'[filter "marker"]\n\tclean = cmd /c echo ran > "{marker.as_posix()}"\n'
        "\trequired = true\n",
        encoding="ascii",
    )
    monkeypatch.setattr(transport_module, "run_user_scoped_git", _fake_git)
    bare, head = _build_remote(
        tmp_path,
        {"a.dat": b"payload\n", "README.md": b"# h\n"},
        gitattributes="*.dat filter=marker\n",
    )
    # Activate the marker driver only AFTER the fixture repository exists, so the
    # marker can only ever be produced by the provider path under test.
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(global_cfg))
    monkeypatch.setattr(transport_module, "remote_url_for", lambda _r: str(bare))
    policy = _policy(tmp_path)
    workspace = derive_workspace(policy, _repository(), _semantic())

    with pytest.raises(DirectCodexCanonicalizationError) as exc:
        await bootstrap_execution_checkout(
            policy=policy,
            workspace=workspace,
            repository=_repository(),
            semantic=_semantic(),
            branch=BRANCH,
            expected_remote_sha=head,
        )
    assert exc.value.code == "direct_codex_unsupported_filter_attribute"
    assert not marker.exists()
    # No worktree was materialized: the rejection precedes checkout.
    assert not (workspace.path / "a.dat").exists()
    assert not (workspace.path / "README.md").exists()


@pytest.mark.asyncio
async def test_global_attributes_are_neutralized_for_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A globally assigned filter must not execute during materialization."""
    marker = tmp_path / "global-filter-marker.txt"
    attrs = tmp_path / "global-attributes"
    attrs.write_text("*.txt filter=marker\n", encoding="ascii")
    global_cfg = tmp_path / "global-config"
    global_cfg.write_text(
        f'[core]\n\tattributesFile = "{attrs.as_posix()}"\n'
        f'[filter "marker"]\n\tclean = cmd /c echo ran > "{marker.as_posix()}"\n',
        encoding="ascii",
    )
    monkeypatch.setattr(transport_module, "run_user_scoped_git", _fake_git)
    bare, head = _build_remote(tmp_path, dict(_DEFAULT_FILES))
    # Activate the global attributes/driver only after the fixture exists.
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(global_cfg))
    monkeypatch.setattr(transport_module, "remote_url_for", lambda _r: str(bare))
    policy = _policy(tmp_path)
    workspace = derive_workspace(policy, _repository(), _semantic())
    bootstrap = await bootstrap_execution_checkout(
        policy=policy,
        workspace=workspace,
        repository=_repository(),
        semantic=_semantic(),
        branch=BRANCH,
        expected_remote_sha=head,
    )

    assert not marker.exists()
    # The versioned .gitattributes (text eol=crlf) is the only attribute
    # authority, so note.txt is materialized as CRLF.
    assert (bootstrap.workspace / "note.txt").read_bytes() == b"hello\r\n"


@pytest.mark.asyncio
async def test_non_empty_info_attributes_blocks_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(transport_module, "run_user_scoped_git", _fake_git)
    bare, head = _build_remote(tmp_path, dict(_DEFAULT_FILES))
    policy = _policy(tmp_path)
    workspace = derive_workspace(policy, _repository(), _semantic())
    workspace.path.parent.mkdir(parents=True, exist_ok=True)
    _git_ok(None, "clone", "-q", str(bare), str(workspace.path))
    _git_ok(workspace.path, "checkout", "-q", BRANCH)
    info = workspace.path / ".git" / "info" / "attributes"
    info.write_text("*.txt filter=marker\n", encoding="ascii")
    state = ensure_provider_state(workspace)

    with pytest.raises(DirectCodexCanonicalizationError) as exc:
        await capture_canonicalization_snapshot(workspace, state, head, 120.0)
    assert exc.value.code == "direct_codex_info_attributes_not_empty"


def test_materialization_clamps_remove_ambient_authority(tmp_path: Path) -> None:
    policy = _policy(tmp_path)
    workspace = derive_workspace(policy, _repository(), _semantic())
    state = ensure_provider_state(workspace)

    class _Snapshot:
        scalars: ClassVar[dict[str, str]] = {
            "core.autocrlf": "true",
            "core.eol": "",
            "core.safecrlf": "",
        }

    clamps = " ".join(materialization_clamps(_Snapshot(), state))
    assert f"core.attributesFile={state.empty_attributes}" in clamps
    assert f"core.hooksPath={state.hooks}" in clamps
    assert "core.fsmonitor=false" in clamps
    assert "submodule.recurse=false" in clamps
    assert "commit.gpgsign=false" in clamps
    assert "core.pager=cat" in clamps
    assert "core.autocrlf=true" in clamps

    env = materialization_env(state)
    assert env["GIT_CONFIG_NOSYSTEM"] == "1"
    assert env["GIT_ATTR_NOSYSTEM"] == "1"
    assert env["GIT_CONFIG_GLOBAL"] == str(state.empty_config)
    assert env["GIT_LITERAL_PATHSPECS"] == "1"


def test_path_escape_and_metadata_paths_are_rejected() -> None:
    for bad in ("/abs/path", "../escape", "a/../b", ".git/config", "a//b", ""):
        with pytest.raises(DirectCodexCanonicalizationError):
            validate_relative_path(bad)
    validate_relative_path("src/sentinelx_core/module.py")


# ── canonical clean semantics (D14.4) ─────────────────────────────────────


@pytest.mark.asyncio
async def test_unchanged_crlf_worktree_recanonicalizes_to_parent_blob(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bootstrap, bare, head, _policy_obj, workspace = await _bootstrap(tmp_path, monkeypatch)
    worktree = bootstrap.workspace / "note.txt"
    assert worktree.read_bytes() == b"hello\r\n"
    assert _blob(bootstrap.workspace, f"{head}:note.txt") == b"hello\n"

    outcome = await _persist(bootstrap, workspace, head)
    assert outcome.status == "no_change"
    assert outcome.candidate_commit is None
    assert _remote_commit_count(bare, BRANCH) == 1


@pytest.mark.asyncio
async def test_semantic_edit_stays_lf_canonical_without_eol_churn(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bootstrap, _bare, head, _policy_obj, workspace = await _bootstrap(tmp_path, monkeypatch)
    (bootstrap.workspace / "note.txt").write_bytes(b"hello world\r\n")

    outcome = await _persist(bootstrap, workspace, head)
    assert outcome.status == "persisted"
    candidate = outcome.candidate_commit
    assert candidate is not None
    assert _changed_paths(bootstrap.workspace, head, candidate) == {"note.txt"}
    assert _blob(bootstrap.workspace, f"{candidate}:note.txt") == b"hello world\n"
    assert outcome.eligible_change_count == 1


@pytest.mark.asyncio
async def test_binary_bytes_are_preserved_exactly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bootstrap, _bare, head, _policy_obj, workspace = await _bootstrap(tmp_path, monkeypatch)
    new_bytes = b"\x00\xff\r\nnew\x01bytes\r\n"
    (bootstrap.workspace / "data.bin").write_bytes(new_bytes)

    outcome = await _persist(bootstrap, workspace, head)
    assert outcome.status == "persisted"
    assert _blob(bootstrap.workspace, f"{outcome.candidate_commit}:data.bin") == new_bytes


@pytest.mark.asyncio
async def test_working_tree_encoding_round_trips(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    attributes = "wte.txt working-tree-encoding=UTF-16\n"
    bootstrap, _bare, head, _policy_obj, workspace = await _bootstrap(
        tmp_path,
        monkeypatch,
        files={"wte.txt": "hello\n".encode("utf-16"), "README.md": b"# h\n"},
        gitattributes=attributes,
    )
    worktree = bootstrap.workspace / "wte.txt"
    assert worktree.read_bytes().startswith((b"\xff\xfe", b"\xfe\xff"))
    assert _blob(bootstrap.workspace, f"{head}:wte.txt") == b"hello\n"

    # An untouched working-tree-encoded file must not become a change.
    assert (await _persist(bootstrap, workspace, head)).status == "no_change"

    # A real edit round-trips back to canonical UTF-8 blob content.
    worktree.write_bytes("hello world\n".encode("utf-16"))
    outcome = await _persist(bootstrap, workspace, head)
    assert outcome.status == "persisted"
    assert _blob(bootstrap.workspace, f"{outcome.candidate_commit}:wte.txt") == b"hello world\n"


# ── candidate construction / index authority (D14.1-D14.3) ────────────────


@pytest.mark.asyncio
async def test_versioned_gitattributes_mutation_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bootstrap, _bare, head, _policy_obj, workspace = await _bootstrap(tmp_path, monkeypatch)
    (bootstrap.workspace / ".gitattributes").write_text(
        "*.txt text eol=crlf\n*.bin -text\n*.md -text\n", encoding="ascii"
    )

    with pytest.raises(DirectCodexPersistenceError) as exc:
        await _persist(bootstrap, workspace, head)
    assert exc.value.code == "direct_codex_unsupported_attribute_mutation"


@pytest.mark.asyncio
async def test_codex_index_is_not_candidate_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A Codex-staged content that differs from the worktree cannot win."""
    bootstrap, _bare, head, _policy_obj, workspace = await _bootstrap(tmp_path, monkeypatch)
    ws = bootstrap.workspace
    (ws / "CHANGE.md").write_bytes(b"staged-content\n")
    _git_ok(ws, "add", "CHANGE.md")
    (ws / "CHANGE.md").write_bytes(b"worktree-content\n")

    outcome = await _persist(bootstrap, workspace, head)
    assert outcome.status == "persisted"
    assert _blob(ws, f"{outcome.candidate_commit}:CHANGE.md") == b"worktree-content\n"


@pytest.mark.asyncio
async def test_pre_staged_excluded_entry_cannot_enter_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bootstrap, _bare, head, _policy_obj, workspace = await _bootstrap(tmp_path, monkeypatch)
    ws = bootstrap.workspace
    root = ws / ".devforge"
    root.mkdir(parents=True, exist_ok=True)
    (root / "leak.md").write_bytes(b"provider-internal\n")
    _git_ok(ws, "add", ".devforge/leak.md")
    (ws / "note.txt").write_bytes(b"edited\r\n")

    outcome = await _persist(bootstrap, workspace, head)
    assert outcome.status == "persisted"
    candidate = outcome.candidate_commit
    assert _changed_paths(ws, head, candidate) == {"note.txt"}
    assert ".devforge/leak.md" not in _tree_paths(ws, candidate)


@pytest.mark.asyncio
async def test_provider_control_artifacts_are_not_committed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bootstrap, _bare, head, _policy_obj, workspace = await _bootstrap(tmp_path, monkeypatch)
    ws = bootstrap.workspace
    (ws / ".devforge").mkdir(parents=True, exist_ok=True)
    (ws / ".devforge" / "direct-codex-handoff.md").write_text("handoff\n", encoding="utf-8")
    (ws / "note.txt").write_bytes(b"edited\r\n")

    outcome = await _persist(bootstrap, workspace, head)
    assert outcome.status == "persisted"
    assert _changed_paths(ws, head, outcome.candidate_commit) == {"note.txt"}
    state = provider_state(workspace)
    assert state.candidate_index.is_file()
    assert not str(state.candidate_index).startswith(str(ws))


@pytest.mark.asyncio
async def test_candidate_is_seeded_from_exact_parent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bootstrap, bare, head, _policy_obj, workspace = await _bootstrap(tmp_path, monkeypatch)
    (bootstrap.workspace / "note.txt").write_bytes(b"edited\r\n")

    outcome = await _persist(bootstrap, workspace, head)
    candidate = outcome.candidate_commit
    parent = _git_ok(bootstrap.workspace, "rev-parse", f"{candidate}^").decode().strip()
    assert parent == head
    assert outcome.base_head == head
    assert _remote_rev(bare, BRANCH) == candidate


@pytest.mark.asyncio
async def test_local_head_owned_by_direct_host_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bootstrap, _bare, head, _policy_obj, workspace = await _bootstrap(tmp_path, monkeypatch)
    ws = bootstrap.workspace
    (ws / "host.txt").write_bytes(b"host commit\n")
    _git_ok(
        ws,
        "-c",
        "user.email=host@example.com",
        "-c",
        "user.name=host",
        "add",
        "host.txt",
    )
    _git_ok(
        ws,
        "-c",
        "user.email=host@example.com",
        "-c",
        "user.name=host",
        "commit",
        "-q",
        "-m",
        "host commit",
    )

    with pytest.raises(DirectCodexPersistenceError) as exc:
        await _persist(bootstrap, workspace, head)
    assert exc.value.code == "direct_codex_local_head_unexpected"


@pytest.mark.asyncio
async def test_unmerged_index_state_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bootstrap, _bare, head, _policy_obj, workspace = await _bootstrap(tmp_path, monkeypatch)
    ws = bootstrap.workspace
    index_info = (
        f"100644 {'1' * 40} 1\tconflict.txt\n"
        f"100644 {'2' * 40} 2\tconflict.txt\n"
        f"100644 {'3' * 40} 3\tconflict.txt\n"
    ).encode()
    _git_ok(ws, "update-index", "--index-info", stdin=index_info)

    with pytest.raises(DirectCodexPersistenceError) as exc:
        await _persist(bootstrap, workspace, head)
    assert exc.value.code == "direct_codex_unmerged_state"


@pytest.mark.asyncio
async def test_hooks_and_signing_cannot_execute_through_persistence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bootstrap, _bare, head, _policy_obj, workspace = await _bootstrap(tmp_path, monkeypatch)
    ws = bootstrap.workspace
    hooks = ws / ".git" / "hooks"
    hooks.mkdir(parents=True, exist_ok=True)
    marker = tmp_path / "hook-ran.txt"
    for name in ("pre-commit", "pre-push", "commit-msg", "post-commit"):
        (hooks / name).write_text(
            f'#!/bin/sh\necho ran >> "{marker.as_posix()}"\n', encoding="ascii"
        )
    # Signing would fail without a key: the provider clamp must disable it.
    _git_ok(ws, "config", "commit.gpgsign", "true")
    (ws / "note.txt").write_bytes(b"edited\r\n")

    outcome = await _persist(bootstrap, workspace, head)
    assert outcome.status == "persisted"
    assert not marker.exists()


# ── publication / drift (D17) ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_remote_drift_before_publish_fails_without_push(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bootstrap, bare, head, _policy_obj, workspace = await _bootstrap(tmp_path, monkeypatch)
    (bootstrap.workspace / "note.txt").write_bytes(b"edited\r\n")

    other = tmp_path / "other"
    _git_ok(None, "clone", "-q", str(bare), str(other))
    _git_ok(other, "checkout", "-q", BRANCH)
    (other / "drift.txt").write_bytes(b"drift\n")
    _git_ok(other, "add", "drift.txt")
    _git_ok(
        other, "-c", "user.email=d@e", "-c", "user.name=d", "commit", "-q", "-m", "drift"
    )
    drifted = _git_ok(other, "rev-parse", "HEAD").decode().strip()
    _git_ok(other, "push", "-q", "origin", BRANCH)

    with pytest.raises(DirectCodexPersistenceError) as exc:
        await _persist(bootstrap, workspace, head)
    assert exc.value.code == "direct_codex_transport_drift"
    assert _remote_rev(bare, BRANCH) == drifted
    assert _remote_commit_count(bare, BRANCH) == 2


@pytest.mark.asyncio
async def test_ordinary_push_creates_no_replacement_branch_or_tag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bootstrap, bare, head, _policy_obj, workspace = await _bootstrap(tmp_path, monkeypatch)
    (bootstrap.workspace / "note.txt").write_bytes(b"edited\r\n")

    outcome = await _persist(bootstrap, workspace, head)
    assert outcome.published is True
    refs = _git_ok(bare, "for-each-ref", "--format=%(refname)").decode().split()
    assert refs == [f"refs/heads/{BRANCH}"]


@pytest.mark.asyncio
async def test_readback_mismatch_is_not_a_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bootstrap, bare, head, _policy_obj, workspace = await _bootstrap(tmp_path, monkeypatch)
    (bootstrap.workspace / "note.txt").write_bytes(b"edited\r\n")

    settings = {"calls": 0}
    real = persistence_module.read_remote_head

    async def _flaky(**kwargs: Any) -> str:
        settings["calls"] += 1
        if settings["calls"] >= 3:
            # The push landed but the independent readback does not observe it.
            return head
        return await real(**kwargs)

    monkeypatch.setattr(persistence_module, "read_remote_head", _flaky)
    outcome = await _persist(bootstrap, workspace, head)
    assert outcome.published is False
    assert outcome.consistent is False
    assert outcome.status == "publication_uncertain_or_not_observed"
    assert outcome.error_code == "direct_codex_publication_uncertain"
    # The candidate really did land; the receipt is honest about the readback.
    assert _remote_rev(bare, BRANCH) == outcome.candidate_commit


# ── recovery journal / determinism (D16) ──────────────────────────────────


@pytest.mark.asyncio
async def test_same_attempt_reconstructs_bit_identical_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bootstrap, bare, head, _policy_obj, workspace = await _bootstrap(tmp_path, monkeypatch)
    (bootstrap.workspace / "note.txt").write_bytes(b"edited\r\n")
    state = provider_state(workspace)

    first = await _persist(bootstrap, workspace, head, clock=lambda: 1_700_000_000)
    assert first.status == "persisted"
    candidate = first.candidate_commit

    journal = persistence_module._read_journal(state)
    assert journal is not None
    frozen = journal.commit_identity

    for state_name in (STATE_PREPARED, STATE_TREE_READY, STATE_CANDIDATE_READY):
        # Reset the transport and journal to an interruption point, keeping the
        # frozen commit identity. Only an identity reuse keeps the SHA stable.
        _git_ok(bare, "update-ref", f"refs/heads/{BRANCH}", head, candidate)
        _git_ok(workspace.path, "update-ref", f"refs/heads/{BRANCH}", head, candidate)
        journal.state = state_name
        journal.candidate_commit_sha = (
            None if state_name in (STATE_PREPARED, STATE_TREE_READY) else candidate
        )
        journal.candidate_tree_sha = None if state_name == STATE_PREPARED else journal.candidate_tree_sha
        persistence_module._write_journal(state, journal)

        outcome = await _persist(bootstrap, workspace, head, clock=lambda: 1_800_000_000)
        assert outcome.status == "persisted", state_name
        assert outcome.candidate_commit == candidate, state_name
        assert outcome.commit_provenance_digest == first.commit_provenance_digest
        assert outcome.actual_branch == BRANCH

    # A different frozen identity would produce a different object, proving the
    # freeze (not the content) is what pins the SHA.
    assert frozen.author_date_utc_seconds == 1_700_000_000
    assert frozen.serialization_version == 1


@pytest.mark.asyncio
async def test_publish_intent_recovery_performs_readback_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bootstrap, bare, head, _policy_obj, workspace = await _bootstrap(tmp_path, monkeypatch)
    (bootstrap.workspace / "note.txt").write_bytes(b"edited\r\n")
    state = provider_state(workspace)
    first = await _persist(bootstrap, workspace, head, clock=lambda: 1_700_000_000)
    candidate = first.candidate_commit

    # Simulate: publish_intent persisted, then the push never landed.
    _git_ok(bare, "update-ref", f"refs/heads/{BRANCH}", head, candidate)
    journal = persistence_module._read_journal(state)
    journal.state = STATE_PUBLISH_INTENT
    journal.candidate_commit_sha = candidate
    persistence_module._write_journal(state, journal)

    outcome = await _persist(bootstrap, workspace, head)
    assert outcome.published is False
    assert outcome.status == "publication_uncertain_or_not_observed"
    # Readback only: the remote must still be the admitted base head, and no
    # hidden automatic second push may have happened.
    assert _remote_rev(bare, BRANCH) == head
    assert _remote_commit_count(bare, BRANCH) == 1
    journal_after = persistence_module._read_journal(state)
    assert journal_after.state == STATE_PUBLISH_INTENT
    assert journal_after.candidate_commit_sha == candidate


@pytest.mark.asyncio
async def test_publish_intent_recovery_observes_a_landed_push(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bootstrap, bare, head, _policy_obj, workspace = await _bootstrap(tmp_path, monkeypatch)
    (bootstrap.workspace / "note.txt").write_bytes(b"edited\r\n")
    state = provider_state(workspace)
    first = await _persist(bootstrap, workspace, head, clock=lambda: 1_700_000_000)

    journal = persistence_module._read_journal(state)
    journal.state = STATE_PUBLISH_INTENT
    persistence_module._write_journal(state, journal)

    outcome = await _persist(bootstrap, workspace, head)
    assert outcome.status == "persisted"
    assert outcome.candidate_commit == first.candidate_commit
    assert _remote_rev(bare, BRANCH) == first.candidate_commit
    assert persistence_module._read_journal(state).state == STATE_PUBLISHED


@pytest.mark.asyncio
async def test_publish_intent_recovery_detects_transport_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bootstrap, bare, head, _policy_obj, workspace = await _bootstrap(tmp_path, monkeypatch)
    (bootstrap.workspace / "note.txt").write_bytes(b"edited\r\n")
    state = provider_state(workspace)
    first = await _persist(bootstrap, workspace, head, clock=lambda: 1_700_000_000)

    other = tmp_path / "other"
    _git_ok(None, "clone", "-q", str(bare), str(other))
    _git_ok(other, "checkout", "-q", BRANCH)
    (other / "drift.txt").write_bytes(b"drift\n")
    _git_ok(other, "add", "drift.txt")
    _git_ok(other, "-c", "user.email=d@e", "-c", "user.name=d", "commit", "-q", "-m", "d")
    _git_ok(other, "push", "-q", "origin", BRANCH)

    journal = persistence_module._read_journal(state)
    journal.state = STATE_PUBLISH_INTENT
    persistence_module._write_journal(state, journal)

    with pytest.raises(DirectCodexPersistenceError) as exc:
        await _persist(bootstrap, workspace, head)
    assert exc.value.code == "direct_codex_transport_drift"
    assert _remote_rev(bare, BRANCH) != first.candidate_commit


@pytest.mark.asyncio
async def test_published_state_is_reconstructed_not_replayed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bootstrap, bare, head, _policy_obj, workspace = await _bootstrap(tmp_path, monkeypatch)
    (bootstrap.workspace / "note.txt").write_bytes(b"edited\r\n")
    first = await _persist(bootstrap, workspace, head, clock=lambda: 1_700_000_000)

    second = await _persist(bootstrap, workspace, head, clock=lambda: 1_900_000_000)
    assert second.status == "persisted"
    assert second.candidate_commit == first.candidate_commit
    assert second.mode == PERSISTENCE_MODE
    assert _remote_commit_count(bare, BRANCH) == 2  # no second candidate commit


@pytest.mark.asyncio
async def test_recovery_journal_identity_mismatch_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bootstrap, _bare, head, _policy_obj, workspace = await _bootstrap(tmp_path, monkeypatch)
    (bootstrap.workspace / "note.txt").write_bytes(b"edited\r\n")
    await _persist(bootstrap, workspace, head, clock=lambda: 1_700_000_000)

    with pytest.raises(DirectCodexPersistenceError) as exc:
        await _persist(bootstrap, workspace, head, attempt="attempt-2", clock=lambda: 1_700_000_000)
    assert exc.value.code == "direct_codex_recovery_journal_identity_mismatch"


# ── isolation of the canonical checkout (AC4) ─────────────────────────────


@pytest.mark.asyncio
async def test_canonical_checkout_is_never_mutated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    canonical = tmp_path / "canonical-checkout"
    bootstrap, _bare, head, _policy_obj, workspace = await _bootstrap(tmp_path, monkeypatch)
    _git_ok(None, "clone", "-q", str(_bare), str(canonical))
    _git_ok(canonical, "checkout", "-q", BRANCH)
    _git_ok(canonical, "config", "user.email", "c@e")
    _git_ok(canonical, "config", "user.name", "c")

    before_head = _git_ok(canonical, "rev-parse", "HEAD").decode().strip()
    before_index = _git_ok(canonical, "ls-files", "-s").decode()
    before_status = _git_ok(canonical, "status", "--porcelain").decode()
    worktrees_before = (canonical / ".git" / "worktrees").exists()

    (bootstrap.workspace / "note.txt").write_bytes(b"edited\r\n")
    outcome = await _persist(bootstrap, workspace, head)
    assert outcome.published is True

    assert _git_ok(canonical, "rev-parse", "HEAD").decode().strip() == before_head
    assert _git_ok(canonical, "ls-files", "-s").decode() == before_index
    assert _git_ok(canonical, "status", "--porcelain").decode() == before_status
    assert (canonical / ".git" / "worktrees").exists() is worktrees_before
    assert _git_ok(canonical, "rev-parse", "HEAD").decode().strip() == before_head


# ── fixed provider Git environment boundary ───────────────────────────────


def test_git_environment_allowlist_is_closed() -> None:
    from sentinelx_core.user_git import GIT_ENV_ALLOWLIST, UserScopedGitError, validate_git_env

    assert "GIT_INDEX_FILE" in GIT_ENV_ALLOWLIST
    assert validate_git_env({"GIT_INDEX_FILE": "x"}) == {"GIT_INDEX_FILE": "x"}
    with pytest.raises(UserScopedGitError) as exc:
        validate_git_env({"GIT_CONFIG_PARAMETERS": "x"})
    assert exc.value.code == "GitEnvironmentRejected"


def test_gitlink_and_type_change_modes_fail_closed() -> None:
    from sentinelx_core.direct_codex_persistence import reject_unsupported_mode

    with pytest.raises(DirectCodexPersistenceError) as exc:
        reject_unsupported_mode("sub", "160000", "160000", "M")
    assert exc.value.code == "direct_codex_unsupported_gitlink_mutation"

    with pytest.raises(DirectCodexPersistenceError) as exc:
        reject_unsupported_mode("link", "100644", "120000", "T")
    assert exc.value.code == "direct_codex_unsupported_mode_change"

    with pytest.raises(DirectCodexPersistenceError):
        reject_unsupported_mode("odd", "100664", "100664", "M")

    # Ordinarary add/modify/delete of regular files and symlinks is accepted.
    reject_unsupported_mode("a.py", "000000", "100644", "A")
    reject_unsupported_mode("b.sh", "100755", "100755", "M")
    reject_unsupported_mode("c.txt", "100644", "000000", "D")
    reject_unsupported_mode("d.link", "000000", "120000", "A")


def test_commit_message_is_deterministic_and_carries_lineage() -> None:
    from sentinelx_core.direct_codex_persistence import commit_message

    first = commit_message(task_id="PR-015", run_id="run-1", attempt_id="a-1", slice_id="S04")
    second = commit_message(task_id="PR-015", run_id="run-1", attempt_id="a-1", slice_id="S04")
    assert first == second
    for expected in ("PR-015", "run-1", "a-1", "S04", "provider: direct", "adapter: codex"):
        assert expected in first
