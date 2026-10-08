# PR-027 — Minimal Runtime Active-Lineage Reconciliation & Owner-Gate Closure V1 — Plan R1

## 0. Status / Authority

```yaml
task_id: PR-027-minimal-runtime-active-lineage-reconciliation-owner-gate-closure-v1
requirement_revision: 1
requirement_blob_sha: 237db269f9cd965a7a2c25d938e679865e3cc102
plan_revision: 1
plan_state: ready_for_review
plan_approved: false
implementation_authorized: false
project_id: sentinelx-cloud-core
repository: bewaterhere-coder/sentinelx-cloud-core
transport:
  type: github-pr
  pr_number: 27
  branch: task/minimal-runtime-active-lineage-reconciliation-owner-gate-closure-v1
  base_branch: main
canonical_main_at_planning: 8d2bafba87b529fb458faaa7fbdce39fe225361f
devforge_main_at_planning: ebc25425160790950bd4d4500186652d3bf52416
```

This document is a **Plan proposal**. Its four conceptual Slices are not executable until a separate `#开发评审` approves this exact blob, creates an exact Plan-R1-bound Slice Set and verified transition Receipt. No owner Task mutation is authorized.

## 1. Architectural Decision and Reused Contracts

MRS-01 is the first program stage of PR-023 Roadmap (blob `8a281b60c1b8e9f5d665003a94f4f6b1d906de34`) following PR-021 Minimal Runtime (Requirement done, ADR `36e0290de039336a8e4ce8561c22c731f12e9602`, Disposition Matrix `05b6906614715e14450a2fd03e0699200e016074`).

Existing DevForge `system/development-task-execution-policy-contract.md` owns the stage/Gate model; `system/incremental-plan-execution-slicing-checkpoint-contract.md` owns one-Slice-per-command and exact Plan binding; `system/artifact-state-transition-resolver-contract.md` owns verified transitions; `system/development-command-completion-guard-contract.md` forbids success without verified postconditions. This Task does not introduce a second Gate state machine.

MRS-01 is a **governance program-exit Gate**, distinct from accepting this Task's evidence artifacts:

```text
PR27 governance package complete
  => can be Accepted with a truthful, actionable MRS01 HOLD
  => does NOT permit MRS02

MRS01 ACCEPTED_AND_READBACK
  => only after #13, #14, #19, #20 owner Tasks
     durably reconcile their live Gate states via their own branches,
     each current owner receipt is fetched and verified,
     all four required exit predicates pass.
```

Do not equate `#27 done` with `MRS01 accepted`.

## 2. Current-Branch Evidence Baseline and Drift

| Owner | Exact read facts | Initial state / owner problem |
| --- | --- | --- |
| #13 | `4a3f8e3504b65d1dc222ecb9421ffa16cd96c76d`, Req R1 blob `55317e8ce3fc850167a38928d448fbf76b3bc6b7`, Plan R2 blob `e65fceea327df2820719d0feb74759e733955efb`, Slice Set blob `7608e78ffd0f99e7823928b3daf1e16ad981eeda` | Implementation/S03 pending; historical S01/S02; old long Agent materialization and publication promises require PR-021 disposition and exact new-main source review |
| #14 | `1dc1e8a649417fc59ee0cd641c955af155b9a687`, Req **R8** blob `cbcf65d391b3aa0f89b8366b870241d5e1cc4a64`, Plan **R14** blob `d860b40805dd0cc0c96670fd84e7e4fea6deb487`, prior Review R13 `4099cdcb1abbbc72526381237a777ef70fb7249f` | Plan Review pending; proposed S07A read-only evidence gate, with no current product implementation authority. PR description is outdated and MUST NOT override branch Task |
| #19 | `f13dfe874f5de20c843e0c8cba4eb7e8af5731b7`, Req R1 blob `1017f9f54cd34d7868d5c0438eadac6e076f16df`, Plan R2 blob `4aff64a35c00d3e854fc63046faf3045caddaf0b` | S01 pending, old `HostMutationScopeCorrupt` blocker `de5e3d4934968fd43cc5c193c417b6d4f1ced5b2`. Candidate `4ffb2dc312fac8d1030eb521641f6c61c33f11f0` cannot be replayed or assumed tested |
| #20 | `96d4ad0001721d2c0b527fd9a1e2a0fe99116f30`, Req R1 blob `2c2c33e6b969e271c4acb7277b08cd212f2f3de3`, Plan R4 blob `304cbf2ab58b4fa3835c35b343bd1214565c2920` | S01 bootstrap blocked; old Task says `implementation_authorized=true`, but PR-021 architecture / PR-023 MRS-01 freezes development-timeout Durable Async **HOLD**. Owner must durably reconcile |
| independent #16 | `c26de0e9fb0d908e9dc6bd16403b07965547f099` | Node/npm compatibility follows its own Task; no owner mutation |
| independent #26 | `4fa5f4f481f226425719a8eb8a913ef89541f1ad` | Scoped PowerShell AppContainer recovery follows its own Task; no owner mutation |

Every planning SHA is a **snapshot**, not an execution/verification proof of present-day owner readiness. Each Slice MUST refresh main, PR state/head, Requirement/Plan and relevant receipts and record drift independently before classifying.

## 3. Scope and Security Matrix

**In this Task's authorized write scope (after approval):**

- `docs/checkpoints/PR-027-minimal-runtime-active-lineage-reconciliation-owner-gate-closure-v1-*.yaml`
- `docs/architecture/sentinelx-minimal-runtime-active-lineage-owner-gate-matrix-v1.md`
- `docs/handoffs/PR-027-minimal-runtime-active-lineage-reconciliation-owner-gate-closure-v1-pr{13,14,19,20}-owner-packet.md`
- `docs/execution/PR-027-minimal-runtime-active-lineage-reconciliation-owner-gate-closure-v1-*.yaml` (Run/Slice bookkeeping)
- current Task's Requirement workflow metadata and validated receipts

**Out of scope:**

- Any file/PR/branch of owners #13/#14/#19/#20, independent #16/#26, or the DevForge repository;
- `src/`, `tests/`, `.github/workflows/`, settings, Host runtime/config, network scopes, local ACL/Job/AppContainer changes or deployments;
- rebase/cherry-pick/force-push/merge/close/replay of an owner branch;
- changing `D:\coco` protected_root, independent execution root/allowlist, or bypassing the canonical mutation firewall, audit and MutationScope;
- implementing new Durable Async, long Agent bootstrap or deleting generic background/pending-result modules;
- declaring MRS-01 program exit or unlocking MRS-02 from document-only evidence.

Any scope expansion requires upstream Requirement/Plan review under DevForge; it is not authorized by prose in a handoff.

## 4. Slices — Approved only after Plan Review

### S01 — Canonical Reality & Owner-Drift Snapshot

**Inputs:** latest GitHub main, PR #21/#23 completed authority, exact owner PR branches, Requirement/Plan and referenced decision/receipt artifacts, existing current branch PRs, DevForge registry.

**Actions:** produce a structured inventory of current heads/sha, readback verified/missing paths, owner stages and contradictory stale PR prose; distinguish `current` / `historical` / `unverified` / `conflict`. No guessing whether old Host problems persist. No owner Task edits.

**Outputs:** `docs/checkpoints/PR-027-minimal-runtime-active-lineage-reconciliation-owner-gate-closure-v1-s01-owner-reality-*.yaml`, S01 Run + completion Receipt and Task state. **PASS** only if all four identities and ambiguity classifications are explicit.

### S02 — Minimal-Runtime Disposition and Owner-Gate Matrix

**Depends on:** verified S01.

**Actions:** map KEEP / RESHAPE / HOLD to retained short-mutation security, long-Agent nonresponsibilities, current owner canonical Gate and read-only evidence. Record each owner exit predicate and exact missing owner receipt, plus contradictory R14/R13 or PR20 HOLD/implementation state. Negative-case checks include firewall/ACL permissions unchanged and no inference from old live Host tests.

**Output:** `docs/architecture/sentinelx-minimal-runtime-active-lineage-owner-gate-matrix-v1.md`; S02 Run/Receipt. The matrix may record `HOLD`, not declare owner Gate approval.

### S03 — Four Owner-scoped Decision/Handoff Packets

**Depends on:** verified S02.

**Actions:** produce exactly four durable owner-specific packets. Each includes canonical owner Task/branch/head, current Requirement/Plan/Review revision, frozen PR-021 constraints, retained security substrate, unsupported long-Agent scope, required authority/proof, executable *owning Task command* after fresh readback, expected owner Decision + Receipt, abort gates and no-replay restrictions. No owner-PR command is executed by this Slice.

**Outputs:** four `docs/handoffs/PR-027-...-prNN-owner-packet.md`, S03 Run/Receipt.

### S04 — Deterministic Program Exit Projection + Final Verification

**Depends on:** verified S03.

**Actions:** re-read **live owner PR** four separate Gate decisions, matching state/plan/source and receipts; check PR27 changed files, initial snapshot drift, MRS-01 roadmap exit predicates and full AC1–AC16. Produce a **truthful two-level verdict**:

```yaml
coordination_artifacts_verified: PASS | FAIL
mrs01_program_exit: ACCEPTED_AND_READBACK | HOLD
all_four_owner_gate_receipts_verified: true | false
mrs02_admitted: true ONLY_IF mrs01_program_exit == ACCEPTED_AND_READBACK
```

HOLD is a **valid truthful outcome** for a coordination artifact, not an MRS-01 accepted proof. It must include exact blocking owner references/actions. If documentation ACs pass but owner Gate receipts are missing, Task Acceptance MAY approve only the governance package **with program HOLD explicitly retained**. If core documentation ACs fail, Task Acceptance must reject/fix normally.

**Outputs:** Task-owned final verification checkpoint, Run/Completion Receipt and Acceptance entry only when S04's required evidence is durably read back. No implicit owner or successor Gate transition.

## 5. Dependency and Impact Controls

Owner Task-level next actions are recommendations until dispatched by explicit user/DevForge commands against the **original** owner transport. The MRS-01 plan does not own their workload. In particular:

- PR #13 may need a new owner Requirement/Plan Review to cut long-Agent scope before S03 resumes;
- PR #14 current Plan R14 permits only S07A evidence decision *if independently approved*; its old R13 rejection remains history;
- PR #19 candidate `4ffb2dc...` and Host schema blocker must be newly proven or formally retired as stale by its owner, then baseline real-Host proof;
- PR #20 current implementation authorization is contradicted by later Minimal Runtime decision; do not run bootstrap/timeout work before an owner Gate reconciles to HOLD.

MRS-02 (provider-neutral Guided CLI) is downstream. MRS-03 registry migration and MRS-04 physical proof are separate. MRS-05 retirement cannot start before accepted/readback of stages 1–4.

## 6. Review Criteria / Abort Gates

Plan Review must check:

1. Requirement R1 is exact and current; every owner reference names its actual PR/branch and authenticated blob.
2. There is no proposed cross-PR mutation, detached authorization, or new owner Task creation.
3. Each Slice writes only current Task's `docs/` paths and has deterministic checkpoint/receipt expectations.
4. Missing owner receipts cannot be silently counted as closed.
5. PR #14 current R8/R14 and PR #20 program HOLD contradiction are explicitly modeled, not hidden by old PR-body states.
6. Old PR #19 blocker cannot be treated as a current-Host fact without updated evidence.
7. `MRS01=HOLD` does not authorize MRS02 or change DevForge binding.
8. Security controls, protected roots, historical Slices/receipts and canonical main remain untouched.
9. A Plan-R1 exact-digest Slice Set is independently compiled **only after Approval**; implementation does not start with this Plan authoring.

**Plan disposition now:** `ReadyForPlanReview`, not `Approved`; no current execution Slice or final program-exit claim.

## 7. Verification Strategy

- Exact GitHub fetch/sha and owner-state/receipt traceability.
- Negative diff inventory: new PR #27 contains `docs/` only, and only its own Task-owned paths.
- S01 latest main/open PR/branch readback, with sticky snapshots as provenance not fresh truth.
- S02 frozen five-stage roadmap order and PR-021 security invariant checks.
- S03 four unique packets and owner-specific recovery actions.
- S04 full AC1–AC16 and owner-readiness barrier.
- **No GitHub-hosted CI addition**; this task is control-plane documentation. Live Windows Host validation remains on the owner PR that claims a physical capability.

Canonical next command only after Task + Plan and PR #27 remote readbacks are verified:

```text
#开发评审 PR-027-minimal-runtime-active-lineage-reconciliation-owner-gate-closure-v1
```
