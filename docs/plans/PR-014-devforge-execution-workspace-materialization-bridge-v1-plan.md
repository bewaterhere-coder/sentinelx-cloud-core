# PR-014 Plan R12 — Updated Runtime Firewall / Placement Read-only Revalidation

```yaml
task_id: PR-014-devforge-execution-workspace-materialization-bridge-v1
requirement_revision: 7
plan_revision: 12
plan_approved: false
implementation_authorized: false
transport: {pr: 14, branch: task/devforge-execution-workspace-materialization-bridge-v1, base: main}
historical_slices: [S01, S02, S03A, S04A, S05A]
```

## Objective and admission

Fresh Windows SentinelX `0.24.1.dev791+g5d9286b22` capability readback verifies Windows Sandbox/Audit/AppContainer/Job/Scope checks PASS. The previous `runtime_read_authority_roots` self-check failure is no longer observed. **The new release is nevertheless not mutation-ready:** `canonical_repository_mutation_firewall_v1` reports `local_api:direct_codex_containment_unproven`, and the independent DevForge execution root is not evident in effective Host locations. No code/Host/main mutation is authorized.

## Proposed S06A — Exactly one read-only decision slice

```yaml
slice_id: S06A
depends_on: []
allowed_effects: [github_current_main_and_provenance_read, sentinelx_structured_capabilities_and_projection_read, documentation_only_receipt_on_existing_pr14]
forbidden_effects: [product_mutation, host_mutation, canonical_main_mutation, execute_scoped, direct_codex_invoke, materialize_workspace, scope_provision, policy_write, source_restore, rebase, cherry_pick, historical_replay]
verification:
  - canonical_main_sha_and_build_provenance_or_unverified
  - mutation_scope_sandbox_audit_and_firewall_current_readback
  - direct_codex_containment_contract_or_explicit_unverified
  - independent_execution_root_and_protected_root_nonoverlap_or_unverified
  - durable_decision_and_remote_receipt_readback
checkpoint_required: true
```

Read current main SHA/build/package provenance and relevant current implementation ownership. Inspect live Host full capabilities and `devforge_direct_codex` **describe** projection without invoking actions; explicitly distinguish API exposure from verified containment. Record effective locations and firewall readiness; `D:\coco` remains protected and must not be reduced, allowlisted or carved out. Classify `runtime_read_authority_roots` parsing repair as historical if current Host self-check passes; do not reset durable scope records. Record whether the missing execution-root policy is a proven deficiency or an unproven obsolete long-agent requirement under PR-021. Preserve S01-S05A evidence and S02 candidate without replay.

Decision output: `NoProductDeltaNeeded`, `NarrowSecurityRepairRequiresSeparateReviewedPlan`, or `DecisionRequired/Blocked`. Unknowns must be explicit. Document and read back one exact checkpoint/receipt on existing PR #14. Do not compile or execute product slices. For any narrowly justified security change, a future Plan Review must establish exact canonical source files, tests, sandbox/firewall evidence and separate Host-owned placement.

## Review boundary

Plan Reviewer may approve **only** the read-only S06A; no permission expansion, Host installation, protected root change, agent invocation, long-lifecycle ownership, or product implementation. The older R11 S05A is complete historical evidence. This Plan is not self-approved.

Next: `#开发评审 PR-014-devforge-execution-workspace-materialization-bridge-v1`.
