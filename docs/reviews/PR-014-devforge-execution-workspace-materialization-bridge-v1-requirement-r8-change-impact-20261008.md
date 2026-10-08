# PR-014 Requirement R8 Change Impact — 2026-10-08

## Evidence
- Canonical product source restored: SentinelX main `5d9286b22f46ae8bdf6d983b6366da0da3f1323e` contains `src/`, `tests/`, `pyproject.toml`.
- Connected Agent: dev791. Sandbox, MutationScope, AppContainer/Job and Audit self-check PASS; Canonical Firewall FAIL with `local_api:direct_codex_containment_unproven`. Independent Host-owned execution root absent from effective locations.
- Historical PR #14 branch remains divergent and not safely mergeable as-is. Current-main `devforge_runtime` rev 1 has no `materialize_workspace`.

## Changes
1. Retire prior "main has no product source" observation as a current blocker while preserving historical record.
2. Keep working scope/Sandbox/Audit unchanged; stop speculative additive-schema replay.
3. Set P0 on real Direct Codex effective-surface security admission; no masking an uncontained endpoint.
4. Require independent Host-owned root **only** for demonstrated short mutation; full checkout/long Agent is DevForge/Guided CLI-owned.
5. Draft a bounded implementation/verification plan with exact source/test candidates and mandatory lossless existing-PR transport gate.

## Revision/Gate
```yaml
task_id: PR-014-devforge-execution-workspace-materialization-bridge-v1
requirement_before: 7
requirement_after: 8
plan_before: 12
plan_after: 13
historical_slices_preserved: [S01, S02, S03A, S04A, S05A, S06A]
historical_candidate_preserved: 45dc99d15a23c499b4c1500fab60ed5e76475aeb
stage: plan_review
plan_approved: false
implementation_authorized: false
product_mutation: false
host_mutation: false
canonical_main_mutation: false
history_rewrite: false
next: "#开发评审 PR-014-devforge-execution-workspace-materialization-bridge-v1"
```
