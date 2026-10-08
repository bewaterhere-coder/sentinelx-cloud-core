---
task_id: PR-026-scoped-powershell-appcontainer-initialization-recovery-v1
title: SentinelX Scoped PowerShell AppContainer Initialization Recovery V1
project_id: sentinelx-cloud-core
repository: bewaterhere-coder/sentinelx-cloud-core
requirement_revision: 1
development:
  stage: implementation
  gates:
    requirement_ready: true
    plan_approved: true
    acceptance_approved: false
    completion_verified: false
  plan_revision: 2
  implementation_authorized: true
  implementation_scope: s02_session0_discrimination_diagnostic_only
  owner_authorization_gate: [service_overlay, service_restart, production_probe]
  repair_authority: none
  next_expected_actor: implementer
  blocking_findings: []
  current_slice: S02
  completed_slices: [S01]
  authorization:
    mode: legacy_command_scoped
transport:
  type: github-pr
  pr_number: 26
  branch: task/scoped-powershell-appcontainer-initialization-recovery-v1
  base_branch: main
artifacts:
  plan: docs/plans/PR-026-scoped-powershell-appcontainer-initialization-recovery-v1-plan.md
  bootstrap: docs/checkpoints/scoped-powershell-appcontainer-initialization-recovery-v1-provisional-bootstrap.md
related_tasks:
  architecture_authority: PR-021-minimal-runtime-complexity-reduction-boundary-v1
  historical_reference_only: PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1
requirement_readiness:
  result: Ready
  ui_semantics:
    applicability: NotApplicable
  visual_fidelity:
    applicability: NotApplicable
  root_cause_evidence:
    state: pending_raw_windows_host_evidence
  implementation_fix:
    state: not_authorized_until_evidence
---

# Requirement R1 — Scoped PowerShell AppContainer Initialization Recovery

## Problem and live observation

On an operational real Windows 11 Host running SentinelX `0.24.1.dev791+g5d9286b22`, the built-in `devforge_runtime` provider's `provision_scope` succeeds. `execute_scoped` with `execution_profile=scoped_mutation` and `interpreter=powershell` fails:

```text
HostMutationSandboxUnavailable
powershell could not initialize inside the required AppContainer
```

Current code in `src/sentinelx_core/handlers/scoped_script.py` raises this result when `returncode.txt` does not exist after the contained process exits. It does not include the raw Windows child process exit status in this failure branch, although `winspawn.py` has `exit_code` support. The error only establishes that the trusted scoped PowerShell runner did not produce its result marker; **DLL, CLR/PowerShell, Session-0, AppContainer ACL, policy and sandbox profile are unproven hypotheses**.

### Canonical baseline, observed 2026-10-08

- SentinelX GitHub `main@8d2bafba87b529fb458faaa7fbdce39fe225361f`.
- Installed Host version: `0.24.1.dev791+g5d9286b22` and connected Host Windows 11 / AMD64.
- Installed commit `5d9286b22f46ae8bdf6d983b6366da0da3f1323e` and current `main` have matching Git blobs for `scoped_script.py`, `windows_mutation_sandbox.py`, `devforge_runtime.py`, and `winspawn.py`.
- Host baseline sandbox self-check reports verified AppContainer/ACL/Job/audit/scope; this is **not** a successful PowerShell `execute_scoped` observation.
- Host policy rejects diagnostic unprofiled script execution with `execution_profile_required`; no unrestricted PowerShell fallback was used.
- PR-021 is completed and freezes the Minimal Runtime Boundary; PR-018 is completed and provides **historical**, not automatic, Session-0/Unity precedent.

## Goal

Restore a short, bounded, auditable `devforge_runtime.execute_scoped` PowerShell execution inside the original required Windows AppContainer with no security weakening. Diagnose the real Windows child startup outcome before selecting any compatibility change.

## Requirements

- **R1 — Evidence-first diagnosis.** Read existing child process status/exit code, process command/path, START/SPAWN/FINISH audit lineage, spawn/Job/AppContainer evidence, terminal scope state, Windows event/security logs where available, interpreter version/path, and environment/profile/ACL facts before modifying compatibility behavior. Record inaccessible evidence as Unknown, not PASS.
- **R2 — Fail-closed observability repair.** If raw code is not durably recorded, admit only narrowly scoped diagnostic instrumentation: record raw unsigned Windows exit code and hexadecimal NTSTATUS representation, distinguish process-creation failure from successful spawn and pre-runner failure, bind to the exact operation/scope/Job identity and current durable audit; never persist secrets, raw environment values, broad paths, or add execution authority.
- **R3 — Root-cause classification.** Distinguish at least (A) interpreter path/image/bitness or PowerShell runtime startup; (B) Session-0 window station/desktop rights; (C) AppContainer filesystem/registry/OS object ACL; (D) sandbox profile/HOME/APPDATA initialization; (E) CLR/runtime dependency or DLL loading; (F) spawn/Job/timeout/audit sequencing. For each candidate record positive discriminator, negative discriminator and confidence; do not infer a cause solely from `returncode.txt` absence.
- **R4 — Minimal compatible correction.** Change only a fault class proven with an exact Windows Host A/B or equivalent reproducible discrimination. Limit authority and implementation to the affected interpreter/process scope. Any material uncertainty or different root cause stops for Plan revision/review rather than expanding permissions speculatively.
- **R5 — Minimal Runtime compatibility.** No long-running Agent orchestration, generic process supervisor, timeout extension, async lifecycle expansion, or DevForge workflow engine in SentinelX. A short PowerShell scoped probe only.
- **R6 — Strong isolation.** Preserve `AppContainer`, suspended spawn, pre-resume durable SPAWN audit, no-breakaway Job, `MutationScope`, exact workspace/runtime authority, canonical mutation firewall, and fail-closed scope terminalization. No interactive shell or Job breakaway.
- **R7 — Non-expanding permission boundary.** No `operator_unrestricted` or unrestricted PowerShell fallback; no broad/global ACL relaxations; no `D:\coco` protected-root expansion, carve-out or allowlist exception; no caller-controlled executable/masks/session-object rights; no default elevation.
- **R8 — Predecessor protection.** Do not re-implement, revert, or replay PR-018 Unity DLL/Session-0 fix. Reuse its regression contracts and the existing generic Session-0 cleanup/closure behavior; preserve PR-017 scoped runtime-root cleanup and PR-011 verification handshake.
- **R9 — Real Windows Host outcome.** Verify actual `provision_scope` and `execute_scoped` via the model-facing `devforge_runtime` action against an admitted noncanonical execution root. `Write-Output 'SCOPED_PS_OK'` must yield exact output and exit 0; source-level unit tests/mocks are supplementary only.
- **R10 — Audit and cleanup.** Verify START -> SPAWN-before-resume -> FINISH ordering; process contained in Job/AppContainer; scope terminalized, Job active count zero, temporary grants revoked and no residual authority. Read back audit operation ID/child exit status/closure/terminal state and canonical repo clean after test.
- **R11 — Scope and transport.** Implement only in this PR #26 branch after formal Plan Review. Canonical source checkout `main + clean`; product mutation only in DevForge-approved isolated execution workspace. No new branch/PR for same Task, no source mutation before approved gate.

## Non-goals

- No Unity process changes or `PR-018` rework.
- No general solution for arbitrary Windows GUI/interactive applications.
- No weakening protected filesystem roots, Host service account, sandbox, Job, policy, or audit.
- No guessing a compatibility fix from the generic error string.
- No production deployment or installed SentinelX update without a separate, explicit verified activation step.

## Acceptance Criteria

1. Canonical `main`, PR-021 and installed Host version/critical source blobs read back.
2. Existing audit/Windows child error evidence captured, or explicit evidence-unavailability receipt explaining the required diagnostic instrumentation.
3. Raw process exit code (integer + hex when available), creation/spawn phase, runner-marker presence, evidence lineage and applicable Windows events durably recorded.
4. Competing fault classes tested/disconfirmed; root-cause verdict backed by real Windows evidence before compatibility mutation.
5. Any correction is the smallest demonstrated change; no PR-018 Unity reimplementation.
6. `devforge_runtime.provision_scope` PASS with exact repository/lineage binding.
7. `devforge_runtime.execute_scoped(execution_profile=scoped_mutation,interpreter=powershell)` PASS with `Write-Output 'SCOPED_PS_OK'`, matching output and `returncode=0`.
8. AppContainer identity and suspended spawn / no-breakaway Job containment PASS.
9. Scope terminal state and active Job count zero; runtime/Session-0 ACL grants removed with durable closure evidence.
10. START/SPAWN/FINISH/audit readback references exact operation and both successful/failure terminalization paths.
11. Canonical checkout `main + clean`; no canonical repo/product mutation outside this Task's approved isolated workspace; `D:\coco` protected-root unchanged.
12. Unit/regression checks cover exact failure and success without unrestricted fallback, no audit or security weakening; include PR-011, PR-017 and PR-018 relevant regressions.
13. Formal DevForge acceptance receipt includes real Host evidence, Git head/PR, code diff, audit, terminal state and repository readback. **No receipt, no completion claim.**

## Requirement Readiness

The observable target and forbidden security changes are unambiguous. Unknown startup root cause is **an explicit diagnostic input**, not implementation authority. Any compatibility fix remains gated on verified S01 evidence and approved Plan scope. R1 is Ready for planning/review only; implementation is not authorized.
