# PR-007 — Requirement Revision 2 / Downstream Invalidation

## Disposition

```yaml
task_id: PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1
change_classification: material_requirement_revision
source_command: "#开发 PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1 ..."
requirement_revision: 2
transport_preserved: github-pr
pr_number: 7
branch: task/host-mutation-scope-control-surface-mcp-admission-bridge-v1
prior_stage: acceptance
new_stage: plan_review
prior_plan_revision: 2
new_plan_revision: 3
prior_acceptance: rejected_external_blocker
implementation_execution_authorized: false
```

## Why the Requirement changed

The prior Requirement assumed that PR-007 should prove its lifecycle by sending a newly registered Agent operation (`mutation_scope`) through the closed-source production Hub generic `/op` catalog/dispatcher. Live S05 evidence disproved that assumption: the connected Agent advertised `mutation_scope`, while the Hub catalog did not route it.

The Hub is not owned by this repository and the user has confirmed it is third-party/closed-source with no source or deployment authority available to this project. Requiring a Hub implementation change therefore makes an external component we cannot control part of PR-007's implementation contract.

The replacement direction treats `mcp.sentinelx.app` as an immutable external boundary and reuses an already model-facing stable envelope, `sentinel_local_api`. A fresh live invocation of `sentinel_local_api` reached the connected Agent and returned `unsupported_op`; this proves the Hub already transports the `local_api` operation. Current Agent source explains the failure: `local_api` is registered only when `policy.local_apis` is non-empty. The new work is therefore Agent-owned: provide a bounded built-in `devforge_runtime` endpoint behind the existing `local_api` envelope.

## Changed semantic boundary

Old requirement path (superseded):

```text
ChatGPT/control plane
-> generic Hub /op with op=mutation_scope
-> Agent mutation_scope
-> scoped script_run
-> terminal readback
```

Current requirement path:

```text
ChatGPT sentinel_local_api
-> existing Hub local_api relay (unchanged third-party boundary)
-> Agent built-in devforge_runtime structured endpoint
-> existing MutationScopeStore authority
-> existing scoped script execution path
-> AppContainer + audit + Job containment
-> terminal scope readback
```

The Hub does not need to learn `mutation_scope`, `execution_profile`, `mutation`, `lineage`, or `repository` as new model-facing fields. Those semantics stay inside the existing `sentinel_local_api(... params={...})` envelope and are validated by Agent-owned code.

## Downstream invalidation

### Retained evidence — still applicable

S01-S04 implementation evidence remains reusable because the revised Requirement preserves the same provider-owned security model:

- exact scope/repository/semantic binding;
- operation-class admission;
- `MutationScopeStore` as sole scope authority;
- bounded provision/revalidate/inspect/terminalize semantics;
- existing scoped executor;
- AppContainer/ACL/Job containment;
- audit START-before-materialization/spawn semantics;
- terminal closure and non-reactivating readback;
- no unrestricted fallback.

These receipts are historical verified prerequisites. They MUST NOT be replayed merely because the Requirement changed.

### Invalidated as current authority

The following artifacts/evidence are preserved historically but are no longer current execution/acceptance authority for Requirement Revision 2:

- Plan Revision 2's D9 generic Hub `/op` bridge decision;
- the Revision 2 Execution Slice Set as the current executable Slice Set;
- S05's generic `/op mutation_scope` live-admission objective;
- Acceptance R1's `HubGenericOpProjectionRequired` blocker as the current acceptance disposition.

S05 remains valid evidence about the old assumption: it proved the Hub does not dynamically route the Agent's new operation. It is not evidence that the revised Agent-owned `devforge_runtime` bridge is blocked.

## Related-task impact

- PR-008 may remain related to model-facing `sentinel_script_run` evolution, but PR-007 Revision 2 does not require that tool surface for its end-to-end path.
- PR-009 may remain an independent exploration/task about dynamic projection, but it is no longer a PR-007 implementation or acceptance blocker and no Hub write/deployment binding is required for PR-007.

No mutation to PR-008 or PR-009 is authorized or performed by this PR-007 revision command.

## Security invariants preserved

The revised path MUST NOT introduce or use:

```text
shell/exec wrapper fallback
Python allowlist expansion
operator_unrestricted
legacy_unrestricted_compat fallback
caller-minted scope/workspace authority
caller-selected mutation workspace
caller-defined operation classes
duplicate scope store
duplicate sandbox/executor
duplicate audit authority
Hub source/deployment mutation
```

`devforge_runtime.execute_scoped` must compose the existing scoped execution path rather than implement a second process runner.

## Workflow effect

This is an explicit same-task Requirement revision under the existing PR #7 lineage. Requirement Revision 2 invalidates the prior Plan approval and current Acceptance applicability, so the Task returns to orchestration-side Plan Review after Plan Revision 3 is persisted and read back.

No implementation is authorized by this invalidation record. A new Plan Review is required before a new current Execution Slice Set can be compiled or implementation resumed.

No completion claim.
