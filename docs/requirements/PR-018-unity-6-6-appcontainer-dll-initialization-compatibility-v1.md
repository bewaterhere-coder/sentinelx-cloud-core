# PR-018 — SentinelX Unity 6.6 AppContainer DLL Initialization Compatibility V1

## State — Requirement Revision 1

~~~yaml
project_id: sentinelx-cloud-core
task_id: PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1
requirement_revision: 1
development:
  stage: implementation
  gates:
    requirement_ready: true
    plan_approved: true
    acceptance_approved: false
    completion_verified: false
  plan_revision: 2
  implementation_authorized: true
  next_expected_actor: implementer
  blocking_findings:
    - S03 exact Host proof is blocked because the live SentinelX package was only partially projected to PR #18 before restart; the Host is offline and no S03 Unity/AppContainer result has been produced.
    - Full Git-tree reconciliation found three additional changed candidate runtime files not projected before restart (handlers/__init__.py, handlers/devforge_runtime.py, user_git.py) plus ten installed-only modules absent from the candidate tree; exact source reinstall/readback is required before S03 may resume.
  current_slice: S03
  current_slice_state: pending
  completed_slices: [S01, S02]
transport:
  type: github-pr
  pr_number: 18
  branch: task/unity-6-6-appcontainer-dll-initialization-compatibility-v1
  base_branch: task/large-runtime-root-acl-cleanup-timeout-recovery-v1
  stacked_on_pr: 17
artifacts:
  plan: docs/plans/PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1-plan.md
  latest_plan_review: docs/reviews/PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1-plan-review-r2.md
  latest_plan_review_transition_receipt: docs/reviews/PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1-plan-review-r2-transition-receipt.yaml
  latest_plan_remediation: docs/checkpoints/PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1-plan-remediation-r2-20261007.yaml
  latest_plan_remediation_transition_receipt: docs/reviews/PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1-plan-remediation-r2-transition-receipt.yaml
  execution_slice_set: docs/execution/PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1-slices.yaml
  latest_slice_checkpoint: docs/checkpoints/PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1-s03-blocked-incomplete-host-candidate-activation-20261008.yaml
  latest_slice_completion_receipt: docs/reviews/PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1-s02-completion-receipt.yaml
related_tasks:
  predecessor:
    - PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1
  evidence_predecessor:
    - PR-011-scoped-verification-toolchain-dependency-capsule-v1
  downstream_consumer:
    - PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1/S03
    - DemonTD/CLIENT-CODE-ARCHITECTURE-BASELINE-V1/C01
~~~

## Problem

PR-017 isolated a remaining compatibility failure after large-runtime ACL lifecycle repair.

Exact live evidence on candidate f7249aef0d25085eb98e741596b6f567ebd83966 proves:

~~~text
scoped Python/AppContainer root        PASS
Unity.exe child process creation       PASS
Unity runtime-root ACL lifecycle       PASS
Job/process cleanup                    PASS
scope terminalization                  PASS
Unity child initialization             FAIL
Windows status                         0xC0000142
                                      STATUS_DLL_INIT_FAILED
~~~

PR-011 contains a strong existing discriminator. On the LocalSystem service session:

~~~text
non-USER32 AppContainer descendants    PASS
USER32-dependent descendants           DLL initialization failure
minimum Session-0 window-object read   fixes the class
~~~

The proven PR-011 root cause was service_session_window_object_read_authority_missing.

Current code keeps that authority verification-only through _grant_verification_session_read(), _remove_verification_session_read(), and enable_verification_descendants(). Generic execute_scoped gets workspace/runtime-root authority but not the Session-0 window station / desktop read grant.

Unity may therefore be reproducing the same boundary, but this remains a hypothesis.

## Repository / Stack Reality

Canonical main:

~~~text
main@018b78ca20984176d53fbe90039dc795a7f2742f
~~~

PR-018 is intentionally stacked on PR-017:

~~~text
base branch:
task/large-runtime-root-acl-cleanup-timeout-recovery-v1

PR-017 head at bootstrap:
3858c7d0e46295d5e0dc184bb21e76da7c963346
~~~

Required integration order:

~~~text
PR-018
→ PR-017 branch
→ rerun PR-017 S03
→ PR-017 acceptance
→ main
~~~

This avoids parallel redefinition of the same windows_mutation_sandbox authority boundary.

## Goal

Prove whether Unity 6000.6.4f1 is failing on the already-known Session-0 USER32 authority gap and, only if proven, add the minimum provider-owned generic scoped compatibility authority required to cross it.

Canonical discriminator:

~~~text
same Host
same Unity.exe
same AppContainer/Job
same runtime roots
same probe

A: no Session-0 window-object read
   → reproduce current 0xC0000142

B: exact existing PR-011 minimum read masks only
   → measure raw Unity child outcome
~~~

If B succeeds, the existing primitive may be generalized under a Host-owned default-off compatibility policy.

If B fails, stop and identify the next concrete boundary before proposing any wider permission.

## Required Behavior

### R1 — Evidence-first A/B discriminator

Before any generic product authority change, real Windows proof must compare A and B with Session-0 read authority as the only material security difference.

Both variants must use Unity 6000.6.4f1, identical AppContainer/Job model, workspace/runtime roots and child command.

The proof must capture the raw Unity child Windows exit status, not infer success from a Python wrapper.

### R2 — Hard stop when hypothesis is false

If B still returns 0xC0000142 or another startup failure:

- do not generalize the PR-011 grant;
- do not guess filesystem, Registry, COM or capability permissions;
- do not disable AppContainer or use Job breakaway;
- persist a diagnostic checkpoint;
- require Plan Revision before further product implementation.

### R3 — Host-owned generic scoped compatibility admission

Only after positive R1 proof may generic scoped execution gain a Host-owned compatibility control.

V1 must be:

- default off;
- Host config only;
- not caller-controlled through execute_scoped, script, lineage, env or verification payload;
- represented in provider policy identity/digest;
- observable in bounded audit/readiness evidence.

Recommended semantic key for Plan Review:

~~~yaml
mutation_execution:
  runtime_session_object_read_enabled: false
~~~

### R4 — Maximum V1 window-object masks

If R1 is positive, the initial maximum masks are the existing PR-011 masks.

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

Forbidden:

~~~text
WINSTA_ACCESSCLIPBOARD
WINSTA_ACCESSGLOBALATOMS
WINSTA_CREATEDESKTOP
WINSTA_WRITEATTRIBUTES
WINSTA_READSCREEN
DESKTOP_CREATEWINDOW
DESKTOP_WRITEOBJECTS
~~~

Authority beyond these masks requires Requirement Revision.

### R5 — Exact SID lifecycle and fail-closed cleanup

Any generic session-object grant must:

1. target only the exact scope AppContainer SID;
2. be object-local/non-inheriting;
3. be admitted after scope identity is durably bound;
4. participate in runtime authority closure;
5. be removed on normal completion and all failure paths;
6. be read back as absent before terminal success;
7. keep the scope revoked when cleanup cannot be proven.

Use the existing MutationScopeStore as the only durable authority ledger if a new marker is required.

### R6 — Policy drift and audit evidence

The Host compatibility setting and effective authority semantics must participate in provider-owned policy identity.

Audit evidence must prove whether the compatibility authority was admitted without exposing unrelated shared DACL state.

### R7 — No interactive desktop escape

This task supports headless/batch initialization only.

It must not introduce:

- window creation rights;
- desktop writes;
- screen read;
- clipboard/global-atom access;
- desktop creation;
- interactive user-session fallback;
- AppContainer escape;
- Job breakaway.

### R8 — Real Unity 6.6 initialization proof

Acceptance must use:

~~~text
C:\Program Files\Unity\Hub\Editor\6000.6.4f1\Editor\Unity.exe
~~~

Success requires more than CreateProcess.

At least one deterministic probe must cross the current DLL initialization boundary, for example:

~~~text
Unity.exe -version
→ clean exit 0 with deterministic version evidence
~~~

or an equivalent bounded batch/version probe.

The exact candidate must no longer return 0xC0000142.

Terminal closure must prove zero active Job/process authority plus exact runtime-root and session-object SID closure.

### R9 — Regression compatibility

Preserve:

- all PR-017 runtime ACL timeout/recovery semantics;
- PR-011 verification Session-0 handshake behavior;
- PR-012 explicit execution-profile contract;
- exact workspace isolation;
- canonical repository firewall;
- Job/no-breakaway containment;
- START/SPAWN/FINISH ordering;
- fail-closed terminalization.

If PR-016 gains overlapping product changes before implementation, stop and reconcile.

### R10 — Stacked integration closes PR-017 S03

An isolated PR-018 Unity success is insufficient.

The accepted PR-018 candidate must be integrated into PR-017, then PR-017 S03 must be replayed against the combined candidate before PR-017 can proceed toward acceptance/main.

## Non-Goals

This task does not:

- add broad DLL tracing infrastructure before the known hypothesis is falsified;
- make Unity interactive;
- disable AppContainer;
- enable Job breakaway;
- add unrestricted shell fallback;
- grant persistent shared Session-0 authority;
- let callers select window objects or masks;
- solve arbitrary Windows application compatibility;
- modify DemonTD game code;
- weaken PR-017 cleanup semantics.

## Acceptance Criteria

1. exact PR-017 stacked baseline is used;
2. Variant A reproduces the Unity initialization failure;
3. Variant B changes only the approved Session-0 read authority;
4. raw child outcome proves or falsifies the hypothesis;
5. no product authority is generalized if the hypothesis is false;
6. if positive, generic compatibility is Host-owned and default off;
7. callers cannot enable or alter it;
8. effective masks do not exceed R4;
9. forbidden interactive/session rights remain absent;
10. exact AppContainer SID is removed from both shared window objects;
11. cleanup ambiguity remains revoked/fail-closed;
12. policy drift reflects the setting;
13. Unity no longer returns 0xC0000142;
14. deterministic real Unity initialization proof passes;
15. final closure has no active Job/process/write/runtime/session-object authority;
16. PR-011 regressions remain green;
17. PR-017 ACL/recovery regressions remain green;
18. combined PR-018-on-PR-017 replay satisfies PR-017 S03;
19. no unrestricted or interactive-session fallback is introduced.

## Requirement Readiness

~~~yaml
requirement_ready: true
diagnostic_hypothesis_frozen: true
implementation_fix_not_yet_frozen: false
material_product_decision_pending: false
current_task_p0_dependencies:
  - PR-017 stacked base remains available
~~~
