# PR-009 — SentinelX MCP Development Execution Projection & Dynamic Tool Contract V1 — Plan

## Plan State

```yaml
task_id: PR-009-mcp-development-execution-projection-dynamic-tool-contract-v1
stage: plan_review_rejected
plan_status: rejected
plan_revision: 2
requirement: docs/requirements/PR-009-mcp-development-execution-projection-dynamic-tool-contract-v1.md
prior_plan_review: docs/reviews/PR-009-mcp-development-execution-projection-dynamic-tool-contract-v1-plan-review-r1.md
plan_review: docs/reviews/PR-009-mcp-development-execution-projection-dynamic-tool-contract-v1-plan-review-r2.md
transport: github-pr
pr_number: 9
task_branch: task/mcp-development-execution-projection-dynamic-tool-contract-v1
base_branch: main
planning_baseline_main: f7e878f3497582547e5d52cd33b060cae18d2e84
implementation_authorized: false
execution_slice_set: null
acceptance_approved: false
completion_verified: false
review_r2:
  result: Rejected
  classification: external_blocker
  unresolved:
    - HubImplementationBinding
    - ProviderScopeAdmission
  verified:
    - AgentExecutionProfileContractExactBinding
```

Plan Revision 2 remediates the Plan-local inconsistencies identified in Review R1 without changing the canonical Requirement semantics. Review R2 confirms those Plan-local corrections are sound, but the Plan is not Implementation Ready because P0-A `HubImplementationBinding` and P0-B `ProviderScopeAdmission` remain unresolved external admission conditions.

No implementation Slice is executable, no Execution Slice Set may be compiled, and no implementation handoff is valid until all current-task P0 admission conditions below are independently resolved and read back.

## Current Verified Reality

### SentinelX repository / transport reality

- Canonical SentinelX project repository remains `bewaterhere-coder/sentinelx-cloud-core`.
- PR-009 transport remains Draft PR #9 on `task/mcp-development-execution-projection-dynamic-tool-contract-v1`.
- Connected GitHub repository discovery exposes no writable production Hub/MCP implementation repository for the `mcp.sentinelx.app` projection owner.
- Current SentinelX model-facing capabilities expose Host/local/Git/integration operations but no authorized Hub MCP projection mutation or deployment operation.
- No independently verified Hub repository, provider configuration target, control-plane API, deployment authority, or deployment receipt is currently bound to PR-009.

These observations establish only the currently available implementation surface. They do not prove that no Hub source exists elsewhere; they do prove that PR-009 currently has no verified writable/deployable Hub target it can lawfully mutate.

### PR-007 dependency reality

Latest Review R2 readback observed:

```yaml
pr: 7
head: c75cb818fef178dd834888b5edb51a56e031cd20
stage: implementation
s01: completed
s02: completed
s03: completed
s04: implementation_landed_verification_blocked
s05: not_started
acceptance_approved: false
completion_verified: false
```

PR-007 therefore remains moving provider-scope admission work. Revision 2 had previously observed head `acf64e62...`; the branch advancing to `c75cb818...` confirms that moving branch state is not stable implementation authority.

### PR-008 dependency reality

Review R2 revalidated the exact immutable Agent contract binding:

```yaml
pr: 8
head: f7594c468d764ad85c0dc508ad47f009c89793c1
stage: acceptance
acceptance: blocked_external
acceptance_approved: false
completion_verified: false
contract:
  path: docs/provider-execution-profile-tool-surface-v1.md
  blob_sha: 792a6e585c5bb516e9f4e8733f5ce7f3b1d6350e
  feature: script_run_execution_profile_v1
```

P0-C remains a valid exact implementation input binding. Any later PR-008 change affecting that contract invalidates the corresponding PR-009 projection assumptions and requires revalidation before implementation.

## Remediation Traceability

| Review finding | Plan disposition |
|---|---|
| R1 F1 — current-task P0 dependencies conflicted with proposed implementation entry | Remediated in Revision 2: no pre-P0 executable work; no Slice Set compiled before P0 closure. |
| R1 F2 — no authorized production Hub projection implementation target | Plan-local structure remediated by explicit `HubImplementationBinding`; external binding itself remains unresolved and blocks approval. |
| R1 F3 — PR-007 / PR-008 were moving dependencies | PR-008 is immutably pinned and verified; PR-007 remains moving/unverified and therefore still blocks P0-B. |
| R2 F1 — Hub implementation surface still absent | External blocker; no further Plan wording can satisfy it. |
| R2 F2 — Provider-scope admission not stable/verified | External dependency; requires exact verified PR-007/equivalent revision + receipt. |

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

Current status: **unresolved**.

### P0-B — ProviderScopeAdmission stable evidence

Before Implementation Ready, PR-007 or an equivalent provider-owned scope admission path must provide a stable exact revision/evidence set sufficient to support:

```text
provision
revalidate
inspect/readback
terminalize
```

with exact repository + semantic lineage binding, no caller-minted workspace authority, and no unrestricted fallback.

A moving implementation branch with verification blocked is not sufficient closure evidence.

Current status: **unresolved**.

### P0-C — AgentExecutionProfileContract exact binding

Current verified exact binding:

```text
PR-008 head = f7594c468d764ad85c0dc508ad47f009c89793c1
contract blob = 792a6e585c5bb516e9f4e8733f5ce7f3b1d6350e
feature token = script_run_execution_profile_v1
```

Current status: **verified exact binding** subject to drift invalidation.

### Admission invariant

```text
P0-A resolved
AND P0-B resolved
AND P0-C exact binding verified
→ Plan may be approved and Slice Set compiled

otherwise
→ remain orchestration-side; implementation forbidden
```

## Target Architecture After Admission

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

## Design After Admission

### D1 — Canonical projection contract

Freeze one versioned, machine-checkable projection contract for the exact target Agent. Required model-facing semantics:

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

### D2 — Projection conformance evaluator

Required cases:

1. complete compatible target schema → PASS;
2. missing `execution_profile` → `HubToolProjectionRequired`;
3. profile present but mutation scope missing → BLOCKED;
4. lineage/repository incomplete → BLOCKED;
5. target Agent missing required contract token → projection not admitted;
6. mixed-fleet target selection does not leak profiled fields;
7. projection cannot synthesize scope/repository/lineage authority.

### D3 — Agent dynamic-contract gap closure only when proven

Use the exact PR-008 bound contract by default. Change Agent advertisement only if conformance work proves a concrete Agent-owned metadata gap. No breaking wire change merely to carry scoped fields.

### D4 — Production Hub projection implementation

Using the exact P0-A binding, modify the Hub-owned implementation surface so a compatible selected Agent projects a model-facing schema capable of carrying:

```text
execution_profile
mutation
lineage
repository
```

Rules:

- per-target-Agent resolution;
- unsupported Agents remain legacy-compatible;
- Hub never invents authority-bearing values;
- payload forwarding preserves exact Agent semantics;
- incompatible contract fails closed;
- no wrapper/direct-exec/allowlist/unrestricted fallback.

### D5 — Provider-owned scope composition

Use the exact P0-B provider-scope revision/evidence:

```text
provision provider scope
→ read back exact scope + generation
→ model-facing profiled call with exact lineage/repository
→ verify scoped execution + audit
→ inspect terminal scope state
```

### D6 — Live ChatGPT projection probe

After Hub deployment, inspect the actual ChatGPT-visible tool schema and persist bounded evidence for target Agent revision, Agent contract revision, Hub deployment revision/receipt, client-visible required fields, and conformance result.

### D7 — Harmless end-to-end scoped transaction

Run one deterministic harmless marker through the actual model-facing profiled surface using provider-issued scope authority and exact repository/semantic lineage. Verify child success, deterministic readback, audit lineage, terminal scope closure, and direct Python `sentinel_exec` denial when Python is not allowlisted.

## Dependency Drift Rules

Any change to HubImplementationBinding, PR-007 consumed authority contract, PR-008 profile contract, Agent feature semantics, or Task/transport lineage invalidates affected assumptions before execution. Stop, reread exact evidence, and return to Planning/Plan Review when material.

## Future Execution Slices — Compile Only After Approval

**No canonical Execution Slice Set exists yet.**

### S01 — Projection Contract + Conformance Baseline
- freeze D1 against exact admitted dependency revisions;
- implement D2 fixtures/evaluator;
- prove mixed-fleet/no-authority-synthesis regressions.

### S02 — Hub Projection Implementation + Deployment
- D3 only if a concrete Agent metadata gap is proven;
- implement D4 on exact P0-A target;
- deploy/promote through authorized Hub mechanism;
- persist exact revision/deployment receipt and readback.

### S03 — Live Model-Facing Projection Verification
- run D6 against the current client-visible schema;
- PASS only if all scoped-development semantics are expressible for the compatible target Agent.

### S04 — End-to-End Scoped Development Transaction
- execute D5 + D7;
- verify audit evidence and terminal scope closure;
- verify direct Python denial;
- produce end-to-end evidence eligible for Acceptance.

## Review R2 Unblock Conditions

Another Plan-local rewrite is not useful while external admission remains unchanged.

A new substantive review becomes meaningful after:

1. a valid P0-A `HubImplementationBinding` is available; and
2. P0-B has an exact stable verified provider-scope admission revision/receipt.

At that point, Plan remediation should refresh exact dependency bindings/current reality, return the Task to `plan_review`, and then run a new Plan Review.
