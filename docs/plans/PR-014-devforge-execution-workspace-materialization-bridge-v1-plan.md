# PR-014 Plan R11 — Canonical Source Ownership & Security Repair Disposition

```yaml
task_id: PR-014-devforge-execution-workspace-materialization-bridge-v1
requirement_revision: 6
plan_revision: 11
stage: ready_for_plan_review
plan_approved: false
implementation_authorized: false
canonical_pr: 14
branch: task/devforge-execution-workspace-materialization-bridge-v1
historical_slices: [S01, S02, S03A, S04A]
historical_product_candidate: 45dc99d15a23c499b4c1500fab60ed5e76475aeb
```

## Objective

Resolve a **single read-only decision** on canonical product-source ownership and the narrow safe-runtime repair pathway before any mutation. Consumes S04A observed security failures and PR-021 minimal short-runtime boundary. No product, Host, main, CI, Git-transport or external-agent mutation.

## One proposed slice S05A (read-only only)

```yaml
slice_id: S05A
depends_on: []
allowed_effects:
  - github_repository_read
  - host_structured_read_only_introspection
  - documentation_only_evidence_receipt_on_existing_pr14_branch
forbidden_effects:
  - product_mutation
  - host_policy_mutation
  - main_mutation
  - mutation_scope_provision
  - execute_scoped
  - materialize_workspace
  - source_restore
  - rebase
  - cherry_pick
  - historical_slice_replay
  - long_agent_lifecycle
outputs:
  - canonical_implementation_source_owner_or_explicit_unverified
  - installed_host_runtime_provenance_and_policy_readback_or_unverified
  - additive_mutation_scope_schema_root_cause_and_safe_repair_contract
  - safe_execution_placement_and_short_consumer_necessity_matrix
  - final_no_delta_narrow_repair_or_blocked_decision_receipt
checkpoint_required: true
```

Read current GitHub `main` tree/history, releases/build provenance and installed Host runtime/package identity without assuming the old PR is authoritative. Inspect *read-only* runtime self-check/effective Host policy: `runtime_read_authority_roots` schema incompatibility, sandbox/audit readiness and current legacy `D:\coco` workspace location. Establish whether a real `execute_scoped` short-mutation consumer requires a separate DevForge placement root. If facts remain unavailable, record `DecisionRequired/Blocked` rather than inventing a replacement source owner.

Freeze one disposition: `NoAdditionalProductDeltaNeeded`, `NarrowSecurityRepairCandidateRequiresSeparatePlanReview`, or `DecisionRequired/Blocked`. Document exact evidence and integration approach, then persist/read back a checkpoint and receipt to PR #14. No mutation authority follows automatically from a positive disposition. Product/security/Host deployment needs a separately reviewed, exact-path implementation Plan and physical Receipt. No S01/S02 replay, no protection carveout, no data-store deletion.

## Review gate

A reviewer may approve **S05A only** as a documentation/evidence slice. Historical Plan R10 is superseded by R6. Any refusal to find current canonical implementation topology is a valid negative outcome; no future product slice is preauthorized.

Next action: `#开发评审 PR-014-devforge-execution-workspace-materialization-bridge-v1`.
