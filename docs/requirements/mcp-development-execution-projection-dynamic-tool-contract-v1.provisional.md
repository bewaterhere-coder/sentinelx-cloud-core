# Provisional Requirement — SentinelX MCP Development Execution Projection & Dynamic Tool Contract V1

```yaml
provisional:
  slug: mcp-development-execution-projection-dynamic-tool-contract-v1
  branch: task/mcp-development-execution-projection-dynamic-tool-contract-v1
project_id: sentinelx-cloud-core
repository: bewaterhere-coder/sentinelx-cloud-core
runtime:
  devforge_version: 2.29.0
  devforge_revision: c0266c113e4e6b8f2b90d9246af153a617e9d301
base_revision: f7e878f3497582547e5d52cd33b060cae18d2e84
```

## Intent

Restore the ordinary ChatGPT → SentinelX → Host Runtime development path by making the model-facing MCP execution surface able to express the already-implemented scoped-mutation contract, and prevent future Agent/Hub tool-schema drift with a versioned dynamic tool-contract boundary.

## Repository Reality / Non-Duplication Boundary

This requirement is related to, but must not reimplement:

- `PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1`, which owns provider-issued mutation-scope lifecycle admission;
- `PR-008-provider-execution-profile-tool-surface-alignment-v1`, which owns Agent-side execution-profile advertisement and is currently Acceptance-blocked on `HubToolProjectionRequired` / provider-scope admission.

The new Task owns the missing projection/integration contract needed to close that external boundary. Existing PR-007/008 verified implementation remains authoritative and must be reused rather than copied.

## Core Problem

The live Agent can require and consume `execution_profile=scoped_mutation`, provider-issued scope authority, lineage and repository identity, while the ChatGPT-visible `sentinel_script_run` schema cannot currently express those fields. The Agent handshake advertises capability names, not a complete model-facing input schema, so Agent capability evolution and Hub/MCP tool projection can drift independently.

Current production ownership boundary:

```text
ChatGPT model-facing tool schema
→ mcp.sentinelx.app Hub / MCP projection
→ SentinelX wire payload
→ sentinelx-cloud-core Agent
```

`mcp.sentinelx.app` Hub source/deployment is not present in this repository and is not currently available as a writable repository through the connected GitHub surface. This external ownership boundary must be represented explicitly; no completion claim may imply Hub code was changed without external evidence.

## Goal

Define and implement the smallest provider-neutral contract that lets a compatible Hub expose the exact scoped-development inputs supported by a target Agent, while preserving fail-closed Host authority, mixed-fleet compatibility, and one canonical scoped execution path.

End-to-end completion requires a real ChatGPT-visible invocation proving the production tool projection can carry the required scoped-development request and complete a harmless provider-issued scoped transaction through terminal scope read-back.

## Required Behavior

1. The projection must expose or equivalently carry `execution_profile`, `mutation.scope_ref`, semantic `lineage`, and `repository` identity for compatible Agents.
2. Provider-owned scope lifecycle remains authoritative; callers never mint `scope_id`, generation, workspace identity/path, write roots, sandbox identity or protected-root authority.
3. PR-007 remains the mutation-scope lifecycle authority and PR-008 remains the Agent execution-profile contract authority; this Task composes them.
4. A versioned, machine-readable dynamic tool-contract mechanism must prevent silent Agent/Hub schema drift. If a handshake-level schema extension is used, it must be additive and mixed-fleet safe. If the existing wire envelope is sufficient, no breaking protocol churn is allowed.
5. Hub projection must be gated per target Agent capability/contract revision; one capable Agent must not cause new fields to be sent to an incompatible Agent.
6. Missing projection support fails closed with a stable diagnostic such as `HubToolProjectionRequired` / `HostExecutionProfileInterfaceMismatch`; no shell wrapper, allowlist expansion, `operator_unrestricted`, direct Python exec, caller-selected workspace or provider fallback is allowed.
7. Production Hub/MCP change is external truth. Source changes in this repository can define/advertise/test the contract but cannot prove production projection deployment.
8. Acceptance must inspect the actual ChatGPT-visible tool schema, execute one harmless scoped marker with provider-issued authority, verify audit/execution evidence and terminal scope closure, and separately verify direct Python exec remains denied when not allowlisted.

## Current Task P0 Dependencies

```yaml
current_task_p0_dependencies:
  - id: HubProjectionWriteOrDeploymentSurface
    state: unresolved_external
    reason: production mcp.sentinelx.app model-facing tool projection is not implemented in this repository and no writable Hub repository/deployment surface is currently available
  - id: ProviderScopeAdmission
    state: active_related_task
    owner: PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1
  - id: AgentExecutionProfileContract
    state: active_related_task
    owner: PR-008-provider-execution-profile-tool-surface-alignment-v1
```

These dependencies do not make the requirement ambiguous, but they must block any false end-to-end completion claim and may constrain implementation readiness during Plan Review.

## Requirement Readiness Evidence

```yaml
depth: deep
behavior_sensitive: true
challenge_completed: true
material_questions: []
readiness: ReadyForPlanning
invariants:
  - no_duplicate_scope_or_scoped_execution_authority
  - no_caller_minted_host_mutation_authority
  - no_unrestricted_or_allowlist_fallback
  - no_production_hub_completion_claim_without_live_external_evidence
  - mixed_fleet_projection_is_target_agent_gated
  - existing_pr007_pr008_verified_work_is_reused_not_reimplemented
behavior_examples:
  - "Compatible Agent advertises contract -> Hub projects scoped fields for that target only -> provider-issued scope + exact lineage/repository reaches existing scoped executor -> harmless marker succeeds -> terminal scope readback succeeds."
  - "Hub has not consumed the dynamic contract -> ChatGPT-visible schema lacks execution_profile -> operation remains blocked and no fallback is attempted."
  - "Older Agent lacks the contract token/revision -> Hub retains legacy tool shape and never sends unknown profiled fields."
```

## Provisional Next Step

Create the Draft PR to obtain the canonical GitHub-backed Task ID, then replace this provisional artifact with the canonical Requirement + Plan and stop at Plan Review.