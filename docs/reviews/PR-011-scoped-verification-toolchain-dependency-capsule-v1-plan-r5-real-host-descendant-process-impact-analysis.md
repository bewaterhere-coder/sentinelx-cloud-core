# PR-011 Plan R5 — Real-Host Descendant Process Impact Analysis

## Trigger

During `#开发执行 PR-011-scoped-verification-toolchain-dependency-capsule-v1`, S04 real-Windows physical verification produced new evidence that invalidates assumptions used by the approved Plan R4 execution lineage.

The decisive physical result was:

```text
AppContainer root Python process starts
→ SENTINELX_STAGE_PYTHON_CHILD_START
→ same python.exe child creation never returns
→ outer scoped runtime times out
→ Job/process tree is terminalized
→ transient sandbox/toolchain authority is absent after terminalization
```

This result is stronger than the earlier Node/npm failures because it removes Node, npm, PATH, shim and toolchain choice from the failing step.

## Evidence Classification

### E1 — Toolchain ancestor ACL assumption invalidated

A real stable provider toolchain rooted under `C:\Program Files\nodejs` caused the existing verification-toolchain ACL helper to attempt an ACL grant on `C:\Program Files`, which failed with access denied.

Impact:

- the S02 implementation assumption that verification-toolchain reachability may be obtained by rewriting every ancestor ACL is invalid for protected system parents;
- that behavior is broader than the Requirement R2 minimum provider-owned read/execute authority;
- the correct fail-closed shape is to grant only the admitted toolchain root and never widen protected ancestor ACLs.

### E2 — Descendant-process assumption invalidated

A minimal in-AppContainer `python.exe -> python.exe -c ...` probe timed out at `PYTHON_CHILD_START`.

Impact:

- the S03 implementation depends on a root Python scoped runner spawning Node/npm and npm lifecycle descendants;
- CI/runner evidence proving that path does not substitute for real-Host proof on the target Windows execution boundary;
- the S03 completion receipt remains historical evidence for unaffected environment/integrity behavior, but it no longer authorizes the claim that descendant execution is physically valid on the real Host.

### E3 — Containment/terminalization remains valid

Across the failed probes:

- the AppContainer root process was created;
- the root process was Job-contained with no breakaway;
- timeout terminalization completed;
- the scope became terminal;
- residual sandbox/toolchain authority was absent.

Therefore the failure does **not** justify weakening AppContainer, Job, Scope or terminalization controls.

## Requirement Impact

Requirement Revision 2 is unchanged.

The Requirement already demands:

- real Node/npm execution inside the existing Windows AppContainer boundary;
- npm lifecycle descendants remaining inside the existing no-breakaway Job;
- no second executor/sandbox/scope/audit authority;
- no network, credential, generic exec or operator-unrestricted fallback.

The new evidence challenges the Plan/implementation, not the Requirement semantics.

## Evidence Validity Disposition

| Prior evidence | R5 disposition |
|---|---|
| S01 policy/profile/source/capsule/toolchain pure contracts | Preserved, no replay |
| S02 source/capsule materialization, audit binding, integrity checks, terminal cleanup | Preserved where independent of ancestor-ACL behavior |
| S02 ancestor traversal ACL behavior for provider toolchain | Invalidated; repair required |
| S03 environment sanitization, cwd confinement, sealed evidence contracts | Preserved as partial evidence |
| S03 real descendant Node/npm execution completion claim | Invalidated for completion authority; repair + real-Host proof required |
| S04 | Never completed; remains unpublished/incomplete |
| S05 | Never started |

No prior completed side effects should be replayed wholesale. Only the invalidated seams are reopened.

## Architecture Constraint for Remediation

The remediation must stay inside the canonical PR-007/PR-010/PR-012 execution model.

The repaired design must:

1. keep the single `MutationScopeStore`, `WindowsMutationSandbox`, Job and `MutationAuditJournal`;
2. keep explicit `execution_profile=scoped_mutation`;
3. never grant protected ancestor ACLs merely to reach a toolchain;
4. first prove a minimal descendant process on the real Host before re-asserting Node/npm support;
5. repair child-process creation semantics inside the existing Windows spawn boundary rather than adding a second executor or breakaway path;
6. fail closed and return to Requirement review if descendant execution cannot be made compatible with the existing security invariants.

Windows platform documentation indicates that an AppContainer child normally inherits the parent's AppContainer token, and child processes normally remain associated with the parent's Job when breakaway is not allowed. The observed `PYTHON_CHILD_START` hang is therefore treated as an implementation/Host-integration defect to diagnose, not as permission to bypass containment.

## Required Plan Change

Plan R4 and its Execution Slice Set can no longer authorize implementation.

Plan R5 must compile, after review approval, this repair sequence:

```text
S01 preserved
→ S02R toolchain ACL minimum-authority repair
→ S03R real-Host descendant-process repair + Node/npm descendant proof
→ S04 readiness/capability physical proof
→ S05 devforge_runtime verification projection + live readback
```

The old Plan R4 Slice Set is historical evidence only after this remediation.

## Disposition

```yaml
requirement_semantics_changed: false
plan_semantics_changed: true
old_plan_revision: 4
new_plan_revision: 5
old_slice_set_authority: stale
s01: preserved_no_replay
s02: partial_evidence_preserved_repair_required
s03: partial_evidence_preserved_completion_authority_invalidated
s04: pending_unpublished
s05: not_started
implementation_authorized_after_remediation: false
next_stage: plan_review
```
