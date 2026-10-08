# PR-020 — SentinelX Durable Async Operation Runtime & Outcome Readback V1 — Plan Review R4

## Review State

~~~yaml
task_id: PR-020-durable-async-operation-runtime-outcome-readback-v1
review_target: plan
requirement_revision: 1
requirement_blob_sha: f0374d11ff0bd5213e9486b4a1ec59fc090deb55
plan_revision: 4
plan_blob_sha: 304cbf2ab58b4fa3835c35b343bd1214565c2920
reviewed_task_head: aa5ba8a23e6673d165ce6c803725caa32a9daea3
result: Approved
runtime:
  devforge_version: "2.95.0"
  devforge_revision: c44591899fb7c3312ca7a30cc816ca878e12b462
  review_contract: "1.3"
  slicing_contract: "1.1"
repository_reality:
  canonical_main: 1028030b33f0ea792a884491a431fffe566f6aa5
  canonical_pr: 20
  canonical_branch: task/durable-async-operation-runtime-outcome-readback-v1
next_gate: implementation
next_expected_actor: implementer
~~~

## Decision

**Approved.**

Plan R4 closes the final stale-plan execution binding without changing Requirement Revision 1 or any previously accepted technical decision.

The Plan is implementation-shaped, bounded, and verifiable:

- atomic semantic-identity admission is durable before material callbacks;
- one Executor-owned DurableOperationRuntime is the Agent operation truth;
- startup reconciliation precedes new material admission;
- Agent-private state placement and crash ordering are explicit;
- terminal evidence retention is bounded and tombstone-first;
- post-retention material admission requires provider-owned semantic freshness;
- local_api exposes only registered start/status/receipt operations;
- Direct Codex and Host Runtime remain consumers of the generic runtime;
- existing background/pending-results behavior remains compatible but non-canonical;
- no generic cancel, arbitrary forwarding, credential expansion, Host-policy widening, or Hub schema change is authorized;
- first implementation mutation is protected by task-scoped bootstrap rather than the synchronous Direct Codex path being repaired.

## Finding Closure

~~~yaml
DurableIdentityAdmissionNotAtomic: closed
DurableRuntimeAgentLifecycleOwnerUndefined: closed
DurableStatePlacementCrashConsistencyUndefined: closed
SelfHostBootstrapDependsOnMissingAsyncBoundary: closed
TerminalRetentionIdentityClaimLifecycleUndefined: closed
ExecutionEntryStalePlanRevisionBinding: closed
~~~

## Review Checks

~~~yaml
solution_direction: pass
scope_control: pass
technical_feasibility: pass
risk_handling: pass
requirement_traceability_R1_R17: pass
acceptance_traceability_AC1_AC24: pass
atomic_duplicate_admission: pass
agent_runtime_ownership: pass
startup_reconciliation_before_material_admission: pass
private_state_and_protected_root: pass
crash_consistency: pass
bounded_retention_and_tombstones: pass
post_retention_semantic_freshness: pass
status_and_receipt_readback: pass
restart_no_replay: pass
direct_codex_consumer_boundary: pass
host_runtime_consumer_boundary: pass
background_job_compatibility: pass
security_and_authority_preservation: pass
exact_plan_revision_binding: pass
bootstrap_self_host_boundary: pass
ux_contract: NotApplicable
visual_fidelity: NotApplicable
~~~

## Mandatory Implementation Guards

1. Preserve PR #20 Task/branch/PR transport identity for every Slice.
2. Before every Slice, re-read current Task, exact Approved Plan R4 blob, exact Slice Set, canonical main, and current PR head.
3. Any Requirement/Plan/transport drift invalidates current Slice admission.
4. S01 product mutation is forbidden until an explicit task-scoped `#开发引导执行 ... direct:codebuddy` override is admitted and read back.
5. Bootstrap does not alter project binding and cannot create replacement branch/PR or permission/credential/write-scope expansion.
6. No fallback to synchronous direct/codex while its durable async boundary is not yet live-verified.
7. Same semantic identity + same request reuses operation; changed authority-bearing request conflicts before callback.
8. No provider callback before durable claim + ADMITTED record.
9. SUCCEEDED requires durable receipt first.
10. OUTCOME_UNKNOWN/nonterminal/quarantined evidence is not terminal-GC eligible.
11. Tombstone must be durable/read-back verified before terminal full-artifact cleanup.
12. Tombstone expiry alone never authorizes material replay; material descriptors require provider semantic-freshness proof.
13. Direct Codex and Host Runtime freshness logic stays provider-owned; generic core does not interpret DevForge semantics.
14. pending_results remains delivery replay only.
15. Existing AppContainer/Job/mutation-scope/canonical-firewall semantics remain authoritative.
16. One explicit `#开发执行` completes at most one Slice.
17. PR-013 uncertain S03 is never replayed as implementation or acceptance proof.

## Slice Compilation

Compile exactly:

1. **S01 — Core durable operation runtime, atomic admission, protected state, lifecycle, restart/retention core.**
2. **S02 — sentinel_operations local_api start/status/receipt surface.**
3. **S03 — Direct Codex + Host Runtime consumer adoption and background/pending-results compatibility.**
4. **S04 — Windows physical E2E, lost-response/restart/retention/security blocker-closure evidence.**

Dependencies are linear: `S01 -> S02 -> S03 -> S04`.

## Gate Result

~~~yaml
decision: Approved
blocking_findings: []
plan_approved: true_after_slice_set_readback
implementation_authorized: true_after_slice_set_readback
next_stage: implementation
current_slice_after_transition: S01
execution_entry:
  bootstrap_required_before_s01: true
  target: direct:codebuddy
canonical_next_action: "#开发引导执行 PR-020-durable-async-operation-runtime-outcome-readback-v1 direct:codebuddy"
~~~

No product implementation, Host policy mutation, installed-Agent mutation, production Hub change, project-binding change, PR-013 replay, PR-019 mutation, merge, release, or deployment is performed by this review.
