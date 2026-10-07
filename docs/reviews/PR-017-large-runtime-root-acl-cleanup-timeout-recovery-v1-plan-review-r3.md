# PR-017 — Large Runtime Root ACL Cleanup Timeout & Recovery V1 — Plan Review R3

## Review State

```yaml
task_id: PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1
review_target: plan
requirement_revision: 1
requirement_blob_sha: 6fd4d1cbe0233368f6e33a3c9be3b5b9236a9eea
plan_revision: 3
plan_blob_sha: 4c73e1b33489c5965ff2fd42156e680b74a6887e
reviewed_task_head: d25c1fefc9d7b5194a3886af9a395f1395c9f288
result: Rejected
runtime:
  devforge_main: 050d9c9559a173a3e0b37fcd2a9db702b6b5a7e6
  review_contract_version: "1.3"
  review_contract_blob_sha: e8fe92cf1e98c3f7eb5bd60277bde8b42b381df7
  slicing_contract_version: "1.1"
  slicing_contract_blob_sha: d173ce7aa909def855b4fe3899e9a3da54b6a330
  artifact_state_transition_contract_version: "1.1"
  artifact_state_transition_contract_blob_sha: 4af7d9b41313f43bf4cc1fb3ab7927de722718ed
next_gate: plan_review_rejected
next_expected_actor: planner
```

## Decision

**Rejected.**

Plan R3 resolves both substantive Plan R2 payload findings. The production-subset integration model is technically acceptable:

- the integration payload is reduced to 11 CAS-bound files;
- all current PR-017 blobs still match the reviewed CAS baseline;
- `src/sentinelx_core/handlers/scoped_script.py` is preserved at blob `4580475ba9bd8ba5301b579ee11a584abbd75d4b`;
- the derived `windows_mutation_sandbox.py` blob `1e662eba2dbc61825bc874e102a735e7a9d9a179` contains the generic compatibility lifecycle and contains none of the PR-018/S01 diagnostic-only terms;
- the derived Windows sandbox test blob `926900b91055707528a6cfdd5fb131d11abdfc89` only genericizes the Task-specific test name;
- S01 and S02 remain valid completed evidence and do not require replay.

However, Plan R3 still contains stale **Plan R2 authority references** in execution-gating prose. Because Plan R2 was formally rejected, those statements create an impossible/ambiguous authority condition for Implementation Ready. This is a blocking Plan consistency issue, not a product or Requirement issue.

Requirement Revision 1 remains unchanged.

## Review Checks

### Solution direction — PASS

The revised direction is correct:

```text
PR-017 completed S01/S02
+ PR-018 production subset
→ PR-017-owned S03 replay
→ R8.3 + cleanup/containment verification
```

### Production-subset minimality — PASS

Fresh readback proves:

```yaml
projected_files: 11
scoped_script_preserved_blob: 4580475ba9bd8ba5301b579ee11a584abbd75d4b
derived_windows_sandbox_blob: 1e662eba2dbc61825bc874e102a735e7a9d9a179
derived_windows_test_blob: 926900b91055707528a6cfdd5fb131d11abdfc89
```

The derived sandbox contains none of:

```text
enable_pr018_paired_session_read
pr018_paired_session_absence
PR018_S01_PAIRED_DIAGNOSTIC
.pr018-s01-paired
```

It still contains the generic production contracts required by PR-017's combined candidate, including the Host-owned Session-0 toggle, durable `SessionObjectReadBinding`, and exact read-only mask definitions.

### CAS drift guard — PASS

Every `current_blob` in the R3 manifest still equals the actual blob on current PR-017. No integration target has drifted after Plan remediation.

The preserved `scoped_script.py` blob also still matches.

### Requirement traceability — PASS

Revised S03 still verifies the real Requirement behavior:

- scoped Python functional;
- real Unity 6000.6.4f1 initializes through the scoped boundary;
- bounded large-root cleanup completes;
- terminal closure is real;
- exact AppContainer SID is absent after cleanup;
- Session-0 authority is exact and temporary;
- Job/no-breakaway, PR-011/PR-012 verification, audit and canonical firewall remain valid;
- temporary compatibility authority is restored to default-off.

### S01/S02 preservation — PASS

S01 and S02 remain completed historical slices. No product drift exists that independently invalidates those receipts.

R3 correctly requires the combined S03 regression set to detect integration regressions without replaying the earlier slices.

### Cross-Task ownership — PASS

PR-018 receipts remain dependency evidence only. PR-017 must generate its own S03 run/checkpoint/receipt.

### Plan revision authority consistency — FAIL

Finding: `StalePlanR2AuthorityReferences`.

Plan Revision 3 still contains these stale references:

```text
line 352:
After Plan R2 approval, S03 execution first materializes ...

line 425:
... artifacts may change only to record Plan R2 lineage ...

line 451:
... #开发执行 ... after Plan R2 approval may complete ...

line 453:
No product mutation is authorized until Plan Review approves Plan R2 ...

line 498:
Does Plan R2 avoid treating PR-018 isolated evidence ...
```

The blocking subset is lines 352, 451 and 453 because they define Implementation authority using a Plan revision that was already rejected.

Under the Slicing Contract, executable Slice authority must bind to the **current Approved Plan revision**. Therefore R3 cannot be approved while its own execution prose points to rejected R2 approval.

## Required Plan R4 Correction

Plan remediation must make only clerical/authority-lineage corrections:

1. Replace all execution-authority references from **Plan R2** to **Plan R3**.
2. Replace “record Plan R2 lineage” with “record Plan R3 lineage”.
3. Replace the stale Review Question reference from Plan R2 to Plan R3.
4. Make no change to:
   - Requirement Revision 1;
   - the 11-file production-subset manifest;
   - either derived blob identity;
   - the preserved `scoped_script.py` blob;
   - S01/S02 completion evidence;
   - S03 verification scope;
   - canonical PR/branch identity.
5. Do not compile the R3 Slice Set until the corrected Plan revision is reviewed and approved.

## Rejected Findings

```yaml
findings:
  - id: StalePlanR2AuthorityReferences
    severity: blocking
    scope: plan
    correction: replace every stale Plan R2 authority/lineage/review reference with the current remediated Plan revision while preserving all technical semantics
```

## Gate Result

```yaml
decision: Rejected
requirement_revision: 1
requirement_change_required: false
plan_revision_reviewed: 3
plan_approved: false
implementation_authorized: false
stage_after: plan_review_rejected
current_slice: S03
s01_state: completed
s02_state: completed
s03_r1_state: blocked_historical
r3_slice_set_compiled: false
canonical_next_action: "#开发计划修复 PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1"
```

No product code, tests, Host policy, Slice Set, PR-018 state, S01/S02 evidence, or canonical main is mutated by this review.
