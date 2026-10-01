# PR-008 — SentinelX Provider Execution Profile Tool Surface Alignment V1

## State

```yaml
project_id: sentinelx-cloud-core
task_id: PR-008-provider-execution-profile-tool-surface-alignment-v1
title: SentinelX Provider Execution Profile Tool Surface Alignment V1
development:
  stage: implementation
  gates:
    requirement_ready: true
    plan_approved: true
    acceptance_approved: false
    completion_verified: false
  next_expected_actor: implementer
  continuation_checkpoint:
    ref: docs/checkpoints/PR-008-provider-execution-profile-tool-surface-alignment-v1-s01-completed-20261001.yaml
transport:
  type: github-pr
  pr_number: 8
  branch: task/provider-execution-profile-tool-surface-alignment-v1
  base_branch: main
artifacts:
  plan: docs/plans/PR-008-provider-execution-profile-tool-surface-alignment-v1-plan.md
  plan_review: docs/reviews/PR-008-provider-execution-profile-tool-surface-alignment-v1-plan-review-r1.md
  execution_slice_set: docs/execution/PR-008-provider-execution-profile-tool-surface-alignment-v1-slices.yaml
related_tasks:
  builds_on:
    - SX-HMSA-001
  active_related:
    - PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1
    - PR-005-provider-capability-release-runtime-activation-v1
external_contracts:
  - bewaterhere-coder/DevForge@v2.23.0:system/host-runtime-execution-profile-tool-contract.md
```

## Problem

`SX-HMSA-001` already implements the Host-side `script_run` profile boundary. When `mutation_execution` is configured, the Agent requires an explicit execution profile and supports a fail-closed `scoped_mutation` path backed by provider-owned mutation scope, audit lineage, Windows AppContainer isolation, and terminalization.

The currently connected ChatGPT/MCP `sentinel_script_run` tool surface does not expose an `execution_profile` argument. The live result is therefore:

```text
Host policy requires explicit execution_profile
+
model-facing tool schema cannot express execution_profile
→ execution_profile_required / HostExecutionProfileInterfaceMismatch
```

The defect is not that the Host handler cannot consume the field. The handler already accepts `execution_profile`, and the wire protocol carries arbitrary operation payload mappings. The missing alignment is between Agent capability advertisement and the closed-source Hub/MCP model-facing tool projection.

For `scoped_mutation`, `execution_profile` is also not sufficient by itself. The existing Host handler requires provider-issued scope authority and semantic binding data equivalent to:

```text
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

A model-facing tool that advertises `scoped_mutation` but cannot carry the required authority/binding fields is still unusable and must not be reported as aligned.

There is a hard repository boundary: this repository owns the SentinelX Host Agent. `mcp.sentinelx.app` owns the Hub/MCP schema projection and is not implemented in this repository. This Task must not claim to modify or deploy closed-source Hub code.

## Goal

Make the Agent advertise a versioned, machine-readable `script_run` execution-profile tool contract that lets a compatible Hub/MCP layer safely project the exact optional fields required for profiled execution, while preserving mixed-fleet compatibility and all SX-HMSA security boundaries.

End-to-end completion requires live evidence that the production model-facing `sentinel_script_run` schema actually exposes the required fields for a capable Agent and that a harmless `scoped_mutation` Python execution can complete through that surface using provider-issued scope authority.

## Required Behavior

### R1 — Versioned profile-tool capability advertisement

The Agent handshake advertises a stable feature token for profiled `script_run` input semantics, equivalent to:

```text
script_run_execution_profile_v1
```

The token means the Agent understands the profiled payload contract. It does not itself grant mutation authority or prove sandbox readiness.

Older Agents that do not advertise the token remain valid mixed-fleet members; the Hub must not send new profiled fields to them merely because another connected Agent supports them.

### R2 — Machine-readable capabilities contract

`capabilities(detail=full)` exposes a bounded execution feature describing the model-facing input requirements for `script_run`, including equivalent evidence for:

```yaml
feature: host_runtime.script_run_execution_profile_v1
operation: script_run
profile_argument: execution_profile
profile_argument_required_when_mutation_execution_configured: true
supported_profiles:
  - scoped_mutation
operator_unrestricted:
  advertised_only_when_host_policy_enabled: true
scoped_mutation_required_input:
  - mutation.scope_ref.scope_id
  - mutation.scope_ref.generation
  - lineage.project_id
  - lineage.task_id
  - lineage.run_id
  - lineage.attempt_id
  - lineage.slice_id?
  - repository.vcs
  - repository.authority
  - repository.path
```

This metadata is descriptive contract evidence. It must not contain a live scope ID, workspace path, credential, token, private inventory, or caller-specific authority.

### R3 — Readiness and policy semantics remain separate

The tool-input contract must distinguish:

```text
field understood by this Agent
vs
profile currently admitted by Host policy/readiness
```

`scoped_mutation` is usable only when existing Host mutation readiness says it is available and verified. Capability advertisement must not turn an unavailable sandbox into executable authority.

### R4 — Existing scoped execution remains canonical

This Task must reuse the existing `make_profiled_script_run_handler` / scoped execution path. It must not create a second script executor, second scope store, second audit path, alternate workspace authority, or alternate sandbox.

### R5 — Stable missing-interface diagnostic metadata

When configured mutation execution rejects an unprofiled `script_run`, the error remains fail-closed and should provide bounded machine-readable details sufficient for an adapter/operator to diagnose the mismatch, equivalent to:

```yaml
required_argument: execution_profile
feature: script_run_execution_profile_v1
supported_profiles:
  - scoped_mutation
```

No diagnostic response may disclose live mutation authority or protected filesystem inventory.

### R6 — No method escalation

Tool-surface mismatch or missing profile must never authorize automatic fallback to:

```text
exec python
PowerShell wrapper
shell wrapper
operator_unrestricted
legacy_unrestricted_compat
allowlist expansion
caller-selected workspace mutation
```

Direct `exec python` remains governed by the existing command allowlist and is not enabled by this Task.

### R7 — Hub/MCP truth boundary

This repository may define and advertise the Agent-side contract but must not claim the production Hub/MCP schema has changed without live external evidence.

If the production model-facing `sentinel_script_run` schema still lacks any field required by the advertised profiled contract, Acceptance must return an explicit external dependency/blocker such as:

```text
HubToolProjectionRequired
```

and must not claim end-to-end completion.

### R8 — Model-facing schema acceptance

For a live Agent build carrying this feature, Acceptance must verify the actual client-visible `sentinel_script_run` schema exposes at minimum:

```text
execution_profile
mutation
lineage
repository
```

with sufficient nested shape to carry the existing scoped handler contract.

The field shape may be provider-specific, but it must preserve the same semantics and cannot silently synthesize scope authority or lineage.

### R9 — Provider-owned scope dependency

A successful live `scoped_mutation` call must consume scope authority issued by the existing provider-owned mutation scope system. This Task does not invent or bypass that authority.

If no admitted external control surface can provision/revalidate the required scope, end-to-end execution Acceptance remains blocked on `PR-007` or an equivalent verified provider-owned scope admission path.

### R10 — Runtime activation dependency

Live production verification must run against a known Agent build containing this Task. Release/install/runtime activation is owned by `PR-005` or an equivalent verified activation path; source-code completion alone does not prove production tool-surface alignment.

### R11 — Harmless end-to-end execution proof

End-to-end Acceptance requires a harmless Python script through the model-facing `sentinel_script_run` profiled surface using:

```text
execution_profile = scoped_mutation
provider-issued scope authority
exact repository identity
exact semantic lineage
```

The script must have no destructive side effect and should emit a deterministic marker only. Acceptance must read back successful execution evidence and terminal scope closure.

### R12 — Direct exec boundary remains intact

Acceptance must separately prove that direct `sentinel_exec` of Python remains denied when Python is not in `allowed_commands`.

This proves the fix restored the profiled script path rather than weakening the command allowlist.

### R13 — Mixed-fleet compatibility

Adding the feature must not break older Agents or unrelated operations. A Hub that does not understand the new feature may ignore the advertisement, but then end-to-end tool-surface Acceptance is not satisfied.

Existing unprofiled `script_run` behavior remains unchanged on Hosts where `mutation_execution` is absent and legacy compatibility is still allowed by current policy semantics.

### R14 — No protocol-version churn unless required

Because `RequestMessage.payload` already carries arbitrary mappings, V1 must not require a wire-protocol breaking change merely to transport `execution_profile` or scoped payload fields.

A protocol dependency change is permitted only if implementation evidence proves an actual protocol limitation; otherwise the current payload envelope is reused.

## Non-Goals

- Implementing or deploying the closed-source `mcp.sentinelx.app` Hub in this repository.
- Redesigning mutation scope storage, AppContainer sandboxing, audit lineage, placement, or terminalization.
- Replacing `PR-007` mutation-scope lifecycle work.
- Replacing `PR-005` release/runtime activation work.
- Adding Python to `allowed_commands`.
- Enabling `operator_unrestricted` by default.
- Creating a generic shell escape hatch.
- Treating capability advertisement as mutation authority.

## Current Evidence

- Current Host code already parses direct/nested `execution_profile` and routes `scoped_mutation` to the existing scoped executor.
- Current Host code fails configured unprofiled `script_run` with `execution_profile_required`.
- Current profiled scoped executor requires provider-issued mutation scope, lineage, and repository identity.
- `RequestMessage.payload` in `sentinelx-cloud-protocol` is `dict[str, Any]`, so these payload fields do not require a new top-level wire field.
- DevForge v2.23.0 now explicitly classifies a required profile that cannot be expressed by the selected tool schema as `HostExecutionProfileInterfaceMismatch` and forbids wrapper/allowlist/unrestricted fallback.
- Current ChatGPT-visible `sentinel_script_run` schema does not expose `execution_profile`.

## Requirement Readiness Evidence

```yaml
depth: deep
behavior_sensitive: true
behavior_examples:
  - id: R1-example
    sequence: "New Agent connects -> hello advertises script_run_execution_profile_v1 -> Hub may safely expose profiled script fields only for a compatible target Agent."
  - id: R7-example
    sequence: "Agent source advertises the feature but ChatGPT tool schema still lacks execution_profile -> Acceptance returns HubToolProjectionRequired; no wrapper fallback is attempted."
  - id: R11-example
    sequence: "Control plane obtains provider-issued scope -> ChatGPT-visible sentinel_script_run carries execution_profile + scope + lineage + repository -> existing scoped AppContainer executor runs a harmless Python marker -> scope terminal readback succeeds."
  - id: R12-example
    sequence: "sentinel_exec python --version remains command_not_allowed while profiled script_run succeeds."
invariants:
  - host_handler_remains_single_execution_authority
  - capability_advertisement_is_not_mutation_authority
  - scoped_mutation_never_falls_back_to_unrestricted_execution
  - caller_never_invents_scope_or_workspace_authority
  - production_hub_schema_change_is_never_claimed_without_live_evidence
  - direct_exec_allowlist_is_not_relaxed
  - mixed_fleet_compatibility_is_preserved
open_external_dependencies:
  - PR-007 or equivalent provider-owned scope admission for full live scoped execution
  - PR-005 or equivalent known-build runtime activation for production verification
  - closed-source Hub/MCP support for projecting advertised profiled fields
readiness: Ready
```
