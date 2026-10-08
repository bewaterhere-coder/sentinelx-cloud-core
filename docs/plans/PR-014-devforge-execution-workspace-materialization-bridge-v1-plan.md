# PR-014 — Plan R10: Source Ownership & Actual Short-Mutation Consumer Readback

```yaml
task_id: PR-014-devforge-execution-workspace-materialization-bridge-v1
requirement_revision: 5
plan_revision: 10
stage: ready_for_plan_review
plan_approved: false
implementation_authorized: false
canonical_pr: 14
branch: task/devforge-execution-workspace-materialization-bridge-v1
prior_plan_r9_s03a: completed_negative_reconciliation
historical_candidate: 45dc99d15a23c499b4c1500fab60ed5e76475aeb
```

## Scope

One read-only evidence slice **S04A** only. This plan must not authorize product mutations, Git tree restoration, canonical main change, Host policy edits, materialization, agent lifecycle, CI workflows, or historical S01/S02 replay. It consumes prior S03A negative evidence and a new live Host readback: operational Windows agent `0.24.1.dev260+g45dc99d15` exposes `devforge_runtime` contract revision 2 including `execute_scoped` (API existence verified), but has not proven an actual bounded business consumer or source ownership.

## S04A — Canonical product owner / effective policy / consumer admission

```yaml
slice_id: S04A
depends_on: []
effects: [github_repository_read, sentinelx_structured_read_only_api, documentation_only_receipt_write_to_existing_pr14]
forbidden_effects: [product_code_mutation, host_mutation, canonical_main_mutation, scope_provision, scoped_execution, materialize_workspace, git_rebase, git_cherry_pick, source_restore, s01_s02_replay, long_agent_invocation]
outputs:
  - installed_agent_source_provenance_and_canonical_main_topology_matrix
  - effective_host_policy_roots_readback_or_explicit_unverified
  - execute_scoped_actual_consumer_and_gap_matrix
  - no_delta_or_product_delta_decision_with_receipt
checkpoint_required: true
```

Read canonical main tree and GitHub historical file-change evidence to determine **whether and why** source paths moved/disappeared; pair with read-only installed package/runtime identity without assuming the installed version identifies canonical main. Inspect closed `devforge_runtime` projection and effective Host source/protected/execution placement policy via structured read-only endpoints only. Find an actual short `execute_scoped` consumer and distinguish its current capability from missing workspace placement needs. Explicitly mark unverifiable facts as `unverified`.

Decision must be `NoAdditionalProductDeltaNeeded`, `ProductDeltaCandidateRequiresNewReviewedPlan`, or `DecisionRequired/Blocked`. A positive product-delta decision is **not implementation authority**; it only supports a separate exact-path, exact-test Plan Review. A negative result is valid S04A evidence and prevents blind development. Write evidence/receipt to PR #14, verify exact remote readback and preserve Task/branch identity.

## Gate and acceptance

Plan R10 review may admit a **single executable read-only S04A** only. The approved Plan R9 S03A completed checkpoint remains immutable. R10 cannot compile future product slices. Security invariants from Requirement R5/R4 and merged PR-021 stay frozen for future gates. PR mergeability unresolved and no automatic rebase or restore is authorized.

Next: `#开发评审 PR-014-devforge-execution-workspace-materialization-bridge-v1`.
