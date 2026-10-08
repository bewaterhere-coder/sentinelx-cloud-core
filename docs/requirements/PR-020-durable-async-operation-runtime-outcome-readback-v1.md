---
task_id: PR-020-durable-async-operation-runtime-outcome-readback-v1
title: SentinelX Durable Async Operation Runtime & Outcome Readback V1
project_id: sentinelx-cloud-core
repository: bewaterhere-coder/sentinelx-cloud-core
requirement_revision: 2
development:
  stage: plan_review
  gates:
    requirement_ready: true
    plan_approved: false
    acceptance_approved: false
    completion_verified: false
  plan_revision: 5
  implementation_authorized: false
  execution_disposition: hold
  execution_blocker: MinimalRuntimeArchitectureSupersedesDevelopmentTimeoutExpansion
  owner_control_state: HOLD
  owner_hold_review_pending: true
  blocking_findings:
    - PriorApprovedImplementationConflictsWithPR021MinimalRuntime
    - PriorBootstrapOverrideRevoked
  current_slice: null
  current_slice_state: hold
  completed_slices: []
  bootstrap_required_before_current_slice: false
  bootstrap_target: null
  bootstrap_execution_override_state: revoked
  bootstrap_execution_override_ref: docs/checkpoints/PR-020-durable-async-operation-runtime-outcome-readback-v1-bootstrap-execution-override.yaml
  bootstrap_revocation_receipt_ref: docs/checkpoints/PR-020-durable-async-operation-runtime-outcome-readback-v1-bootstrap-revocation-20261008.yaml
  historical_plan_revision: 4
  historical_slice_set_ref: docs/execution/PR-020-durable-async-operation-runtime-outcome-readback-v1-slices.yaml
  historical_blocked_run_ref: docs/execution/PR-020-durable-async-operation-runtime-outcome-readback-v1-s01-run-001.yaml
  historical_blocked_checkpoint_ref: docs/checkpoints/PR-020-durable-async-operation-runtime-outcome-readback-v1-s01-blocked-20261008.yaml
  next_expected_actor: reviewer
  canonical_next_action: "#开发评审 PR-020-durable-async-operation-runtime-outcome-readback-v1"
transport:
  type: github-pr
  pr_number: 20
  branch: task/durable-async-operation-runtime-outcome-readback-v1
  base_branch: main
artifacts:
  plan: docs/plans/PR-020-durable-async-operation-runtime-outcome-readback-v1-plan.md
  requirement_r1_historical_blob_sha: 2c2c33e6b969e271c4acb7277b08cd212f2f3de3
  plan_r4_historical_blob_sha: 304cbf2ab58b4fa3835c35b343bd1214565c2920
  plan_r4_approval_sha: 2082e376c8bda337f5d82eb34785a499d6295a5c
  legacy_slice_set_historical_blob_sha: f461220e206af7935619640b96288a3880381224
  historical_bootstrap_admission_receipt_sha: 649747ff84130a7e60b93da15c20b77e917c8bd9
  minimal_runtime_adr_sha: 36e0290de039336a8e4ce8561c22c731f12e9602
  owner_gate_matrix_sha: 7507dff0032f29a99387c25f648508c48a03b6e9
  owner_handoff_sha: 3b5ef4d066293250ebc8ebbcf549d9b5f14f94cc
requirement_readiness:
  result: ReadyForHoldPlanReview
  ui_semantics: NotApplicable
---

# Requirement R2 — Owner HOLD Reconciliation

## 1. Decision and authority

**HOLD is effective immediately for this Owner Task's development-timeout-driven Durable Async expansion.** The user explicitly instructed suspension in the existing PR #20. Plan R5 is a **non-executing HOLD reconciliation plan** pending independent DevForge Plan Review. This declaration is not acceptance, feature completion, or a MRS-01 exit decision.

Source authorities, read back on 2026-10-08:
- Current SentinelX `main@2e5c69a112323867ee01783521554c43ebd731be`.
- PR-021 Minimal Runtime ADR `docs/architecture/sentinelx-minimal-runtime-boundary-v1.md@36e0290de039336a8e4ce8561c22c731f12e9602` and Capability Disposition Matrix `05b6906614715e14450a2fd03e0699200e016074`.
- PR-023 successor roadmap `8a281b60c1b8e9f5d665003a94f4f6b1d906de34`.
- PR-027 completed Owner-Gate Matrix `7507dff0032f29a99387c25f648508c48a03b6e9`, PR #20 Owner handoff `3b5ef4d066293250ebc8ebbcf549d9b5f14f94cc`.
- DevForge bootstrap-override contract `system/task-scoped-bootstrap-execution-override-contract.md@31fea7271020e76075b2eed656cbeda0ac8fe52b`.

## 2. Superseding scope and disposition

The R1/R4 proposal to introduce a provider-neutral Durable Async Operation Runtime arose from the DevForge/Direct Codex request-window timeout and missing durable status/receipt handoff. PR-021 now delegates long development and Agent execution lifecycle to DevForge/Guided CLI; SentinelX retains a small bounded scoped-mutation/verification runtime. **A development-timeout workaround is not an independent product requirement.**

- **HOLD:** introduction of any new durable operation scheduler, persistent ADMITTED/RUNNING lifecycle, `sentinel_operations` API, provider adoption, retention/GC protocol or long-Agent bootstrap that was justified solely by the historical development timeout.
- **KEEP unchanged:** existing Agent background exec/script jobs, completion/pending-result delivery, `pending_results` reconnect/replay, current minimal scoped Host runtime, provider-owned receipts and verified readback of bounded work.
- **NOT DECIDED:** whether a future independent product use case warrants a new durable async capability. Such work must supply its own observable need, security/cost evidence, narrower design alternatives, and a fresh authorized Requirement/Plan/Review before any implementation.
- **NOT CLAIMED:** that existing background jobs or pending_results already provide generic durable in-flight operation semantics; do not manufacture that guarantee.
- **NOT AUTHORIZED:** migration of DevForge `direct/codex` binding, widening Host/ACL/AppContainer/Job/MutationScope/firewall/audit authority, or edits to PR #13/#14/#19/#21/#27 and unrelated PRs.

## 3. Execution stop and lineage preservation

Existing original GitHub transport **must remain** PR #20 on `task/durable-async-operation-runtime-outcome-readback-v1`, base `main`; do not create a replacement Task or PR.

The formerly approved Requirement R1 (blob `2c2c33e6b969e271c4acb7277b08cd212f2f3de3`), Plan R4 (blob `304cbf2ab58b4fa3835c35b343bd1214565c2920`), approved Plan Review R4 and corresponding Slice Set are **historical, superseded, NON-EXECUTABLE**. Keep R1 original acceptance criteria AC1–AC24 and all S01–S04 planned specifications recoverable from original Git blobs. Do not replay any Slice or refire previously blocked attempt.

Read-back facts before revision:
- S01 `BLOCKED` (`WorkspaceMaterializationProviderUnavailable`), `provider_process_started=false`, `product_mutation_started=false` in checkpoint `962e3ea9069a29db3d1eba6a8e423df4c2c214c4`.
- Original bootstrap override blob `fbe24326a67fd4620e19b63123b38c4f1fe98c6f`, initial admission Receipt `649747ff84130a7e60b93da15c20b77e917c8bd9`; neither is a license to execute under current authority.
- Bootstrap override is now explicitly **revoked**; historical admission Receipt remains immutable and must not be interpreted as current.
- The old R4 Slice Set is marked historical/suspended; no current implementation Slice or approved Plan is active. No `direct:codebuddy` bootstrap, product mutation, or unrestricted executor fallback is permitted while HOLD.
- Terminal `cancelled` is *not* asserted: this is an Owner HOLD for later explicit decision, not silent task deletion or completion.

## 4. Review-ready requirements

R2-1. Preserve original Task and PR identity, exact Git history and historical Run/Review/Approval/Blocked receipts.

R2-2. Persist and independently read back fail-closed states: `implementation_authorized=false`, `plan_approved=false`, Task Stage `plan_review`, `execution_disposition=hold`, bootstrap override `revoked`, old Slice Set `suspended`.

R2-3. Plan R5 is strictly non-executable HOLD reconciliation. No S01/S02/S03/S04 product Slice is admitted, compiled, restarted, or promoted to acceptance.

R2-4. Preserve existing generic background jobs and `pending_results` functionality verbatim. No product code, test, CI, Host, permission, service or policy mutation.

R2-5. A future admission requires independent product problem/evidence, Requirement impact, explicit Plan/Review approval, new Slice Set tied to exact new approved Plan, and fresh physical Host security/receipt tests where appropriate.

R2-6. The Owner Plan Review must explicitly decide `HOLD` with a durable reviewed decision/transition Receipt before PR-027 program Gate may count this owner as reconciled. Pending Review means program `MRS-01=HOLD` and `MRS-02=not admitted`.

R2-7. Do not modify project binding `direct/codex`; retain AppContainer, Job, MutationScope, canonical firewall, durable audit, `D:\coco` protected root and no-fallback rules.

R2-8. If current main, owner PR Head, Revocation Receipt, Task/Plan/legacy Slice Set, or relevant architectural blob drifts, stop and re-review exact lineage; do not auto-reactivate.

## 5. Acceptance criteria for the HOLD reconciliation

- **AC1** Original PR #20, branch, Requirement R1 / Plan R4 exact blob history is preserved without replay.
- **AC2** PR-021 and PR-027 architectural reasons for HOLD are explicitly linked and independently readable.
- **AC3** Current Task execution/Plan/bootstrap authority is disabled and Revocation Receipt is independently verified.
- **AC4** Legacy R4 Slice Set is suspended; old blocker and initial override admission receipt remain historical.
- **AC5** Generic background jobs and pending_results are untouched; no product/Host mutation.
- **AC6** The new Plan R5 permits only reviewer-owned HOLD decision and receipt, never implementation.
- **AC7** Canonical mutation firewall, AppContainer, Job, MutationScope, ACL/protected root and durable audit are not widened.
- **AC8** `MRS-01=HOLD`, `MRS-02=false` until separately verified Owner disposition; no other Owner Task/Gate is mutated.

## 6. Gate / next action

**Owner execution state:** HOLD (fail-closed). **Workflow stage:** `plan_review` (Plan R5 review pending). These are distinct; neither implies a fresh implementation authorization.

The following is the **only** next DevForge command. Reviewer must verify exact PR #20 Task, Plan R5, suspended Slice Set, revoked bootstrap and receipts. A HOLD-approval only approves administrative suspension, not product execution.

```text
#开发评审 PR-020-durable-async-operation-runtime-outcome-readback-v1
```
