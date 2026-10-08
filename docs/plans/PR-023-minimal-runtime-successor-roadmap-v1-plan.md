---
task_id: PR-023-minimal-runtime-successor-roadmap-v1
title: SentinelX Minimal Runtime Successor Roadmap V1 — Plan
plan_revision: 2
plan_state: accepted_finalization_ready
requirement_revision: 1
project_id: sentinelx-cloud-core
repository: bewaterhere-coder/sentinelx-cloud-core
transport:
  type: github-pr
  pr_number: 23
  branch: task/minimal-runtime-successor-roadmap-v1
  base_branch: main
implementation_authorized: false
finalization:
  status: accepted_finalization_ready
  approved_plan_revision: 2
  approved_plan_semantic_authority_blob_sha: 9e56b512951b8dcaa4b7d6789d3bc350a5f24dce
  implementation_execution_complete: true
  completed_current_plan_slices: [S05R]
  historical_completed_plan_r1_slices: [S01, S02, S03, S04]
  historical_slices_replayed: false
  acceptance_approved: true
  completion_verified: false
  merge_pending: true
  finalization_receipt: docs/checkpoints/PR-023-minimal-runtime-successor-roadmap-v1-premerge-finalization-r1-receipt.yaml
  integration_receipt: docs/reviews/PR-023-minimal-runtime-successor-roadmap-v1-integration-receipt-r1.yaml
  original_pr_number: 23
  canonical_main_at_finalization: 5d9286b22f46ae8bdf6d983b6366da0da3f1323e
---

# Plan R2 — AC2 Recovery Scope

## R2 Narrow Amendment — Prior R1 Implementation Preserved as Historical Evidence

### Reason and change-impact authority

- Requirement remains **Revision 1 with identical semantics**. AC2 already requires direct predecessor completion-evidence citation.
- S05 R1 final verification durably blocked on AC2: `docs/checkpoints/PR-023-minimal-runtime-successor-roadmap-v1-final-verification-blocked-ac2-20261008.yaml` (blob `d4829e0e430e842f27abf47e831737ae069de66d`).
- `docs/reviews/PR-023-minimal-runtime-successor-roadmap-v1-s05-ac2-plan-change-impact-r1.md` (blob `da61cf37f31fb1bad50018e2f32c217eaa160d29`) classifies this as a narrow **Plan/Slice write-scope change**, not a new product or architecture decision.
- Previously Approved Plan R1 blob: `5bdb8e70887a7b78f12d01f81477273d0b0df29b`.
- R1 Slice Set blob: `875857fcf0803abf7a45ef9cb0331631b2487fea`; S01–S04 are completed **under R1 only**. Their original run/checkpoint/receipt files are immutable historical evidence and are **not** executable current-plan slices.
- S05 R1 blocked Run `docs/execution/PR-023-minimal-runtime-successor-roadmap-v1-s05-run-001.yaml` (blob `c0b8bf28c3abf3266683aa7e72007e6396ed75f2`) is historical blocked evidence, not success.

### R2 proposed implementation — single S05R repair/verification Slice

**S05R is not authorized until Plan Review R2 is approved and an exact R2-bound Slice Set is compiled, persisted, and read back.** The reviewer may reject/replan if historical Slice evidence cannot safely be admitted read-only without replay.

```yaml
slice_id: S05R
depends_on_historical_evidence:
  plan: R1
  required_verified_receipts: [S01, S02, S03, S04]
prior_r1_slice_s05:
  state: blocked_historical_evidence
scope:
  write_refs:
    - docs/architecture/sentinelx-minimal-runtime-successor-roadmap-v1.md
    - docs/checkpoints/PR-023-minimal-runtime-successor-roadmap-v1-final-verification-*.yaml
    - docs/execution/PR-023-minimal-runtime-successor-roadmap-v1-s05r-*.yaml
    - docs/requirements/PR-023-minimal-runtime-successor-roadmap-v1.md
    - docs/execution/PR-023-minimal-runtime-successor-roadmap-v1-slices.yaml
  roadmap_write_boundary: exact_two_lines_under_architecture_authority_only
  product_source_write: forbidden
  other_pr_or_cross_repo_mutation: forbidden
```

1. Re-read canonical PR #23/branch/head, Requirement R1 semantics, approved Plan R2 SHA, the freshly compiled R2 Slice Set, R1 historical S01–S04 receipts, PR-021 predecessor authority, current SentinelX `main` and DevForge project registry.
2. Edit **only** the `Architecture authority` list in `docs/architecture/sentinelx-minimal-runtime-successor-roadmap-v1.md`. Append both exact paths **and current Git blob hashes**:
   - `docs/reviews/PR-021-minimal-runtime-complexity-reduction-boundary-v1-integration-receipt-r1.yaml` @ `87bf6ebea89e12d3f8f31dd01a230bc66d8987a8`;
   - `docs/checkpoints/PR-021-minimal-runtime-complexity-reduction-boundary-v1-accepted-to-done-transition-receipt.yaml` @ `e819beaefd1a7d2529edbe561420483cff342b1c`.
3. Assert the Roadmap body outside that authority-list insertion is byte-identical to the S04 Roadmap blob `1117d0279ed9c513424ad12f72ed1ecdb2d7a116`. Do not rewrite stage titles, ordering, disposition rows or retirement gates.
4. Evaluate **all AC1–AC16**, including AC2 direct predecessor completion authority, with exact Roadmap/readback and fresh changed-file/PR/Host/DevForge non-mutation evidence. Use the same PR #23 branch; no hosted CI, product tests or deployment.
5. Persist S05R final verification checkpoint, Run and Completion Receipt under R2 identity. Transition into Acceptance **only** after this independently reviewed Slice passes and transport read-back is verified. No implicit S05-to-acceptance transition from Plan authoring.

### R2 review / recompile gate

The existing R1 Plan Review/transition receipt remains authentic historical R1 evidence; **it does not approve R2**. The R1 Slice Set must not be relabeled as R2 or reused as current authority. Only an independently authorized `#开发评审 PR-023-minimal-runtime-successor-roadmap-v1` may:

- approve this scoped R2 change;
- compile and verify a distinct R2 Slice Set (single S05R execution slice) with correct current Plan digest;
- bind current Task state to implementation and current S05R;
- prove S01–S04 verified historical inputs without replay; reject if any history is missing or contradictory.

The proposed `S05R` is **one new execution-scope definition in the same Task/PR**, not a new Task or a replayed completed Slice. No S05 R1 blocked Run is silently marked complete.

## Historical R1 plan content (reference-only; not current executable scope)

## Objective

Materialize PR-021's frozen Minimal Runtime successor sequence into one durable roadmap and reconciliation artifact without changing product/runtime code, active related PR state, DevForge binding, deployment, or CI.

## Inputs

Canonical predecessor authority:

- `docs/requirements/PR-021-minimal-runtime-complexity-reduction-boundary-v1.md`
- `docs/architecture/sentinelx-minimal-runtime-boundary-v1.md`
- `docs/architecture/sentinelx-capability-disposition-matrix-v1.md`
- PR #21 acceptance/completion artifacts.

Current transport baseline:

- repository: `bewaterhere-coder/sentinelx-cloud-core`
- base branch: `main`
- PR: `#23`
- task branch: `task/minimal-runtime-successor-roadmap-v1`
- base SHA at PR creation: `b0c5addad3aab0c63271dc241a6942b313d6b82d`.

External workflow authority:

- DevForge Runtime `2.102.0` at canonical revision `12cf21254a6c7ca89840dc0cb8445793e913eed8`.
- DevForge project registry currently resolves `sentinelx-cloud-core` to direct/codex execution binding.
- Any binding mutation belongs to a separate DevForge-owned successor Task.

## Planned Artifacts

Primary roadmap:

- `docs/architecture/sentinelx-minimal-runtime-successor-roadmap-v1.md`

Implementation evidence/checkpoint:

- one task-scoped evidence artifact under `docs/checkpoints/` recording:
  - canonical main evidence baseline;
  - open PR inventory;
  - predecessor authority revisions;
  - DevForge binding read-back;
  - final roadmap read-back digest/identity.

No source, test, workflow, deployment, or project-binding files are planned.

## Implementation Steps

### S01 — Canonical Reality Inventory

Read back current canonical `main`, PR-021 authority artifacts, and all currently open SentinelX PRs.

For every open PR, capture:

- PR number / Task identity;
- title;
- base/head;
- current state/stage when durable Task metadata is resolvable;
- architecture relationship;
- evidence worth preserving;
- possible conflict with Minimal Runtime ownership.

Also read the current DevForge `sentinelx-cloud-core` project registration to confirm execution-binding reality.

Stop if predecessor architecture authority is missing, materially contradictory, or PR-021 is no longer the accepted source.

### S02 — Active Work Reconciliation Matrix

Create a revisioned reconciliation section covering every open SentinelX PR visible at the S01 evidence baseline.

Use only evidence-backed dispositions:

- continue;
- reshape;
- hold;
- supersede-candidate;
- close-candidate;
- independent/non-conflicting.

Mandatory constraints:

- PR-014 cannot blindly continue current long-Agent/bootstrap scope;
- PR-019 must not permanently require long-Agent Direct Codex as SentinelX stability;
- PR-020 remains HOLD for the development-timeout motivation;
- no row grants mutation authority over that PR.

For mixed-scope PRs, explicitly separate reusable security/evidence substrate from orchestration-specific work.

### S03 — Five-Stage Successor Roadmap

Write exactly one primary dependency chain:

1. MRS-01 Active Work Reconciliation
2. MRS-02 Provider-Neutral Guided CLI Routing & Handoff
3. MRS-03 DevForge Execution Binding Migration
4. MRS-04 SentinelX Minimal Runtime Proof
5. MRS-05 Long-Agent Surface Retirement Program

For each stage define:

- problem solved;
- owner;
- repository/runtime authority;
- prerequisites;
- allowed scope;
- forbidden scope;
- entry gate;
- exit/acceptance evidence;
- predecessor/successor dependency;
- candidate follow-on DevForge Task title;
- whether work is same-repo or cross-repo.

Do not create/start those follow-on Tasks.

### S04 — Retirement and Safety Gates

Encode explicit no-shortcut rules:

- guided CLI accepted before binding migration;
- binding migration accepted before Minimal Runtime proof;
- Minimal Runtime proof accepted before long-Agent retirement;
- PR-019 baseline reconciliation before Direct Codex retirement;
- equivalent commit/receipt/read-back validation before removing reusable Codex-specific evidence logic;
- component-level retirement Tasks only;
- no broad source deletion authority.

Preserve KEEP/SIMPLIFY security surfaces from PR-021.

### S05 — Deterministic Verification and Read-Back

Verify:

- Requirement and Plan remain unchanged semantically from approved revisions;
- roadmap contains exactly five ordered stages;
- every open PR from the evidence baseline appears in reconciliation;
- every stage has owner/repository/prerequisite/exit evidence;
- PR-014/019/020 mandatory constraints are present;
- cross-repository DevForge mutation is not performed;
- no `src/`, `tests/`, `.github/workflows/`, deployment, or project-binding mutation occurred;
- PR #23 remains the sole transport lineage;
- roadmap and checkpoint are readable from PR head.

No repository-hosted CI is required or introduced. Verification is deterministic artifact/read-back validation for this docs-only scope.

## Test / Verification Strategy

Required:

- GitHub PR/head read-back;
- exact changed-file inventory;
- exact content read-back of Requirement, Plan, roadmap and evidence checkpoint;
- predecessor reference resolution;
- open-PR coverage check;
- five-stage ordering check;
- forbidden-path check;
- project-binding non-mutation check by comparison/read-back where applicable.

Not required:

- product unit tests;
- integration tests;
- Unity/browser tests;
- live Agent deployment;
- GitHub Actions execution.

These are not meaningful proof for a documentation/control-plane roadmap task with no product source mutation.

## Risks and Mitigations

1. **Open PR drift**
   - Mitigation: S01 records exact evidence baseline; S05 revalidates before completion.

2. **Roadmap accidentally mutates other tasks**
   - Mitigation: roadmap classifications are explicit non-authority; no related PR write operations in this task.

3. **Provider-specific guided CLI**
   - Mitigation: MRS-02 acceptance requires provider-neutral identity/evidence contract.

4. **Premature Direct Codex deletion**
   - Mitigation: hard dependency gates require accepted guided CLI, binding migration, baseline reconciliation, and Minimal Runtime proof.

5. **Security simplification**
   - Mitigation: PR-021 KEEP/SIMPLIFY security boundaries are explicit invariants and acceptance checks.

6. **Cross-repository authority leakage**
   - Mitigation: DevForge binding migration is represented only as a successor dependency and separate Task requirement.

## Review Focus

The Plan Reviewer should specifically challenge:

- whether the five stages exactly preserve PR-021's frozen primary sequence;
- whether any open PR can escape MRS-01 reconciliation;
- whether guided CLI semantics are sufficiently provider-neutral;
- whether MRS-03 correctly stays DevForge-owned;
- whether MRS-04 is strong enough to prove Minimal Runtime without demanding long-Agent lifecycle ownership;
- whether MRS-05 retirement preconditions prevent destructive simplification;
- whether CI has been incorrectly reintroduced as a completion requirement.

## Plan Review Boundary

Approval authorizes only later implementation of the documentation/evidence artifacts described above.

It does not authorize:

- source/test changes;
- active PR edits/closures/merges;
- DevForge repository mutation;
- project binding migration;
- Direct Codex removal;
- PR-020 implementation;
- deployment/restart;
- release;
- CI/workflow changes.
