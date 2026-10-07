# PR-018 Unity 6.6 AppContainer DLL Initialization Compatibility V1 — Plan R2

## Status

~~~yaml
task_id: PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1
plan_revision: 2
plan_status: ready_for_review
implementation_authority: false
requirement_ref: docs/requirements/PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1.md
requirement_revision: 1
prior_plan_revision: 1
rejected_review_ref: docs/reviews/PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1-plan-review-r1.md
transport:
  type: github-pr
  pr_number: 18
  branch: task/unity-6-6-appcontainer-dll-initialization-compatibility-v1
  base: task/large-runtime-root-acl-cleanup-timeout-recovery-v1
  stacked_on_pr: 17
~~~

## R2 Remediation Delta

Plan R2 preserves Requirement Revision 1 and the accepted evidence-first direction from Plan R1. It changes only the two plan-local findings from Plan Review R1.

### F1 resolved — PR-018 does not execute PR-017 work

PR-018 implementation authority is bounded to PR #18 and its canonical branch.

The revised ownership boundary is:

~~~text
PR-018 S01/S02/S03
→ mutate/verify PR-018 transport only
→ #开发验收 PR-018
→ after Acceptance, #开发完成 PR-018 may integrate the accepted PR-018 transport into its configured base branch
→ PR-017 independently re-reads its own canonical Task/transport
→ PR-017 S03 replay proceeds only through PR-017-owned workflow/command authority
~~~

No PR-018 Slice may:

- mutate PR-017 Task state, Plan, Slice Set, checkpoint, receipt, branch or PR metadata;
- mark PR-017 S03 complete;
- invoke or emulate PR-017 `#开发执行`;
- create a replacement integration branch or transport.

Requirement R10 remains a cross-Task integration obligation. PR-018 completion is not evidence that PR-017 S03 or the wider dependent DemonTD path is complete.

### F2 resolved — generic Session-0 authority is durable

For generic untrusted scoped execution, process-local `_verification_session_reads` is not authoritative and is not reused as the lifecycle ledger.

Plan R2 requires one durable session-object authority binding inside the existing `MutationScopeStore` record/lifecycle. No second ledger is permitted.

The durable binding must be sufficient to identify and clean the exact provider-selected service Session-0 window objects after process-local handles are lost. V1 must persist/read back, before any shared-DACL grant:

~~~yaml
session_object_read_binding:
  cleanup_required: true
  session_id: 0
  window_station_identity: <provider-observed broker window-station identity>
  desktop_identity: <provider-observed broker thread-desktop identity>
  window_station_mask: <exact R4 mask>
  desktop_mask: <exact R4 mask>
~~~

The exact AppContainer SID remains the scope's existing durable `sandbox_identity`; callers never supply SID, object identity or masks.

If exact window-object identity cannot be observed and durably rebound/reacquired, generic compatibility admission fails closed.

## Plan Objective

Diagnose Unity 6000.6.4f1 `0xC0000142 / STATUS_DLL_INIT_FAILED` using the already-proven PR-011 Session-0 USER32 boundary as an A/B discriminator. Only after a positive discriminator may SentinelX add the minimum Host-owned generic scoped compatibility authority required to cross that boundary.

Do not start by adding new DLL/file/Registry/COM permissions.

## Technical Decision

Current architecture:

~~~text
generic scoped:
  workspace + runtime roots
  no Session-0 window-object read authority

verification descendants:
  trusted root handshake
  exact SID Session-0 read grant
  process-local verification bookkeeping
  USER32-dependent descendants supported
~~~

PR-018 first proves whether Unity is the same compatibility class.

If positive, generic scoped execution gains a separate Host-owned, default-off compatibility admission whose authority is durably represented and cleaned through the existing MutationScopeStore lifecycle.

## Frozen V1 Policy Boundary

Canonical key:

~~~yaml
mutation_execution:
  runtime_session_object_read_enabled: false
~~~

Rules:

- default `false`;
- boolean Host configuration only;
- no caller/request/script/env/lineage/verification override;
- participates in provider policy/placement digest;
- effective admission is observable in bounded audit/readiness evidence;
- no caller-selected Session, window station, desktop, SID or masks.

Maximum V1 rights remain exactly Requirement R4 / PR-011 masks:

Window station:

~~~text
READ_CONTROL
WINSTA_ENUMDESKTOPS
WINSTA_READATTRIBUTES
WINSTA_ENUMERATE
~~~

Desktop:

~~~text
READ_CONTROL
DESKTOP_READOBJECTS
DESKTOP_ENUMERATE
~~~

No broader authority is permitted under Plan R2.

## Planned Work

### S01 — Exact real-Windows A/B discriminator

Build a bounded diagnostic fixture on the exact stacked PR-017 baseline.

A and B share:

- Unity 6000.6.4f1 executable;
- exact AppContainer identity model;
- Job/no-breakaway containment;
- workspace/runtime roots;
- Unity child command;
- broker/session context.

Variant A:

~~~text
no Session-0 window-object read authority
→ reproduce and capture raw Unity child 0xC0000142
~~~

Variant B:

~~~text
only existing PR-011 window-station/desktop read masks
→ capture raw Unity child outcome
~~~

Diagnostic B may use the existing low-level PR-011 helper in bounded diagnostic/test code. It must not change production generic admission before evidence exists.

Required evidence:

- raw child Windows exit for A and B;
- exact AppContainer SID;
- exact effective masks;
- observed Session-0/broker object identity;
- Job containment/no-breakaway;
- exact SID absence from window station and desktop after cleanup;
- runtime-root cleanup and terminal closure.

Decision:

~~~text
B crosses DLL initialization boundary
→ hypothesis_confirmed
→ S02 becomes eligible

B still fails startup
→ hypothesis_rejected
→ persist diagnostic checkpoint
→ stop Plan R2
→ no S02/S03 product implementation
→ new Plan Revision required before any different permission hypothesis
~~~

### S02 — Generic compatibility admission and durable lifecycle, only if S01 confirms

#### S02.1 Shared DACL primitive

Refactor only as needed so verification and generic paths can share the low-level exact-SID window-object DACL merge/revoke/readback primitive.

The existing verification-specific trusted-root handshake and its admission timing remain unchanged.

#### S02.2 Durable pre-grant binding

Before the first generic Session-0 DACL grant can become effective:

1. scope/AppContainer identity is already durably bound;
2. provider observes the current service Session-0 window station + thread desktop identities;
3. provider verifies Session ID 0 and exact R4 masks;
4. `MutationScopeStore` persists `cleanup_required=true` plus the provider-observed window-object binding;
5. the durable record is read back;
6. only then may the shared DACL primitive grant the exact scope AppContainer SID.

The durable marker intentionally means "cleanup may be required", not "both grants definitely succeeded". Therefore a crash or partial grant cannot publish a false no-authority state.

#### S02.3 Grant and activation

Generic enabled path:

~~~text
durable scope/AppContainer identity
→ durable cleanup-required Session-0 binding
→ readback
→ grant exact SID to exact window station with R4 mask
→ exact readback
→ grant exact SID to exact desktop with R4 mask
→ exact readback
→ only then allow untrusted scoped process to continue
~~~

Any first/second-object failure triggers bounded cleanup. The durable marker remains set until both exact objects prove SID absence.

No interactive rights are added.

#### S02.4 Terminalization and restart/retry

`MutationScopeStore.terminalize_scope()` must treat a durable Session-0 binding with `cleanup_required=true` as residual runtime authority.

Cleanup must work without relying on process-local `_verification_session_reads` handles:

~~~text
read durable session-object binding
→ reacquire/verify the exact provider-bound Session-0 window station and desktop
→ remove exact scope AppContainer SID from desktop
→ read back exact SID absence
→ remove exact scope AppContainer SID from window station
→ read back exact SID absence
→ clear durable session-object binding
→ read back cleared marker
→ only then permit terminal
~~~

If the current broker cannot prove it reacquired the same durable window-object identities, cleanup fails closed and the scope remains revoked.

A service/broker restart or loss of in-memory maps must not erase cleanup responsibility.

#### S02.5 MutationScopeStore / closure model

Use the existing store only. Extend the existing runtime-authority representation so that:

- the durable session-object binding is serialized/read back;
- runtime closure reports whether Session-0 cleanup responsibility remains;
- `has_runtime_authority` includes it;
- terminal state is impossible while it remains;
- scope digest / immutable identity semantics are preserved according to the existing runtime-field model;
- no second state machine or authority ledger is introduced.

#### S02.6 Policy/audit surface

Add `runtime_session_object_read_enabled` to the provider-owned policy model and policy/placement digest.

Audit/readiness may report bounded facts such as enabled/disabled and exact scope identity binding, but must not dump unrelated shared DACL entries.

### S02 focused verification

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

1. default policy is false;
2. valid boolean parsing;
3. caller/request cannot override;
4. policy digest changes;
5. disabled generic path grants nothing;
6. enabled path uses exact PR-011 masks only;
7. forbidden rights are absent;
8. durable cleanup marker is persisted/read back before first DACL grant;
9. first-object grant failure keeps/cleans durable responsibility correctly;
10. second-object grant failure compensates both exact objects and does not clear marker before dual absence readback;
11. activation/process/script failure cleans exact SID from both objects;
12. cleanup ambiguity leaves scope revoked;
13. terminalization treats durable Session-0 binding as residual authority;
14. simulated service restart / empty in-memory session-handle map can reacquire and clean from durable binding;
15. object identity mismatch after restart fails closed rather than cleaning an unproven target;
16. retry can transition revoked -> terminal only after dual SID-absence + marker-clear readback;
17. verification trusted-root handshake behavior is unchanged;
18. no Job breakaway;
19. no interactive desktop/screen/clipboard/global-atom/create-window/write rights.

### S03 — Exact PR-018 candidate Unity proof

S03 verifies only the PR-018 canonical candidate. It does not mutate or advance PR-017.

Host proof configuration:

~~~text
runtime_session_object_read_enabled = true
runtime_acl_timeout_seconds = 300
operator_unrestricted_enabled = false
Unity runtime root = C:\Program Files\Unity\Hub\Editor\6000.6.4f1
~~~

Required sequence:

A. scoped Python marker → returncode 0 / terminal

B. classified Unity child probe → raw child result is not `0xC0000142`

C. deterministic `Unity.exe -version` or bounded batch/version probe → clean deterministic success

D. closure → no active Job/process authority; exact runtime-root SID absent; exact window-station SID absent; exact desktop SID absent; durable Session-0 cleanup binding cleared

E. negative security proof → no screen/clipboard/global-atom/create-window/write authority, no AppContainer escape, no Job breakaway

F. affected PR-011 / PR-012 / PR-017 sandbox regression suites remain green on the PR-018 candidate

S03 stops at PR-018 implementation evidence. It does not merge PR-018, mutate PR-017, or replay PR-017 S03.

## Cross-Task Integration Boundary

After all PR-018 slices complete:

~~~text
#开发验收 PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1
~~~

If PR-018 Acceptance is approved, only then may:

~~~text
#开发完成 PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1
~~~

perform PR-018's transport finalization into its configured base branch.

After that integration is canonically read back, PR-017 remains a separate Task. Its own workflow must re-read the combined branch and resume PR-017 S03 using PR-017-owned command authority.

PR-018 must never claim that PR-017 S03, PR-017 Acceptance, or DemonTD downstream integration is complete without their own receipts.

## Verification Strategy

Order:

1. S01 real-Windows A/B discriminator;
2. only on positive S01, focused durable-lifecycle implementation/tests;
3. affected Windows security/regression suites;
4. real Host exact-candidate Unity proof.

CI alone cannot satisfy the defining Session-0/AppContainer/Unity compatibility evidence.

## Slice Proposal

Plan Review should compile exactly:

~~~text
S01 — A/B discriminator
      confirm/reject Session-0 hypothesis

S02 — only if S01 confirms
      Host-owned default-off generic session-object compatibility
      + durable pre-grant cleanup binding
      + crash/restart-safe cleanup/readback
      + regression closure

S03 — exact PR-018 candidate Host Unity proof
      + security/closure/regression evidence
      + no PR-017 mutation/replay
~~~

No Slice is authorized until Plan Review approves Plan R2 and persists/read-backs the exact Slice Set.

If S01 rejects the hypothesis, S02/S03 do not proceed under Plan R2.

## Concurrent Reconciliation

Before every slice:

- re-read PR-018 head and stacked PR-017 base head;
- preserve PR #18 branch/transport identity;
- if PR-017 base moves materially, stop and reconcile before mutation;
- if PR-016 introduces overlapping product changes in `windows_mutation_sandbox.py` or related authority code, stop and reconcile;
- if PR-015 changes overlapping policy/config semantics, reconcile those semantics without broadening this Task.

## Risks

### RSK-1 — Same status, different root cause

Matching `0xC0000142` is not proof of the same cause.

Mitigation: exact A/B before product mutation.

### RSK-2 — Durable marker published although no grant occurred

This is intentional fail-closed bookkeeping: the marker means cleanup may be required. Exact SID-absence readback allows safe clear.

### RSK-3 — Shared Session-0 ACE survives broker restart

Mitigation: durable provider-bound object identity + existing scope SID + cleanup-required marker; cleanup/retry does not depend on in-memory handles.

### RSK-4 — Reacquired object identity differs

Mitigation: fail closed and keep scope revoked. Do not remove authority from an unproven object.

### RSK-5 — Generic visibility is wider than verification-only path

Mitigation: Host-owned default-off policy, exact read-only masks, exact SID, bounded audit, forbidden-rights regression tests.

### RSK-6 — Cross-Task ownership drift

Mitigation: PR-018 Slices stop at PR-018 evidence; integration/finalization and PR-017 replay use their own canonical command boundaries.

### RSK-7 — Unity needs another resource

Mitigation: negative S01 hard-stop and new Plan Revision before any new permission hypothesis.

## Plan Review Questions

Plan R2 freezes the prior open questions as follows:

1. PR-011 Session-0 A/B is sufficient as the first discriminator; no tracing subsystem is added before falsification.
2. Generic V1 policy is `mutation_execution.runtime_session_object_read_enabled`, Host-owned and default off.
3. PR-011 masks are the maximum V1 rights.
4. Generic grant may occur before untrusted root continuation only after durable cleanup-required binding is persisted/read back.
5. Durable MutationScopeStore representation is mandatory for generic Session-0 authority.
6. Negative rights tests plus exact DACL readback are required.
7. PR-018 implementation does not integrate/replay PR-017; cross-Task progression remains owned by finalization + PR-017 workflow.
