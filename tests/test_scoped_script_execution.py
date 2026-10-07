from __future__ import annotations

import asyncio
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

import sentinelx_core.windows_mutation_sandbox as windows_sandbox
from sentinelx_core.executor import HandlerError
from sentinelx_core.handlers.devforge_runtime import make_devforge_execute_scoped_adapter
from sentinelx_core.handlers.mutation_scope import make_mutation_scope_handler
from sentinelx_core.handlers import scoped_script as scoped_script_handler
from sentinelx_core.handlers.scoped_script import make_profiled_script_run_handler
from sentinelx_core.mutation_audit import (
    EVENT_FINISHED,
    EVENT_SPAWNED,
    EVENT_STARTED,
    MutationAuditJournal,
)
from sentinelx_core.mutation_placement import RepositoryIdentity, SemanticIdentity
from sentinelx_core.mutation_scope import MutationScopeStore
from sentinelx_core.policy import MutationExecutionPolicy, Policy
from sentinelx_core.request_context import RequestContext
from sentinelx_core.windows_mutation_sandbox import WindowsMutationSandbox

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows scoped mutation only")


def _fixture(
    tmp_path: Path,
    *,
    attempt_id: str,
    interpreter: str = "python3",
    operation_classes: tuple[str, ...] = ("scoped_script",),
):
    workspace_root = tmp_path / "workspaces"
    state_root = tmp_path / "provider-state"
    upload_base = tmp_path / "uploads"
    protected = tmp_path / "protected"
    for path in (workspace_root, state_root, upload_base, protected):
        path.mkdir(parents=True, exist_ok=True)

    runtime_roots = {
        Path(sys.prefix).resolve(),
        Path(sys.base_prefix).resolve(),
    }
    if interpreter == "pwsh":
        executable = shutil.which("pwsh")
        if executable:
            runtime_roots.add(Path(executable).resolve().parent)

    mutation_policy = MutationExecutionPolicy(
        configured=True,
        scoped_mutation_enabled=True,
        workspace_root=workspace_root,
        protected_roots=(protected,),
        runtime_read_roots=tuple(sorted(runtime_roots, key=lambda p: str(p).casefold())),
        scope_ttl_seconds=600,
        evidence_retention_days=7,
        operator_unrestricted_enabled=False,
    )
    policy = Policy(mutation_execution=mutation_policy, upload_base=upload_base)
    repository = RepositoryIdentity(
        vcs="git",
        authority="github.com",
        path="bewaterhere-coder/sentinelx-cloud-core",
    )
    semantic = SemanticIdentity(
        project_id="sentinelx-cloud-core",
        task_id="PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1",
        run_id="s04-scoped-composition",
        attempt_id=attempt_id,
        slice_id="S04",
    )
    lineage = {
        "project_id": semantic.project_id,
        "task_id": semantic.task_id,
        "run_id": semantic.run_id,
        "attempt_id": semantic.attempt_id,
        "slice_id": semantic.slice_id,
    }
    repo = {"vcs": repository.vcs, "authority": repository.authority, "path": repository.path}
    store = MutationScopeStore(state_root)
    if operation_classes == ("scoped_script",):
        lifecycle = make_mutation_scope_handler(
            policy,
            upload_base,
            mutation_state_root=state_root,
        )
        lifecycle_context = RequestContext(
            request_id=f"scope-{attempt_id}",
            op="mutation_scope",
            opaque_ref="s04",
            received_at=datetime.now(UTC),
        )
        provisioned = asyncio.run(
            lifecycle(
                lifecycle_context,
                {
                    "action": "provision",
                    "purpose": "scoped_script",
                    "repository": repo,
                    "lineage": lineage,
                },
            )
        )
        scope = provisioned["scope"]
        record = store.read_scope(scope["scope_id"])
    else:
        record = store.provision_scope(
            mutation_policy,
            repository,
            semantic,
            allowed_operation_classes=operation_classes,
            provider_protected_roots=(state_root.resolve(),),
        )
    handler = make_profiled_script_run_handler(
        policy,
        upload_base,
        mutation_state_root=state_root,
    )
    context = RequestContext(
        request_id=f"req-{attempt_id}",
        op="script_run",
        opaque_ref="s04",
        received_at=datetime.now(UTC),
    )
    mutation = {
        "execution_profile": "scoped_mutation",
        "scope_ref": {"scope_id": record.scope_id, "generation": record.generation},
    }
    return handler, context, store, record, mutation, lineage, repo


def _run(handler, context, payload):
    return asyncio.run(handler(context, payload))


def test_python_runner_uses_base_interpreter_not_venv_launcher(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = tmp_path / "base" / "python.exe"
    base.parent.mkdir()
    base.write_text("", encoding="utf-8")
    monkeypatch.setattr(
        scoped_script_handler.sys,
        "_base_executable",
        str(base),
        raising=False,
    )

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    argv = scoped_script_handler._runner_argv(
        "python3",
        workspace / "script.py",
        [],
        workspace,
        workspace / "stdout.bin",
        workspace / "stderr.bin",
        workspace / "returncode.txt",
    )

    assert argv[0] == str(base)
    assert Path(argv[1]).name == "sentinelx_runner.py"


def test_scoped_python_preserves_unicode_cwd_and_drops_host_credentials(tmp_path: Path, monkeypatch) -> None:
    handler, context, store, record, mutation, lineage, repo = _fixture(
        tmp_path, attempt_id="python", interpreter="python3"
    )
    monkeypatch.setenv("GITHUB_TOKEN", "must-not-inherit")
    payload = {
        "interpreter": "python3",
        "content": (
            "import os\n"
            "print('臺灣 café 漢字')\n"
            "print('cwd=' + os.path.basename(os.getcwd()))\n"
            "print('credential=' + os.environ.get('GITHUB_TOKEN', '<none>'))\n"
            "print('custom=' + os.environ.get('S05_SAFE', '<none>'))\n"
        ),
        "args": [],
        "cwd": "subdir",
        "env": {"S05_SAFE": "preserved"},
        "timeout": 30,
        "cleanup": True,
        "mutation": mutation,
        "lineage": lineage,
        "repository": repo,
    }
    result = _run(handler, context, payload)
    assert result["ok"] is True
    assert result["execution_profile"] == "scoped_mutation"
    assert "臺灣 café 漢字" in result["output"]
    assert "cwd=subdir" in result["output"]
    assert "credential=<none>" in result["output"]
    assert "custom=preserved" in result["output"]
    assert result["terminal_state"] == "terminal"
    assert store.read_scope(record.scope_id).state == "terminal"
    events = MutationAuditJournal(store.root.parent, evidence_retention_days=7).read_events(
        result["audit_operation_id"]
    )
    assert [event["event"] for event in events] == [
        EVENT_STARTED, EVENT_SPAWNED, EVENT_FINISHED
    ]
    assert events[0]["authority"]["scope_digest"] == record.scope_digest
    assert events[0]["authority"]["protected_inventory_digest"] == record.protected_inventory_digest
    assert events[0]["process_intent"]["interpreter"] == "python3"
    assert events[0]["requested_identity"]["sandbox_kind"] == "appcontainer"
    assert events[1]["ppid"] > 0
    assert events[1]["os_identity"]["is_appcontainer"] is True
    assert events[1]["containment"]["breakaway_allowed"] is False
    assert events[2]["closure"]["scope_state"] == "terminal"
    assert events[2]["closure"]["process_tree_quiescent"] is True
    assert events[2]["closure"]["sandbox_write_authority_present"] is False


def test_scoped_powershell_preserves_unicode(tmp_path: Path) -> None:
    handler, context, _store, _record, mutation, lineage, repo = _fixture(
        tmp_path, attempt_id="powershell", interpreter="powershell"
    )
    try:
        result = _run(
            handler,
            context,
            {
                "interpreter": "powershell",
                "content": "Write-Output '臺灣 café 漢字'",
                "timeout": 30,
                "mutation": mutation,
                "lineage": lineage,
                "repository": repo,
            },
        )
    except HandlerError as exc:
        # Windows PowerShell 5.1 is not AppContainer-compatible on every Host.
        # That platform outcome must be explicit and fail closed, never fallback.
        assert exc.code == "HostMutationSandboxUnavailable"
        assert "required AppContainer" in str(exc)
        return
    assert result["ok"] is True
    assert "臺灣 café 漢字" in result["output"]


def test_scoped_pwsh_preserves_unicode_when_installed(tmp_path: Path) -> None:
    if shutil.which("pwsh") is None:
        pytest.skip("pwsh is not installed on this Windows host")
    handler, context, _store, _record, mutation, lineage, repo = _fixture(
        tmp_path, attempt_id="pwsh", interpreter="pwsh"
    )
    result = _run(
        handler,
        context,
        {
            "interpreter": "pwsh",
            "content": "Write-Output '臺灣 café 漢字'",
            "timeout": 30,
            "mutation": mutation,
            "lineage": lineage,
            "repository": repo,
        },
    )
    assert result["ok"] is True
    assert "臺灣 café 漢字" in result["output"]


def test_scoped_rejects_elevation_absolute_cwd_and_authority_env(tmp_path: Path) -> None:
    cases = [
        ("sudo", {"sudo": True}),
        ("cwd", {"cwd": str(tmp_path / "outside")}),
        ("env", {"env": {"GITHUB_TOKEN": "caller-token"}}),
    ]
    for name, extra in cases:
        case_root = tmp_path / name
        handler, context, store, record, mutation, lineage, repo = _fixture(
            case_root, attempt_id=name, interpreter="python3"
        )
        payload = {
            "interpreter": "python3",
            "content": "print('must not escape')",
            "timeout": 30,
            "mutation": mutation,
            "lineage": lineage,
            "repository": repo,
            **extra,
        }
        with pytest.raises(HandlerError):
            _run(handler, context, payload)
        current = store.read_scope(record.scope_id)
        if name in {"sudo", "cwd"}:
            # Rejected before durable START/materialization; no authority was activated.
            assert current.state == "provisioned"
        else:
            assert current.state in {"terminal", "revoked"}


@pytest.mark.parametrize("binding", ["repository", "lineage"])
def test_lifecycle_scope_requires_exact_repository_and_lineage_before_materialization(
    tmp_path: Path, binding: str
) -> None:
    handler, context, store, record, mutation, lineage, repo = _fixture(
        tmp_path / binding, attempt_id=f"binding-{binding}", interpreter="python3"
    )
    wrong_repo = dict(repo)
    wrong_lineage = dict(lineage)
    if binding == "repository":
        wrong_repo["path"] = "bewaterhere-coder/not-the-issued-repository"
    else:
        wrong_lineage["attempt_id"] = "not-the-issued-attempt"

    with pytest.raises(HandlerError) as exc_info:
        _run(
            handler,
            context,
            {
                "interpreter": "python3",
                "content": "print('must not materialize')",
                "timeout": 30,
                "mutation": mutation,
                "lineage": wrong_lineage,
                "repository": wrong_repo,
            },
        )
    assert exc_info.value.code == "HostMutationScopeBindingMismatch"
    assert store.read_scope(record.scope_id).state == "provisioned"
    assert not Path(record.exact_workspace).exists()
    assert MutationAuditJournal(store.root.parent, evidence_retention_days=7).read_events() == []


def test_lifecycle_scope_timeout_terminalizes_authority(tmp_path: Path) -> None:
    handler, context, store, record, mutation, lineage, repo = _fixture(
        tmp_path, attempt_id="timeout-terminal", interpreter="python3"
    )
    result = _run(
        handler,
        context,
        {
            "interpreter": "python3",
            "content": "import time\ntime.sleep(5)\n",
            "timeout": 1,
            "mutation": mutation,
            "lineage": lineage,
            "repository": repo,
        },
    )
    assert result["timed_out"] is True
    assert result["returncode"] == -1
    current = store.read_scope(record.scope_id)
    assert current.state == "terminal"
    assert not current.active_job_ids
    assert not current.active_process_ids
    assert not current.sandbox_write_authority_present
    events = MutationAuditJournal(store.root.parent, evidence_retention_days=7).read_events(
        result["audit_operation_id"]
    )
    assert [event["event"] for event in events] == [EVENT_STARTED, EVENT_SPAWNED, EVENT_FINISHED]
    assert events[-1]["status"] == "timeout"
    assert events[-1]["closure"]["scope_state"] == "terminal"
    assert events[-1]["closure"]["process_tree_quiescent"] is True


def test_lifecycle_scope_nonzero_failure_terminalizes_authority(tmp_path: Path) -> None:
    handler, context, store, record, mutation, lineage, repo = _fixture(
        tmp_path, attempt_id="nonzero-terminal", interpreter="python3"
    )
    result = _run(
        handler,
        context,
        {
            "interpreter": "python3",
            "content": "raise SystemExit(7)\n",
            "timeout": 30,
            "mutation": mutation,
            "lineage": lineage,
            "repository": repo,
        },
    )
    assert result["ok"] is False
    assert result["returncode"] == 7
    assert result["terminal_state"] == "terminal"
    current = store.read_scope(record.scope_id)
    assert current.state == "terminal"
    assert not current.active_job_ids
    assert not current.active_process_ids
    assert not current.sandbox_write_authority_present
    events = MutationAuditJournal(store.root.parent, evidence_retention_days=7).read_events(
        result["audit_operation_id"]
    )
    assert [event["event"] for event in events] == [EVENT_STARTED, EVENT_SPAWNED, EVENT_FINISHED]
    assert events[-1]["status"] == "failed"
    assert events[-1]["returncode"] == 7
    assert events[-1]["closure"]["scope_state"] == "terminal"


def test_scoped_failure_never_falls_back_to_unrestricted(tmp_path: Path) -> None:
    handler, context, _store, record, mutation, lineage, repo = _fixture(
        tmp_path, attempt_id="no-fallback", interpreter="python3"
    )
    marker = tmp_path / "outside-marker.txt"
    bad_mutation = dict(mutation)
    bad_mutation["scope_ref"] = {"scope_id": "caller-minted", "generation": record.generation}
    payload = {
        "interpreter": "python3",
        "content": f"from pathlib import Path\nPath(r'{marker}').write_text('fallback-ran')",
        "timeout": 30,
        "mutation": bad_mutation,
        "lineage": lineage,
        "repository": repo,
    }
    with pytest.raises(HandlerError):
        _run(handler, context, payload)
    assert not marker.exists()


def test_operator_unrestricted_requires_explicit_opt_in(tmp_path: Path) -> None:
    mutation_policy = MutationExecutionPolicy(configured=True, operator_unrestricted_enabled=False)
    policy = Policy(mutation_execution=mutation_policy, upload_base=tmp_path / "uploads")
    handler = make_profiled_script_run_handler(policy, policy.upload_base, mutation_state_root=tmp_path / "state")
    context = RequestContext("req-op", "script_run", None, datetime.now(UTC))
    with pytest.raises(HandlerError, match="explicit Host policy opt-in"):
        _run(
            handler,
            context,
            {
                "execution_profile": "operator_unrestricted",
                "interpreter": "python3",
                "content": "print('no')",
            },
        )


def test_terminalization_failure_prevents_success_and_successful_finish(
    tmp_path: Path, monkeypatch
) -> None:
    handler, context, store, _record, mutation, lineage, repo = _fixture(
        tmp_path, attempt_id="terminalization-failure", interpreter="python3"
    )

    def fail_terminalize(self, scope_id, generation):
        raise RuntimeError("injected closure read-back failure")

    monkeypatch.setattr(WindowsMutationSandbox, "terminalize", fail_terminalize)
    with pytest.raises(HandlerError, match="injected closure read-back failure"):
        _run(
            handler,
            context,
            {
                "interpreter": "python3",
                "content": "print('ran but must not be reported successful')",
                "timeout": 30,
                "mutation": mutation,
                "lineage": lineage,
                "repository": repo,
            },
        )

    journal = MutationAuditJournal(store.root.parent, evidence_retention_days=7)
    events = journal.read_events()
    kinds = [event["event"] for event in events]
    assert kinds == [EVENT_STARTED, EVENT_SPAWNED]
    assert EVENT_FINISHED not in kinds


def test_scoped_requires_durable_operation_class_before_audit_or_materialization(
    tmp_path: Path,
) -> None:
    handler, context, store, record, mutation, lineage, repo = _fixture(
        tmp_path,
        attempt_id="operation-class-denied",
        interpreter="python3",
        operation_classes=("different_operation",),
    )
    with pytest.raises(HandlerError) as exc_info:
        _run(
            handler,
            context,
            {
                "interpreter": "python3",
                "content": "print('must not run')",
                "timeout": 30,
                "mutation": mutation,
                "lineage": lineage,
                "repository": repo,
            },
        )
    assert exc_info.value.code == "HostMutationScopeOperationNotAllowed"
    assert store.read_scope(record.scope_id).state == "provisioned"
    assert not Path(record.exact_workspace).exists()
    events = MutationAuditJournal(store.root.parent, evidence_retention_days=7).read_events()
    assert events == []


def test_devforge_execute_scoped_adapter_reuses_existing_executor(tmp_path: Path) -> None:
    handler, _script_context, store, record, mutation, lineage, repo = _fixture(
        tmp_path, attempt_id="devforge-adapter", interpreter="python3"
    )
    adapter = make_devforge_execute_scoped_adapter(handler)
    local_context = RequestContext(
        request_id="req-devforge-adapter",
        op="local_api",
        opaque_ref="s07",
        received_at=datetime.now(UTC),
    )
    result = asyncio.run(
        adapter(
            local_context,
            {
                "scope_ref": mutation["scope_ref"],
                "repository": repo,
                "lineage": lineage,
                "execution_profile": "scoped_mutation",
                "interpreter": "python3",
                "content": "print('devforge-s07-marker')",
                "timeout": 30,
            },
        )
    )
    assert result["ok"] is True
    assert result["execution_profile"] == "scoped_mutation"
    assert result["terminal_state"] == "terminal"
    assert "devforge-s07-marker" in result["output"]
    assert "cwd" not in result
    assert "command" not in result
    assert "script_path" not in result
    assert "workdir" not in result
    assert store.read_scope(record.scope_id).state == "terminal"


def test_activation_residual_runtime_authority_never_false_terminal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    handler, context, store, record, mutation, lineage, repo = _fixture(
        tmp_path,
        attempt_id="activation-residual-runtime-authority",
        interpreter="python3",
    )

    def residual_grant(*_args, **_kwargs):
        raise windows_sandbox.HostMutationSandboxResidualAuthority(
            "injected grant compensation ambiguity"
        )

    def residual_cleanup(*_args, **_kwargs):
        raise windows_sandbox.HostMutationSandboxResidualAuthority(
            "injected cleanup ambiguity"
        )

    monkeypatch.setattr(windows_sandbox, "_grant_runtime_read", residual_grant)
    monkeypatch.setattr(windows_sandbox, "_remove_runtime_read", residual_cleanup)

    with pytest.raises(HandlerError) as exc_info:
        _run(
            handler,
            context,
            {
                "interpreter": "python3",
                "content": "print('must not spawn')",
                "timeout": 30,
                "mutation": mutation,
                "lineage": lineage,
                "repository": repo,
            },
        )
    assert exc_info.value.code == "HostMutationSandboxResidualAuthority"

    current = store.read_scope(record.scope_id)
    assert current.state == "revoked"
    assert current.runtime_read_authority_roots
    assert current.terminalized_at is None

    events = MutationAuditJournal(store.root.parent, evidence_retention_days=7).read_events()
    assert [event["event"] for event in events] == [EVENT_STARTED]
    assert EVENT_FINISHED not in [event["event"] for event in events]
