# PR-014 Plan R13 — Firewall Safety Repair & Minimal Execution Binding

```yaml
task_id: PR-014-devforge-execution-workspace-materialization-bridge-v1
project_id: sentinelx-cloud-core
requirement_revision: 8
plan_revision: 13
stage: ready_for_plan_review
plan_approved: false
implementation_authorized: false
transport:
  repository: bewaterhere-coder/sentinelx-cloud-core
  pr_number: 14
  branch: task/devforge-execution-workspace-materialization-bridge-v1
  base: main
canonical_source_commit: 5d9286b22f46ae8bdf6d983b6366da0da3f1323e
installed_host_version: 0.24.1.dev791+g5d9286b22
historical_slices: [S01, S02, S03A, S04A, S05A, S06A]
replay_authorized: false
```

## 1. Scope, excluded goals and verified baseline

PR-021 permits **only minimal isolated security substrate for bounded short Host mutations**, not long CodeBuddy/Codex Agent lifecycle, full Git checkout creation, source capsule/bootstrap/handoff or a generic `materialize_workspace` endpoint. Product source is available again on current main. Sandbox/MutationScope/Audit already verify PASS; do not repeat their historical repairs.

P0 is the **effective canonical repository firewall** (`local_api:direct_codex_containment_unproven`) while independent short-mutation execution root binding remains unverified. A higher Agent version does not constitute successful feature acceptance.

## 2. Proposed implementation slices — pending Plan Review, NOT authorized

**S07 — Focused effective-surface Firewall closure.** Trace `devforge_direct_codex` reachability and registration under effective Host policy, then select the smallest proven fail-closed disposition: (a) actual policy-owned disablement so unproven action cannot be called, or (b) physical containment proof for any endpoint intentionally remaining reachable. A code change is permitted only after the exact impact/transport review demonstrates necessity; no fake readiness / skipped inventory checks. Current-main candidate sources: `src/sentinelx_core/handlers/direct_codex.py`, `src/sentinelx_core/handlers/local_api.py`, `src/sentinelx_core/operation_registry.py`, `src/sentinelx_core/policy.py` and exact registration sites. Focused tests: `tests/test_canonical_repository_firewall_readiness.py`, `tests/test_canonical_repository_firewall_incident_regression.py`, `tests/test_direct_codex_provider.py`, `tests/test_local_api.py`, `tests/test_policy.py`. Never silently disable a previously active user workflow or modify live Host policy without separate explicit Host change authorization. Preserve current short `devforge_runtime` and sandbox controls.

**S08 — Conditional Host-owned execution placement.** Resolve whether a demonstrated short mutation truly needs an additional independent execution-root binding. Read effective source / execution authority separately; require strict non-overlap with protected `D:\\coco`, no carve-out or caller-selectable paths. `D:\\SentinelX\\devforge-workspaces` is a candidate only, not an admitted root. If an independent root is required, design exact Host-owned config schema, placement and audit/MutationScope sealing; Host config deployment is separately gated. If not required, record `NoAdditionalProductDeltaNeededForPlacement`; keep full workspaces and long Agents in DevForge / guided CLI.

**S09 — Regression and physical acceptance.** Verify Windows Sandbox/AppContainer/ACL/Job and audit START-before-resume stay PASS; the uncontained Direct Codex endpoint is provably unreachable or physically contained; canonical firewall `available=true, verified=true` is truthful across every exposed mutating surface; no `D:\\coco` path mutation; sealed short scope lifecycle and receipts for any admitted short operation. Observe separate Node/npm readiness without mislabeling it. Require exact deployed candidate provenance, Host readback, failure rollback and source/PR integration receipts before any completion claim.

## 3. Blocking transport gate — prior to S07 product mutation

The original PR #14 branch contains stale product code and is not a safe merge input. Before any S07 product edit, a separately reviewed same-Task PR #14 **no-loss transport normalization** must bind the proposed delta to current `main@5d9286b22` blobs. Compare proposed final Git tree against current main; abort if unintended files disappear, stale product blobs overwrite main, or historical S01/S02 mutation is replayed. No blind rebase, cherry-pick, force-push, replacement PR, or canonical-main working-tree mutation. If exact normalization cannot be proven, return `TransportBlocked` without touching product code.

Plan Review approval alone does not authorize Host configuration edits, live process execution, uncontained Agent invocation or unsafe source transport. Those mutations require explicit gated authority and receipts. A plan may be Approved conditionally for safety work only when these blockers have a concrete, independently verified admission path; otherwise Rejected/Changes Requested is correct.

## 4. Review matrix

Plan Review R13 must decide:
- Current-main source ownership and exact S07 candidate-file/test set;
- Direct Codex containment/disablement negative proof with complete effective Firewall coverage;
- S08 real short-consumer necessity, independent Host-owned execution binding and unchanged `D:\\coco` protection;
- PR #14 preservation and lossless transport strategy without old code replay;
- S09 tests, physical Host readback, rollback and `No Receipt, No Completion`.

Historical Plan R12/S06A and prior S01–S05A receipts remain evidence-only. No new Slice Set is compiled or executed by this document.

**Next Gate:** `#开发评审 PR-014-devforge-execution-workspace-materialization-bridge-v1`.
