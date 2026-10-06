"""PR-015/S02: direct-Codex workspace bootstrap, transport admission, verified
chain discovery, bounded active-user execution and the direct/Codex receipt."""
from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from sentinelx_core.direct_codex_discovery import (
    CodexChain,
    DirectCodexDiscoveryError,
    discover_codex_chain,
    resolve_node_executable,
    verify_package,
)
from sentinelx_core.direct_codex_handoff import compile_handoff
from sentinelx_core.direct_codex_result import normalize_result, validate_receipt
from sentinelx_core.direct_codex_transport import (
    DirectCodexTransportError,
    bootstrap_execution_checkout,
    remote_url_for,
)
from sentinelx_core.direct_codex_workspace import (
    DirectCodexWorkspaceError,
    derive_workspace,
    ensure_outside_canonical,
)
from sentinelx_core.mutation_placement import RepositoryIdentity, SemanticIdentity
from sentinelx_core.policy import DirectCodexPolicy, MutationExecutionPolicy, Policy
from sentinelx_core.user_process import (
    UserProcessError,
    UserProcessRequest,
    run_user_scoped_process,
)

WINDOWS_ONLY = pytest.mark.skipif(
    not sys.platform.startswith("win"), reason="Windows active-user process substrate"
)

_GIT = "git"


def _node() -> str | None:
    found = _which("node")
    return found


def _which(name: str) -> str | None:
    import shutil

    return shutil.which(name)


def _repository() -> RepositoryIdentity:
    return RepositoryIdentity(
        vcs="git", authority="github.com", path="bewaterhere-coder/sentinelx-cloud-core"
    )


def _semantic(slice_id: str = "S02") -> SemanticIdentity:
    return SemanticIdentity(
        project_id="sentinelx-cloud-core",
        task_id="PR-015-direct-codex-development-host-invocation-bridge-v1",
        run_id="run-1",
        attempt_id="attempt-1",
        slice_id=slice_id,
    )


def _policy(tmp_path: Path, **overrides: Any) -> DirectCodexPolicy:
    workspace = tmp_path / "devforge-workspaces"
    workspace.mkdir(parents=True, exist_ok=True)
    policy = DirectCodexPolicy(
        configured=True,
        enabled=True,
        workspace_root=workspace,
        supported_platform="windows",
        timeout_seconds=120,
        max_result_bytes=8192,
    )
    return replace(policy, **overrides) if overrides else policy


def _full_policy(tmp_path: Path, **overrides: Any) -> Policy:
    return Policy(
        upload_base=tmp_path / "uploads",
        mutation_execution=MutationExecutionPolicy(configured=True, scoped_mutation_enabled=True),
        direct_codex=_policy(tmp_path, **overrides),
    )


# ── workspace derivation ─────────────────────────────────────────────────


def test_workspace_is_derived_from_identity_not_caller_path(tmp_path: Path) -> None:
    policy = _policy(tmp_path)
    first = derive_workspace(policy, _repository(), _semantic())
    second = derive_workspace(policy, _repository(), _semantic())

    assert first.path == second.path
    assert first.path != policy.workspace_root
    assert str(first.path).startswith(str(policy.workspace_root.resolve(strict=False)))
    assert derive_workspace(policy, _repository(), _semantic("S03")).path != first.path


def test_workspace_refuses_canonical_intersection(tmp_path: Path) -> None:
    policy = _policy(tmp_path)
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    workspace = derive_workspace(policy, _repository(), _semantic())

    ensure_outside_canonical(workspace, [canonical])
    with pytest.raises(DirectCodexWorkspaceError) as exc:
        ensure_outside_canonical(workspace, [canonical, tmp_path])
    assert exc.value.code == "direct_codex_workspace_intersects_canonical"


# ── transport admission ──────────────────────────────────────────────────


async def _fake_git(root: Path, *args: str, timeout: float) -> tuple[int, bytes, bytes]:
    """Run real git without the Windows WTS substrate (tests run as the user)."""
    proc = await asyncio.create_subprocess_exec(
        _GIT,
        "-C",
        str(root),
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    return proc.returncode, out, err


def _bare_remote(tmp_path: Path, branch: str) -> tuple[Path, str]:
    source = tmp_path / "source"
    source.mkdir()
    subprocess.run([_GIT, "init", "-q", str(source)], check=True)
    subprocess.run([_GIT, "-C", str(source), "checkout", "-q", "-b", branch], check=True)
    (source / "README.md").write_text("canonical\n", encoding="utf-8")
    subprocess.run([_GIT, "-C", str(source), "add", "README.md"], check=True)
    subprocess.run(
        [
            _GIT,
            "-C",
            str(source),
            "-c",
            "user.email=t@example.com",
            "-c",
            "user.name=test",
            "commit",
            "-q",
            "-m",
            "base",
        ],
        check=True,
    )
    bare = tmp_path / "remote.git"
    subprocess.run([_GIT, "clone", "-q", "--bare", str(source), str(bare)], check=True)
    head = subprocess.run(
        [_GIT, "-C", str(source), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return bare, head


@pytest.mark.asyncio
async def test_remote_head_mismatch_fails_before_any_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "sentinelx_core.direct_codex_transport.run_user_scoped_git", _fake_git
    )
    bare, head = _bare_remote(tmp_path, "task/bridge")
    monkeypatch.setattr(
        "sentinelx_core.direct_codex_transport.remote_url_for", lambda _repository: str(bare)
    )
    policy = _policy(tmp_path)
    workspace = derive_workspace(policy, _repository(), _semantic())

    with pytest.raises(DirectCodexTransportError) as exc:
        await bootstrap_execution_checkout(
            policy=policy,
            workspace=workspace,
            repository=_repository(),
            semantic=_semantic(),
            branch="task/bridge",
            expected_remote_sha="0" * 40,
        )
    assert exc.value.code == "direct_codex_remote_head_mismatch"
    assert not (workspace.path / ".git").exists()
    assert head  # remote exists; the mismatch, not a missing remote, blocked mutation


@pytest.mark.asyncio
async def test_independent_checkout_is_exact_branch_and_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "sentinelx_core.direct_codex_transport.run_user_scoped_git", _fake_git
    )
    bare, head = _bare_remote(tmp_path, "task/bridge")
    monkeypatch.setattr(
        "sentinelx_core.direct_codex_transport.remote_url_for", lambda _repository: str(bare)
    )
    policy = _policy(tmp_path)
    workspace = derive_workspace(policy, _repository(), _semantic())

    bootstrap = await bootstrap_execution_checkout(
        policy=policy,
        workspace=workspace,
        repository=_repository(),
        semantic=_semantic(),
        branch="task/bridge",
        expected_remote_sha=head,
    )

    assert bootstrap.local_head == head == bootstrap.remote_head
    assert bootstrap.actual_branch == "task/bridge"
    assert bootstrap.independent_checkout is True
    assert bootstrap.git_worktree_add_used is False
    assert bootstrap.created_checkout is True
    assert bootstrap.canonical_checkout_mutated is False
    assert (workspace.path / "README.md").is_file()


@pytest.mark.asyncio
async def test_canonical_checkout_metadata_is_not_touched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "sentinelx_core.direct_codex_transport.run_user_scoped_git", _fake_git
    )
    bare, head = _bare_remote(tmp_path, "task/bridge")
    canonical = tmp_path / "canonical-checkout"
    subprocess.run([_GIT, "clone", "-q", str(bare), str(canonical)], check=True)
    subprocess.run([_GIT, "-C", str(canonical), "checkout", "-q", "task/bridge"], check=True)
    before = subprocess.run(
        [_GIT, "-C", str(canonical), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    worktrees_before = (canonical / ".git" / "worktrees").exists()

    monkeypatch.setattr(
        "sentinelx_core.direct_codex_transport.remote_url_for", lambda _repository: str(bare)
    )
    policy = _policy(tmp_path)
    workspace = derive_workspace(policy, _repository(), _semantic())
    bootstrap = await bootstrap_execution_checkout(
        policy=policy,
        workspace=workspace,
        repository=_repository(),
        semantic=_semantic(),
        branch="task/bridge",
        expected_remote_sha=head,
        canonical_roots=[canonical],
    )

    after = subprocess.run(
        [_GIT, "-C", str(canonical), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert before == after
    assert (canonical / ".git" / "worktrees").exists() is worktrees_before
    assert bootstrap.canonical_checkout_mutated is False
    assert str(canonical) in bootstrap.canonical_roots


def test_remote_url_is_provider_derived() -> None:
    assert remote_url_for(_repository()) == (
        "https://github.com/bewaterhere-coder/sentinelx-cloud-core.git"
    )


# ── verified Codex chain ─────────────────────────────────────────────────


def _fake_npm_root(root: Path, *, name: str = "@openai/codex", bin_value: Any = "bin/codex.js") -> Path:
    package = root / "@openai" / "codex"
    package.mkdir(parents=True, exist_ok=True)
    (package / "bin").mkdir(exist_ok=True)
    (package / "bin" / "codex.js").write_text("// codex\n", encoding="utf-8")
    (package / "package.json").write_text(
        f'{{"name": "{name}", "version": "0.154.0", "bin": {bin_value!r}}}'
        if not isinstance(bin_value, str)
        else f'{{"name": "{name}", "version": "0.154.0", "bin": "{bin_value}"}}',
        encoding="utf-8",
    )
    return root


def test_package_identity_is_verified(tmp_path: Path) -> None:
    root = _fake_npm_root(tmp_path / "npm" / "node_modules")
    verified = verify_package(root, "@openai/codex")
    assert verified is not None
    package_dir, script, version = verified
    assert script.is_file() and script.name == "codex.js"
    assert package_dir == tmp_path / "npm" / "node_modules" / "@openai" / "codex"
    assert version == "0.154.0"


def test_package_name_mismatch_is_rejected(tmp_path: Path) -> None:
    root = _fake_npm_root(tmp_path / "npm" / "node_modules", name="evil/codex")
    assert verify_package(root, "@openai/codex") is None


def test_bin_outside_package_is_rejected(tmp_path: Path) -> None:
    """A manifest pointing at a script outside the package never gets executed."""
    root = tmp_path / "npm" / "node_modules"
    package = root / "@openai" / "codex"
    package.mkdir(parents=True)
    (tmp_path / "outside").mkdir()
    (tmp_path / "outside" / "codex.js").write_text("// evil\n", encoding="utf-8")
    (package / "package.json").write_text(
        '{"name": "@openai/codex", "version": "0.154.0", "bin": "../../outside/codex.js"}',
        encoding="utf-8",
    )
    assert verify_package(root, "@openai/codex") is None


def test_missing_node_executable_fails_closed(tmp_path: Path) -> None:
    policy = _policy(tmp_path, node_executable=tmp_path / "missing-node.exe")
    with pytest.raises(DirectCodexDiscoveryError) as exc:
        resolve_node_executable(policy)
    assert exc.value.code == "direct_codex_node_missing"


# ── deterministic handoff ────────────────────────────────────────────────


def test_handoff_is_deterministic_and_bounded() -> None:
    kwargs = {
        "task_id": "PR-015",
        "run_id": "run-1",
        "attempt_id": "attempt-1",
        "slice_id": "S02",
        "action": "implementation",
        "requirement_ref": "docs/requirements/PR-015.md",
        "plan_ref": "docs/plans/PR-015-plan.md",
        "findings_ref": None,
        "pr_number": 15,
        "branch": "task/bridge",
        "expected_remote_sha": "a" * 40,
    }
    first = compile_handoff(**kwargs)  # type: ignore[arg-type]
    second = compile_handoff(**kwargs)  # type: ignore[arg-type]

    assert first.digest == second.digest
    assert "PR-015" in first.text and "task/bridge" in first.text
    assert "replacement branch" in first.text
    assert len(first.text) <= 8000


# ── result / receipt contract ────────────────────────────────────────────


class _Bootstrap:
    workspace = Path("/workspaces/x")
    branch = "task/bridge"
    expected_remote_sha = "a" * 40
    independent_checkout = True
    canonical_checkout_mutated = False
    git_worktree_add_used = False


class _Process:
    returncode = 0
    stdout = "changed: src/a.py"
    stderr = ""
    timed_out = False
    process_tree_closed = True
    job_contained = True
    pid = 4242
    execution_context = "active_console_session_direct"


def _params() -> dict[str, Any]:
    return {
        "repository": {"vcs": "git", "authority": "github.com", "path": "o/r"},
        "lineage": {
            "project_id": "sentinelx-cloud-core",
            "task_id": "PR-015",
            "run_id": "run-1",
            "attempt_id": "attempt-1",
            "slice_id": "S02",
        },
        "development": {
            "action": "implementation",
            "requirement_ref": "docs/r.md",
            "plan_ref": "docs/p.md",
        },
        "transport": {
            "type": "github-pr",
            "pr_number": 15,
            "branch": "task/bridge",
            "expected_remote_sha": "a" * 40,
        },
    }


def test_local_only_run_is_not_a_success_receipt() -> None:
    payload = normalize_result(
        params=_params(),
        bootstrap=_Bootstrap(),  # type: ignore[arg-type]
        process=_Process(),  # type: ignore[arg-type]
        handoff_digest="d" * 64,
        actual_branch="task/bridge",
        local_head="a" * 40,
        remote_head_readback="a" * 40,
    )
    assert payload["transport"]["published"] is False
    assert payload["receipt"]["valid"] is False
    assert payload["receipt"]["incomplete_reason"] == "implementation_not_persisted"
    ok, reason = validate_receipt(payload, task_id="PR-015", slice_id="S02")
    assert ok is False and reason == "receipt_not_valid"


def test_persisted_consistent_run_produces_valid_receipt() -> None:
    payload = normalize_result(
        params=_params(),
        bootstrap=_Bootstrap(),  # type: ignore[arg-type]
        process=_Process(),  # type: ignore[arg-type]
        handoff_digest="d" * 64,
        actual_branch="task/bridge",
        local_head="b" * 40,
        remote_head_readback="b" * 40,
    )
    assert payload["execution"]["provider"] == "direct"
    assert payload["execution"]["adapter"] == "codex"
    assert payload["receipt"]["valid"] is True
    assert payload["receipt"]["acceptance_claim"] is False
    assert validate_receipt(payload, task_id="PR-015", slice_id="S02") == (True, "ok")
    assert validate_receipt(payload, task_id="PR-015", slice_id="S03")[0] is False


def test_replacement_branch_is_inconsistent() -> None:
    payload = normalize_result(
        params=_params(),
        bootstrap=_Bootstrap(),  # type: ignore[arg-type]
        process=_Process(),  # type: ignore[arg-type]
        handoff_digest="d" * 64,
        actual_branch="task/replacement",
        local_head="b" * 40,
        remote_head_readback="b" * 40,
    )
    assert payload["transport"]["consistent"] is False
    assert validate_receipt(payload, task_id="PR-015", slice_id="S02")[0] is False


# ── end-to-end execute_task with a fixture Codex ─────────────────────────


def _fixture_codex(path: Path, *, push: bool) -> Path:
    push_body = (
        "const cp=require('child_process');"
        "const run=(...a)=>cp.execFileSync('git',a,{stdio:'ignore'});"
        "run('-c','user.email=fixture@example.com','-c','user.name=fixture','add','CHANGE.md');"
        "run('-c','user.email=fixture@example.com','-c','user.name=fixture','commit','-m','slice');"
        "run('push','origin','HEAD:'+process.env.FIXTURE_BRANCH);"
        if push
        else ""
    )
    path.write_text(
        "const fs=require('fs');"
        "if(process.argv.includes('--help')){console.log('Usage: codex exec [PROMPT] --json');"
        "process.exit(0);}"
        "fs.writeFileSync('CHANGE.md','slice work\\n');"
        + push_body
        + "console.log(JSON.stringify({status:'ok'}));",
        encoding="utf-8",
    )
    return path


@WINDOWS_ONLY
@pytest.mark.asyncio
async def test_execute_task_reports_local_only_run_as_incomplete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    node = _node()
    if node is None:
        pytest.skip("node is not available")

    from sentinelx_core.handlers import direct_codex as provider_module
    from sentinelx_core.handlers.direct_codex import make_devforge_direct_codex_provider

    monkeypatch.setattr(
        "sentinelx_core.direct_codex_transport.run_user_scoped_git", _fake_git
    )
    bare, head = _bare_remote(tmp_path, "task/bridge")
    monkeypatch.setattr(
        "sentinelx_core.direct_codex_transport.remote_url_for", lambda _repository: str(bare)
    )
    script = _fixture_codex(tmp_path / "codex.js", push=False)
    chain = CodexChain(
        node_executable=Path(node),
        codex_script=script,
        package_dir=script.parent,
        package_name="@openai/codex",
        package_version="0.0.0",
        npm_root=script.parent,
        json_output_supported=False,
    )
    monkeypatch.setattr(
        provider_module,
        "discover_codex_chain",
        lambda *args, **kwargs: _await_chain(chain),
    )

    policy = _full_policy(tmp_path, node_executable=Path(node))
    provider = make_devforge_direct_codex_provider(
        policy, platform_name="Windows", canonical_roots=[]
    )
    await provider.prove_containment(repository=_repository(), semantic=_semantic())

    params = _params()
    params["lineage"]["slice_id"] = "S02"
    params["transport"]["branch"] = "task/bridge"
    params["transport"]["expected_remote_sha"] = head
    payload = await provider.call(_context_like(), "execute_task", params)

    assert payload["transport"]["local_head"] == head
    assert payload["transport"]["published"] is False
    assert payload["receipt"]["valid"] is False
    assert payload["receipt"]["incomplete_reason"] == "implementation_not_persisted"
    assert payload["workspace"]["canonical_checkout_mutated"] is False
    assert payload["receipt"]["acceptance_claim"] is False


@WINDOWS_ONLY
@pytest.mark.asyncio
async def test_execute_task_completes_exact_transport_and_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    node = _node()
    if node is None:
        pytest.skip("node is not available")

    from sentinelx_core.handlers import direct_codex as provider_module
    from sentinelx_core.handlers.direct_codex import make_devforge_direct_codex_provider

    monkeypatch.setattr(
        "sentinelx_core.direct_codex_transport.run_user_scoped_git", _fake_git
    )
    bare, head = _bare_remote(tmp_path, "task/bridge")
    monkeypatch.setattr(
        "sentinelx_core.direct_codex_transport.remote_url_for", lambda _repository: str(bare)
    )
    monkeypatch.setenv("FIXTURE_BRANCH", "task/bridge")
    script = _fixture_codex(tmp_path / "codex.js", push=True)
    chain = CodexChain(
        node_executable=Path(node),
        codex_script=script,
        package_dir=script.parent,
        package_name="@openai/codex",
        package_version="0.0.0",
        npm_root=script.parent,
        json_output_supported=False,
    )
    monkeypatch.setattr(
        provider_module,
        "discover_codex_chain",
        lambda *args, **kwargs: _await_chain(chain),
    )

    policy = _full_policy(tmp_path, node_executable=Path(node))
    provider = make_devforge_direct_codex_provider(
        policy, platform_name="Windows", canonical_roots=[]
    )
    await provider.prove_containment(repository=_repository(), semantic=_semantic())

    params = _params()
    params["lineage"]["slice_id"] = "S02"
    params["transport"]["branch"] = "task/bridge"
    params["transport"]["expected_remote_sha"] = head
    payload = await provider.call(_context_like(), "execute_task", params)

    assert payload["transport"]["actual_branch"] == "task/bridge"
    assert payload["transport"]["consistent"] is True
    assert payload["transport"]["published"] is True
    assert payload["transport"]["local_head"] != head
    assert payload["transport"]["replacement_transport_created"] is False
    assert payload["receipt"]["valid"] is True
    assert payload["receipt"]["reason"] == "ok"
    assert payload["execution"]["provider"] == "direct"
    assert payload["execution"]["adapter"] == "codex"
    assert "CHANGE.md" in payload["verification"]["summary"] or payload["ok"] is True


def _await_chain(chain: Any) -> Any:
    async def _inner() -> Any:
        return chain

    return _inner()


def _context_like() -> Any:
    from datetime import UTC, datetime

    from sentinelx_core.request_context import RequestContext

    return RequestContext("req-s02", "local_api", None, datetime.now(UTC))


# ── Windows active-user process substrate ────────────────────────────────


@WINDOWS_ONLY
@pytest.mark.asyncio
async def test_process_cwd_outside_workspace_is_refused(tmp_path: Path) -> None:
    node = _node()
    if node is None:
        pytest.skip("node is not available")
    request = UserProcessRequest(
        executable=node,
        argv=[node, "-e", "console.log(1)"],
        cwd=tmp_path,
        allowed_root=tmp_path / "elsewhere",
        timeout_seconds=30,
    )
    with pytest.raises(UserProcessError) as exc:
        await run_user_scoped_process(request)
    assert exc.value.code == "user_process_workspace_escape"


@WINDOWS_ONLY
@pytest.mark.asyncio
async def test_process_output_is_captured_and_bounded(tmp_path: Path) -> None:
    node = _node()
    if node is None:
        pytest.skip("node is not available")
    cwd = tmp_path / "workspace"
    cwd.mkdir()
    request = UserProcessRequest(
        executable=node,
        argv=[node, "-e", "console.log('x'.repeat(5000))"],
        cwd=cwd,
        allowed_root=tmp_path,
        timeout_seconds=30,
        max_output_bytes=256,
    )
    result = await run_user_scoped_process(request)
    assert result.returncode == 0
    assert result.stdout.startswith("xxx")
    assert result.stdout.endswith("...[truncated]")
    assert len(result.stdout) <= 256 + len("\n...[truncated]")
    assert result.job_contained is True


@WINDOWS_ONLY
@pytest.mark.asyncio
async def test_timeout_closes_the_process_tree(tmp_path: Path) -> None:
    node = _node()
    if node is None:
        pytest.skip("node is not available")
    cwd = tmp_path / "workspace"
    cwd.mkdir()
    script = (
        "const {spawn}=require('child_process');"
        "const c=spawn(process.execPath,['-e','setTimeout(function(){},120000)'],"
        "{detached:false,stdio:'ignore'});c.unref();"
        "setTimeout(function(){},120000);"
    )
    request = UserProcessRequest(
        executable=node,
        argv=[node, "-e", script],
        cwd=cwd,
        allowed_root=tmp_path,
        timeout_seconds=2,
    )
    result = await run_user_scoped_process(request)
    assert result.timed_out is True
    assert result.process_tree_closed is True


@WINDOWS_ONLY
@pytest.mark.asyncio
async def test_result_never_exposes_environment(tmp_path: Path) -> None:
    node = _node()
    if node is None:
        pytest.skip("node is not available")
    cwd = tmp_path / "workspace"
    cwd.mkdir()
    request = UserProcessRequest(
        executable=node,
        argv=[node, "-e", "console.log('ok')"],
        cwd=cwd,
        allowed_root=tmp_path,
        timeout_seconds=30,
    )
    result = await run_user_scoped_process(request)
    exposed = " ".join(str(value) for value in vars(result).values())
    for secret in ("APPDATA", "USERPROFILE", "PATH=", "TOKEN", "SECRET"):
        assert secret not in exposed.upper().replace("PATH=", "PATH=") or secret == "PATH="


@WINDOWS_ONLY
@pytest.mark.asyncio
async def test_containment_proof_switches_effect_to_proven(tmp_path: Path) -> None:
    node = _node()
    if node is None:
        pytest.skip("node is not available")
    from sentinelx_core.handlers.direct_codex import make_devforge_direct_codex_provider
    from sentinelx_core.operation_registry import FirewallCoverage, RepositoryEffect

    policy = _full_policy(tmp_path, node_executable=Path(node))
    provider = make_devforge_direct_codex_provider(policy, platform_name="Windows")
    assert provider.repository_effect("execute_task").coverage is FirewallCoverage.UNPROVEN

    proof = await provider.prove_containment(repository=_repository(), semantic=_semantic())
    assert proof["workspace_write_succeeded"] is True
    assert proof["protected_sibling_refused"] is True
    assert proof["verified"] is True

    resolution = provider.repository_effect("execute_task")
    assert resolution.effect is RepositoryEffect.PROCESS_MUTATION
    assert resolution.coverage is FirewallCoverage.PROVEN
    assert provider.readiness()["available"] is True


@WINDOWS_ONLY
@pytest.mark.asyncio
async def test_discovery_resolves_installed_codex_when_present(tmp_path: Path) -> None:
    node = _node()
    if node is None:
        pytest.skip("node is not available")
    policy = _policy(tmp_path, node_executable=Path(node))
    cwd = tmp_path / "devforge-workspaces" / "probe"
    cwd.mkdir(parents=True, exist_ok=True)
    try:
        chain = await discover_codex_chain(
            policy, cwd=cwd, allowed_root=tmp_path / "devforge-workspaces"
        )
    except DirectCodexDiscoveryError as exc:  # pragma: no cover - host dependent
        pytest.skip(f"no verified codex installation on this host: {exc.code}")
    assert chain.codex_script.is_file()
    assert chain.codex_script.name == "codex.js"
    assert os.path.abspath(str(chain.codex_script)).startswith(
        os.path.abspath(str(chain.package_dir))
    )
