---
task_id: PR-012-execute-scoped-explicit-execution-profile-v1
title: SentinelX execute_scoped Explicit Execution Profile Schema & End-to-End Propagation V1
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
  plan_revision: 3
  implementation_authorized: true
  next_expected_actor: implementer
  current_slice: S01
  current_slice_state: pending
  authorization:
    mode: legacy_command_scoped
artifacts:
  review_correction: docs/reviews/PR-012-execute-scoped-explicit-execution-profile-v1-review-correction-r3.md
  latest_plan_review: docs/reviews/PR-012-execute-scoped-explicit-execution-profile-v1-plan-review-r3.md
  latest_plan_review_transition_receipt: docs/reviews/PR-012-execute-scoped-explicit-execution-profile-v1-plan-review-r3-transition-receipt.yaml
  prior_plan_review: docs/reviews/PR-012-execute-scoped-explicit-execution-profile-v1-plan-review-r2.md
  plan: docs/plans/PR-012-execute-scoped-explicit-execution-profile-v1-plan.md
  execution_slice_set: docs/execution/PR-012-execute-scoped-explicit-execution-profile-v1-slices.yaml
transport:
  type: github-pr
  pr_number: 12
  branch: task/execute-scoped-explicit-execution-profile-v1
requirement_readiness:
  result: Ready
  ui_semantics:
    applicability: NotApplicable
---

# Requirement

## Problem and evidence
At canonical main dbf4bfc9, src/sentinelx_core/handlers/devforge_runtime.py excludes execution_profile from allowed/required fields and action schema. The adapter creates an internal payload with a hard-coded scoped_mutation value. Live local_api.describe likewise omits the field and forbids additional properties. DevForge therefore cannot explicitly select its required execution profile.

## Goal
Allow the model-facing local_api execute_scoped action to explicitly carry execution_profile=scoped_mutation through existing validation and the canonical profiled executor, without creating a second executor or weakening scope/audit/firewall authority.

## Scope
- Required execution_profile property in the execute_scoped action schema and advertised parameter list.
- Explicit validation on the actual adapter invocation, including direct builtin calls.
- Propagation of the validated caller value to the existing profiled_script_handler.
- Existing local_api routing integration and regression tests.
- Describe/call compatibility documentation and live activation acceptance instructions.

## Non-goals
No general script_run MCP redesign, production Hub deployment, dynamic tool registry implementation, new profile, scope minting mechanism, permission expansion, firewall change, or unrestricted fallback. PR-008/009 remain separate. No modification of canonical checkout.

## Behavior
B1: Describe advertises execution_profile as required, with only scoped_mutation supported.
B2: A valid explicit scoped_mutation request preserves existing repository/lineage/scope validation and invokes the existing executor with that validated profile.
B3: Missing profile is rejected before executor invocation; do not synthesize a default.
B4: Other strings, null and non-string values are rejected before executor invocation.
B5: The downstream result must report scoped_mutation; unexpected results remain failures.
B6: Policy-disabled execution and scope/audit/firewall failures retain existing fail-closed behavior.
B7: Old clients omitting the newly required field receive an explicit validation error. The interface change must be documented; no silent compatibility default.

## Acceptance
AC1: Actual local_api.describe schema and parameter projection include the required field and exact allowed value.
AC2: Integration tests route a valid request through local_api to a recording existing executor and verify the explicit value arrives.
AC3: Missing/invalid/non-string values result in zero executor calls.
AC4: Existing scope ownership, disabled-operation, lineage and unexpected-result regressions pass.
AC5: Targeted tests and appropriate repository checks pass on the exact task transport.
AC6: End-to-end live activation is independently verified after approved installation: current Agent describe includes the field, a harmless scoped marker executes with provider-owned scope, and audit plus scope terminalization are read back. Unit mocks alone do not satisfy AC6.

## Refinement evidence
Normal: explicit scoped_mutation plus valid bindings reaches the existing executor.
Boundary: omitted/null/operator_unrestricted/read_only profile never reaches execution.
Counterexample: if the profile is visible in describe but dropped or replaced by a default, the requirement is not met.
Readiness: no unresolved product decision; deliberate missing-field rejection follows the explicitly requested profile contract. No readiness profile was observed; absence alone does not block planning.
Related tasks: PR-007 existing local_api scope bridge; PR-008/009 broader projection work; PR-010 firewall.
Implementation has not begun. Plan approval and live execution admission remain independent requirements.
