# SX-HMSA-001 — Implementation Plan

## Plan State

```yaml
task_id: SX-HMSA-001
stage: plan_review
requirement: docs/requirements/SX-HMSA-001-host-mutation-sandbox-pre-execution-audit-lineage-provider-v1.md
transport: github-pr
task_branch: task/sx-host-mutation-sandbox-pre-execution-audit-lineage-provider-v1
plan_status: ready_for_review
```

## Objective

Implement the SentinelX provider side of:

```text
host_mutation_sandbox_v1
pre_execution_audit_lineage_v1
```

with Windows as the mandatory V1 OS-enforced platform and fail-closed behavior everywhere the provider cannot prove the boundary.

The existing unrestricted/best-effort paths must not be relabeled as these capabilities.

## Current Code Anchors

Primary implementation seams:

```text
src/sentinelx_core/executor.py
src/sentinelx_core/local_audit.py
src/sentinelx_core/handlers/script.py
src/sentinelx_core/handlers/__init__.py
src/sentinelx_core/policy.py
src/sentinelx_core/jobs.py
src/sentinelx_core/winspawn.py
```

Likely supporting modules to add:

```text
src/sentinelx_core/mutation_scope.py
src/sentinelx_core/mutation_audit.py
src/sentinelx_core/mutation_sandbox.py
src/sentinelx_core/windows_mutation_sandbox.py
```

Tests should stay under the repository's existing test layout and follow existing platform-gating conventions.

## Architecture

### 1. Separate ordinary telemetry from security audit

Keep `local_audit.record()` compatible for existing ordinary operations.

Add a dedicated security-critical mutation audit writer with an API shaped around lifecycle records rather than one post-hoc row:

```python
start = mutation_audit.begin(...)
# begin() returns only after durable write + flush succeeds
spawn = mutation_audit.record_spawn(start, ...)
finish = mutation_audit.finish(start, ...)
```

`begin()` must raise a named admission failure on write/durability failure. Scoped mutation catches that failure before any child process is created.

Use append-only JSONL or an equivalent simple on-host journal in V1, but make durability explicit:

```text
write complete row
flush userspace buffer
os.fsync(file descriptor)
return durable reference
```

If directory creation/first artifact creation matters for crash durability, fsync the containing directory where the platform supports it. Windows implementation must use a platform-equivalent flush guarantee rather than silently skipping durability.

### 2. Persist forensic scripts separately from temporary staging

Before START is committed:

1. normalize the exact script bytes that will be executed;
2. compute SHA-256;
3. write the bytes to a restricted evidence store outside `script_job_*` cleanup;
4. durably persist/verify the artifact;
5. include only the hash + restricted artifact reference in START.

Normal `cleanup=true` may still remove the temporary workdir after execution.

Evidence retention must be bounded/configurable and must not expose secret content through normal capability responses.

### 3. Runtime-owned mutation scope store

Add a provider-owned store independent of caller paths.

Recommended V1 storage shape:

```text
<SentinelX state dir>/mutation-scopes/
  <scope-id>.json
```

Each record includes:

```text
workspace_id
scope_id + generation
semantic lineage
exact canonical future workspace path/ref + digest
protected inventory digest
allowed operation classes
issued/expires timestamps
state
scope digest
```

Writes use atomic replace + durable flush. The store is writable only by the SentinelX service identity/provider, not by the scoped mutation worker.

Expose structured provider operations through the existing operation registry:

```text
mutation_scope_provision
mutation_scope_revalidate
mutation_scope_terminalize
```

The external operation names may differ if repository conventions require, but capability metadata must map them unambiguously to:

```text
host_mutation_sandbox_v1.provision_scope
host_mutation_sandbox_v1.revalidate_scope
host_mutation_sandbox_v1.terminalize_scope
```

`provision_scope` receives semantic identity plus placement evidence, independently canonicalizes/revalidates placement against provider-owned policy, allocates opaque IDs, and seals authority.

`revalidate_scope` never broadens authority.

`terminalize_scope` atomically moves the exact generation to terminal/revoked and returns authoritative read-back.

### 4. Explicit execution profiles

Extend mutation/script execution admission with explicit semantics:

```text
read_only
scoped_mutation
operator_unrestricted
```

Do not infer `scoped_mutation` from a cwd/path.

For `scoped_mutation`, require:

```text
mutation_scope_ref
scope generation
structured lineage
provider capability available
```

Reject missing/stale/mismatched authority before script staging or spawn.

Keep legacy unrestricted script behavior only behind explicit local operator policy. It must advertise separately and never satisfy `host_mutation_sandbox_v1`.

Suggested policy evolution:

```yaml
mutation_execution:
  operator_unrestricted_enabled: false   # safe default for new installs/config examples
  scoped_mutation_enabled: true|false    # actual capability still depends on OS provider readiness
  scope_ttl_seconds: ...
  evidence_retention: ...
```

Backward compatibility handling must be explicit in tests and release notes; do not silently reinterpret an old config as scoped authority.

### 5. Windows OS sandbox provider

Implement a dedicated `WindowsMutationSandboxProvider` behind a platform-neutral interface.

Mandatory security properties, not implementation-detail names, are the acceptance boundary:

```text
exact workspace mutation allowed
outside-scope write/delete denied by OS
child processes have same-or-less authority
no detached/breakaway escape
process tree kill-on-close/timeout
no automatic user credential inheritance
```

Preferred enforcement stack:

```text
restricted dedicated mutation identity/token
+ exact workspace/staging ACL admission
+ low-privilege/restricted token semantics
+ Windows Job Object containment
+ kill-on-job-close
+ no breakaway fallback
```

If the implementation cannot prove exact boundary semantics with this stack, use a stronger Windows primitive (for example lowbox/AppContainer-equivalent containment) rather than weakening the requirement.

Important: a Job Object alone is process containment, not a filesystem authorization boundary. Likewise path checks alone are not a sandbox.

The provider must perform a self-check before advertising `host_mutation_sandbox_v1`. If the restricted identity/token, filesystem confinement or Job containment cannot be established, capability is unavailable.

### 6. Scoped process spawn seam

Refactor `script.py` so argv/env/encoding behavior remains reusable, but actual spawn is delegated:

```text
prepare_script
build_process_intent
admit scope
persist durable START
sandbox.spawn(process_intent)
persist SPAWN
wait/timeout/cancel under containment
persist FINISH
terminalize/read-back when requested by lifecycle owner
```

Do not write START from `Executor.dispatch()` after handler return. The handler/provider must own pre-spawn audit because only it knows the exact process intent and sandbox identity before spawn.

`Executor.dispatch()` may continue to write ordinary post-operation telemetry separately.

Background jobs must preserve the same request/scope/lineage/evidence references in durable job state.

### 7. Capability advertisement

Extend hello/capabilities so the agent advertises:

```text
host_mutation_sandbox_v1
pre_execution_audit_lineage_v1
```

only when runtime self-check proves the required provider is available.

Do not advertise based merely on code presence or configuration text.

Recommended provider readiness check:

```text
policy allows scoped mutation
+ authority store is secure/writable
+ mutation audit store is secure/writable
+ durable evidence store is secure/writable
+ OS sandbox provider self-check passes
+ required process containment primitive is available
```

Linux/macOS V1 returns capability unavailable unless an equivalent provider is actually implemented and verified.

## Proposed Execution Slices

These are proposed slices for Plan Review; review may refine boundaries before implementation.

### Slice 1 — Provider contracts, policy and capability readiness

Implement:

- execution-profile model;
- policy/config parsing and safe defaults;
- provider readiness/self-check abstraction;
- capability advertisement rules;
- failure-code model;
- no legacy unrestricted path can claim scoped capability.

Verification:

- unit matrix for Windows-ready/not-ready, Linux/macOS unavailable, policy disabled, missing secure stores;
- capability names disappear when prerequisites are absent;
- legacy script path remains distinguishable from scoped mutation.

Checkpoint:

```text
No OS mutation behavior changed yet; capability semantics cannot lie.
```

### Slice 2 — Host-owned mutation scope authority lifecycle

Implement:

- durable scope store;
- `provision_scope`;
- `revalidate_scope`;
- `terminalize_scope`;
- generation/TTL/revocation/state handling;
- lineage + exact placement binding;
- digest/read-back receipts.

Negative tests:

- caller-minted scope;
- stale generation;
- cross-Run/Attempt/Slice;
- wrong workspace;
- placement drift;
- expired/revoked/terminal reuse;
- terminalize wrong generation;
- active-after-terminalization impossible.

Checkpoint:

```text
Authority exists before filesystem materialization and cannot be minted from caller paths.
```

### Slice 3 — Durable mutation audit + forensic script evidence

Implement:

- security audit journal;
- durable `OPERATION_STARTED`;
- retained script artifact + SHA-256;
- SPAWN and FINISH rows;
- structured request/opaque_ref/lineage identity;
- crash/interruption semantics;
- retention/access control.

Tests:

- injected audit write failure => spawn callback never invoked;
- fsync/flush failure => spawn never invoked;
- `cleanup=true` leaves forensic artifact;
- forced crash leaves START without fabricated FINISH;
- missing lineage when required fails before spawn;
- background job retains same identity binding.

Checkpoint:

```text
No durable START => no process creation.
```

### Slice 4 — Windows sandbox identity + Job containment

Implement:

- restricted mutation identity/token provider;
- exact workspace/staging ACL admission and cleanup/revocation semantics;
- Job Object creation/configuration;
- assign process before untrusted work can run;
- no breakaway;
- kill-on-close;
- process-tree timeout/cancel;
- sandbox identity/containment receipt.

Use fixture-owned temporary roots only. Never test against real `D:\coco` or user repositories.

Tests must prove:

- write inside admitted workspace succeeds;
- sibling/parent/protected fixture write and delete fail;
- nested child attack fails;
- detached/background attempt cannot outlive/escape containment;
- junction/reparse escape fails;
- unavailable/failed sandbox setup causes no child spawn.

Checkpoint:

```text
Windows scoped mutation boundary is enforced by OS primitives, not text/path discipline.
```

### Slice 5 — Scoped script execution integration

Refactor/integrate `handlers/script.py` without regressing its existing interpreter, Unicode, cwd, timeout and background semantics.

For `scoped_mutation`:

```text
scope revalidate
→ durable evidence + START
→ OS-contained spawn
→ SPAWN
→ result/timeout/cancel
→ FINISH
```

Keep operator-unrestricted behavior separate and explicit.

Regression focus:

- powershell / pwsh / python3 paths;
- cwd behavior;
- Unicode behavior;
- timeout process-tree behavior;
- no sudo/elevation upgrade into scoped mode;
- env cannot override authority/sandbox identity;
- user-scoped Git credentials are not inherited by sandbox process.

Checkpoint:

```text
Existing script ergonomics remain, but scoped mutation has a separate enforceable security path.
```

### Slice 6 — Incident regression, docs and release readiness

Create canonical fixture:

```text
INCIDENT-20260927-D-ROOT-RECURSIVE-DELETE
```

Within a temporary synthetic root, create:

```text
root/
  admitted-workspace/
  sibling-workspace/MUST_SURVIVE
  canonical-repo/MUST_SURVIVE
  personal-project/MUST_SURVIVE
  parent-sentinel/MUST_SURVIVE
```

Run representative PowerShell/cmd/Python/.NET/Win32/reparse/move/git-clean attacks from the admitted scope and prove only the admitted workspace can change.

Also update:

- README security/tool semantics;
- Windows config example;
- generic config example;
- SECURITY/THREAT_MODEL if required by existing documentation ownership;
- CHANGELOG/release note entry.

Checkpoint:

```text
Provider evidence satisfies the consumer contract and the incident family is a permanent regression.
```

## Verification Strategy

### Static / unit

- policy and capability matrices;
- scope lifecycle state machine;
- digest/identity binding;
- audit record schema and ordering;
- injected failure paths;
- receipt identity matching.

### Windows integration

Must run on a real Windows host/provider environment capable of the same service mode used in production.

Required proof includes:

```text
service identity
sandbox identity
workspace ACL state
Job Object / containment identity
root PID + child PIDs
START timestamp/ref
SPAWN timestamp/ref
FINISH timestamp/ref or intentional absence after crash
terminal scope read-back
protected fixture hashes/existence before and after
```

### Existing regression suite

Run targeted existing suites around:

```text
script_run
executor/audit
background jobs
Windows spawning
file operations
policy/capabilities
user-scoped Git
```

Then run the broad suite available on the target platform. Platform-incompatible collection failures must be identified separately; they are not evidence that this task passed.

## Safety Rules During Implementation

1. Never use `D:\coco`, a real user project, canonical checkout or real protected directory as a destructive test target.
2. All destructive regression attacks run only inside disposable fixture roots created specifically for the test.
3. No recursive delete fallback outside fixture-owned paths.
4. Do not weaken existing file-op path canonicalization or Git credential boundaries to make scoped mutation work.
5. Never mark `host_mutation_sandbox_v1` available until the real OS enforcement self-check passes.
6. Provider unavailability is an acceptable fail-closed V1 outcome on unsupported hosts.

## Completion Evidence

Implementation is a completion candidate only when it can return evidence equivalent to:

```yaml
provider_capabilities:
  host_mutation_sandbox_v1: verified
  pre_execution_audit_lineage_v1: verified
scope:
  producer: provision_scope
  revalidation: verified
  terminalization: verified_non_active
audit:
  started_before_spawn: true
  request_lineage_verified: true
  script_evidence_retained: true
process:
  sandbox_identity_verified: true
  containment_verified: true
incident_regression:
  admitted_workspace_mutation: allowed
  out_of_scope_mutation: denied
  protected_sentinels_intact: true
legacy_regressions:
  status: pass_or_explicitly_classified
```
