# PR-009 — SentinelX MCP Development Execution Projection & Dynamic Tool Contract V1 — Plan

## Plan State

```yaml
task_id: PR-009-mcp-development-execution-projection-dynamic-tool-contract-v1
stage: plan_review
plan_status: revised_pending_review
plan_revision: 2
requirement: docs/requirements/PR-009-mcp-development-execution-projection-dynamic-tool-contract-v1.md
prior_plan_review: docs/reviews/PR-009-mcp-development-execution-projection-dynamic-tool-contract-v1-plan-review-r1.md
transport: github-pr
pr_number: 9
task_branch: task/mcp-development-execution-projection-dynamic-tool-contract-v1
base_branch: main
planning_baseline_main: f7e878f3497582547e5d52cd33b060cae18d2e84
implementation_authorized: false
execution_slice_set: null
acceptance_approved: false
completion_verified: false
```

Plan Revision 2 remediates the Plan-local inconsistencies identified in Review R1 without changing the canonical Requirement semantics. It deliberately does **not** pretend that the production Hub is writable or that active PR-007 / PR-008 dependencies have become completed merely because this Plan was revised.

No implementation Slice is executable, no Execution Slice Set may be compiled, and no implementation handoff is valid until all current-task P0 admission conditions below are independently resolved and read back.

## Current Verified Reality

Planning was refreshed against the current observable environment.

### SentinelX repository / transport reality

- Canonical SentinelX project repository remains `bewaterhere-coder/sentinelx-cloud-core`.
- PR-009 transport remains Draft PR #9 on `task/mcp-development-execution-projection-dynamic-tool-contract-v1`.
- Connected GitHub repository discovery exposes `sentinelx-cloud-core` but no writable production Hub repository.
- Read-only listing of the registered local repository root `D:\coco\repos` shows `bewaterhere-coder\sentinelx-cloud-core` but no separately materialized Hub repository under that root.
- Current SentinelX model-facing capabilities expose Host/local operations but no authorized Hub MCP projection mutation or deployment operation.

These observations establish only the currently available implementation surface. They do not prove that no Hub source exists elsewhere; they do prove that PR-009 currently has no verified writable/deployable Hub target it can lawfully mutate.

### PR-007 dependency reality

Current observed PR #7:

```yaml
pr: 7
head: acf64e62b72d72e5bd7fdb6070d7904f881b3360
stage: implementation
s01: completed
s02: completed
s03: completed
s04: implementation_landed_verification_blocked
acceptance_approved: false
completion_verified: false
```

PR-007 therefore remains moving provider-scope admission work. PR-009 may inspect it but must not treat its moving branch as final authority.

### PR-008 dependency reality

Current observed PR #8:

```yaml
pr: 8
head: f7594c468d764ad85c0dc508ad47f009c89793c1
stage: acceptance
acceptance: blocked_external
acceptance_approved: false
completion_verified: false
```

PR-008's Agent-owned execution-profile contract is available at the immutable revision above. The exact public contract artifact at that revision is:

```text
docs/provider-execution-profile-tool-surface-v1.md
blob_sha = 792a6e585c5bb516e9f4e8733f5ce7f3b1d6350e
```

PR-009 may use this immutable revision as planning evidence for Agent payload semantics. Any later PR-008 change affecting that contract invalidates the corresponding PR-009 projection assumptions and requires revalidation before implementation.

This immutable binding breaks the circular assumption that PR-008 must first complete an Acceptance which itself depends on the Hub projection being fixed. It does **not** mark PR-008 completed and does not remove the Requirement's current P0 state by itself.

## Remediation Traceability

| Review R1 finding | Revision 2 remediation |
|---|---|
| F1 — current-task P0 dependencies conflict with proposed implementation entry | Remove all pre-P0 executable work. D1/D2 contract/fixture work is no longer an implementation exception. No Slice Set is compiled and no Slice becomes executable until the exact current-task P0 admission conditions are resolved. |
| F2 — no authorized production Hub projection implementation target | Add an explicit `HubImplementationBinding` admission contract. Plan approval/implementation is forbidden until a concrete writable/deployable Hub-owned target, mutation interface, authority, deployment path, and readback evidence are bound. Repository docs/fixtures cannot substitute for that target. |
| F3 — PR-007 / PR-008 are active moving dependencies | Add immutable dependency-binding and drift-invalidation rules. PR-008 planning semantics are pinned to exact head/blob evidence; PR-007 must reach verified provider-scope admission (or equivalent exact verified revision) before Implementation Ready. Any dependency drift invalidates affected assumptions. |

## Implementation-Ready Admission Gate

The following are **preconditions for Plan approval and Implementation Ready**, not implementation Slices.

### P0-A — HubImplementationBinding

A valid binding MUST identify exactly one production-Hub-owned implementation surface capable of changing the ChatGPT-facing MCP tool projection.

Acceptable target kinds:

```text
source_repository
provider_deployment_configuration
provider_control_plane_api
other independently verified Hub-owned mutation surface
```

The binding must record durable evidence equivalent to:

```yaml
hub_implementation_binding:
  target_kind: <kind>
  target_identity: <exact repo/service/config/api identity>
  owner: <Hub implementation owner>
  mutation_interface: <exact code/config/API seam>
  authorization_evidence: <verified authority reference>
  version_or_revision_binding: <exact immutable ref when applicable>
  deployment_interface: <exact deployment/promotion mechanism>
  deployment_receipt_shape: <how deployment success is proven>
  model_facing_readback: <how current ChatGPT/MCP schema is re-read>
```

Invalid evidence includes:

- a support ticket alone;
- a desired JSON schema with no mutation target;
- Agent capability advertisement;
- changes only inside `sentinelx-cloud-core` while Hub remains unchanged;
- an assumed hidden repository;
- conversation memory or a guessed deployment path.

Until this binding exists and is read back, `HubProjectionWriteOrDeploymentSurface` remains unresolved and implementation is forbidden.

### P0-B — ProviderScopeAdmission stable evidence

Before Implementation Ready, PR-007 or an equivalent provider-owned scope admission path must provide a stable exact revision/evidence set sufficient to support:

```text
provision
revalidate
inspect/readback
terminalize
```

with exact repository + semantic lineage binding, no caller-minted workspace authority, and no unrestricted fallback.

For PR-007 specifically, a moving implementation branch with verification still blocked is not sufficient P0 closure evidence. The accepted evidence must identify the exact revision that PR-009 consumes and the verification/receipt proving the required provider-owned scope path.

### P0-C — AgentExecutionProfileContract exact binding

PR-009 currently pins planning semantics to:

```text
PR-008 head = f7594c468d764ad85c0dc508ad47f009c89793c1
contract blob = 792a6e585c5bb516e9f4e8733f5ce7f3b1d6350e
feature token = script_run_execution_profile_v1
```

Before Plan approval, the reviewer must verify that this exact contract remains a valid immutable implementation input or replace it with a newer exact verified revision. If the relevant PR-008 contract changes, the old binding is stale and PR-009 must re-evaluate its projection contract before implementation.

### Admission invariant

```text
P0-A resolved
AND P0-B resolved
AND P0-C exact binding verified
→ Plan may be approved and Slice Set compiled

otherwise
→ remain orchestration-side; implementation forbidden
```

This preserves the canonical Requirement's current-task P0 semantics rather than silently reclassifying them.

## Target Architecture After Admission

Once the admission gate is satisfied, PR-009 implements one composition rather than a second execution system:

```text
ChatGPT model-facing tool schema
        ↓
Hub per-target projection                     ← exact P0-A target
        ↓
SentinelX request payload
        ↓
PR-008 profiled script_run contract           ← exact immutable binding
        ↓
PR-007 provider-owned scope admission         ← exact verified binding
        ↓
existing scoped_mutation executor
        ↓
AppContainer + audit + terminalization
```

## Design

### D1 — Canonical projection contract

After P0 admission, freeze one versioned, machine-checkable projection contract describing the mapping a compatible Hub must expose for the exact target Agent.

Repository-owned artifacts may include:

```text
docs/mcp-development-execution-projection-v1.md
tests/fixtures/mcp_development_execution_projection_v1.json
```

Required model-facing semantics:

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

The contract references rather than redefines PR-007 scope authority and PR-008 profile semantics.

### D2 — Projection conformance evaluator

Add a pure conformance evaluator/test surface that can classify a normalized client-visible schema against D1.

Required cases:

1. complete compatible target schema → PASS;
2. missing `execution_profile` → `HubToolProjectionRequired`;
3. profile present but mutation scope missing → BLOCKED;
4. lineage/repository incomplete → BLOCKED;
5. target Agent missing required contract token → projection not admitted;
6. mixed-fleet target selection does not leak profiled fields;
7. projection cannot synthesize scope/repository/lineage authority.

Do not add production Agent runtime code merely to parse a ChatGPT schema when a fixture/evaluator layer is sufficient.

### D3 — Agent dynamic-contract gap closure only when proven

Use the exact PR-008 bound contract as the default Agent-owned input.

Only if D1/D2 prove a concrete Agent-owned metadata gap may PR-009 change Agent contract advertisement. Any such change must be additive, versioned and mixed-fleet safe.

The existing arbitrary request payload mapping means no breaking request-wire protocol change is planned merely to carry scoped fields.

### D4 — Production Hub projection implementation

This is the implementation step that Plan Revision 1 was missing.

Using the exact `HubImplementationBinding` from P0-A, modify the Hub-owned implementation surface so a compatible selected Agent projects a model-facing execution schema semantically capable of carrying:

```text
execution_profile
mutation
lineage
repository
```

Rules:

- resolution is per target Agent, not fleet-global;
- unsupported Agents retain legacy-compatible shape;
- the Hub projects fields but never invents authority-bearing values;
- payload forwarding preserves exact semantics expected by the Agent;
- missing/incompatible target contract fails closed;
- no wrapper/direct-exec/allowlist/unrestricted fallback is introduced.

The external implementation must produce exact revision/deployment evidence through the bound target's own transport. PR-009 records references/receipts; it does not copy Hub code into `sentinelx-cloud-core` to fake ownership.

### D5 — Provider-owned scope composition

Use the exact P0-B provider-scope revision/evidence. The live flow is:

```text
provision provider scope
→ read back exact scope + generation
→ model-facing profiled call with exact lineage/repository
→ verify scoped execution + audit
→ inspect terminal scope state
```

No caller-created scope/workspace identity is valid.

### D6 — Live ChatGPT projection probe

After Hub deployment, inspect the actual ChatGPT-visible tool schema and normalize it into the D2 evaluator.

Persist bounded evidence of:

```text
target Agent build/revision
Agent contract revision
Hub deployment revision/receipt
client-visible required fields
projection conformance result
```

Do not persist secrets or reusable live mutation authority.

### D7 — Harmless end-to-end scoped transaction

Run one deterministic harmless marker through the actual model-facing profiled surface using provider-issued scope authority and exact repository/semantic lineage.

Success requires:

- child execution success;
- deterministic marker/readback;
- audit lineage evidence;
- terminal/non-reactivatable scope readback;
- no canonical source-checkout mutation used as a shortcut.

Separately prove direct Python `sentinel_exec` remains `command_not_allowed` while Python is not allowlisted.

## Dependency Drift Rules

Any of the following invalidates affected PR-009 implementation assumptions before execution:

```text
HubImplementationBinding target/revision changes
PR-007 consumed authority contract changes
PR-008 execution-profile contract changes
Agent feature token/required-field semantics change
repository or task transport lineage changes
```

On drift:

1. stop before further implementation side effects;
2. read the new exact dependency evidence;
3. determine whether Plan semantics are still valid;
4. return upstream to Planning/Plan Review when material;
5. never silently follow a moving branch.

## Execution Slices — Compile Only After Plan Approval

This section defines future slice semantics. **No canonical Execution Slice Set exists yet.** It may be compiled only after P0-A/P0-B/P0-C admission passes and Plan Review approves this exact revision.

### S01 — Projection Contract + Conformance Baseline

- freeze D1 against exact P0 dependency revisions;
- implement D2 fixtures/evaluator;
- prove mixed-fleet/no-authority-synthesis regressions.

### S02 — Hub Projection Implementation + Deployment

- execute D3 only if a proven Agent-owned metadata gap exists;
- implement D4 on the exact P0-A Hub target;
- deploy/promote through the authorized Hub mechanism;
- persist exact revision/deployment receipt and readback.

### S03 — Live Model-Facing Projection Verification

- run D6 against the production/current client-visible schema;
- PASS only if all required scoped-development semantics are expressible for the compatible target Agent.

### S04 — End-to-End Scoped Development Transaction

- execute D5 + D7;
- verify audit evidence and terminal scope closure;
- verify direct Python denial;
- produce end-to-end evidence eligible for Acceptance.

## Verification Strategy

Repository-owned checks:

```text
focused projection-contract tests
mixed-fleet compatibility tests
no-authority-synthesis tests
existing exact PR-008 profile contract checks when touched
existing exact PR-007 scope contract checks when composed
git diff --check or equivalent static validation
```

External/live checks:

```text
Hub deployment receipt/readback
actual ChatGPT-visible tool schema
known target Agent build + contract token
provider-issued scope lifecycle
harmless scoped execution
audit + terminal scope readback
direct exec denial
```

CI is optional evidence, not the only semantic acceptance channel.

## Risk Controls

- **False implementation target:** P0-A requires an exact Hub-owned mutation/deployment surface before approval.
- **P0 bypass:** no repository-owned "pre-work" Slice is executable while current-task P0 remains unresolved.
- **Dependency drift:** exact immutable refs plus invalidation rules; no moving-branch authority.
- **Duplicate authority:** PR-007/008 semantics are composed, never reimplemented casually.
- **Security regression:** no synthesized authority, no unrestricted fallback, no allowlist expansion.
- **Mixed-fleet regression:** projection is resolved per selected Agent.
- **False completion:** only production schema + harmless scoped transaction + terminal readback can close the task.

## Plan Review Checklist for Revision 2

The next reviewer must verify all of the following before an `Approved` decision:

1. P0-A identifies a real writable/deployable Hub-owned implementation target with authority and readback evidence.
2. P0-B identifies a stable verified provider-scope admission revision/evidence set.
3. P0-C still points to a valid exact PR-008 contract revision or has been refreshed to a newer immutable one.
4. No implementation Slice is being used to resolve a still-open current-task P0 dependency.
5. Hub projection changes occur on the actual Hub-owned target, not as documentation-only changes in `sentinelx-cloud-core`.
6. final verification still requires the real ChatGPT-visible schema and harmless scoped transaction.

If any item is unresolved, the Plan is not Implementation Ready and must not be approved into `implementation`.
