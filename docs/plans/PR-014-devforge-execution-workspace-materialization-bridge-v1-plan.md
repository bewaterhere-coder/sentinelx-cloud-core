# PR-014 Plan R14 — Read-only Security/Transport Admission Decision

```yaml
task_id: PR-014-devforge-execution-workspace-materialization-bridge-v1
project_id: sentinelx-cloud-core
requirement_revision: 8
plan_revision: 14
stage: ready_for_plan_review
plan_approved: false
implementation_authorized: false
transport:
  repository: bewaterhere-coder/sentinelx-cloud-core
  pr_number: 14
  branch: task/devforge-execution-workspace-materialization-bridge-v1
  base: main
historical_slices: [S01, S02, S03A, S04A, S05A, S06A]
historical_replay: forbidden
```

## R13 findings addressed

R13-F01–F04 are remediation inputs. R14 removes all proposed S07/S08/S09 product and Host mutation slices. It admits at most **one evidence-only slice S07A**, with deterministic decision/negative outcomes. Approval of R14 must never imply acceptance of a product implementation.

## S07A — Read-only current-main source, transport, firewall/placement admission

```yaml
slice_id: S07A
depends_on: []
allowed_effects:
  - github_current_main_and_existing_pr14_read
  - sentinelx_structured_read_only_inspection
  - task_scoped_documentation_and_receipt_write_on_existing_pr14_branch
forbidden_effects:
  - product_code_mutation
  - host_configuration_or_runtime_mutation
  - canonical_main_mutation
  - direct_codex_invoke
  - scoped_execution
  - provision_scope
  - materialize_workspace
  - source_restore
  - rebase
  - cherry_pick
  - force_push
  - historical_slice_replay
outputs:
  - current_main_exact_owned_files_test_blobs_or_unverified
  - no_loss_pr14_transport_mechanics_with_preconditions_abort_checks_or_TransportBlocked
  - direct_codex_reachable_surface_negative_proof_or_DecisionRequired
  - selected_containment_or_policy_disablement_path_with_owner_authority_or_DecisionRequired
  - independent_root_short_consumer_necessity_or_NoAdditionalProductDeltaNeededForPlacement
  - final_decision_checkpoint_and_readback_receipt
checkpoint_required: true
```

### 1. Source/transport admission (R13-F01)

Read fresh GitHub main SHA, actual implementation paths, immutable blob IDs, exact candidate tests, original PR #14 branch and compare metadata. Record a **proposed** lossless, same-PR-only transport process with preflight and postcondition: Git tree prospective delta must contain only the explicitly reviewed current-main-backed paths, preserve every unrelated current-main file/blob, preserve historical Task evidence and PR #14 identity, and fail closed on concurrent main or PR head drift. No prospective implementation commit or branch rewrite in S07A. If the connector cannot prove an executable lossless strategy without stale blob replacement, mark `TransportBlocked`; do not attempt a rebase, cherry-pick, force push or new PR.

### 2. Direct Codex authority decision (R13-F02)

Use structured read-only Host capability, `devforge_direct_codex` descriptor, source registrations, effective Host policy and canonical firewall diagnostics. Identify mutating reachability and classify two possibilities: **policy-owned fail-closed disablement** with a negative reachability test, or **verified physical containment** with AppContainer/ACL/Job/audit/canonical firewall evidence. This is a decision test, not an implementation option list. Select one only if owner authority, practical negative test and scope are proven; otherwise emit `DecisionRequired/Blocked`. Never hide endpoint from status alone, widen allowlists, invoke the endpoint, or claim coverage while reachable.

### 3. Independent execution root decision (R13-F03)

Identify an actual bounded synchronous `execute_scoped` consumer and its isolation/placement requirement, read effective Host-owned source/execution bindings, protected `D:\coco` and candidate `D:\SentinelX\devforge-workspaces` only as a **candidate**, not authority. If no additional placement consumer/gap exists, record `NoAdditionalProductDeltaNeededForPlacement`. If required, record strict non-overlap, sealed MutationScope, audit START, AppContainer/Job and separate Host deployment admission prerequisites; no path carve-out, no caller-controlled root.

### 4. Candidate verification disposition (R13-F04)

No executable S09 or Host deployment admitted. Produce decision `NoAdditionalProductDeltaNeeded`, `NarrowSecurityRepairCandidateRequiresSeparateReviewedPlan`, `TransportBlocked`, or `DecisionRequired/Blocked`. Positive decision only permits a new **exact-source, exact-test Plan Review**, including physical Host proof, rollback, and readback receipts. Preserve installed dev791 Sandbox/Audit PASS as prior evidence; do not replay MutationScope remediation or historical S01–S06A. Main must remain clean and untouched.

## Review Gate

Reviewer may approve exactly S07A read-only, not product or Host implementation. This plan does not self-approve and does not compile a pending Slice Set before Review. Next: `#开发评审 PR-014-devforge-execution-workspace-materialization-bridge-v1`.
