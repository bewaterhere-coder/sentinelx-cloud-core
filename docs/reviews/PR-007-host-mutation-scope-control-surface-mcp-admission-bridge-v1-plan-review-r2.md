# PR-007 — Host Mutation Scope Control Surface & MCP Admission Bridge V1 — Plan Review R2

## Review State

```yaml
task_id: PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1
review_target: plan
plan_revision: 2
result: Approved
reviewed_task_head: afc97d03c9e88adccab257f45f2c018112518abd
planning_baseline_main: f7e878f3497582547e5d52cd33b060cae18d2e84
next_gate: implementation
next_expected_actor: implementer
implementation_authorized: true
```

## Decision

**Approved.** Plan Revision 2 closes both blocking findings from Plan Review R1 without widening caller authority or creating a second scope/readback truth path.

Approval authorizes implementation only through the compiled durable Execution Slice Set. It does not approve Acceptance, merge, Hub changes, unrestricted execution, caller-minted scope authority, or any bypass of the existing AppContainer/audit/scope boundaries.

## R1 Finding Closure

### F1 — Operation-class authority must be consumed at execution time

**Status: Closed by Plan Revision 2.**

Current canonical code confirms the repository reality used by the revised Plan:

- `MutationScopeRecord.allowed_operation_classes` is durable immutable scope authority;
- `provision_scope(...)` persists the normalized class set and rejects same-Attempt retries that request a different class set;
- `revalidate_scope(...)` validates generation/repository/semantic/placement state but does not currently require an operation class;
- existing `script_run scoped_mutation` calls `store.revalidate_scope(...)` before audit evidence preparation, sandbox activation, materialization and spawn.

Revision 2 therefore chooses the correct strengthening seam: a provider-owned operation-aware revalidation method that reuses canonical scope revalidation and then requires the internal canonical `scoped_script` class. The existing scoped execution entry must call it before audit START, evidence materialization, workspace materialization, sandbox activation or spawn.

The caller is not permitted to submit `allowed_operation_classes` or `required_operation_class`; the external lifecycle API accepts only bounded `purpose=scoped_script`, and the provider owns the purpose-to-class mapping.

This makes the durable class an execution authorization boundary rather than descriptive metadata.

### F2 — Existing `read_scope(scope_id)` must be reused

**Status: Closed by Plan Revision 2.**

Current canonical code contains the existing non-reactivating `MutationScopeStore.read_scope(scope_id)` method. Revision 2 explicitly preserves that method and the same `MutationScopeStore` as the single read authority.

The proposed external bound read adds exact validation for:

- scope generation;
- repository identity digest;
- semantic project/task/run/attempt[/slice] binding;
- immutable record integrity.

It remains a pure read: it must not provision, reactivate, evolve placement authority, repair authority, terminalize, or create a second persisted readback ledger.

Wrong generation/repository/lineage and terminal-state behavior are explicitly covered by the S01 verification matrix.

## Reviewer Notes

### N1 — Terminalize remains lifecycle closure, not process cancellation

Preserved. Revision 2 explicitly prohibits treating the lifecycle operation as a generic remote kill API. Active runtime authority without authoritative cleanup evidence remains fail-closed.

### N2 — Registry discoverability remains distinct from readiness

Preserved. `mutation_scope` may be registry-visible while actual scope provisioning/revalidation remains gated by Host mutation readiness/policy.

### N3 — PR-005 reconciliation is resolved

PR-005 is merged in canonical `main@f7e878f3497582547e5d52cd33b060cae18d2e84`. Revision 2 no longer treats it as an active implementation dependency and preserves its release/runtime semantics.

### N4 — PR-008 remains a separate external/tool-surface dependency

PR-007 may implement and prove provider-owned scope lifecycle admission independently. It must not claim the combined model-facing profiled execution path complete while PR-008 remains blocked on Hub projection.

### N5 — Task branch is behind current main

The PR transport was created from an older base revision. This is not a Plan rejection because D12 explicitly requires an implementation-entry refresh against current canonical main and PR-008 before product-code mutation.

The compiled Slice Set therefore treats baseline reconciliation as a hard S01 entry gate. If current main/PR-008 materially changes `MutationScopeStore`, `scoped_script`, registry or capability seams, execution must stop at a Decision Boundary rather than overwrite or silently transplant stale code.

## Requirement Traceability Assessment

- R1/R2/R3/R4: **planned adequately** — bounded lifecycle operation, provider-only purpose/class mapping, exact repository/semantic binding and idempotent same-Attempt semantics are explicit.
- R5: **planned adequately** — existing read authority is reused with exact bound pure read semantics.
- R6/R7/R8: **planned adequately** — readiness stays fail-closed, unrestricted fallback remains forbidden, existing executor/sandbox/audit path remains canonical.
- R9: **planned adequately** — registry-derived discoverability and disabled-op behavior are explicit.
- R10/R11: **planned adequately with external Acceptance dependency** — generic Hub relay must be proven live; closed-source Hub capability must never be inferred from Agent source.
- R12/R13/R14: **planned adequately** — bounded evidence, compatibility and no fixed deployment identity remain explicit.

## Execution Authorization

Plan Review R2 authorizes compilation/execution of the durable slices in:

`docs/execution/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-slices.yaml`

Execution remains incremental and bounded:

1. S01 — authority admission + exact bound readback;
2. S02 — lifecycle handler + provider-owned purpose mapping;
3. S03 — registry/capability/operator contract projection;
4. S04 — existing scoped execution composition + security regressions;
5. S05 — live generic Hub `/op` admission evidence.

S05 may end in an explicit external blocker without invalidating repository-local implementation if the closed-source Hub cannot relay the required operation/payload. No fallback is authorized.

## Gate Result

```text
Plan Review R2: Approved
Plan Revision: 2
Plan Approved: true
Implementation Authorized: true
Next Gate: implementation
Next Actor: implementer
```
