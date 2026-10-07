# PR-017 — S02 Live Invalidation R2

## Disposition

```yaml
task_id: PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1
classification: live_exact_candidate_evidence_invalidated_repaired_slice_completion
requirement_revision: 1
plan_revision: 1
requirement_semantics_changed: false
plan_semantics_changed: false
s01: preserved_no_replay
s02: repair_required
s03: blocked
implementation_authorized: true
```

## Exact Candidate

The Windows Host was successfully activated on:

```text
0.24.1.dev431+g4896a55cb
candidate 4896a55cb951dec47422c738ccb1ba98762e13a9
```

Host policy remained:

```yaml
runtime_acl_timeout_seconds: 300
operator_unrestricted_enabled: false
```

## Live Evidence

A real S03 scoped Python proof created:

```text
scope_id: mss_JB_VJlJg4Np6LdrxgKd_fCw9
generation: 1
run_id: S03-PHYSICAL-REPAIR-20261007
attempt_id: python
```

The outer local_api request timed out at 60 seconds while the Agent continued the bounded operation.

Readback then showed:

```text
state: revoked
terminalized_at: null
```

This is correct fail-closed behavior and proves the previous false-terminal defect was repaired.

An explicit bounded retry through:

```text
devforge_runtime.terminalize_scope
```

returned:

```text
HostMutationResidualAuthorityDetected:
sandbox/runtime-read authority remains; terminalization requires OS cleanup
```

Source readback proves why:

```text
DevforgeRuntimeProvider.terminalize_scope
→ generic mutation_scope lifecycle service
→ MutationScopeStore.terminalize_scope(...)
→ runtime_cleanup = None
```

Therefore the durable residual marker is correct, but the required explicit OS-cleanup retry path is not reachable through the canonical bounded API.

## Requirement Violation

R5 already requires:

```text
revoked
→ explicit later cleanup/retry
→ authoritative OS cleanup
→ exact SID absence readback
→ terminal
```

Current candidate stops at:

```text
revoked
→ devforge_runtime.terminalize_scope
→ HostMutationResidualAuthorityDetected
```

So S02 repair completion cannot remain valid.

## Required Repair

The next S02 repair must:

1. keep one canonical `MutationScopeStore`;
2. wire bounded explicit `devforge_runtime.terminalize_scope` to the same canonical `WindowsMutationSandbox` cleanup semantics used by scoped execution;
3. never create a second executor or cleanup authority;
4. preserve repository/semantic/scope binding checks before cleanup;
5. clean durable `runtime_read_authority_roots` using the exact stored AppContainer identity;
6. require exact SID-absence readback before clearing each durable marker;
7. retain `revoked` on any cleanup ambiguity;
8. publish `terminal` only after all Job/process/write/runtime-read authority is closed;
9. include an end-to-end regression through the actual `devforge_runtime.terminalize_scope` action;
10. reuse the real live revoked scope `mss_JB_VJlJg4Np6LdrxgKd_fCw9` as physical retry evidence after the repaired candidate is activated.

## Evidence Disposition

- S01 remains completed.
- S02 R1/R2 CI remains historical useful evidence but completion authority is invalidated.
- The real revoked scope must not be manually terminalized or replaced with a fresh scope before repaired retry evidence is attempted.
- S03 remains blocked and incomplete.
