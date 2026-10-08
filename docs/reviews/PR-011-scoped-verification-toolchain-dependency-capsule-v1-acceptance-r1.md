# PR-011 — Scoped Verification Toolchain & Dependency Capsule V1 — Acceptance R1

## Decision

```yaml
task_id: PR-011-scoped-verification-toolchain-dependency-capsule-v1
requirement_revision: 2
plan_revision: 6
acceptance_revision: 1
result: Rejected
finding_classification: repair_local
finding_code: AC11RelevantWindowsCIRegression
canonical_transport: github-pr
pr_number: 11
canonical_branch: task/scoped-verification-toolchain-dependency-capsule-v1
evaluated_head: a25c3d9dd31d86a2e393e5afd8fe2b6cb76828af
verified_product_candidate: 9948eb4d481ca773b2ea14cf2571e0cf6342f213
canonical_main: e7064c9bf4fcd15bdb6f5a2678414210c01d1c00
current_stage: fixing
gate_transition: acceptance_to_fixing
acceptance_approved: false
completion_verified: false
```

**PR-011 Acceptance R1: Rejected.**

The implementation is substantially complete and the required live Windows Host behavior is physically proven, but Acceptance cannot approve while the current relevant PR-011 S04 Windows workflow is red. This directly conflicts with Requirement AC11 and the approved S04 verification rule requiring relevant CI to pass.

The finding is `repair_local`. No Requirement or Plan semantic change is needed.

## Runtime / Transport Consistency

PASS.

- DevForge source of truth: `bewaterhere-coder/DevForge main@af6cfb5153b5c982d9039e4c9f74fe44940ddbfb`.
- Acceptance Contract: `contracts/development/acceptance-contract.md` v1.5, blob `1c5e96a20d665e68b1f68e18b7d294945e501ec2`.
- Latest observed DevForge release: `v2.67.0`.
- Canonical repository: `bewaterhere-coder/sentinelx-cloud-core`.
- Canonical PR: #11, open/draft, branch `task/scoped-verification-toolchain-dependency-capsule-v1`, base `main`.
- Evaluated head: `a25c3d9dd31d86a2e393e5afd8fe2b6cb76828af`.
- Canonical main: `e7064c9bf4fcd15bdb6f5a2678414210c01d1c00`.
- GitHub reported the PR mergeable at evaluation.
- No TransportDrift was found.

The exact verified product candidate is `9948eb4d481ca773b2ea14cf2571e0cf6342f213`. The evaluated head is five commits ahead only for checkpoints, Slice Set state and completion receipts. Compare readback shows no product-code change after that candidate.

## Requirement Change Guard

PASS.

- Requirement Revision 2 remains current.
- Plan Revision 6 remains current and Approved.
- S01 is preserved/no-replay.
- S02R, S03R, S04 and S05 use the Revision-2 / Plan-R6 repair sequence.
- The dirty historical S04 workspace was not published wholesale.
- PR-007, PR-010 and PR-012 authority seams remain reused rather than duplicated.
- Downstream ChatGPTControlShell PR-015 evidence remains explicitly non-gating.

No stale Requirement interpretation is used to create this decision.

## Positive Acceptance Evidence

### AC1 — PASS

Provider-owned logical Node/npm profiles, source/capsule integrity identities and caller-path rejection are covered by S01 and S05 schema/admission evidence.

### AC2 — PASS

S02R restricts transient toolchain authority to exact-root read/execute only, and S03R physically proves real Node/npm execution while preserving no-write and terminal cleanup semantics.

### AC3 — PASS

S03R real-Host evidence proves deterministic offline npm operation and package-script execution inside the existing AppContainer/Job path.

### AC4 — PASS

Preserved S01/S02 integrity evidence plus S04 request-time drift/tamper checks cover wrong profile, source/capsule/lock/toolchain mismatch and post-readiness tamper rejection.

### AC5 — PASS

S03R, S04 and S05 evidence show DNS/HTTP/network fallback unavailable and credential/proxy authority absent.

### AC6 — PASS

Real-Host descendant execution remains in the no-breakaway Job, exact-workspace mutation authority is preserved, protected/provider roots remain inaccessible or non-writable, and terminal readback shows no residual authority.

### AC7 — PASS

Unprofiled scoped Python behavior and base `host_mutation_sandbox_v1` readiness remain compatible. Verification-profile absence does not disable the base sandbox.

### AC8 — PASS

S04 and live S05 activation prove separately gated Node/npm readiness is false when the profile is absent and true only after a real AppContainer self-check with Node/npm, network-denial, protected-root-denial and terminal-authority checks.

### AC9 — PASS

The exact S05 candidate was activated as Agent `0.24.1.dev403+g9948eb4d4`. Live `devforge_runtime.describe` exposed the bounded `verification` selector, and live `execute_scoped` returned bounded profile/toolchain/capsule/offline/audit/terminal evidence. Scope `mss_Z3lQdi9jbPHmH7OH9DXL7ftc` independently read back `terminal`.

### AC10 — PASS

Repository coverage includes policy/profile contracts, path/overlap validation, source/capsule integrity, environment sanitization, Windows sandbox/materialization, offline execution, readiness, local-api integration and negative authority-field cases.

### AC12 — NON-GATING

No downstream PR-015 receipt is required for PR-011 Acceptance. Its absence does not affect this decision.

## Blocking Finding

### F1 — AC11 / S04 relevant Windows CI is failing

Classification: `repair_local`.

The evaluated head has fresh generic and focused successes, including:

- `ci` run `37465837749`: success;
- `macos-agent` run `37465837667`: success;
- `pr011-s05-verification` run `37465837819`: success;
- PR-011 S01/S02/S03 and PR-010 regression workflows: success.

However, the relevant S04 Windows workflow is red:

```yaml
workflow: pr011-s04-verification
run_id: 37465837618
job_id: 112276510445
conclusion: failure
result: 2 failed, 53 passed, 1 warning
failed_tests:
  - tests/test_verification_readiness.py::test_real_windows_node_npm_readiness_is_physical_and_revokes_toolchain_acl
  - tests/test_verification_readiness.py::test_post_readiness_toolchain_tamper_fails_before_start
failure_shape: VerificationRuntimeReadiness.available == false
```

The same workflow also failed on the exact product candidate:

```yaml
run_id: 37462685310
job_id: 112265911567
conclusion: failure
result: 2 failed, 53 passed, 1 warning
```

Therefore this is not merely evidence-persistence drift after the product candidate.

The mandatory real Host gate itself remains green: S04 SYSTEM proof passed `35/35`, S05 live readiness passed, and live profiled execution/terminal readback passed. That evidence shows the target Host behavior is viable, but it cannot make a specifically required relevant CI failure disappear.

The S04 completion receipt is retained as valid evidence for its real-Host behaviors, but it cannot independently satisfy the Acceptance statement that relevant CI passes while the current canonical PR workflow is red.

## Required Repair

The fixing pass must stay inside current Requirement R2 / Plan R6 and must not weaken any physical Host gate.

Required outcome:

1. Reconcile `.github/workflows/pr011-s04-verification.yml` and the Windows readiness fixture/CI boundary so the workflow truthfully matches its declared role.
2. Either make the hosted Windows readiness path deterministic under the same security invariants, or separate non-Host CI coverage from the mandatory `D:\coco` physical Host proof without pretending hosted CI is equivalent to that proof.
3. Re-run `pr011-s04-verification` successfully on the exact repaired product head.
4. If readiness/product semantics change, re-run affected S04 physical Host proof and S05 live/regression evidence; if only CI harness semantics change, preserve existing real-Host evidence only after an explicit impact analysis.
5. Persist corrected repair evidence before Acceptance is repeated.

Forbidden repairs:

- network or credential widening;
- `operator_unrestricted`;
- allowlist/permission expansion;
- Hub modification;
- second executor/sandbox/scope/audit authority;
- weakening or skipping the mandatory real Host proof merely to turn CI green.

## Acceptance Result

```text
Acceptance Approved: false
Completion Verified: false
Result: Rejected
Finding: AC11RelevantWindowsCIRegression
Finding Class: repair_local
Gate Transition: acceptance -> fixing
Current Stage: fixing
```

The Task must not be merged or marked done from this state.

Canonical next action:

`#开发执行 PR-011-scoped-verification-toolchain-dependency-capsule-v1`
