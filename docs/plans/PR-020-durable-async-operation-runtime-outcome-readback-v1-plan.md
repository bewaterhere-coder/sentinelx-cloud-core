# PR-020 SentinelX Durable Async Operation Runtime & Outcome Readback V1 — Plan R1

## Status

~~~yaml
task_id: PR-020-durable-async-operation-runtime-outcome-readback-v1
plan_revision: 1
plan_status: ready_for_review
implementation_authority: false
requirement_ref: docs/requirements/PR-020-durable-async-operation-runtime-outcome-readback-v1.md
requirement_revision: 1
transport:
  type: github-pr
  pr_number: 20
  branch: task/durable-async-operation-runtime-outcome-readback-v1
  base: main
repository_baseline:
  main_sha: 1028030b33f0ea792a884491a431fffe566f6aa5
runtime:
  devforge_version: 2.95.0
  devforge_revision: 162337cc2fffa710d49a9cd38ab4cc8643f09ffb
~~~

## Objective

Implement one generic durable operation runtime over the existing SentinelX Agent execution substrate so long-running operations can return a stable handle immediately, persist lifecycle/outcome evidence, survive transport disconnects as readable state, reconcile uncertain external outcomes without replay, and expose bounded status/receipt read-back through the existing local_api transport.

The design reuses current mechanisms:

~~~text
Hub background job / job_id
           │
           │ transport correlation only
           ▼
SentinelX Durable Operation Runtime
  ├─ durable admission/state store
  ├─ deterministic semantic identity
  ├─ provider/action eligibility registry
  ├─ async task ownership
  ├─ terminal receipt store
  ├─ restart reconciliation
  └─ outcome-unknown read-back-first reconciliation
           │
   ┌───────┼──────────┐
   │       │          │
direct   host-      existing
host     runtime    background
actions  builtins   exec/script
   │       │          │
   └───────┴──────────┘
           │
pending_results / job_completed
delivery compatibility only
~~~

Provider-specific execution authority remains inside each provider. The generic runtime owns only async lifecycle, persistence, deduplication and read-back.

## Current repository reality

Current main already contains useful primitives:

- src/sentinelx_core/jobs.py: background timeout, job_completed event construction and mutation identity validation;
- src/sentinelx_core/pending_results.py: completed-result staging before WebSocket send and reconnect replay, explicitly not a job registry;
- src/sentinelx_core/client.py: request.payload.background dispatch, immediate job_id acknowledgement and detached Agent asyncio task;
- src/sentinelx_core/handlers/local_api.py: synchronous builtin local_api invocation;
- src/sentinelx_core/handlers/direct_codex.py: current long-running Direct Codex builtin path;
- src/sentinelx_core/handlers/devforge_runtime.py: Host Runtime builtin control surface;
- DevForge Execution Run Runtime: upstream Task/Run/Attempt/Slice authority.

Observed gap:

~~~text
builtin local_api long action
→ no generic async acknowledgement
→ caller waits for provider body
→ transport window expires
→ provider may still be running
→ no operation handle available
→ safe replay decision unavailable
~~~

## Technical decisions

### D1 — New provider-neutral core

Recommended module:

~~~text
src/sentinelx_core/durable_operations.py
~~~

Responsibilities:

- operation identity model;
- durable operation/receipt store;
- lifecycle transition validation;
- request/identity digesting;
- duplicate start resolution;
- terminal receipt persistence;
- restart scan/reconciliation;
- bounded retention;
- sanitized read models.

Suggested abstractions:

~~~text
DurableOperationDescriptor
DurableOperationIdentity
DurableOperationRecord
DurableOperationReceipt
DurableOperationStore
DurableOperationRegistry
DurableOperationRuntime
~~~

The module contains no Codex-, CodeBuddy-, Unity-, game- or repository-specific logic.

### D2 — Provider descriptor contract

Each async-capable action registers a static provider-owned descriptor equivalent to:

~~~yaml
provider: <stable provider id>
action: <stable action id>
schema_revision: 1
side_effect_class: read | process | filesystem | repository | service | other
identity_resolver: provider_owned
request_validator: provider_owned
execution_callback: provider_owned
result_sanitizer: provider_owned
reconciler: optional
retention_class: host_policy_owned
~~~

No caller may register descriptors.

### D3 — Deterministic semantic identity

The runtime computes:

~~~text
identity_digest = H(provider + action + sealed semantic identity)
request_digest  = H(canonical validated request)
~~~

For DevForge providers, semantic identity includes applicable Task/Run/Attempt/Slice and exact canonical transport.

Resolution:

~~~text
no prior identity
→ create operation

same identity + same request
→ return existing operation

same identity + changed request
→ OperationIdentityConflict
~~~

No caller-selected operation_id participates in admission.

### D4 — Durable store before execution

Use provider-owned Agent state storage, logically:

~~~text
<agent-state>/durable-operations/
  records/<operation_id>.json
  receipts/<operation_id>.json
~~~

Exact Host paths remain runtime authority and are not projected as caller authority.

Writes use atomic write-then-rename. ADMITTED must be durable before the executor callback starts.

### D5 — Canonical lifecycle

Allowed principal transitions:

~~~text
ADMITTED -> RUNNING
RUNNING -> VERIFYING
VERIFYING -> SUCCEEDED

ADMITTED/RUNNING/VERIFYING -> FAILED
ADMITTED/RUNNING/VERIFYING -> BLOCKED
RUNNING/VERIFYING -> INTERRUPTED
RUNNING/VERIFYING -> OUTCOME_UNKNOWN

OUTCOME_UNKNOWN -> SUCCEEDED | FAILED | BLOCKED | INTERRUPTED
~~~

Terminal states do not return to RUNNING under the same operation identity.

### D6 — Async task ownership

The runtime owns only the in-Agent asyncio task that calls the already-authorized provider callback.

- persist ADMITTED;
- transition RUNNING immediately before callback;
- callback result enters VERIFYING;
- provider sanitizer/verification produces terminal evidence;
- terminal receipt persists before SUCCEEDED;
- disconnect does not cancel work only because requester disappeared;
- callback exception becomes FAILED only when absence of uncertain effects is proven, otherwise OUTCOME_UNKNOWN.

This is not an OS scheduler.

### D7 — Generic builtin endpoint

Recommended Agent-owned builtin endpoint:

~~~text
sentinel_operations
~~~

Actions:

~~~yaml
start:
  target:
    provider: <registered builtin provider>
    action: <registered async-capable action>
  request: <target action request>

status:
  operation_id: <opaque id>

receipt:
  operation_id: <opaque id>
~~~

Security:

- target must exist in DurableOperationRegistry;
- configured arbitrary external local_api endpoints are excluded from V1 start;
- owning provider validates request before persistence/execution;
- status/receipt are read-only;
- no list-all action;
- no generic cancel action;
- no caller path/executable/credential/provider-policy override.

### D8 — Provider adapter boundary

Providers expose their existing execution callback plus descriptor metadata.

The generic runtime invokes the same internal implementation logic; provider business logic is not forked into separate sync/async implementations.

Backward-compatible synchronous actions may remain while callers migrate.

### D9 — Direct Codex adoption

Direct Codex is the first real long-running builtin consumer.

Refactor only enough to expose equivalents of:

~~~text
validate_execute_task
resolve_execute_task_identity
execute_task_internal
sanitize_execute_task_receipt
reconcile_execute_task_outcome
~~~

Existing direct/codex behavior remains authoritative:

- exact PR/branch/head;
- isolated workspace;
- containment proof;
- active-user Codex invocation;
- deterministic provider persistence;
- non-force publication;
- remote read-back;
- ACL handoff/revocation;
- canonical checkout protection.

The generic runtime knows none of these details.

For uncertain publication, the provider reconciler reads exact remote/provider persistence evidence first and never re-runs Codex or re-pushes merely to discover outcome.

### D10 — Host Runtime adoption

At least one current long Host Runtime builtin action must adopt the same runtime, preferably devforge_runtime execute_scoped where its existing contract permits long execution.

Existing scoped_mutation, mutation scope, AppContainer, Job and audit semantics remain authoritative. No second executor or execution profile is introduced.

### D11 — Existing background exec/script compatibility

Current Hub behavior remains supported:

~~~text
background=true + job_id
→ immediate running ack
→ detached execution
→ job_completed event
→ notifications
~~~

Where migrated internally:

- job_id remains Hub transport correlation;
- it binds to a durable operation record;
- terminal job_completed derives from the persisted terminal operation outcome;
- pending_results remains WebSocket-delivery replay;
- no second independent truth exists.

If a compatibility edge cannot safely migrate in V1, legacy behavior remains, but tests must prove no regression and core design must support later registration without redesign.

### D12 — pending_results remains delivery replay

pending_results owns only:

~~~text
terminal delivery payload exists
+ WebSocket send fails
→ persist delivery copy
→ replay on reconnect
~~~

Durable operation receipt exists before the delivery copy.

### D13 — Restart reconciliation

On startup:

~~~text
terminal receipt exists
→ preserve/repair matching terminal record

provider reconciler available
→ bounded read-only/read-back-first reconciliation

external effect proven complete
→ persist terminal receipt

external effect proven absent and provider declares safe interruption
→ INTERRUPTED

outcome not provable
→ OUTCOME_UNKNOWN
~~~

Startup never invokes the original material callback.

### D14 — Exactly-once claim boundary

V1 does not claim universal exactly-once execution.

It guarantees:

- durable admission before execution;
- deterministic duplicate detection;
- no blind same-identity replay;
- terminal receipt persistence before success;
- read-back-first reconciliation when possible.

External systems without deterministic read-back remain OUTCOME_UNKNOWN.

### D15 — Audit

Audit lifecycle transitions using only bounded metadata:

- operation_id;
- provider/action;
- identity/request digests;
- from/to state;
- reason;
- upstream lineage refs;
- provider evidence digest;
- external-effect verified flag.

No raw credentials, full environment or hidden reasoning.

### D16 — Stable Baseline relation

PR-020 repairs the concrete receipt/read-back blocker exposed during PR-019 stabilization work.

PR-020 Acceptance proves generic runtime behavior. PR-019 later consumes that evidence and retains sole stabilization-exit authority.

PR-020 never mutates PR-019 state.

## Implementation slices

Formal Slice Set is compiled only after Plan Review approval.

### S01 — Core durable operation runtime

Objective: implement identity, state machine, durable record/receipt store, duplicate resolution, retention eligibility and restart reconciliation skeleton without production provider adoption.

Likely files:

~~~text
src/sentinelx_core/durable_operations.py
tests/test_durable_operations.py
~~~

Required verification:

1. ADMITTED is durable before callback invocation;
2. same identity/request returns same operation;
3. changed request conflicts;
4. invalid transition fails closed;
5. SUCCEEDED without durable receipt is impossible;
6. terminal state is immutable;
7. restart never treats stale RUNNING as proven-live;
8. unknown reconciliation remains OUTCOME_UNKNOWN;
9. provider-specific imports/semantics absent;
10. atomic-write failure prevents callback start;
11. malformed/tampered record fails closed.

### S02 — sentinel_operations local_api surface

Objective: expose generic start/status/receipt through existing local_api without Hub changes.

Likely files:

~~~text
src/sentinelx_core/handlers/durable_operations.py
src/sentinelx_core/handlers/local_api.py
src/sentinelx_core/handlers/__init__.py
src/sentinelx_core/operation_registry.py
tests/test_durable_operations_local_api.py
tests/test_local_api.py
~~~

Required verification:

1. endpoint discoverable by local_api list/describe;
2. start rejects unregistered provider/action;
3. target request validates before durable admission;
4. start returns promptly with operation_id;
5. status/receipt are read-only;
6. no path/executable/credential/cancel/list-all controls;
7. configured external local_api cannot be tunneled through start;
8. existing local_api remains compatible.

### S03 — Multi-family consumer adoption

Objective: prove provider-neutral reuse across Direct Codex, one Host Runtime long action and existing background-job compatibility.

Likely files:

~~~text
src/sentinelx_core/handlers/direct_codex.py
src/sentinelx_core/handlers/devforge_runtime.py
src/sentinelx_core/client.py
src/sentinelx_core/jobs.py
src/sentinelx_core/pending_results.py
tests/test_direct_codex_execution.py
tests/test_devforge_runtime_local_api.py
tests/test_jobs.py
tests/test_pending_results.py
~~~

Required verification:

1. Direct Codex has no private async lifecycle;
2. Host Runtime consumer uses the same lifecycle;
3. Direct Codex security/transport semantics unchanged;
4. Host Runtime scope/AppContainer/Job/audit semantics unchanged;
5. lost Direct Codex response is readable later;
6. uncertain publication does remote/provider read-back before replay;
7. duplicate Direct Codex same Attempt returns existing operation;
8. background exec/script compatibility remains passing;
9. pending_results remains delivery-only;
10. production Hub source/schema unchanged.

### S04 — Windows E2E and blocker-closure evidence

Required fixtures:

#### E1 — Long Direct Codex
- start through sentinel_operations;
- execution exceeds normal synchronous local_api window;
- acknowledgement returns promptly;
- status remains readable;
- terminal receipt later reads successfully;
- canonical transport read-back matches provider receipt.

#### E2 — Lost completion response
- operation completes;
- delivery path is lost;
- later status/receipt returns same outcome/digest;
- provider execution count remains one.

#### E3 — Agent restart
- persist nonterminal operation;
- reconstruct/restart runtime;
- reconcile or produce INTERRUPTED/OUTCOME_UNKNOWN;
- prove original material callback is not automatically replayed.

#### E4 — Duplicate start
- same semantic identity/request returns same operation_id;
- callback count remains one.

#### E5 — Authority-changing duplicate
- same semantic identity with changed branch/head/request authority conflicts before callback.

#### E6 — Security regressions
Re-run affected canonical repository firewall, Direct Codex containment/ACL, mutation sandbox/audit, scoped execution profile, local_api schema and Git tests.

#### E7 — PR-013 relation
Do not blindly replay the earlier uncertain PR-013 S03 attempt. PR-020 does not complete PR-013. Any later PR-013 resume must first prove old effects absent or reconcile them safely.

## Self-host implementation entry

Current project binding remains:

~~~yaml
provider: direct
adapter: codex
~~~

This task repairs a failure mode in that path.

At implementation time:

1. revalidate live development_host.direct_codex_v1;
2. use normal direct/codex only if the selected Slice can return a valid implementation receipt;
3. if the missing async boundary prevents safe self-host execution, stop fail-closed;
4. an alternate bootstrap Development Host requires the existing explicit task-scoped DevForge bootstrap command;
5. project binding must not change;
6. no silent provider fallback.

## Verification strategy

Unit:
- lifecycle;
- digest identity;
- duplicate resolution;
- receipt persistence;
- restart scan;
- reconciliation;
- retention;
- schema validation.

Integration:
- local_api start/status/receipt;
- Direct Codex adapter;
- Host Runtime adapter;
- background jobs;
- pending-result replay.

Windows physical:
- real long-running Direct Codex;
- disconnect/reconnect;
- restart recovery;
- remote transport read-back;
- authority closure.

Minimum affected regressions:

~~~text
tests/test_jobs.py
tests/test_local_api.py
tests/test_direct_codex_provider.py
tests/test_direct_codex_execution.py
tests/test_devforge_runtime_local_api.py
tests/test_scoped_script_execution.py
tests/test_user_scoped_git.py
tests/test_canonical_repository_firewall.py
tests/test_canonical_repository_firewall_readiness.py
tests/test_mutation_scope_admission.py
tests/test_windows_mutation_sandbox.py
~~~

## Failure policy

- durable store unavailable before admission → no execution;
- invalid/tampered record → BLOCKED, no replay;
- duplicate identity/request → return existing operation;
- identity conflict → fail closed;
- callback exception with uncertain effects → OUTCOME_UNKNOWN;
- response delivery failure after receipt → receipt stays canonical;
- restart with uncertain effect → reconcile read-only or OUTCOME_UNKNOWN;
- reconciler unavailable → OUTCOME_UNKNOWN;
- receipt persistence failure → never SUCCEEDED;
- provider capability/permission failure → preserve provider failure;
- transport drift → fail closed under owning provider contract.

## Explicit non-authority

Plan approval will not authorize Hub changes, project-binding mutation, provider fallback, arbitrary endpoint forwarding, caller-selected Host paths, credential mutation, force push, merge/release/deployment, generic process cancellation, replay of PR-013 S03, or DevForge workflow changes.

## Plan-review questions

Reviewer must challenge:

1. whether sentinel_operations.start can become generic local_api forwarding;
2. whether duplicate identity is strong enough after lost acknowledgement;
3. whether SUCCEEDED can occur before durable receipt;
4. whether restart can preserve stale RUNNING incorrectly;
5. whether job_completed and durable state can diverge;
6. whether provider adapters retain private async state machines;
7. whether reconciliation can accidentally perform material work;
8. whether background exec/script compatibility is preserved;
9. whether operation_id is confused with DevForge or mutation-audit identities;
10. whether this becomes a second canonical execution runtime instead of a SentinelX async transport/runtime layer.

## Post-plan state

~~~yaml
requirement_ready: true
plan_ready: true
plan_approved: false
implementation_authorized: false
next_stage: plan_review
next_expected_actor: reviewer
canonical_next_action: "#开发评审 PR-020-durable-async-operation-runtime-outcome-readback-v1"
~~~
