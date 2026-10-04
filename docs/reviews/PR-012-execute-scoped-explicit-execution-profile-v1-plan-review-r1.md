# PR-012-execute-scoped-explicit-execution-profile-v1 — Plan Review R1

Decision: Rejected
Reviewed Plan: R1, blob ee7814614d6a8d1d6e10cd7030aff76f6d6b7098
Requirement: R1, blob 9715bff9177dd38631031dac201806926efb56e4
Canonical transport: PR #12 / task/execute-scoped-explicit-execution-profile-v1
Review scope: pre-implementation Plan Review; no product mutation or implementation authorization.

## Accepted direction
The schema/adapter correction is narrow and supported by source evidence. Existing code already supplies a fixed scoped_mutation value to the existing executor. Explicit validation and propagation preserve this design without adding another executor. Required-field rejection is consistent with B3/B7. Unit/integration evidence and live evidence are correctly distinguished.

## Findings

### F01 — Execution bootstrap admission unresolved
Severity: BLOCKER
Classification: external_blocker
Plan identifies the current Host projection mismatch but leaves the admitted implementation/test execution path to later discovery. The task cannot repair its own schema by calling the incompatible current interface. Repository API artifact persistence does not establish an admitted code execution/test workspace.
Required resolution: verify the configured direct/codex execution channel, its exact PR-12 transport binding, isolated workspace and appropriate test mechanism, or another independently contract-admitted bootstrap path with exact evidence. Do not invent wrapper, unrestricted execution or canonical-checkout mutation. Missing execution admission must remain explicit.

### F02 — Live activation and lifecycle ownership are underspecified
Severity: IMPORTANT, approval-blocking for current Plan
Classification: plan_local
Proposed S02 is live activation/verification at acceptance, whereas implementation Slice completion and Acceptance ownership are distinct. Step 6 calls for an approved deployment path but does not identify activation ownership, exact-candidate selection or its separate authorization boundary.
Required correction: distinguish implementation Slice(s) from Acceptance/deployment operations. Map AC6 to verifier-owned live acceptance evidence; name required activation admission facts (exact candidate, installation/restart owner and authority, previous build/recovery boundary, schema readback, harmless provider-scoped marker, audit and terminal scope readback). Missing activation evidence must block acceptance without inventing permission or completion.

### F03 — Integration and regression targets need bounded discovery
Severity: IMPORTANT
Classification: plan_local
The Plan says directly relevant tests and local_api/profile tests without establishing concrete existing test modules or how action parameter projection is produced.
Required correction: inspect the relevant existing adapter/local_api test modules and schema projection path, identify exact regression entrypoints and map B1-B7/AC1-AC6 to implementation and evidence. Do not expand into unrelated Hub work.

## Counterevidence
This is a small change and may be implementable through the already configured direct Codex channel. Therefore F01 does not prove technical infeasibility. It proves that current read-back evidence has not admitted that path. Existing fixed-profile execution is also not inherently unrestricted; the defect is explicit caller/schema contract alignment.

## Gate
Requirement remains Ready and unchanged.
Plan Approved: false.
Implementation Authorized: false.
Current stage: plan_review_rejected.
Next actor: orchestration.
Plan-local repairs cannot claim F01 resolved without external admission evidence.
Next command: #开发计划修复 PR-012-execute-scoped-explicit-execution-profile-v1
