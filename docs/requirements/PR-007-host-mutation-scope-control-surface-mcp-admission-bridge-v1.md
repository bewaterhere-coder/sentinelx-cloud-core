# PR-007 — Host Mutation Scope Control Surface & MCP Admission Bridge V1

## State

```yaml
project_id: sentinelx-cloud-core
task_id: PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1
title: Host Mutation Scope Control Surface & MCP Admission Bridge V1
requirement_revision: 2
development:
  stage: acceptance
  gates:
    requirement_ready: true
    plan_approved: true
    acceptance_approved: false
    completion_verified: false
  next_expected_actor: verifier
transport:
  type: github-pr
  pr_number: 7
  branch: task/host-mutation-scope-control-surface-mcp-admission-bridge-v1
  base_branch: main
artifacts:
  plan: docs/plans/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-plan.md
  plan_review: docs/reviews/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-plan-review-r4.md
  execution_slice_set: docs/execution/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-r4-slices.yaml
  requirement_change_invalidation: docs/reviews/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-requirement-r2-invalidation.md
  acceptance_review: docs/reviews/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-acceptance-r2.md
  acceptance_transition_receipt: docs/reviews/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-acceptance-r2-transition-receipt.yaml
  acceptance_repair_checkpoint: docs/checkpoints/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-acceptance-r2-repair-completed-20261003.yaml
  acceptance_repair_transition_receipt: docs/reviews/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-acceptance-r2-repair-transition-receipt.yaml
historical_artifacts:
  prior_plan_review: docs/reviews/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-plan-review-r3.md
  prior_execution_slice_set: docs/execution/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-slices.yaml
  prior_acceptance: docs/reviews/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-acceptance-r1.md
related_tasks:
  builds_on:
    - SX-HMSA-001
  non_blocking_related:
    - PR-008-provider-execution-profile-tool-surface-alignment-v1
    - PR-009-mcp-development-execution-projection-dynamic-tool-contract-v1
  completed_related:
    - PR-005-provider-capability-release-runtime-activation-v1
```

## Problem

`SX-HMSA-001` and the first PR-007 implementation pass established provider-owned mutation scope, exact repository/semantic binding, Windows AppContainer enforcement, pre-execution audit lineage, bounded lifecycle control and scoped script execution.

The remaining problem is no longer the Host mutation authority. It is how ordinary ChatGPT can reach that authority through a control surface that this project actually owns.

The previous Requirement assumed a newly registered Agent operation (`mutation_scope`) could be sent through the production Hub generic `/op` relay merely because the Agent advertised it. Live S05 evidence disproved that assumption: the Agent advertised `mutation_scope`, but the closed-source Hub catalog/dispatcher did not route it.

`mcp.sentinelx.app` is a third-party closed-source external boundary for this project. PR-007 has no Hub source/deployment authority and MUST NOT make a Hub implementation change a prerequisite for completion.

The Hub already exposes the stable model-facing `sentinel_local_api` envelope with:

```text
operation = list | describe | call
endpoint
 action
params = structured object
```

A live invocation reached the connected Agent and returned `unsupported_op`, proving the Hub already transports `local_api`. Current Agent code registers `local_api` only when host-configured `policy.local_apis` is non-empty. The revised task therefore owns only the Agent-side gap: expose a bounded built-in `devforge_runtime` endpoint through the existing `local_api` operation and compose existing provider authority/execution without adding a second executor.

## Goal

Allow ordinary ChatGPT to perform one complete, provider-authorized scoped development transaction through an immutable existing Hub interface:

```text
ChatGPT sentinel_local_api
→ existing Hub local_api relay (unchanged)
→ Agent built-in devforge_runtime endpoint
→ existing MutationScopeStore provider authority
→ existing scoped script execution path
→ AppContainer + audit + Job containment
→ terminal scope read-back
```

The bridge must preserve every accepted SX-HMSA/PR-007 security boundary. It must not create caller-owned workspace authority, a second scope model, a second executor, or any unrestricted fallback.

## Required Behavior

### R1 — Canonical provider-owned mutation scope remains unchanged

`MutationScopeStore` remains the sole producer/store of mutation authority. Existing bounded lifecycle semantics remain canonical:

```text
provision
revalidate
inspect/readback
terminalize
```

The already implemented `mutation_scope` Agent operation may remain as an Agent/internal compatibility control surface, but PR-007 completion no longer depends on the Hub projecting that operation by name.

### R2 — Provider-only mutation authority

`provision_scope` remains the only producer of mutation authority.

The caller MUST NOT provide or override:

```text
workspace_id
workspace_root
exact workspace path
allowed write roots
protected roots
placement generation
scope digest
protected inventory
sandbox identity
AppContainer identity
free-form allowed operation classes
required operation class
```

The external envelope may request only the bounded V1 purpose `scoped_script`; provider code maps it to the canonical internal operation class.

### R3 — Exact repository and semantic lineage binding

Provisioning, execution and all later authority-sensitive operations bind to:

```text
repository:
  vcs
  authority
  canonical path

lineage:
  project_id
  task_id
  run_id
  attempt_id
  optional slice_id
```

Repository or lineage mismatch fails closed. Payload identity MUST NOT override immutable transport `RequestContext` identity such as request ID, opaque correlation value, receive time, or the actual outer operation.

### R4 — Idempotent same-Attempt provisioning

A repeated valid provision request for the same repository + Attempt[/Slice] + provider placement authority returns the same current scope/workspace authority after live revalidation.

It MUST NOT mint a competing current scope or broaden authority.

### R5 — Non-reactivating state read-back

Bounded read-back for exact `scope_id + generation + repository + lineage` returns current or terminal state without reactivating authority.

Terminal, revoked or expired authority remains non-reactivatable.

### R6 — Fail-closed policy and readiness behavior

When scoped mutation is unconfigured, disabled, runtime-unready, stale, expired, revoked, conflicting, binding-invalid, or unavailable on the current platform, all `devforge_runtime` mutation actions fail closed with stable machine-readable classification.

The built-in endpoint MUST NOT imply usable mutation authority merely because `local_api` is routable.

### R7 — No unrestricted fallback

Failure of provisioning, revalidation, scoped execution, audit, AppContainer enforcement, process containment, terminalization, endpoint admission, or read-back MUST NEVER fall back to:

```text
operator_unrestricted
legacy_unrestricted_compat
ordinary exec/shell execution
Python allowlist expansion
caller-selected workspace mutation
```

### R8 — Compose the existing scoped executor

`devforge_runtime.execute_scoped` MUST reuse the existing scoped script execution implementation. It must not introduce another process runner, sandbox, audit journal, workspace authority or terminalization path.

The existing scoped path remains responsible for:

- live scope revalidation and operation-class admission;
- durable forensic script evidence;
- durable audit START before materialization/spawn;
- AppContainer + ACL + Job containment;
- process evidence;
- terminalization before successful completion.

The adapter may inject the internal fixed `execution_profile=scoped_mutation`; the caller does not choose or override an unrestricted profile.

### R9 — Existing `local_api` envelope is the model-facing transport contract

PR-007 reuses the already model-facing `sentinel_local_api` tool / Agent `local_api` operation. It does not add a new Hub tool or require a Hub schema change.

The Agent exposes one built-in endpoint:

```text
endpoint = devforge_runtime
```

with bounded actions equivalent to:

```text
provision_scope
revalidate_scope
inspect_scope
terminalize_scope
execute_scoped
```

`operation=list` and `operation=describe` MUST reveal only the bounded endpoint/action contract available on that exact Agent/Host.

### R10 — Built-in endpoint admission is provider-controlled and opt-in

`devforge_runtime` is an Agent-owned built-in endpoint, not a host-configured arbitrary socket target.

It is exposed only when the existing provider mutation policy constitutes explicit Host opt-in for scoped mutation. A host that has not enabled/configured scoped mutation MUST NOT gain mutation authority merely because a newer Agent ships the endpoint.

Normal host-configured `local_apis` remain separate and backward compatible.

### R11 — Immutable closed-source Hub boundary

This repository treats production `mcp.sentinelx.app` as an immutable external dependency whose existing public interface may be consumed but not changed by this Task.

PR-007 MUST NOT require or claim:

```text
Hub source modification
Hub deployment/config mutation
new Hub-native mutation_scope operation
new dedicated sentinel_mutation_scope tool
new sentinel_script_run schema fields
Hub dynamic projection support
```

Live acceptance proves only that the pre-existing `sentinel_local_api` envelope reaches the exact connected Agent and can carry the bounded Agent-owned endpoint contract.

### R12 — Durable diagnostic evidence

Lifecycle responses expose only bounded orchestration/receipt evidence equivalent to:

```text
scope_id
generation
workspace_id when contractually required
state
issued/expires/terminalized timestamps
scope digest
workspace digest
protected-inventory digest
repository/semantic binding digests
audit operation identifier where applicable
```

Raw protected inventories, credentials, tokens, private keys, environment secrets, AppContainer secrets and unrestricted filesystem authority MUST NOT be returned.

### R13 — Backward compatibility and mixed fleet

Existing public/read-only/file/Git/service operations keep their prior behavior.

Existing configured external `local_apis` continue to use their declared endpoint/action allowlists. The built-in endpoint does not reinterpret or widen those profiles.

Older/incompatible Agents may return `unsupported_op` for `local_api`; Hosts with no eligible endpoint/action must remain fail-closed. One capable Agent MUST NOT make another Agent mutation-capable.

### R14 — No hard-coded deployment identity

No fixed host ID, hostname, workspace path, installation path, release version, user identity, credential or token becomes canonical authority.

### R15 — PR-008 / PR-009 are not PR-007 completion dependencies

PR-008 may continue evolving the dedicated model-facing `sentinel_script_run` contract and PR-009 may continue exploring projection architecture, but PR-007's revised end-to-end path does not require either Hub projection change.

The revised PR-007 acceptance path uses `sentinel_local_api` plus Agent-owned `devforge_runtime` and therefore must be independently completable within this repository plus the already existing Hub interface.

## Non-Goals

- Modifying production Hub source, deployment or schema.
- Designing a general dynamic Hub tool-projection system.
- Replacing all SentinelX tools with `local_api`.
- Redesigning `MutationScopeStore`, placement, AppContainer, audit or terminalization semantics.
- Adding Linux/macOS scoped-mutation enforcement in V1.
- Adding shell/exec/Python allowlist escape hatches.
- Making caller-supplied paths or operation classes authoritative.
- Creating a duplicate sandbox, executor, scope ledger or audit subsystem.
- Replacing PR-005 release/install/runtime-activation work.

## Requirement Change / Evidence Invalidation

Canonical change record:

`docs/reviews/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-requirement-r2-invalidation.md`

Disposition:

- S01-S04 evidence is retained as verified prerequisite evidence and MUST NOT be replayed.
- Plan Revision 2 is historical and no longer approved/current for Requirement Revision 2.
- the old Execution Slice Set is historical and not current execution authority.
- S05 remains truthful historical evidence that generic `/op mutation_scope` was not projected, but its objective is superseded.
- Acceptance R1 remains truthful historical evidence for Requirement Revision 1, but its `HubGenericOpProjectionRequired` result is not current Acceptance authority for Revision 2.

## Requirement Readiness Evidence

```yaml
depth: deep
behavior_sensitive: true
behavior_examples:
  - id: R2-example
    sequence: "ChatGPT calls sentinel_local_api endpoint=devforge_runtime action=provision_scope with repository + project/task/run/attempt + purpose=scoped_script -> Agent returns provider-issued scope/workspace identity; caller provides no workspace path or operation class."
  - id: R4-example
    sequence: "The same Attempt repeats provision before terminalization -> provider revalidates and returns the same current scope; no second active scope exists."
  - id: R8-example
    sequence: "ChatGPT calls devforge_runtime execute_scoped with exact provider-issued scope + repository + lineage + harmless script -> adapter injects scoped_mutation internally -> existing AppContainer/audit path executes -> existing executor terminalizes scope."
  - id: R9-example
    sequence: "sentinel_local_api list/describe reveals devforge_runtime and its bounded actions on an eligible Host -> provision_scope -> execute_scoped -> inspect_scope proves terminal state, without any new Hub tool/schema."
invariants:
  - provider_is_only_scope_and_workspace_authority
  - caller_paths_never_become_mutation_authority
  - same_attempt_never_has_two_current_scope_leases
  - terminal_scope_never_reactivates
  - scoped_failure_never_falls_back_to_unrestricted_execution
  - existing_sandbox_audit_and_executor_are_reused_not_duplicated
  - hub_is_consumed_as_immutable_external_interface
  - local_api_builtin_endpoint_does_not_widen_host_configured_external_endpoints
  - sensitive_provider_inventory_and_credentials_are_not_returned
assumptions:
  - statement: "The existing model-facing sentinel_local_api path reaches Agent op=local_api without requiring a new Hub schema."
    validation: "Live call already reached the current connected Agent and returned agent-level unsupported_op; final acceptance repeats the call against the revised known build and requires endpoint list/describe/call success."
  - statement: "The Agent can add a built-in devforge_runtime endpoint without weakening arbitrary local_api endpoint allowlisting."
    validation: "Focused registry/list/describe/call tests prove built-in and host-configured endpoint namespaces/authority stay separate and fail closed."
  - statement: "execute_scoped can compose the existing scoped execution path while preserving authoritative RequestContext and terminalization semantics."
    validation: "Integration tests and live harmless marker prove the existing audit/AppContainer/Job/terminal path is used and no duplicate executor or fallback path is invoked."
material_questions: []
disconfirming_cases:
  - "devforge_runtime becomes reachable when mutation_execution is not explicitly configured/enabled."
  - "execute_scoped uses exec, shell, a second subprocess implementation, operator_unrestricted, or legacy unrestricted compatibility instead of the existing scoped executor."
  - "caller can supply workspace paths, operation classes, execution_profile=operator_unrestricted, or other authority-bearing provider fields."
  - "local_api built-in support broadens or bypasses host-configured external local_api allowlists."
  - "terminal readback reactivates scope authority."
  - "live sentinel_local_api cannot reach the revised Agent endpoint, but the Task still claims end-to-end completion."
challenge_completed: true
```

## Acceptance Criteria

- **A1 / R1:** existing provider-owned lifecycle authority remains canonical; no second scope ledger/authority path exists.
- **A2 / R2,R4:** `devforge_runtime provision_scope` returns provider-issued `scope_id + generation + workspace_id` for bounded `purpose=scoped_script`; repeated same-Attempt provision is idempotent and cannot broaden authority.
- **A3 / R2,R3:** caller path/operation-class/profile authority, repository mismatch, lineage mismatch, stale generation and conflicting scope/workspace binding fail before material mutation.
- **A4 / R3,R6:** revalidation succeeds only for exact current repository + semantic binding and fails closed for disabled/unready/stale/expired/revoked state.
- **A5 / R5:** explicit terminalization/readback proves terminal/non-current state; inspect never reactivates authority.
- **A6 / R7,R8:** `execute_scoped` composes the existing scoped script AppContainer/audit path with no duplicate executor and no unrestricted/exec/shell/allowlist fallback.
- **A7 / R9,R10,R11:** live current ChatGPT `sentinel_local_api` evidence proves `list/describe -> provision_scope -> execute_scoped -> inspect_scope` against one exact scope lineage without any Hub source/schema/deployment change.
- **A8 / R10,R13:** Hosts without eligible mutation policy or older Agents remain fail-closed; existing configured external `local_apis` retain their prior behavior.
- **A9:** SX-HMSA/PR-007 security regressions remain passing, including scope uniqueness, AppContainer containment, START-before-spawn, terminal closure and `INCIDENT-20260927-D-ROOT-RECURSIVE-DELETE` protection.
- **A10 / R11,R12:** capability/help/operator docs describe the immutable-Hub boundary and built-in Agent endpoint truthfully and expose only bounded non-secret evidence.
- **A11 / R13:** legacy/public SentinelX operations remain compatible and mixed-fleet behavior does not project capability from one Agent to another.
- **A12:** affected tests plus compile/import checks pass on the canonical Task transport; S01-S04 retained evidence is revalidated but not replayed.
- **A13 / R14:** static/review verification finds no fixed host/path/version/user/credential identity in the authority model.
- **A14 / R15:** PR-007 Acceptance does not depend on PR-008/PR-009 Hub projection completion.

## Requirement Decision

```text
Requirement Revision: 2
Requirement Ready: true
Prior Plan Revision 2: invalidated for current requirement
Current Plan Revision: 4
Prior Plan Review R3: Rejected / remediated by Revision 4
Current Plan Review R4: Approved
Current Execution Slice Set: docs/execution/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-r4-slices.yaml
Current Gate: acceptance
Plan Approved: true
Implementation Authorized: true
Next Actor: verifier
```
