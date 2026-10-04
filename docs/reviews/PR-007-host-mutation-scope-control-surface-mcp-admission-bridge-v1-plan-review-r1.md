# PR-007 — Host Mutation Scope Control Surface & MCP Admission Bridge V1 — Plan Review R1

## Review State

```yaml
task_id: PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1
review_target: plan
plan_revision: 1
result: Rejected
reviewed_task_head: 9afd06cb28f7e0aea390b9bcbc41120a99ee0de9
runtime:
  devforge_version: v2.9.0
  devforge_revision: 39f50caeb2055c76bf91014654886980641834db
  project_development_workflow: 1.9
  review_contract: 1.3
next_gate: plan_review_rejected
next_expected_actor: planner
```

## Scope Reviewed

- Canonical Requirement: `docs/requirements/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1.md`
- Canonical Plan: `docs/plans/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-plan.md`
- Current `sentinelx-cloud-core/main`: `732a8dbf292a798af55edbc0abbb2f2070a5a6f9`
- Active related Task PR #5 remains open and owns release/install/runtime-activation semantics.
- Current SentinelX control surface exposes the short-lived REST API-key flow for the generic `POST /op` relay, so the Plan's live generic-relay validation direction is feasible and is not a rejection reason.

## Decision

**Rejected.**

The overall direction is valid: expose a narrow Agent lifecycle operation, preserve provider-owned scope authority, compose the existing scoped executor, and require live generic-Hub evidence before claiming MCP admission. However, Plan Revision 1 contains two implementation-shaping gaps that affect the security boundary and repository reality. Implementation MUST NOT start until both are remediated and the revised Plan is reviewed again.

## Blocking Finding F1 — Operation-class authority is persisted but not consumed by the scoped executor

### Evidence

`MutationScopeStore.provision_scope(...)` normalizes and persists `allowed_operation_classes`, and same-Attempt retries compare the stored classes. That establishes durable metadata/authority intent.

Current `script_run` `scoped_mutation` flow revalidates the scope and proceeds into audit, AppContainer activation, materialization and spawn, but does not require or consume an expected operation class from the scope record. The Windows sandbox activation/spawn path likewise validates scope/sandbox/audit binding but does not establish that the current operation is included in `allowed_operation_classes`.

Therefore Plan D2's current shape:

```text
purpose=scoped_script
→ provider maps to fixed allowed_operation_classes
```

is insufficient by itself. Without an execution-time check, the fixed class can become recorded metadata rather than enforced authority.

### Required remediation

Revise the Plan so the provider-owned scope admission path **consumes** the operation class before any material mutation. A valid direction is one of:

```text
revalidate_scope_for_operation(..., required_operation_class="scoped_script")
```

or an equivalent provider-owned admission method that:

1. revalidates exact scope generation, repository and semantic lineage;
2. verifies the required canonical operation class is present in the durable scope authority;
3. fails closed before audit/materialization/spawn when it is absent;
4. does not accept a caller-defined/free-form operation class;
5. is actually called by the existing `script_run` `scoped_mutation` path.

Required verification must include at least:

- a scope provisioned for the canonical `scoped_script` purpose can execute scoped script;
- a scope whose durable class does not authorize scoped script is rejected before materialization/spawn;
- caller-supplied arbitrary class names cannot broaden authority;
- duplicate same-Attempt provisioning cannot change the authorized class set.

This is a Plan Review blocker because it is the mechanism that makes the proposed purpose enum an authorization boundary rather than a descriptive field.

## Blocking Finding F2 — Plan D4 is based on stale repository reality

### Evidence

Plan D4 states that `MutationScopeStore` "currently ... does not provide a bounded public API for reading a terminal scope" and proposes adding an API equivalent to `read_scope(...)`.

Current `main` already contains:

```python
def read_scope(self, scope_id: str) -> MutationScopeRecord:
    """Read authoritative state without changing lifecycle state."""
```

That existing seam is non-reactivating, but it is **not sufficiently bound for the new external control surface** because it accepts only `scope_id`; it does not verify generation, repository identity, or semantic lineage.

### Required remediation

Revise D4 and S01 against current reality:

- reuse/extend the existing `read_scope` seam or add a distinctly named bound wrapper;
- require exact `scope_id + generation` and expected repository + semantic binding for the external lifecycle projection;
- preserve pure read semantics: inspect/readback must not provision, reactivate, advance lifecycle state, or silently repair authority;
- return terminal/current evidence only after immutable digest and binding checks;
- add wrong-generation, wrong-repository and wrong-lineage tests;
- avoid creating a duplicate readback truth path.

## Reviewer Notes — Non-blocking but must remain explicit

### N1 — External terminalize is not in-flight cancellation

Current provider semantics already fail closed when active Job/process or sandbox write authority remains and no authoritative runtime-cleanup callback is available. The revised Plan should state that the lifecycle control operation does not become a generic remote process-kill path. Existing scoped execution remains owner of runtime cleanup for an active execution.

### N2 — Capability readiness model is acceptable

The Agent already separates registry-derived `ops_supported` from readiness-gated `execution_features.host_mutation_sandbox_v1` / `pre_execution_audit_lineage_v1`. The revised Plan may keep the lifecycle op registry-derived, provided admission still checks mutation readiness and documentation does not equate "op is dispatchable" with "scoped mutation is runtime-ready".

### N3 — PR #5 overlap is currently controlled

PR #5 remains open and currently owns packaging/release/install/runtime activation. No product-code overlap requiring Task cancellation was found at this review boundary. The existing implementation-entry reconciliation rule should remain.

## Requirement Traceability Assessment

- R1/R2/R3/R4: direction is viable, but F1 blocks approval because purpose-to-authority enforcement is incomplete.
- R5: viable after F2 corrects the existing readback seam and exact binding requirements.
- R6/R7/R8/R9: architecture is compatible with current readiness, registry, sandbox and no-fallback behavior.
- R10/R11: generic `/op` validation is a valid external acceptance boundary; no dedicated closed-source Hub tool may be inferred.
- R12/R13/R14: bounded evidence/backward-compatibility/no-hardcoded-identity direction is acceptable.

## Gate Result

```text
Plan Review: Rejected
Current Gate: plan_review_rejected
Implementation Authorized: false
Execution Slice Set: not compiled
```

Canonical next action:

```text
#开发计划修复 PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1
```
