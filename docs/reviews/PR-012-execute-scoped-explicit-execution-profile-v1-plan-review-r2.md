# PR-012-execute-scoped-explicit-execution-profile-v1 — Plan Review R2

Decision: Rejected
Plan revision: 2
Plan blob: 286f4fb82afbb617e4ba03ba4d389ceb0b41c76f
Requirement revision: 1, unchanged
Transport: PR #12 / task/execute-scoped-explicit-execution-profile-v1

## Finding disposition
- R1 F02: Resolved. Live activation and AC6 belong to verifier-owned Acceptance, not an implementation Slice. Exact-candidate, operator authorization, recovery and audit/terminal readback requirements are explicit.
- R1 F03: Resolved. Concrete test modules, schema-to-params projection, adapter and integration checks map the behavior/acceptance rules.
- R1 F01: Unresolved, external_blocker. Read-only ls-remote proves branch access only. No verified isolated direct Codex execution workspace, current test toolchain admission and writable exact transport evidence has been produced.

## Technical assessment
The implementation strategy, scope, deliberate omitted-field incompatibility, no-default behavior and proposed verification are acceptable. No further Plan prose correction is required for F02/F03.
Missing live installation authority is a later Acceptance boundary, not an additional current planning defect.
F01 is operational admission, not evidence that the code solution is infeasible. It cannot be resolved by rewording the Plan, creating a provisional scope through an incompatible interface, or claiming read access proves execution authority.

## Required next work
Perform read-only discovery of the configured direct Codex execution environment and applicable workspace admission contracts; obtain exact transport/isolation/toolchain/persistence evidence through a contract-admitted path. If unavailable, preserve external_blocker and stop; do not churn Plan revisions or fall back to Windows wrappers/source checkout mutation.
No implementation handoff, Slice Set or approval is issued.

## Gate
stage: plan_review_rejected
plan_approved: false
implementation_authorized: false
next_expected_actor: orchestration
Manual remediation control remains #开发计划修复 PR-012-execute-scoped-explicit-execution-profile-v1, but only meaningful when it can add real F01 admission evidence; F02/F03 do not need another rewrite.
