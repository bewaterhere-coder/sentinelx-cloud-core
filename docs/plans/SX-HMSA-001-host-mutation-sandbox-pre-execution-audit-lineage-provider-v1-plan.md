# SX-HMSA-001 — Implementation Plan

## Plan State

```yaml
task_id: SX-HMSA-001
stage: plan_review
requirement: docs/requirements/SX-HMSA-001-host-mutation-sandbox-pre-execution-audit-lineage-provider-v1.md
transport: github-pr
task_branch: task/sx-host-mutation-sandbox-pre-execution-audit-lineage-provider-v1
plan_status: revised_ready_for_review
plan_revision: 2
```

## Objective

Implement the SentinelX provider side of:

```text
host_mutation_sandbox_v1
pre_execution_audit_lineage_v1
```

with Windows as the mandatory V1 OS-enforced platform and fail-closed behavior everywhere the provider cannot prove the boundary.

The existing unrestricted/best-effort paths must not be relabeled as these capabilities.

## Plan Review Remediation — Authoritative Decisions

This revision closes the first Plan Review findings and supersedes any earlier ambiguous design choice in this plan.

The following decisions are fixed for V1:

1. **Workspace placement authority is Host/provider-owned.** SentinelX owns one explicit scoped-mutation workspace-root policy and a deterministic placement resolver. Caller `cwd`, `workspace_root`, `file_ops` rw paths, remembered paths, or arbitrary path strings are evidence only and cannot mint or select authority.
2. **Windows V1 sandbox primitive is fixed to AppContainer + exact ACL + Job Object containment.** V1 does not fall back from AppContainer to a restricted service token, normal user token, LocalSystem, unrestricted PowerShell, or path-only checking.
3. **The trusted SentinelX broker materializes the exact empty workspace only after durable `OPERATION_STARTED`.** The broker creates the directory, applies an exact scope-specific AppContainer ACL, validates it, creates the process suspended, assigns it to a no-breakaway kill-on-close Job Object, records spawn evidence, then resumes the first untrusted instruction.
4. **Transport identity reaches the mutation handler through an immutable `RequestContext` built by `Executor` from `RequestMessage`.** Payload cannot supply or override authoritative `request_id` or `opaque_ref`.
5. **Legacy unrestricted compatibility is isolated from the new execution profiles.** Old configs that do not contain a `mutation_execution` block retain historical unprofiled `script_run` compatibility, but that path is internally classified as `legacy_unrestricted_compat`, never advertises or satisfies `host_mutation_sandbox_v1`, and cannot be selected by a DevForge scoped request. New configs contain an explicit `mutation_execution` block with `operator_unrestricted_enabled: false`.

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

Supporting modules to add:

```text
src/sentinelx_core/request_context.py
src/sentinelx_core/mutation_placement.py
src/sentinelx_core/mutation_scope.py
src/sentinelx_core/mutation_audit.py
src/sentinelx_core/mutation_sandbox.py
src/sentinelx_core/windows_mutation_sandbox.py
```

Tests stay under the repository's existing test layout and follow existing platform-gating conventions.

## Architecture

### 1. Authoritative RequestContext seam

Current `Executor.dispatch()` passes only `request.payload` to a handler. That is insufficient for security audit because `request.id` and `request.opaque_ref` are transport-level values and must not be reconstructed from caller payload.

Introduce an immutable executor-created context:

```python
@dataclass(frozen=True)
class RequestContext:
    request_id: str
    op: str
    opaque_ref: str | None
    received_at: datetime
```

Creation rule:

```text
RequestMessage
→ Executor constructs RequestContext from RequestMessage fields
→ handler invocation receives RequestContext + payload
```

The payload is never authoritative for:

```text
request_id
opaque_ref
received_at
op
```

A payload containing fields with the same names is ignored for transport identity or rejected when the scoped schema forbids them.

To avoid a broad semantic rewrite of all existing handlers, standardize the registry around a context-aware invocation adapter:

```python
Handler = Callable[[RequestContext, dict[str, Any]], Awaitable[dict[str, Any]]]
```

Existing payload-only handlers are wrapped by a compatibility adapter that deliberately discards `RequestContext`. New mutation-scope and scoped-script handlers consume it directly.

Semantic lineage remains distinct:

```text
request_id   = transport identity from RequestMessage
opaque_ref   = optional transport correlation from RequestMessage
lineage      = semantic project/task/run/attempt[/slice] supplied as intent,
               then independently verified against provider-owned scope state
```

No payload field may substitute for transport identity.

Background work captures the exact `RequestContext` before scheduling and stores an immutable job binding containing:

```text
request_id
opaque_ref
scope_id + generation
workspace_id
semantic lineage digest
script_sha256
sandbox identity
containment id when known
```

Completion events and audit FINISH reuse that binding; they must not reconstruct identity from a completion payload.

### 2. Provider-owned canonical workspace placement authority

#### 2.1 Host policy

Add a Host-owned policy block:

```yaml
mutation_execution:
  scoped_mutation_enabled: false
  workspace_root: <absolute-host-owned-root>
  protected_roots:
    - <provider-owned-protected-root>
  runtime_read_roots:
    - <immutable-interpreter-or-runtime-root>
  scope_ttl_seconds: 3600
  evidence_retention_days: 30
  operator_unrestricted_enabled: false
```

Security rules:

- `workspace_root`, `protected_roots`, and `runtime_read_roots` come only from SentinelX Host configuration.
- They are not derived from `file_ops` rw entries.
- `file_ops` rw permission does not grant scoped-mutation placement authority.
- Caller `cwd`, `workspace_root`, `allowed_write_root(s)`, `protected_roots`, or arbitrary path values are comparison evidence only.
- Configuration load canonicalizes the roots and rejects overlap that would make the scoped workspace ambiguous or place it beneath a protected root.
- The state/audit/evidence stores are provider control-plane roots and are never caller-selected mutation roots.

#### 2.2 Deterministic placement resolver

Placement is derived from canonical repository identity plus semantic Attempt identity:

```text
repository identity:
  vcs + authority + path
semantic identity:
  project_id + task_id + run_id + attempt_id + optional slice_id
Host placement policy:
  workspace_root + placement_generation
```

Use stable canonical encoding and SHA-256 to derive bounded path-safe keys:

```text
repo_key    = short_digest(vcs, authority, path)
attempt_key = short_digest(project_id, task_id, run_id, attempt_id, slice_id)
future_workspace = workspace_root / repo_key / attempt_key
```

Human-readable labels may be stored in metadata but do not participate in authority or path construction.

This means caller strings cannot inject `..`, alternate drive letters, UNC roots, sibling names, or arbitrary local paths into the authoritative future workspace.

The resolver returns:

```yaml
placement:
  placement_ref: <opaque-provider-ref>
  generation: <positive-generation>
  policy_digest: <sha256>
  exact_future_workspace: <provider-derived-absolute-path>
  exact_workspace_digest: <sha256>
  repository_identity_digest: <sha256>
  semantic_identity_digest: <sha256>
  protected_inventory_digest: <sha256>
```

#### 2.3 Placement generation and drift

SentinelX keeps provider-owned placement state:

```text
normalized placement policy digest
+ monotonically increasing placement_generation
```

On startup/reload:

```text
same normalized policy digest
→ generation unchanged

changed workspace root / protected roots / runtime read roots / placement rules
→ generation increments and new policy digest is persisted
```

`provision_scope` seals placement generation + digest into the scope record.

`revalidate_scope` re-runs placement resolution from the current Host policy and exact semantic/repository identity. Any mismatch in:

```text
placement generation
policy digest
exact future workspace
protected inventory digest
repository identity digest
semantic identity digest
```

returns `HostMutationScopeBindingMismatch` before materialization or later mutation.

A stale scope is never retargeted to a new path.

#### 2.4 Protected inventory derivation

Protected inventory is provider-derived and includes at minimum:

- configured `protected_roots`;
- the workspace root itself except the exact admitted descendant;
- all existing sibling workspace entries visible under the derived repository/attempt parents;
- provider state/audit/evidence roots unless explicitly read-only to the sandbox;
- canonical repository roots configured as protected Host roots;
- any parent path whose mutation could rename/delete the exact workspace or its siblings.

The AppContainer receives no write ACE on these objects. Their normalized identities/digests are sealed into scope evidence.

### 3. Runtime-owned mutation scope store

Add a provider-owned store independent of caller paths:

```text
<SentinelX state dir>/mutation-scopes/
  <scope-id>.json
```

Each record includes:

```text
workspace_id
scope_id + generation
semantic lineage + digest
repository identity + digest
placement ref/generation/policy digest
exact canonical future workspace + digest
protected inventory digest
allowed operation classes
issued/expires timestamps
state
scope digest
sandbox identity metadata when activated
containment ids / active process bindings when present
```

Writes use atomic replace + durable flush. The store is broker-only: the AppContainer worker has no write access.

Expose structured provider operations:

```text
mutation_scope_provision
mutation_scope_revalidate
mutation_scope_terminalize
```

They map unambiguously to:

```text
host_mutation_sandbox_v1.provision_scope
host_mutation_sandbox_v1.revalidate_scope
host_mutation_sandbox_v1.terminalize_scope
```

`provision_scope` inputs are limited to semantic/repository identity plus optional expected placement evidence. SentinelX independently resolves the authoritative placement and allocates opaque `workspace_id` and `scope_id`.

`revalidate_scope` never broadens authority.

`terminalize_scope` targets exact `scope_id + generation`, prevents new spawn, terminates any still-bound Job/process tree, revokes scope-specific workspace write authority, disposes the scope AppContainer profile when safe, moves the record to terminal/revoked, and returns authoritative non-active read-back.

Terminalization failure returns `HostMutationScopeTerminalizationFailed`; a read-back still showing `active` or `provisioned` returns `HostMutationScopeStillActive`. Neither may produce successful completion.

### 4. Separate ordinary telemetry from security audit

Keep `local_audit.record()` compatible for existing ordinary operations.

Add a security-critical mutation audit journal:

```python
start = mutation_audit.begin(...)
spawn = mutation_audit.record_spawn(start, ...)
finish = mutation_audit.finish(start, ...)
```

`begin()` returns only after the START record is durably committed.

V1 journal semantics:

```text
append complete JSON record
flush userspace buffer
FlushFileBuffers/os.fsync equivalent
return durable record reference
```

Audit failure before untrusted execution is fail-closed.

The required lifecycle is:

```text
REQUEST_RECEIVED
→ ADMISSION_VERIFIED
→ OPERATION_STARTED [durable]
→ trusted workspace materialization / ACL preparation
→ suspended sandbox process creation
→ Job assignment
→ PROCESS_SPAWNED evidence
→ ResumeThread / first untrusted instruction
→ OPERATION_FINISHED
```

This ordering is deliberate: the broker may perform security-control-plane materialization only after START, while untrusted code cannot execute until containment is fully installed.

If `PROCESS_SPAWNED` evidence cannot be recorded after suspended process creation but before resume, the broker terminates the suspended process/Job and returns `HostMutationAuditSpawnEvidenceUnavailable`; it does not resume the child.

### 5. Persist forensic scripts separately from temporary staging

Before START is committed:

1. normalize the exact script bytes that will later be materialized for execution;
2. compute SHA-256;
3. write those bytes to the restricted provider evidence store;
4. durably persist/verify the artifact;
5. record `script_sha256 + script_artifact_ref` in START.

The future executable script path is deterministic under the exact workspace, for example a provider-owned `.sentinelx-exec` child beneath that workspace. START may record this intended final path before the directory exists.

After START and trusted workspace materialization, the broker writes/copies the exact retained bytes into the final script path and verifies the hash again before process creation.

The AppContainer gets no write access to the forensic evidence store. `cleanup=true` may remove ordinary execution staging but cannot remove the forensic artifact.

### 6. Fixed Windows V1 sandbox primitive

#### 6.1 Primitive choice

Windows V1 uses:

```text
scope-specific AppContainer profile/SID
+ exact ACL grants on the admitted workspace
+ provider-owned read/execute grants only for required immutable runtime roots when necessary
+ no network capability by default
+ Windows Job Object with kill-on-close and no breakaway
+ suspended process creation and pre-resume Job assignment
```

There is **no V1 fallback** from this primitive to:

```text
LocalSystem execution
interactive user execution
CreateRestrictedToken-only execution
ordinary user token
PowerShell policy/string filtering
path validation alone
uncontained subprocess execution
```

If AppContainer construction, ACL verification, interpreter launch, or Job containment self-check fails, `host_mutation_sandbox_v1` is unavailable.

#### 6.2 Trusted bootstrap sequence

For the first materialization/spawn under a provisioned scope:

```text
1. Executor builds authoritative RequestContext.
2. Scoped handler validates semantic lineage against scope authority.
3. revalidate_scope confirms current placement/generation/protected inventory.
4. Exact script evidence is retained and hashed in broker-only evidence storage.
5. OPERATION_STARTED is durably committed.
6. Trusted SentinelX broker creates ONLY the exact derived empty workspace path.
7. Broker creates/loads the scope-specific AppContainer profile and SID.
8. Broker disables inheritance on the exact workspace DACL and installs explicit scope ACLs.
9. Broker verifies the AppContainer SID has required workspace rights and no write/delete/create-child rights on parent/sibling/protected objects.
10. Broker materializes the exact script bytes inside the admitted workspace and verifies SHA-256.
11. Broker creates a Job Object with kill-on-close; breakaway is not enabled.
12. Broker creates the process suspended with AppContainer security capabilities, CREATE_SUSPENDED, EXTENDED_STARTUPINFO_PRESENT, CREATE_NO_WINDOW, and handle inheritance disabled.
13. Broker assigns the still-suspended process to the Job Object.
14. Broker verifies Job membership / sandbox identity and records PROCESS_SPAWNED evidence.
15. Only after all checks succeed does Broker ResumeThread.
16. Timeout/cancel closes/terminates the Job and verifies the root/children have exited.
17. OPERATION_FINISHED records result/process-tree/scope read-back evidence.
18. Lifecycle owner later invokes exact-scope terminalization; successful DevForge completion requires terminal non-active read-back.
```

If any step from 6 through 14 fails, no untrusted instruction is resumed. Any suspended process is terminated and the operation fails closed.

#### 6.3 Exact filesystem authority

The AppContainer SID receives write/modify rights only on:

```text
exact admitted workspace and descendants
scope-specific provider scratch/profile storage if Windows requires it
```

Provider audit/evidence/scope stores remain broker-only.

Required interpreter/runtime files are either already AppContainer-readable or receive **read/execute only** provider-owned grants on explicitly configured immutable `runtime_read_roots`. No write grant is permitted there.

The scope-specific AppContainer SID receives no write/create-child/delete rights on the parent workspace tree, sibling workspaces, protected roots, canonical repositories, or arbitrary drive roots.

Because the exact workspace child is created by the trusted broker, the sandbox identity never needs parent create-child authority to bootstrap itself.

#### 6.4 Reparse points and path finalization

Before ACL install, before script materialization, and immediately before spawn, the broker opens/validates the final workspace path using Windows final-path/reparse-aware APIs. The exact workspace must not resolve through a caller-controlled junction/symlink/reparse point.

Creation uses no-follow/reparse-safe semantics where available. A reparse point inserted after provisioning or during execution causes admission/read-back failure rather than retargeting authority.

#### 6.5 Process containment

The Job Object must use kill-on-close semantics and must not set breakaway flags.

The root process is created suspended and assigned before resume. Children inherit Job membership under normal Windows Job semantics; attempts to request breakaway are denied because the Job does not permit it.

Background mode may keep the Job handle in provider-owned durable job state, but caller disconnect does not remove scope identity or audit lineage. Explicit cancel/timeout/terminalization terminates the Job tree.

### 7. Execution profiles and legacy compatibility

Public/new execution profiles:

```text
read_only
scoped_mutation
operator_unrestricted
```

Internal compatibility classification:

```text
legacy_unrestricted_compat
```

Rules:

#### New explicit profiles

`scoped_mutation` requires:

```text
host_mutation_sandbox_v1 available
mutation_scope_ref + current generation
validated semantic lineage
RequestContext from Executor
```

`operator_unrestricted` requires an explicit policy block:

```yaml
mutation_execution:
  operator_unrestricted_enabled: true
```

It never satisfies `host_mutation_sandbox_v1` and cannot be a fallback from scoped mode.

#### Existing config migration

Compatibility is determined structurally:

```text
mutation_execution block absent
→ preserve historical unprofiled script_run behavior as legacy_unrestricted_compat
→ emit operator-visible migration/security warning
→ do NOT advertise host_mutation_sandbox_v1 because of that path
→ reject any request that explicitly asks for operator_unrestricted unless policy opts in
→ scoped_mutation still requires full new provider readiness

mutation_execution block present
→ missing operator_unrestricted_enabled means false
→ unprofiled legacy script behavior follows the explicit block's compatibility setting/defaults
```

New installer/config examples include the block explicitly with:

```yaml
mutation_execution:
  operator_unrestricted_enabled: false
  scoped_mutation_enabled: false
```

This preserves upgraded old-host behavior without treating omission as explicit authorization for the new unrestricted profile, while giving new configurations a safe explicit default.

Tests must cover old-config omission, new-block omission, explicit true/false, unprofiled legacy requests, explicit operator requests, and scoped requests.

### 8. Scoped script execution integration

Refactor `handlers/script.py` into preparation and execution seams while preserving existing interpreter/Unicode/cwd/output behavior for legacy mode.

Scoped path:

```text
RequestContext
→ validate scoped payload schema
→ scope revalidate
→ prepare normalized script bytes/process intent
→ persist forensic artifact
→ durable START
→ trusted workspace materialization + ACL
→ suspended AppContainer spawn
→ Job assignment
→ SPAWN audit
→ resume
→ wait/timeout/cancel under containment
→ FINISH audit
```

Security rules:

- `cwd` for scoped mode must equal or be a provider-derived descendant allowed by the scope; caller cannot move execution outside the exact workspace.
- `sudo`/elevation is forbidden in scoped mode.
- environment cannot override scope identity, sandbox SID, evidence paths, audit paths, credential context, AppContainer attributes, Job identity, or placement.
- user-scoped Git credentials are not injected. Authenticated Git stays in the separate structured Git executor/broker.
- an explicit failure in scoped mode never falls back to legacy or operator-unrestricted execution.

### 9. Capability advertisement

Advertise:

```text
host_mutation_sandbox_v1
pre_execution_audit_lineage_v1
```

only when runtime self-check proves all required provider components are ready.

Readiness matrix:

```text
Windows
+ scoped_mutation_enabled
+ valid provider-owned workspace-root policy
+ placement state/generation store healthy
+ scope store secure/writable
+ mutation audit journal secure/writable + durable flush self-check
+ evidence store secure/writable
+ AppContainer APIs/profile self-check
+ exact ACL admission/read-back self-check
+ configured interpreter/runtime read access self-check
+ Job Object create/assign/kill-on-close self-check
+ suspended-create-before-resume self-check
→ advertise both capabilities
```

Any failed prerequisite removes the capability evidence and returns the relevant fail-closed reason when scoped execution is requested.

Linux/macOS V1 do not advertise `host_mutation_sandbox_v1` unless an equivalent provider is separately implemented and verified.

## Proposed Execution Slices

These slices are the durable execution set to compile if Plan Review approves.

### Slice 1 — RequestContext, policy migration, placement authority, capability truthfulness

Implement:

- immutable `RequestContext` + legacy-handler adapter;
- `mutation_execution` policy parsing and migration semantics;
- canonical repository/semantic placement resolver;
- placement generation/policy digest state;
- provider readiness model;
- capability advertisement matrix;
- no legacy path can claim scoped capability.

Verification:

- payload cannot spoof `request_id`/`opaque_ref`;
- old config with no block preserves only `legacy_unrestricted_compat`;
- new block defaults operator-unrestricted false;
- arbitrary `cwd/workspace_root/file_ops` path cannot select placement;
- path traversal/drive/UNC input cannot affect canonical future workspace;
- policy drift increments generation and invalidates stale placement evidence;
- capability absent on unsupported/not-ready host.

Checkpoint:

```text
Transport identity and workspace placement authority are provider-owned before scope state exists.
```

### Slice 2 — Host-owned mutation scope lifecycle

Implement:

- durable scope store;
- `provision_scope`;
- `revalidate_scope`;
- `terminalize_scope`;
- generation/TTL/revocation/state handling;
- semantic/repository/placement/protected-inventory binding;
- authoritative read-back receipts.

Negative tests:

- caller-minted scope;
- stale generation;
- cross-Run/Attempt/Slice;
- wrong repository/workspace;
- placement drift;
- expired/revoked/terminal reuse;
- terminalize wrong generation;
- active-after-terminalization blocked.

Checkpoint:

```text
Scope authority exists before filesystem materialization and cannot be minted from caller paths.
```

### Slice 3 — Durable mutation audit + forensic script evidence

Implement:

- security audit journal;
- durable `OPERATION_STARTED`;
- retained script artifact + SHA-256;
- SPAWN and FINISH records;
- RequestContext + semantic-lineage separation;
- crash/interruption semantics;
- background identity binding;
- retention/access control.

Tests:

- injected START write/flush failure => workspace/process spawn callback never invoked;
- SPAWN audit failure while child is suspended => child terminated, never resumed;
- `cleanup=true` leaves forensic artifact;
- forced crash leaves START without fabricated FINISH;
- missing/mismatched lineage fails before spawn;
- background job preserves original RequestContext/scope/script identity.

Checkpoint:

```text
No durable START => no workspace materialization or untrusted process execution.
```

### Slice 4 — Windows AppContainer + ACL + suspended Job containment

Implement:

- scope-specific AppContainer profile/SID lifecycle;
- exact workspace broker creation after START;
- protected/non-inherited workspace DACL;
- read/execute-only runtime roots as needed;
- reparse-safe final-path verification;
- Job Object kill-on-close/no-breakaway;
- suspended process creation + pre-resume Job assignment;
- process-tree timeout/cancel;
- sandbox/containment receipt;
- terminalization cleanup/revocation.

Use fixture-owned temporary roots only. Never test against real `D:\coco` or user repositories.

Tests prove:

- write inside admitted workspace succeeds;
- parent/sibling/protected fixture create/write/delete fail;
- child attack fails;
- detached/background child cannot escape Job;
- reparse/junction escape fails;
- move/rename escape fails;
- AppContainer/ACL/Job setup failure causes no resumed child;
- terminalization revokes scope SID authority and leaves non-active read-back.

Checkpoint:

```text
Windows scoped mutation boundary is enforced by AppContainer filesystem authority plus pre-resume Job containment.
```

### Slice 5 — Scoped script execution integration

Integrate the scoped provider with `handlers/script.py` while preserving legacy script behavior outside the new profile.

Regression focus:

- powershell / pwsh / python3 process-intent preparation;
- Unicode behavior;
- cwd descendant validation;
- timeout process-tree behavior;
- no sudo/elevation in scoped mode;
- env cannot override authority/sandbox identity;
- normal-user Git credentials not inherited;
- scoped failure never falls back to legacy/operator-unrestricted.

Checkpoint:

```text
Existing script ergonomics remain for legacy callers; scoped mutation is a distinct enforceable path.
```

### Slice 6 — Incident regression, docs and release readiness

Create canonical fixture:

```text
INCIDENT-20260927-D-ROOT-RECURSIVE-DELETE
```

Inside a disposable synthetic root create:

```text
root/
  workspace-root/
    admitted-workspace/
    sibling-workspace/MUST_SURVIVE
  canonical-repo/MUST_SURVIVE
  personal-project/MUST_SURVIVE
  parent-sentinel/MUST_SURVIVE
```

Run representative escape attempts from the admitted AppContainer:

- PowerShell recursive deletion outside scope;
- `cmd.exe /c rmdir /s /q` outside scope;
- Python `shutil.rmtree` outside scope;
- .NET/Win32 deletion outside scope;
- child PowerShell/cmd/Python mutation outside scope;
- detached/background escape;
- junction/symlink/reparse-point escape;
- move/rename escape;
- `git clean -fdx` or equivalent against a protected fixture.

Prove all protected sentinels survive unchanged.

Update:

- README security/tool semantics;
- Windows config example;
- generic config example;
- SECURITY/THREAT_MODEL as required;
- CHANGELOG/release note entry.

Checkpoint:

```text
Provider evidence satisfies the DevForge consumer contract and the incident family is a permanent regression.
```

## Verification Strategy

### Static / unit

- RequestContext provenance/spoofing tests;
- policy migration matrix;
- placement resolver determinism and drift;
- scope lifecycle state machine;
- digest/identity binding;
- audit record schema and ordering;
- injected audit failure paths;
- receipt identity matching;
- explicit no-fallback tests.

### Windows integration

Must run on a real Windows host/provider environment capable of the service mode used in production.

Required proof includes:

```text
service identity
AppContainer name/SID
workspace final path + DACL read-back
parent/sibling/protected DACL/access checks
Job Object / containment identity
root PID + child PIDs
proof process was created suspended and assigned before resume
START timestamp/ref
SPAWN timestamp/ref
FINISH timestamp/ref or intentional absence after crash
scope terminal read-back
protected fixture hashes/existence before and after
```

A unit mock of AppContainer/Job APIs is not sufficient acceptance evidence for the Windows sandbox criterion.

### Existing regression suite

Run targeted suites around:

```text
script_run
executor/audit
background jobs
Windows spawning
file operations
policy/capabilities
user-scoped Git
```

Then run the broad suite available on the target platform. Platform-incompatible collection failures must be classified separately and never reported as task PASS evidence.

## Safety Rules During Implementation

1. Never use `D:\coco`, a real user project, canonical checkout, or real protected directory as a destructive test target.
2. All destructive regression attacks run only inside disposable fixture roots created specifically for the test.
3. No recursive delete fallback outside fixture-owned paths.
4. Do not weaken existing file-op path canonicalization or Git credential boundaries to make scoped mutation work.
5. Never mark `host_mutation_sandbox_v1` available until the real AppContainer + ACL + Job self-check passes.
6. Provider unavailability is an acceptable fail-closed V1 outcome on unsupported/not-ready hosts.
7. Do not implement a restricted-token/LocalSystem fallback if AppContainer readiness fails.
8. Workspace materialization by the trusted broker is allowed only for the exact provider-derived future workspace after durable START.

## Completion Evidence

Implementation is a completion candidate only when it can return evidence equivalent to:

```yaml
provider_capabilities:
  host_mutation_sandbox_v1: verified
  pre_execution_audit_lineage_v1: verified
request_context:
  request_id_source: RequestMessage
  opaque_ref_source: RequestMessage
  payload_spoofing_rejected: true
placement:
  authority: runtime_host_owned
  generation_verified: true
  exact_workspace_verified: true
  caller_path_authority: false
scope:
  producer: provision_scope
  revalidation: verified
  terminalization: verified_non_active
audit:
  started_before_workspace_materialization: true
  started_before_untrusted_spawn: true
  request_lineage_verified: true
  script_evidence_retained: true
process:
  sandbox_identity: appcontainer
  workspace_acl_verified: true
  suspended_before_job_assignment: true
  containment_verified: true
  breakaway_allowed: false
incident_regression:
  admitted_workspace_mutation: allowed
  out_of_scope_mutation: denied
  protected_sentinels_intact: true
legacy_regressions:
  status: pass_or_explicitly_classified
```
