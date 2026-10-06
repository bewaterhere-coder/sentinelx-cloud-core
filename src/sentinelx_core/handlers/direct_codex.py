"""Bounded Agent-owned ``devforge_direct_codex`` local_api provider.

PR-015/S01 owns the provider contract, Host policy admission, closed action
schema and the repository-effect/readiness projection. PR-015/S02 adds the
provider-owned execution path: derived isolated workspace, fixed canonical
transport bootstrap, verified Codex chain, bounded active-user process
execution and the structured direct/Codex result contract. The live
direct-Codex recovery proof remains S03 and Acceptance/Acceptance-proof
ownership remains untouched.

Nothing here widens generic ``exec`` or ``script_run``: the action schema is
closed and provider-owned values (executable, sandbox settings, workspace
placement, timeout and result limits) are never caller data.
"""
from __future__ import annotations

import platform
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from sentinelx_core.direct_codex_discovery import (
    CodexChain,
    DirectCodexDiscoveryError,
    discover_codex_chain,
    resolve_node_executable,
    verify_cli_contract,
)
from sentinelx_core.direct_codex_handoff import compile_handoff, write_handoff
from sentinelx_core.direct_codex_result import normalize_result, validate_receipt
from sentinelx_core.direct_codex_transport import (
    DirectCodexTransportError,
    bootstrap_execution_checkout,
    read_remote_head,
    transport_git,
)
from sentinelx_core.direct_codex_workspace import (
    DirectCodexWorkspaceError,
    derive_workspace,
    ensure_outside_canonical,
    revalidate_workspace,
)
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

# Provider-owned, deterministic containment fixtures (D9).
_FIXTURE_WRITE_SCRIPT = (
    "const fs=require('fs');"
    "fs.writeFileSync(process.argv[1],'devforge-direct-codex-containment-ok');"
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

    async def prove_containment(
        self,
        *,
        repository: RepositoryIdentity,
        semantic: SemanticIdentity,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Run the D9 physical fixture: allowed write succeeds, protected
        target is refused, and the process tree closes with no detached child."""
        policy = self._policy.direct_codex
        workspace = derive_workspace(policy, repository, semantic)
        ensure_outside_canonical(workspace, self._canonical_roots)
        workspace.path.mkdir(parents=True, exist_ok=True)
        root_dir = workspace.path / ".devforge"
        root_dir.mkdir(parents=True, exist_ok=True)
        target = root_dir / "containment-proof.txt"

        node = resolve_node_executable(policy)
        budget = float(timeout if timeout is not None else min(policy.timeout_seconds, 120.0))

        def request(argv: list[str], cwd: Path) -> UserProcessRequest:
            return UserProcessRequest(
                executable=str(node),
                argv=argv,
                cwd=cwd,
                allowed_root=workspace.root,
                timeout_seconds=budget,
                max_output_bytes=4096,
            )

        write = await run_user_scoped_process(
            request([str(node), "-e", _FIXTURE_WRITE_SCRIPT, str(target)], workspace.path)
        )
        workspace_write_succeeded = write.returncode == 0 and target.is_file()

        sibling = workspace.root.parent if workspace.root.parent.is_dir() else workspace.root
        protected_refused = False
        try:
            await run_user_scoped_process(
                request(
                    [str(node), "-e", _FIXTURE_WRITE_SCRIPT, str(sibling / "contaminated.txt")],
                    sibling,
                )
            )
        except UserProcessError as exc:
            protected_refused = exc.code == "user_process_workspace_escape"

        tree = await run_user_scoped_process(
            request([str(node), "-e", _FIXTURE_TREE_SCRIPT], workspace.path)
        )

        verified = bool(
            workspace_write_succeeded
            and protected_refused
            and tree.process_tree_closed
            and tree.job_contained
        )
        proof = {
            "feature_id": FEATURE_ID,
            "workspace_write_succeeded": workspace_write_succeeded,
            "protected_sibling_refused": protected_refused,
            "process_tree_closed": tree.process_tree_closed,
            "job_contained": tree.job_contained,
            "execution_context": tree.execution_context,
            "workspace_digest": workspace.workspace_digest,
            "verified": verified,
        }
        if verified:
            self._containment_proof = proof
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
            "--ask-for-approval",
            "never",
        ]
        if chain.json_output_supported:
            argv.append("--json")
        argv.append(handoff.text)

        try:
            process = await run_user_scoped_process(
                UserProcessRequest(
                    executable=str(chain.node_executable),
                    argv=argv,
                    cwd=bootstrap.workspace,
                    allowed_root=workspace.root,
                    timeout_seconds=budget,
                    max_output_bytes=policy.max_result_bytes,
                )
            )
        except UserProcessError as exc:
            raise HandlerError(exc.code, str(exc)) from exc

        revalidate_workspace(workspace, policy, repository, semantic)
        local_head, actual_branch = await self._local_state(bootstrap, budget)
        remote_head = await read_remote_head(
            cwd=bootstrap.workspace,
            repository=repository,
            branch=str(transport["branch"]),
            timeout=budget,
        )

        payload = normalize_result(
            params=validated,
            bootstrap=bootstrap,
            process=process,
            handoff_digest=handoff.digest,
            actual_branch=actual_branch,
            local_head=local_head,
            remote_head_readback=remote_head,
        )
        ok, reason = validate_receipt(
            payload,
            task_id=str(lineage["task_id"]),
            slice_id=str(lineage["slice_id"]) if lineage.get("slice_id") else None,
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

    async def _local_state(self, bootstrap: Any, budget: float) -> tuple[str, str]:
        code, stdout, _stderr = await transport_git(
            bootstrap.workspace, "rev-parse", "HEAD", timeout=budget
        )
        if code != 0:
            raise HandlerError(
                "direct_codex_head_read_failed", "cannot read the execution checkout head"
            )
        local_head = stdout.decode("utf-8", errors="replace").strip()
        code, stdout, _stderr = await transport_git(
            bootstrap.workspace, "rev-parse", "--abbrev-ref", "HEAD", timeout=budget
        )
        actual_branch = stdout.decode("utf-8", errors="replace").strip() if code == 0 else ""
        return local_head, actual_branch


def make_devforge_direct_codex_provider(
    policy: Policy,
    *,
    platform_name: str | None = None,
    canonical_roots: Iterable[Path] | None = None,
) -> DevforgeDirectCodexProvider:
    return DevforgeDirectCodexProvider(
        policy, platform_name=platform_name, canonical_roots=canonical_roots
    )
