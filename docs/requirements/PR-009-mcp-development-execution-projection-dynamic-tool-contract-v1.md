# PR-009 — SentinelX MCP Development Execution Projection & Dynamic Tool Contract V1

## State

```yaml
project_id: sentinelx-cloud-core
task_id: PR-009-mcp-development-execution-projection-dynamic-tool-contract-v1
title: SentinelX MCP Development Execution Projection & Dynamic Tool Contract V1
development:
  stage: plan_review
  gates:
    requirement_ready: true
    plan_approved: false
    acceptance_approved: false
    completion_verified: false
  latest_plan_review: rejected_round_1
  plan_revision: 2
  plan_remediation: revision_2_persisted
  unresolved_current_task_p0_dependencies:
    - HubProjectionWriteOrDeploymentSurface
    - ProviderScopeAdmission
    - AgentExecutionProfileContract
  next_expected_actor: reviewer
transport:
  type: github-pr
  pr_number: 9
  branch: task/mcp-development-execution-projection-dynamic-tool-contract-v1
  base_branch: main
artifacts:
  plan: docs/plans/PR-009-mcp-development-execution-projection-dynamic-tool-contract-v1-plan.md
  prior_plan_review: docs/reviews/PR-009-mcp-development-execution-projection-dynamic-tool-contract-v1-plan-review-r1.md
related_tasks:
  builds_on:
    - PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1
    - PR-008-provider-execution-profile-tool-surface-alignment-v1
    - PR-005-provider-capability-release-runtime-activation-v1
```

## Problem

The Host-side scoped mutation implementation is no longer the primary defect. Current repository and live-runtime evidence show:

```text
Agent understands profiled script_run                 ✅
Agent can require execution_profile                   ✅
Agent advertises profiled-execution capability        ✅
Host mutation sandbox/readiness can be available      ✅
ChatGPT-visible sentinel_script_run schema             ❌ required fields not projected
provider-owned scope admission                         ⚠ owned by active PR-007
```

The model-facing MCP surface currently cannot express the complete existing scoped execution contract:

```text
execution_profile
mutation.scope_ref.scope_id
mutation.scope_ref.generation
lineage.project_id
lineage.task_id
lineage.run_id
lineage.attempt_id
lineage.slice_id?
repository.vcs
repository.authority
repository.path
```

That creates a control-plane deadlock: DevForge correctly requires `scoped_mutation`, but ChatGPT cannot carry the required arguments to the Agent. The live Agent therefore returns `execution_profile_required` rather than weakening policy.

A second structural issue causes the drift to recur. The Agent hello path advertises capability names, while the production Hub owns the model-facing MCP tool schema. Agent input-contract evolution and Hub schema projection can therefore diverge unless there is an explicit versioned projection contract and compatibility rule.

## Ownership Boundary

Current production path:

```text
ChatGPT model-facing tool schema
→ mcp.sentinelx.app Hub / MCP projection
→ SentinelX request payload
→ sentinelx-cloud-core Agent
→ provider-owned scope + sandbox + audit
```

Repository ownership is split:

- `bewaterhere-coder/sentinelx-cloud-core` owns the Host Agent and may define/advertise/test Agent-side contract semantics;
- `PR-007` owns provider-issued scope lifecycle admission;
- `PR-008` owns the Agent-side execution-profile capability/tool-surface contract and has already implemented substantial parts of that boundary;
- production `mcp.sentinelx.app` owns the ChatGPT-facing MCP projection and is not implemented in this repository;
- no writable Hub repository/deployment surface is currently available through the connected GitHub environment.

This Task MUST NOT claim to have changed or deployed production Hub code without independently verified external evidence.

## Goal

Close the projection contract between a target SentinelX Agent and the model-facing MCP surface so ordinary ChatGPT can lawfully drive the existing DevForge Host Runtime scoped-development path.

The solution must:

1. reuse PR-007 provider-owned mutation authority and PR-008 profiled execution semantics rather than duplicate them;
2. define a versioned, machine-checkable dynamic tool projection contract that a Hub can consume per target Agent;
3. make the production ChatGPT-visible execution surface semantically capable of carrying the existing scoped-development request;
4. preserve mixed-fleet compatibility and all fail-closed security boundaries;
5. prove completion through a real ChatGPT-visible harmless scoped transaction and terminal scope read-back.

## Required Behavior

### R1 — Existing authority remains canonical

This Task MUST NOT create a second mutation scope store, workspace authority, audit lineage, sandbox executor, script executor, or terminalization path.

Provider-issued scope lifecycle remains owned by PR-007/equivalent verified provider control surface. Profiled `script_run` semantics remain owned by PR-008/equivalent verified Agent contract.

### R2 — Complete model-facing scoped input surface

For a compatible target Agent, the production model-facing execution surface must expose or equivalently carry all semantics required by the existing Host handler:

```text
execution_profile
mutation.scope_ref
lineage
repository
```

Nested shape must be sufficient to preserve exact scope generation, repository identity, and project/task/run/attempt[/slice] lineage.

### R3 — Dynamic projection contract

A stable versioned contract must let the Hub determine, for the exact target Agent, which model-facing fields/operations are supported and how they map to Agent payload semantics.

The contract must distinguish:

```text
field understood by Agent
Host policy/readiness admits profile
provider-owned authority currently exists
model-facing Hub projection is available
```

No one layer may be treated as proof of another.

### R4 — Prefer additive compatibility over protocol churn

The current wire request payload already carries arbitrary operation mappings. A breaking wire-protocol version change MUST NOT be introduced merely to transport scoped fields.

If a handshake-level contract extension is necessary to prevent drift, it must be additive, versioned, bounded and mixed-fleet safe. Older Agents/Hubs must continue to interoperate without receiving unknown profiled fields.

### R5 — Per-target-Agent gating

One capable Agent MUST NOT cause the Hub to expose/send new profiled fields to another incompatible Agent.

Projection resolution is bound to the exact target Agent capability/contract revision selected for the invocation.

### R6 — No authority synthesis in projection

The Hub/model-facing layer may project fields but MUST NOT synthesize:

```text
scope_id
scope generation
workspace_id
workspace path
allowed write roots
protected roots
sandbox/AppContainer identity
semantic lineage
repository identity
```

Authority-bearing values come from the canonical provider/control-plane sources only.

### R7 — Fail-closed interface mismatch

When the target Agent requires scoped execution but the current model-facing surface cannot express it, the request remains blocked with stable evidence equivalent to:

```text
HubToolProjectionRequired
HostExecutionProfileInterfaceMismatch
```

No fallback may use:

```text
sentinel_exec python
PowerShell/shell wrapper
allowlist expansion
operator_unrestricted
legacy unrestricted compatibility
caller-selected workspace mutation
provider substitution
```

### R8 — Hub truth boundary

Agent source, protocol documentation, schema fixtures, or capability advertisement are not proof that production `mcp.sentinelx.app` has deployed the projection.

Production projection success requires live client-visible evidence.

### R9 — Contract drift regression

Regression coverage must detect at least:

- Agent advertises a profiled contract but model-facing schema omits required fields;
- Hub projects a field not supported by target Agent;
- contract revision changes without compatible projection semantics;
- model-facing schema can carry profile but not provider scope/lineage/repository binding;
- mixed-fleet projection leaks newer fields to older Agents.

### R10 — End-to-end acceptance

Full Acceptance requires a live known Agent build and a real ChatGPT-visible tool invocation:

```text
provider-issued scope
→ current ChatGPT model-facing execution tool
→ execution_profile=scoped_mutation
→ exact repository + lineage + scope generation
→ harmless deterministic marker execution
→ audit/execution read-back
→ terminal scope closure read-back
```

Acceptance must separately verify direct Python execution remains denied when Python is not allowlisted.

## Current P0 Dependencies

```yaml
current_task_p0_dependencies:
  - id: HubProjectionWriteOrDeploymentSurface
    state: unresolved_external
    reason: production mcp.sentinelx.app projection is outside this repository and no writable Hub source/deployment surface is currently available
  - id: ProviderScopeAdmission
    state: active_related_task
    owner: PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1
  - id: AgentExecutionProfileContract
    state: active_related_task
    owner: PR-008-provider-execution-profile-tool-surface-alignment-v1
```

These are implementation/acceptance dependencies, not ambiguity in the requested behavior. They MUST prevent false end-to-end completion claims.

## Compatibility / Non-Goals

- No redesign of SX-HMSA AppContainer/sandbox/audit semantics.
- No second provider scope lifecycle.
- No replacement of PR-007 or PR-008 verified work.
- No direct Python allowlist expansion.
- No default `operator_unrestricted` enablement.
- No generic shell escape hatch.
- No hard-coded host, workspace, installation path, credential, or current user identity.
- No claim that production Hub is fixed merely because this repository defines a contract.

## Requirement Readiness Evidence

```yaml
depth: deep
behavior_sensitive: true
challenge_completed: true
material_questions: []
readiness: Ready
behavior_examples:
  - id: compatible-target
    sequence: "Target Agent advertises supported contract -> Hub projects only compatible scoped-development fields -> provider-issued scope + exact lineage/repository reaches existing scoped executor -> harmless marker succeeds -> terminal readback succeeds."
  - id: missing-hub-projection
    sequence: "Agent supports scoped profile but ChatGPT schema omits execution_profile/mutation/lineage/repository -> request remains blocked as HubToolProjectionRequired -> zero fallback execution."
  - id: mixed-fleet
    sequence: "New Agent and older Agent are both connected -> Hub resolves projection per target -> older Agent receives legacy-compatible payload only."
invariants:
  - existing_pr007_scope_authority_is_reused
  - existing_pr008_profile_contract_is_reused
  - no_caller_minted_mutation_authority
  - no_unrestricted_or_allowlist_fallback
  - mixed_fleet_projection_is_target_bound
  - production_hub_state_requires_live_external_evidence
  - no_receipt_no_completion_claim
```

## Acceptance Criteria

- **A1:** canonical projection contract explicitly composes PR-007 provider scope authority and PR-008 profiled execution semantics without duplicating either implementation.
- **A2:** machine-checkable contract/fixtures define the exact required model-facing scoped-development payload and target-Agent compatibility conditions.
- **A3:** regression tests detect incomplete projection (`execution_profile` without scope/lineage/repository), incompatible target-Agent projection, and mixed-fleet leakage.
- **A4:** no implementation or test weakens direct command allowlists, scoped sandboxing, audit lineage, provider-owned placement, or terminalization.
- **A5:** current production ChatGPT-visible schema exposes semantically sufficient scoped-development input for a compatible Agent, proven by live evidence rather than repository assertion.
- **A6:** provider-issued scope can flow through that model-facing surface into existing `scoped_mutation` execution with exact repository/lineage binding.
- **A7:** harmless deterministic marker execution succeeds and terminal scope read-back proves no active mutation authority remains.
- **A8:** direct Python exec remains denied when not allowlisted.
- **A9:** if Hub source/deployment remains inaccessible or production projection remains stale, Acceptance is Blocked with explicit external dependency and completion remains false.

## Regression Surface

- Agent hello/capability advertisement and execution feature metadata;
- model-facing `sentinel_script_run`/equivalent tool schema;
- PR-007 mutation-scope admission contract;
- PR-008 execution-profile contract;
- mixed-fleet compatibility;
- direct exec allowlist behavior;
- scoped execution audit/terminalization evidence;
- Hub deployment/read-back evidence boundary.
