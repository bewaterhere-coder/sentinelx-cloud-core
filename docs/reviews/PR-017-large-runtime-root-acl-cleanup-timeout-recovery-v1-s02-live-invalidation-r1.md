# PR-017 — S02 Live Invalidation R1

## Disposition

```yaml
task_id: PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1
source_command: "#开发执行 PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1"
classification: live_exact_candidate_evidence_invalidated_slice_completion
requirement_revision: 1
plan_revision: 1
requirement_semantics_changed: false
plan_semantics_changed: false
s01: preserved_no_replay
s02: completion_authority_invalidated_repair_required
s03: blocked_until_s02_repaired
implementation_authorized: true
next_expected_actor: implementer
```

## Exact Candidate Evidence

The Windows Host was activated on:

```text
0.24.1.dev426+gd083921b3
candidate d083921b3f0146455bd4b0732d8e0ce219728344
```

Host policy retained:

```yaml
runtime_acl_timeout_seconds: 300
operator_unrestricted_enabled: false
```

A live scoped PowerShell Attempt produced:

```text
HostMutationSandboxResidualAuthority:
runtime ACL grant for
C:\Windows\System32\WindowsPowerShell\v1.0
failed and compensating cleanup could not prove AppContainer SID removal
```

The exact scope:

```text
scope_id: mss_62URoGdXBbPJCnNK6Xdm_dye
generation: 1
```

then read back as:

```text
state: terminal
terminalized_at: 2026-10-07T11:47:35.727761Z
```

## Why S02 Completion Is Invalid

Requirement R4/R5 already require:

```text
compensation cannot prove closure
→ residual authority
→ fail closed
→ scope remains revoked
→ no terminal publication
```

The live candidate instead demonstrated:

```text
grant/compensation ambiguity
→ HostMutationSandboxResidualAuthority
→ outer scoped-script exception cleanup
→ terminalize_scope()
→ durable scope becomes terminal
```

Therefore the S02 completion receipt remains historical evidence for its focused unit/CI behavior but is no longer valid current completion authority.

The defect is not a Requirement or Plan semantic change. It is an implementation gap in the activation-failure / outer-exception composition.

## Required Repair

S02 repair must ensure all of the following:

1. activation-time residual runtime-read authority is represented durably before generic exception cleanup can publish terminal;
2. a `HostMutationSandboxResidualAuthority` from activation/compensation cannot be converted to terminal by `scoped_script` exception handling;
3. the scope remains `revoked` when runtime-read cleanup closure is ambiguous;
4. an explicit later cleanup/retry path can close the exact residual authority and only then publish terminal;
5. end-to-end regression covers the real handler composition, not only helper-level compensation;
6. S02 repair does not introduce a second scope store, executor, lifecycle state, unrestricted fallback or caller-controlled cleanup authority.

## Evidence Disposition

- S01 remains completed and reusable.
- S02 focused tests/CI remain useful historical evidence, but the S02 completion decision is invalidated.
- S03 physical proof is blocked and incomplete.
- No Unity success claim is made.
- No Task completion or Acceptance claim is made.

## Host Safety

The temporary S03 runtime-root narrowing used to isolate the PowerShell proof was reverted. The Host is again running the exact PR-017 candidate with the original runtime root set and `runtime_acl_timeout_seconds=300`.

Because the failed compensation could not prove SID absence, no additional live mutation scope should be created until the residual-authority handling defect is repaired and any real Host residual ACL is independently checked/cleaned.
