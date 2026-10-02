# PR-007 — Host Mutation Scope Control Surface & MCP Admission Bridge V1

## State

```yaml
project_id: sentinelx-cloud-core
task_id: PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1
title: Host Mutation Scope Control Surface & MCP Admission Bridge V1
development:
  stage: implementation
  gates:
    requirement_ready: true
    plan_approved: true
    acceptance_approved: false
    completion_verified: false
  next_expected_actor: implementer
  continuation_checkpoint:
    ref: docs/checkpoints/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-s05-verification-blocked-20261002.yaml
transport:
  type: github-pr
  pr_number: 7
  branch: task/host-mutation-scope-control-surface-mcp-admission-bridge-v1
  base_branch: main
artifacts:
  plan: docs/plans/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-plan.md
  plan_review: docs/reviews/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-plan-review-r2.md
  execution_slice_set: docs/execution/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-slices.yaml
related_tasks:
  builds_on:
    - SX-HMSA-001
  active_related:
    - PR-008-provider-execution-profile-tool-surface-alignment-v1
  completed_related:
    - PR-005-provider-capability-release-runtime-activation-v1
```

## Problem

`SX-HMSA-001` implemented provider-owned `host_mutation_sandbox_v1` and `pre_execution_audit_lineage_v1`, including durable mutation-scope authority, Windows AppContainer enforcement, pre-execution audit lineage, and scoped `script_run` execution.

The provider capability can be runtime-ready while an external control plane still cannot lawfully start scoped mutation, because the Agent registry exposes no routable operation for obtaining and validating the provider-owned mutation scope required by the scoped execution path.

Today the internal scoped execution path requires provider-issued evidence equivalent to:

```text
workspace_id
scope_id + generation
repository identity
project/task/run/attempt[/slice] lineage
```

The caller must not invent any of those authority-bearing placement values. Without a bounded control surface, ChatGPT/DevForge reaches a dead end between capability discovery and scoped execution.

There is also a repository ownership boundary: this repository owns the Host Agent, while `mcp.sentinelx.app` is a closed-source Hub. This Task must not claim to add or modify a dedicated model-facing MCP tool in that Hub unless live external evidence proves such a tool exists.

## Goal

Expose the existing provider-owned mutation-scope lifecycle through one bounded Agent operation and prove that an authorized control plane can use SentinelX's existing generic Hub operation relay to perform the complete admission sequence:

```text
control plane
→ generic Hub operation relay
→ Agent mutation-scope operation
→ provider-owned scope authority
→ existing scoped script_run
→ existing AppContainer/audit execution
→ terminal scope read-back
```

The bridge must preserve every accepted SX-HMSA security boundary. It must not create a second authority model, caller-defined workspace authority, or unrestricted fallback.

## Required Behavior

### R1 — Bounded Agent mutation-scope lifecycle operation

The Agent exposes one registered operation for mutation-scope lifecycle control, with bounded actions equivalent to:

```text
provision
revalidate
inspect/readback
terminalize
```

The operation is implemented as a thin control surface over the existing provider-owned `MutationScopeStore`; it does not duplicate scope storage, placement logic, lease rules, sandbox logic, or audit authority.

### R2 — Provider-only mutation authority

`provision_scope` remains the only producer of mutation authority.

The caller must not be able to provide or override:

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
```

The caller may request only a bounded purpose/profile. V1 supports a purpose equivalent to `scoped_script`; the provider maps that purpose to the fixed internal operation classes needed by the existing scoped execution contract.

### R3 — Exact repository and semantic lineage binding

Provisioning and all later authority-sensitive operations bind to:

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

A repository or lineage mismatch fails closed. Payload identity must not override immutable transport `RequestContext` fields such as request ID or opaque correlation identity.

### R4 — Idempotent same-Attempt provisioning

A repeated valid provision request for the same current repository + Attempt[/Slice] + provider placement authority returns the same current scope/workspace authority after live revalidation.

It must not mint a second non-terminal scope or broaden authority.

### R5 — Non-reactivating state read-back

The control surface provides bounded read-back for an exact `scope_id + generation`, including terminal/non-current states, without reactivating the scope.

This is required so an external control plane can prove terminal closure after the existing scoped execution path terminalizes its scope internally.

Terminal, revoked, or expired authority remains non-reactivatable.

### R6 — Fail-closed policy and readiness behavior

When scoped mutation is unconfigured, disabled, runtime-unready, stale, expired, revoked, conflicting, or binding-invalid, the lifecycle operation fails closed with stable diagnostic classification.

Capability advertisement must not imply usable scope admission when the provider readiness boundary is unavailable.

### R7 — No unrestricted fallback

Failure of scope provisioning, revalidation, scoped execution, audit, AppContainer enforcement, process containment, or terminalization must never fall back to:

```text
operator_unrestricted
legacy_unrestricted_compat
ordinary shell execution
caller-selected workspace mutation
```

### R8 — Compose the existing scoped executor

This Task does not create a second sandbox executor.

A provider-issued scope obtained through the new control operation must feed the existing `script_run` `scoped_mutation` path, which remains responsible for:

- live scope revalidation;
- durable forensic script evidence;
- durable `OPERATION_STARTED` before materialization/spawn;
- AppContainer + ACL + Job containment;
- process evidence;
- terminalization before successful finish.

### R9 — Agent capability discoverability

The lifecycle operation is registered in the Agent operation registry and therefore appears in the Agent's derived `ops_supported` / handshake capability surface when available.

If the operation is disabled by normal Agent policy, it is both unadvertised and unreachable according to existing registry semantics.

### R10 — Generic Hub `/op` admission bridge

V1 uses SentinelX's existing generic Hub operation relay as the control-plane bridge instead of requiring a new dedicated Hub MCP tool.

Acceptance must prove, against a live connected Agent where feasible, that the generic relay can carry:

1. the new mutation-scope lifecycle operation;
2. the existing `script_run` scoped-mutation payload using the returned provider-issued scope;
3. the final scope read-back.

### R11 — Closed-source Hub truth boundary

This repository must not claim that a dedicated `sentinel_mutation_scope` MCP tool, MCP schema extension, or Hub deployment has been implemented unless independently verified external Hub evidence exists.

If the generic Hub relay rejects the new operation or cannot carry the required scoped execution payload, the Task must surface an explicit external Hub dependency and must not claim MCP admission complete.

### R12 — Durable diagnostic evidence

Scope lifecycle responses expose enough bounded evidence for orchestration and receipts to verify identity and state, including equivalent fields for:

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
```

Raw protected inventories, credentials, tokens, private keys, environment secrets, and unrestricted filesystem authority must never be returned.

### R13 — Backward compatibility

Existing public/read-only/file/Git/service operations keep their prior behavior.

The normal model-facing `sentinel_script_run` compatibility shape does not need to expose internal scoped fields merely because the generic operation relay can carry them.

Mixed-fleet compatibility remains fail-closed: older Agents that do not register the lifecycle op return `unsupported_op` rather than being treated as scope-capable.

### R14 — No hard-coded deployment identity

No fixed host ID, hostname, workspace path, installation path, release version, credential, token, or machine-specific identity becomes canonical authority in this feature.

## Non-Goals

- Redesigning SX-HMSA scope storage, placement, AppContainer, audit, or terminalization semantics.
- Adding Linux/macOS scoped-mutation enforcement in V1.
- Adding an unrestricted shell escape hatch.
- Making caller-supplied paths authoritative.
- Implementing or modifying the closed-source SentinelX Hub code in this repository.
- Claiming a dedicated MCP tool exists without external proof.
- Replacing PR-005 release/install/runtime-activation work.

## Relationship to PR-005

`PR-005-provider-capability-release-runtime-activation-v1` owns versioned packaging, release, exact-artifact installation, and runtime activation. This Task owns mutation-scope control/admission semantics.

The tasks may touch adjacent capability documentation or package surfaces, so implementation must re-read current `main` and PR-005 before the first execution Slice. If PR-005 has merged, PR-007 adapts to the merged release/runtime surface. If PR-005 has materially changed a shared seam, PR-007 must reconcile rather than duplicate or overwrite it.

## Requirement Readiness Evidence

```yaml
depth: deep
behavior_sensitive: true
behavior_examples:
  - id: R1-example
    sequence: "Authorized control plane submits repository + project/task/run/attempt + purpose=scoped_script -> Agent asks provider scope store to provision -> response returns provider-issued scope/workspace identity; no caller path is accepted as authority."
  - id: R4-example
    sequence: "Same Attempt repeats provision before terminalization -> provider revalidates and returns the same current scope; no second active scope exists."
  - id: R8-example
    sequence: "Control plane provisions scope -> sends existing script_run with execution_profile=scoped_mutation and exact scope/repository/lineage -> existing AppContainer/audit path executes -> scope becomes terminal -> readback proves terminal state."
  - id: R10-example
    sequence: "Generic Hub /op relay sends mutation-scope provision to connected Agent -> receives provider-issued authority -> relay sends scoped script_run -> final readback proves terminal closure."
invariants:
  - provider_is_only_scope_and_workspace_authority
  - caller_paths_never_become_mutation_authority
  - same_attempt_never_has_two_current_scope_leases
  - terminal_scope_never_reactivates
  - scoped_failure_never_falls_back_to_unrestricted_execution
  - existing_sandbox_and_audit_executor_is_reused_not_duplicated
  - dedicated_hub_mcp_support_is_never_claimed_without_external_evidence
  - sensitive_provider_inventory_and_credentials_are_not_returned
assumptions:
  - statement: "A single Agent operation with an action selector is sufficient for V1 lifecycle control."
    validation: "Unit/integration tests prove provision, revalidate, terminalize and non-reactivating readback with one registry entry and stable error semantics."
  - statement: "The existing generic Hub /op relay can route an Agent operation that appears in the Agent capability registry."
    validation: "Live end-to-end relay test; failure creates an explicit external dependency and blocks the MCP-admission acceptance claim."
  - statement: "The generic Hub relay can carry the existing internal scoped script_run payload without changing the normal dedicated MCP tool schema."
    validation: "Live provision -> scoped script -> terminal readback flow through the generic relay."
material_questions: []
disconfirming_cases:
  - "Lifecycle handler accepts caller-selected workspace/write/protected roots or free-form mutation classes as authority."
  - "Repeated same-Attempt provision creates a second non-terminal scope or second writable workspace."
  - "Terminal readback requires reactivating or converting the scope back to current."
  - "Scoped execution failure silently retries through legacy or operator-unrestricted execution."
  - "Agent advertises the lifecycle op while the operation is not actually dispatchable under current policy."
  - "Generic Hub /op cannot relay the new Agent operation or required scoped script payload, but the Task still claims MCP admission complete."
  - "Implementation requires editing closed-source Hub code while the Task claims repository-local completion."
challenge_completed: true
```

## Acceptance Criteria

- **A1 / R1,R9:** Agent registry exposes the lifecycle operation and `ops_supported` derives it automatically; disabled/unavailable operation is not falsely advertised.
- **A2 / R2,R4:** provision returns provider-issued `scope_id + generation + workspace_id` for a valid bounded purpose, and duplicate same-Attempt provision returns the same current authority with no competing non-terminal scope.
- **A3 / R2,R3:** caller path authority, free-form operation classes, repository mismatch, lineage mismatch, stale generation, and conflicting lease/workspace binding are rejected before material mutation.
- **A4 / R3,R6:** revalidation succeeds only for the exact current repository + semantic binding and fails closed for disabled/unready/stale/expired/revoked state.
- **A5 / R5:** explicit terminalization and readback prove terminal/non-current state; readback never reactivates authority.
- **A6 / R7,R8:** a scope obtained through the lifecycle operation drives the existing scoped `script_run` AppContainer/audit path; no duplicate sandbox path or unrestricted fallback is introduced.
- **A7 / R10:** live generic Hub `/op` evidence proves provision -> scoped script execution -> terminal readback against one exact scope lineage.
- **A8 / R11:** if live `/op` cannot relay the new operation or scoped payload, Acceptance records the external Hub dependency and does not claim MCP admission complete.
- **A9:** SX-HMSA security regressions remain passing, including scope uniqueness, AppContainer containment, START-before-spawn, terminal closure, and `INCIDENT-20260927-D-ROOT-RECURSIVE-DELETE` protection.
- **A10 / R9,R11,R12:** capabilities/help/documentation describe the Agent operation and generic relay contract without implying an unverified dedicated MCP tool, and expose only bounded non-secret evidence.
- **A11 / R13:** legacy/public SentinelX operations and normal `sentinel_script_run` behavior remain compatible; older Agents fail with `unsupported_op` rather than false admission.
- **A12:** affected tests plus compile/import checks pass on the canonical Task transport; no material implementation is claimed without durable execution evidence.
- **A13 / R14:** static/review verification finds no fixed host/path/version/credential identity in the authority model.

## Plan Review R1

Result: **Rejected**.

Durable findings: `docs/reviews/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-plan-review-r1.md`.

Required remediation:

1. make the canonical scoped operation class an execution-time admission check consumed by `script_run scoped_mutation`, not merely persisted metadata;
2. revise D4/S01 to reuse or safely extend the existing `MutationScopeStore.read_scope(scope_id)` seam with exact generation + repository + semantic binding and non-reactivating semantics.

## Requirement Decision

```text
Requirement Ready: true
Plan Revision: 2
Plan Review R2: Approved
Current Gate: implementation
Plan Approved: true
Implementation Authorized: true
Next Actor: implementer
```
