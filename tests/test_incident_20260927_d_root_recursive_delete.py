from __future__ import annotations

import asyncio
import hashlib
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

from sentinelx_core.executor import HandlerError
from sentinelx_core.handlers.basic import make_capabilities_handler
from sentinelx_core.handlers.mutation_scope import make_mutation_scope_handler
from sentinelx_core.handlers.scoped_script import make_profiled_script_run_handler
from sentinelx_core.mutation_placement import RepositoryIdentity, SemanticIdentity
from sentinelx_core.mutation_readiness import probe_mutation_runtime
from sentinelx_core.mutation_scope import MutationScopeStore
from sentinelx_core.policy import MutationExecutionPolicy, Policy
from sentinelx_core.request_context import RequestContext

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows V1 incident regression")
INCIDENT = "INCIDENT-20260927-D-ROOT-RECURSIVE-DELETE"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_root(tmp_path: Path) -> Path:
    root = (tmp_path / INCIDENT).resolve()
    real_workspace = Path(r"D:\coco").resolve(strict=False)
    assert not root.is_relative_to(real_workspace), "destructive fixture must never live under D:\\coco"
    root.mkdir(parents=True)
    return root


def _layout(tmp_path: Path):
    root = _safe_root(tmp_path)
    workspace_root = root / "workspace-root"
    sibling = workspace_root / "sibling-workspace"
    canonical_repo = root / "canonical-repo"
    personal_project = root / "personal-project"
    parent_sentinel = root / "parent-sentinel"
    state_root = root / "state"
    upload_base = root / "uploads"
    for path in (
        workspace_root,
        sibling,
        canonical_repo,
        personal_project,
        parent_sentinel,
        state_root,
        upload_base,
    ):
        path.mkdir(parents=True, exist_ok=True)

    sentinels = {
        sibling / "MUST_SURVIVE": b"sibling-workspace\n",
        canonical_repo / "MUST_SURVIVE": b"canonical-repo\n",
        personal_project / "MUST_SURVIVE": b"personal-project\n",
        parent_sentinel / "MUST_SURVIVE": b"parent-sentinel\n",
    }
    for path, body in sentinels.items():
        path.write_bytes(body)

    git = shutil.which("git")
    assert git, "canonical git-clean regression requires git on the Windows validation host"
    subprocess.run([git, "init", "-q", str(canonical_repo)], check=True)

    runtime_roots = (
        Path(sys.prefix).resolve(),
        Path(sys.base_prefix).resolve(),
    )
    mutation_policy = MutationExecutionPolicy(
        configured=True,
        scoped_mutation_enabled=True,
        workspace_root=workspace_root,
        protected_roots=(canonical_repo, personal_project, parent_sentinel),
        runtime_read_roots=runtime_roots,
        scope_ttl_seconds=600,
        evidence_retention_days=7,
        operator_unrestricted_enabled=False,
    )
    policy = Policy(mutation_execution=mutation_policy, upload_base=upload_base)
    repository = RepositoryIdentity(
        vcs="git", authority="github.com", path="bewaterhere-coder/sentinelx-cloud-core"
    )
    before = {path: _sha(path) for path in sentinels}
    return {
        "root": root,
        "workspace_root": workspace_root,
        "sibling": sibling,
        "canonical_repo": canonical_repo,
        "personal_project": personal_project,
        "parent_sentinel": parent_sentinel,
        "state_root": state_root,
        "upload_base": upload_base,
        "sentinels": sentinels,
        "before": before,
        "policy": policy,
        "repository": repository,
        "git": git,
    }


def _assert_protected(layout) -> None:
    for path, digest in layout["before"].items():
        assert path.exists(), f"protected sentinel disappeared: {path}"
        assert _sha(path) == digest, f"protected sentinel changed: {path}"


def _scoped_case(layout, name: str, interpreter: str, content: str, *, delay: float = 0.0):
    policy: Policy = layout["policy"]
    repository: RepositoryIdentity = layout["repository"]
    semantic = SemanticIdentity(
        project_id="sentinelx-cloud-core",
        task_id="SX-HMSA-001",
        run_id="s06-incident-regression",
        attempt_id=name,
        slice_id="S06",
    )
    store = MutationScopeStore(layout["state_root"])
    repository_payload = {
        "vcs": repository.vcs,
        "authority": repository.authority,
        "path": repository.path,
    }
    lineage_payload = {
        "project_id": semantic.project_id,
        "task_id": semantic.task_id,
        "run_id": semantic.run_id,
        "attempt_id": semantic.attempt_id,
        "slice_id": semantic.slice_id,
    }
    lifecycle = make_mutation_scope_handler(
        policy,
        layout["upload_base"],
        mutation_state_root=layout["state_root"],
    )
    lifecycle_context = RequestContext(
        request_id=f"s06-scope-{name}",
        op="mutation_scope",
        opaque_ref=INCIDENT,
        received_at=datetime.now(UTC),
    )
    provisioned = asyncio.run(
        lifecycle(
            lifecycle_context,
            {
                "action": "provision",
                "purpose": "scoped_script",
                "repository": repository_payload,
                "lineage": lineage_payload,
            },
        )
    )
    scope = provisioned["scope"]
    handler = make_profiled_script_run_handler(
        policy,
        layout["upload_base"],
        mutation_state_root=layout["state_root"],
    )
    context = RequestContext(
        request_id=f"s06-{name}",
        op="script_run",
        opaque_ref=INCIDENT,
        received_at=datetime.now(UTC),
    )
    payload = {
        "interpreter": interpreter,
        "content": content,
        "timeout": 30,
        "cleanup": False,
        "mutation": {
            "execution_profile": "scoped_mutation",
            "scope_ref": {"scope_id": scope["scope_id"], "generation": scope["generation"]},
        },
        "lineage": lineage_payload,
        "repository": repository_payload,
    }
    try:
        result = asyncio.run(handler(context, payload))
        assert result["execution_profile"] == "scoped_mutation"
        if result.get("timed_out"):
            assert result["returncode"] == -1
        else:
            assert result["terminal_state"] == "terminal"
    except HandlerError as exc:
        assert exc.code.startswith("HostMutationSandbox") or exc.code == "interpreter_missing"
        result = {"blocked": exc.code}
    if delay:
        time.sleep(delay)
    _assert_protected(layout)
    inspected = asyncio.run(
        lifecycle(
            lifecycle_context,
            {
                "action": "inspect",
                "scope_ref": {"scope_id": scope["scope_id"], "generation": scope["generation"]},
                "repository": repository_payload,
                "lineage": lineage_payload,
            },
        )
    )
    assert inspected["scope"]["state"] in {"terminal", "revoked"}
    current = store.read_scope(scope["scope_id"])
    assert inspected["scope"]["scope_digest"] == current.scope_digest
    assert not current.active_job_ids
    assert not current.active_process_ids
    assert not current.sandbox_write_authority_present
    return result


def _py_targets(paths: list[Path]) -> str:
    return repr([str(path) for path in paths])


def _ps(value: Path) -> str:
    return str(value).replace("'", "''")


def test_incident_20260927_destructive_escape_matrix(tmp_path: Path) -> None:
    layout = _layout(tmp_path)
    target_dirs = [
        layout["sibling"],
        layout["canonical_repo"],
        layout["personal_project"],
        layout["parent_sentinel"],
    ]

    baseline = _scoped_case(
        layout,
        "baseline-admitted-write",
        "python3",
        "from pathlib import Path\nPath('ALLOWED_MUTATION').write_text('ok', encoding='utf-8')\n",
    )
    assert baseline.get("ok") is True
    assert (Path(baseline["workdir"]) / "ALLOWED_MUTATION").read_text(encoding="utf-8") == "ok"

    _scoped_case(
        layout,
        "python-shutil-rmtree",
        "python3",
        "import shutil\n"
        f"targets={_py_targets(target_dirs)}\n"
        "for target in targets:\n"
        "    try: shutil.rmtree(target)\n"
        "    except Exception: pass\n"
        "from pathlib import Path\nPath('ATTEMPTED').write_text('python')\n",
    )

    _scoped_case(
        layout,
        "cmd-rmdir",
        "python3",
        "import subprocess\n"
        f"targets={_py_targets(target_dirs)}\n"
        "for target in targets:\n"
        "    subprocess.run(['cmd','/c','rmdir','/s','/q',target], capture_output=True)\n",
    )

    ps_targets = ",".join(f"'{_ps(path)}'" for path in target_dirs)
    _scoped_case(
        layout,
        "powershell-remove-item",
        "powershell",
        f"$targets=@({ps_targets})\n"
        "foreach($p in $targets){ Remove-Item -LiteralPath $p -Recurse -Force -ErrorAction SilentlyContinue }\n"
        "Set-Content -LiteralPath '.\\ATTEMPTED' -Value 'powershell'\n",
    )

    _scoped_case(
        layout,
        "dotnet-directory-delete",
        "powershell",
        f"$targets=@({ps_targets})\n"
        "foreach($p in $targets){ try { [System.IO.Directory]::Delete($p,$true) } catch {} }\n",
    )

    sentinel_files = list(layout["sentinels"].keys())
    _scoped_case(
        layout,
        "win32-delete-file",
        "python3",
        "import ctypes\n"
        f"targets={_py_targets(sentinel_files)}\n"
        "for target in targets:\n"
        "    ctypes.windll.kernel32.DeleteFileW(str(target))\n",
    )

    _scoped_case(
        layout,
        "child-process-delete",
        "python3",
        "import subprocess,sys\n"
        f"targets={_py_targets(target_dirs)}\n"
        "code='import shutil,sys\\ntry: shutil.rmtree(sys.argv[1])\\nexcept Exception: pass'\n"
        "for target in targets:\n"
        "    subprocess.run([sys.executable,'-c',code,target], capture_output=True)\n",
    )

    detached_target = str(layout["canonical_repo"])
    _scoped_case(
        layout,
        "detached-background-delete",
        "python3",
        "import subprocess\n"
        f"target={detached_target!r}\n"
        "command='ping 127.0.0.1 -n 3 >nul & rmdir /s /q \"' + target + '\"'\n"
        "subprocess.Popen(['cmd','/c',command], creationflags=0x00000008|0x00000200, "
        "stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n",
        delay=3.0,
    )

    junction_target = str(layout["canonical_repo"])
    _scoped_case(
        layout,
        "junction-escape",
        "python3",
        "from pathlib import Path\nimport subprocess\n"
        f"target={junction_target!r}\n"
        "junction=Path.cwd()/'escape-junction'\n"
        "subprocess.run(['cmd','/c','mklink','/J',str(junction),target], capture_output=True)\n"
        "try: (junction/'MUST_SURVIVE').unlink()\n"
        "except Exception: pass\n",
    )

    move_target = str(layout["personal_project"])
    _scoped_case(
        layout,
        "move-rename-escape",
        "python3",
        "from pathlib import Path\nimport os\n"
        f"target={move_target!r}\n"
        "try: os.replace(target, str(Path.cwd()/'moved-protected'))\n"
        "except Exception: pass\n",
    )

    git_target = str(layout["canonical_repo"])
    git_exe = str(layout["git"])
    _scoped_case(
        layout,
        "git-clean-protected",
        "python3",
        "import subprocess\n"
        f"git={git_exe!r}\n"
        f"target={git_target!r}\n"
        "subprocess.run([git,'-C',target,'clean','-fdx'], capture_output=True)\n",
    )

    _assert_protected(layout)


def test_runtime_self_check_gates_capability_advertisement(tmp_path: Path) -> None:
    layout = _layout(tmp_path)
    readiness = probe_mutation_runtime(
        layout["policy"].mutation_execution,
        layout["state_root"],
        force=True,
    )
    assert readiness.available, readiness.reason
    assert all(readiness.checks.values()), readiness.checks

    handler = make_capabilities_handler(
        layout["policy"],
        ops_supported=lambda: ("script_run", "capabilities"),
        upload_base=layout["upload_base"],
    )
    result = asyncio.run(handler({"detail": "full"}))
    features = result["execution_features"]
    assert features["host_mutation_sandbox_v1"]["available"] is True
    assert features["host_mutation_sandbox_v1"]["verified"] is True
    assert features["pre_execution_audit_lineage_v1"]["available"] is True
    assert features["pre_execution_audit_lineage_v1"]["verified"] is True
