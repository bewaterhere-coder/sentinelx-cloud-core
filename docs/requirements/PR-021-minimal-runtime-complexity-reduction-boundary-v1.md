---
task_id: PR-021-minimal-runtime-complexity-reduction-boundary-v1
title: SentinelX Minimal Runtime & Complexity Reduction Boundary V1
project_id: sentinelx-cloud-core
repository: bewaterhere-coder/sentinelx-cloud-core
requirement_revision: 1
development:
  stage: implementation
  gates:
    requirement_ready: true
    plan_approved: true
    acceptance_approved: false
    completion_verified: false
  plan_revision: 1
  implementation_authorized: true
  blocking_findings: []
  next_expected_actor: reviewer
  current_slice: S04
  current_slice_state: completed
  completed_slices: [S01, S02, S03, S04]
  implementation_execution_complete: true
  formal_acceptance_performed: false
  canonical_next_action: "#开发验收 PR-021-minimal-runtime-complexity-reduction-boundary-v1"
  latest_execution_run: docs/execution/PR-021-minimal-runtime-complexity-reduction-boundary-v1-s04-run-001.yaml
  latest_execution_checkpoint: docs/checkpoints/PR-021-minimal-runtime-complexity-reduction-boundary-v1-s04-completion-20261008.yaml
transport:
  type: github-pr
  pr_number: 21
  branch: task/minimal-runtime-complexity-reduction-boundary-v1
  base_branch: main
artifacts:
  plan: docs/plans/PR-021-minimal-runtime-complexity-reduction-boundary-v1-plan.md
  latest_plan_review: docs/reviews/PR-021-minimal-runtime-complexity-reduction-boundary-v1-plan-review-r1.md
  latest_plan_review_transition_receipt: docs/reviews/PR-021-minimal-runtime-complexity-reduction-boundary-v1-plan-review-r1-transition-receipt.yaml
  execution_slice_set: docs/execution/PR-021-minimal-runtime-complexity-reduction-boundary-v1-slices.yaml
  latest_execution_run: docs/execution/PR-021-minimal-runtime-complexity-reduction-boundary-v1-s01-run-001.yaml
  latest_execution_checkpoint: docs/checkpoints/PR-021-minimal-runtime-complexity-reduction-boundary-v1-s01-completion-20261008.yaml
  latest_runtime_revalidation: docs/checkpoints/PR-021-minimal-runtime-complexity-reduction-boundary-v1-s01-runtime-drift-revalidation-20261008.yaml
  provisional_bootstrap: docs/checkpoints/minimal-runtime-complexity-reduction-boundary-v1-provisional-bootstrap.md
  architecture_decision: docs/architecture/sentinelx-minimal-runtime-boundary-v1.md
  disposition_matrix: docs/architecture/sentinelx-capability-disposition-matrix-v1.md
  pre_acceptance_evidence: docs/checkpoints/PR-021-minimal-runtime-complexity-reduction-boundary-v1-s04-acceptance-evidence-20261008.yaml
related_tasks:
  workspace_materialization_bridge: PR-014-devforge-execution-workspace-materialization-bridge-v1
  direct_codex_bridge: PR-015-direct-codex-development-host-invocation-bridge-v1
  stabilization_gate: PR-019-stable-baseline-stabilization-exit-gate-v1
  durable_async_runtime: PR-020-durable-async-operation-runtime-outcome-readback-v1
  devforge_incremental_execution_dependency: PR-229-incremental-execution-slice-v1
requirement_readiness:
  result: Ready
  ui_semantics:
    applicability: NotApplicable
  visual_fidelity:
    applicability: NotApplicable
---

# Requirement

## Problem

SentinelX has accumulated responsibilities beyond its core value as a secure bridge between ChatGPT and a local Host.

The current codebase and active development lineages now span:

- structured local API projection;
- generic command/script execution;
- scoped mutation execution;
- Host Mutation Scope lifecycle;
- Windows AppContainer / ACL / Job containment;
- write-ahead mutation audit;
- canonical repository mutation firewall;
- verification runtime;
- direct Codex discovery, sandboxing, workspace, persistence, transport and result handling;
- DevForge runtime execution projection;
- background job execution and result replay;
- execution workspace materialization;
- proposed durable asynchronous operation lifecycle and outcome reconciliation.

Individually these capabilities have valid motivations. Together they are causing SentinelX to become a development workflow engine, long-running Agent runtime, workspace manager and orchestration layer rather than a bounded security bridge.

The concrete pressure is the Hub request window. A Hub/local_api interaction is approximately 60 seconds and should be treated as a short control-plane / interaction window. Long-running development work can take minutes or substantially longer and has unbounded variance.

The wrong response is to keep extending the Hub execution lifecycle with:

~~~text
longer timeout
→ durable async runtime
→ operation lifecycle
→ reconnect/readback state
→ agent-specific execution bridges
→ workspace materialization dependencies
→ execution slicing/projection dependencies
→ more resume/orchestration semantics
~~~

That direction increases architecture surface and introduces new failure modes merely to keep a long-running development Agent inside a transport that is not intended to own its lifecycle.

## Goal

Freeze a minimal SentinelX runtime boundary before further long-running execution capability expansion.

SentinelX shall become:

> a secure, bounded, short-duration local capability bridge for ChatGPT.

Long-running or duration-uncertain development execution shall move outside the Hub request lifecycle and use guided / semi-interactive local CLI execution.

The first phase of this task is architecture-only. It must produce:

1. one Architecture Decision defining the minimal runtime boundary and execution-mode resolution;
2. one read-only capability inventory with a disposition for each material capability:
   - KEEP
   - SIMPLIFY
   - DEPRECATE
   - HOLD
3. explicit disposition analysis for PR-014, PR-020, PR-229 / `incremental_execution.slice_v1`, and direct CodeBuddy/Codex execution;
4. one minimal successor implementation order.

This task does not remove implementation in V1.

## User-selected boundary

### R1 — Hub is a short control-plane window

The Hub request/local_api window is a bounded interaction window, not a long-running job budget.

SentinelX must not solve long development work by:

- extending the Hub timeout;
- keeping the request open until CodeBuddy/Codex finishes;
- introducing a new durable long-running Agent lifecycle solely to survive the request window;
- adding additional execution slicing/orchestration layers whose purpose is to make the Hub own long tasks.

No exact wall-clock threshold other than the Host's real bounded window is granted as execution authority. Duration estimation is advisory only.

### R2 — Direct SentinelX responsibilities

The minimal runtime must continue to support short, bounded, auditable local work including:

- read;
- bounded file write;
- short command execution;
- short verification;
- Host Mutation Scope;
- sandbox / AppContainer containment where mutation requires it;
- audit;
- MCP Tool Projection / structured local capability projection;
- canonical repository mutation protection;
- receipt / read-back verification.

Security boundaries are not simplification targets merely because they add code.

### R3 — Guided CLI for long or uncertain work

The following classes are outside the Hub execution lifecycle by default:

- CodeBuddy Agent execution;
- Codex Agent execution;
- large builds;
- long test suites;
- large refactors;
- any operation whose duration is materially uncertain or likely to outlive the bounded interaction window.

For these cases ChatGPT/DevForge should emit a complete, copyable guided CLI handoff containing at least:

- repository;
- canonical Task ID;
- canonical PR/branch when applicable;
- current workflow stage;
- exact Requirement and Plan references/revisions;
- allowed mutation scope;
- forbidden actions;
- verification requirements;
- expected evidence / receipt / commit or read-back result.

The user runs the CLI locally and returns durable evidence. SentinelX does not need to hold the Agent lifecycle open.

### R4 — ChatGPT should still execute genuinely short work

The new boundary must not turn every local mutation into manual CLI work.

When a task is bounded, short, within the already-authorized scope and can be completed reliably inside the interaction window, ChatGPT/SentinelX may execute it directly.

Examples include:

- small file edits;
- configuration or schema edits;
- short Git inspection/operations permitted by policy;
- narrow unit/static checks;
- read-back verification.

The execution-mode resolver must prefer the simplest valid path rather than automatically launching a development Agent.

### R5 — Preserve security complexity, remove orchestration complexity

The disposition process must distinguish security-critical complexity from orchestration complexity.

Security-critical capabilities require a strong presumption of KEEP, including:

- Host Mutation Scope authority;
- fail-closed mutation audit;
- Windows mutation sandbox / AppContainer / ACL / Job containment;
- canonical repository firewall;
- operation/effect registration used by repository safety;
- structured tool projection and schema validation;
- exact receipt/read-back verification needed to prove effects.

A capability must not be deprecated if doing so weakens an existing safety boundary.

### R6 — Capability inventory is evidence-based

The inventory must use current `sentinelx-cloud-core/main` plus live open PR/task artifacts as evidence.

At minimum it must inspect and classify:

- `src/sentinelx_core/handlers/direct_codex.py` and supporting `direct_codex_*.py`;
- `src/sentinelx_core/handlers/devforge_runtime.py`;
- `src/sentinelx_core/local_api.py` and `handlers/local_api.py`;
- `src/sentinelx_core/jobs.py`;
- `src/sentinelx_core/pending_results.py`;
- `src/sentinelx_core/mutation_scope.py`;
- `src/sentinelx_core/mutation_audit.py`;
- `src/sentinelx_core/windows_mutation_sandbox.py`;
- `src/sentinelx_core/operation_registry.py`;
- `src/sentinelx_core/canonical_repository_firewall.py`;
- scoped verification / scoped script paths materially affected by the boundary;
- open PRs/tasks that exist primarily to support long-running development orchestration.

Each matrix entry must include evidence, current responsibility, disposition, rationale, dependency impact and successor/retirement action.

### R7 — PR-014 must be re-evaluated, not automatically continued

PR-014 DevForge Execution Workspace Materialization Bridge V1 currently exists to provide a DevForge execution workspace capability and is blocked by direct invocation/projection dependencies.

The new architecture must decide which part, if any, remains necessary for short bounded mutations.

The task must not assume either:

- all workspace materialization is unnecessary; or
- the current PR-014 bridge must be completed unchanged.

If safe short mutation still requires provider-owned isolated workspace materialization, retain only that minimal security/execution substrate. Long-Agent bootstrap/projection requirements must not justify additional Hub orchestration complexity.

### R8 — PR-020 must be evaluated against the new boundary

PR-020 Durable Async Operation Runtime & Outcome Readback V1 is the strongest counterproposal to this requirement.

It addresses a real defect: a long operation can outlive the synchronous request and leave the caller without a durable handle/receipt.

However the new product decision is to remove long-running development Agent work from the Hub lifecycle rather than make SentinelX own a generic durable long-operation state machine for that use case.

The architecture decision must therefore determine whether PR-020 should be:

- HOLD;
- narrowed to non-development use cases that independently require durable background execution;
- replaced by existing background job/result-delivery semantics where adequate;
- or deprecated as unnecessary for the minimal runtime.

PR-020 must not continue unchanged without passing this architecture boundary.

### R9 — PR-229 / incremental execution slicing remains a DevForge concern unless independently required

DevForge's `incremental_execution.slice_v1` / incremental plan execution slicing semantics may remain valuable inside DevForge for task planning, checkpointing and safe bounded implementation progression.

SentinelX must not grow special orchestration or bootstrap dependencies merely to host that workflow inside a long Hub call.

The Architecture Decision must separate:

~~~text
DevForge workflow semantics
!= SentinelX execution lifecycle ownership
~~~

If DevForge chooses one-slice-per-command semantics, the Host bridge should expose only the minimal short operation needed for a slice that is actually suitable for direct execution. A long slice must resolve to guided CLI rather than timeout extension.

### R10 — Direct CodeBuddy/Codex execution is not a core SentinelX responsibility

Direct development Agent lifecycle management is outside the minimal runtime unless a future requirement independently proves a bounded short use case.

The inventory must explicitly evaluate:

- Direct Codex local_api provider;
- Codex discovery;
- Codex-specific ACL/sandbox/workspace/persistence/result/transport support;
- any CodeBuddy direct invocation projection;
- task-scoped bootstrap mechanisms that exist only to force a long Agent through SentinelX.

No deletion occurs in this task, but the disposition matrix must make ownership and retirement/hold direction explicit.

### R11 — Existing background jobs are not automatically removed

`jobs.py` already supports Agent-side background jobs with a longer timeout, and `pending_results.py` persists completion delivery when the socket disappears.

These capabilities predate the proposed minimal-development boundary and may support legitimate non-development operations.

The inventory must distinguish:

- generic background execution capability with independent product value;
- development-Agent orchestration that should move to guided CLI.

A capability is not deprecated merely because it can run longer than 60 seconds.

### R12 — No source deletion in first phase

The implementation phase of this V1 task may modify only documentation / development artifacts required to freeze the architecture decision and disposition matrix.

It must not:

- delete or disable production source;
- remove a local_api provider;
- change tool exposure;
- change project binding;
- change production Hub behavior;
- change service installation;
- change Host permissions;
- modify DevForge Runtime;
- close or merge PR-014/019/020 automatically.

Those become explicit successor decisions/tasks after this V1 is accepted.

### R13 — One minimal successor sequence

The output must recommend exactly one primary implementation sequence after the architecture is accepted.

The sequence should minimize simultaneous change and dependency churn.

It must identify, at minimum:

1. which active PR/task should be paused/closed/reshaped first;
2. the smallest execution-mode routing change needed to establish guided CLI;
3. which long-Agent-specific SentinelX surfaces can later be retired or simplified;
4. which security substrates remain untouched;
5. what evidence proves the resulting minimal runtime still supports normal short ChatGPT operations.

## Current evidence baseline

At `sentinelx-cloud-core/main@1028030b33f0ea792a884491a431fffe566f6aa5`:

- the Direct Codex provider explicitly owns a closed local_api endpoint and a provider-owned execution path;
- the Direct Codex source contains a real Codex sandbox probe timeout of 300 seconds, demonstrating that this path already exceeds the Hub interaction window;
- `jobs.py` allows background work up to one hour;
- `pending_results.py` explicitly states it persists the answer, not the running job, and that the work still dies with the Agent process;
- `local_api.py` is a synchronous structured request/response transport with endpoint timeouts;
- `mutation_audit.py` is fail-closed and requires durable audit before materialization/process spawn;
- `windows_mutation_sandbox.py` is a fail-closed AppContainer + exact ACL + Job security boundary;
- `operation_registry.py` is the authoritative operation/effect registration used for repository safety;
- PR-014 is open and blocked in its current execution/bootstrap lineage;
- PR-020 is open and proposes a generic Durable Async Operation Runtime;
- PR-019 remains the stabilization-exit owner.

These facts are sufficient to justify an architecture decision before further implementation expansion.

## Non-goals

V1 does not:

- implement the guided CLI adapter;
- remove Direct Codex code;
- implement CodeBuddy integration;
- finish PR-014;
- implement PR-020;
- modify DevForge incremental execution contracts;
- remove generic background jobs;
- redesign all SentinelX operations;
- weaken sandbox/audit/mutation scope/firewall protections;
- attempt to make SentinelX feature-minimal at the expense of security;
- define a new scheduler or durable long-running job runtime.

## Acceptance criteria

1. one canonical Architecture Decision exists under `docs/architecture/`;
2. the Architecture Decision explicitly defines SentinelX as a short-duration secure capability bridge;
3. it defines direct-short versus guided-CLI execution mode resolution;
4. it forbids timeout extension as the primary long-development-task solution;
5. one capability disposition matrix exists under `docs/architecture/`;
6. every material current capability is classified KEEP, SIMPLIFY, DEPRECATE or HOLD with evidence and dependency impact;
7. PR-014 has an explicit disposition and rationale;
8. PR-020 has an explicit disposition and rationale;
9. PR-229 / `incremental_execution.slice_v1` is separated from SentinelX lifecycle ownership;
10. Direct CodeBuddy/Codex execution has an explicit ownership/disposition decision;
11. Host Mutation Scope, sandbox/AppContainer, audit, canonical repository firewall and receipt/read-back safety are preserved;
12. no product source file is deleted or behaviorally disabled by this V1;
13. no production Hub change occurs;
14. no project binding changes;
15. the strongest counterargument for Durable Async automation is recorded and answered;
16. one primary minimal successor implementation order is frozen;
17. current main and open-PR evidence used by the decision is revisioned/identified;
18. the final documentation is sufficient for a fresh DevForge session to decide what to implement next without relying on chat history.

## Strongest counterevidence

A generic Durable Async Runtime can preserve automation, survive request loss and provide deterministic read-back without manual CLI handoff. PR-020 is a technically coherent response to the observed timeout problem.

This V1 must not dismiss that evidence.

The decision in favor of guided CLI is valid only if the Architecture Decision demonstrates that:

- SentinelX does not need to own long development Agent lifecycle to satisfy its core product purpose;
- CLI execution can preserve DevForge Task/Requirement/Plan/transport identity and return verifiable evidence;
- removing the Hub from the long-task lifecycle materially reduces state machines, recovery paths and provider-specific dependencies;
- security boundaries remain intact;
- any legitimate non-development async requirement can be evaluated separately instead of being used to justify a universal development orchestration runtime.

## Requirement readiness

~~~yaml
requirement_ready: true
refinement_depth: deep
ui_semantics: NotApplicable
visual_fidelity: NotApplicable
material_product_decision_pending: false
product_decision:
  long_development_execution: guided_cli_outside_hub_lifecycle
  sentinelx_role: secure_short_duration_local_capability_bridge
first_phase_source_deletion: forbidden
first_phase_product_behavior_change: forbidden
implementation_p0_dependencies: []
~~~
