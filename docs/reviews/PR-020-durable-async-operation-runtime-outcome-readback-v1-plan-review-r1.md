# PR-020 — SentinelX Durable Async Operation Runtime & Outcome Readback V1 — Plan Review R1

## Review State

~~~yaml
task_id: PR-020-durable-async-operation-runtime-outcome-readback-v1
review_target: plan
requirement_revision: 1
requirement_blob_sha: 5136e9a7d10517a7ed8b5ba6182d5cf568241cd2
plan_revision: 1
plan_blob_sha: 4d5e7d0883f3fd597755eb40227233b7b0c91cf7
reviewed_task_head: 69a6ea2e6bd1c1f02de89b2d59fab1d1924dbd2d
result: Rejected
finding_classification: plan_local
runtime:
  devforge_version: "2.95.0"
  devforge_revision: 162337cc2fffa710d49a9cd38ab4cc8643f09ffb
  review_contract: "1.3"
repository_reality:
  canonical_main: 1028030b33f0ea792a884491a431fffe566f6aa5
  canonical_pr: 20
  canonical_branch: task/durable-async-operation-runtime-outcome-readback-v1
next_gate: plan_review_rejected
next_expected_actor: planner
~~~

## Decision

**Rejected.**

Requirement Revision 1 is Ready and the provider-neutral Durable Async Operation Runtime direction is accepted.

Plan Revision 1 has four P0 implementation-shaping gaps. None requires a Requirement rewrite; all are plan-local. The defects are concentrated in exactly the boundaries the task exists to guarantee: duplicate suppression, Agent lifecycle ownership, durable-state truth, and safe self-host implementation.

## F1 — Duplicate suppression is not atomic, so two concurrent starts can execute twice

Requirement R7 requires:

~~~text
same semantic identity + same request digest
→ return the existing operation
→ do not replay work
~~~

Plan D3 defines the lookup rule, but Plan D4 only describes per-operation record/receipt files and atomic write-then-rename. It does not define an atomic identity claim keyed by identity_digest.

That leaves this race:

~~~text
start A                         start B
  │                               │
lookup identity → none          lookup identity → none
  │                               │
create operation A             create operation B
  │                               │
invoke callback                invoke callback
~~~

A single Agent process can receive multiple requests concurrently, so this does not require a multi-process edge case. The current Hub client and Executor are asyncio based and may have concurrent request tasks.

If both callbacks reach repository/service/filesystem side effects, the runtime has already violated the core no-blind-replay guarantee before status/receipt logic can help.

### Required correction

Plan R2 must freeze a deterministic, atomic semantic-identity admission protocol.

At minimum:

1. one unique claim exists per provider/action/identity_digest;
2. claim creation/compare is atomic under concurrent asyncio starts;
3. a second same-request start returns the already claimed operation_id;
4. a second different-request start fails with identity conflict before provider callback invocation;
5. the identity claim is durable enough to survive process restart;
6. crash between identity claim and operation-record persistence has a deterministic recovery rule;
7. stale/orphan claims do not cause replay;
8. no caller can select or overwrite the claim key.

Acceptable implementation directions include a provider-private identity-index file created with exclusive semantics plus a process-local per-digest lock, or an equivalent single-writer durable CAS mechanism. The exact mechanism must work on Windows.

Required concurrency tests must launch multiple identical starts simultaneously and prove provider callback count is exactly one.

## F2 — DurableOperationRuntime has no frozen Agent lifecycle owner

Current repository reality matters here:

- HubClient owns exactly one Executor instance;
- Executor lazily builds exactly one handler registry;
- builtin local_api providers are created inside build_registry;
- existing background tasks are owned by HubClient._background_tasks;
- pending-result replay is initiated by HubClient on connection establishment.

Plan R1 says the new runtime will own async tasks and perform startup reconciliation, but it does not freeze which existing object owns the one canonical DurableOperationRuntime instance or when restart recovery executes.

Without that decision, implementation can accidentally produce:

- one runtime per builtin provider;
- one runtime per handler build;
- a module-global singleton detached from Executor/config lifetime;
- a local_api runtime that is different from the one used by background exec/script compatibility;
- startup reconciliation that runs only after the first sentinel_operations call;
- multiple reconciliation passes racing with new starts.

Any of those outcomes would create more than one operation truth or permit a new start before stale RUNNING state is reconciled.

### Required correction

Plan R2 must freeze one Agent-scoped lifecycle.

The Plan must state the equivalent of:

~~~text
HubClient
  └─ one Executor
       └─ one DurableOperationRuntime
            ├─ one DurableOperationStore
            ├─ one DescriptorRegistry
            ├─ sentinel_operations builtin
            ├─ Direct/Host Runtime adapters
            └─ optional background-job compatibility bridge
~~~

It must also define:

1. construction order;
2. injection into builtin providers/handlers;
3. how HubClient background compatibility reaches the same runtime instance;
4. when startup reconciliation is run;
5. whether new material starts are blocked until reconciliation completes;
6. shutdown behavior without creating generic cancellation authority;
7. that module-global mutable singleton state is forbidden.

Required tests must prove local_api and background compatibility share the same runtime/store and that recovery executes once before post-restart material admission.

## F3 — Durable-state placement and crash consistency are still abstract

Requirement R3 requires durable state before material side effects, and R6 requires the terminal receipt to be durable before SUCCEEDED.

Plan R1 currently gives only a logical path:

~~~text
<agent-state>/durable-operations/
  records/
  receipts/
~~~

and says writes use atomic write-then-rename.

That is not enough to prove the security/durability boundary on the current Windows Host.

The Plan does not freeze:

- what current Agent-owned root is authoritative;
- whether that root can overlap user-facing upload/file-ops writable paths;
- what ACL/ownership expectation protects operation truth;
- the exact ordering between identity claim, ADMITTED record, receipt and terminal-state update;
- recovery from receipt-written / state-not-updated crash;
- recovery from identity-claim-written / record-not-written crash;
- behavior on disk-full/replace failure;
- how corrupted or partially migrated records are quarantined without deleting OUTCOME_UNKNOWN evidence.

### Required correction

Plan R2 must define an Agent-private state placement and persistence protocol.

It must guarantee:

1. the root is Host/Agent-owned and not caller-selected;
2. the root is outside user-facing upload content and is not made writable through generic file_ops merely to support this feature;
3. identity claim and ADMITTED durability precede provider callback start;
4. terminal receipt persists before state may become SUCCEEDED;
5. startup can repair a receipt/state split without replay;
6. persistence failure before callback means no callback;
7. persistence failure after a possibly material callback becomes OUTCOME_UNKNOWN unless absence is independently proven;
8. malformed records fail closed and are retained/quarantined according to bounded policy rather than silently normalized to success.

The implementation may reuse an existing SentinelX internal state root if one is already canonical; it must not invent a parallel user-writable state authority.

## F4 — Self-host implementation can reproduce the exact unknown-outcome defect before PR-020 exists

Plan R1 currently says:

~~~text
1. revalidate development_host.direct_codex_v1
2. use normal direct/codex if the selected Slice can return a valid receipt
3. if the missing async boundary prevents safe self-host execution, stop fail-closed
~~~

The problem is step 2 cannot safely be determined in advance.

The concrete trigger for this task is precisely:

~~~text
direct/codex mutation started
→ operation outlived synchronous local_api window
→ caller got timeout
→ no durable handle/receipt
→ outcome became unknown
~~~

Using the same synchronous mutating path for S01 and waiting to see whether it finishes in time can reproduce the same ambiguous side-effect state. A successful short dry run cannot prove a real implementation slice will stay inside the transport deadline.

This is a circular bootstrap assumption and it materially affects whether implementation can start safely.

### Required correction

Plan R2 must define a pre-mutation bootstrap admission rule.

Before S01 product mutation, one of these must be true:

1. a currently verified execution path already provides durable/background result identity sufficient for this Task's implementation receipt; or
2. an explicit existing DevForge task-scoped bootstrap execution target is selected through #开发引导执行 and verified before mutation; or
3. implementation is blocked before any material provider invocation.

The Plan must explicitly forbid:

- invoking current synchronous direct/codex implementation merely to test whether it happens to finish under the timeout;
- silently falling back to another provider;
- changing the project binding;
- replaying an outcome-unknown implementation attempt.

If an alternate bootstrap target is required, its availability must be resolved before the first implementation Slice starts, not after a timeout.

## Accepted Plan R1 direction

The following direction is accepted and should be preserved in Plan R2:

- one provider-neutral Durable Async Operation Runtime;
- operation_id is SentinelX correlation identity, not a replacement for DevForge Run/Attempt/Slice;
- explicit async eligibility registry;
- no arbitrary local_api forwarding;
- generic sentinel_operations start/status/receipt surface;
- SUCCEEDED requires durable receipt;
- OUTCOME_UNKNOWN is a real state and does not imply retry;
- read-back-first reconciliation;
- no generic cancel/kill authority;
- no production Hub schema/source changes;
- no permission, credential, workspace or transport broadening;
- Direct Codex is a consumer, not the runtime definition;
- at least one Host Runtime consumer must use the same lifecycle;
- existing background jobs and pending_results remain compatible;
- pending_results remains delivery replay rather than canonical operation truth;
- PR-019 retains Stable Baseline exit authority;
- PR-013 must not be blindly replayed.

## Requirement Traceability

~~~yaml
R1_explicit_async_eligibility: pass
R2_prompt_admission_ack: pass
R3_durable_state_before_side_effect: reject_F1_F3
R4_single_canonical_lifecycle: pass_with_F2_owner_correction
R5_status_readback: pass
R6_durable_receipt_readback: pass_with_F3_crash_consistency_correction
R7_retry_idempotency_duplicate_start: reject_F1
R8_outcome_unknown_reconciliation: pass
R9_connection_lifecycle_independence: pass_with_F2_owner_correction
R10_agent_restart_semantics: reject_F2_F3
R11_existing_background_job_composition: pass_with_F2_single_runtime_correction
R12_generic_local_api_surface: pass
R13_provider_neutral_adoption: pass
R14_authority_preservation: pass
R15_cancellation_boundary: pass
R16_retention_cleanup: pass_with_F3_state_root_correction
R17_audit: pass
self_host_implementation_feasibility: reject_F4
~~~

## Feasibility / Risk Review

- **Solution direction:** Pass.
- **Scope control:** Pass.
- **Technical feasibility:** Rejected until F1/F2/F3 are frozen.
- **Risk handling:** Rejected because concurrent duplicate execution and crash/restart ordering remain under-specified.
- **Requirement traceability:** Rejected for R3/R7/R10 until the above corrections are made.
- **Behavioral verification:** Mostly sound, but must add atomic-concurrency and single-runtime-startup tests.
- **Security boundary preservation:** Direction passes; F3 must freeze the private state root so generic file authority is not accidentally expanded.
- **Self-host execution safety:** Rejected until F4 removes the circular timeout gamble.
- **UX Contract:** NotApplicable.
- **Visual Fidelity:** NotApplicable.

## Gate Result

~~~yaml
decision: Rejected
blocking_findings:
  - DurableIdentityAdmissionNotAtomic
  - DurableRuntimeAgentLifecycleOwnerUndefined
  - DurableStatePlacementCrashConsistencyUndefined
  - SelfHostBootstrapDependsOnMissingAsyncBoundary
finding_classification: plan_local
plan_approved: false
implementation_authorized: false
execution_slice_set: not_compiled
next_stage: plan_review_rejected
next_expected_actor: planner
canonical_next_action: "#开发计划修复 PR-020-durable-async-operation-runtime-outcome-readback-v1"
~~~

No SentinelX product code, Host policy, installed Agent, production Hub, project binding, PR-013 execution state, PR-019 state or canonical main is modified by this review.
