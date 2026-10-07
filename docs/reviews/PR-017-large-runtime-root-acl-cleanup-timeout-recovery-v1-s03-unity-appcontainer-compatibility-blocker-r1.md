# PR-017 — S03 Unity AppContainer Compatibility Blocker R1

## Disposition

```yaml
task_id: PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1
slice_id: S03
classification: external_runtime_compatibility_blocker
requirement_revision: 1
plan_revision: 1
s01: completed
s02: completed
s03: blocked
task_completion_verified: false
acceptance_approved: false
```

## Exact Candidate

```text
f7249aef0d25085eb98e741596b6f567ebd83966
0.24.1.dev439+gf7249aef0
```

Host policy during large-runtime proof:

```yaml
runtime_acl_timeout_seconds: 300
operator_unrestricted_enabled: false
unity_runtime_root: C:\Program Files\Unity\Hub\Editor\6000.6.4f1
```

## Positive Physical Evidence

### Preserved revoked scope recovery

The pre-repair real scope:

```text
mss_JB_VJlJg4Np6LdrxgKd_fCw9
```

was retried through `devforge_runtime.terminalize_scope` on the exact candidate and transitioned:

```text
revoked -> authoritative Windows cleanup/readback -> terminal
```

This closes the S02 R5 physical retry requirement.

### Python

```text
scope: mss_LYcEztB2Tgf2Uv8MjSFjVc2k
output: PR017_S03_PYTHON_OK
returncode: 0
terminal_state: terminal
```

### PowerShell

With the explicit PowerShell system runtime root configured:

```text
C:\Windows\System32\WindowsPowerShell\v1.0
```

Windows rejects the ACL grant with `HostMutationSandboxAclViolation / Access Denied`.
The scope:

```text
mss_Xm5WKsMrHRlmY37fCse78xeE
```

still reaches `terminal`; no residual authority remains. This is deterministic fail-closed behavior rather than the prior residual-authority ambiguity.

### Unity large-root cleanup

Multiple scopes using the real Unity 6000.6.4f1 runtime root reached `terminal` under the configured 300-second bound:

```text
mss_NgKCbAFve96a2cp5xRbx3AEM
mss_By25SNCI-5slwpGCtb6TxkQH
mss_lrSnR5loSxD-rqRSt_Ca4NP0
mss_XVQaRAUDz6J0R9qd-zq8wvSs
mss_ZeDUEM6nvAOSIwGN1Z44iD_b
mss_RzzUMrqRePo3BZHfc1m83rAw
```

MutationAudit closure evidence reports:

```text
scope_state = terminal
active_job_ids = []
active_process_ids = []
job_active_process_count = 0
process_tree_quiescent = true
sandbox_write_authority_present = false
```

The durable runtime-read markers can only clear after exact SID-absence readback, so terminal closure is evidence that the AppContainer runtime-root authority was closed.

## Unity Compatibility Failure

A no-extra-Unity-ACL probe created `Unity.exe` but returned Windows status:

```text
3221225794
0xC0000142
STATUS_DLL_INIT_FAILED
```

A later classified probe ran with the Unity runtime root explicitly granted and encoded the child outcome into the scoped Python return code:

```text
scope: mss_RzzUMrqRePo3BZHfc1m83rAw
attempt: unity-exit-classify
Python returncode:
  0  = Unity alive >=5 seconds or clean exit 0
  82 = Unity child returned 0xC0000142
  84 = other early nonzero Unity exit
observed: 82
```

MutationAudit recorded:

```text
OPERATION_STARTED
PROCESS_SPAWNED
OPERATION_FINISHED
returncode = 82
status = failed
scope_state = terminal
process_tree_quiescent = true
```

Therefore the Unity child is created through the scoped/AppContainer boundary, but DLL initialization fails before the intended version/batch probe can be considered successful.

## Acceptance Impact

The following PR-017 goals are now evidenced:

- provider-owned bounded runtime ACL timeout;
- large Unity runtime-root grant/cleanup no longer fails at the old 20-second ceiling;
- exact SID absence gates authority closure;
- residual authority stays revoked;
- explicit later retry can reach terminal;
- Python scoped execution passes;
- deterministic PowerShell fail-closed behavior;
- exact-candidate CI/security regressions remain green;
- no unrestricted fallback or security widening persists.

But Requirement R8.3 remains unsatisfied:

```text
Unity runtime process can be launched through the scoped boundary
far enough to perform the intended batch/version probe.
```

The real failure is now application compatibility:

```text
Unity 6000.6.4f1 + Windows AppContainer
→ child process created
→ 0xC0000142 DLL initialization failed
```

PR-017 explicitly lists general Windows application compatibility under AppContainer as a Non-Goal. Expanding PR-017 to redesign Unity/AppContainer compatibility would violate the approved scope.

## Decision Gate

One upstream decision is required:

1. **Keep Unity as mandatory R8.3 acceptance:** create a separate Unity/AppContainer compatibility task and make PR-017 S03 depend on it; or
2. **Treat PR-017 strictly as ACL timeout/recovery:** revise Requirement R8/S03 acceptance to allow the already-proven large-runtime ACL closure plus a bounded equivalent process fixture, while tracking Unity compatibility separately.

Until that decision is made, S03 remains Blocked and PR-017 is not accepted.

## Host Restoration

After evidence capture:

- original four `runtime_read_roots` were restored;
- `runtime_acl_timeout_seconds=300` remains;
- `operator_unrestricted_enabled=false`;
- temporary exact-file read access to the mutation audit journal was removed;
- no product-code mutation occurred during this S03 run.
