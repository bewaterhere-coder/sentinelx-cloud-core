---
task_id: PR-015-direct-codex-development-host-invocation-bridge-v1
title: SentinelX Direct Codex Development Host Invocation Bridge V1
project_id: sentinelx-cloud-core
repository: bewaterhere-coder/sentinelx-cloud-core
requirement_revision: 1
development:
  stage: plan_review
  gates:
    requirement_ready: true
    plan_approved: false
    acceptance_approved: false
    completion_verified: false
  plan_revision: 2
  implementation_authorized: false
  latest_plan_review: rejected_round_1
  latest_plan_remediation: r2_ready
  review_disposition: plan_local_remediated
  next_expected_actor: reviewer
  authorization:
    mode: durable
    ref: docs/authorizations/PR-015-direct-codex-development-host-invocation-bridge-v1-development-authorization.yaml
artifacts:
  plan: docs/plans/PR-015-direct-codex-development-host-invocation-bridge-v1-plan.md
  latest_plan_review: docs/reviews/PR-015-direct-codex-development-host-invocation-bridge-v1-plan-review-r1.md
  latest_plan_remediation: docs/checkpoints/PR-015-direct-codex-development-host-invocation-bridge-v1-plan-remediation-r2-20261006.yaml
transport:
  type: github-pr
  pr_number: 15
  branch: task/direct-codex-development-host-invocation-bridge-v1
  base_branch: main
requirement_readiness:
  result: Ready
  depth: deep
  ui_semantics:
    applicability: NotApplicable
  refinement_evidence:
    canonical_main_at_creation: 018b78ca20984176d53fbe90039dc795a7f2742f
    project_binding: direct/codex
    live_host_codex_package_observed: "@openai/codex 0.154.0"
    live_host_codex_shim_observed: "active-user npm codex.cmd -> node + @openai/codex/bin/codex.js"
    current_blocker: DirectCodexExecutionSurfaceUnavailable
    pr013_relation: related_unblocker_not_same_task
---

# Requirement

## Problem

The DevForge project binding for `sentinelx-cloud-core` is explicitly:

```yaml
execution_binding:
  provider: direct
  adapter: codex
```

The current Windows Host has Codex CLI installed for the active interactive user, but ChatGPT/DevForge has no bounded Agent-owned surface that can invoke that direct Development Host.

The current SentinelX surfaces do not solve this:

- `exec` is not exposed by the live Agent;
- `script_run` is governed by scoped-mutation execution-profile policy and is not a lawful direct-Codex launcher;
- `devforge_runtime.execute_scoped` is a Host Runtime scoped-execution surface, not the direct/Codex adapter;
- `repository_transaction_v1` is owned by PR-013 and must not be copied or required to invoke the direct adapter;
- production `mcp.sentinelx.app` is an immutable external transport boundary.

This blocks `#开发执行 PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1` before implementation admission even though Codex itself is installed.

## Goal

Add one Agent-owned, model-reachable, structured bridge that lets DevForge invoke **Codex as the existing direct Development Host** while preserving:

```text
DevForge Task/Plan/Slice authority
+ direct/codex provider identity
+ canonical PR/branch transport lock
+ active-user Codex authentication context
+ isolated DevForge execution workspace
+ bounded non-interactive Codex invocation
+ post-run transport/readback receipt
```

SentinelX is transport and policy enforcement only. It does not become the Development Host and does not reinterpret the project binding as `host-runtime`.

## Scope

V1 targets Windows because the concrete blocker is a LocalSystem SentinelX service plus an installed active-user Codex CLI.

The bridge is projected through the existing model-facing `sentinel_local_api` envelope as an Agent-owned builtin provider. Hub source/schema/deployment changes are out of scope.

The implementation may introduce a private Windows active-user process primitive only if it remains non-model-facing and can be called only by fixed, policy-owned brokers. It must not become a generic run-as-user or arbitrary command primitive.

## Required behavior

### R1 — Preserve direct/Codex execution identity

A successful invocation represents:

```text
execution provider = direct
development adapter = codex
development host = Codex
capability transport = SentinelX Agent builtin local_api
```

The bridge MUST NOT report or persist `host-runtime` as the execution provider merely because SentinelX carries the invocation.

### R2 — Agent-owned structured projection

The bridge MUST be discoverable through existing `local_api.list/describe/call`.

V1 SHOULD use a dedicated builtin provider identity such as `devforge_direct_codex` rather than widening generic `script_run` or `exec`.

Production Hub modification is forbidden.

### R3 — Explicit Host policy opt-in

The provider is unavailable unless the Host explicitly opts in to direct Codex execution.

Readiness MUST fail closed when any required component is absent, including supported platform, active user session, Codex executable identity, workspace root, or required sandbox behavior.

Tool/provider availability is not inferred merely because a `codex.cmd` file exists.

### R4 — Fixed executable identity; no shell wrapper authority

The caller MUST NOT supply an executable path, shell, command string, arbitrary argv, Node path, npm path, or Codex package path.

On Windows the provider MUST resolve and verify the active user's installed Codex package and execute a fixed provider-owned chain equivalent to:

```text
verified node executable
+ verified @openai/codex/bin/codex.js
+ provider-owned codex exec arguments
```

A `.cmd`/PowerShell shim may be inspected for discovery evidence but MUST NOT turn `cmd.exe /c <caller text>` or PowerShell into the execution boundary.

Version is runtime evidence, not project binding. The observed `@openai/codex 0.154.0` is not a permanent version pin.

### R5 — Active-user identity without credential exposure

Codex MUST run under the active interactive Windows user's token/environment so it can reuse that user's existing Codex login state.

The Agent MUST NOT read, return, persist, log, copy, or proxy Codex tokens, ChatGPT credentials, browser cookies, API keys, SSH keys, credential-helper secrets, or equivalent authentication material.

No caller-supplied credential/environment fields are accepted.

### R6 — Closed invocation schema

The model-facing action accepts only structured DevForge execution identity and transport data, including at minimum:

- normalized repository identity;
- exact `task_id`;
- `implementation | fixing` action;
- exact Requirement and Approved Plan references;
- exact `run_id` / `attempt_id`;
- exact `slice_id` when slicing is active;
- canonical GitHub PR number;
- canonical PR branch;
- expected remote branch head SHA.

It MUST NOT accept:

- free-form shell;
- arbitrary Codex argv;
- caller-selected cwd/workspace path;
- arbitrary environment variables;
- arbitrary executable/plugin/MCP configuration;
- replacement branch or PR identity;
- permission/sandbox bypass flags.

### R7 — Provider-derived isolated DevForge workspace

The bridge MUST derive the execution workspace from Host-owned DevForge workspace configuration plus repository/Task/Run/Attempt identity.

The caller never supplies an absolute workspace path.

The canonical checkout MUST remain `main + clean` and MUST NOT be the Codex cwd or mutation target.

A new direct-Codex workspace is independent execution state and MUST NOT mutate canonical checkout Git worktree metadata as a hidden side effect.

### R8 — Exact canonical transport bootstrap

Before Codex starts, the bridge MUST establish an exact local execution copy for the existing canonical transport using fixed provider-owned Git mechanics and the active-user Git context when required.

Admission MUST verify:

```text
repository identity
+ PR number
+ exact canonical branch
+ expected remote head SHA
```

No replacement branch/PR is created. Remote-head mismatch fails closed before Codex mutation.

This direct-adapter workspace bootstrap is NOT `repository_transaction_v1`, does not satisfy PR-013/PR-014 Host Runtime contracts, and cannot be reused as Host mutation-scope authority.

### R9 — Deterministic DevForge handoff package

The provider MUST compile the Codex task instructions from structured fields and canonical artifact references.

The caller MUST NOT receive a generic arbitrary-prompt field.

The handoff MUST tell Codex to:

- operate only on the supplied Task;
- consume the exact Requirement, Approved Plan, current Slice/fix findings;
- preserve the exact PR/branch transport;
- not create replacement branch/PR;
- not rewrite Requirement/Plan/Gate state;
- return changed files, verification evidence and transport receipt.

Repository content remains implementation context, not authority to override these bindings.

### R10 — Non-interactive Codex execution with bounded sandbox

The provider MUST use Codex's supported non-interactive execution mode and an explicit workspace-write sandbox profile or stronger bounded equivalent.

Approval/sandbox escalation, dangerous bypass flags and unrestricted filesystem mode are forbidden.

Before advertising readiness on a Windows Host, a physical self-check MUST prove that the selected Codex execution mode can mutate its exact execution workspace while failing to mutate a protected canonical-like sibling outside that workspace.

If that isolation cannot be proven, the direct Codex provider is unavailable.

### R11 — Bounded process lifecycle

One bridge call binds to one DevForge Run/Attempt[/Slice].

The provider MUST enforce:

- bounded timeout;
- process-tree cleanup on timeout/cancel/failure;
- no detached long-lived Codex child;
- bounded stdout/stderr/structured result size;
- durable invocation identity/evidence sufficient for readback;
- no automatic retry after an uncertain externally visible mutation.

### R12 — Structured completion and transport readback

Codex completion MUST produce a bounded machine-readable result or a provider-normalized result containing at least:

- task/run/attempt/slice identity;
- actual repository;
- canonical PR/branch and actual branch;
- resulting local head;
- verification summary;
- Codex exit disposition.

Before the bridge reports execution success it MUST independently read back the canonical remote branch and require transport consistency.

A missing/mismatched receipt is not success.

### R13 — Direct-host failure taxonomy

Use specific fail-closed states such as:

- `DirectCodexPolicyDisabled`
- `DirectCodexUserSessionUnavailable`
- `DirectCodexExecutableUnavailable`
- `DirectCodexExecutableIdentityMismatch`
- `DirectCodexWorkspaceAdmissionFailed`
- `DirectCodexTransportDrift`
- `DirectCodexSandboxUnavailable`
- `DirectCodexInvocationFailed`
- `DirectCodexTimeout`
- `DirectCodexReceiptInvalid`

Failure MUST NOT switch execution provider automatically.

### R14 — No generic-execution expansion

This Task MUST NOT solve the problem by:

- enabling generic `exec`;
- making `script_run` an arbitrary direct-host launcher;
- adding caller-supplied shell/argv/cwd/env;
- enabling `operator_unrestricted`;
- widening command/file allowlists;
- exposing a generic run-as-user primitive;
- allowing direct writes in canonical checkout;
- modifying production Hub.

### R15 — Composition with existing work

- PR-013 remains an independent Task and keeps ownership of Host Runtime `repository_transaction_v1`.
- PR-014 remains an independent Task and keeps ownership of Host Runtime DevForge execution-workspace materialization.
- PR-011 verification/toolchain semantics on current `main` remain canonical and must not regress.
- PR-010 canonical repository mutation firewall remains mandatory for existing SentinelX operations.
- This Task may unblock PR-013's **direct/Codex Development Host admission**, but it does not change PR-013's Plan, Slice or transport.

## Acceptance criteria

- **AC1:** `local_api.describe` exposes one bounded direct-Codex provider/action with no arbitrary command/executable/cwd/env/prompt fields.
- **AC2:** Provider readiness is absent/false when Host opt-in, active-user session, Codex executable identity, workspace binding or physical sandbox proof is unavailable.
- **AC3:** On an admitted Windows Host, exact installed Codex executes non-interactively under the active user's identity without SentinelX returning credential material.
- **AC4:** The provider creates/uses only the derived DevForge execution workspace; canonical checkout remains unchanged and `main + clean`.
- **AC5:** A physical negative test proves Codex cannot write a canonical-like protected sibling outside the exact workspace.
- **AC6:** Exact PR/branch/expected-head mismatch fails before implementation mutation.
- **AC7:** Codex receives the exact Requirement/Plan/Slice transport lock and cannot obtain a replacement transport from the bridge.
- **AC8:** One successful fixture execution returns a valid direct/Codex receipt with exact Task/Run/Attempt/Slice and transport identity.
- **AC9:** Timeout/nonzero/malformed receipt/transport drift returns a specific failure and no success claim.
- **AC10:** Existing `script_run`, `devforge_runtime`, mutation-scope, repository firewall and verification tests remain passing.
- **AC11:** No generic `exec`, no `operator_unrestricted`, no allowlist/permission widening, no Hub mutation.
- **AC12:** After live activation, `#开发执行 PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1` can pass direct/Codex provider admission through this bridge without changing PR-013 Task identity or project binding.

## Requirement Challenge

### Challenge 1 — Why not just enable `sentinel_exec codex`?

Rejected. That creates or expands a generic command surface and does not preserve the direct-adapter execution contract.

### Challenge 2 — Why not call `codex.cmd` through `script_run`?

Rejected. `script_run` is currently governed by Host mutation execution-profile policy; using it as a wrapper bypass would collapse two distinct execution-provider boundaries.

### Challenge 3 — Why not change the project binding to `host-runtime`?

Rejected. The current project binding is explicitly `direct/codex`; PR-014 also shows the Host Runtime workspace path is a separate incomplete capability. Provider substitution is not a repair.

### Challenge 4 — Why active-user execution?

The installed Codex login is user-scoped while SentinelX runs as a service identity. A fixed active-user broker is the narrowest way to reuse existing authentication without copying credentials.

### Challenge 5 — Why not make the active-user broker generic?

Rejected. A generic run-as-user primitive would become a privilege/credential-context expansion surface. Only fixed Codex and existing fixed Git brokers may use any shared internal token mechanics.

## Bootstrap implementation note

This Task repairs the exact capability needed by the current `direct/codex` project binding to execute it. After Plan approval, implementation admission SHOULD evaluate DevForge's Task-Scoped Bootstrap Execution Override contract rather than weakening the project binding or inventing a fallback.

The bootstrap override itself requires its own explicit canonical command and is not granted by this Requirement.

## Non-goals

- replacing DevForge's Codex adapter;
- changing the project-wide execution binding;
- implementing a generic coding-agent launcher;
- implementing arbitrary shells or run-as-user commands;
- modifying Codex itself;
- implementing PR-013 repository transactions;
- implementing PR-014 Host Runtime workspace materialization;
- modifying production Hub;
- production release/deployment.
