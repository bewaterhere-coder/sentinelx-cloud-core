---
task_id: PR-029-direct-codex-host-owned-disablement-negative-reachability-v1
title: SentinelX Direct Codex Host-Owned Fail-Closed Disablement and Negative Reachability V1
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
  latest_plan_review: approved_round_2
  latest_rejected_plan_review: rejected_round_1
  latest_reviewed_plan_sha: 300b1adc237dd4220d866ecdeb4047880d203874
  plan_remediation_required: false
  plan_remediation_completed_round: 1
  plan_remediation_disposition: revised_plan_r2_approved_readonly_s01
  proposed_current_plan_slices: [S01]
  executable_slices_admitted: [S01]
  implementation_scope: readonly_S01_evidence_only
  current_slice_state: pending
  product_code_mutation_authorized: false
  service_reload_authorized: false
  local_api_call_authorized: false
  plan_review_blocking_findings: []
  historical_rejected_findings: [R1-F01, R1-F02, R1-F03, R1-F04]
  external_owner_dependency_gate: pending_S01_readback
  implementation_authorized: true
  host_policy_mutation_authorized: false
  direct_codex_execution_authorized: false
  safety_negative_call_authorized: false
  canonical_main_mutation_authorized: false
  next_expected_actor: owner
  s01_run_state: BLOCKED
  s01_latest_run_id: RUN-PR029-S01-001
  s01_blocker: OwnerConsumerAndHostPolicyReadbackEvidenceUnverified
  s01_owner_attestation_required: true
  s01_investigation_verdict: DecisionRequired/Blocked
  s01_completion_verified: false
  canonical_next_action: null
  current_slice: S01
  pending_slices: [S01]
  completed_slices: []
  implementation_execution_complete: false
  material_architecture_decision: owner_selected_host_owned_direct_codex_policy_disable
  baseline_host_security_state: direct_codex_containment_unproven_and_firewall_fail
  requirement_ready_source: docs/reviews/PR-029-direct-codex-host-owned-disablement-negative-reachability-v1-requirement-refinement-r1.md
  authorization:
    mode: legacy_command_scoped
transport:
  type: github-pr
  pr_number: 29
  branch: task/direct-codex-host-owned-disablement-negative-reachability-v1
  base_branch: main
artifacts:
  s01_readonly_evidence: docs/execution/PR-029-direct-codex-host-owned-disablement-negative-reachability-v1-s01-readonly-evidence-20261008.md
  s01_attempt_receipt: docs/execution/PR-029-direct-codex-host-owned-disablement-negative-reachability-v1-s01-attempt-001-receipt.yaml
  s01_run_record: docs/execution/PR-029-direct-codex-host-owned-disablement-negative-reachability-v1-s01-run-001.yaml
  s01_run_ledger: docs/execution/PR-029-direct-codex-host-owned-disablement-negative-reachability-v1-s01-run-001-ledger.yaml
  s01_run_finalization: docs/execution/PR-029-direct-codex-host-owned-disablement-negative-reachability-v1-s01-run-001-finalization.yaml
  s01_blocked_checkpoint: docs/checkpoints/PR-029-direct-codex-host-owned-disablement-negative-reachability-v1-s01-blocked-owner-attestation-20261008.yaml
  plan_r2_slice_set: docs/execution/PR-029-direct-codex-host-owned-disablement-negative-reachability-v1-plan-r2-slices.yaml
  plan_r2_slice_set_blob_sha: 539b385615c1d2c2bb29c0bdd7af60bce45e6f53
  latest_plan_review_approval_receipt: docs/reviews/PR-029-direct-codex-host-owned-disablement-negative-reachability-v1-plan-review-r2-approval-receipt.yaml
  latest_plan_remediation: docs/checkpoints/PR-029-direct-codex-host-owned-disablement-negative-reachability-v1-plan-remediation-r1-20261008.md
  latest_plan_remediation_transition_receipt: docs/reviews/PR-029-direct-codex-host-owned-disablement-negative-reachability-v1-plan-remediation-r1-transition-receipt.yaml
  latest_rejected_plan_review: docs/reviews/PR-029-direct-codex-host-owned-disablement-negative-reachability-v1-plan-review-r1.md
  latest_plan_review: docs/reviews/PR-029-direct-codex-host-owned-disablement-negative-reachability-v1-plan-review-r2.md
  latest_rejected_plan_review_transition_receipt: docs/reviews/PR-029-direct-codex-host-owned-disablement-negative-reachability-v1-plan-review-r1-transition-receipt.yaml
  latest_plan_review_transition_receipt: docs/reviews/PR-029-direct-codex-host-owned-disablement-negative-reachability-v1-plan-review-r2-transition-receipt.yaml
  provisional_intake: docs/intake/direct-codex-host-owned-disablement-negative-reachability-v1.md
  requirement_refinement: docs/reviews/PR-029-direct-codex-host-owned-disablement-negative-reachability-v1-requirement-refinement-r1.md
  requirement_ready_receipt: docs/checkpoints/PR-029-direct-codex-host-owned-disablement-negative-reachability-v1-requirement-ready-r1-receipt.yaml
  plan: docs/plans/PR-029-direct-codex-host-owned-disablement-negative-reachability-v1-plan.md
  current_plan_blob_sha: 300b1adc237dd4220d866ecdeb4047880d203874
  plan_creation_transition_receipt: docs/checkpoints/PR-029-direct-codex-host-owned-disablement-negative-reachability-v1-planning-to-plan-review-r1-receipt.yaml
  upstream_owner_decision: https://github.com/bewaterhere-coder/sentinelx-cloud-core/blob/task/devforge-execution-workspace-materialization-bridge-v1/docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-owner-direct-codex-disablement-decision-r1.md
requirement_readiness:
  result: Ready
  depth: deep
  requirement_revision: 1
  readiness_basis: owner_selection_plus_current_main_policy_and_dispatch_contract
  ui_semantics:
    applicability: NotApplicable
  visual_fidelity:
    applicability: NotApplicable
  material_questions: []
  challenge_completed: true
---

# Requirement R1 — Host-owned Direct Codex Fail-Closed Disablement and Negative Reachability

## 1. Owner decision / scope authority

The Owner explicitly selects **Host-owned policy disablement** for unproven SentinelX-managed `devforge_direct_codex`. This is a **new DevForge Task**, allocated by actual Draft PR #29; it is not a revision/replacement of PR #14. PR-014 Owner Decision R1 @`412509bd7d2db4484ea8b4916984f79eb5052e7e` is the decision source. PR-021 Minimal Runtime Frozen ADR @`36e0290de039336a8e4ce8561c22c731f12e9602` and Capability Disposition Matrix @`05b6906614715e14450a2fd03e0699200e016074` govern the work (separate DevForge Task for provider disablement).

**Current-main baseline:** `2e5c69a112323867ee01783521554c43ebd731be`.
**DevForge contract baseline:** `047df4f1c45ce9099ec112017063751243c78d7b`.
**Current live Host precondition (read-only):** Windows agent `0.24.1.dev791+g5d9286b22` has `devforge_direct_codex.execute_task` projected while `canonical_repository_mutation_firewall_v1.verified=false` with `local_api:direct_codex_containment_unproven`. Sandbox/Audit readiness remain PASS. The direction is selected; **no physical disablement has occurred**.

## 2. Problem and target observable behavior

An unverified Direct Codex process-mutation action remains registered on the Host. A false readiness advertisement cannot prove the action uncallable, and global `local_api` disabling would harm unrelated bounded operations.

After the approved change, **no SentinelX-exposed Direct Codex mutating route may invoke, spawn, or bootstrap the Agent**. The Host policy must deny the builtin and rule out all external/same-name/alias routes. Normal bounded `devforge_runtime` and unrelated `local_api` actions continue to work. Independent local CLI sessions used through guided DevForge are *not* blocked.

## 3. Rules and stable acceptance criteria

- **AC01 Effective Host policy:** Host-authoritative current config selects `direct_codex.enabled: false` (or a stricter provably equivalent policy denial). Read back loaded/effective policy and a digest/identity, not merely edited YAML. No caller-supplied enable/path override; no modifying protected roots or unrelated scopes.
- **AC02 Dispatch closure:** `sentinel_local_api(list)` and `describe(devforge_direct_codex)` show no admitted `execute_task`. Inspect Host route registry and effective `local_apis`; configured external same-name overrides, alternate endpoints, and aliases MUST not provide a mutating bypass. A disabled builtin advertised as unsupported alone is insufficient.
- **AC03 Safe negative invocation:** Following approved policy application and service reload, attempt an **explicitly approved, fail-safe negative probe** on the real `devforge_direct_codex.execute_task` entry. A structurally incomplete no-workload payload may be used only when source and configuration preflight prove it cannot spawn under any result; `endpoint_not_available` / `endpoint_not_configured` / equivalent policy denial must be observed. `invalid_payload` alone is **NOT** proof of disablement. Never submit a valid executable Task payload. Capture a bounded actual refusal and supporting audit evidence.
- **AC04 Zero execution side effects:** Prove no newly spawned Direct Codex child process, no transient workspace creation, no repository mutation, no credential access or publish operation. Combine provider/service telemetry and creation/audit evidence with before/after Host snapshots; mere absence of a process at a later instant does not suffice.
- **AC05 Firewall truth:** After the negative proof, require `canonical_repository_mutation_firewall_v1` effective surface inventory to pass (or report exact *other* blockers rather than claiming pass). Never force/mask `verified` flags; preserve `host_mutation_sandbox_v1`, pre-execution audit, MutationScope, AppContainer/ACL/Job and canonical protected roots.
- **AC06 No collateral disabling:** Global `local_api` stays available for `devforge_runtime` and any other policy-admitted unrelated endpoints; existing generic background task and pending_results behavior is not removed. Legacy `D:\coco` protection remains intact. DevForge's current `direct/codex` execution binding is **not** changed by this Task without its own explicitly reviewed migration.
- **AC07 Reversible, auditable Host change:** Record exact before/after policy (redacted hash/identity), explicit Host-owner authority, deployment/reload/restart logs, negative route test, dispatch/firewall re-read, retained service readiness, and a rollback plan that never re-enables the unverified path. No Receipt, No Completion Claim.
- **AC08 Transport/current source:** Any source or test changes, if truly necessary, are against exact current-main blobs and confined to this PR #29 execution workspace. No direct mutation of `main` or original PR #14. Do not rebase/replay PR #14 older materializer, widen access or substitute a new Task/PR during fixing. Preserve original PR #14 and S01–S07A receipts.

## 4. Source facts / implementation-sensitive risks

- `src/sentinelx_core/policy.py`: `DirectCodexPolicy.enabled` defaults false; `missing_prerequisites` reports `direct_codex_disabled`.
- `src/sentinelx_core/handlers/direct_codex.py`: builtin `available_actions()`, `describe()`, `call()` guard policy admission.
- `src/sentinelx_core/handlers/__init__.py`: single builtin provider map and registry; full `local_api` must remain for `devforge_runtime`.
- `src/sentinelx_core/handlers/local_api.py`: external configured name shadows builtin; denial must cover external routes.
- `src/sentinelx_core/canonical_repository_firewall.py`: still owns independently fail-closed write safety.
- Existing tests include `tests/test_direct_codex_provider.py`, `tests/test_canonical_repository_firewall_readiness.py`.
- `config.example.windows.yaml` already documents `direct_codex.enabled: false`.

Do not mistake source-level `enabled=false` for **effective Host state**. Do not call the Direct Codex endpoint before an approved safe-probe gate or perform any Host change solely because Requirement is Ready.

## 5. Non-goals and exclusion boundaries

No new full workspace materializer, execution-root binding or Source Restore; no long Agent execution/runtime, detached Durable Async or PR-020 expansion; no Direct Codex physical containment engineering; no wholesale source deletion; no disabling global `local_api`; no generic shell/scoped mutation fallback to bypass refusal; no Main/canonical branch mutation, stale PR #14 merge, policy bypass, protected-root carve-out, Credential/ACL/MutationScope expansion, CI pipeline creation, or DevForge routing migration.

## 6. Requirement challenge and counterexamples

- **C1:** Builtin is disabled but `local_apis.devforge_direct_codex` external entry remains callable → FAIL AC02.
- **C2:** `describe` hides action but `call` still dispatches with valid input → FAIL AC02/03.
- **C3:** `call` returns `invalid_payload` for an incomplete payload while route remains otherwise reachable → FAIL AC03.
- **C4:** Service reload silently uses old policy or another Host → FAIL AC01.
- **C5:** No process is running after call but Codex spawned and exited quickly → FAIL AC04.
- **C6:** Firewall PASS obtained by changing effect metadata, dropping an action from inventory or disabling entire `local_api` → FAIL AC05/06.
- **C7:** Physical stop requires changing `D:\coco` protection or the DevForge binding → FAIL / Owner DecisionRequired.

## 7. Gating, plan, and host admission

This Requirement makes the security target testable but **does not itself authorize Host policy edits, service restart/reload or even a negative action call**. Plan R1 must distinguish read-only preflight, independent Host policy mutation authorization, safe negative-call admission, exact receipt verification and rollback. If the configured policy can achieve AC01–AC07 without a product-code delta, **prefer zero source modification**. If no safe negative proof route exists, return `DecisionRequired/Blocked` and request a separately reviewed narrow change rather than loosening permissions. Next Gate: Plan Review.
