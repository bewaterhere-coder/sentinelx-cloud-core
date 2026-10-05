"""S05 scoped ``script_run`` integration.

This module deliberately wraps the historical script handler rather than
changing it.  Legacy execution therefore keeps its old byte/argv/output
semantics, while ``scoped_mutation`` takes a separate fail-closed path bound to
provider-owned scope, audit and Windows AppContainer authority.
"""
from __future__ import annotations

import asyncio
import hashlib
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from sentinelx_core.executor import HandlerError
from sentinelx_core.handlers.script import (
    PreparedMutationScript,
    TIMEOUT_MAX,
    TIMEOUT_MIN,
    _decode_output,
    _scoped_script_bytes,
    prepare_scoped_script_evidence,
)
from sentinelx_core.handlers.script import (
    make_script_run_handler as make_legacy_script_run_handler,
)
from sentinelx_core.mutation_audit import (
    MutationAuditJournal,
    MutationAuditStart,
    MutationAuditBinding,
    MutationAuthorityEvidence,
    MutationFinishClosureEvidence,
    MutationProcessIntent,
)
from sentinelx_core.mutation_placement import RepositoryIdentity, SemanticIdentity
from sentinelx_core.mutation_sandbox import build_mutation_sandbox
from sentinelx_core.mutation_scope import (
    SCOPED_SCRIPT_OPERATION_CLASS,
    MutationScopeRecord,
    MutationScopeStore,
)
from sentinelx_core.policy import Policy
from sentinelx_core.request_context import MutationLineage, RequestContext, context_aware
from sentinelx_core.verification_execution import (
    build_verification_environment,
    planned_verification_cwd,
    prepare_verification_execution,
    revalidate_verification_after_run,
    validate_verification_environment_request,
    verification_cwd,
    verification_cwd_label,
    verification_evidence,
)
from sentinelx_core.windows_mutation_sandbox import (
    final_executable_path,
    requested_mutation_identity,
)

_AUTHORITY_ENV_PREFIXES = (
    "SENTINELX_",
    "GIT_",
    "GH_",
    "GITHUB_",
    "GITLAB_",
    "SSH_",
)
_AUTHORITY_ENV_WORDS = ("TOKEN", "PASSWORD", "SECRET", "CREDENTIAL", "API_KEY")
_AUTHORITY_ENV_EXACT = frozenset(
    {"HOME", "USERPROFILE", "HOMEDRIVE", "HOMEPATH", "APPDATA", "LOCALAPPDATA"}
)


def _profile(payload: dict[str, Any]) -> str | None:
    mutation = payload.get("mutation")
    nested = mutation.get("execution_profile") if isinstance(mutation, dict) else None
    direct = payload.get("execution_profile")
    if nested is not None and direct is not None and nested != direct:
        raise HandlerError("invalid_payload", "conflicting execution_profile values")
    value = nested if nested is not None else direct
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise HandlerError("invalid_payload", "execution_profile must be a non-empty string")
    return value.strip()


def _authority(
    payload: dict[str, Any],
) -> tuple[str, int, MutationLineage, RepositoryIdentity, SemanticIdentity]:
    mutation = payload.get("mutation")
    if not isinstance(mutation, dict):
        raise HandlerError("invalid_payload", "scoped_mutation requires a mutation mapping")
    scope_ref = mutation.get("scope_ref")
    if isinstance(scope_ref, dict):
        scope_id = scope_ref.get("scope_id")
        generation = scope_ref.get("generation", mutation.get("scope_generation"))
    else:
        scope_id = scope_ref
        generation = mutation.get("scope_generation")
    if not isinstance(scope_id, str) or not scope_id.strip():
        raise HandlerError("invalid_payload", "scoped_mutation requires mutation.scope_ref.scope_id")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation <= 0:
        raise HandlerError("invalid_payload", "scoped_mutation requires a positive scope generation")
    try:
        lineage = MutationLineage.from_mapping(payload.get("lineage"))
    except ValueError as exc:
        raise HandlerError("HostMutationAuditLineageInvalid", str(exc)) from exc
    raw_repository = payload.get("repository")
    if not isinstance(raw_repository, dict):
        raise HandlerError("invalid_payload", "scoped_mutation requires repository identity")
    try:
        repository = RepositoryIdentity(
            vcs=str(raw_repository.get("vcs") or ""),
            authority=str(raw_repository.get("authority") or ""),
            path=str(raw_repository.get("path") or ""),
        )
        _ = repository.canonical
    except ValueError as exc:
        raise HandlerError("invalid_payload", str(exc)) from exc
    semantic = SemanticIdentity(
        project_id=lineage.project_id,
        task_id=lineage.task_id,
        run_id=lineage.run_id,
        attempt_id=lineage.attempt_id,
        slice_id=lineage.slice_id,
    )
    return scope_id.strip(), generation, lineage, repository, semantic


def _credential_like(key: str) -> bool:
    upper = key.upper()
    return (
        upper in _AUTHORITY_ENV_EXACT
        or any(upper.startswith(prefix) for prefix in _AUTHORITY_ENV_PREFIXES)
        or any(word in upper for word in _AUTHORITY_ENV_WORDS)
    )


def _scoped_environment(extra: dict[str, str], workspace: Path) -> dict[str, str]:
    """Build a child environment without broker profile/Git/secret authority."""
    result = {key: value for key, value in os.environ.items() if not _credential_like(key)}

    profile = workspace / ".sandbox-profile"
    local = profile / "AppData" / "Local"
    roaming = profile / "AppData" / "Roaming"
    local.mkdir(parents=True, exist_ok=True)
    roaming.mkdir(parents=True, exist_ok=True)
    profile_text = str(profile)
    result.update(
        {
            "HOME": profile_text,
            "USERPROFILE": profile_text,
            "HOMEDRIVE": workspace.drive or os.environ.get("SystemDrive", "C:"),
            "HOMEPATH": profile_text[2:] if len(profile_text) >= 2 and profile_text[1:2] == ":" else profile_text,
            "APPDATA": str(roaming),
            "LOCALAPPDATA": str(local),
        }
    )
    for key, value in extra.items():
        if _credential_like(key):
            raise HandlerError(
                "HostMutationSandboxBindingMismatch",
                f"scoped environment key {key!r} may carry authority or credentials",
            )
        result[key] = value
    return result


def _cwd(workspace: Path, value: Any, *, materialize: bool = True) -> Path:
    if value in (None, "", "."):
        return workspace
    if not isinstance(value, str):
        raise HandlerError("invalid_payload", "scoped cwd must be a relative path")
    relative = Path(value)
    if relative.is_absolute() or any(part == ".." for part in relative.parts):
        raise HandlerError(
            "HostMutationSandboxPathViolation",
            "scoped cwd must remain provider-derived inside the exact workspace",
        )
    target = (workspace / relative).resolve(strict=False)
    try:
        target.relative_to(workspace.resolve(strict=False))
    except ValueError as exc:
        raise HandlerError("HostMutationSandboxPathViolation", "scoped cwd escaped exact workspace") from exc
    if materialize:
        target.mkdir(parents=True, exist_ok=True)
    return target


def _runner_argv(
    interpreter: str,
    script_path: Path,
    args: list[str],
    workspace: Path,
    stdout_path: Path,
    stderr_path: Path,
    result_path: Path,
    *,
    materialize: bool = True,
    runner_cwd: Path | None = None,
) -> list[str]:
    """Create an in-sandbox runner that persists exit status before process close."""
    if interpreter == "bash":
        raise HandlerError(
            "HostMutationSandboxUnavailable",
            "scoped bash is outside the Windows V1 interpreter contract",
        )
    if interpreter == "python3":
        executable = Path(sys.executable)
        if executable.name.lower() == "pythonw.exe":
            executable = executable.with_name("python.exe")
        runner = workspace / "sentinelx_runner.py"
        if materialize:
            runner.write_text(
                "import contextlib, runpy, sys, traceback\n"
            "target,out_path,err_path,result_path,*script_args=sys.argv[1:]\n"
            "sys.argv=[target,*script_args]\n"
            "code=0\n"
            "with open(out_path,'w',encoding='utf-8',errors='replace') as out, open(err_path,'w',encoding='utf-8',errors='replace') as err:\n"
            "  with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):\n"
            "    try: runpy.run_path(target,run_name='__main__')\n"
            "    except SystemExit as exc: code=exc.code if isinstance(exc.code,int) else (0 if exc.code is None else 1)\n"
            "    except BaseException: traceback.print_exc(); code=1\n"
            "open(result_path,'w',encoding='ascii').write(str(code))\n"
            "raise SystemExit(code)\n",
                encoding="utf-8",
            )
        return [
            str(executable), str(runner), str(script_path), str(stdout_path),
            str(stderr_path), str(result_path), *args,
        ]

    executable = shutil.which(interpreter)
    if not executable:
        raise HandlerError("interpreter_missing", f"interpreter not found: {interpreter}")
    runner = workspace / "sentinelx_runner.ps1"
    cwd_parameter = ",[string]$WorkingDirectory" if runner_cwd is not None else ""
    cwd_binding = (
        " $ExecutionContext.SessionState.Path.SetLocation($WorkingDirectory)\n"
        if runner_cwd is not None
        else ""
    )
    if materialize:
        runner_text = "".join(
            (
                f"param([string]$Target,[string]$Stdout,[string]$Stderr,[string]$Result{cwd_parameter},[Parameter(ValueFromRemainingArguments=$true)][string[]]$ScriptArgs)\n",
                "$ErrorActionPreference='Stop'\n",
                "$utf8=New-Object System.Text.UTF8Encoding($false)\n",
                "try {\n",
                cwd_binding,
                " $text=[System.IO.File]::ReadAllText($Target,$utf8); $sb=[ScriptBlock]::Create($text)\n",
                " $global:LASTEXITCODE=$null; $records=& $sb @ScriptArgs *>&1; $ok=$?\n",
                " if($null -ne $LASTEXITCODE){$code=[int]$LASTEXITCODE}elseif($ok){$code=0}else{$code=1}\n",
                " $records|Out-File -LiteralPath $Stdout -Encoding utf8\n",
                " [System.IO.File]::WriteAllText($Stderr,'',$utf8)\n",
                " [System.IO.File]::WriteAllText($Result,[string]$code,[System.Text.Encoding]::ASCII)\n",
                " exit $code\n",
                "} catch {\n",
                " [System.IO.File]::WriteAllText($Stderr,($_|Out-String),$utf8)\n",
                " [System.IO.File]::WriteAllText($Result,'1',[System.Text.Encoding]::ASCII); exit 1\n",
                "}\n",
            )
        )
        runner.write_text(
            runner_text,
            encoding="utf-8-sig" if interpreter == "powershell" else "utf-8",
        )
    return [
        executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
        "-File", str(runner), str(script_path), str(stdout_path), str(stderr_path),
        str(result_path), *([str(runner_cwd)] if runner_cwd is not None else []), *args,
    ]


def _authority_evidence(record: MutationScopeRecord) -> MutationAuthorityEvidence:
    return MutationAuthorityEvidence(
        scope_digest=record.scope_digest,
        exact_workspace_digest=record.exact_workspace_digest,
        protected_inventory_digest=record.protected_inventory_digest,
        policy_digest=record.policy_digest,
        repository_identity_digest=record.repository_identity_digest,
        semantic_identity_digest=record.semantic_identity_digest,
    )


def _finish_closure(
    record: MutationScopeRecord, process: Any = None
) -> MutationFinishClosureEvidence:
    job_binding = process.job_ref if process is not None else None
    root_pid = process.pid if process is not None else None
    job_handle_closed = process.job_handle_closed if process is not None else True
    job_active_process_count = process.active_process_count if process is not None else 0
    return MutationFinishClosureEvidence(
        scope_state=record.state,
        scope_digest=record.scope_digest,
        protected_inventory_digest=record.protected_inventory_digest,
        sandbox_identity=record.sandbox_identity,
        job_binding=job_binding,
        root_pid=root_pid,
        job_handle_closed=job_handle_closed,
        job_active_process_count=job_active_process_count,
        active_job_ids=record.active_job_ids,
        active_process_ids=record.active_process_ids,
        sandbox_write_authority_present=record.sandbox_write_authority_present,
        process_tree_quiescent=(
            job_handle_closed
            and job_active_process_count == 0
            and not record.active_job_ids
            and not record.active_process_ids
        ),
        terminalized_at=record.terminalized_at or "",
    )


async def _run_scoped(
    *, context: RequestContext, payload: dict[str, Any], policy: Policy, state_root: Path
) -> dict[str, Any]:
    if sys.platform != "win32":
        raise HandlerError("HostMutationSandboxUnavailable", "scoped_mutation V1 requires Windows AppContainer")
    if bool(payload.get("sudo", False)):
        raise HandlerError("HostMutationSandboxBindingMismatch", "sudo/elevation is forbidden in scoped_mutation")
    if bool(payload.get("background", False)):
        raise HandlerError("HostMutationSandboxUnavailable", "scoped background execution is not enabled")

    args = payload.get("args") or []
    env_extra = payload.get("env") or {}
    if not isinstance(args, list) or not all(isinstance(value, str) for value in args):
        raise HandlerError("invalid_payload", "'args' must be a list of strings")
    if not isinstance(env_extra, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in env_extra.items()
    ):
        raise HandlerError("invalid_payload", "'env' must be dict[str, str]")
    try:
        timeout = int(payload.get("timeout", 60))
    except (TypeError, ValueError) as exc:
        raise HandlerError("invalid_payload", "timeout must be an integer") from exc
    if timeout < TIMEOUT_MIN or timeout > TIMEOUT_MAX:
        raise HandlerError("invalid_payload", f"timeout must be between {TIMEOUT_MIN} and {TIMEOUT_MAX} seconds")

    scope_id, generation, lineage, repository, semantic = _authority(payload)
    mutation_policy = policy.mutation_execution
    if not mutation_policy.configured or not mutation_policy.scoped_mutation_enabled:
        raise HandlerError("HostMutationSandboxUnavailable", "scoped_mutation is not enabled by Host policy")

    store = MutationScopeStore(state_root)
    protected = (state_root.resolve(strict=False),)
    audit = MutationAuditJournal(state_root, evidence_retention_days=mutation_policy.evidence_retention_days)
    start: MutationAuditStart | None = None
    sandbox = None
    record = None
    finished = False
    terminalized = False
    process = None
    try:
        record = store.revalidate_scope_for_operation(
            scope_id, generation, mutation_policy, repository, semantic,
            required_operation_class=SCOPED_SCRIPT_OPERATION_CLASS,
            provider_protected_roots=protected,
        )
        interpreter = payload.get("interpreter")
        extensions = {"python3": "py", "powershell": "ps1", "pwsh": "ps1", "bash": "sh"}
        if not isinstance(interpreter, str) or interpreter not in extensions:
            raise HandlerError("invalid_payload", "unsupported scoped interpreter")

        try:
            verification = prepare_verification_execution(
                mutation_policy,
                payload.get("verification"),
            )
            if verification is not None:
                if not bool(payload.get("cleanup", True)):
                    raise ValueError("profiled verification requires cleanup=true")
                validate_verification_environment_request(env_extra)
        except ValueError as exc:
            raise HandlerError("HostMutationVerificationAdmissionFailed", str(exc)) from exc

        planned_workspace = Path(record.exact_workspace)
        script_path = planned_workspace / f"script.{extensions[interpreter]}"
        stdout_path = planned_workspace / "stdout.bin"
        stderr_path = planned_workspace / "stderr.bin"
        result_path = planned_workspace / "returncode.txt"
        try:
            run_cwd = (
                planned_verification_cwd(planned_workspace, payload.get("cwd"))
                if verification is not None
                else _cwd(planned_workspace, payload.get("cwd"), materialize=False)
            )
        except ValueError as exc:
            raise HandlerError("HostMutationSandboxPathViolation", str(exc)) from exc
        profiled_pwsh = verification is not None and interpreter in {"powershell", "pwsh"}
        planned_spawn_cwd = planned_workspace if profiled_pwsh else run_cwd
        planned_argv = _runner_argv(
            interpreter, script_path, args, planned_workspace,
            stdout_path, stderr_path, result_path, materialize=False,
            runner_cwd=run_cwd if profiled_pwsh else None,
        )
        process_intent = MutationProcessIntent(
            interpreter=interpreter,
            argv=tuple(planned_argv),
            executable_final_path=final_executable_path(Path(planned_argv[0])),
            cwd_final_path=str(planned_spawn_cwd),
        )
        requested_identity = requested_mutation_identity(record.unique_lease_key)
        if verification is None:
            prepared = prepare_scoped_script_evidence(
                context=context,
                payload=payload,
                lineage=lineage,
                audit=audit,
                scope_id=record.scope_id,
                scope_generation=record.generation,
                workspace_id=record.workspace_id,
                unique_lease_key=record.unique_lease_key,
                authority=_authority_evidence(record),
                process_intent=process_intent,
                requested_identity=requested_identity,
            )
        else:
            content = payload.get("content")
            if not isinstance(content, str):
                raise HandlerError("invalid_payload", "missing 'content'")
            exact_bytes = _scoped_script_bytes(content, interpreter)
            evidence = audit.evidence.retain(exact_bytes)
            binding = MutationAuditBinding.from_context(
                context,
                lineage,
                scope_id=record.scope_id,
                scope_generation=record.generation,
                workspace_id=record.workspace_id,
                unique_lease_key=record.unique_lease_key,
                job_id=(
                    payload.get("job_id")
                    if isinstance(payload.get("job_id"), str)
                    else None
                ),
            )
            verification_start = audit.begin(
                binding,
                evidence,
                authority=_authority_evidence(record),
                process_intent=process_intent,
                requested_identity=requested_identity,
                verification_intent=verification.plan.audit_intent,
            )
            prepared = PreparedMutationScript(
                interpreter=interpreter,
                exact_bytes=exact_bytes,
                evidence=evidence,
                audit_start=verification_start,
            )
        start = prepared.audit_start
        sandbox = build_mutation_sandbox(
            policy=mutation_policy,
            scope_store=store,
            repository=repository,
            semantic=semantic,
            provider_protected_roots=protected,
        )
        activation = sandbox.activate(record, start)
        if activation.workspace != planned_workspace:
            raise RuntimeError("activated workspace differs from sealed process intent")
        audit.evidence.materialize_verified(prepared.evidence, script_path)
        if hashlib.sha256(script_path.read_bytes()).hexdigest() != prepared.evidence.sha256:
            raise RuntimeError("materialized scoped script hash mismatch")

        verification_materialized = None
        if verification is not None:
            verification_materialized = sandbox.materialize_verification(
                activation,
                start,
                verification.plan,
            )
            try:
                run_cwd = verification_cwd(
                    verification_materialized,
                    payload.get("cwd"),
                )
            except ValueError as exc:
                raise HandlerError("HostMutationSandboxPathViolation", str(exc)) from exc
        else:
            run_cwd = _cwd(activation.workspace, payload.get("cwd"), materialize=True)

        profiled_pwsh = verification_materialized is not None and prepared.interpreter in {"powershell", "pwsh"}
        spawn_cwd = activation.workspace if profiled_pwsh else run_cwd
        argv = _runner_argv(
            prepared.interpreter, script_path, args, activation.workspace,
            stdout_path, stderr_path, result_path, materialize=True,
            runner_cwd=run_cwd if profiled_pwsh else None,
        )
        if argv != planned_argv:
            raise RuntimeError("materialized runner argv differs from sealed process intent")

        child_environment = _scoped_environment(env_extra, activation.workspace)
        if verification_materialized is not None:
            child_environment = build_verification_environment(
                child_environment,
                env_extra,
                verification_materialized,
            )
        response_cwd = (
            verification_cwd_label(payload.get("cwd"))
            if verification_materialized is not None
            else str(run_cwd)
        )
        process = sandbox.spawn(
            activation,
            audit=audit,
            audit_start=start,
            argv=argv,
            cwd=spawn_cwd,
            env=child_environment,
            verification=verification_materialized,
        )
        done = await asyncio.to_thread(process.wait, float(timeout))
        if not done:
            process.terminate()
            terminal = sandbox.terminalize(scope_id, generation)
            terminalized = True
            audit.finish(
                start, status="timeout", closure=_finish_closure(terminal, process),
                returncode=-1, error_code="timeout",
            )
            finished = True
            return {
                "ok": False,
                "interpreter": prepared.interpreter,
                "sudo": False,
                "cwd": response_cwd,
                "cleanup": bool(payload.get("cleanup", True)),
                "execution_profile": "scoped_mutation",
                "output": "Timeout",
                "returncode": -1,
                "timed_out": True,
                "mutation_scope_ref": {"scope_id": scope_id, "generation": generation},
                "audit_operation_id": start.operation_id,
            }

        if not result_path.exists():
            terminal = sandbox.terminalize(scope_id, generation)
            terminalized = True
            audit.finish(
                start, status="failed", closure=_finish_closure(terminal, process),
                error_code="HostMutationSandboxUnavailable",
            )
            finished = True
            raise HandlerError(
                "HostMutationSandboxUnavailable",
                f"{prepared.interpreter} could not initialize inside the required AppContainer",
            )
        try:
            returncode = int(result_path.read_text(encoding="ascii").strip())
        except (OSError, ValueError) as exc:
            raise RuntimeError("scoped runner return-code evidence is invalid") from exc

        stdout = _decode_output(stdout_path.read_bytes() if stdout_path.exists() else b"").strip()
        stderr = _decode_output(stderr_path.read_bytes() if stderr_path.exists() else b"").strip()
        output = (stdout + "\n" + stderr).strip() or "No output"
        if returncode == 0 and verification_materialized is not None:
            try:
                revalidate_verification_after_run(verification_materialized)
            except ValueError as exc:
                raise HandlerError("HostMutationVerificationIntegrityFailed", str(exc)) from exc

        terminal = sandbox.terminalize(scope_id, generation)
        terminalized = True
        audit.finish(
            start, status="succeeded" if returncode == 0 else "failed",
            closure=_finish_closure(terminal, process), returncode=returncode,
        )
        finished = True
        response: dict[str, Any] = {
            "ok": returncode == 0,
            "interpreter": prepared.interpreter,
            "sudo": False,
            "cwd": response_cwd,
            "cleanup": bool(payload.get("cleanup", True)),
            "execution_profile": "scoped_mutation",
            "output": output,
            "returncode": returncode,
            "mutation_scope_ref": {"scope_id": scope_id, "generation": generation},
            "audit_operation_id": start.operation_id,
            "terminal_state": terminal.state,
        }
        if verification_materialized is not None:
            response["verification"] = verification_evidence(verification_materialized)
        else:
            response["command"] = argv
            if not bool(payload.get("cleanup", True)):
                response["script_path"] = str(script_path)
                response["workdir"] = str(activation.workspace)
        return response
    except Exception as exc:
        terminal = None
        if start is not None and not terminalized and record is not None:
            try:
                if sandbox is not None:
                    terminal = sandbox.terminalize(scope_id, generation)
                else:
                    terminal = store.terminalize_scope(
                        scope_id, generation, mutation_policy, repository, semantic,
                        provider_protected_roots=protected,
                    )
                terminalized = True
            except (RuntimeError, OSError, ValueError):
                terminal = None
        if start is not None and not finished and terminal is not None:
            try:
                audit.finish(
                    start, status="failed", closure=_finish_closure(terminal, process),
                    error_code=str(getattr(exc, "code", type(exc).__name__)),
                )
                finished = True
            except (RuntimeError, OSError, ValueError):
                finished = False
        if isinstance(exc, HandlerError):
            raise
        raise HandlerError(str(getattr(exc, "code", "scoped_mutation_failed")), str(exc)) from exc


def make_profiled_script_run_handler(
    policy: Policy,
    upload_base: Path,
    *,
    config_path: Path | None = None,
    mutation_state_root: Path | None = None,
):
    """Compose historical and scoped script profiles without fallback."""
    legacy = make_legacy_script_run_handler(policy, upload_base)
    state_root = (
        mutation_state_root.resolve(strict=False)
        if mutation_state_root is not None
        else ((config_path.parent if config_path is not None else upload_base.parent) / "state").resolve(strict=False)
    )

    @context_aware
    async def handle(
        context_or_payload: RequestContext | dict[str, Any],
        maybe_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if maybe_payload is None:
            context: RequestContext | None = None
            payload = context_or_payload
            if not isinstance(payload, dict):
                raise HandlerError("invalid_payload", "script_run payload must be a mapping")
        else:
            if not isinstance(context_or_payload, RequestContext):
                raise HandlerError("HostMutationAuditLineageInvalid", "transport RequestContext is unavailable")
            context = context_or_payload
            payload = maybe_payload

        execution_profile = _profile(payload)
        if execution_profile == "scoped_mutation":
            if context is None:
                raise HandlerError("HostMutationAuditLineageInvalid", "scoped_mutation requires RequestContext")
            return await _run_scoped(context=context, payload=payload, policy=policy, state_root=state_root)
        if execution_profile == "operator_unrestricted":
            if not policy.mutation_execution.operator_unrestricted_enabled:
                raise HandlerError(
                    "operator_unrestricted_disabled",
                    "operator_unrestricted requires explicit Host policy opt-in",
                )
            return await legacy(payload)
        if execution_profile is not None:
            raise HandlerError("invalid_payload", f"unsupported execution_profile: {execution_profile}")
        if policy.mutation_execution.configured:
            raise HandlerError(
                "execution_profile_required",
                "configured mutation_execution requires an explicit execution_profile",
            )
        return await legacy(payload)

    return handle
