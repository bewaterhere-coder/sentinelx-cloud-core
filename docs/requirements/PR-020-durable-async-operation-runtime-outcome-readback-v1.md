---
task_id: PR-020-durable-async-operation-runtime-outcome-readback-v1
title: SentinelX Durable Async Operation Runtime & Outcome Readback V1
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
  blocking_findings: []
  next_expected_actor: reviewer
transport:
  type: github-pr
  pr_number: 20
  branch: task/durable-async-operation-runtime-outcome-readback-v1
  base_branch: main
artifacts:
  plan: docs/plans/PR-020-durable-async-operation-runtime-outcome-readback-v1-plan.md
  latest_plan_review: docs/reviews/PR-020-durable-async-operation-runtime-outcome-readback-v1-plan-review-r1.md
  latest_plan_review_transition_receipt: docs/reviews/PR-020-durable-async-operation-runtime-outcome-readback-v1-plan-review-r1-transition-receipt.yaml
  latest_plan_remediation: docs/checkpoints/PR-020-durable-async-operation-runtime-outcome-readback-v1-plan-remediation-r2-20261008.yaml
  latest_plan_remediation_transition_receipt: docs/reviews/PR-020-durable-async-operation-runtime-outcome-readback-v1-plan-remediation-r2-transition-receipt.yaml
related_tasks:
  stabilization_gate: PR-019-stable-baseline-stabilization-exit-gate-v1
  observed_trigger: PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1
  provider_predecessor: PR-015-direct-codex-development-host-invocation-bridge-v1
requirement_readiness:
  result: Ready
  ui_semantics:
    applicability: NotApplicable
---

# Requirement

## Problem

SentinelX already has Agent-side background jobs and pending-results replay, but these do not form a canonical durable operation runtime. The current pending-results module explicitly persists completed answers only; executing work still belongs to the current Agent process. Builtin local_api calls also execute synchronously inside the request/response window.

A real PR-013 S03 execution exposed the missing boundary:

~~~text
DevForge #开发执行
→ SentinelX devforge_direct_codex.execute_task admitted
→ physical containment proof became verified
→ Codex/verification continued beyond the MCP request window
→ caller received a 60-second local_api timeout
→ no operation handle / durable terminal receipt was returned
→ safe retry could not be proven
~~~

The system could no longer distinguish still-running, failed-before-effect, completed-with-lost-response, or externally-completed-with-lost-acknowledgement.

This is not Codex-specific. Any SentinelX operation that can outlive a synchronous transport window or produce externally durable side effects can hit the same ambiguity.

## Goal

Add one provider-neutral Durable Async Operation Runtime that lets eligible SentinelX operations:

~~~text
admit exact operation identity
→ persist durable operation record before material side effects
→ return operation_id promptly
→ execute asynchronously under the owning provider authority
→ persist state/evidence
→ persist terminal outcome / receipt before delivery
→ allow status + receipt read-back after timeout, reconnect or fresh caller session
→ reconcile uncertain external outcomes without replay
~~~

The runtime must be reusable by Direct Development Hosts, Host Runtime builtin providers, scoped verification/materialization/publication operations, existing background exec/script jobs where compatible, and future long-running SentinelX providers.

No provider may invent a competing async lifecycle.

## Core identity

The runtime introduces one SentinelX correlation identity: operation_id.

operation_id must not replace or reinterpret upstream identities such as DevForge task_id, run_id, attempt_id, slice_id, canonical repository/PR/branch, provider_run_id, or narrower mutation-audit operation identities.

Where upstream lineage exists, the operation record binds it exactly. Hub job_id, PID, session ID and provider run IDs are evidence/correlation only.

## Required behavior

### R1 — Explicit async eligibility

Not every operation becomes asynchronous.

A provider/action is eligible only when it explicitly registers a Durable Async V1 descriptor containing at least:

- provider/action identity;
- deterministic semantic identity source;
- request validation/schema;
- side-effect class;
- terminal receipt/result sanitizer;
- optional uncertain-outcome reconciler;
- bounded timeout/retention policy.

Unknown or unregistered actions fail closed. Eligibility is never inferred from model name, provider name, repository, duration or chat intent.

### R2 — Prompt admission acknowledgement

Starting an eligible operation returns promptly without waiting for the long-running body:

~~~yaml
accepted: true
operation_id: <opaque durable id>
status: ADMITTED | RUNNING
request_digest: <digest>
identity_digest: <digest>
status_readback_available: true
receipt_readback_available: true
~~~

No Host path, PID, credential, workspace path or provider-private state is needed by the caller to read it later.

### R3 — Durable state before material side effects

Before material side effects, SentinelX persists an operation record equivalent to:

~~~yaml
schema_version: "1.0"
operation_id: <id>
provider: <provider>
action: <action>
identity_digest: <digest>
request_digest: <digest>
lineage:
  task_id: <optional>
  run_id: <optional>
  attempt_id: <optional>
  slice_id: <optional>
transport:
  repository: <optional>
  pr: <optional>
  branch: <optional>
state: ADMITTED
receipt_ref: null
external_effects_verified: false
~~~

No durable admission record means no async execution start.

### R4 — Single canonical lifecycle

V1 uses one shared lifecycle:

~~~text
ADMITTED
→ RUNNING
→ VERIFYING
→ SUCCEEDED

or terminal/non-success states:
FAILED
BLOCKED
INTERRUPTED
OUTCOME_UNKNOWN
~~~

State and reason code are separate. Provider-specific statuses normalize into this lifecycle instead of defining another state machine.

SUCCEEDED is permitted only after required verification and durable receipt persistence.

### R5 — Status read-back

A generic bounded read API returns current durable state by operation_id, including:

- provider/action;
- state and reason;
- timestamps;
- safe upstream lineage refs;
- terminal-receipt presence;
- external-effect verification state;
- reconciliation-required flag.

It must not expose credentials, raw environment variables, unrestricted command lines, canonical checkout paths or provider-private authorization material.

### R6 — Durable receipt read-back

Terminal success produces a durable receipt before success is reported.

The provider-neutral envelope binds:

- operation_id;
- provider/action;
- request digest;
- semantic identity digest;
- upstream Task/Run/Attempt/Slice lineage when present;
- canonical transport identity when present;
- terminal state;
- start/finish timestamps;
- verification disposition;
- external-effect disposition;
- provider evidence/receipt digest;
- read-back digest.

No receipt means no completion claim.

### R7 — Retry/idempotency

A semantically identical retry must not blindly execute again.

~~~text
same semantic identity + same request digest + active operation
→ return same operation_id/status

same semantic identity + same request digest + terminal operation
→ return same operation_id/receipt

same semantic identity + changed authority-bearing request
→ conflict; no execution

verified external side effect already exists
→ replay forbidden
~~~

For DevForge-bound operations, Task/Run/Attempt/Slice plus exact canonical transport participate in identity.

Existing Hub job_id may be bound as transport correlation when present but is not canonical semantic identity.

### R8 — Outcome-unknown reconciliation

Timeout, process interruption or lost acknowledgement must not be converted automatically into failure or success.

~~~text
OUTCOME_UNKNOWN
→ provider reconciler performs read-only/read-back-first inspection
→ reconcile to SUCCEEDED / FAILED / BLOCKED / INTERRUPTED
OR remain OUTCOME_UNKNOWN
~~~

A reconciler may not replay the original material side effect merely to discover the outcome.

Examples include exact remote Git read-back, exact persisted artifact digest read-back, provider-owned durable evidence, or a dedicated external deployment read API.

If no deterministic reconciler exists, OUTCOME_UNKNOWN remains and blind retry is blocked.

### R9 — Connection lifecycle independence

A completed operation receipt remains readable after:

- the original MCP request times out;
- WebSocket disconnect/reconnect;
- Hub worker/session change;
- a fresh ChatGPT conversation;
- loss of the response that acknowledged completion.

Existing pending-result replay should be reused where useful, but durable operation truth must not depend on successful Hub delivery.

### R10 — Agent restart semantics

V1 need not keep arbitrary child processes alive across an Agent service restart, but durable state must survive restart.

On startup:

1. terminal records remain terminal and readable;
2. nonterminal records are revalidated;
3. deterministic provider read-back may reconcile an external outcome;
4. otherwise state becomes INTERRUPTED or OUTCOME_UNKNOWN according to evidence;
5. stale pre-restart state is never reported as proven-live RUNNING;
6. material operations are never auto-replayed.

### R11 — Existing background jobs composition

Existing background=true exec/script behavior remains compatible.

The existing job_completed event and notifications flow may remain a delivery surface, but:

~~~text
durable operation truth
!= transient WebSocket delivery
!= Hub notification record
~~~

Where adopted, job_id binds to the durable operation record and terminal delivery derives from the same persisted outcome.

### R12 — Generic local_api surface

Production mcp.sentinelx.app remains an immutable external transport boundary.

The new start/read-back surface must fit through the existing sentinel_local_api envelope.

Recommended Agent-owned builtin endpoint:

~~~text
sentinel_operations
~~~

Recommended actions:

~~~text
start
status
receipt
~~~

start may invoke only actions registered in the Durable Async eligibility registry. It is not a generic arbitrary endpoint/action forwarder.

The caller cannot select executables, Host paths, credentials, permissions or unregistered actions.

### R13 — Provider-neutral adoption

V1 architecture must support these consumer classes without provider-specific runtime forks:

1. Direct Development Host actions such as current Direct Codex execution;
2. Host Runtime builtin actions such as long devforge_runtime execution;
3. scoped verification/materialization/publication operations when they exceed synchronous windows;
4. existing top-level background exec/script through compatibility composition;
5. future builtin providers that explicitly register Durable Async V1.

The core runtime contains no Codex-, CodeBuddy-, game-, Unity-, repository- or model-specific lifecycle semantics.

### R14 — Authority preservation

Durable async changes timing and observability only.

It must not broaden file write scope, mutation scope, AppContainer/Job authority, canonical repository mutation authority, Git credentials, service control, provider permissions, project binding, canonical transport, DevForge identities, force push, merge, release or deployment authority.

Existing provider admission and security boundaries remain authoritative.

### R15 — Cancellation

V1 does not expose generic process kill/cancel as new caller authority unless an owning provider already has an explicit safe cancellation contract.

Observation by operation_id is not process-control authority.

### R16 — Retention and cleanup

Terminal operation records have bounded Host-owned retention.

- nonterminal or OUTCOME_UNKNOWN records are not deleted merely because the request timed out;
- receipt retention must preserve verifiability for the declared window;
- cleanup targets only provider-owned operation-state storage;
- no generic recursive Host deletion fallback;
- retention is not caller-selected.

### R17 — Audit

Lifecycle transitions must be auditable without secrets, including operation_id, provider/action, identity/request digests, transition, reason, upstream lineage refs, provider evidence/receipt ref and external-effect verification flag.

Hidden reasoning, raw credentials and full environment snapshots are forbidden.

## Stabilization relation

PR-019 Requirement R3 classifies inability to produce required audit/receipt/read-back evidence as a baseline_blocker.

The observed PR-013 attempt proves that concrete defect on the current baseline Direct Codex path: execution admission occurred, containment reached verified, synchronous local_api timed out, no durable operation handle/receipt was returned, and safe retry could not be established.

PR-020 owns the generic infrastructure repair.

PR-019 continues to own stabilization-exit classification and consumes PR-020 evidence rather than reimplementing async operation semantics.

## Non-goals

V1 does not:

- modify or deploy production Hub source/schema;
- make every short operation asynchronous;
- replace DevForge Execution Run Runtime;
- create a scheduler;
- make arbitrary child processes survive Agent restart;
- add generic process cancellation;
- silently retry failed/unknown operations;
- add provider fallback;
- change project binding;
- broaden credentials or permissions;
- replace mutation audit, sandbox, Job or canonical repository firewall;
- absorb PR-013 repository transaction semantics;
- absorb PR-019 stabilization semantics.

## Acceptance criteria

1. one provider-neutral Durable Async Operation Runtime exists;
2. operation state is durable before material side effects;
3. eligible long-operation start returns promptly with operation_id;
4. status read-back works after the original request ended;
5. terminal receipt read-back works independently of WebSocket delivery;
6. identical semantic retry returns the existing operation instead of replaying;
7. authority-changing duplicate request conflicts fail closed;
8. success requires a persisted verified receipt;
9. lost response after successful side effect can reconcile by read-back without replay;
10. no deterministic reconciliation leaves OUTCOME_UNKNOWN and blocks blind retry;
11. Agent restart preserves durable records and never treats stale RUNNING as proven-live;
12. pending-results replay remains compatible but is not canonical operation truth;
13. existing background exec/script behavior remains compatible;
14. Direct Codex uses the generic runtime without a Codex-specific lifecycle;
15. a Host Runtime builtin long action uses the same runtime contract;
16. local_api cannot start unregistered actions;
17. callers cannot inject executable/path/credential/permission authority;
18. canonical repository firewall semantics remain unchanged;
19. AppContainer/Job/mutation scope semantics remain unchanged;
20. project direct/codex binding remains unchanged;
21. a real long-running Direct Codex fixture exceeds the normal synchronous window, returns a prompt operation handle, completes, and is later read back with a verified receipt;
22. a lost-completion-response fixture returns the same receipt on later read-back;
23. restart during a nonterminal fixture never replays the side effect and resolves by reconciliation or OUTCOME_UNKNOWN;
24. PR-013 S03 is never blindly replayed as acceptance proof.

## Requirement readiness

~~~yaml
requirement_ready: true
ui_semantics: NotApplicable
visual_fidelity: NotApplicable
material_product_decision_pending: false
implementation_p0_dependencies: []
acceptance_external_evidence:
  - Windows Agent long-running builtin operation fixture
  - reconnect/lost-response readback
  - restart reconciliation
  - Direct Codex generic-runtime adoption proof
~~~
