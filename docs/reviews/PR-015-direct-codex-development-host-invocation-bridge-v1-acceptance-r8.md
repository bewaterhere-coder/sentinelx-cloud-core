# PR-015 — Direct Codex Development Host Invocation Bridge V1 — Acceptance R8

## Decision

```yaml
task_id: PR-015-direct-codex-development-host-invocation-bridge-v1
requirement_revision: 2
plan_revision: 6
acceptance_revision: 8
result: Approved
canonical_transport: github-pr
pr_number: 15
canonical_branch: task/direct-codex-development-host-invocation-bridge-v1
evaluated_head_before_acceptance_artifacts: 0500e457495a148573fcc2e184d6c7dca8058201
verified_product_candidate: 7adfa7a74c437ccc29cdcd7078373c6e8d224904
stage_before_transition: acceptance
target_stage: accepted
acceptance_approved_after_transition: true
completion_verified: false
```

**PR-015 Acceptance R8: Approved.**

The exact repaired product candidate `7adfa7a74c437ccc29cdcd7078373c6e8d224904`
satisfies Requirement Revision 2 / Approved Plan Revision 6. All product changes
after the candidate are absent: subsequent PR #15 commits contain only DevForge
control artifacts, so the tested/live-activated product bytes remain exact.

The previous R5 containment-lifecycle and R7 Windows workspace ACL handoff findings
are both closed by durable fixing receipts and independent live verification.

## Transport Consistency

- canonical repository: `bewaterhere-coder/sentinelx-cloud-core`;
- canonical PR: `#15`;
- canonical branch: `task/direct-codex-development-host-invocation-bridge-v1`;
- repair candidate is on the canonical branch;
- no replacement branch or PR was created;
- no transport migration was used;
- commits after the repair candidate are control-plane artifacts only.

Result: **PASS**.

## Acceptance Matrix

- **AC1 — PASS.** `local_api.describe devforge_direct_codex` exposes one closed
  `execute_task` schema containing only repository, lineage, development and
  canonical transport structures. No arbitrary executable/shell/cwd/env/prompt
  field is projected.

- **AC2 — PASS.** On exact candidate activation readiness initially returned
  `direct_codex_containment_unproven`. After the provider-owned physical proof
  using the selected real Codex `workspace-write` mode, readiness became
  `available=true / verified=true`. Missing proof therefore fails closed.

- **AC3 — PASS.** Real `gpt-5.6-sol` Codex executed non-interactively in the
  provider-derived Windows workspace under the active interactive user context.
  The real session executed commands and modified the authorized fixture without
  SentinelX projecting credential material.

- **AC4 — PASS.** The real Codex cwd was the derived
  `D:\SentinelX\devforge-workspaces\...` workspace. Independent read-back of
  `D:\coco\repos\bewaterhere-coder\sentinelx-cloud-core` remained
  `main + clean`, ahead/behind `0/0`.

- **AC5 — PASS.** Verified readiness now includes the selected real Codex
  workspace-write setup and the protected-sibling negative proof. The ACL handoff
  implementation targets only the exact execution workspace; parent/sibling paths
  are not granted, reparse points are not followed, and protected sibling write
  authority remains denied.

- **AC6 — PASS.** Exact remote-head mismatch was exercised repeatedly, including
  the final PR-013 admission-only proof. The provider returned
  `direct_codex_remote_head_mismatch` before implementation mutation.

- **AC7 — PASS.** The real Codex fixture received exact Requirement/Plan plus
  Task/Run/Attempt/Slice and PR/branch/expected-head transport identity. The action
  schema provides no replacement-transport authority.

- **AC8 — PASS.** Verification fixture `bewaterhere-coder/devforge-harness#230`
  produced one eligible change through real Codex. SentinelX then created provider
  commit `900e29a349a8e65d54ab1cad45507c88641d59d3` with parent
  `f19dbe1ef072596129884e05797936632f0fb850`, author/committer
  `SentinelX Direct Codex`, ordinary fast-forward publication, and independent
  remote read-back. The only remote change was
  `fixtures/pr015-ac12/probe.txt: before -> after-direct-codex-live`.

- **AC9 — PASS.** Wrong remote SHA, unsupported user model during R7 diagnostics,
  and the historical ACL setup failure all failed closed without manufactured
  success or unintended remote mutation. Current receipt validation/persistence
  tests remain passing.

- **AC10 — PASS.** Candidate GitHub workflow `ci` run `37635132767` succeeded.
  All observed PR010 S01-S05, PR011 S01-S05/native-cwd and macOS regression
  workflows on the exact candidate completed successfully.

- **AC11 — PASS.** No generic `exec`, `operator_unrestricted`, caller-controlled
  run-as-user/ACL API, allowlist widening, project-binding mutation, Host-policy
  mutation, permission-scope expansion or Hub mutation was introduced.

- **AC12 — PASS.** Exact candidate
  `0.24.1.dev530+g7adfa7a74` completed the real persisted direct/Codex fixture
  end to end. For PR-013, current Task state remains
  `implementation / S03 pending`, project binding remains `direct/codex`,
  and DevForge routing gives the explicit project binding authority when no Task
  override exists. A live `devforge_direct_codex.execute_task` probe using the
  exact PR-013 Task/Requirement/Plan/S03 identity reached the canonical remote
  head check and returned the deliberately induced
  `direct_codex_remote_head_mismatch`. Independent read-back confirmed PR #13
  head remained `4a3f8e3504b65d1dc222ecb9421ffa16cd96c76d`, S03 remained
  pending and no PR-013 mutation occurred. This proves direct/Codex provider
  admission without executing S03 or changing Task identity/project binding.

## Requirement / Risk Review

- Requirement R2 remains unchanged.
- Approved Plan R6 remains unchanged.
- UX/visual applicability is NotApplicable.
- No unresolved blocking finding remains.
- No material Requirement/product/architecture decision is outstanding.
- Production Hub remains immutable.
- Completion/finalization has not been executed.

## Disposition

```yaml
acceptance:
  decision: Approved
  acceptance_approved: true
  completion_verified: false
  transition: acceptance -> accepted
  canonical_next_command: "#开发完成 PR-015-direct-codex-development-host-invocation-bridge-v1"
```
