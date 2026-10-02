# PR-007 — Host Mutation Scope Control Surface & MCP Admission Bridge V1 — Plan Review R3

## Review State

```yaml
task_id: PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1
review_target: plan
requirement_revision: 2
plan_revision: 3
result: Rejected
finding_classification: plan_local
reviewed_task_head: 250caeb883500d708b7927ae08ff2ff72e79b80d
planning_baseline_main: f7e878f3497582547e5d52cd33b060cae18d2e84
next_gate: plan_review_rejected
next_expected_actor: planner
implementation_authorized: false
execution_slice_set_compiled: false
```

## Decision

**Rejected — Plan-local remediation required.**

Requirement Revision 2 is coherent and the revised architecture is feasible: production `mcp.sentinelx.app` remains an immutable external boundary, the already model-facing `sentinel_local_api` envelope is reused, and the new repository-owned work is limited to an Agent built-in `devforge_runtime` endpoint that composes existing provider authority.

The Plan is not yet safe enough to authorize implementation because three adapter-boundary cases are under-specified. None requires a Requirement change, Hub change, new Task, replacement PR, unrestricted fallback, or duplicate executor.

## What passes review

### P1 — Immutable Hub boundary

**PASS.** Plan Revision 3 no longer requires Hub source/config/schema/deployment mutation and no longer depends on generic `/op mutation_scope` projection.

The live observation used by the Plan is appropriately narrow: the current model-facing `sentinel_local_api` call reached the connected Agent and returned Agent-level `unsupported_op`; final Acceptance must still prove the revised known build through the real model-facing tool.

### P2 — Reuse of provider authority

**PASS.** The Plan correctly preserves `MutationScopeStore`, provider-owned purpose-to-operation-class mapping, exact repository/semantic binding, non-reactivating readback, AppContainer/audit/Job containment, and terminalization as existing authority.

D5 explicitly requires a shared lifecycle service rather than copying `handlers/mutation_scope.py` semantics. D6 requires `execute_scoped` to call the existing profiled scoped execution path rather than create a second runner/sandbox/audit/store.

### P3 — RequestContext direction

**PASS.** Making `local_api` context-aware is the correct seam. The actual outer request remains `op=local_api`; payload values do not mint or replace `request_id`, `opaque_ref`, receive time, or transport operation identity.

### P4 — S01-S04 evidence reuse

**PASS.** Requirement Change Invalidation correctly retains S01-S04 as historical verified prerequisites and does not replay their side effects. The old S05 and Acceptance R1 are no longer current authority.

## Blocking Findings

### F1 — `disabled_ops` can be bypassed unless action admission is explicitly transitive

**Severity: P0 / security boundary**  
**Classification: plan_local**

Current Agent semantics intentionally remove disabled operations from the registry at the end of registry construction so an operation becomes both unadvertised and unreachable. Current PR-007 branch registers both `script_run` and `mutation_scope` as ordinary operations before applying `policy.disabled_ops`.

Plan Revision 3 proposes `devforge_runtime` actions that call their internal lifecycle/scoped-execution implementation directly. Without an explicit transitive rule this creates a second route around the operator switch:

```text
disabled_ops: [mutation_scope]
local_api -> devforge_runtime.provision_scope -> shared lifecycle service   # possible bypass

or

disabled_ops: [script_run]
local_api -> devforge_runtime.execute_scoped -> profiled script handler     # possible bypass
```

This contradicts the existing `disabled_ops` contract that removal is the last word for reachability and contradicts R6/R7/R13 fail-closed/backward-compatibility intent.

**Required remediation:** Plan Revision 4 must define action-level admission/description rules derived from the same Host policy:

1. `disabled_ops` containing `local_api` removes the entire outer operation as today;
2. `disabled_ops` containing `mutation_scope` makes `provision_scope`, `revalidate_scope`, `inspect_scope`, and `terminalize_scope` unavailable through `devforge_runtime` as well;
3. `disabled_ops` containing `script_run` makes `execute_scoped` unavailable through `devforge_runtime` as well;
4. `list`/`describe` must not falsely advertise an action that policy has made unavailable;
5. direct `call` must independently fail closed even if a caller skips `describe`;
6. focused tests must cover all three disable cases plus mixed cases.

The remediation must reuse policy truth, not create a second deny list.

### F2 — `cleanup=false` can leak exact provider workspace/script paths through the new model-facing envelope

**Severity: P0 / authority-information boundary**  
**Classification: plan_local**

D6 currently lists `cleanup` as an allowed caller execution input and proposes forwarding into the existing scoped script path. The current scoped implementation returns `script_path` and `workdir` when `cleanup=false`.

Requirement Revision 2 intentionally exposes bounded receipt evidence (`scope_id`, generation, workspace_id, digests, audit operation identifier) and does not make exact provider workspace/script paths part of the model-facing contract. The new `devforge_runtime` adapter therefore must not accidentally widen the response simply because the reused internal handler has a debugging response mode.

**Required remediation:** Plan Revision 4 must choose and test one fail-closed model-facing rule. Preferred V1 rule:

- `devforge_runtime.execute_scoped` fixes `cleanup=true` internally and rejects caller `cleanup=false` / caller cleanup override;
- response projection must not expose `workdir`, `script_path`, exact workspace path, provider-private roots, or other path authority even if the internal handler later adds debugging fields.

A bounded explicit response projection is required rather than assuming the inner handler's response remains safe forever.

### F3 — Built-in/external endpoint name collision has no deterministic compatibility rule

**Severity: P1 / backward compatibility**  
**Classification: plan_local**

Existing `policy.local_apis` endpoint names are operator-defined. Revision 3 reserves the same flat endpoint name `devforge_runtime` for a built-in provider but does not define what happens if an existing Host already has a configured external endpoint with that name.

Without a rule, implementation could silently shadow an existing external endpoint, silently shadow the built-in endpoint, or route `describe` and `call` inconsistently. Any of those would violate R10/R13's requirement that configured external `local_apis` remain separate and behaviorally compatible.

**Required remediation:** Plan Revision 4 must define one deterministic fail-closed collision policy and tests. A safe V1 option is:

- configured external endpoints retain their existing meaning and are never reinterpreted as built-ins;
- a name collision makes the built-in `devforge_runtime` endpoint unavailable on that Host with a stable diagnostic rather than shadowing the existing external endpoint;
- `list`/`describe`/`call` resolve the same provider deterministically;
- built-in metadata includes a provider kind/contract revision sufficient for Acceptance to prove it reached the built-in endpoint rather than a same-name external profile.

Equivalent behavior is acceptable if it preserves existing external endpoint semantics and cannot route a privileged built-in action ambiguously.

## Requirement Traceability Assessment

- R1-R5: **adequately planned** through retained S01/S02 plus D5/S06 shared lifecycle composition.
- R6-R7: **blocked by F1** until all internal routes preserve `disabled_ops` and fail-closed policy semantics.
- R8: **direction adequate**, but execution adapter remains unapproved until F1/F2 are resolved.
- R9-R10: **direction adequate**, with endpoint admission/detail requiring F1/F3 remediation.
- R11: **adequately planned**; Hub is immutable and only existing interface evidence is claimed.
- R12: **blocked by F2** until the new model-facing execution response is explicitly bounded.
- R13: **blocked by F1/F3** until disable semantics and external/built-in collision behavior are deterministic.
- R14: **adequately planned**.
- R15: **adequately planned**; PR-008/PR-009 are not completion dependencies.

## Required Plan Remediation Scope

Plan remediation is intentionally narrow. Revision 4 should change only the affected adapter decisions/tests:

1. add transitive `disabled_ops` admission and truthfully filtered `describe` semantics;
2. lock `execute_scoped` to bounded cleanup/response projection with no exact path leakage;
3. define built-in/external endpoint collision resolution and built-in identity/version metadata;
4. extend S06/S07 verification cases accordingly.

Do not reopen the Hub direction, rewrite S01-S04, add a second executor/store/audit path, widen an allowlist, or create a new Task/PR.

## Gate Result

```text
Plan Review R3: Rejected
Plan Revision: 3
Plan Approved: false
Implementation Authorized: false
Execution Slice Set: not compiled
Next Gate: plan_review_rejected
Next Actor: planner
```
