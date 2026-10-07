# PR-017 — S02 Live Invalidation R3

## Disposition

```yaml
task_id: PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1
classification: live_exact_candidate_evidence_invalidated_cleanup_proof_completion
requirement_revision: 1
plan_revision: 1
requirement_semantics_changed: false
plan_semantics_changed: false
s01: preserved_no_replay
s02: repair_required
s03: blocked
implementation_authorized: true
```

## Exact Candidate Evidence

Windows Host:

```text
0.24.1.dev436+ga214921cd
candidate a214921cd34fcab5874696f45281306622a73421
```

Preserved real scope:

```text
scope_id: mss_JB_VJlJg4Np6LdrxgKd_fCw9
generation: 1
state before retry: revoked
```

The repaired bounded retry:

```text
devforge_runtime.terminalize_scope
→ canonical mutation_scope lifecycle
→ canonical WindowsMutationSandbox.terminalize
→ Windows OS cleanup
```

was reached successfully.

The cleanup then returned:

```text
HostMutationSandboxResidualAuthority:
runtime ACL cleanup could not prove AppContainer SID removal on
C:\Windows\System32\WindowsPowerShell\v1.0

cause:
runtime ACL cleanup ... failed: Access Denied
```

Readback after failure:

```text
state: revoked
terminalized_at: null
```

So fail-closed state is correct and the R2 retry-surface wiring is proven.

## Newly Exposed Gap

Current `_remove_runtime_read()` order is:

```text
icacls /remove:g exact SID
→ DACL readback
→ assert exact SID absent
```

This cannot distinguish:

1. SID is present and removal is required; from
2. grant failed before SID was ever installed, while the service also lacks permission to mutate the protected root.

Case 2 can already satisfy the Requirement's closure condition — exact SID absence — without any ACL mutation.

The correct bounded algorithm is:

```text
read exact root DACL
├─ SID absent
│  → closure proven
│  → return success without ACL mutation
└─ SID present
   → icacls /remove:g exact SID
   → read exact root DACL again
   ├─ SID absent → closure proven
   └─ SID present/readback failure/remove failure → residual authority
```

This remains fail-closed and does not widen any permission.

## Required Repair

1. Add pre-removal exact DACL readback to `_remove_runtime_read()`.
2. If exact AppContainer SID is already absent, return success without invoking `icacls /remove:g`.
3. If the SID is present, retain the current bounded removal + post-removal readback.
4. Any pre-read failure remains residual-authority ambiguity.
5. Any removal failure while SID is known present remains residual authority.
6. Add focused tests for:
   - SID already absent -> no icacls write;
   - SID present -> removal invoked -> absent on second readback;
   - pre-read failure -> fail closed;
   - SID present + removal denied -> fail closed.
7. After exact candidate activation, retry the same real scope `mss_JB_VJlJg4Np6LdrxgKd_fCw9`; do not replace it with a fresh scope before retry evidence.

## Evidence Disposition

- S01 remains completed.
- The R2 false-terminal repair remains valid.
- The R3 bounded terminalize-to-Windows-cleanup wiring remains valid.
- S02 completion is invalidated only for cleanup proof ordering.
- S03 remains blocked.
