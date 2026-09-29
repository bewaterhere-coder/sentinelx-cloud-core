# SX-HMSA-001 — Host Mutation Sandbox & Pre-Execution Audit Lineage Provider V1

## State

```yaml
project_id: sentinelx-cloud-core
task_id: SX-HMSA-001
stage: implementation
base_branch: main
task_branch: task/sx-host-mutation-sandbox-pre-execution-audit-lineage-provider-v1
transport: github-pr
requirement_status: ready
plan_status: approved
plan_revision: 3
plan_head: e0acae46662ee9792eafd91a30b25db8d7488919
gates:
  requirement_ready: true
  plan_approved: true
  acceptance_approved: false
  completion_verified: false
artifacts:
  plan: docs/plans/SX-HMSA-001-host-mutation-sandbox-pre-execution-audit-lineage-provider-v1-plan.md
  plan_review: docs/reviews/SX-HMSA-001-host-mutation-sandbox-pre-execution-audit-lineage-provider-v1-plan-review-r3.md
  execution_slice_set: docs/execution/SX-HMSA-001-execution-slice-set.yaml
next_expected_actor: implementer
```

## Requirement Source

Implement the SentinelX provider side required by the DevForge consumer contracts merged in `bewaterhere-coder/DevForge` as `EVO-SENTINELX-HOST-MUTATION-SANDBOX-PRE-EXECUTION-AUDIT-LINEAGE-V1-001`.

Provider capabilities to satisfy:

```text
host_mutation_sandbox_v1
pre_execution_audit_lineage_v1
```

Canonical mutation-scope lifecycle semantics:

```text
host_mutation_sandbox_v1.provision_scope
host_mutation_sandbox_v1.revalidate_scope
host_mutation_sandbox_v1.terminalize_scope
```

## Observed Current State

Current `script_run` behavior explicitly treats script content as outside the `exec` allowlist and as an intentionally more powerful capability. A script may therefore perform arbitrary operations available to the SentinelX service OS identity.

Current executor audit is written after the handler returns. Current local audit is explicitly best-effort and swallows write failures. Therefore the existing audit cannot prove a durable mutation START before process spawn.

Current script staging is deleted when `cleanup=true`, so the temporary script body is not durable forensic evidence after execution.

Current Windows timeout cleanup uses `taskkill /T /F` after process creation; this is cleanup behavior, not an OS mutation authority boundary and not proof that detached/background descendants cannot escape.

Windows service installation may run SentinelX as LocalSystem. A mutating script must therefore never inherit unrestricted LocalSystem filesystem authority merely because the SentinelX service itself has it.

## Goal

Add a provider-owned Host mutation security boundary so a DevForge mutation can execute only inside one exact Runtime-owned workspace scope, with durable pre-spawn audit lineage and process containment.

The safety invariant is:

> No Runtime-owned scope, no Host mutation. No durable pre-execution audit START, no spawn. No verified OS sandbox, no scoped mutation. No terminalized authority, no successful completion receipt.

## Required Capability Model

SentinelX must expose capability evidence sufficient for DevForge to distinguish:

```text
read_only
scoped_mutation
operator_unrestricted
```

For DevForge-originated Host mutation:

```text
execution_profile = scoped_mutation
operator_unrestricted = forbidden
```

`operator_unrestricted` may exist for explicit local-operator workflows, but it must not be advertised as satisfying `host_mutation_sandbox_v1`, must not be selected as fallback from scoped mutation, and must require explicit operator policy.

## Host-Owned Mutation Scope Authority

SentinelX must own canonical scope state independently of caller paths.

A scope binding must contain equivalent authority state:

```yaml
mutation_scope_binding:
  authority: runtime_host_owned
  producer: host_mutation_sandbox_v1.provision_scope
  workspace_id: <host-allocated-id>
  mutation_scope_ref:
    scope_id: <host-allocated-id>
    generation: <positive-generation>
  lineage:
    project_id:
    task_id:
    run_id:
    attempt_id:
    slice_id: null | string
  placement:
    exact_workspace_ref:
    exact_workspace_digest:
  protected_inventory_digest:
  allowed_operation_classes:
    - workspace_materialize
    - scoped_mutation
  issued_at:
  expires_at:
  state: provisioned | active | revoked | expired | terminal
  scope_digest:
```

Rules:

1. `provision_scope` is the only producer of `workspace_id` and `mutation_scope_ref` for this capability.
2. Caller-provided `allowed_write_root`, `protected_roots`, arbitrary workspace root, scope id, generation or expiry are evidence only and never authority.
3. Scope binds one exact Run/Attempt and, when present, Slice.
4. `revalidate_scope` verifies current generation, lifecycle state, expiry/revocation, lineage, exact workspace placement and protected inventory before material mutation.
5. Stale, unknown, caller-minted, cross-Attempt, wrong-workspace, expired, revoked or terminal scopes fail closed.
6. `terminalize_scope` permanently moves the exact scope/generation to a non-active state and authoritative read-back must prove it is no longer `active` or `provisioned`.

## Windows OS-Enforced Scoped Mutation

Windows is the mandatory V1 enforcement platform.

A conforming implementation must enforce the boundary below PowerShell/Python/script semantics. Command-string scanning is insufficient.

Required guarantees:

1. scoped mutation executes under a dedicated restricted mutation identity/token or an equivalent OS-enforced identity boundary;
2. the identity can mutate only the exact admitted workspace and explicitly required staging/audit resources;
3. parent directories, sibling workspaces, canonical repository checkouts, `D:\\`, `D:\\coco`, user project directories and unrelated Host locations remain non-writable/non-deletable;
4. child processes inherit the same or stricter authority;
5. detached/background descendants cannot escape containment;
6. use Windows Job Object or equivalent process-tree containment, including kill-on-close semantics and no privilege-expanding breakaway fallback;
7. timeout/cancel terminates the complete admitted process tree or returns a blocking containment failure;
8. a sandbox construction/verification failure prevents mutation rather than falling back to the SentinelX service identity;
9. normal-user Git credentials are not injected into the mutation sandbox. Authenticated Git remains a separate structured capability/broker.

Linux/macOS may remain unavailable for `scoped_mutation` in V1, but they must fail closed rather than silently use unrestricted execution.

## Pre-Execution Write-Ahead Audit

Material Host mutation must use a security-critical audit lifecycle:

```text
REQUEST_RECEIVED
→ ADMISSION_VERIFIED
→ OPERATION_STARTED   # durable before spawn
→ PROCESS_SPAWNED
→ OPERATION_FINISHED
```

`OPERATION_STARTED` must be flushed/durably committed before the mutating process is created. If the write or durability verification fails, return a named audit failure and do not spawn.

The existing best-effort local audit may remain for ordinary telemetry, but it cannot be the only audit path for scoped mutation.

### START evidence

Record equivalent fields:

```yaml
request_id:
job_id: null | string
received_at:
started_at:
operation:
capability:
opaque_ref: null | string
lineage:
  origin_runtime:
  project_id:
  task_id:
  run_id:
  attempt_id:
  slice_id:
  workspace_id:
  transport_ref:
mutation:
  execution_profile: scoped_mutation
  scope_ref:
  scope_generation:
  scope_digest:
  allowed_write_roots_digest:
  protected_roots_digest:
process_intent:
  interpreter:
  cwd:
  argv:
  executable:
  script_sha256:
  script_artifact_ref:
host:
  host_id:
  service_identity:
  sandbox_identity:
```

`request_id`, `opaque_ref` and semantic lineage are distinct identities. Missing semantic fields remain absent/null; they must never be invented.

### Durable script evidence

For generated script execution, retain:

```text
script_sha256
+
restricted durable script artifact reference
```

The forensic artifact must survive ordinary `script_job_*` cleanup and must not depend on `cleanup=false`.

### Spawn evidence

Record after spawn:

```yaml
request_id:
pid:
parent_pid:
executable_final_path:
cwd_final_path:
os_identity:
sandbox_identity:
containment_id:
started_at:
```

### Finish evidence

Record equivalent outcome/process-tree/read-back evidence. A crash may leave START without FINISH; it must never be backfilled as success.

## Protocol / Compatibility Requirements

1. Existing read-only and structured file operations must retain their current behavior unless explicitly affected by the new scoped mutation boundary.
2. Legacy unrestricted script execution must not accidentally satisfy the new provider capabilities.
3. Capability advertisement must reflect actual availability on the current Host. Do not advertise `host_mutation_sandbox_v1` when the OS sandbox provider cannot be constructed/verified.
4. Background execution preserves request/scope/lineage/script identity across job polling and completion.
5. Existing `opaque_ref` remains correlation evidence and does not replace structured lineage.

## Failure Semantics

At minimum expose stable equivalents for:

```text
HostMutationSandboxUnavailable
HostMutationScopeUnavailable
HostMutationScopeStale
HostMutationScopeExpired
HostMutationScopeBindingMismatch
HostMutationSandboxAdmissionBlocked
HostMutationProcessContainmentBlocked
HostMutationAuditUnavailable
HostMutationAuditStartWriteFailed
HostMutationAuditLineageInvalid
HostMutationAuditScriptEvidenceUnavailable
HostMutationAuditSpawnEvidenceUnavailable
HostMutationScopeTerminalizationFailed
HostMutationScopeStillActive
```

All pre-spawn security failures are fail-closed.

## Incident Regression

Canonical regression:

```text
INCIDENT-20260927-D-ROOT-RECURSIVE-DELETE
```

The Windows verification fixture must attempt representative escapes from an admitted workspace, including:

- PowerShell recursive deletion outside scope;
- `cmd.exe /c rmdir /s /q` outside scope;
- Python `shutil.rmtree` outside scope;
- .NET / Win32 filesystem deletion outside scope;
- child PowerShell/cmd/Python process mutation outside scope;
- detached/background child escape;
- junction/symlink/reparse-point escape;
- move/rename escape;
- `git clean -fdx` or equivalent outside the admitted workspace.

Fixture-owned protected sentinels representing `D:\\coco`, a canonical repo, a personal project and a sibling workspace must survive unchanged.

## Acceptance Criteria

V1 is accepted only when evidence proves all of the following:

1. `host_mutation_sandbox_v1` and `pre_execution_audit_lineage_v1` are advertised only when their real provider prerequisites are available.
2. `provision_scope`, `revalidate_scope`, and `terminalize_scope` use Host-owned authority; caller-minted authority is rejected.
3. Workspace materialization cannot occur before scope admission and durable audit START.
4. A valid scoped mutation can write inside its exact workspace.
5. The same script/process tree cannot write/delete outside the exact workspace.
6. Windows child/detached processes cannot escape the sandbox/Job boundary.
7. Audit START is durably persisted before spawn; forced audit failure proves no process starts.
8. START includes request identity, semantic lineage, scope identity/digests, process intent and durable script evidence.
9. SPAWN includes PID/PPID, final executable/cwd identity, OS identity and containment identity.
10. FINISH records terminal outcome/process-tree/read-back; forced crash may leave START without false FINISH.
11. `cleanup=true` does not erase durable forensic script evidence.
12. Scope terminalization targets the exact admitted scope/generation and read-back proves non-active state before successful completion.
13. Missing/failed terminalization or active/provisioned read-back blocks success.
14. `operator_unrestricted` is never fallback for scoped mutation and is not advertised as satisfying DevForge capabilities.
15. Authenticated Git credential execution remains separate from mutation sandbox authority.
16. Canonical incident regression proves all out-of-scope fixture sentinels survive.
17. Existing relevant SentinelX regression tests remain passing; any platform-inapplicable test is explicitly classified rather than silently skipped as proof.
18. Documentation/config examples describe opt-in unrestricted behavior, scoped mutation capability semantics, audit evidence and platform availability.

## Non-Goals

- Changing DevForge consumer contracts in this task.
- Granting the mutation sandbox normal-user credentials.
- Treating prompt instructions, string scanning, command allowlists or ordinary worktree isolation as the OS security boundary.
- Claiming Linux/macOS scoped mutation support without equivalent verified OS enforcement.
- Broad redesign of unrelated SentinelX file/service/network operations.
