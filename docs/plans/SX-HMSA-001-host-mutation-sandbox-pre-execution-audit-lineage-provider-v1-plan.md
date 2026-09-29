# SX-HMSA-001 — Implementation Plan

## Plan State

```yaml
task_id: SX-HMSA-001
stage: accepted
requirement: docs/requirements/SX-HMSA-001-host-mutation-sandbox-pre-execution-audit-lineage-provider-v1.md
transport: github-pr
task_branch: task/sx-host-mutation-sandbox-pre-execution-audit-lineage-provider-v1
plan_status: approved
execution_state: completed
acceptance_approved: true
completion_verified: false
plan_revision: 3
```

## Objective

Implement the SentinelX provider side of:

```text
host_mutation_sandbox_v1
pre_execution_audit_lineage_v1
```

Windows is the mandatory V1 enforcement platform. Everywhere the provider cannot prove the required boundary, scoped mutation fails closed.

The existing unrestricted/best-effort paths must never be relabeled as these capabilities.

## Authoritative V1 Decisions

The following decisions are fixed and must not be deferred to an implementation slice:

1. **Workspace placement authority is Host/provider-owned.** SentinelX owns one scoped-mutation workspace-root policy and deterministic placement resolver. Caller `cwd`, `workspace_root`, `file_ops` rw roots, remembered paths, and arbitrary path strings are evidence only.
2. **Windows V1 sandbox primitive is AppContainer + exact ACL + Job Object containment.** No fallback to LocalSystem execution, ordinary/restricted service token, interactive-user execution, unrestricted shell, or path-only checking.
3. **Trusted broker bootstrap happens only after durable `OPERATION_STARTED`.** The broker creates the exact provider-derived workspace, installs/verifies exact ACLs, creates the untrusted process suspended, assigns it to a no-breakaway kill-on-close Job, records spawn evidence, and only then resumes the first instruction.
4. **Transport identity enters through immutable `RequestContext`.** `request_id` and `opaque_ref` come from `RequestMessage`, not from payload.
5. **Legacy unrestricted compatibility is isolated.** Old configs without `mutation_execution` retain historical unprofiled `script_run` only as `legacy_unrestricted_compat`; that path never satisfies or advertises the new capabilities. Explicit `operator_unrestricted` requires explicit policy opt-in.
6. **Mutation authority is a unique provider-owned lease.** For one canonical repository identity + Run/Attempt[/Slice] + placement generation + exact workspace digest, at most one non-terminal mutation-scope lease may exist. Retry/resume reuses that lease; it does not mint another active scope or AppContainer SID.

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

## 1. Authoritative RequestContext Seam

Current `Executor.dispatch()` passes only `request.payload` to handlers. Scoped mutation requires transport identity that payload cannot spoof.

Introduce:

```python
@dataclass(frozen=True)
class RequestContext:
    request_id: str
    op: str
    opaque_ref: str | None
    received_at: datetime
```

Canonical flow:

```text
RequestMessage
→ Executor constructs RequestContext from transport fields
→ scoped/context-aware handler receives RequestContext + payload
```

Payload is never authoritative for:

```text
request_id
opaque_ref
received_at
op
```

Registry compatibility may wrap existing payload-only handlers and deliberately discard `RequestContext`; new scope/scoped-script handlers consume it directly.

Semantic lineage remains separate:

```text
request_id = transport identity
opaque_ref = optional transport correlation
lineage    = project/task/run/attempt[/slice] intent, later verified against provider-owned scope state
```

Background work captures the original context and immutable job binding. START, SPAWN, FINISH, polling, cancel, and completion events must reuse that binding rather than reconstruct identity from payload.

## 2. Provider-Owned Workspace Placement Authority

### 2.1 Host Policy

Add provider-owned configuration equivalent to:

```yaml
mutation_execution:
  scoped_mutation_enabled: false
  workspace_root: <absolute-host-owned-root>
  protected_roots:
    - <provider-owned-protected-root>
  runtime_read_roots:
    - <immutable-runtime-root>
  scope_ttl_seconds: 3600
  evidence_retention_days: 30
  operator_unrestricted_enabled: false
```

Rules:

- `workspace_root`, `protected_roots`, and `runtime_read_roots` come only from Host configuration.
- They are not derived from `file_ops` rw entries.
- caller `cwd`, `workspace_root`, `allowed_write_root(s)`, `protected_roots`, drive letters, UNC paths, or remembered paths cannot choose placement.
- control-plane scope/audit/evidence stores are never caller mutation roots.
- configuration load canonicalizes roots and rejects protected/workspace overlap that would make authority ambiguous.

### 2.2 Deterministic Resolver

Placement input:

```text
repository identity = vcs + authority + canonical repository path
semantic identity   = project_id + task_id + run_id + attempt_id + optional slice_id
Host policy         = workspace_root + placement_generation
```

Derivation:

```text
repo_key    = short_digest(canonical repository identity)
attempt_key = short_digest(project/task/run/attempt[/slice])
future_workspace = workspace_root / repo_key / attempt_key
```

The resolver returns provider-owned evidence equivalent to:

```yaml
placement:
  placement_ref:
  generation:
  policy_digest:
  exact_future_workspace:
  exact_workspace_digest:
  repository_identity_digest:
  semantic_identity_digest:
  protected_inventory_digest:
```

Human-readable names may exist only as metadata; they do not participate in authority/path construction.

### 2.3 Placement Generation and Drift

Persist:

```text
normalized placement policy digest
+ monotonically increasing placement_generation
```

Rules:

- same normalized policy digest → generation unchanged;
- changed workspace/protected/runtime-read roots or placement rules → generation increments;
- scope seals placement generation/digests;
- every revalidation independently re-runs placement from current Host policy;
- generation/path/policy/protected/repository/semantic digest mismatch → `HostMutationScopeBindingMismatch`;
- stale scope is never silently retargeted.

### 2.4 Protected Inventory

Provider-derived protected inventory includes at minimum:

- configured protected roots;
- workspace root and parents except the exact admitted child authority;
- sibling workspaces;
- canonical repository roots;
- provider scope/audit/evidence stores;
- any parent whose delete/rename rights could remove or replace the admitted workspace or siblings.

The sandbox SID receives no write/create-child/delete authority on this inventory.

## 3. Mutation-Scope Store and Authoritative Unique Lease

### 3.1 Scope Store

Use a broker-only durable provider store equivalent to:

```text
<SentinelX state dir>/mutation-scopes/
```

A scope record contains:

```text
workspace_id
scope_id + generation
unique_lease_key
semantic lineage + digest
repository identity + digest
placement ref/generation/policy digest
exact workspace + digest
protected inventory digest
allowed operation classes
issued/expires timestamps
state
scope digest
sandbox/AppContainer identity when activated
active Job/process bindings when present
```

Writes are atomic and durably flushed. The AppContainer worker cannot write the authority store.

Provider operations:

```text
host_mutation_sandbox_v1.provision_scope
host_mutation_sandbox_v1.revalidate_scope
host_mutation_sandbox_v1.terminalize_scope
```

`provision_scope` is the only producer of `workspace_id` and `mutation_scope_ref`.

### 3.2 Unique Lease Key

The canonical unique lease key is derived from:

```text
canonical repository identity digest
+ run_id
+ attempt_id
+ optional slice_id
+ placement_generation
+ exact_workspace_digest
```

`project_id` and `task_id` remain sealed lineage evidence, but the uniqueness boundary must include the execution identities that make the Attempt/placement unique. Implementations may include additional sealed identity fields, but may not omit the fields above.

Invariant:

> For one unique lease key, at most one scope in `{provisioned, active}` may exist.

The provider must also maintain a reverse exact-workspace authority index so two distinct lease keys cannot accidentally map to the same exact writable workspace without an explicit, valid same-Attempt identity match.

A collision between:

```text
unique lease key
scope/workspace binding
exact workspace digest
repository/semantic digest
```

is a security failure, not a reason to mint another scope.

### 3.3 Atomic, Idempotent `provision_scope`

`provision_scope` executes inside a provider-owned transactional/locking boundary covering:

```text
unique lease index
scope record creation/update
workspace reverse index
AppContainer/SID activation reservation
```

Required behavior:

1. resolve authoritative placement first;
2. compute unique lease key;
3. acquire provider-owned exclusive lease lock/transaction;
4. re-read current authority state under the lock;
5. if a current matching `{provisioned, active}` scope exists for the same exact binding, return that exact scope/workspace identity after `revalidate_scope`;
6. if another non-terminal scope exists with conflicting binding, return fail-closed conflict;
7. only when no current non-terminal authority exists may SentinelX allocate new opaque `workspace_id + scope_id`;
8. persist unique index and scope record atomically/durably before returning.

Same-Attempt retry/resume therefore behaves idempotently:

```text
retry/resume
→ same unique lease key
→ same current scope_id/workspace_id/generation
→ live revalidation
→ no second active scope
```

Concurrent duplicate provisioning must serialize on the same lease key. A losing caller either receives the already-created exact current scope after revalidation or an explicit fail-closed conflict; it never creates a second scope.

### 3.4 No Reactivation

A scope in:

```text
terminal
revoked
expired
```

never returns to `provisioned` or `active` by caller request.

A stale retry after terminalization returns the terminal/non-current state and does not recreate authority under the same completed Attempt.

If new mutation authority is legitimately required after terminal completion, orchestration must create a new valid Attempt and therefore a distinct unique lease identity/generation according to canonical execution semantics.

### 3.5 AppContainer SID / ACL Binding

AppContainer profile/SID activation is bound 1:1 to the unique non-terminal lease.

Rules:

- a retry of the same lease reuses/verifies the same sandbox identity rather than adding another write SID;
- the exact workspace DACL must not accumulate write ACEs from multiple active scope SIDs;
- before activation, the broker reads back the DACL and rejects an unexpected stale/foreign mutation SID;
- activation reservation participates in the same provider-owned lease transaction/state machine;
- path/digest/key collision returns fail closed before ACL broadening.

### 3.6 Revalidation

Before materialization and before every later material mutation boundary, verify:

```text
scope exists and is current
state ∈ {provisioned, active}
generation current
unique lease key still maps to this exact scope
no competing non-terminal scope for the lease/workspace
not expired/revoked
semantic/repository binding matches
placement generation/path/digests match
protected inventory matches
sandbox SID/ACL binding matches when activated
```

Any mismatch blocks mutation.

### 3.7 Terminalization Closure

`terminalize_scope(scope_id, generation)` must execute under the same authoritative lease lock/transaction.

Required sequence:

```text
prevent new spawn/admission
→ revalidate exact scope + unique lease ownership
→ terminate/close every Job bound to this lease
→ verify no bound root/child process remains
→ remove/revoke exact scope SID workspace write authority
→ verify DACL has no residual mutation write ACE for this lease
→ dispose scope-specific AppContainer profile when safe
→ mark scope terminal/revoked durably
→ verify unique lease index has no other {provisioned, active} scope
→ verify exact workspace reverse index has no other active lease
→ authoritative non-active read-back
```

Successful completion is forbidden when any of the following remains:

```text
another active/provisioned scope for same unique lease
another active lease mapped to same exact workspace
active Job/process binding
residual AppContainer/SID write authority
scope state active/provisioned
```

Failures return named fail-closed results such as:

```text
HostMutationScopeConflict
HostMutationScopeTerminalizationFailed
HostMutationScopeStillActive
HostMutationResidualAuthorityDetected
```

## 4. Security-Critical Write-Ahead Audit

Keep ordinary `local_audit.record()` compatible for non-security telemetry.

Add a dedicated mutation audit journal:

```python
start = mutation_audit.begin(...)
spawn = mutation_audit.record_spawn(start, ...)
finish = mutation_audit.finish(start, ...)
```

`begin()` returns only after durable write/flush succeeds.

Required lifecycle:

```text
REQUEST_RECEIVED
→ ADMISSION_VERIFIED
→ OPERATION_STARTED [durable]
→ trusted workspace materialization / ACL preparation
→ suspended sandbox process creation
→ Job assignment
→ PROCESS_SPAWNED [durable enough for provider contract]
→ ResumeThread / first untrusted instruction
→ OPERATION_FINISHED
```

If START durability fails, no workspace materialization and no process creation occur.

If SPAWN evidence fails while the process is still suspended, terminate the suspended process/Job and never resume it.

## 5. Durable Forensic Script Evidence

Before START:

1. normalize exact script bytes;
2. SHA-256 them;
3. store them in broker-only retained evidence storage;
4. durably persist/verify artifact;
5. record hash + restricted artifact reference in START.

After START and trusted workspace creation, copy/write those exact bytes into the deterministic execution path inside the admitted workspace and verify the hash again.

`cleanup=true` may remove temporary execution staging, but cannot delete the retained forensic artifact.

## 6. Fixed Windows V1 Sandbox Primitive

Windows V1 uses:

```text
scope-specific AppContainer profile/SID
+ exact workspace ACL
+ provider-owned read/execute grants only for required immutable runtime roots
+ no network capability by default
+ Job Object kill-on-close / no breakaway
+ suspended process creation / pre-resume Job assignment
```

No fallback is allowed to LocalSystem, interactive user, CreateRestrictedToken-only, ordinary user token, unrestricted shell, command filtering, path checks, or uncontained subprocess execution.

### 6.1 Trusted Bootstrap

Canonical first-spawn sequence:

```text
1. Executor creates RequestContext.
2. scoped handler validates semantic lineage.
3. revalidate_scope confirms unique lease/placement/protected inventory.
4. retain/hash exact script evidence.
5. durable OPERATION_STARTED.
6. trusted broker creates only the exact derived empty workspace.
7. create/load the unique-lease AppContainer profile/SID.
8. disable inheritance on exact workspace DACL and install exact scope ACL.
9. verify SID can mutate workspace but cannot write/delete/create-child on parent/sibling/protected objects.
10. verify no second active mutation SID/write ACE exists for this workspace.
11. materialize exact retained script bytes and verify SHA-256.
12. create Job Object with kill-on-close and no breakaway.
13. create process suspended with AppContainer security attributes, `CREATE_SUSPENDED`, `EXTENDED_STARTUPINFO_PRESENT`, `CREATE_NO_WINDOW`, and disabled handle inheritance.
14. assign still-suspended process to Job.
15. verify Job membership/sandbox identity and persist PROCESS_SPAWNED evidence.
16. only then ResumeThread.
17. timeout/cancel terminates and verifies the full Job tree.
18. persist FINISH.
19. terminalization later performs full unique-lease residual-authority closure.
```

Failure before step 16 never resumes untrusted code.

### 6.2 Reparse / Final Path

Before ACL install, materialization, and spawn, validate the final workspace using Windows final-path/reparse-aware APIs. Caller-controlled junction/symlink/reparse redirection causes fail-closed binding failure.

## 7. Execution Profiles and Legacy Compatibility

New profiles:

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

- `scoped_mutation` requires verified provider capabilities, current scope lease, validated lineage, and authoritative RequestContext.
- `operator_unrestricted` requires explicit `mutation_execution.operator_unrestricted_enabled: true`.
- scoped failure never falls back to operator/legacy mode.

Migration:

```text
mutation_execution block absent
→ preserve historical unprofiled script_run only as legacy_unrestricted_compat
→ emit migration/security warning
→ never advertise scoped capability because of this path
→ explicit operator_unrestricted request rejected unless opted in

mutation_execution block present
→ missing operator_unrestricted_enabled = false
→ missing scoped_mutation_enabled = false
```

New configuration examples include both explicit false defaults.

## 8. Scoped Script Integration

Refactor `handlers/script.py` into preparation and execution seams while preserving legacy interpreter/Unicode/cwd/output behavior outside scoped mode.

Scoped path:

```text
RequestContext
→ validate scoped payload
→ revalidate unique lease
→ prepare exact process intent/script bytes
→ retained forensic evidence
→ durable START
→ trusted workspace/ACL/AppContainer activation
→ suspended spawn
→ Job assignment
→ SPAWN audit
→ resume
→ wait/timeout/cancel under Job
→ FINISH
```

Rules:

- scoped `cwd` must be provider-derived inside the exact workspace;
- `sudo`/elevation is forbidden;
- environment cannot override authority, SID, placement, evidence/audit path, credential context, or Job identity;
- normal-user Git credentials are not injected;
- authenticated Git remains a separate structured broker.

## 9. Capability Advertisement

Advertise:

```text
host_mutation_sandbox_v1
pre_execution_audit_lineage_v1
```

only when runtime self-check proves:

```text
Windows
+ scoped policy enabled
+ provider-owned placement store healthy
+ unique lease/scope store healthy
+ atomic lease locking/transaction primitive healthy
+ mutation audit durable-flush self-check
+ retained evidence store healthy
+ AppContainer API/profile self-check
+ exact ACL admission/read-back self-check
+ runtime read/execute access self-check
+ Job create/assign/kill-on-close/no-breakaway self-check
+ suspended-create-before-resume self-check
+ residual-authority read-back self-check
```

Linux/macOS V1 do not advertise scoped capability unless an equivalent provider is separately implemented and verified.

## Execution Slices

### Slice 1 — RequestContext, Policy Migration, Placement Authority, Capability Truthfulness

Implement:

- immutable `RequestContext` + legacy handler adapter;
- `mutation_execution` policy/migration semantics;
- deterministic provider-owned placement resolver;
- placement generation/policy digest state;
- provider readiness model;
- truthful capability advertisement.

Verification includes payload-spoof rejection, old/new config matrix, caller-path non-authority, path traversal/drive/UNC non-authority, placement drift, and unsupported-host capability absence.

### Slice 2 — Unique Mutation-Scope Lease Lifecycle

Implement:

- durable scope store + unique lease index + exact-workspace reverse index;
- provider-owned lease lock/transaction;
- atomic idempotent `provision_scope`;
- `revalidate_scope`;
- exact `terminalize_scope` residual-authority closure;
- scope generation/TTL/revocation;
- 1:1 unique lease ↔ AppContainer activation binding.

Required negative/regression cases:

```text
caller-minted scope
stale generation
cross Run/Attempt/Slice
wrong repository/workspace
placement drift
expired/revoked/terminal reuse
terminalize wrong generation
active-after-terminalization
duplicate provision retry
same-Attempt resume
concurrent duplicate provision
path/digest/key collision
terminal-after-stale-retry
two-scope same-workspace attempt
two-SID same-workspace write-authority accumulation
second active lease on exact workspace
residual Job/process after terminalize
residual SID write ACE after terminalize
```

Checkpoint:

```text
One Attempt/workspace placement has at most one non-terminal mutation authority, and completion proves no parallel/residual authority remains.
```

### Slice 3 — Durable Mutation Audit + Forensic Script Evidence

Implement START/SPAWN/FINISH journal, durable script artifact, RequestContext/lineage separation, crash semantics, background identity binding, and retention controls.

Tests include START write/flush failure ⇒ no materialization/spawn, SPAWN-audit failure ⇒ suspended child killed/not resumed, cleanup preservation, crash START-without-false-FINISH, and background identity continuity.

### Slice 4 — Windows AppContainer + Exact ACL + Suspended Job Containment

Implement unique-lease AppContainer profile/SID, exact workspace broker materialization, non-inherited ACL, reparse-safe path verification, no-breakaway Job, suspended pre-resume assignment, timeout/cancel, and terminal residual-authority cleanup.

All destructive testing uses disposable fixtures only. Never use real `D:\coco`, canonical repositories, or personal project directories.

### Slice 5 — Scoped Script Execution Integration

Integrate scoped execution without regressing legacy script behavior. Verify PowerShell/pwsh/python paths, Unicode, cwd validation, no elevation, no authority-env override, no user Git credential inheritance, and no fallback.

### Slice 6 — Canonical Incident Regression, Docs, Release Readiness

Canonical fixture:

```text
INCIDENT-20260927-D-ROOT-RECURSIVE-DELETE
```

Synthetic disposable layout:

```text
root/
  workspace-root/
    admitted-workspace/
    sibling-workspace/MUST_SURVIVE
  canonical-repo/MUST_SURVIVE
  personal-project/MUST_SURVIVE
  parent-sentinel/MUST_SURVIVE
```

Attack matrix includes PowerShell recursive delete, `cmd /c rmdir /s /q`, Python `shutil.rmtree`, .NET/Win32 delete, child process attack, detached/background escape, reparse/junction escape, move/rename escape, and `git clean -fdx` against protected fixtures.

All protected sentinels must remain unchanged.

Update README/security semantics, Windows/generic config examples, threat model as needed, and release notes.

## Verification Strategy

### Static / Unit

- RequestContext provenance/spoofing;
- policy migration matrix;
- placement determinism/drift;
- unique lease idempotency/concurrency state machine;
- scope lifecycle and reverse-index collision handling;
- audit ordering/durability failure injection;
- receipt identity matching;
- no-fallback behavior;
- terminal residual-authority detection.

### Windows Integration

Must run on a real Windows environment representative of production service mode.

Required evidence includes:

```text
service identity
unique lease key/ref
scope_id + generation
AppContainer name/SID
workspace final path + DACL read-back
proof no second mutation SID/write ACE exists
parent/sibling/protected access checks
Job/containment identity
root PID + child PIDs
proof suspended-before-Job-assignment/resume ordering
START/SPAWN/FINISH references
terminal scope read-back
proof no competing active lease
proof no active Job/process
proof no residual SID write authority
protected fixture hashes/existence before and after
```

Mocks alone are not acceptance evidence for the Windows sandbox boundary.

### Existing Regression Suite

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

Then run the broad suite available on the target platform. Platform-incompatible collection failures must be explicitly classified and never presented as PASS evidence.

## Safety Rules During Implementation

1. Never use real `D:\coco`, a real user project, canonical checkout, or real protected directory as a destructive target.
2. Destructive regressions run only under fixture-owned disposable roots.
3. No recursive-delete fallback outside fixture roots.
4. Do not weaken file-op canonicalization or Git credential boundaries.
5. Do not advertise scoped capability until real AppContainer + ACL + Job + unique-lease self-check passes.
6. Provider unavailability is an acceptable fail-closed V1 outcome.
7. Do not implement restricted-token/LocalSystem fallback.
8. Trusted broker workspace creation is allowed only for the exact provider-derived workspace after durable START.
9. Duplicate provisioning must never create a second active scope/SID.
10. Successful terminalization must prove absence of competing leases, active Jobs/processes, and residual mutation write authority.

## Completion Evidence

Implementation is a completion candidate only when it can produce evidence equivalent to:

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
  unique_lease_key_verified: true
  duplicate_provision_idempotent: true
  competing_active_scope_count: 0
  workspace_reverse_index_verified: true
  revalidation: verified
  terminalization: verified_non_active
  active_jobs_after_terminalize: 0
  residual_sid_write_authority: false
audit:
  started_before_workspace_materialization: true
  started_before_untrusted_execution: true
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
