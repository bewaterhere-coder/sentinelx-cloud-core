# PR-017 — Large Runtime Root ACL Cleanup Timeout & Recovery V1 — Plan Review R5

## Review State

```yaml
task_id: PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1
review_target: plan
requirement_revision: 1
requirement_blob_sha: 45e572e905a07925bd8a05fba19598b2ce62e3c8
plan_revision: 5
plan_blob_sha: 1542d734c3e0aed6aa6818947a75dc26814e8912
reviewed_task_head: 28c4a3a619612cd2520fe51e988235c81b3de3fc
result: Approved
runtime:
  devforge_main: 050d9c9559a173a3e0b37fcd2a9db702b6b5a7e6
  review_contract_version: "1.3"
  review_contract_blob_sha: e8fe92cf1e98c3f7eb5bd60277bde8b42b381df7
  slicing_contract_version: "1.1"
  slicing_contract_blob_sha: d173ce7aa909def855b4fe3899e9a3da54b6a330
  artifact_state_transition_contract_version: "1.1"
  artifact_state_transition_contract_blob_sha: 4af7d9b41313f43bf4cc1fb3ab7927de722718ed
next_gate: slice_compilation
next_expected_actor: orchestrator
```

## Decision

**Approved.**

Plan R5 is technically coherent, bounded to Requirement Revision 1, free of stale current-authority references, and sufficiently deterministic for Slice compilation.

The Plan may advance to Implementation Ready only after a new Plan-R5-bound canonical Slice Set is compiled and read back.

## Review Checks

### Solution direction — PASS

The final implementation path is:

```text
historical PR-017 S01/S02 completion evidence
+ frozen PR-018 production subset
→ canonical PR-017 combined candidate
→ PR-017-owned S03 / R8.3 replay
→ cleanup/security/regression closure
```

No Requirement redesign is introduced.

### Production-subset manifest — PASS

The exact integration surface is bounded to 11 files and uses compare-and-swap current-blob guards.

Fresh readback at review time proves all 11 current blobs still equal their Plan-R5 expected values.

### Diagnostic seam exclusion — PASS

`src/sentinelx_core/handlers/scoped_script.py` is preserved at:

```text
4580475ba9bd8ba5301b579ee11a584abbd75d4b
```

and is not part of the integration payload.

The derived sandbox blob:

```text
1e662eba2dbc61825bc874e102a735e7a9d9a179
```

contains none of the PR-018/S01-only diagnostic surfaces:

```text
enable_pr018_paired_session_read
pr018_paired_session_absence
PR018_S01_PAIRED_DIAGNOSTIC
.pr018-s01-paired
```

while preserving the generic default-off Session-0 production lifecycle.

### Derived test — PASS

The derived Windows sandbox test blob:

```text
926900b91055707528a6cfdd5fb131d11abdfc89
```

only genericizes the production mask-test name and preserves the test body.

### Requirement traceability — PASS

S03 continues to prove the real Requirement behavior, including:

- scoped Python success;
- exact Unity 6000.6.4f1 initialization;
- raw Unity child status different from `0xC0000142`;
- deterministic `6000.6.4f1` output;
- bounded large-runtime-root cleanup;
- terminal scope closure;
- exact AppContainer SID absence from runtime root;
- exact temporary Session-0 authority removal;
- durable Session-object cleanup binding closure;
- AppContainer and Job containment;
- no-breakaway;
- PR-011 / PR-012 verification health;
- audit lineage and canonical mutation firewall;
- mandatory restoration of `runtime_session_object_read_enabled=false`.

### Historical S01/S02 evidence — PASS

S01 and S02 were completed under Plan R1 and have durable receipts:

```text
S01:
docs/reviews/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-s01-completion-receipt.yaml

S02:
docs/reviews/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-s02-repair-completion-receipt-r4.yaml
```

They remain valid **historical completion evidence**, but under Slicing Contract v1.1 they MUST NOT be represented as completed slices of Plan R5.

The Plan-R1 Slice Set is stale for executable authority because the Plan revision changed.

The Plan-R5 Slice Set MUST therefore:

- supersede the Plan-R1 Slice Set;
- contain only revised `S03` as a current executable Slice;
- set `S03.state=pending`;
- represent S01/S02 only in historical evidence metadata;
- make no R5 completion claim for S01/S02;
- never replay their verified external side effects.

### Slice decomposition — PASS

One current Slice is appropriate:

```text
S03
  = production-subset integration
  + focused/affected regression closure
  + exact Host activation when separately admitted
  + real Unity R8.3 replay
  + cleanup/security readback
  + proof-config restoration
```

This is one meaningful integration/verification boundary and one explicit `#开发执行` may complete at most this Slice.

### Current authority lineage — PASS

No current execution, compilation, lineage, or review authority sentence points to rejected Plan R2/R3/R4.

Historical references to Plan R1/R2/R3 remain descriptive lineage only and do not grant execution authority.

### Risk handling — PASS

The Plan fails closed on:

- CAS drift;
- derived-blob mismatch;
- Host runtime unavailability;
- cleanup ambiguity;
- residual authority;
- Unity initialization failure;
- security/self-check regression;
- unexpected overlap with protected/canonical repository state.

## Approved Slice Compilation Contract

The canonical Slice compiler is authorized to create a Plan-R5 Slice Set with:

```yaml
plan_revision: 5
current_slices:
  - S03
historical_evidence:
  - S01
  - S02
current_completed_slices: []
current_pending_slices:
  - S03
```

No new architectural or product decision may be introduced during compilation.

## Gate Result

```yaml
decision: Approved
requirement_revision: 1
plan_revision: 5
plan_approved: true
implementation_authorized: pending_slice_set_compilation
current_slice: S03
current_slice_state_after_compilation: pending
historical_completed_evidence: [S01, S02]
canonical_next_transition:
  slice_set_compilation
  -> implementation
```

Approval alone does not authorize product mutation until the Plan-R5 Slice Set is persisted and read back.
