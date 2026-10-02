# PR-007 — Host Mutation Scope Control Surface & MCP Admission Bridge V1 — Plan

## Plan State

```yaml
task_id: PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1
stage: implementation
plan_status: approved
implementation_authorized: true
plan_revision: 2
requirement: docs/requirements/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1.md
prior_plan_review: docs/reviews/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-plan-review-r1.md
plan_review: docs/reviews/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-plan-review-r2.md
execution_slice_set: docs/execution/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-slices.yaml
transport: github-pr
pr_number: 7
task_branch: task/host-mutation-scope-control-surface-mcp-admission-bridge-v1
base_branch: main
planning_baseline_main: f7e878f3497582547e5d52cd33b060cae18d2e84
```

## Objective

Close the control-plane admission gap between an SX-HMSA-ready SentinelX Host and the existing scoped execution path without weakening provider-owned authority.

Target composition:

```text
generic control-plane /op relay
→ Agent mutation_scope lifecycle operation
→ MutationScopeStore provider authority
→ execution-time operation-class admission
→ existing script_run scoped_mutation
→ existing AppContainer + audit lifecycle
→ provider terminalization
→ exact, bound, non-reactivating scope readback
```

Plan Revision 2 remediates both blocking findings from Plan Review R1. No implementation is authorized until this revision is reviewed and approved.

## Current Repository Reality

Planning was refreshed against canonical `main@f7e878f3497582547e5d52cd33b060cae18d2e84`.

- PR-005 is merged into canonical `main`; release/runtime work is no longer an open implementation dependency for this Plan.
- `MutationScopeRecord.allowed_operation_classes` is durable authority and participates in the immutable scope digest.
- `MutationScopeStore.provision_scope(...)` normalizes/persists `allowed_operation_classes`, and duplicate same-Attempt provisioning already rejects a changed operation-class set.
- `MutationScopeStore.revalidate_scope(...)` revalidates current scope generation, placement, exact repository binding and semantic lineage, but does not currently require an operation class.
- `MutationScopeStore.read_scope(scope_id)` already exists and is non-reactivating; it verifies record integrity through the canonical store read path but accepts only `scope_id` and therefore is not sufficiently bound for an external lifecycle projection.
- existing `script_run` `scoped_mutation` calls `store.revalidate_scope(...)` before planning/materialization/spawn. That call site is the canonical execution-admission seam to strengthen.
- existing sandbox, audit, placement, scope storage and terminalization remain authoritative and must not be duplicated.
- PR-008 is a separate active dependency for model-facing `script_run` profile projection. PR-007 owns scope lifecycle admission, not Hub tool-schema projection.

## Remediation Traceability

| R1 finding | Revision 2 remediation |
|---|---|
| F1 — durable operation classes are persisted but not consumed | Add provider-owned `revalidate_scope_for_operation(...)` (or semantically equivalent method) that performs normal exact scope revalidation and then requires the canonical `scoped_script` class. Existing `script_run scoped_mutation` must call this method before any audit-start/materialization/sandbox activation/spawn. |
| F2 — D4 proposed a duplicate/stale read seam | Keep existing `read_scope(scope_id)` as canonical raw store read and add/extend a bound read on the same `MutationScopeStore` authority that requires exact generation + repository + semantic binding, remains pure/non-reactivating, and does not establish a second readback store or lifecycle path. |

## Authoritative Decisions

### D1 — One lifecycle operation, no second authority model

Add one Agent operation, provisionally `mutation_scope`, with bounded actions:

```text
provision | revalidate | inspect | terminalize
```

The handler delegates to `MutationScopeStore`. It must not persist a parallel scope ledger, reconstruct placement authority, or execute user code.

### D2 — Caller requests bounded purpose, never operation-class authority

The wire payload MUST NOT accept `allowed_operation_classes` or any equivalent free-form authority field.

Provision accepts only the bounded V1 purpose:

```text
purpose = scoped_script
```

The provider maps this purpose internally to the canonical durable operation class:

```text
scoped_script
```

The mapping is code-owned/provider-owned. Unknown purposes fail closed. Caller-supplied class names are rejected rather than normalized into authority.

### D3 — Operation class is an execution-time admission boundary

Persisting `allowed_operation_classes` is not sufficient. Add a provider-owned admission method semantically equivalent to:

```python
revalidate_scope_for_operation(
    scope_id,
    generation,
    policy,
    repository,
    semantic,
    *,
    required_operation_class="scoped_script",
    provider_protected_roots=...,
) -> MutationScopeRecord
```

Required semantics:

1. reuse the existing exact `revalidate_scope` / `_revalidate_locked` authority path rather than duplicating repository, semantic, placement or lifecycle validation;
2. verify immutable digest and exact scope generation;
3. verify exact repository and semantic lineage;
4. verify the required canonical class is present in durable `record.allowed_operation_classes`;
5. fail closed with a stable scope-admission classification if the class is absent;
6. perform no materialization, audit start, sandbox activation or spawn itself;
7. never accept a caller-defined `required_operation_class` through the external payload.

The existing `script_run` `scoped_mutation` path MUST replace its current plain `revalidate_scope(...)` entry call with this operation-aware admission using the internal constant `scoped_script`.

This check must occur before any operation audit START, evidence materialization, workspace directory creation, AppContainer activation or process spawn.

### D4 — Exact repository + lineage remain mandatory authority inputs

Provision/revalidate/inspect/terminalize parse canonical repository identity and semantic lineage and pass them through the provider-owned scope authority.

Transport `RequestContext` data remains transport-derived. Payload values never override request ID, opaque correlation identity, receive time or operation name.

### D5 — Reuse existing read_scope; add a bound non-reactivating projection

Revision 1 incorrectly stated that no public read seam exists. Canonical reality is:

```python
MutationScopeStore.read_scope(scope_id)
```

Revision 2 preserves that method as the raw authoritative non-mutating store read. For the external lifecycle handler, add or extend a store-level bound read semantically equivalent to:

```python
read_bound_scope(
    scope_id,
    generation,
    repository,
    semantic,
) -> MutationScopeRecord
```

It MUST:

- use the same `MutationScopeStore` state, lock, `_record` and immutable-digest validation path;
- require exact `scope_id + generation`;
- require exact repository identity digest;
- require exact semantic identity digest/project/task/run/attempt[/slice] binding;
- return current or terminal records without changing lifecycle state;
- never call provisioning, revalidation that can evolve authority, placement repair, activation or terminalization;
- never make a terminal/expired/revoked record current;
- fail closed for wrong generation, repository or lineage;
- expose only the bounded response projection defined below.

A separately persisted readback ledger or second source of truth is forbidden.

### D6 — Same-Attempt authority remains immutable

Existing duplicate same-Attempt provisioning behavior remains canonical: the same Attempt can idempotently recover the same current scope only when repository/semantic/placement and the provider-derived operation-class set remain identical.

A repeated request cannot change `allowed_operation_classes`, purpose, workspace authority or scope generation.

### D7 — Existing scoped script remains the only execution path

`mutation_scope` never executes code. Actual execution remains in existing `script_run` with `execution_profile=scoped_mutation` and the existing AppContainer/audit/sandbox path.

No second executor, sandbox, scope store, audit journal or workspace authority may be introduced.

### D8 — External terminalize is not a process-kill API

The lifecycle `terminalize` action does not become a generic in-flight cancellation primitive.

If an active Job/process/sandbox write authority still exists and authoritative runtime-cleanup evidence is unavailable, terminalization must preserve existing fail-closed behavior. Existing scoped execution owns runtime cleanup for its active process tree.

### D9 — Generic Hub operation relay is the V1 scope-admission bridge

Repository-local implementation exposes the Agent lifecycle operation through the existing generic operation dispatch. A dedicated public MCP tool is not required or claimed.

Acceptance must separately verify live Hub relay behavior. Hub inability to route the operation becomes an external dependency, not a reason to weaken Host authority.

### D10 — Registry discoverability is not readiness

Registering `mutation_scope` makes it visible through normal registry-derived `ops_supported`. Existing `disabled_ops` behavior must remove reachability/advertisement.

Actual provisioning/revalidation remains gated by mutation policy/readiness. Dispatchability never implies scope authority is usable.

### D11 — Bounded response projection

Lifecycle responses may expose only orchestration/receipt evidence such as:

```text
scope_id
generation
workspace_id
state
issued_at
expires_at
terminalized_at
scope_digest
exact_workspace_digest
protected_inventory_digest
repository_identity_digest
semantic_identity_digest
allowed purpose identifier (not caller-editable authority)
```

Do not return raw protected-root inventories, exact provider-private policy contents, credentials, tokens, AppContainer secrets or unrestricted filesystem authority.

### D12 — PR-005/PR-008 reconciliation before implementation

Before S01 execution:

1. re-read canonical `main` and use the then-current main as implementation baseline;
2. preserve merged PR-005 packaging/release semantics and do not hard-code a release version;
3. re-read PR-008 state because its known-build/tool-surface work touches adjacent `scoped_script` and capability surfaces;
4. if main or PR-008 materially changes `MutationScopeStore` or the `script_run` admission seam, stop at a Decision Boundary and refresh the Slice inputs before mutation;
5. do not merge or copy PR-008 implementation into PR-007 unless canonical main contains it or an explicitly reviewed dependency reconciliation requires it.

## Payload Contract Direction

Conceptual request shape:

```yaml
op: mutation_scope
payload:
  action: provision | revalidate | inspect | terminalize
  purpose: scoped_script        # provision only
  repository:
    vcs: git
    authority: github.com
    path: owner/repository
  lineage:
    project_id: ...
    task_id: ...
    run_id: ...
    attempt_id: ...
    slice_id: ... | null
  scope_ref:                    # non-provision actions
    scope_id: ...
    generation: 1
```

Forbidden caller authority fields include equivalent forms of:

```text
workspace_id
workspace_root
workspace_path
allowed_write_roots
protected_roots
allowed_operation_classes
required_operation_class
placement_ref
placement_generation
sandbox_identity
scope_digest override
```

## Error Semantics

Reuse existing SX-HMSA classifications where they already express provider failure. Add only thin stable classifications where a new admission distinction is required.

Expected fail-closed families include equivalent forms of:

```text
invalid_payload
HostMutationSandboxUnavailable
HostMutationScopeConflict
HostMutationScopeNotCurrent
HostMutationScopeBindingMismatch
HostMutationScopeOperationNotAllowed
HostMutationScopeTerminalizationFailed
HostMutationScopeStillActive
HostMutationResidualAuthorityDetected
unsupported_op
```

`HostMutationScopeOperationNotAllowed` is illustrative; implementation may reuse an existing binding/admission error only if tests preserve a stable, unambiguous machine classification.

No error permits unrestricted fallback.

## Implementation Slices

### S01 — Authority admission + exact bound readback

Primary surfaces:

```text
src/sentinelx_core/mutation_scope.py
src/sentinelx_core/handlers/scoped_script.py
tests/test_mutation_scope*.py
tests/test_scoped_script_execution.py
```

Outcomes:

- add operation-aware scope revalidation on the canonical store authority;
- change existing scoped `script_run` entry admission to require internal `scoped_script` class;
- prove denial occurs before audit START/materialization/sandbox activation/spawn when durable class is absent;
- preserve existing duplicate same-Attempt class-set immutability;
- reuse existing `read_scope` authority and add exact generation/repository/semantic bound readback without lifecycle mutation;
- wrong generation/repository/lineage fails closed;
- terminal bound inspect returns terminal evidence without reactivation.

Required focused tests:

1. canonical `scoped_script` scope executes through the existing scoped path;
2. a durable scope lacking `scoped_script` is denied before any materialization/spawn/audit START;
3. caller cannot inject arbitrary operation classes or `required_operation_class`;
4. duplicate same-Attempt provision cannot broaden/change class authority;
5. bound inspect rejects wrong generation;
6. bound inspect rejects wrong repository;
7. bound inspect rejects wrong project/task/run/attempt/slice;
8. terminal inspect is pure and non-reactivating.

### S02 — Lifecycle handler + provider-owned purpose mapping

Primary surfaces:

```text
src/sentinelx_core/handlers/<mutation-scope-handler>.py
src/sentinelx_core/handlers/__init__.py
focused handler tests
```

Outcomes:

- bounded `mutation_scope` provision/revalidate/inspect/terminalize actions;
- strict repository/lineage/scope-ref parser;
- provider-owned `scoped_script` purpose → canonical class mapping;
- authority-shaped payload fields rejected;
- inspect uses the S01 bound readback path;
- terminalize remains lifecycle closure, not generic process cancellation;
- RequestContext remains transport authority.

### S03 — Registry/capability/operator contract projection

Primary surfaces:

```text
src/sentinelx_core/handlers/__init__.py
capabilities/help projection as required
README.md
focused registry/disabled_ops tests
```

Outcomes:

- lifecycle op dispatches through normal registry;
- `ops_supported` derives registry truth;
- disabled op is unadvertised and unreachable;
- docs distinguish dispatchability from mutation readiness;
- no dedicated Hub MCP tool claim;
- no fixed host/path/version identity.

### S04 — Existing scoped execution composition + regressions

Outcomes:

- provider-issued lifecycle scope feeds existing profiled scoped execution;
- execution-time class admission remains before material mutation;
- exact repository/semantic binding remains enforced;
- success/timeout/failure terminalization remains authoritative;
- final bound inspect proves terminal state;
- existing AppContainer/audit/Job containment remains unchanged;
- no unrestricted fallback.

### S05 — Live generic Hub `/op` admission evidence

Controlled sequence:

```text
1. resolve a connected Windows Host with verified mutation readiness;
2. obtain supported short-lived generic Hub operation-relay authorization;
3. call mutation_scope/provision through generic /op;
4. verify provider-issued scope identity/bindings;
5. call profiled script_run with exact scope + repository + lineage through an actually supported control surface;
6. call mutation_scope/inspect through generic /op;
7. prove terminal/non-active state and exact binding;
8. prove mismatched lineage/repository attempts fail closed;
9. reconfirm direct Python denial / no unrestricted fallback;
10. run affected SX-HMSA security regressions.
```

PR-008 currently tracks a separate Hub model-facing tool projection dependency. If the generic `/op` path can provision/inspect scope but the model-facing `script_run` surface still cannot carry profiled fields, PR-007 may prove scope admission while the combined end-to-end path remains externally blocked on PR-008. The two external boundaries must not be conflated.

## Verification Matrix

| Case | Expected |
|---|---|
| provision purpose=scoped_script | provider-issued current scope with canonical durable class |
| duplicate same Attempt, same purpose | same scope/workspace authority |
| duplicate same Attempt, changed class/purpose | rejected |
| caller free-form operation class | rejected |
| caller required_operation_class | rejected |
| scope has scoped_script class | scoped script admission succeeds |
| scope lacks scoped_script class | denied before audit START/materialization/spawn |
| mismatched repository | binding failure |
| mismatched task/run/attempt/slice | binding failure |
| stale generation | failure |
| terminal bound inspect | terminal evidence; no state mutation/reactivation |
| wrong generation/repository/lineage inspect | failure |
| expired/revoked/terminal revalidate | non-current failure |
| external terminalize while active runtime authority remains | fail closed; no generic kill semantics |
| disabled lifecycle op | unadvertised + unsupported |
| provider runtime unavailable | fail closed |
| scoped execution failure | no unrestricted fallback |
| generic Hub relay supports lifecycle op | live scope-admission evidence PASS |
| Hub/model-facing profiled script remains unavailable | explicit external dependency; no end-to-end completion claim |

## Regression Requirements

At minimum retain/execute affected checks for:

- mutation scope uniqueness and durable authority;
- operation-class immutable digest participation;
- placement/repository/semantic binding;
- audit START/SPAWN/FINISH ordering;
- Windows AppContainer ACL/Job containment;
- scoped script execution;
- capability advertisement and disabled operations;
- canonical destructive-escape incident fixture `INCIDENT-20260927-D-ROOT-RECURSIVE-DELETE`;
- normal existing operation dispatch compatibility;
- direct Python denial on the final Acceptance Host when Python is not operator-allowed.

Security-sensitive Acceptance uses fresh canonical-host evidence; retained receipts are context, not substitutes.

## Risks and Controls

### Risk A — purpose remains descriptive rather than authoritative
Control: `script_run scoped_mutation` itself consumes the canonical durable class through operation-aware provider admission before any material mutation.

### Risk B — control API becomes authority API
Control: caller chooses bounded purpose only; provider owns class mapping, placement, workspace and scope authority.

### Risk C — readback duplicates authority or reactivates scope
Control: same `MutationScopeStore`, same durable record/digest, bound pure read only; no separate ledger or provisioning call.

### Risk D — external terminalize becomes remote kill
Control: existing runtime cleanup/terminalization semantics remain authoritative; active runtime authority without valid cleanup evidence fails closed.

### Risk E — duplicate execution/sandbox path
Control: lifecycle handler never executes user code; compose existing scoped script path.

### Risk F — Hub ownership overstated
Control: repository boundary remains explicit; live relay/tool evidence required; external blocker retained when unavailable.

### Risk G — branch/main drift
Control: implementation-entry refresh against canonical main and PR-008; Decision Boundary on shared-seam drift.

## Plan Review Questions — Revision 2

Reviewer must specifically verify:

1. Does D3 make `allowed_operation_classes` actual execution authority rather than metadata?
2. Is the required operation class provider/internal only, with no caller widening path?
3. Does the denial happen before audit START, materialization, sandbox activation and spawn?
4. Does D5 reuse the existing `MutationScopeStore.read_scope` authority rather than create a second readback truth path?
5. Are generation, repository and full semantic lineage all required for external inspect/readback?
6. Can terminal inspect remain pure and non-reactivating?
7. Does terminalize remain distinct from in-flight process cancellation?
8. Are PR-008 Hub tool projection and PR-007 scope admission kept as separate dependencies?
9. Is implementation-entry reconciliation against current main sufficient to avoid stale-branch overwrite?

## Remediation Result

Plan Review R1 findings are addressed by Revision 2:

- **F1 addressed:** durable operation classes are explicitly consumed by the canonical scoped execution admission path.
- **F2 addressed:** existing `read_scope(scope_id)` is acknowledged and reused as the canonical authority; the plan adds only exact bound validation/projection semantics on the same store.
- **N1 preserved:** lifecycle terminalize is not a generic remote process-kill API.
- **N2 preserved:** registry discoverability remains separate from readiness.
- **N3 reconciled:** PR-005 is now merged; implementation must use current canonical main.

This remediation changes only the Plan. It does not authorize implementation and does not compile an Execution Slice Set before approval.

## Gate

```text
Plan Revision: 2
Plan Review R2: Approved
Plan Approved: true
Implementation Authorized: true
Current Gate: implementation
Next Actor: implementer
Canonical Next Action: #开发执行 PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1
```
