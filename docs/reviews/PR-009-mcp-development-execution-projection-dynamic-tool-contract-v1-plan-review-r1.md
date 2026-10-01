# PR-009 — SentinelX MCP Development Execution Projection & Dynamic Tool Contract V1 — Plan Review R1

## Review State

```yaml
task_id: PR-009-mcp-development-execution-projection-dynamic-tool-contract-v1
review_target: plan
plan_revision: 1
result: Rejected
reviewed_task_head: 7499b56fed68772969f062b3b188484fb91c9a6e
runtime:
  devforge_version: v2.29.0
  devforge_revision: c0266c113e4e6b8f2b90d9246af153a617e9d301
  project_development_workflow: "2.1"
  review_contract: "1.3"
next_gate: plan_review_rejected
next_expected_actor: planner
```

## Scope Reviewed

- Canonical Requirement: `docs/requirements/PR-009-mcp-development-execution-projection-dynamic-tool-contract-v1.md`
- Canonical Plan Revision 1: `docs/plans/PR-009-mcp-development-execution-projection-dynamic-tool-contract-v1-plan.md`
- Current task transport: PR #9 / `task/mcp-development-execution-projection-dynamic-tool-contract-v1`
- Current canonical SentinelX base: `f7e878f3497582547e5d52cd33b060cae18d2e84`
- Related active Task PR-007: provider-owned mutation-scope admission remains incomplete.
- Related active Task PR-008: Agent-side profiled execution contract is implemented substantially but Acceptance remains blocked on production Hub projection and provider-scope admission.
- Production `mcp.sentinelx.app` Hub source/deployment remains outside this repository and no writable Hub implementation/deployment surface is currently available through the connected project environment.

## Decision

**Rejected.**

The architectural direction is valid: reuse PR-007 scope authority, reuse PR-008 execution-profile semantics, keep Hub projection target-specific, prohibit authority synthesis/fallback, and require a live ChatGPT-visible scoped transaction before completion. The Plan is not implementation-ready, however, because its declared current-task P0 dependency state conflicts with its proposed execution slices, and because the Task has no authorized implementation target for the actual production Hub projection that the Requirement asks to fix.

Implementation MUST NOT start until the blockers below are resolved and a revised Plan is reviewed again.

## Blocking Finding F1 — Current-task P0 dependencies conflict with proposed implementation entry

### Evidence

The canonical Requirement declares all of the following under `current_task_p0_dependencies`:

```text
HubProjectionWriteOrDeploymentSurface = unresolved_external
ProviderScopeAdmission = active_related_task / PR-007
AgentExecutionProfileContract = active_related_task / PR-008
```

Plan Revision 1 repeats that `HubProjectionWriteOrDeploymentSurface` is a current-task P0 implementation dependency, but then proposes executable S01/S02 repository-owned implementation before those P0 dependencies are resolved.

Current DevForge project-development semantics require Implementation Ready to have no unresolved current-task P0 dependency. A Plan cannot preserve these dependencies as P0 implementation blockers and simultaneously authorize implementation slices around them.

### Required remediation

Make the dependency model internally consistent before Implementation Ready. The revised Plan must choose a semantically valid path:

1. **Keep the current Requirement P0 semantics:** no implementation Slice may become executable until the exact current-task P0 dependencies are resolved and read back; or
2. If repository-owned contract/fixture work is intentionally independent and should be implementable before Hub/PR-007/PR-008 completion, that is an upstream Requirement/decomposition change. It must be resolved at the Requirement/Task boundary rather than silently reclassifying P0 semantics inside Plan remediation.

Plan remediation MUST NOT simply rename a P0 dependency to an acceptance-only dependency if that changes the canonical Requirement meaning.

## Blocking Finding F2 — No authorized implementation target exists for the actual Hub projection fix

### Evidence

The Requirement goal is not merely to document a desired schema. It requires the production model-facing surface to become semantically capable of carrying scoped-development requests and requires live ChatGPT evidence.

Plan D1/D2/D4 can produce useful repository-owned contract fixtures, conformance tests, and a Hub implementation handoff. But the same Plan explicitly states:

```text
production mcp.sentinelx.app Hub source/deployment ← external owner
no writable Hub repository/deployment surface currently available
```

No concrete implementation step identifies an authorized source repository, deployment target, change interface, or external executor that can actually modify the production MCP projection. Therefore S01/S02 can at most improve the handoff contract; they cannot satisfy the requested "directly fix MCP Development Execution Projection" outcome.

A documentation/fixture change in `sentinelx-cloud-core` must not be treated as implementation progress on the production Hub itself.

### Required remediation

Before Plan approval, establish one of the following:

- a writable/authorized Hub source repository and exact implementation seam; or
- an authorized production Hub deployment/configuration interface capable of changing the model-facing tool projection; or
- another independently verified implementation surface owned by the Hub that can consume the versioned target-Agent contract and project the required fields.

The revised Plan must name the exact external implementation boundary and how its revision/deployment/readback evidence is recorded without making `sentinelx-cloud-core` the false owner of Hub code.

If no such surface can be obtained, the current Task cannot honestly be an end-to-end "fix Projection" implementation Task. Narrowing it to contract/handoff-only work would be a material Requirement/task-scope decision and must return upstream rather than be hidden in Plan remediation.

## Blocking Finding F3 — PR-007 / PR-008 are active dependencies, not stable implementation inputs

### Evidence

PR-009 states that it composes PR-007 and PR-008 instead of duplicating them. At this review boundary:

- PR-007 is still in `implementation` and has remaining verification/implementation work;
- PR-008 is in `acceptance` but remains blocked and is not completed/merged as an accepted canonical dependency.

Plan S01 says the current Agent contract source will be explicitly bound, and D3 says to reuse the exact PR-008 output. That is not stable enough while the owning Tasks remain active and may still change under their own Gate semantics.

### Required remediation

The revised Plan must require exact dependency evidence before consuming those semantics as implementation authority. At minimum:

- resolve PR-007/equivalent provider scope admission to a verified stable revision before S04 composition;
- resolve PR-008/equivalent execution-profile contract to a verified stable revision before freezing the dynamic projection contract, or explicitly bind to an immutable reviewed revision with drift invalidation rules;
- require dependency drift to invalidate affected PR-009 fixtures/Plan assumptions rather than silently consuming moving branch state.

## Non-blocking Findings

### N1 — Security/no-fallback boundary is correct

The Plan correctly prohibits caller-minted scope/workspace authority, direct Python allowlist expansion, wrapper execution, provider substitution, and `operator_unrestricted` fallback. Preserve this unchanged.

### N2 — No breaking wire-protocol churn is justified by current evidence

The existing request payload can carry arbitrary mappings, so the Plan is correct not to introduce a breaking request protocol merely to transport scoped fields. A handshake/protocol extension should remain conditional on demonstrated necessity.

### N3 — Live acceptance evidence is correctly stronger than repository assertions

D6/D7 correctly require the actual ChatGPT-visible tool schema and a harmless scoped transaction with terminal scope readback. Repository tests or Agent capability advertisement alone are insufficient.

## Requirement Traceability Assessment

- R1 / A1: direction is sound; PR-007/008 authority is preserved.
- R2-R5 / A2-A3: repository-owned contract/conformance work is technically feasible, but F1/F3 prevent it from becoming implementation-ready under the current dependency state.
- R6-R7 / A4: security boundaries are preserved by the Plan.
- R8 / A5: correctly requires external Hub truth, but F2 shows there is no implementation target yet.
- R9 / A3: conformance regression direction is valid.
- R10 / A5-A9: verification strategy is appropriate, but cannot become executable until the Hub and provider-scope dependencies are resolved.

## Gate Result

```text
Plan Review: Rejected
Current Gate: plan_review_rejected
Implementation Authorized: false
Execution Slice Set: not compiled
```

Canonical next action:

```text
#开发计划修复 PR-009-mcp-development-execution-projection-dynamic-tool-contract-v1
```

If remediation reaches the point where satisfying F1/F2 requires changing the canonical Requirement scope or dependency classification, it must fail closed and return that material decision to the upstream Requirement boundary rather than silently rewriting Requirement semantics.
