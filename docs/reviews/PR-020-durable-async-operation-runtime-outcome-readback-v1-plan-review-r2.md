# PR-020 — SentinelX Durable Async Operation Runtime & Outcome Readback V1 — Plan Review R2

## Review State

~~~yaml
task_id: PR-020-durable-async-operation-runtime-outcome-readback-v1
review_target: plan
requirement_revision: 1
requirement_blob_sha: 60e12a84a5b6bfbc08fbc2bbf73043a8f8629b25
plan_revision: 2
plan_blob_sha: e553a058e3feee880130cc68e5a1698505005402
reviewed_task_head: ea059ea978d89c974c5ae27afa15de56a9d8f46d
result: Rejected
finding_classification: plan_local
runtime:
  devforge_version: "2.95.0"
  devforge_revision: dfea0e30481f9257e540c99cc872e6e6515e2725
  review_contract: "1.3"
  slicing_contract: "1.1"
repository_reality:
  canonical_main: 1028030b33f0ea792a884491a431fffe566f6aa5
  canonical_pr: 20
  canonical_branch: task/durable-async-operation-runtime-outcome-readback-v1
next_gate: plan_review_rejected
next_expected_actor: planner
~~~

## Decision

**Rejected.**

Plan R2 closes all four Plan Review R1 findings:

- atomic same-identity admission is now implementation-shaped and testable;
- one Executor-owned Agent-scoped DurableOperationRuntime is frozen;
- private state placement and crash ordering are frozen;
- the first product Slice no longer self-hosts through the synchronous Direct Codex path and instead requires explicit task-scoped bootstrap admission.

Those corrections are accepted.

One new P0 Plan-local inconsistency remains between the R2 identity-claim model and Requirement R16 bounded retention. It must be resolved before the Plan can be approved and compiled into an Execution Slice Set.

## F1 — Permanent semantic-identity claims conflict with bounded terminal retention

Requirement R16 requires:

~~~text
Terminal operation records have bounded Host-owned retention.
receipt retention preserves verifiability for the declared window.
cleanup targets only provider-owned operation-state storage.
~~~

Plan R2 simultaneously freezes:

~~~text
terminal claim/record remains reserved for the same semantic identity
~~~

and makes the exclusive durable claim the canonical duplicate-suppression primitive:

~~~text
claims/<identity_digest>.json
~~~

The Plan does not define a retention/GC lifecycle for claims, records and receipts as one coherent identity unit.

That creates two invalid implementation outcomes.

### Outcome A — claim is retained forever

If terminal claims are never collected:

- provider-owned operation-state storage grows without bound;
- semantic identities remain permanently reserved even after their declared receipt/status retention window;
- Requirement R16 bounded retention is not satisfied.

### Outcome B — records/receipts expire but claim remains

If records and receipts are collected while the claim remains:

~~~text
claim exists
+ record missing
~~~

R2 currently classifies that shape as:

~~~text
INTERRUPTED / admission_record_not_committed
~~~

But after legitimate GC this is not an interrupted admission. It is an expired terminal operation.

The runtime would therefore confuse valid retention cleanup with crash evidence and could return a false lifecycle state.

### Outcome C — claim is simply deleted with record/receipt

If all evidence is deleted without a provider-defined post-retention rule, a stale same-semantic request may be admitted as a brand-new operation and replay material work.

That can violate R7 no-blind-replay semantics, especially for DevForge Task/Run/Attempt/Slice identities whose owning workflow may still regard the prior attempt as completed.

## Required correction

Plan R3 must freeze one coherent **terminal retention unit** and post-retention duplicate policy.

At minimum it must define:

1. claim, record and receipt retention relationships;
2. the declared terminal retention window source and bounded maximum;
3. which artifacts are removed together and in what order;
4. how GC is distinguished from crash/tamper recovery;
5. whether a compact terminal tombstone is used after receipt eviction;
6. tombstone retention must itself be bounded and Host-owned;
7. a request matching an expired/tombstoned semantic identity must never be silently treated as a fresh replayable operation;
8. provider-owned semantic validity must decide whether a new material operation is legal after retention expiry;
9. for DevForge-bound identity, stale Task/Run/Attempt/Slice identity must fail closed rather than become a new operation;
10. nonterminal, OUTCOME_UNKNOWN, quarantined, or unresolved reconciliation evidence remains ineligible for terminal GC;
11. status/receipt behavior for expired terminal operations is explicit, for example terminal_evidence_expired rather than INTERRUPTED/not-found ambiguity;
12. GC itself never invokes provider execution or external side effects.

A valid direction is:

~~~text
active/nonterminal
→ no GC

terminal receipt window
→ claim + record + receipt retained

receipt window expires
→ receipt may be removed
→ compact bounded terminal tombstone retains
   identity_digest + operation_id + terminal_state
   + request_digest + provider/action
   + terminal/evidence digest + expired_at
→ duplicate start returns terminal_evidence_expired / replay_forbidden

tombstone expiry
→ provider semantic-validity check is mandatory
→ stale DevForge identity = reject
→ only a provider contract that proves a genuinely reusable semantic identity
   may admit a new operation
~~~

The Plan does not need to mandate this exact representation, but it must preserve both R7 and R16 without an unbounded claim registry.

Required tests:

1. terminal record/receipt retention is bounded;
2. nonterminal and OUTCOME_UNKNOWN are not GC eligible;
3. receipt eviction cannot turn a prior terminal operation into claim-only crash recovery;
4. duplicate during tombstone window does not execute;
5. expired DevForge Task/Run/Attempt/Slice identity does not execute;
6. GC failure is fail-safe and does not erase the only no-replay evidence;
7. GC never calls a provider callback;
8. caller cannot select retention or force cleanup.

## R1 Finding Closure

~~~yaml
DurableIdentityAdmissionNotAtomic: closed
DurableRuntimeAgentLifecycleOwnerUndefined: closed
DurableStatePlacementCrashConsistencyUndefined: closed
SelfHostBootstrapDependsOnMissingAsyncBoundary: closed
~~~

### Atomic admission

Pass.

The combination of process-local per-identity serialization plus Windows create-if-absent durable claim closes the concurrent duplicate race, and R2 requires a physical concurrent callback-count proof.

### Agent runtime ownership

Pass.

R2 now defines one Executor-owned DurableOperationRuntime and one store/registry shared by local_api, provider adapters and background compatibility. Startup reconciliation precedes material admission.

### Private state / crash consistency

Pass, subject only to the new retention finding above.

The config-relative internal state root, protected-root guard, claim/ADMITTED/callback/receipt/SUCCEEDED ordering, and receipt/state split repair are implementation-shaped and testable.

### Self-host bootstrap

Pass.

Current DevForge bootstrap contract requires Task stage implementation, Approved Plan, current Slice Set, verified self-host relation, registered/current target, exact transport and unchanged project binding. R2 correctly requires explicit #开发引导执行 before S01 and does not treat Plan prose as provider-switch authority.

The requested target remains subject to live bootstrap admission; Plan Review does not claim that CodeBuddy is currently available.

## Requirement Traceability

~~~yaml
R1_explicit_async_eligibility: pass
R2_prompt_admission_ack: pass
R3_durable_state_before_side_effect: pass
R4_single_canonical_lifecycle: pass
R5_status_readback: pass
R6_durable_receipt_readback: pass
R7_retry_idempotency_duplicate_start: reject_F1_post_retention_semantics
R8_outcome_unknown_reconciliation: pass
R9_connection_lifecycle_independence: pass
R10_agent_restart_semantics: pass
R11_existing_background_job_composition: pass
R12_generic_local_api_surface: pass
R13_provider_neutral_adoption: pass
R14_authority_preservation: pass
R15_cancellation_boundary: pass
R16_retention_cleanup: reject_F1
R17_audit: pass
self_host_implementation_feasibility: pass
~~~

## Feasibility / Risk Review

- **Solution direction:** Pass.
- **Scope control:** Pass.
- **Technical feasibility:** Pass except terminal retention semantics.
- **Atomic duplicate prevention:** Pass.
- **Agent lifecycle ownership:** Pass.
- **Crash/restart consistency:** Pass except GC/claim ambiguity.
- **Security boundary preservation:** Pass.
- **Self-host bootstrap safety:** Pass.
- **Behavioral verification:** Reject only because retention expiry can currently invalidate duplicate/no-replay semantics.
- **UX Contract:** NotApplicable.
- **Visual Fidelity:** NotApplicable.

## Gate Result

~~~yaml
decision: Rejected
blocking_findings:
  - TerminalRetentionIdentityClaimLifecycleUndefined
finding_classification: plan_local
plan_approved: false
implementation_authorized: false
execution_slice_set: not_compiled
next_stage: plan_review_rejected
next_expected_actor: planner
canonical_next_action: "#开发计划修复 PR-020-durable-async-operation-runtime-outcome-readback-v1"
~~~

No SentinelX product code, Host policy, installed Agent, production Hub, project binding, PR-013 state, PR-019 state or canonical main is modified by this review.
