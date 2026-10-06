# PR-011 — Scoped Verification Toolchain & Dependency Capsule V1 — Acceptance R2

## Decision

```yaml
task_id: PR-011-scoped-verification-toolchain-dependency-capsule-v1
requirement_revision: 2
plan_revision: 6
acceptance_revision: 2
result: Approved
canonical_transport: github-pr
pr_number: 11
canonical_branch: task/scoped-verification-toolchain-dependency-capsule-v1
evaluated_head_before_acceptance_artifacts: bff1edb8511d8ba47ccf476cd52b5cc631f875dd
verified_acceptance_repair_head: e02ae617860d8181ec9946ecae41c9ac81d3d2dc
verified_runtime_candidate: 9948eb4d481ca773b2ea14cf2571e0cf6342f213
canonical_main: e7064c9bf4fcd15bdb6f5a2678414210c01d1c00
current_stage: accepted
gate_transition: acceptance_to_accepted
acceptance_approved: true
completion_verified: false
macos_evidence_used: false
```

**PR-011 Acceptance R2: Approved.**

Requirement Revision 2 is satisfied on the canonical PR transport. Acceptance enters the `accepted` boundary only. It does not merge PR #11, mark the Task done, or perform completion finalization.

Per the operator instruction for this Acceptance, macOS verification is not part of the decision and no macOS result is used as acceptance evidence.

## Runtime / Transport Consistency

PASS.

- DevForge source of truth: `bewaterhere-coder/DevForge main@af6cfb5153b5c982d9039e4c9f74fe44940ddbfb`.
- Acceptance Contract: `contracts/development/acceptance-contract.md` v1.5, blob `1c5e96a20d665e68b1f68e18b7d294945e501ec2`.
- Latest observed DevForge release: `v2.67.0`.
- Canonical repository: `bewaterhere-coder/sentinelx-cloud-core`.
- Canonical PR: #11, branch `task/scoped-verification-toolchain-dependency-capsule-v1`, base `main`.
- Evaluated head before Acceptance persistence: `bff1edb8511d8ba47ccf476cd52b5cc631f875dd`.
- Canonical main: `e7064c9bf4fcd15bdb6f5a2678414210c01d1c00`.
- PR was open, draft and GitHub-reported mergeable.
- No TransportDrift is present.

The Acceptance R1 repair head is `e02ae617860d8181ec9946ecae41c9ac81d3d2dc`. The evaluated head is one later evidence/state commit ahead of that repair head; compare readback shows only the Requirement state, repair checkpoint and repair transition receipt changed. No runtime code, workflow, test or security semantics changed after the verified repair head.

## Requirement Change Guard

PASS.

- Requirement Revision 2 is current.
- Plan Revision 6 is current and Approved.
- S01 remains preserved/no-replay.
- S02R, S03R, S04 and S05 are completed under the R6 repair sequence.
- Acceptance R1's only finding, `AC11RelevantWindowsCIRegression`, was classified `repair_local`.
- The repair impact analysis confirms the fix changes only hosted CI orchestration; runtime, test semantics, AppContainer/Job containment and the mandatory real-Host gate are unchanged.
- No stale R1 failure evidence is reused as positive proof.
- PR-007, PR-010 and PR-012 canonical authority seams remain reused rather than duplicated.
- Downstream ChatGPTControlShell PR-015 evidence remains non-gating.

## Fresh Verification After Acceptance R1 Repair

PASS.

Exact repair head: `e02ae617860d8181ec9946ecae41c9ac81d3d2dc`.

Windows / repository verification used for this decision:

- `pr011-s04-verification` run `37467396706`: success, **53 passed**, 1 warning;
- generic `ci` run `37467396768`: success;
- `pr011-s01-verification` run `37467396717`: success;
- `pr011-s02-verification` run `37467396891`: success;
- `pr011-s03-verification` run `37467396792`: success;
- `pr011-s03-native-cwd-diagnostic` run `37467396695`: success;
- `pr011-s05-verification` run `37467396747`: success;
- PR-010 regression runs S01-S05: all success.

No macOS run is used.

The mandatory physical Host evidence is retained because the repair did not alter runtime/test/security semantics:

- S04 SYSTEM physical gate: **35 passed, 0 failed**;
- S04 focused post-readiness tamper gate: passed;
- S05 live readiness: passed;
- S05 live profiled `execute_scoped`: passed;
- S05 terminal scope readback: passed.

## Live Agent Evidence

PASS.

The exact S05 runtime candidate remains active as:

```text
0.24.1.dev403+g9948eb4d4
```

Fresh live readback during Acceptance confirms:

- `devforge_runtime.describe` still exposes the bounded `verification` selector;
- explicit `execution_profile=scoped_mutation` remains the contract;
- the temporary Node/npm profile has been removed after proof, so `host_runtime.scoped_verification_node_npm_v1.available=false` now correctly reports `Node/npm verification profile is not configured`.

This post-restore unavailable state is expected and proves configuration compatibility: base scoped mutation remains available without a verification profile. The required positive profiled live execution is preserved in the S05 completion receipt from the exact active runtime candidate.

## Acceptance Matrix

- **AC1 — PASS:** provider-owned logical Node/npm profile resolution, source/capsule integrity binding and caller path-authority rejection are covered by S01 plus S05 schema/admission proof.
- **AC2 — PASS:** S02R limits transient toolchain authority to exact-root read/execute only; S03R physically proves Node/npm execution with no write escape.
- **AC3 — PASS:** S03R real-Host evidence proves deterministic offline npm operation and package-script execution.
- **AC4 — PASS:** source/capsule/profile/lock/toolchain mismatch and tamper cases fail closed; S04 proves post-readiness toolchain drift is rejected before successful execution.
- **AC5 — PASS:** DNS/HTTP/network fallback remains unavailable and credential/proxy authority is absent.
- **AC6 — PASS:** descendants remain inside the no-breakaway Job; exact-workspace mutation authority and protected/canonical boundaries remain intact; terminal readback shows no residual authority.
- **AC7 — PASS:** unprofiled scoped Python/base sandbox behavior remains compatible and verification-profile absence does not disable base readiness.
- **AC8 — PASS:** Node/npm readiness is separately gated and was physically proven true only with a valid profile/self-check, while current post-restore absence correctly returns false.
- **AC9 — PASS:** live Agent-owned `describe` exposes the bounded selector and live profiled `execute_scoped` returned profile/toolchain/capsule/offline/audit/terminal evidence without Hub modification.
- **AC10 — PASS:** repository coverage includes profile/policy parsing, overlap validation, capsule integrity, environment sanitization, AppContainer ACL/materialization, offline execution, readiness, local-api integration and negative security cases.
- **AC11 — PASS:** the repaired relevant Windows workflow is green, generic CI and affected regression workflows are green, and the mandatory real Windows Host physical gate is green. No canonical checkout is used as a mutation workspace.
- **AC12 — NON-GATING:** downstream ChatGPTControlShell PR-015 evidence is not required for PR-011 Acceptance or Completion.

## Safety / Scope

PASS.

- No Hub modification.
- No permission or allowlist widening.
- No `operator_unrestricted`.
- No generic shell/exec fallback.
- No second executor, scope store, sandbox or audit path.
- No canonical-main or canonical-checkout mutation by Acceptance.
- Temporary S05 verification configuration was restored and the temporary provider tree was deleted.
- The canonical checkout remains `main + clean`.

## Integration Boundary

Acceptance approves the implementation and evidence only. PR #11 is not claimed integrated.

Merge/integration, current-main reconciliation, final integration verification and the Task `done` transition belong exclusively to:

`#开发完成 PR-011-scoped-verification-toolchain-dependency-capsule-v1`

## Acceptance Result

```text
Acceptance Approved: true
Completion Verified: false
Result: Approved
Gate Transition: acceptance -> accepted
Current Stage: accepted
```

Canonical next action:

`#开发完成 PR-011-scoped-verification-toolchain-dependency-capsule-v1`
