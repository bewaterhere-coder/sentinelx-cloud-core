# PR-014 — SentinelX DevForge Execution Workspace Materialization Bridge V1 — Plan Review R7

## Review State

~~~yaml
task_id: PR-014-devforge-execution-workspace-materialization-bridge-v1
review_target: plan
requirement_revision: 3
requirement_blob_sha: 2de30e1386f9627e9615d1f30a5fd42d753f43df
plan_revision: 7
plan_blob_sha: cd5b3f379b03e778d7fe5368325855866f4fb9c2
reviewed_task_head: 7c81f31fa2d6dc701d4cc006d0c0e910ae89db62
result: Rejected
finding_classification: upstream_architecture_and_canonical_repository_reality
runtime:
  devforge_version: "2.103.0"
  devforge_revision: ebc25425160790950bd4d4500186652d3bf52416
  review_contract: "1.3"
  slicing_contract: "1.1"
repository_reality:
  canonical_main: cd42e371f18056327c1d8b744f8956a76bc11541
  canonical_pr: 14
  canonical_branch: task/devforge-execution-workspace-materialization-bridge-v1
  pr_head: 7c81f31fa2d6dc701d4cc006d0c0e910ae89db62
  merge_base: e7064c9bf4fcd15bdb6f5a2678414210c01d1c00
  branch_ahead_by: 94
  branch_behind_by: 598
  mergeable: false
next_gate: plan_review_rejected
next_expected_actor: planner
~~~

## Decision

**Rejected / Changes Requested.**

The R7 dual-binding repair is directionally sound in isolation:

- canonical source binding remains Host-owned and protected;
- execution placement is separated into a dedicated Host-owned root;
- `D:\\coco` protection is not weakened;
- caller-selected paths and generic Git/shell/filesystem fallback remain forbidden;
- MutationScope additive durable-schema migration is designed fail-closed and must preserve `runtime_read_authority_roots`;
- S01/S02 product replay remains forbidden;
- exact Windows physical proof remains Acceptance-owned.

However, Plan R7 is not Implementation Ready against current canonical architecture and current canonical repository reality.

Two blocking findings prevent Slice Set compilation.

## Blocking Finding F1 — PR021MinimalRuntimeDispositionNotConsumed

### Severity

~~~yaml
severity: P0
classification: upstream_requirement_semantic_conflict
requirement_change_required: true
plan_only_remediation_sufficient: false
~~~

### Evidence

Canonical `main` already contains the accepted PR-021 Minimal Runtime Boundary V1 architecture decision.

That decision explicitly splits workspace materialization into:

~~~text
workspace isolation / placement needed for short safe mutation
→ retain as minimal security substrate

workspace/bootstrap machinery needed only to run long CodeBuddy/Codex through SentinelX
→ HOLD / later deprecate or reshape
~~~

It further freezes Step 1 of the successor sequence:

~~~text
PR-014 is replanned so its retained target is only the minimum
short-mutation workspace isolation/security substrate proven necessary;

PR-014 long-Agent / direct-CodeBuddy bootstrap objectives are removed
from the active target.
~~~

Requirement R3 intentionally preserves all Requirement R2 semantics except the dual Host binding and MutationScope schema-compatibility repair.

Plan R7 therefore still retains materialization semantics whose end state is a user-level Development Host handoff, including source capsule/materializer, workspace Git readback, handoff ACL normalization and `devforge_runtime.materialize_workspace` as the path to a Development Host execution workspace.

Those semantics are not automatically admitted by the now-canonical Minimal Runtime architecture.

The dual-binding repair may remain useful, but only after PR-014 is reshaped to the minimal short-mutation security substrate required by PR-021.

### Required remediation

The upstream Requirement boundary must first decide and freeze the retained PR-014 scope under PR-021:

1. retain only provider-owned workspace placement/isolation primitives required for bounded short safe mutation;
2. preserve protected-root separation, MutationScope binding, audit, AppContainer/Job confinement and no-caller-path authority;
3. remove or explicitly HOLD long-Agent / Direct Development Host bootstrap, lifecycle and handoff objectives that are not independently required by direct-short operations;
4. identify which source acquisition/materialization/handoff pieces remain necessary for a bounded short mutation consumer rather than carrying S02 forward by historical inertia;
5. preserve historical S01/S02 receipts and candidate `45dc99d...` as evidence only; they do not authorize the new retained target.

Because this changes Requirement semantics, `#开发计划修复` must fail closed rather than silently absorb the change if the Requirement has not first been revised.

## Blocking Finding F2 — CanonicalMainImplementationSurfaceMismatch

### Severity

~~~yaml
severity: P0
classification: canonical_repository_reality
requirement_change_required: conditional
current_plan_implementation_surface_valid: false
~~~

### Evidence

Plan R7 proposes S03 mutations under branch-local paths including:

~~~text
src/sentinelx_core/devforge_workspace_placement.py
src/sentinelx_core/devforge_workspace_source.py
src/sentinelx_core/devforge_workspace_materialization.py
src/sentinelx_core/mutation_scope.py
src/sentinelx_core/handlers/devforge_runtime.py
~~~

Current canonical `main@cd42e371...` does not contain the reviewed core source surface:

~~~text
src/sentinelx_core/policy.py                       → absent
src/sentinelx_core/mutation_scope.py               → absent
src/sentinelx_core/handlers/devforge_runtime.py    → absent
pyproject.toml                                     → absent
README.md                                          → absent
~~~

The PR #14 branch is also currently diverged from main:

~~~text
ahead: 94
behind: 598
mergeable: false
merge base: e7064c9b...
~~~

By contrast, the preserved PR-014 branch still contains the historical product implementation and proves that the dual-binding / MutationScope repair is technically plausible there. That does not make the branch-local tree current canonical product truth.

Plan R7 contains no current-main normalization, successor ownership, or reconstruction strategy for this topology.

Continuing S03 directly on the historical branch would deepen a stale implementation lineage before resolving where the retained minimal-runtime substrate canonically belongs.

### Required remediation

Before any new product mutation:

1. resolve the current canonical product-source ownership/topology after PR-021 and subsequent main normalization;
2. determine whether the retained short-mutation substrate belongs back in this repository/main, in a successor task, or in another canonical runtime surface;
3. bind the revised Plan to source paths that actually exist in the chosen canonical implementation baseline;
4. define a safe same-Task transport normalization or supersession strategy without blind replay of S01/S02;
5. re-evaluate the historical `45dc99d...` candidate only as reusable evidence/code provenance, not as an automatically mergeable current candidate.

No product file should be restored, rebased, cherry-picked or replayed merely to make Plan R7 executable.

## Non-blocking lineage notes

### Requirement blob bookkeeping

Plan R7 records Requirement blob `3df1b5b...`, while the current task/Requirement blob is `2de30e1...`.

The observed difference is workflow/frontmatter bookkeeping from planning to plan-review state, not a new R3 semantic body change. This review binds the current readable Requirement blob and does not reject on that difference alone.

The Requirement's nested historical `requirement_readiness` metadata still references Revision 2 and should be normalized when the upstream Requirement boundary is revised.

### DevForge runtime drift

Plan R7 was authored against DevForge `e0ea494...` / v2.103.0.

Current DevForge main is `ebc2542...`. The delta is one documentation-only evolution artifact and does not modify the Review Contract, project-development workflow, or slicing contract used by this review.

No Runtime drift blocker exists.

### PR-023

Open PR #23 reinforces the already-canonical PR-021 successor sequence and states that PR-014 must not blindly continue long-Agent/workspace-bootstrap scope.

PR #23 is not relied upon as authority for this decision because it is still open; PR-021 on canonical main is sufficient.

## Review Matrix

~~~yaml
r7_dual_host_binding_direction: pass
protected_root_preservation: pass
caller_path_forbidden: pass
mutation_scope_schema_compatibility_direction: pass
historical_s01_s02_no_replay: pass
windows_physical_acceptance_gate: pass
pr021_minimal_runtime_architecture_consumed: fail
current_canonical_main_implementation_surface: fail
current_branch_integration_feasibility: fail
slice_compilation: forbidden
blocking_findings:
  - PR021MinimalRuntimeDispositionNotConsumed
  - CanonicalMainImplementationSurfaceMismatch
~~~

## Gate Result

~~~yaml
decision: Rejected
stage_after: plan_review_rejected
requirement_revision: 3
plan_revision_reviewed: 7
plan_approved: false
implementation_authorized: false
execution_slice_set: null
current_slice: null
s01_s02_historical_evidence_preserved: true
s01_s02_product_replay: forbidden
next_expected_actor: planner
canonical_next_action: "#开发计划修复 PR-014-devforge-execution-workspace-materialization-bridge-v1"
~~~

No product implementation, R7 Slice Set, S03 mutation, Host policy mutation, protected-root weakening, workspace materialization, Development Host invocation, CI execution, PR-013 replay, project-binding mutation or canonical-main mutation is authorized by this review.
