# PR-012 — execute_scoped Explicit Execution Profile Schema & End-to-End Propagation V1 — Acceptance R1

## Decision

```yaml
task_id: PR-012-execute-scoped-explicit-execution-profile-v1
requirement_revision: 1
plan_revision: 3
acceptance_revision: 1
result: Approved
canonical_transport: github-pr
pr_number: 12
canonical_branch: task/execute-scoped-explicit-execution-profile-v1
evaluated_head_before_acceptance_artifacts: 6a8b576e5d2aa55ff9153cee60392d34157ccc4b
verified_product_candidate: 1e4012d7d6bfe4fa1bff70f364f3199d67626104
current_stage: accepted
gate_transition: acceptance_to_accepted
acceptance_approved: true
completion_verified: false
```

**PR-012 Acceptance R1: Approved.**

Requirement Revision 1 is satisfied on the canonical PR transport. Approval enters the DevForge `accepted` boundary only. It does not merge PR #12, mark the Task done, or perform completion finalization.

## Runtime / Transport Consistency

PASS.

- DevForge Runtime: `bewaterhere-coder/DevForge main@1dc76ed0bcc1a70a2c5a860cd7a99aedd5d7820a`, version `2.40.0`.
- Acceptance Contract: `1.5`.
- Canonical repository: `bewaterhere-coder/sentinelx-cloud-core`.
- Canonical PR: `#12`, branch `task/execute-scoped-explicit-execution-profile-v1`, base `main`.
- Canonical main at Acceptance: `dbf4bfc9ebcdbde2374d41e6825b613d46aa87f2`.
- PR remained open, draft, mergeable, and on the canonical transport before Acceptance persistence.
- No TransportDrift is present.

The exact verified product candidate is `1e4012d7d6bfe4fa1bff70f364f3199d67626104`. The branch head immediately before Acceptance persistence was eight commits ahead of that candidate only for DevForge checkpoints, Slice Set state, Requirement state, and completion receipts; compare readback showed no product-code change after the verified candidate.

## Implementation / Verification Evidence

PASS.

- Focused exact-candidate verification: Python `3.12.13`, `47 passed`, `0 failed`, `0 errors`, exit `0`.
- Generic CI run `37225111632`: success.
- macOS Agent run `37225111636`: success.
- PR-010 regression runs S01-S05: all success (`37225111592`, `37225111580`, `37225111578`, `37225111593`, `37225111625`).
- S01 completion checkpoint and completion receipt are durable and read back.

## Live Activation / AC6 Evidence

PASS.

### Exact candidate activation

The verifier restarted the SentinelX service after the operator-installed exact candidate. Live capability readback changed from the pre-fix build `0.24.1.dev155+gdbf4bfc9e` to:

```text
0.24.1.dev175+g1e4012d7d
```

The embedded git revision `1e4012d7d` matches the exact verified product candidate.

### Live describe

Current `devforge_runtime` `local_api.describe` advertises `execute_scoped` with `execution_profile` in both the ordered parameter projection and required schema. The schema is exactly:

```json
{"type":"string","const":"scoped_mutation"}
```

No additional compatibility default is exposed.

### Positive scoped execution

A provider-owned scope was provisioned and revalidated for the exact repository and PR-012 lineage. Live execution used:

```text
execution_profile = scoped_mutation
interpreter = python3
marker = PR012_AC6_SCOPED_MARKER_OK
```

Observed result:

```yaml
returncode: 0
output: PR012_AC6_SCOPED_MARKER_OK
execution_profile: scoped_mutation
audit_operation_id: mao_piytxrpXU06EHTgqwswtL-ki
scope_id: mss_KqXM5SqyDhicYNOXhluiail6
generation: 1
terminal_state: terminal
```

Independent `inspect_scope` readback confirmed the same scope in `terminal` state with terminalization timestamp `2026-10-04T19:28:33.679212Z`.

### Negative admission evidence

A separate provider-owned scope was used to prove pre-executor rejection:

- omitted `execution_profile` -> `invalid_payload: missing execute_scoped fields: ['execution_profile']`;
- `execution_profile=operator_unrestricted` -> `invalid_payload: unsupported execution_profile: operator_unrestricted`;
- after both rejected calls, `inspect_scope` still reported `state=provisioned`, showing execution had not consumed/terminalized the scope;
- the verifier then terminalized that scope explicitly and read back `state=terminal`.

This is live evidence that omitted/unsupported profiles are rejected before the scoped executor runs.

### Fail-closed observation

An initial live marker attempt with `interpreter=powershell` returned `HostMutationSandboxUnavailable: powershell could not initialize inside the required AppContainer`; its scope was automatically terminalized. This is non-material to PR-012 because the Requirement does not mandate a specific interpreter, the subsequent Python marker proved the exact end-to-end profile path, and the failed PowerShell path remained fail-closed rather than bypassing the sandbox.

## Acceptance Matrix

- **AC1 — PASS:** live `local_api.describe` exposes required `execution_profile` with only `scoped_mutation`.
- **AC2 — PASS:** focused integration tests verify routing to the existing executor, and live AC6 execution returned the explicit profile unchanged.
- **AC3 — PASS:** focused tests cover missing/null/non-string/unsupported values with zero executor calls; live omitted and `operator_unrestricted` requests were rejected before scope consumption.
- **AC4 — PASS:** scope ownership, disabled-operation, lineage, unexpected-result and PR-010 security regressions pass; live sandbox failure remained fail-closed.
- **AC5 — PASS:** exact-candidate focused tests passed (`47/47`), repository CI/macOS checks passed, and no product-code drift occurred afterward.
- **AC6 — PASS:** exact verified candidate is running, describe includes the field, provider scope was provisioned/revalidated, explicit `scoped_mutation` marker executed successfully, durable audit identity was returned, and scope terminalization was independently read back.

## Safety / Scope

PASS.

- No canonical checkout mutation was used for development or Acceptance.
- No Hub modification, permission expansion, command allowlist expansion, `operator_unrestricted`, generic script fallback, second executor, second scope store, or alternate transport was introduced.
- Acceptance service restart loaded the explicitly operator-installed exact candidate; Acceptance did not install moving `main`.
- UI / Visual Fidelity: NotApplicable.

## Acceptance Result

```text
Acceptance Approved: true
Completion Verified: false
Result: Approved
Gate Transition: acceptance -> accepted
Current Stage: accepted
```

Canonical next action:

`#开发完成 PR-012-execute-scoped-explicit-execution-profile-v1`
