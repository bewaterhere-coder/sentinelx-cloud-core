# PR-009 — SentinelX MCP Development Execution Projection & Dynamic Tool Contract V1 — Plan

## State

```yaml
task_id: PR-009-mcp-development-execution-projection-dynamic-tool-contract-v1
stage: plan_review_rejected
requirement: docs/requirements/PR-009-mcp-development-execution-projection-dynamic-tool-contract-v1.md
transport: github-pr
pr_number: 9
task_branch: task/mcp-development-execution-projection-dynamic-tool-contract-v1
plan_status: rejected
plan_revision: 1
plan_review: docs/reviews/PR-009-mcp-development-execution-projection-dynamic-tool-contract-v1-plan-review-r1.md
implementation_authorized: false
acceptance_approved: false
completion_verified: false
```

## Rejected Findings

Plan Review R1 rejected this revision on:

- `F1-current-task-p0-dependencies-conflict-with-proposed-implementation-entry`;
- `F2-no-authorized-production-hub-projection-implementation-target`;
- `F3-active-pr007-pr008-dependencies-are-not-stable-implementation-inputs`.

Canonical remediation input:

`docs/reviews/PR-009-mcp-development-execution-projection-dynamic-tool-contract-v1-plan-review-r1.md`

## Planning Decision

Do not reimplement Host mutation scope or profiled script execution. PR-009 is an integration/projection task with three distinct truth boundaries:

```text
A. Agent contract semantics / fixtures        ← repository-owned
B. Hub/MCP projection implementation          ← external production owner
C. Live ChatGPT end-to-end acceptance         ← external evidence boundary
```

PR-007 remains authority for provider-issued scope lifecycle. PR-008 remains authority for Agent-side profiled `script_run` support and capability metadata. PR-009 adds only the missing cross-layer projection contract, conformance fixtures, external Hub handoff surface, and live end-to-end proof.

Because production Hub source/deployment is not currently writable from this project environment, Plan Review must treat `HubProjectionWriteOrDeploymentSurface` as a current-task P0 implementation dependency. The Task may implement repository-owned contract/evidence work, but it cannot claim end-to-end completion until the Hub projection is independently changed and verified.

## Design

### D1 — Freeze one canonical projection contract

Create a focused versioned contract document and machine-readable fixture describing the exact mapping required by a compatible Hub.

Proposed artifacts:

```text
docs/mcp-development-execution-projection-v1.md
tests/fixtures/mcp_development_execution_projection_v1.json
```

The contract must reference, not copy/redefine, canonical semantics from:

- PR-007 mutation-scope lifecycle;
- PR-008 execution-profile contract;
- current Agent `RequestMessage.payload` envelope.

Required model-facing semantic fields:

```text
execution_profile
mutation.scope_ref.scope_id
mutation.scope_ref.generation
lineage.project_id
lineage.task_id
lineage.run_id
lineage.attempt_id
lineage.slice_id?
repository.vcs
repository.authority
repository.path
```

The fixture also freezes compatibility inputs such as contract/version token and target-Agent capability requirements.

### D2 — Add projection conformance evaluator/tests

Add a repository-owned evaluator that can validate a model-facing tool schema or normalized schema snapshot against D1.

Preferred shape:

```text
src/sentinelx_core/tool_projection_contract.py   # pure schema/compatibility semantics only, if runtime code is justified
or
scripts/tools/test helper / tests-only evaluator # if no Agent runtime behavior is required
```

Selection rule: do not add runtime production code solely to parse ChatGPT schema if a test/fixture layer is sufficient.

Tests must cover:

1. complete scoped-development schema → PASS;
2. missing `execution_profile` → `HubToolProjectionRequired`;
3. `execution_profile` present but missing `mutation` → BLOCKED;
4. scope present but lineage/repository incomplete → BLOCKED;
5. target Agent lacking required contract token/revision → projection not admitted;
6. mixed-fleet target resolution does not leak new fields;
7. model-facing projection never supplies authority-bearing values itself.

### D3 — Dynamic contract advertisement integration

Reuse PR-008 Agent capability metadata as the primary Agent-owned contract source where sufficient.

First verify the exact PR-008 merged/active output. Only add Agent changes when a concrete gap remains. Possible additive gap closure may include a stable contract revision/fingerprint or normalized projection descriptor, but MUST NOT duplicate the full execution profile metadata already implemented by PR-008.

Protocol rule:

- `RequestMessage.payload` already supports arbitrary mappings, so no breaking request-wire change is planned;
- changing `HelloMessage` or `sentinelx-cloud-protocol` is allowed only if evidence proves capability-name + on-demand capability detail cannot support safe target-specific Hub projection;
- because the upstream protocol repository is not currently writable here, any required protocol change becomes an explicit external dependency rather than an unauthorized fork claim.

### D4 — Hub implementation handoff contract

Produce an exact Hub-side implementation contract for the production owner. It must specify:

```text
per-target Agent capability/contract resolution
model-facing schema projection rules
payload forwarding semantics
mixed-fleet compatibility
no authority synthesis
stable blocked diagnostics
schema/readback evidence required for deployment acceptance
```

This repository may persist the handoff contract/evidence, but no file in this repository may claim production Hub deployment.

If a writable Hub repository/deployment surface becomes available during the Task, implementation must occur in that exact external target under separately verified authority; PR-009 must record the external revision/deployment evidence rather than copying Hub code into sentinelx-cloud-core.

### D5 — Compose provider-owned scope admission

Consume PR-007/equivalent verified mutation-scope operation for live testing. Do not mint scope/workspace values in tests or orchestration.

Required sequence:

```text
provision provider scope
→ read back scope + generation
→ invoke model-facing scoped execution with exact lineage/repository
→ verify execution/audit evidence
→ inspect terminal scope state
```

If PR-007 remains unverified/incomplete, D5 is blocked; no substitute path is authorized.

### D6 — Live ChatGPT projection probe

Acceptance must inspect the actual current ChatGPT-visible tool surface, not merely Agent capabilities.

Normalize observed schema into the D2 evaluator and persist bounded evidence of:

```text
target Agent build/revision
advertised contract revision
client-visible required fields
Hub projection result
```

No secrets, credentials, live reusable mutation authority, or protected filesystem inventory may be persisted.

### D7 — Harmless end-to-end scoped transaction

After D5/D6 pass, execute one deterministic harmless marker through the actual ChatGPT-visible surface:

```text
execution_profile=scoped_mutation
provider-issued scope
exact repository identity
exact project/task/run/attempt[/slice] lineage
```

Success requires:

- scoped executor result proves child success;
- deterministic marker/readback proves intended workspace execution only;
- audit lineage is present;
- final scope readback is terminal/non-reactivatable;
- no canonical source checkout mutation occurred as a test shortcut.

Separately verify direct Python `sentinel_exec` remains `command_not_allowed` when Python is not allowlisted.

### D8 — External blocker semantics

If production Hub remains inaccessible or the live tool schema remains stale:

```text
Acceptance = Blocked
finding = external_blocker
reason = HubProjectionWriteOrDeploymentSurface | HubToolProjectionRequired
completion_verified = false
```

Do not churn Agent code after repository-owned contract tests pass merely because the closed-source Hub remains unchanged.

## Expected Repository-Owned Changes

Likely:

```text
docs/mcp-development-execution-projection-v1.md
tests/fixtures/mcp_development_execution_projection_v1.json
tests/test_mcp_development_execution_projection.py
README.md or focused operator/dependency documentation only if needed
```

Conditional only after evidence of a real gap:

```text
src/sentinelx_core/executor.py
src/sentinelx_core/handlers/basic.py
other PR-008 contract-advertisement seams
```

Explicitly not owned here:

```text
production mcp.sentinelx.app Hub source/deployment
PR-007 scope-store/lifecycle implementation
PR-008 scoped-script executor implementation
Windows AppContainer redesign
command allowlist expansion
operator_unrestricted fallback
```

## Execution Slices (proposed after Plan approval)

### S01 — Projection Contract & Conformance Fixtures

Scope:

- D1 projection contract;
- D2 fixture/evaluator/tests;
- exact references to PR-007/008 semantics;
- no Agent runtime mutation unless required by failing evidence.

Exit:

- complete/incomplete schema cases deterministically classified;
- mixed-fleet and no-authority-synthesis regressions pass;
- current Agent contract source is explicitly bound.

### S02 — Agent Contract Gap Closure / External Handoff

Scope:

- D3 only if S01 proves an Agent-owned contract gap;
- D4 Hub implementation handoff artifact;
- preserve wire compatibility and existing Host security boundaries.

Exit:

- repository-owned dynamic contract is sufficient for a compatible Hub;
- external Hub action required is exact and machine-testable;
- no false Hub deployment claim.

### S03 — Live Hub Projection Verification

Preconditions:

- writable/deployed Hub projection change independently evidenced;
- known Agent build containing required PR-007/008/009 contract inputs.

Scope:

- D6 actual ChatGPT-visible schema probe;
- D2 conformance evaluator against live normalized schema.

Exit:

- PASS only if full scoped-development schema is visible for the compatible target Agent;
- otherwise BLOCKED external dependency, not Agent-code churn.

### S04 — End-to-End Scoped Development Transaction

Preconditions:

- S03 PASS;
- PR-007/equivalent provider scope admission verified.

Scope:

- D5 + D7 harmless scoped marker;
- terminal scope readback;
- direct Python exec denial regression.

Exit:

- end-to-end Receipt proves the ordinary ChatGPT → Hub → Agent → scoped Host Runtime path works without fallback;
- task becomes eligible for Acceptance.

## Verification Strategy

Repository-owned checks:

```text
python -m pytest focused projection tests
existing PR-008 capability/profile regressions
existing PR-007 scope contract regressions where composition is touched
git diff --check / equivalent static validation
```

External/live checks:

```text
actual ChatGPT-visible tool schema
known target Agent capability/readiness
provider-issued scope lifecycle
harmless scoped execution
audit and terminal scope readback
direct exec denial
```

CI is useful evidence but is not the only semantic acceptance channel.

## Risk Controls

- **Duplicate implementation risk:** PR-007/008 code is consumed by reference; changes to their seams require evidence of an uncovered gap.
- **Closed-source Hub risk:** repository completion cannot substitute for deployment evidence.
- **Schema drift risk:** machine-readable fixture + target-specific conformance evaluator becomes regression evidence.
- **Security regression risk:** no synthesized scope/workspace authority and no unrestricted fallback.
- **Mixed-fleet risk:** contract resolution is per target Agent.
- **False-positive acceptance risk:** only current ChatGPT-visible schema plus real harmless invocation can close the external boundary.

## Plan Review Questions

Plan Review should verify:

1. PR-009 is materially distinct from PR-007/008 and does not duplicate their implementation authority;
2. D1/D2 provide enough machine-checkable value to justify repository-owned work while Hub remains external;
3. `HubProjectionWriteOrDeploymentSurface` is correctly treated as a current-task P0 implementation/acceptance dependency;
4. no protocol change is proposed without concrete necessity;
5. S03/S04 cannot be entered from repository-only evidence;
6. the final acceptance proof matches DevForge Host Runtime requirements without provider fallback.
