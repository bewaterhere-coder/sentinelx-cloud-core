# PR-020 SentinelX Durable Async Operation Runtime & Outcome Readback V1 — Plan R2

## Status

~~~yaml
task_id: PR-020-durable-async-operation-runtime-outcome-readback-v1
plan_revision: 2
plan_status: ready_for_review
implementation_authority: false
requirement_ref: docs/requirements/PR-020-durable-async-operation-runtime-outcome-readback-v1.md
requirement_revision: 1
prior_plan_revision: 1
rejected_review_ref: docs/reviews/PR-020-durable-async-operation-runtime-outcome-readback-v1-plan-review-r1.md
transport:
  type: github-pr
  pr_number: 20
  branch: task/durable-async-operation-runtime-outcome-readback-v1
  base: main
repository_baseline:
  main_sha: 1028030b33f0ea792a884491a431fffe566f6aa5
runtime:
  devforge_version: 2.95.0
  devforge_revision: a693dde368c5c3b43ea577581190cac16c5b81ff
~~~

## R2 Remediation Delta

Plan R2 preserves Requirement Revision 1 and repairs only the four Plan Review R1 findings.

### F1 resolved — atomic semantic-identity admission is frozen

R2 adds a two-level admission guard:

~~~text
process-local per-identity asyncio lock
        +
durable identity claim created with create-if-absent semantics
~~~

The durable claim key is derived only from provider, action and provider-sealed semantic identity.

Recommended shape:

~~~text
identity_digest = SHA256(provider + action + canonical semantic identity)
operation_id = "op_" + SHA256("sentinelx-durable-operation-v1" + identity_digest)
claim path = claims/<identity_digest>.json
~~~

The operation_id is deterministic for one semantic identity and is not caller-selected.

Admission order:

~~~text
validate provider request
→ resolve provider-owned semantic identity
→ compute identity_digest + request_digest
→ acquire in-process per-identity lock
→ exclusively create durable identity claim
→ fsync/close claim
→ persist ADMITTED operation record atomically
→ only then schedule provider callback
~~~

For an existing claim:

~~~text
same identity + same request digest
→ return existing operation_id and current state

same identity + different request digest
→ OperationIdentityConflict
→ no callback
~~~

The identity claim is created with an exclusive create primitive that maps to Windows create-if-absent semantics, such as os.open with O_CREAT | O_EXCL. Atomic replace alone is not the uniqueness primitive.

Crash handling:

- claim exists and ADMITTED record exists: recover from record;
- claim exists but record is absent: callback could not have legally started; startup materializes a fail-closed INTERRUPTED admission record with reason admission_record_not_committed and does not replay;
- record exists without matching valid claim: treat as malformed/tampered state and BLOCKED;
- terminal claim/record remains reserved for the same semantic identity;
- retry requiring new material execution must use a new owning upstream semantic attempt, not delete/reuse the old claim.

Required concurrency proof launches multiple simultaneous same-identity starts and proves exactly one provider callback.

### F2 resolved — one Agent-scoped DurableOperationRuntime owner

R2 freezes the object lifetime:

~~~text
HubClient
  └─ one Executor
       └─ one DurableOperationRuntime
            ├─ one DurableOperationStore
            ├─ one DurableOperationRegistry
            ├─ one active-task registry
            ├─ sentinel_operations builtin adapter
            ├─ Direct Development Host adapters
            ├─ Host Runtime adapters
            └─ optional legacy background compatibility bridge
~~~

Rules:

1. Executor constructs exactly one DurableOperationRuntime for its config/runtime lifetime.
2. build_registry receives/injects that runtime; builtin providers never construct their own runtime.
3. HubClient background compatibility obtains the exact same runtime through Executor.
4. mutable module-global DurableOperationRuntime state is forbidden.
5. HubClient.run invokes Executor.start before entering the connection/read loop.
6. Executor.start runs exactly one startup reconciliation pass.
7. new material sentinel_operations.start calls are rejected with runtime_recovery_in_progress until recovery is complete.
8. status/receipt reads may remain available during recovery when their records can be safely read.
9. WebSocket reconnect does not reconstruct the runtime; the runtime belongs to the Agent process, not a connection epoch.
10. graceful Agent shutdown stops new admission; it does not expose a new caller cancellation capability. Active tasks may finish within the process shutdown window; if process termination interrupts them, next startup reconciles their durable nonterminal records.

This gives local_api, Direct Host, Host Runtime and any migrated background jobs one canonical operation truth.

### F3 resolved — Agent-private state root and crash protocol are explicit

For V1 Windows, the durable state root is provider-owned and derived from the actual SentinelX config location:

~~~text
agent_state_root = config_path.parent / "state"
durable_root = agent_state_root / "durable-operations"
~~~

Examples:

~~~text
system/service install:
C:\ProgramData\SentinelX\state\durable-operations

per-user/task install:
%LOCALAPPDATA%\SentinelX\state\durable-operations
~~~

The caller cannot supply or override this path.

The runtime must not fall back to upload_base.

The durable root is internal Agent state:

- outside user-facing upload content;
- never added to file_ops simply to make this feature work;
- generic file read/write/move/copy/delete/edit handlers must treat the durable root as an internal protected root even when an operator configured a broader ancestor path;
- no local_api response returns the physical state-root path.

Recommended layout:

~~~text
durable-operations/
  claims/<identity_digest>.json
  records/<operation_id>.json
  receipts/<operation_id>.json
  quarantine/
~~~

Persistence protocol:

~~~text
A. exclusive durable claim
B. durable ADMITTED record
C. provider callback may start
D. RUNNING / VERIFYING state updates
E. durable terminal receipt
F. durable SUCCEEDED state update
~~~

Durability uses same-volume temp file, flush/fsync of file content, close, then os.replace for mutable records/receipts. The exclusive claim is written directly through create-if-absent, flushed and closed before ADMITTED record creation.

Crash consistency rules:

- failure during claim creation: no operation admitted;
- claim committed but ADMITTED not committed: no callback; startup records INTERRUPTED/admission_record_not_committed;
- ADMITTED committed but callback not known started: recover using provider evidence; never replay automatically;
- callback may have produced material effect and any later persistence step fails: OUTCOME_UNKNOWN unless provider read-back proves a terminal outcome;
- receipt committed but SUCCEEDED state update missing: startup verifies receipt binding/digest and repairs record to SUCCEEDED without executing provider callback;
- SUCCEEDED without valid receipt is invalid and fails closed;
- malformed/tampered record or digest mismatch is moved/logically projected to quarantine/blocked evidence without silently deleting the original evidence;
- OUTCOME_UNKNOWN evidence is not retention-GC eligible while unresolved.

R2 does not claim survival beyond the operating system/filesystem durability guarantees after successful flush; acceptance tests cover Agent/process/service restart and injected write/replace failures, not catastrophic media loss.

### F4 resolved — bootstrap is decided before S01 mutation

The current canonical project binding remains:

~~~yaml
provider: direct
adapter: codex
source: explicit_project_binding
~~~

PR-020 exists because the current SentinelX synchronous Direct Codex local_api path can begin mutation and then lose its result at the request timeout. Therefore R2 explicitly forbids using that same path for the first product-changing Slice merely to see whether it finishes quickly.

After Plan R2 is approved and the Execution Slice Set is compiled, S01 has this mandatory precondition:

~~~text
explicit #开发引导执行
PR-020-durable-async-operation-runtime-outcome-readback-v1
direct:codebuddy
~~~

Rationale:

- CodeBuddy is a registered DevForge Development Host adapter;
- it is outside the SentinelX Direct Codex local_api path being repaired;
- the existing task-scoped bootstrap contract verifies the self-host relation, exact Approved Plan, exact Slice Set, canonical transport, target registration/current availability and unchanged project binding before any implementation mutation;
- the override expires under the existing DevForge rules and never rewrites the project binding.

If direct:codebuddy is unavailable or not currently verifiable when the bootstrap command is invoked:

~~~text
→ BootstrapTargetUnavailable / BootstrapTargetUnregistered
→ stop before S01 mutation
~~~

There is no fallback to current direct/codex, Harness, Host Runtime or another provider.

After S01/S02 establish the generic durable operation surface and a live exact-candidate activation proves that the Direct Codex action can return a durable operation_id/status/receipt, later Slices may return to canonical direct/codex only through normal DevForge execution resolution and fresh admission. The bootstrap override itself does not silently switch back or execute a successor Slice.

No synchronous Direct Codex material invocation is allowed as a preflight for S01.

## Objective

Implement one provider-neutral durable operation runtime over the existing SentinelX Agent execution substrate so long-running operations can return a stable handle immediately, persist lifecycle/outcome evidence, survive transport disconnects as readable state, reconcile uncertain external outcomes without replay, and expose bounded status/receipt read-back through the existing local_api transport.

The design reuses current mechanisms:

~~~text
Hub background job / job_id
           │
           │ transport correlation only
           ▼
SentinelX Durable Operation Runtime
  ├─ atomic semantic-identity admission
  ├─ durable operation/receipt store
  ├─ provider/action eligibility registry
  ├─ Agent-scoped async task ownership
  ├─ startup reconciliation
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

Provider-specific execution authority remains inside each provider. The generic runtime owns async lifecycle, persistence, duplicate suppression and read-back only.

## Current repository reality

Current main already contains useful primitives:

- src/sentinelx_core/jobs.py: background timeout, job_completed event construction and mutation identity validation;
- src/sentinelx_core/pending_results.py: completed-result staging and reconnect replay, explicitly not a job registry;
- src/sentinelx_core/client.py: concurrent request handling, background task ownership and job_completed delivery;
- src/sentinelx_core/executor.py: one Executor per HubClient with one lazily built handler registry;
- src/sentinelx_core/handlers/local_api.py: synchronous builtin local_api invocation;
- src/sentinelx_core/handlers/direct_codex.py: long-running Direct Codex builtin path;
- src/sentinelx_core/handlers/devforge_runtime.py: Host Runtime builtin path;
- DevForge Execution Run Runtime: upstream Task/Run/Attempt/Slice authority.

The current request loop explicitly dispatches incoming requests in background tasks, so concurrent same-identity start admission is a real local race unless the runtime serializes identity claims.

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

- descriptor and semantic identity model;
- deterministic operation identity;
- atomic identity-claim admission;
- durable operation/receipt store;
- lifecycle transition validation;
- duplicate resolution;
- Agent-scoped active task registry;
- startup reconciliation;
- bounded retention;
- sanitized read models.

Suggested abstractions:

~~~text
DurableOperationDescriptor
DurableOperationIdentity
DurableOperationClaim
DurableOperationRecord
DurableOperationReceipt
DurableOperationStore
DurableOperationRegistry
DurableOperationRuntime
~~~

No Codex-, CodeBuddy-, Unity-, game- or repository-specific lifecycle logic belongs in the core.

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

### D3 — Atomic deterministic semantic identity

Provider validation happens before admission and produces canonical request + sealed semantic identity.

The runtime computes identity_digest, request_digest and deterministic operation_id.

Within one Agent process a per-identity asyncio lock serializes admission. Across crashes/restarts the durable exclusive claim is canonical.

A claim contains only bounded metadata:

~~~yaml
operation_id:
provider:
action:
identity_digest:
request_digest:
created_at:
schema_version:
~~~

The claim does not carry executable, credentials, workspace path or arbitrary request body.

Same identity + same request returns the existing operation. Same identity + changed request conflicts before any callback.

### D4 — Agent-private durable store

The single DurableOperationStore root is derived from config_path.parent/state/durable-operations.

This root is not upload_base and is not caller-selectable.

Implementation must add a provider-owned internal protected-root guard so generic file APIs cannot mutate/read the operation truth merely because a broader file_ops ancestor is allowed.

Store writes use:

- exclusive create + flush for claims;
- temp + flush + same-volume atomic replace for mutable records/receipts;
- deterministic digest validation on read.

No durable admission means no provider callback.

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

A claim-without-record recovery may materialize INTERRUPTED without invoking the provider.

Terminal states do not return to RUNNING under the same semantic identity.

### D6 — Agent lifecycle and async task ownership

Executor owns exactly one DurableOperationRuntime instance and exposes it to HubClient and handler construction.

Construction sequence:

~~~text
HubClient.__init__
→ Executor(config_path)
→ resolve private durable state root
→ construct DurableOperationStore
→ construct DurableOperationRegistry
→ construct DurableOperationRuntime
→ build/inject handlers lazily using the same runtime
~~~

Startup sequence:

~~~text
HubClient.run
→ await Executor.start()
→ DurableOperationRuntime.reconcile_startup_once()
→ mark runtime admission-ready
→ connect/serve requests
~~~

No material start before startup recovery is complete.

The runtime owns only its internal async provider tasks. Disconnect does not cancel them. Agent shutdown stops new admission but adds no generic kill/cancel caller API.

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
  request: <target request>

status:
  operation_id: <opaque id>

receipt:
  operation_id: <opaque id>
~~~

Security:

- target must be registered;
- configured external local_api endpoints cannot be tunneled;
- owning provider validates before admission;
- status/receipt are read-only;
- no list-all;
- no generic cancel;
- no caller path/executable/credential/provider-policy override.

### D8 — Provider adapter boundary

Providers expose existing execution logic plus descriptor metadata. Generic runtime calls the same internal implementation callback.

Backward-compatible synchronous provider surfaces may remain while callers migrate, but cannot be used as alternate operation truth.

### D9 — Direct Codex adoption

Direct Codex is the first real long-running builtin consumer after bootstrap implementation establishes the generic runtime.

Refactor only enough to expose equivalents of:

~~~text
validate_execute_task
resolve_execute_task_identity
execute_task_internal
sanitize_execute_task_receipt
reconcile_execute_task_outcome
~~~

Existing Direct Codex transport/security semantics remain authoritative.

For uncertain publication, reconciler first reads exact provider persistence evidence and canonical remote head. It never re-runs Codex or pushes again to discover outcome.

### D10 — Host Runtime adoption

At least one current long Host Runtime builtin action adopts the same DurableOperationRuntime, preferably devforge_runtime execute_scoped where its existing contract permits.

Existing mutation scope, AppContainer, Job, audit and scoped_mutation semantics remain authoritative.

### D11 — Existing background exec/script compatibility

Current Hub background contract remains externally compatible:

~~~text
background=true + job_id
→ immediate running ack
→ job_completed event
→ notifications
~~~

When migrated:

- Hub job_id is transport correlation only;
- it binds to the same durable operation record;
- terminal job_completed derives from persisted terminal outcome;
- pending_results replays delivery only;
- local_api and background compatibility use the same Executor-owned runtime/store.

If an exec/script migration edge is unsafe in V1, legacy behavior may remain, but regression tests must prove no behavior loss and no competing runtime is introduced.

### D12 — pending_results remains delivery replay

pending_results continues to own only failed WebSocket delivery replay.

A terminal durable receipt is canonical and exists before its delivery event copy.

### D13 — Restart reconciliation

Startup recovery scans claims, records and receipts before material admission.

Resolution order:

~~~text
claim exists + record absent
→ INTERRUPTED admission_record_not_committed
→ no provider replay

valid terminal receipt + nonterminal/stale record
→ verify binding/digest
→ repair terminal state without callback

nonterminal record + provider reconciler
→ read-back-first reconciliation

external outcome proven
→ persist terminal state/receipt

absence safely proven
→ INTERRUPTED or FAILED per provider contract

outcome not provable
→ OUTCOME_UNKNOWN
~~~

No startup path invokes the original material callback.

### D14 — Exactly-once claim boundary

V1 does not claim universal exactly-once execution.

It guarantees:

- one atomic claim per semantic identity;
- no provider callback before durable admission;
- duplicate same request reuses claim;
- different request conflicts;
- no blind same-identity replay;
- terminal receipt before success;
- read-back-first reconciliation.

### D15 — Audit

Audit transition metadata only:

- operation_id;
- provider/action;
- identity/request digests;
- from/to state;
- reason;
- upstream refs;
- evidence digest;
- external-effect verified flag.

No raw credential/full environment/hidden reasoning.

### D16 — Stable Baseline relation

PR-020 repairs the concrete long-operation receipt/read-back blocker exposed during PR-019 stabilization.

PR-019 remains the only owner of Stable Baseline exit.

## Implementation slices

Formal Slice Set is compiled only after Plan R2 approval.

### S01 — Core durable operation runtime and protected state

Objective: implement the Agent-private store, atomic identity claim, lifecycle, one Executor-owned runtime, startup reconciliation and protected-root boundary without production provider adoption.

Likely files:

~~~text
src/sentinelx_core/durable_operations.py
src/sentinelx_core/executor.py
src/sentinelx_core/client.py
src/sentinelx_core/handlers/__init__.py
src/sentinelx_core/handlers/fileops.py
src/sentinelx_core/handlers/edit.py
src/sentinelx_core/handlers/fsmutate.py
tests/test_durable_operations.py
tests/test_durable_operation_lifecycle.py
~~~

Required verification:

1. concurrent identical starts call provider callback exactly once;
2. concurrent identity conflict invokes zero second callback;
3. exclusive claim works on Windows;
4. claim exists before ADMITTED record and both before callback;
5. claim-only crash recovers INTERRUPTED without replay;
6. receipt-before-SUCCEEDED ordering is enforced;
7. receipt/state split repairs without replay;
8. tampered record fails closed;
9. protected state root is inaccessible through generic file APIs even under a broader allowed ancestor;
10. upload_base is never used as operation truth;
11. one Executor owns exactly one runtime/store;
12. startup reconciliation runs once before material admission;
13. no module-global mutable runtime singleton.

### S02 — sentinel_operations local_api surface

Objective: expose bounded start/status/receipt through existing local_api and validate prompt admission.

Likely files:

~~~text
src/sentinelx_core/handlers/durable_operations.py
src/sentinelx_core/handlers/local_api.py
src/sentinelx_core/handlers/__init__.py
tests/test_durable_operations_local_api.py
tests/test_local_api.py
~~~

Required verification:

1. endpoint discoverable;
2. unregistered targets rejected;
3. request validates before claim;
4. start returns operation_id promptly;
5. same request returns same operation_id;
6. conflicting request fails before callback;
7. status/receipt are read-only;
8. external configured local_api cannot be tunneled;
9. no path/executable/credential/cancel/list-all controls.

### S03 — Multi-family consumer adoption

Objective: adapt Direct Codex and one Host Runtime consumer to the same runtime, then compose background delivery compatibility.

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
2. Host Runtime uses the same core runtime;
3. existing provider security semantics unchanged;
4. uncertain Git publication performs read-back before any replay;
5. duplicate same DevForge Attempt returns same operation;
6. changed expected head/request conflicts;
7. local_api and background bridge share same runtime/store;
8. job_completed derives from persisted outcome where migrated;
9. pending_results remains delivery-only;
10. Hub source/schema unchanged.

### S04 — Windows E2E and blocker-closure evidence

Required fixtures:

#### E1 — long Direct Codex
- start through sentinel_operations;
- acknowledgement returns before long work completes;
- status remains readable;
- terminal receipt later reads successfully;
- canonical transport read-back matches provider receipt.

#### E2 — lost completion response
- operation completes;
- delivery path is lost;
- later read returns same operation and receipt digest;
- execution count remains one.

#### E3 — Agent restart
- persist nonterminal operation;
- restart runtime;
- recover before new material admission;
- reconcile or OUTCOME_UNKNOWN/INTERRUPTED;
- no replay.

#### E4 — concurrent duplicate
- launch simultaneous identical starts;
- one claim;
- one operation_id;
- callback count exactly one.

#### E5 — authority-changing duplicate
- same semantic identity with changed request/head;
- conflict before callback.

#### E6 — protected state root
- configure a broader file_ops ancestor;
- prove durable state path remains inaccessible to generic file mutation/read APIs.

#### E7 — security regressions
Re-run canonical repository firewall, Direct Codex containment/ACL, mutation sandbox/audit, scoped execution profile, local_api schema and Git regression suites.

#### E8 — PR-013 relation
Do not blindly replay the earlier uncertain PR-013 S03 attempt. PR-020 does not complete PR-013.

## Implementation bootstrap entry

S01 product mutation requires an admitted task-scoped bootstrap override.

Required sequence after Plan R2 approval:

~~~text
Plan R2 Approved
→ Execution Slice Set compiled/read back
→ explicit #开发引导执行 PR-020... direct:codebuddy
→ DevForge verifies registered/current CodeBuddy target + exact self-host relation
→ bootstrap receipt read back
→ explicit #开发执行 PR-020...
→ at most S01
~~~

Failure to admit direct:codebuddy blocks before product mutation.

The bootstrap target:

- uses the same PR #20 and branch;
- does not create replacement transport;
- does not change project binding;
- has no Requirement/Plan/Gate/Acceptance/release authority;
- expires under the canonical bootstrap contract.

Canonical direct/codex is not used for S01 material execution.

Return to canonical direct/codex is allowed only after the generic async path is implemented, activated and live-read-back verified as capable of durable operation start/status/receipt. That return is resolved by normal DevForge execution admission, not by fallback.

## Verification strategy

Unit:
- atomic claims;
- concurrency;
- lifecycle;
- digest identity;
- receipt ordering;
- crash splits;
- restart reconciliation;
- retention;
- schema/tamper validation.

Integration:
- single Executor-owned runtime;
- local_api start/status/receipt;
- Direct Codex adapter;
- Host Runtime adapter;
- background jobs;
- pending-result replay;
- internal protected-root guard.

Windows physical:
- O_EXCL claim race;
- long-running Direct Codex;
- disconnect/reconnect;
- service restart;
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
tests/test_fileops.py
tests/test_fsmutate.py
~~~

## Failure policy

- bootstrap target unavailable before S01 → no product mutation;
- claim create failure → no operation admitted;
- claim/request conflict → no callback;
- claim-only crash → INTERRUPTED, no replay;
- ADMITTED persistence failure → no callback;
- runtime recovery incomplete → material start blocked;
- invalid/tampered record → BLOCKED/quarantined evidence, no replay;
- callback exception with uncertain effects → OUTCOME_UNKNOWN;
- response delivery failure after receipt → receipt remains canonical;
- receipt persistence failure after possible material effect → OUTCOME_UNKNOWN, never SUCCEEDED;
- reconciler unavailable → OUTCOME_UNKNOWN;
- provider capability/permission failure → preserve provider failure;
- transport drift → fail closed;
- state-root overlap with generic user-writable surface → implementation test failure / no acceptance.

## Explicit non-authority

Plan approval will not authorize:

- production Hub changes;
- project-binding mutation;
- silent provider fallback;
- arbitrary local_api forwarding;
- caller-selected Host state paths;
- credential mutation;
- force push;
- merge/release/deployment;
- generic process cancellation;
- replay of PR-013 S03;
- DevForge workflow changes;
- direct/codex S01 execution without durable async capability;
- automatic invocation of #开发引导执行.

## Plan-review questions for R2

Reviewer should verify:

1. atomic identity claim closes the concurrent duplicate race on Windows;
2. claim-only and receipt/state crash splits have deterministic no-replay recovery;
3. Executor is the sole owner of one runtime/store;
4. startup reconciliation completes before new material admission;
5. protected state root cannot be mutated through generic file APIs;
6. local_api and background compatibility cannot maintain divergent operation truth;
7. Direct Codex and Host Runtime remain consumers, not runtime definitions;
8. reconciliation never invokes the material callback;
9. direct:codebuddy bootstrap is admitted before S01 mutation and leaves project binding unchanged;
10. canonical direct/codex is not used as a timeout gamble before the feature exists.

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
