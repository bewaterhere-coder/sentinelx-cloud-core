# PR-011 — Plan Review R6

## Review Identity

```yaml
schema_version: "1.0"
kind: devforge_plan_review
project_id: sentinelx-cloud-core
task_id: PR-011-scoped-verification-toolchain-dependency-capsule-v1
source_command: "#开发评审 PR-011-scoped-verification-toolchain-dependency-capsule-v1"
requirement_revision: 2
requirement_blob_sha: ffc2f28d3d9224868e969a9bea251b9d38b7428d
plan_revision: 6
plan_blob_sha: fc59575081f3d35b7195711961ed387bc7a56fb2
impact_analysis_blob_sha: c3c35ab25448621a4136d736d1aa515dd2dce3ed
prior_rejected_review_blob_sha: 889a632e21b1b3bfeda4e72dd06bb6ee37fb7dad
prior_slice_set_blob_sha: b0e92968c7a082cba6dce251bc3ff5ba50b334e8
reviewed_pr_head: 7a68f18dbab3d5725e90e8d847ec57f014b32505
canonical_main: e7064c9bf4fcd15bdb6f5a2678414210c01d1c00
current_devforge:
  version: "2.51.0"
  main_sha: 7e5a098473d89f88a69066a9bc88d1213b2f7e49
  runtime_blob_sha: 54eb9e4f0c79620357bc2cf1b8d06d6af9771d6d
review_contract:
  version: "1.3"
  blob_sha: e8fe92cf1e98c3f7eb5bd60277bde8b42b381df7
decision: Approved
```

## Conclusion

Plan R6 is **Approved**.

R6 preserves Requirement Revision 2, repairs the R5 workflow/provenance defect, narrows reopened implementation to the two seams disproved by real-Host evidence, and defines verification that observes the actual required Windows behavior before Node/npm readiness can be claimed.

No unresolved material product, security, transport or architecture decision remains at Plan Review.

## Review Findings

### 1. Real-Host descendant-process evidence

**Pass.**

The `PYTHON_CHILD_START` timeout materially invalidates S03's prior real-descendant completion authority. R6 correctly requires the smallest same-interpreter child process to pass on the real Host before Node/npm or npm lifecycle proof is attempted.

### 2. Toolchain ACL impact scope

**Pass.**

The `C:\Program Files` ACL failure reopens only the provider-toolchain reachability seam. R6 does not replay source/capsule materialization, audit binding, integrity checks or terminal cleanup.

### 3. Requirement stability

**Pass.**

Requirement R2 already requires:

- minimum provider-owned read/execute authority;
- real AppContainer Node/npm execution;
- descendant containment inside the no-breakaway Job;
- one scoped executor/scope/audit/sandbox authority;
- fail-closed behavior with no network/credential/unrestricted fallback.

The new evidence is implementation-shaping evidence, not Requirement semantic drift.

### 4. S02R minimum-authority design

**Pass.**

R6 forbids protected/system ancestor ACL mutation merely for toolchain reachability, limits transient authority to the exact admitted toolchain root, preserves read-only execution authority and fails closed when existing traversal is insufficient.

The prior real-Host run already demonstrated that after protected-parent ACL widening was removed, execution progressed to process creation, so this rule is physically relevant rather than speculative.

### 5. S03R descendant repair boundary

**Pass.**

The Plan explicitly limits investigation and repair to the existing Windows spawn/AppContainer/Job path, including child-process attributes, handle inheritance, token semantics, Job inheritance, environment and executable initialization.

It forbids:

- Job breakaway;
- launching descendants outside AppContainer;
- a second executor;
- broker-side unrestricted fan-out;
- generic Host shell/exec fallback;
- caller-minted process authority.

This preserves R6's one-executor requirement.

### 6. Evidence preservation / no replay

**Pass.**

Evidence disposition is correctly narrow:

- S01 remains completed and no-replay;
- prior S02 receipt is historical authority for unaffected behavior only;
- prior S03 receipt is historical authority for unaffected environment/integrity behavior only;
- S02R and S03R reopen only invalidated seams;
- S04 remains incomplete/unpublished;
- S05 remains not started.

### 7. Repair order

**Pass.**

The only valid implementation order is:

```text
S02R -> S03R -> S04 -> S05
```

This prevents readiness/capability work from masking an unproven descendant-process path.

### 8. Fail-closed architecture boundary

**Pass.**

If descendant execution cannot be repaired under the existing AppContainer/Job/Scope/audit constraints, R6 explicitly requires returning upstream rather than weakening containment.

### 9. R5 provenance blocker remediation

**Pass.**

R6 is bound to:

```yaml
DevForge: 2.51.0
DevForge main: 7e5a098473d89f88a69066a9bc88d1213b2f7e49
Runtime blob: 54eb9e4f0c79620357bc2cf1b8d06d6af9771d6d
Review Contract: v1.3
Rejected R5 review: 889a632e21b1b3bfeda4e72dd06bb6ee37fb7dad
```

The invalid prior `implementation -> plan_review` remediation path is not reused.

### 10. Current transition provenance

**Pass.**

The R6 remediation entered from durable `plan_review_rejected`, persisted the revised Plan, read it back, and persisted a verified `plan_review_rejected -> plan_review` transition receipt.

No self-approval occurred and no R6 Slice Set was compiled before this review.

## Approval Conditions for Implementation Entry

Approval alone does not authorize implementation until the exact R6 Execution Slice Set is compiled, persisted and read back.

The Slice Set MUST:

- bind Requirement R2 + exact Plan R6 blob;
- bind this exact Approved Review;
- import S01 as completed/no-replay;
- preserve S02/S03 prior receipts as partial historical evidence only;
- create pending S02R, S03R, S04 and S05;
- set current Slice to S02R;
- sequence exactly `S02R -> S03R -> S04 -> S05`;
- retain PR #11 / existing task branch;
- mark the old R4 Slice Set stale/non-authorizing;
- preserve one explicit `#开发执行` invocation → at most one Slice;
- publish no dirty local S04 candidate merely because the Plan is approved.

## Review Disposition

```yaml
decision: Approved
blocking_findings: []
plan_revision: 6
plan_approved: true_after_exact_slice_set_readback
implementation_authorized: true_after_exact_slice_set_readback
next_transition:
  from: plan_review
  to: implementation
  required_evidence:
    - current Approved Plan R6
    - this Approved Plan Review
    - exact current R6 Execution Slice Set readback
next_expected_actor_after_transition: implementer
canonical_next_action_after_transition: "#开发执行 PR-011-scoped-verification-toolchain-dependency-capsule-v1"
```
