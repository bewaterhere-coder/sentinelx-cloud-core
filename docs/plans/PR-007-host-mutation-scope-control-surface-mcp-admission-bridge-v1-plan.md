# PR-007 — Host Mutation Scope Control Surface & MCP Admission Bridge V1 — Plan

## Plan State

```yaml
task_id: PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1
stage: plan_review_rejected
plan_status: rejected
implementation_authorized: false
plan_revision: 1
requirement: docs/requirements/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1.md
plan_review: docs/reviews/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-plan-review-r1.md
transport: github-pr
pr_number: 7
task_branch: task/host-mutation-scope-control-surface-mcp-admission-bridge-v1
base_branch: main
```

## Objective

Close the control-plane admission gap between an SX-HMSA-ready SentinelX Host and the existing scoped execution path without weakening provider-owned authority.

Target composition:

```text
generic control-plane /op relay
→ Agent mutation_scope operation
→ MutationScopeStore provider authority
→ existing script_run scoped_mutation
→ existing AppContainer + audit lifecycle
→ provider terminalization
→ non-reactivating scope readback
```

No implementation is authorized until Plan Review approves this Plan and DevForge compiles the durable execution Slice Set.

## Current Reality / Inputs

- Canonical base at planning start: `sentinelx-cloud-core main@732a8dbf292a798af55edbc0abbb2f2070a5a6f9`.
- `SX-HMSA-001` already owns durable scope storage, provider placement, AppContainer sandbox, audit lineage, and scoped `script_run`.
- `Executor.dispatch()` already routes arbitrary registered Agent operation names and supplies immutable `RequestContext` to context-aware handlers.
- Agent `ops_supported` is derived from the operation registry.
- No scope lifecycle operation is currently registered.
- The open-source repository does not own the closed-source Hub/MCP schema.
- SentinelX currently exposes a generic authenticated Hub operation relay suitable for end-to-end validation; its live behavior remains an Acceptance fact to verify, not an implementation assumption to declare complete.
- Active PR #5 owns provider release/install/runtime activation and may change adjacent packaging/documentation surfaces.

## Authoritative Decisions

### D1 — One Agent lifecycle operation, no second authority model

Add one Agent operation, provisionally named:

```text
mutation_scope
```

with an action selector equivalent to:

```text
provision | revalidate | inspect | terminalize
```

The handler delegates to `MutationScopeStore`. It must not persist a parallel scope ledger or reconstruct provider authority in the handler.

### D2 — Caller requests purpose, never operation-class authority

The wire payload must not accept arbitrary `allowed_operation_classes`.

Instead, V1 accepts a bounded provider-recognized purpose enum:

```text
scoped_script
```

The Agent/provider maps that purpose internally to the fixed classes required for current scoped script execution. Unknown purposes fail closed.

The payload also rejects/ignores-as-error any authority-shaped fields such as workspace root/path, protected roots, workspace ID, placement, sandbox identity, or caller-provided digests.

### D3 — Exact repository + lineage are mandatory authority inputs

Provision/revalidate/terminalize must parse a canonical repository identity and semantic lineage and pass them through the existing provider placement/scope validation path.

The handler is `RequestContext`-aware. Transport `request_id`, `opaque_ref`, received time, and op name remain transport-derived and cannot be supplied as payload authority.

### D4 — Add a public non-reactivating scope readback seam

`MutationScopeStore` currently exposes current-scope revalidation but does not provide a bounded public API for reading a terminal scope as terminal evidence.

Add an API equivalent to:

```python
read_scope(scope_id, generation, *, expected_repository=None, expected_semantic=None)
```

Semantics:
- verify durable record integrity and exact generation;
- optionally/mandatorily verify expected repository + semantic binding as required by the control handler;
- return current or terminal state without making it current;
- never repair, reprovision, or reactivate authority;
- never expose provider-private inventory contents.

### D5 — Existing scoped `script_run` remains the only execution path

Do not move sandbox/audit/spawn logic into `mutation_scope`.

The lifecycle operation only supplies/revalidates/reads/terminalizes authority. Actual scoped code execution remains in existing `script_run` with `execution_profile=scoped_mutation`.

### D6 — Generic Hub operation relay is the V1 bridge

The repository-local implementation target is Agent-side operation support and an operation-level contract that can travel over the existing generic Hub relay.

A dedicated public MCP tool is explicitly not required for V1 and must not be claimed.

### D7 — Live bridge proof is mandatory for the MCP-admission claim

Unit tests can prove Agent operation semantics but cannot prove the closed-source Hub forwards them.

Acceptance therefore requires live evidence for:

```text
Hub generic /op
→ mutation_scope provision
→ script_run scoped_mutation using returned scope
→ mutation_scope inspect terminal state
```

If the relay rejects the new op or cannot carry the scoped payload, implementation can still prove the Agent control surface, but the Task cannot receive an unqualified MCP-admission Acceptance. The external dependency must be surfaced explicitly.

### D8 — Bounded response projection

Return only orchestration/receipt evidence needed to bind scope identity and state. Prefer opaque IDs and digests over raw authority internals.

Response projection may include:

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
```

Do not return raw protected-root inventories, sandbox secrets, credentials, environment authority, or tokens.

### D9 — Existing disable/capability semantics remain authoritative

Registering the op makes it visible through the existing registry-derived capabilities. Existing `disabled_ops` behavior must remove both reachability and advertisement.

Provider policy/readiness remains an additional fail-closed admission boundary; registry presence alone is not proof that a requested scope can be provisioned.

### D10 — PR #5 reconciliation before implementation

Before the first `#开发执行`:

1. re-read canonical `main`;
2. re-read PR #5 state and changed surfaces;
3. if PR #5 merged, adapt package/version/docs references to merged reality;
4. if PR #5 remains active but only owns release/activation files, continue without duplicating that work;
5. if PR #5 materially changes a shared registry/protocol/help seam, stop at a Decision Boundary and reconcile the implementation plan/slice inputs before mutation.

PR-007 must not hard-code a release version or turn PR #5 into hidden implementation authority.

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

The exact serialized shape may be refined during implementation only if semantics remain equivalent and Plan Review findings permit it.

Explicitly forbidden authority-shaped request fields include equivalent forms of:

```text
workspace_id
workspace_root
workspace_path
allowed_write_roots
protected_roots
allowed_operation_classes
placement_ref
placement_generation
sandbox_identity
scope_digest overrides
```

## Error Semantics

Reuse existing SX-HMSA classifications where they already express the provider failure. Add thin handler validation classifications only where needed.

Expected fail-closed families include equivalent forms of:

```text
invalid_payload
HostMutationSandboxUnavailable
HostMutationScopeConflict
HostMutationScopeNotCurrent
HostMutationScopeBindingMismatch
HostMutationScopeTerminalizationFailed
HostMutationScopeStillActive
HostMutationResidualAuthorityDetected
unsupported_op
```

No error permits automatic unrestricted fallback.

## Implementation Slices

### S01 — Scope readback + lifecycle control core

Likely surfaces:

```text
src/sentinelx_core/mutation_scope.py
src/sentinelx_core/handlers/<mutation-scope-handler>.py
src/sentinelx_core/handlers/__init__.py (only if required in this slice)
tests/test_mutation_scope*.py
```

Outcomes:
- public, non-reactivating exact scope readback;
- strict payload parser for repository/lineage/scope ref;
- bounded purpose → fixed operation-class mapping;
- provision/revalidate/inspect/terminalize handler behavior;
- `RequestContext` use;
- stable fail-closed errors;
- no caller placement/write-root authority.

Verification:
- same-Attempt duplicate provision returns same current scope;
- conflicting binding fails;
- terminal readback works without reactivation;
- terminalized Attempt cannot reprovision;
- authority-shaped caller fields are rejected.

### S02 — Registry, capability and operator contract projection

Likely surfaces:

```text
src/sentinelx_core/handlers/__init__.py
src/sentinelx_core/handlers/basic.py and/or help projection
README.md
config examples only if policy semantics require it
tests for registry/capabilities/help/disabled_ops
```

Outcomes:
- `mutation_scope` is dispatchable through the normal Agent registry;
- `ops_supported` advertises it from registry truth;
- disabled operation is unadvertised/unreachable;
- help/docs explain Agent operation and generic relay semantics;
- no documentation claims a dedicated Hub MCP tool exists;
- no new host/path/version constants.

### S03 — Existing scoped execution composition

Likely surfaces:

```text
tests/test_scoped_script_execution.py
new focused integration tests
minimal scoped_script changes only if a real composition defect is found
```

Outcomes:
- provisioned lifecycle scope feeds existing `script_run` `scoped_mutation` unchanged in authority semantics;
- exact repository/lineage scope binding enforced;
- scope execution reaches existing AppContainer/audit path;
- success/timeout/failure terminalization remains authoritative;
- post-execution inspect proves terminal state;
- no duplicate sandbox implementation and no unrestricted fallback.

### S04 — Generic Hub `/op` admission evidence + regression closure

This Slice is evidence-heavy and must separate repository implementation from external Hub behavior.

Controlled live sequence:

```text
1. resolve connected Windows Host with verified mutation readiness;
2. obtain short-lived authorized generic Hub operation relay credentials through supported product flow;
3. call Agent `mutation_scope/provision` through generic /op;
4. verify response identity and capability evidence;
5. call existing `script_run` scoped_mutation through generic /op using exact returned scope + repository + lineage;
6. call `mutation_scope/inspect` through generic /op;
7. prove state is terminal/non-active and binding matches;
8. prove a mismatched lineage/path-authority attempt fails closed;
9. run affected SX-HMSA security/regression matrix and compile/import checks.
```

If steps 3 or 5 are unsupported by the external Hub relay:

```text
Agent control surface may be implemented and tested locally
BUT
MCP Admission Bridge acceptance remains blocked by explicit external dependency
```

No dedicated MCP tool or Hub deployment may be inferred from Agent code alone.

## Verification Matrix

| Case | Expected |
|---|---|
| valid provision scoped_script | provider-issued current scope |
| duplicate same Attempt provision | same scope/workspace identity |
| caller workspace/path authority | rejected |
| caller free-form operation classes | rejected |
| mismatched repository | binding failure |
| mismatched task/run/attempt/slice | binding failure |
| stale generation | failure |
| expired/revoked/terminal revalidate | non-current failure |
| terminal inspect | terminal evidence, no reactivation |
| reprovision same completed Attempt | rejected |
| disabled lifecycle op | unadvertised + unsupported |
| provider runtime unavailable | fail closed |
| scoped execution success | existing audit/sandbox path + terminal scope |
| scoped execution failure | no unrestricted fallback |
| generic Hub relay supports new op | live e2e PASS |
| generic Hub relay blocks op/payload | explicit external dependency; no MCP-admission completion claim |

## Regression Requirements

At minimum retain/execute affected checks for:

- mutation scope uniqueness and durable authority;
- mutation placement/binding;
- mutation audit START/SPAWN/FINISH ordering;
- Windows AppContainer ACL/Job containment;
- scoped script execution;
- capability advertisement;
- disabled operations;
- canonical destructive-escape incident fixture `INCIDENT-20260927-D-ROOT-RECURSIVE-DELETE`;
- normal existing operation dispatch compatibility.

Use fresh canonical-host evidence for security-sensitive Acceptance claims; retained SX-HMSA receipts are context, not substitutes for affected fresh checks.

## Risks and Controls

### Risk A — Control API accidentally becomes authority API
Control: purpose enum only; provider computes placement/classes; reject authority-shaped fields.

### Risk B — Terminal readback reopens authority
Control: separate non-reactivating read API; never call provisioning from inspect.

### Risk C — Hub ownership is overstated
Control: repository boundary documented; generic relay live proof required; no dedicated MCP claim.

### Risk D — Duplicate execution/sandbox path
Control: lifecycle handler never executes user code; compose existing scoped `script_run`.

### Risk E — PR #5 overlap/drift
Control: mandatory implementation-entry refresh; reuse merged packaging/docs reality; no version pin.

### Risk F — Mixed fleet false positive
Control: registry-derived op advertisement; older Agent returns `unsupported_op`; no version-only admission.

## Plan Review Questions

Reviewer must specifically challenge:

1. whether `mutation_scope` action-based API is sufficiently narrow;
2. whether `purpose=scoped_script` prevents caller authority expansion;
3. whether terminal readback can be implemented without weakening no-reactivation;
4. whether generic Hub `/op` evidence is sufficient to claim control-plane admission without a dedicated MCP tool;
5. whether Acceptance properly blocks on live Hub relay failure;
6. whether PR #5 creates any shared-surface conflict before implementation.

## Plan Review R1 Result

**Rejected.** Durable findings are recorded in:

`docs/reviews/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-plan-review-r1.md`

Blocking remediation required before another review:

1. enforce the canonical scoped operation class at execution admission; `allowed_operation_classes` must be consumed by `script_run scoped_mutation`, not merely persisted by provisioning;
2. revise D4/S01 to match current repository reality: `MutationScopeStore.read_scope(scope_id)` already exists and must be safely reused/extended with exact generation + repository + semantic binding rather than duplicating readback authority.

No execution Slice Set is compiled for rejected Plan Revision 1.

## Gate

```text
Plan Revision: 1
Plan Approved: false
Implementation Authorized: false
Current Gate: plan_review_rejected
Next Actor: planner
```
