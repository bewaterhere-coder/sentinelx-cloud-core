# PR-011 — Scoped Verification Toolchain & Dependency Capsule V1 — Plan Review R2

## Review State

```yaml
task_id: PR-011-scoped-verification-toolchain-dependency-capsule-v1
review_target: plan
requirement_revision: 1
requirement_blob_sha: d219c40b739c1ae2b4e478f72a7c195c25f8f7cc
plan_revision: 2
plan_blob_sha: c30d771ea5167db92f549bcb8e55589a7550dafd
reviewed_task_head: c0bff982ceadc34c0e5a27ee12c12b980559f4f1
result: Rejected
finding_classification: plan_local
runtime:
  devforge_version: v2.35.0
  devforge_revision: c6972894f187da7d41e384bfbc663a1ae06d1e35
  project_development_workflow: "2.1"
  review_contract: "1.3"
next_gate: plan_review_rejected
next_expected_actor: planner
```

## Scope Reviewed

- Canonical Requirement Revision 1.
- Canonical Plan Revision 2.
- Round-1 Review and Remediation checkpoint.
- Current remote `sentinelx-cloud-core/main@df9252fd4305eed361d8dc84e04da90222cd622e`.
- PR-007 completion/merge state and the resulting canonical `devforge_runtime` seam on `main`.
- PR-010 current state: still unmerged, implementation with S04 pending.
- DevForge `main@c6972894f187da7d41e384bfbc663a1ae06d1e35` / v2.35.0.

## Decision

**Rejected / Changes Requested.**

Plan Revision 2 successfully closes both Round-1 findings in substance:

- F1 source-under-test truth binding is now implementation-shaped with an immutable source snapshot, exact repository/revision identity, broker materialization into the exact workspace, and mandatory package-lock verification before SPAWN.
- F2 toolchain/capsule integrity is now implementation-shaped with a complete toolchain manifest, sealed launcher mechanism, request-time revalidation, explicit resource bounds, and partial-copy cleanup.

No new defect was found in those two remediations.

A new repository-reality blocker appeared after Revision 2 was persisted: PR-007 completed and merged to `main`. The current Plan still treats PR-007 as accepted-but-unmerged and still uses the pre-merge baseline. That assumption now directly changes implementation entry, file ancestry, and Slice construction, so Implementation Ready cannot be granted from the stale Plan revision.

## Blocking Finding F3 — Repository baseline and PR-007 integration state are stale

### Evidence

Plan Revision 2 states:

```text
repository_baseline = f7e878f3497582547e5d52cd33b060cae18d2e84
PR-007 = Accepted but unmerged
Step E = dependency-gated devforge_runtime integration
```

Current repository reality is now:

```text
main = df9252fd4305eed361d8dc84e04da90222cd622e
PR-007 = done / merged
PR-007 merge commit = 26fe28bd5e2317d31e09d2055b191447c3f7ed37
devforge_runtime.py = canonical main seam
```

Git comparison between current main and PR-011 head reports:

```text
status: diverged
PR-011 ahead_by: 24
PR-011 behind_by: 82
merge_base: f7e878f3497582547e5d52cd33b060cae18d2e84
```

The current main `src/sentinelx_core/handlers/devforge_runtime.py` already owns contract revision 1 and the existing `execute_scoped` schema/adapter. Therefore Revision 2's dependency-gated Step E and its statement that this file is not on main are no longer true.

This is not merely documentation drift. The exact implementation surface and the approved Slice Set depend on whether `devforge_runtime` is an external/unmerged dependency or an existing baseline seam.

### Required remediation

Plan Revision 3 must reconcile against current repository reality before another approval attempt:

1. refresh the same PR-011 task branch ancestry against current canonical `main` without creating a replacement PR/branch;
2. record the exact refreshed `main`/task baseline used for planning;
3. update Repository Reality so merged PR-007 / canonical `devforge_runtime` is treated as baseline code, not an external dependency;
4. replace the old dependency-gated Step E with an ordinary integration step that extends the canonical main `devforge_runtime.execute_scoped` contract while preserving its single-executor / generic `sentinel_local_api` boundaries;
5. re-evaluate expected file overlap after the branch refresh, especially `policy.py`, `handlers/scoped_script.py`, `windows_mutation_sandbox.py`, capability/readiness surfaces, and `handlers/devforge_runtime.py`;
6. keep PR-010 as a separate unmerged overlap reconciliation boundary; do not copy its implementation into PR-011;
7. preserve all Revision-2 F1/F2 security contracts unless current main reality requires an explicitly reviewed adjustment;
8. do not compile an Execution Slice Set until the refreshed Plan is reviewed and approved.

## Related-Task Assessment

### PR-007

PR-007 is no longer an integration blocker. It is completed, merged, and part of canonical `main`. Its `devforge_runtime` provider must now be consumed as repository reality.

### PR-010

PR-010 remains unmerged with S04 pending. Revision 2's implementation-entry reconciliation remains appropriate. This review does not authorize importing unmerged PR-010 code or weakening its canonical repository firewall semantics.

## Round-1 Finding Re-evaluation

- **F1:** Closed in substance by Plan Revision 2.
- **F2:** Closed in substance by Plan Revision 2.
- Their closure is retained as remediation intent, but final approval must evaluate them again after the baseline refresh to ensure no merged-main seam invalidates their implementation assumptions.

## Gate Result

```text
Plan Review: Rejected
Current Gate: plan_review_rejected
Implementation Authorized: false
Execution Slice Set: not compiled
```

No product implementation or implementation Slice is authorized by this review.

Canonical next action:

```text
#开发计划修复 PR-011-scoped-verification-toolchain-dependency-capsule-v1
```
