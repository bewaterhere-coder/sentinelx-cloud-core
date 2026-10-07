"""Bounded Agent-owned ``devforge_direct_codex`` local_api provider.

PR-015/S01 owns the provider contract, Host policy admission, closed action
schema and the repository-effect/readiness projection. PR-015/S02 adds the
provider-owned execution path: derived isolated workspace, fixed canonical
transport bootstrap, verified Codex chain, bounded active-user process
execution and the structured direct/Codex result contract. PR-015/S03
validates the exact Task/Run/Attempt/Slice and canonical repository/PR/branch
echo and runs the exact-candidate live self-host recovery proof through the
delivered bridge. Acceptance/acceptance-proof ownership remains untouched.

Nothing here widens generic ``exec`` or ``script_run``: the action schema is
closed and provider-owned values (executable, sandbox settings, workspace
placement, timeout and result limits) are never caller data.
"""
from __future__ import annotations

import os
import platform
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Sequence

from sentinelx_core.direct_codex_discovery import (
    CodexChain,
    DirectCodexDiscoveryError,
    discover_codex_chain,
    resolve_node_executable,
    verify_cli_contract,
)
from sentinelx_core.direct_codex_handoff import compile_handoff, write_handoff
from sentinelx_core.direct_codex_persistence import persist_implementation
from sentinelx_core.direct_codex_result import normalize_result, validate_receipt
from sentinelx_core.direct_codex_transport import (
    DirectCodexTransportError,
    bootstrap_execution_checkout,
)
from sentinelx_core.direct_codex_workspace import (
    DirectCodexWorkspaceError,
    derive_workspace,
    ensure_outside_canonical,
    revalidate_workspace,
)
from sentinelx_core import windows_integrity
from sentinelx_core.executor import HandlerError
from sentinelx_core.mutation_placement import RepositoryIdentity, SemanticIdentity
from sentinelx_core.operation_registry import (
    FirewallCoverage,
    OperationEffectResolution,
    RepositoryEffect,
)
from sentinelx_core.policy import Policy
from sentinelx_core.request_context import RequestContext
from sentinelx_core.user_process import (
    UserProcessError,
    UserProcessRequest,
    run_user_scoped_process,
)

ENDPOINT_NAME = "devforge_direct_codex"
CONTRACT_ID = "devforge_direct_codex"
CONTRACT_REVISION = 1
FEATURE_ID = "development_host.direct_codex_v1"

EXECUTE_TASK_ACTION = "execute_task"

CONTAINMENT_UNPROVEN_REASON = "direct_codex_containment_unproven"

# The containment mechanism is a real Windows sandbox: the provider-owned
# workspace is labeled low and every provider child starts at low integrity, so
# Mandatory Integrity Control is what refuses a write outside the workspace.
SANDBOX_MECHANISM = "windows_mandatory_integrity_control"
SANDBOX_INTEGRITY_LEVEL = windows_integrity.LOW_INTEGRITY
SANDBOX_UNAVAILABLE_REASON = "direct_codex_sandbox_unavailable"

# Provider-owned name for the canonical-like protected sibling fixture. Never
# caller data, never a path inside a canonical checkout.
NEGATIVE_TARGET_NAME = "sentinelx-protected-sibling.txt"

# errno/code values the operating system returns when MIC (NO_WRITE_UP) refuses
# a write. A refusal is only credited when the child observed one of these.
_DENIAL_CODES = frozenset({"EPERM", "EACCES", "ERR_FS_EACCES", "ERR_FS_EPERM"})

# Fields that would transfer execution authority from the provider to the
# caller. The JSON schemas below are already closed; this list is defence in
# depth so a future schema edit cannot silently reintroduce a caller-owned
# executable, prompt, working directory or credential.
_FORBIDDEN_FIELDS = frozenset(
    {
        "executable",
        "executable_path",
        "argv",
        "args",
        "command",
        "command_line",
        "shell",
        "cwd",
        "workspace",
        "workspace_path",
        "workspace_root",
        "env",
        "environment",
        "prompt",
        "system_prompt",
        "instructions",
        "model",
        "reasoning_effort",
        "sandbox",
        "sandbox_mode",
        "approval",
        "approval_policy",
        "dangerously_bypass",
        "yolo",
        "credential",
        "credentials",
        "token",
        "secret",
        "replacement_transport",
        "remote_url",
    }
)

_STRING = {"type": "string", "minLength": 1}

_REPOSITORY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["vcs", "authority", "path"],
    "additionalProperties": False,
    "properties": {
        "vcs": _STRING,
        "authority": _STRING,
        "path": _STRING,
    },
}
_LINEAGE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["project_id", "task_id", "run_id", "attempt_id"],
    "additionalProperties": False,
    "properties": {
        "project_id": _STRING,
        "task_id": _STRING,
        "run_id": _STRING,
        "attempt_id": _STRING,
        "slice_id": _STRING,
    },
}
_DEVELOPMENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["action", "requirement_ref", "plan_ref"],
    "additionalProperties": False,
    "properties": {
        "action": {"enum": ["implementation", "fixing"]},
        "requirement_ref": _STRING,
        "plan_ref": _STRING,
        "findings_ref": _STRING,
    },
}
_TRANSPORT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["type", "pr_number", "branch", "expected_remote_sha"],
    "additionalProperties": False,
    "properties": {
        "type": {"const": "github-pr"},
        "pr_number": {"type": "integer", "minimum": 1},
        "branch": _STRING,
        "expected_remote_sha": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
    },
}
_EXECUTE_TASK_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["repository", "lineage", "development", "transport"],
    "additionalProperties": False,
    "properties": {
        "repository": _REPOSITORY_SCHEMA,
        "lineage": _LINEAGE_SCHEMA,
        "development": _DEVELOPMENT_SCHEMA,
        "transport": _TRANSPORT_SCHEMA,
    },
}

_ACTION_SCHEMAS = {EXECUTE_TASK_ACTION: _EXECUTE_TASK_SCHEMA}

_NESTED_SPECS = (
    ("repository", _REPOSITORY_SCHEMA),
    ("lineage", _LINEAGE_SCHEMA),
    ("development", _DEVELOPMENT_SCHEMA),
    ("transport", _TRANSPORT_SCHEMA),
)

# Provider-owned, deterministic containment fixtures (D9). One single process
# start performs both the allowed write and the out-of-workspace attempt, so
# the refusal cannot be confused with "the process never started".
_FIXTURE_WRITE_SCRIPT = (
    "const fs=require('fs');"
    "const out=[];"
    "for (const p of process.argv.slice(1)) {"
    "  try {"
    "    fs.writeFileSync(p,'devforge-direct-codex-containment-ok');"
    "    out.push(p+'=WROTE');"
    "  } catch (e) {"
    "    out.push(p+'='+(e.code||e.errno||'ERROR'));"
    "  }"
    "}"
    "process.stdout.write(out.join(' | '));"
)
_FIXTURE_TREE_SCRIPT = (
    "const {spawn}=require('child_process');"
    "const child=spawn(process.execPath,['-e','setTimeout(function(){},120000)'],"
    "{detached:false,stdio:'ignore'});"
    "child.unref();"
)


def _reject_forbidden_fields(node: Any, prefix: str = "") -> None:
    """Fail closed on any caller-owned execution-authority field."""
    if isinstance(node, dict):
        for key, value in node.items():
            name = str(key)
            if name in _FORBIDDEN_FIELDS:
                raise HandlerError("invalid_payload", f"unsupported field: {prefix}{name}")
            _reject_forbidden_fields(value, f"{prefix}{name}.")
    elif isinstance(node, (list, tuple)):
        for index, value in enumerate(node):
            _reject_forbidden_fields(value, f"{prefix}[{index}].")


def _require_object(params: dict[str, Any], name: str) -> dict[str, Any]:
    value = params.get(name)
    if not isinstance(value, dict):
        raise HandlerError("invalid_payload", f"{name} must be an object")
    return value


def validate_execute_task_params(params: Any) -> dict[str, Any]:
    """Validate the closed ``execute_task`` payload without executing anything."""
    if not isinstance(params, dict):
        raise HandlerError("invalid_payload", "execute_task params must be an object")

    extras = sorted(set(params) - set(_EXECUTE_TASK_SCHEMA["properties"]))
    if extras:
        raise HandlerError("invalid_payload", f"unsupported execute_task fields: {extras}")
    missing = sorted(set(_EXECUTE_TASK_SCHEMA["required"]) - set(params))
    if missing:
        raise HandlerError("invalid_payload", f"missing execute_task fields: {missing}")

    _reject_forbidden_fields(params)

    for name, schema in _NESTED_SPECS:
        block = _require_object(params, name)
        extras = sorted(set(block) - set(schema["properties"]))
        if extras:
            raise HandlerError("invalid_payload", f"unsupported {name} fields: {extras}")
        missing = sorted(set(schema["required"]) - set(block))
        if missing:
            raise HandlerError("invalid_payload", f"missing {name} fields: {missing}")

    lineage = params["lineage"]
    for name in ("project_id", "task_id", "run_id", "attempt_id"):
        if not str(lineage.get(name) or "").strip():
            raise HandlerError("invalid_payload", f"lineage.{name} must be a non-empty string")

    development = params["development"]
    if development["action"] not in ("implementation", "fixing"):
        raise HandlerError(
            "invalid_payload", f"unsupported development.action: {development['action']}"
        )

    transport = params["transport"]
    if transport["type"] != "github-pr":
        raise HandlerError("invalid_payload", "transport.type must be github-pr")
    if not isinstance(transport["pr_number"], int) or isinstance(transport["pr_number"], bool):
        raise HandlerError("invalid_payload", "transport.pr_number must be an integer")

    return dict(params)


def _identity(params: dict[str, Any]) -> tuple[RepositoryIdentity, SemanticIdentity]:
    repository_block = params["repository"]
    try:
        repository = RepositoryIdentity(
            vcs=str(repository_block["vcs"]),
            authority=str(repository_block["authority"]),
            path=str(repository_block["path"]),
        )
        _ = repository.canonical
    except ValueError as exc:
        raise HandlerError("invalid_payload", f"repository identity is invalid: {exc}") from exc
    lineage = params["lineage"]
    try:
        semantic = SemanticIdentity(
            project_id=str(lineage["project_id"]),
            task_id=str(lineage["task_id"]),
            run_id=str(lineage["run_id"]),
            attempt_id=str(lineage["attempt_id"]),
            slice_id=str(lineage["slice_id"]) if lineage.get("slice_id") else None,
        )
        _ = semantic.canonical
    except ValueError as exc:
        raise HandlerError("invalid_payload", f"lineage identity is invalid: {exc}") from exc
    return repository, semantic


def _negative_target(workspace: Any) -> Path | None:
    """Provider-owned canonical-like sibling strictly outside the workspace root."""
    parent = Path(os.path.abspath(str(workspace.root))).parent
    if not parent.is_dir():
        return None
    return parent / NEGATIVE_TARGET_NAME


def _activate_integrity_sandbox(paths: Iterable[Path]) -> dict[str, Any]:
    """Label provider-owned workspace trees low and read the label back."""
    labels: dict[str, str | None] = {}
    stamped = 0
    for path in paths:
        stamped += windows_integrity.set_low_mandatory_label_tree(path)
        labels[str(path)] = windows_integrity.mandatory_label(path)
    return {
        "mechanism": SANDBOX_MECHANISM,
        "integrity_level": SANDBOX_INTEGRITY_LEVEL,
        "labels": labels,
        "stamped_objects": stamped,
    }


def _parse_fixture_report(stdout: str) -> dict[str, str]:
    """Parse the ``<path>=<result>`` pairs emitted by the containment fixture."""
    parsed: dict[str, str] = {}
    for chunk in stdout.split(" | "):
        if "=" not in chunk:
            continue
        path, _, result = chunk.rpartition("=")
        parsed[os.path.normcase(path.strip())] = result.strip()
    return parsed


class DevforgeDirectCodexProvider:
    """Policy-admitted builtin direct-Codex contract and bounded execution path."""

    name = ENDPOINT_NAME

    def __init__(
        self,
        policy: Policy,
        *,
        platform_name: str | None = None,
        canonical_roots: Iterable[Path] | None = None,
    ) -> None:
        self._policy = policy
        self._platform_name = platform_name or platform.system()
        self._canonical_roots = (
            tuple(Path(str(root)) for root in canonical_roots)
            if canonical_roots is not None
            else tuple(
                Path(str(spec.root))
                for spec in getattr(policy.mutation_execution, "canonical_repositories", ())
            )
        )
        self._containment_proof: dict[str, Any] | None = None

    # -- admission ---------------------------------------------------------
    @property
    def admission_reasons(self) -> tuple[str, ...]:
        """Policy/platform prerequisites owned by the Host, never by a caller."""
        return self._policy.direct_codex.missing_prerequisites(
            platform_name=self._platform_name
        )

    def available_actions(self) -> tuple[str, ...]:
        if self.admission_reasons:
            return ()
        if "local_api" in self._policy.disabled_ops:
            return ()
        return (EXECUTE_TASK_ACTION,)

    # -- containment proof -------------------------------------------------
    @property
    def containment_proof(self) -> dict[str, Any] | None:
        return self._containment_proof

    def _contained_request(
        self,
        workspace: Any,
        *,
        executable: Any,
        argv: Sequence[str],
        cwd: Path,
        budget: float,
        max_output_bytes: int = 8192,
        integrity_level: str | None = None,
    ) -> UserProcessRequest:
        """The provider-owned execution request shape.

        The real direct-Codex run uses the active-user integrity level and is
        confined by the Codex CLI's own ``--sandbox workspace-write`` (a real
        Windows sandbox mechanism). The containment proof separately stakes a
        low-integrity Mandatory-Integrity-Control enclave around the exact same
        derived workspace and proves the OS refuses an out-of-workspace write;
        ``execute_task`` becomes ``PROVEN`` only once that physical negative
        proof has succeeded.
        """
        return UserProcessRequest(
            executable=str(executable),
            argv=list(argv),
            cwd=cwd,
            allowed_root=workspace.root,
            timeout_seconds=budget,
            max_output_bytes=max_output_bytes,
            integrity_level=integrity_level,
        )

    def _unproven_proof(
        self,
        workspace: Any,
        *,
        reason: str,
        detail: str | None = None,
    ) -> dict[str, Any]:
        proof: dict[str, Any] = {
            "feature_id": FEATURE_ID,
            "workspace_write_succeeded": False,
            "protected_sibling_refused": False,
            "process_tree_closed": False,
            "job_contained": False,
            "execution_context": None,
            "workspace_digest": workspace.workspace_digest,
            "sandbox": None,
            "negative_probe": {
                "attempted": False,
                "started_inside_workspace": False,
                "reason": reason,
            },
            "verified": False,
        }
        if detail:
            proof["negative_probe"]["detail"] = detail
        self._containment_proof = None
        return proof

    async def prove_containment(
        self,
        *,
        repository: RepositoryIdentity,
        semantic: SemanticIdentity,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Run the D9 physical fixture inside a real Windows sandbox.

        One provider-owned child starts inside the legal workspace and, within a
        single process lifetime, performs both the allowed workspace write and
        the out-of-workspace attempt against a canonical-like protected sibling.
        The sibling attempt is therefore really executed by a running process
        and must be refused by the operating system (Mandatory Integrity
        Control), never by a pre-spawn cwd admission check. Any contamination
        is removed and disproves containment.
        """
        policy = self._policy.direct_codex
        workspace = derive_workspace(policy, repository, semantic)
        ensure_outside_canonical(workspace, self._canonical_roots)
        workspace.path.mkdir(parents=True, exist_ok=True)

        node = resolve_node_executable(policy)
        budget = float(timeout if timeout is not None else min(policy.timeout_seconds, 120.0))

        outside = _negative_target(workspace)
        if outside is None:
            return self._unproven_proof(
                workspace, reason=CONTAINMENT_UNPROVEN_REASON,
                detail="no provider-owned protected sibling outside the workspace root",
            )

        try:
            # The label is stamped with subtree inheritance, so everything the
            # execution checkout and the direct host create later stays inside
            # the same low-integrity enclave.
            activation = _activate_integrity_sandbox((workspace.path,))
        except windows_integrity.IntegritySandboxError as exc:
            # No real sandbox, no attempt: a negative proof that cannot be
            # enforced by the OS must never be simulated by writing outside.
            return self._unproven_proof(workspace, reason=exc.code, detail=str(exc))

        root_dir = workspace.path / ".devforge"
        root_dir.mkdir(parents=True, exist_ok=True)
        target = root_dir / "containment-proof.txt"

        if outside.exists():
            outside.unlink()

        write = await run_user_scoped_process(
            self._contained_request(
                workspace,
                executable=node,
                argv=[str(node), "-e", _FIXTURE_WRITE_SCRIPT, str(target), str(outside)],
                cwd=workspace.path,
                budget=budget,
                integrity_level=SANDBOX_INTEGRITY_LEVEL,
            )
        )
        report = _parse_fixture_report(write.stdout)
        inside_result = report.get(os.path.normcase(str(target)))
        outside_result = report.get(os.path.normcase(str(outside)))
        workspace_write_succeeded = inside_result == "WROTE" and target.is_file()
        contaminated = outside.exists()
        if contaminated:
            outside.unlink()
        denied = outside_result in _DENIAL_CODES
        protected_refused = bool(
            write.returncode == 0
            and write.integrity_level == SANDBOX_INTEGRITY_LEVEL
            and workspace_write_succeeded
            and denied
            and not contaminated
        )

        tree = await run_user_scoped_process(
            self._contained_request(
                workspace,
                executable=node,
                argv=[str(node), "-e", _FIXTURE_TREE_SCRIPT],
                cwd=workspace.path,
                budget=budget,
            )
        )

        verified = bool(
            workspace_write_succeeded
            and protected_refused
            and tree.process_tree_closed
            and tree.job_contained
        )
        proof: dict[str, Any] = {
            "feature_id": FEATURE_ID,
            "workspace_write_succeeded": workspace_write_succeeded,
            "protected_sibling_refused": protected_refused,
            "process_tree_closed": tree.process_tree_closed,
            "job_contained": tree.job_contained,
            "execution_context": tree.execution_context,
            "workspace_digest": workspace.workspace_digest,
            "sandbox": activation,
            "negative_probe": {
                "attempted": True,
                "started_inside_workspace": True,
                "cwd": str(workspace.path),
                "target": str(outside),
                "target_kind": "workspace_root_sibling",
                "child_exit_code": write.returncode,
                "child_integrity_level": write.integrity_level,
                "child_session_id": write.session_id,
                "workspace_write_result": inside_result,
                "outside_write_result": outside_result,
                "denied_by": SANDBOX_MECHANISM if denied else None,
                "contaminated": contaminated,
            },
            "verified": verified,
        }
        # The fixture leaves no residue: the execution workspace must still be
        # an empty derived directory so the transport bootstrap can create the
        # independent checkout there. The low mandatory label stays in force.
        for artifact in (target, root_dir):
            try:
                if artifact.is_file():
                    artifact.unlink()
                elif artifact.is_dir() and not any(artifact.iterdir()):
                    artifact.rmdir()
            except OSError:  # pragma: no cover - best-effort cleanup
                pass
        self._containment_proof = proof if verified else None
        return proof

    # -- effect / readiness projection ------------------------------------
    def repository_effect(self, action: str) -> OperationEffectResolution:
        if action == EXECUTE_TASK_ACTION:
            if self._containment_proof is not None and self._containment_proof.get("verified"):
                # Provider-owned containment is proven by the D9 fixture: job
                # containment, workspace-scoped cwd and a protected-root refusal.
                return OperationEffectResolution(
                    RepositoryEffect.PROCESS_MUTATION,
                    FirewallCoverage.PROVEN,
                    selector="direct_codex_scoped_workspace",
                )
            # A direct development host is an external process. It is a process
            # mutation and stays UNPROVEN until the physical containment proof
            # succeeds, so provider-wide effective-surface readiness cannot
            # become true through an unproven containment path.
            return OperationEffectResolution(
                RepositoryEffect.PROCESS_MUTATION,
                FirewallCoverage.UNPROVEN,
                reason=CONTAINMENT_UNPROVEN_REASON,
            )
        return OperationEffectResolution(
            RepositoryEffect.UNKNOWN,
            FirewallCoverage.UNPROVEN,
            reason="unknown_direct_codex_action",
        )

    def readiness(self) -> dict[str, Any]:
        """Provider-owned readiness projection for ``FEATURE_ID``."""
        reasons = list(self.admission_reasons)
        if not reasons and not self.available_actions():
            reasons.append("local_api_disabled")
        if not reasons and self._containment_proof is None:
            reasons.append(CONTAINMENT_UNPROVEN_REASON)
        return {
            "available": self._containment_proof is not None,
            "verified": bool(self._containment_proof and self._containment_proof.get("verified")),
            "contract_id": CONTRACT_ID,
            "contract_revision": CONTRACT_REVISION,
            "reason": reasons[0] if reasons else None,
            "uncovered_classes": list(dict.fromkeys(reasons)),
        }

    # -- local_api surface -------------------------------------------------
    def list_entry(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "protocol": "builtin",
            "transport": "agent",
            "action_count": len(self.available_actions()),
            "provider_kind": "builtin",
            "contract_id": CONTRACT_ID,
            "contract_revision": CONTRACT_REVISION,
            "feature_id": FEATURE_ID,
        }

    def describe(self) -> dict[str, Any]:
        actions = self.available_actions()
        if not actions:
            raise HandlerError(
                "endpoint_not_available",
                "devforge_direct_codex requires explicit direct-codex Host policy opt-in",
            )
        return {
            "ok": True,
            "operation": "describe",
            "endpoint": self.name,
            "provider_kind": "builtin",
            "contract_id": CONTRACT_ID,
            "contract_revision": CONTRACT_REVISION,
            "feature_id": FEATURE_ID,
            "readiness": self.readiness(),
            "actions": {
                action: {
                    "description": f"Bounded {action} action",
                    "params": list(_ACTION_SCHEMAS[action]["required"]),
                    "params_schema": _ACTION_SCHEMAS[action],
                }
                for action in actions
            },
        }

    async def call(
        self,
        context: RequestContext,
        action: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(context, RequestContext):
            raise HandlerError(
                "invalid_payload",
                "devforge_direct_codex requires transport RequestContext",
            )
        if self.admission_reasons:
            raise HandlerError(
                "endpoint_not_available",
                "devforge_direct_codex requires explicit direct-codex Host policy opt-in",
            )
        if "local_api" in self._policy.disabled_ops:
            raise HandlerError("operation_disabled", "local_api is disabled by Host policy")
        if action != EXECUTE_TASK_ACTION:
            raise HandlerError("unknown_action", f"unknown devforge_direct_codex action: {action}")
        if "action" in params:
            raise HandlerError("invalid_payload", "params.action is transport-owned")

        validated = validate_execute_task_params(params)
        if self._containment_proof is None or not self._containment_proof.get("verified"):
            # Fail closed: an external development host may only run after the
            # D9 physical containment proof succeeded. There is no shell,
            # generic exec or provider fallback path.
            raise HandlerError(
                "direct_codex_execution_unavailable",
                "devforge_direct_codex.execute_task requires a verified direct-Codex "
                "containment proof (workspace-scoped process, job containment, "
                "protected-root refusal)",
            )
        repository, semantic = _identity(validated)
        policy = self._policy.direct_codex
        lineage = validated["lineage"]
        transport = validated["transport"]
        development = validated["development"]

        workspace = derive_workspace(policy, repository, semantic)
        budget = float(policy.timeout_seconds)

        bootstrap = await self._bootstrap(workspace, repository, semantic, transport, budget)

        chain = await self._chain(policy, workspace, bootstrap, budget)
        await verify_cli_contract(
            chain, cwd=bootstrap.workspace, allowed_root=workspace.root, timeout=min(budget, 60.0)
        )

        handoff = compile_handoff(
            task_id=str(lineage["task_id"]),
            run_id=str(lineage["run_id"]),
            attempt_id=str(lineage["attempt_id"]),
            slice_id=str(lineage["slice_id"]) if lineage.get("slice_id") else None,
            action=str(development["action"]),
            requirement_ref=str(development["requirement_ref"]),
            plan_ref=str(development["plan_ref"]),
            findings_ref=(
                str(development["findings_ref"]) if development.get("findings_ref") else None
            ),
            pr_number=int(transport["pr_number"]),
            branch=str(transport["branch"]),
            expected_remote_sha=str(transport["expected_remote_sha"]),
        )
        write_handoff(bootstrap.workspace, handoff)

        argv = [
            str(chain.node_executable),
            str(chain.codex_script),
            "exec",
            "--sandbox",
            "workspace-write",
        ]
        if chain.approval_flag_supported:
            # Only pass the flag when the verified CLI advertises it: an
            # unrecognized flag makes the whole non-interactive run fail.
            argv += ["--ask-for-approval", "never"]
        if chain.json_output_supported:
            argv.append("--json")
        argv.append(handoff.text)

        try:
            process = await run_user_scoped_process(
                self._contained_request(
                    workspace,
                    executable=chain.node_executable,
                    argv=argv,
                    cwd=bootstrap.workspace,
                    budget=budget,
                    max_output_bytes=policy.max_result_bytes,
                )
            )
        except UserProcessError as exc:
            raise HandlerError(exc.code, str(exc)) from exc

        revalidate_workspace(workspace, policy, repository, semantic)
        # The direct host runs inside the integrity sandbox and never owns the
        # canonical transport. After Codex exits, the provider owns deterministic
        # local persistence (one provenance-bound candidate commit) and ordinary
        # fast-forward publication of the exact checkout changes, followed by an
        # independent remote readback.
        try:
            persistence = await persist_implementation(
                workspace=workspace,
                bootstrap=bootstrap,
                repository=repository,
                semantic=semantic,
                canonical_pr=int(transport["pr_number"]),
                branch=str(transport["branch"]),
                expected_remote_sha=str(transport["expected_remote_sha"]),
                timeout=budget,
            )
        except (DirectCodexTransportError, DirectCodexWorkspaceError) as exc:
            raise HandlerError(exc.code, str(exc)) from exc

        payload = normalize_result(
            params=validated,
            bootstrap=bootstrap,
            process=process,
            handoff_digest=handoff.digest,
            actual_branch=persistence.actual_branch,
            local_head=persistence.local_head,
            remote_head_readback=persistence.remote_head_readback,
            persistence=persistence,
        )
        ok, reason = validate_receipt(
            payload,
            task_id=str(lineage["task_id"]),
            run_id=str(lineage["run_id"]),
            attempt_id=str(lineage["attempt_id"]),
            slice_id=str(lineage["slice_id"]) if lineage.get("slice_id") else None,
            canonical_pr=int(transport["pr_number"]),
            canonical_repository=repository.canonical,
        )
        payload["ok"] = bool(ok)
        payload["operation"] = EXECUTE_TASK_ACTION
        payload["endpoint"] = self.name
        payload["receipt"]["reason"] = reason
        return payload

    # -- execution helpers -------------------------------------------------
    async def _bootstrap(
        self,
        workspace: Any,
        repository: RepositoryIdentity,
        semantic: SemanticIdentity,
        transport: dict[str, Any],
        budget: float,
    ) -> Any:
        try:
            return await bootstrap_execution_checkout(
                policy=self._policy.direct_codex,
                workspace=workspace,
                repository=repository,
                semantic=semantic,
                branch=str(transport["branch"]),
                expected_remote_sha=str(transport["expected_remote_sha"]),
                canonical_roots=self._canonical_roots,
                timeout=budget,
            )
        except DirectCodexWorkspaceError as exc:
            raise HandlerError(exc.code, str(exc)) from exc
        except DirectCodexTransportError as exc:
            raise HandlerError(exc.code, str(exc)) from exc

    async def _chain(
        self,
        policy: Any,
        workspace: Any,
        bootstrap: Any,
        budget: float,
    ) -> CodexChain:
        try:
            return await discover_codex_chain(
                policy,
                cwd=bootstrap.workspace,
                allowed_root=workspace.root,
                probe_timeout=min(budget, 30.0),
            )
        except (DirectCodexDiscoveryError, UserProcessError) as exc:
            raise HandlerError(
                getattr(exc, "code", "direct_codex_chain_unavailable"), str(exc)
            ) from exc


def make_devforge_direct_codex_provider(
    policy: Policy,
    *,
    platform_name: str | None = None,
    canonical_roots: Iterable[Path] | None = None,
) -> DevforgeDirectCodexProvider:
    return DevforgeDirectCodexProvider(
        policy, platform_name=platform_name, canonical_roots=canonical_roots
    )
