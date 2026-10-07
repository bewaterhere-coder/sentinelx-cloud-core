# PR-018 Unity 6.6 AppContainer DLL Initialization Compatibility V1 — Plan

## Status

~~~yaml
task_id: PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1
plan_revision: 1
plan_status: ready_for_review
implementation_authority: false
requirement_ref: docs/requirements/PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1.md
transport:
  type: github-pr
  pr_number: 18
  branch: task/unity-6-6-appcontainer-dll-initialization-compatibility-v1
  base: task/large-runtime-root-acl-cleanup-timeout-recovery-v1
  stacked_on_pr: 17
~~~

## Plan Objective

Diagnose Unity 6000.6.4f1 0xC0000142 using the already-proven PR-011 Session-0 USER32 boundary as an A/B discriminator, then implement only the minimum Host-owned generic scoped compatibility authority if the discriminator is positive.

## Technical Decision

Do not start by adding new DLL/file/Registry/COM permissions.

Reuse the existing PR-011 window-station/desktop read primitive as diagnostic evidence.

Current architecture:

~~~text
generic scoped:
  workspace + runtime roots
  no Session-0 read grant

verification descendants:
  trusted root handshake
  exact SID Session-0 read grant
  USER32-dependent children supported
~~~

PR-018 must first determine whether Unity belongs to that same class.

## Stacked Delivery

PR-018 is stacked on PR-017 because both tasks modify the same sandbox boundary and PR-017 S03 depends on this compatibility repair.

Delivery order:

~~~text
PR-018 candidate
→ PR-017 branch
→ combined Host activation
→ PR-017 S03 replay
→ PR-017 acceptance
→ main
~~~

Do not merge PR-018 independently to main ahead of PR-017.

## Planned Work

### S01 — Exact real-Windows A/B discriminator

Build a bounded diagnostic fixture using the stacked PR-017 candidate.

A and B must share:

- Unity 6000.6.4f1 executable;
- AppContainer identity model;
- Job/no-breakaway containment;
- workspace/runtime roots;
- Unity child command.

A:

~~~text
no Session-0 read authority
→ reproduce 0xC0000142
~~~

B:

~~~text
only the existing PR-011 window-station/desktop read masks
→ capture raw Unity child outcome
~~~

Diagnostic B may call the existing low-level helper in test/diagnostic code. It must not change production generic admission before evidence exists.

Required evidence:

- raw child exit for A and B;
- exact AppContainer SID;
- exact masks;
- Job containment;
- cleanup/readback showing SID absence;
- runtime-root cleanup and terminal closure.

Decision:

~~~text
B crosses initialization boundary
→ hypothesis_confirmed
→ S02 may implement

B still fails
→ hypothesis_rejected
→ stop
→ Plan Revision required
~~~

### S02 — Generic compatibility admission, only if S01 confirms

Preferred policy:

~~~yaml
mutation_execution:
  runtime_session_object_read_enabled: false
~~~

Freeze exact key during Plan Review.

Policy rules:

- default false;
- boolean Host config only;
- no request override;
- included in policy digest.

Generalize the existing verification helper only as needed into one shared exact-SID window-object DACL primitive. Preserve the verification-specific trusted-root handshake.

Generic enabled path:

~~~text
durable scope/AppContainer identity
→ exact workspace/runtime authority
→ exact SID Session-0 read grant
→ readback masks
→ untrusted scoped root starts
~~~

Because this is generic untrusted execution, add durable authority tracking in the existing MutationScopeStore if needed. Do not create another ledger.

Cleanup:

~~~text
reacquire current service Session-0 window station/desktop
→ remove exact SID
→ read back absence
→ clear durable marker
→ permit terminal
~~~

Any ambiguity stays revoked.

### Focused tests

Likely files after positive S01:

~~~text
src/sentinelx_core/policy.py
src/sentinelx_core/mutation_placement.py
src/sentinelx_core/mutation_scope.py
src/sentinelx_core/windows_mutation_sandbox.py
config.example.windows.yaml
tests/test_policy.py
tests/test_mutation_scope_admission.py
tests/test_windows_mutation_sandbox.py
tests/test_scoped_script_execution.py
tests/test_verification_windows_materialization.py
tests/test_verification_scoped_execution.py
~~~

Required cases:

1. default false;
2. valid policy parsing;
3. caller cannot override;
4. digest changes;
5. disabled generic path grants nothing;
6. enabled path uses exact PR-011 masks;
7. forbidden bits absent;
8. activation failure cleans SID;
9. process/script failure cleans SID;
10. cleanup ambiguity remains revoked;
11. retry can close and terminalize;
12. verification trusted-root handshake unchanged;
13. no Job breakaway;
14. no interactive desktop rights.

### S03 — Exact-candidate Unity proof and PR-017 replay

Host proof requires:

~~~text
runtime_session_object_read_enabled = true
runtime_acl_timeout_seconds = 300
operator_unrestricted_enabled = false
Unity runtime root = C:\Program Files\Unity\Hub\Editor\6000.6.4f1
~~~

Sequence:

A. scoped Python marker → returncode 0 / terminal

B. classified Unity child probe → not 0xC0000142

C. deterministic Unity -version or bounded batch/version probe → success

D. closure → no active Job/process authority, runtime-root SID absent, window-station SID absent, desktop SID absent

E. negative security proof → no screen/clipboard/global-atom/create-window/write authority, no escape, no breakaway

Then integrate PR-018 into PR-017 and rerun PR-017 S03 on the combined candidate.

## Verification Strategy

Focused tests first, then Windows security/regression suites, then real Host Unity proof.

CI alone cannot satisfy the task because the defining bug is a real Session-0/AppContainer/Unity compatibility boundary.

## Slice Proposal

Plan Review should compile:

~~~text
S01 — A/B discriminator; confirm or reject Session-0 hypothesis

S02 — only if confirmed:
      Host-owned generic session-object compatibility
      + durable cleanup
      + regression closure

S03 — exact-candidate Host Unity proof
      + integrate into PR-017
      + replay PR-017 S03
~~~

If S01 rejects the hypothesis, S02/S03 must not proceed under Plan Revision 1.

## Concurrent Reconciliation

PR-017 is the stacked base and must be re-read before every slice.

PR-016 has planned overlap in windows_mutation_sandbox.py; if product overlap appears before PR-018 mutation, stop and reconcile.

PR-015 may move runtime/provider composition; re-read overlap but do not broaden PR-018 to solve unrelated invocation behavior.

## Risks

RSK-1: matching 0xC0000142 does not prove the same root cause.
Mitigation: exact A/B before product mutation.

RSK-2: generic untrusted root receives extra Session-0 visibility.
Mitigation: explicit Host-owned default-off setting, exact read-only masks, negative rights tests.

RSK-3: leaked shared-object ACE.
Mitigation: exact SID lifecycle, durable marker if required, removal/readback and retryable terminalization.

RSK-4: stacked branch drift.
Mitigation: pre-slice head/overlap readback.

RSK-5: Unity needs a different resource.
Mitigation: hard-stop after negative S01; Plan Revision before further diagnostics.

## Plan Review Questions

1. Is the PR-011 Session-0 A/B discriminator sufficient without adding a tracing subsystem?
2. Is a Host-owned default-off generic session-object switch the correct product boundary if positive?
3. Are the PR-011 masks the maximum acceptable V1 authority?
4. Is generic pre-root grant timing acceptable with these read-only rights?
5. Must generic session-object authority be durably represented in MutationScopeStore?
6. Do negative tests sufficiently prove no interactive desktop/clipboard/screen/create-window capability?
7. Is stacked integration PR-018 → PR-017 → main the correct delivery order?
