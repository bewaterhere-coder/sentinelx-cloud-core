# PR-007 — Host Mutation Scope Control Surface & MCP Admission Bridge V1 — Plan Review R4

## Review State

```yaml
task_id: PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1
review_target: plan
requirement_revision: 2
plan_revision: 4
result: Approved
reviewed_task_head: 25fd5737c044a06985b82c582eb814adfbd45c05
planning_baseline_main: f7e878f3497582547e5d52cd33b060cae18d2e84
next_gate: implementation
next_expected_actor: implementer
implementation_authorized: true
execution_slice_set: docs/execution/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-r4-slices.yaml
```

## Decision

**Approved.** Plan Revision 4 preserves the Requirement Revision 2 architecture and closes all three Plan Review R3 findings without widening caller authority, modifying the closed-source Hub, or introducing a second mutation authority/execution path.

Canonical `main` remains `f7e878f3497582547e5d52cd33b060cae18d2e84`, equal to the Plan's reviewed baseline. PR #7 remains on the same Task/branch lineage and no new external implementation dependency was introduced.

Approval authorizes only the compiled Revision-4 Execution Slice Set. It does not authorize Hub mutation, unrestricted execution, Acceptance approval, merge/finalization, replay of retained S01-S04 effects, or more than one Slice per manual `#开发执行` invocation.

## R3 Finding Closure

### F1 — `disabled_ops` transitive admission

**CLOSED.** D11 derives built-in action admission from the existing `policy.disabled_ops`; it does not create a second deny-list authority.

The Plan now requires:

- `disabled_ops=[local_api]` to keep removing the entire outer operation through the existing registry path;
- `disabled_ops=[mutation_scope]` to disable all built-in lifecycle actions;
- `disabled_ops=[script_run]` to disable `execute_scoped`;
- `list`/`describe` and direct `call` to use the same policy-derived admission function;
- direct calls to fail closed even when callers skip or cache `describe`.

This preserves the current operator semantic that a disabled operation has no alternate route to the same authority.

### F2 — cleanup/path leakage

**CLOSED.** D6/D13 fix the built-in adapter's inner invocation to `cleanup=true`, reject caller cleanup overrides, and require a positive response projection.

Current scoped execution code confirms why this is necessary and feasible: the inner handler returns provider-private `cwd`/`command`, and additionally returns `script_path`/`workdir` when `cleanup=false`. Revision 4 explicitly treats the inner response as untrusted for model projection and permits only a bounded allowlist of execution/receipt fields. Unknown future fields are dropped by default.

This closes the model-facing authority-information leak without changing the canonical scoped executor.

### F3 — built-in/external endpoint name collision

**CLOSED.** D12 preserves the pre-existing meaning of an operator-configured external endpoint named `devforge_runtime`; the built-in endpoint becomes unavailable on that Host rather than shadowing, merging with, or reinterpreting the external endpoint.

Current `local_api` source resolves configured endpoints directly by operator-defined name, so the collision case is real. Revision 4 makes `list`, `describe`, and `call` provider resolution deterministic and requires built-in Acceptance evidence to prove:

```text
provider_kind=builtin
contract_id=devforge_runtime
contract_revision=1
```

No automatic rename or namespace migration is introduced.

## Architecture / Security Review

### Immutable Hub boundary

**PASS.** No implementation step requires Hub source, configuration, deployment, new Hub-native operation, new model schema field, or dynamic projection support. Final live evidence uses only the already model-visible `sentinel_local_api` envelope.

### Provider-owned authority

**PASS.** `MutationScopeStore` remains the sole scope authority. Lifecycle composition shares the existing parser/store service, while `execute_scoped` reuses the existing profiled scoped executor and exact transport `RequestContext`.

### No duplicate executor / fallback

**PASS.** The Plan forbids shell/exec wrappers, Python allowlist expansion, `operator_unrestricted`, legacy unrestricted fallback, caller-minted workspace/scope authority, duplicate sandbox/audit/store/executor paths, and provider substitution.

### Backward compatibility

**PASS.** Existing configured external `local_apis` retain their existing endpoint/action semantics. Built-in eligibility is additive, policy-bound, collision-safe, and does not make an unconfigured Host mutation-capable.

### Verification observability

**PASS.** S06/S07 include focused policy, collision, projection, scope-binding and security tests. S08 requires known-build activation and real model-facing `sentinel_local_api list/describe/call` evidence, including built-in identity, bounded result, terminal readback and negative checks.

## Requirement Traceability

- R1-R5: adequately covered by retained S01/S02 authority plus D5/S06 shared lifecycle composition.
- R6-R7: adequately covered by D11 and S06/S07 transitive admission/no-fallback checks.
- R8: adequately covered by D6/D13 and S07 canonical scoped-executor composition.
- R9-R10: adequately covered by D2/D3/D7/D11/D12 and S06 endpoint admission/identity rules.
- R11: adequately covered by D1/D10 and S08 immutable-Hub live proof.
- R12: adequately covered by D6/D13 bounded positive response projection.
- R13: adequately covered by D11/D12 mixed-fleet/disabled/collision regressions.
- R14: adequately covered by static review in S06/S07.
- R15: adequately covered by D9; PR-008/PR-009 remain non-blocking related work.

## Execution Authorization Boundary

Plan Review R4 authorizes compilation and incremental execution of:

`docs/execution/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-r4-slices.yaml`

Only new Revision-4 work is executable:

1. S06 — built-in `devforge_runtime` endpoint + lifecycle composition;
2. S07 — `execute_scoped` adapter + bounded projection + no-fallback regressions;
3. S08 — known-build activation + real `sentinel_local_api` end-to-end evidence.

S01-S04 remain retained verified prerequisites and MUST NOT be replayed. The old S05 generic-Hub objective remains superseded.

## Gate Result

```text
Plan Review R4: Approved
Plan Revision: 4
Plan Approved: true
Implementation Authorized: true
Execution Slice Set: required and compiled for Revision 4 before Gate completion
Next Gate: implementation
Next Actor: implementer
```
