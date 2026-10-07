# PR-018 — Unity 6.6 AppContainer DLL Initialization Compatibility V1 — Plan Review R1

## Review State

~~~yaml
task_id: PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1
review_target: plan
requirement_revision: 1
requirement_blob_sha: 414efb5c28993226895a0eacef1ddf71b0722b1e
plan_revision: 1
plan_blob_sha: 12e8c73c3b232bfa4b7b74cf86facff68eabadac
reviewed_task_head: 36d61bc07682a6cda9f72b0bc3c8548759d97903
result: Rejected
finding_classification: plan_local
runtime:
  devforge_version: "2.93.0"
  devforge_revision: 041f390592a78c13f5eabdc542735dc72485e0ef
  review_contract: "1.3"
  artifact_state_transition_contract: "1.1"
  slicing_contract: "1.1"
repository_reality:
  canonical_main: 018b78ca20984176d53fbe90039dc795a7f2742f
  canonical_pr: 18
  canonical_branch: task/unity-6-6-appcontainer-dll-initialization-compatibility-v1
  stacked_base_pr: 17
  stacked_base_head: 3858c7d0e46295d5e0dc184bb21e76da7c963346
  open_pr15_head: 0b710e14e7e7749c7d322199d4bb2892ce1d2805
  open_pr16_head: c26de0e9fb0d908e9dc6bd16403b07965547f099
next_gate: plan_review_rejected
next_expected_actor: planner
~~~

## Decision

**Rejected.**

Requirement Revision 1 remains Ready, and the evidence-first Session-0 USER32 diagnostic direction is accepted. Plan Revision 1 has two P0 implementation-shaping gaps that must be corrected before Implementation Ready.

## F1 — S03 crosses the PR-018 transport / Task boundary

Plan R1 places these operations inside PR-018 S03:

1. integrate PR-018 into the PR-017 branch;
2. rerun PR-017 S03.

That is not a normal PR-018 implementation Slice. PR-018's canonical transport is PR #18 on `task/unity-6-6-appcontainer-dll-initialization-compatibility-v1`; PR-017 owns a different Task and branch. Generic `#开发执行 PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1` must preserve the current Task transport and must not use an implementation Slice to advance another Task.

Plan R2 must separate the boundaries:

- PR-018 S03 ends with exact-candidate Unity/security/regression proof on the PR-018 head only;
- after PR-018 Acceptance, PR-018 finalization may integrate its accepted transport into its configured base branch under `#开发完成 PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1`;
- PR-017 S03 replay remains owned by PR-017 and resumes only through PR-017's own canonical development command/state;
- no PR-018 implementation Slice directly mutates PR-017 Task state, checkpoints, Slice state, or implementation evidence.

Requirement R10 is preserved as cross-Task integration ordering; this correction changes orchestration ownership, not product semantics.

## F2 — Generic Session-0 authority lifecycle is not durably frozen

Current repository behavior proves the existing PR-011 verification Session-0 grant is tracked only in process memory through `_verification_session_reads`. `MutationScopeRecord` and `MutationRuntimeClosure` do not currently represent window-station/desktop authority.

Plan R1 says durable MutationScopeStore tracking should be added "if needed". For the generic untrusted scoped path, it is required. Without durable representation, a broker/service interruption after DACL mutation can leave an exact AppContainer SID ACE that later terminalization cannot prove or clean, while the durable scope has no corresponding residual-authority marker.

Plan R2 must freeze:

1. one durable session-object authority marker/binding in the existing MutationScopeStore lifecycle; no second ledger;
2. ordering that persists the fail-closed authority marker before the external shared-DACL grant can become effective;
3. exact AppContainer SID + service Session-0 window-station/desktop binding sufficient for deterministic cleanup/reacquisition;
4. terminalization treats the marker as residual authority;
5. cleanup removes the exact SID from both objects and reads back absence before clearing the durable marker;
6. crash/restart/retry coverage proving no false terminal state when process-local handle maps are lost;
7. partial grant / second-object failure compensation remains fail-closed;
8. the existing verification trusted-root handshake remains unchanged.

## Accepted Plan R1 direction

The following should be preserved in Plan R2:

- S01 is an evidence-first real-Windows A/B discriminator;
- Variant B changes only the existing PR-011 read masks;
- no filesystem/Registry/COM permission guessing after a negative discriminator;
- Host-owned `mutation_execution.runtime_session_object_read_enabled` is the V1 setting, default off;
- callers cannot override the setting, object selection, SID, or masks;
- PR-011 masks are the maximum V1 authority;
- no interactive desktop, screen, clipboard/global-atom, create-window, write, AppContainer escape, or Job breakaway authority;
- policy identity/digest must include the compatibility setting;
- PR-011 verification handshake semantics remain unchanged;
- exact candidate Unity 6000.6.4f1 proof is required;
- PR-016 remains a reconciliation guard if it later introduces overlapping sandbox product code.

## Gate Result

~~~text
Plan Review R1: Rejected
Requirement Revision: 1 / Ready
Plan Revision: 1 / Rejected
Plan Approved: false
Implementation Authorized: false
Execution Slice Set: not compiled
Current Gate: plan_review_rejected
Next Actor: planner
~~~

No SentinelX product code or Host policy is modified by this review.

## Required Plan R2 delta

1. remove PR-017 branch mutation / PR-017 S03 replay from PR-018 implementation Slices and place them at the correct finalization/successor-Task boundaries;
2. freeze durable generic Session-0 authority tracking, ordering, cleanup/readback, and restart/retry semantics in the existing MutationScopeStore lifecycle.

No Requirement rewrite is requested.
