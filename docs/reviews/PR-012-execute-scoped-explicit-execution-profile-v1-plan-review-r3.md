# PR-012 — execute_scoped Explicit Execution Profile Schema & End-to-End Propagation V1 — Plan Review R3

## Review State

```yaml
task_id: PR-012-execute-scoped-explicit-execution-profile-v1
review_target: plan
requirement_revision: 1
task_blob_sha: cdb16d3961850f30c5cad5ac7a404707345addb9
plan_revision: 3
plan_blob_sha: 675cb684561bf1d1bad3b0e673f384c4b4833294
reviewed_task_head: cc080f8037fc8f5e5fec93a008dd3ece112a865e
result: Approved
runtime:
  devforge_version: 2.39.0
  devforge_revision: 6b11d1615a1bb1492a2b09e1059b51f75f9c285b
  project_development_workflow: "2.1"
  review_contract: "1.3"
  slicing_contract: "1.1"
next_gate: implementation
next_expected_actor: implementer
```

## Decision

**Approved.**

Plan Revision 3 correctly withdraws the former independent-Codex prerequisite, preserves Requirement Revision 1, and reduces implementation to one bounded schema/adapter/test/documentation Slice. The Plan does not weaken existing scope, audit, firewall, disabled-operation, repository-lineage or executor authority and does not introduce a second executor or a compatibility default.

Approval does not claim that the currently deployed Agent already exposes a compatible `execution_profile` field. If the implementation command cannot obtain an admitted mutation route under the current Host contracts, execution must stop as `BlockedByTool`/equivalent without Plan churn, generic script fallback, source-checkout mutation, unrestricted execution, provider escalation or permission expansion.

Live installation/restart and end-to-end scoped execution remain Acceptance-owned evidence under AC6 and are not part of implementation Slice completion.

## R1/R2 Finding Re-evaluation

### F01 — independent Codex prerequisite

**Closed as an invalid review constraint.**

The Requirement never required a separate Codex channel. Review Correction R3 explicitly withdraws that requirement. Plan R3 now distinguishes three things correctly:

1. the product defect: `execute_scoped` does not expose/require the explicit profile;
2. implementation admission: use an already-authorized restricted development route when one exists, otherwise stop before mutation;
3. activation/physical proof: verifier-owned Acceptance after exact-candidate installation authority is available.

The absence of a currently compatible self-hosting execution interface is therefore an execution availability constraint, not a reason to require a new agent platform and not a Plan design defect.

### F02 — activation mixed into implementation

**Closed.**

AC6 is explicitly separated from S01. Exact-candidate activation, restart, live `local_api.describe`, harmless scoped marker execution, audit readback and terminal scope evidence are verifier-owned Acceptance work. Missing activation authority blocks Acceptance rather than causing implementation to self-deploy.

### F03 — insufficient test traceability

**Closed.**

The Plan names the concrete focused modules and existing test anchors, maps schema projection, adapter propagation, invalid-value zero-call behavior, downstream-profile rejection, disabled-operation preservation and local_api routing to B1–B7 / AC1–AC5, and preserves physical evidence as non-mockable AC6.

## Review Checks

### Solution direction

**Pass.** The change is localized to the existing `devforge_runtime` builtin provider and its existing profiled script adapter. Current main confirms `_EXECUTE_SCOPED_ALLOWED`, `_EXECUTE_SCOPED_REQUIRED` and the `execute_scoped` action schema omit `execution_profile`, while the adapter hard-codes `scoped_mutation`. Plan R3 changes that exact seam rather than adding a parallel executor.

### Scope control

**Pass.** Write scope is limited to the existing provider adapter, focused tests and directly related compatibility documentation. No Hub modification, dynamic tool registry, generic `script_run` redesign, new profile, scope minting mechanism, firewall change, permission expansion or unrestricted fallback is authorized.

### Technical feasibility

**Pass.** `DevforgeRuntimeProvider.describe()` already derives its required parameter projection from `_ACTION_SCHEMAS[action]["required"]`, so adding the required field to the canonical schema updates both advertised params and validation source consistently. The adapter already has one explicit payload handoff to `profiled_script_handler`; validating and propagating the caller value there is a bounded change.

### Requirement traceability

**Pass.** B1/AC1 bind schema + describe projection; B2/AC2 bind exact propagation; B3/B4/B7/AC3 bind missing/invalid rejection before executor invocation; B5 binds downstream profile readback; B6/AC4 preserve fail-closed policy/scope/audit/firewall behavior; AC5 names focused repository checks; AC6 remains independent live Acceptance.

### Verification realism

**Pass.** Unit/integration tests are sufficient for AC1–AC5 but are explicitly insufficient for AC6. This prevents mock-only evidence from replacing the live deployed-interface proof.

### Compatibility behavior

**Pass.** Old omitted-profile clients intentionally fail. The Plan forbids a silent default, which matches the Requirement's explicit-profile contract. `operator_unrestricted`, `read_only`, null, non-string and unknown values are rejected before the existing executor is called.

### Concurrent PR overlap

**Pass with implementation-entry revalidation.** PR-011 is open at `a4382230d39f7b2ea3d97c657dc545f5ed9085dc` but its current changed-file set does not overlap `src/sentinelx_core/handlers/devforge_runtime.py` or `tests/test_devforge_runtime_local_api.py`. Plan R3 still correctly requires overlap/state revalidation before mutation and forbids transport sharing.

## Slice Compilation Guidance

Compile one Slice only:

- **S01** — add required explicit `execution_profile=scoped_mutation` schema/parameter support, validate and propagate the exact caller value through the existing adapter, extend focused regression/integration coverage, and update directly relevant compatibility documentation.

S01 must preserve the canonical transport, current scope/audit/firewall authority, disabled-operation semantics and existing bounded result projection. It must not install/restart the live Agent or claim AC6.

## Gate Result

```text
Plan Review R3: Approved
Requirement Revision: 1
Plan Revision: 3
Plan Approved: true
Execution Slice Set: required and compiled by this review transition
Next Gate: implementation
Next Slice: S01
Next Actor: implementer
```

No product implementation is executed by this review.
