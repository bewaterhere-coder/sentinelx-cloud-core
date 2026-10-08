# PR-017 — Large Runtime Root ACL Cleanup Timeout & Recovery V1 — Plan Review R4

## Review State

```yaml
task_id: PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1
review_target: plan
requirement_revision: 1
requirement_blob_sha: c1f6eddf91dcf13aab6d0e4abf457b6465df3267
plan_revision: 4
plan_blob_sha: 7191bfdf51153bb07bac1e912ec83f4699fcbee5
reviewed_task_head: bf27ce33085cfaeee0023790cdd8d1e45504ec46
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

Plan R4 keeps the technically valid production-subset design from R3 and successfully removes every stale Plan R2 authority reference. The technical review remains positive:

- 11-file production-subset manifest is bounded and CAS-guarded;
- all current blobs still match the reviewed PR-017 baseline;
- `src/sentinelx_core/handlers/scoped_script.py` remains preserved at `4580475ba9bd8ba5301b579ee11a584abbd75d4b`;
- derived sandbox blob `1e662eba2dbc61825bc874e102a735e7a9d9a179` excludes the PR-018/S01 paired-diagnostic seam while preserving generic production compatibility;
- derived test blob `926900b91055707528a6cfdd5fb131d11abdfc89` is valid;
- S01/S02 remain completed historical evidence;
- revised S03 still covers PR-017 R8.3 and cleanup/containment.

However, Plan R4 still contains two current-authority statements bound to the already-rejected Plan R3. Under the Slicing Contract, executable Slice authority must bind to the current Approved Plan revision. Therefore R4 cannot be approved until these last two stale authority references are corrected.

Requirement Revision 1 remains unchanged.

## Review Checks

### Production-subset manifest — PASS

Fresh readback confirms all 11 `current_blob` values still match the current PR-017 tree. No integration target drift is present.

### Diagnostic-seam exclusion — PASS

Derived sandbox blob contains none of:

```text
enable_pr018_paired_session_read
pr018_paired_session_absence
PR018_S01_PAIRED_DIAGNOSTIC
.pr018-s01-paired
```

### Generic compatibility semantics — PASS

The derived sandbox still contains:

- Host-owned `runtime_session_object_read_enabled`;
- durable `SessionObjectReadBinding`;
- exact Session-0 read-only masks;
- cleanup/readback and fail-closed terminalization semantics.

### S01/S02 carry-forward — PASS

S01 and S02 remain historical completion evidence and MUST NOT be replayed.

For the current Plan revision, the newly compiled Slice Set must treat S01/S02 as historical evidence and make only revised S03 executable; the stale prior Slice Set must not execute.

### R8.3 traceability — PASS

Revised S03 still requires:

- scoped Python success;
- exact Unity 6000.6.4f1 initialization;
- raw child status not `0xC0000142`;
- bounded large-root cleanup;
- terminal closure;
- exact AppContainer SID absence from runtime root;
- exact temporary Session-0 authority cleanup;
- Job/no-breakaway, PR-011/PR-012, audit and canonical-firewall verification;
- default-off restoration after proof.

### Revision authority consistency — FAIL

Finding: `StalePlanR3AuthorityReferences`.

Two current execution/compilation authority statements remain stale:

```text
line 423:
Plan R3 authorizes no new local design beyond the frozen production-subset manifest.

line 440:
Plan Review R3 must preserve S01 and S02 as completed historical slices with their existing receipts and compile only the revised S03 authority.
```

Plan R3 was formally rejected. These are not merely historical notes; they directly define what is authorized and what Plan Review must compile.

The historical references to:

- `Revision 3 integration objective`;
- `Revision 3 — PR-018 production-subset integration decision`;
- `Plan Review R2 rejected...`;
- historical Plan R1 evidence;

are not blocking by themselves, because they describe lineage/history rather than current execution authority.

## Required Plan R5 Correction

Make only the following lineage correction:

1. `Plan R3 authorizes...` → `Plan R5 authorizes...`.
2. `Plan Review R3 must preserve...` → `Plan Review R5 must preserve...`.
3. Review the Plan once for any other sentence that grants current execution/slice-compilation authority to a rejected Plan revision.
4. Do not change:
   - Requirement Revision 1;
   - the 11-file manifest;
   - CAS blob identities;
   - either derived blob;
   - preserved `scoped_script.py` blob;
   - S01/S02 evidence;
   - S03 verification scope;
   - canonical transport.

## Rejected Finding

```yaml
findings:
  - id: StalePlanR3AuthorityReferences
    severity: blocking
    scope: plan
    correction: bind every current execution/slice-compilation authority sentence to the current Plan revision; preserve historical revision references that are lineage-only
```

## Gate Result

```yaml
decision: Rejected
requirement_revision: 1
requirement_change_required: false
plan_revision_reviewed: 4
plan_approved: false
implementation_authorized: false
stage_after: plan_review_rejected
current_slice: S03
s01_state: completed_historical
s02_state: completed_historical
s03_r1_state: blocked_historical
r4_slice_set_compiled: false
canonical_next_action: "#开发计划修复 PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1"
```

No product code, tests, Host policy, Slice Set, PR-018 state, S01/S02 evidence, or canonical main is mutated by this review.
