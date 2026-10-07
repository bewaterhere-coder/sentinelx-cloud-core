# PR-018 — Unity 6.6 AppContainer DLL Initialization Compatibility V1 — Plan Review R2

## Review State

~~~yaml
task_id: PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1
review_target: plan
requirement_revision: 1
requirement_blob_sha: 74ec2e438d05bdf93b2b8ceb81ab98007b32d66c
plan_revision: 2
plan_blob_sha: 1d171bce2815a5dba428746ad65f5cab408794a0
reviewed_task_head: af4bc1be32a979500d56005b5fe9b42fb46ad32e
result: Approved
runtime:
  devforge_version: "2.93.0"
  devforge_revision: fb0d02d646d6312d938fdfb3fbe03c64319fb122
  review_contract: "1.3"
  artifact_state_transition_contract: "1.1"
  slicing_contract: "1.1"
repository_reality:
  canonical_main: 018b78ca20984176d53fbe90039dc795a7f2742f
  canonical_pr: 18
  canonical_branch: task/unity-6-6-appcontainer-dll-initialization-compatibility-v1
  stacked_base_pr: 17
  stacked_base_head: 3858c7d0e46295d5e0dc184bb21e76da7c963346
  open_pr15_head: 0500e457495a148573fcc2e184d6c7dca8058201
  open_pr16_head: c26de0e9fb0d908e9dc6bd16403b07965547f099
next_gate: implementation
next_expected_actor: implementer
~~~

## Decision

**Approved.**

Plan R2 closes both Plan Review R1 findings without changing Requirement Revision 1 or the canonical PR #18 transport.

The evidence-first discriminator, default-off Host policy, maximum read-only mask boundary, durable generic Session-0 authority lifecycle, crash/restart-safe cleanup requirement, and cross-Task ownership boundary are sufficiently frozen for implementation.

## Review Checks

- **Solution direction: Pass.** The Plan still tests the already-proven PR-011 Session-0 USER32 boundary before adding any generic authority.
- **Scope control: Pass.** A negative A/B result stops Plan R2. No filesystem, Registry, COM, AppContainer bypass, Job breakaway or general Windows compatibility expansion is authorized.
- **Technical feasibility: Pass.** Existing code already has exact-SID window-object DACL read/merge/revoke primitives, exact PR-011 masks, MutationScopeStore two-phase terminalization and runtime authority fields. R2 extends those existing boundaries rather than inventing a second lifecycle.
- **Durable authority lifecycle: Pass.** Generic authority must publish a cleanup-required durable binding before the shared-DACL mutation can become effective; terminalization cannot succeed until both exact objects prove SID absence and the binding is cleared/read back.
- **Crash/restart behavior: Pass.** Generic cleanup is explicitly independent of process-local `_verification_session_reads`; loss of in-memory handles cannot erase cleanup responsibility.
- **Policy ownership: Pass.** `mutation_execution.runtime_session_object_read_enabled` is Host-owned, default-off, caller-inaccessible and participates in policy identity.
- **Security maximum: Pass.** Requirement R4 / PR-011 masks remain the maximum V1 authority and interactive rights remain forbidden.
- **Behavioral verification: Pass.** Real Unity evidence requires raw child outcome, deterministic initialization success and exact residual-authority closure; wrapper success or CreateProcess alone cannot satisfy S03.
- **Cross-Task ownership: Pass.** PR-018 slices no longer mutate or advance PR-017. PR-018 finalization and later PR-017 workflow retain separate command/receipt ownership.
- **UX Contract: NotApplicable.** This Task has no user-visible product UI/interaction contract.
- **Concurrent PR-017: Pass.** Stacked base head remains the reviewed `3858c7d...`.
- **Concurrent PR-016: Pass.** Current PR-016 still has no product overlap with the Session-0 authority files.
- **Concurrent PR-015: Pass with reconciliation guard.** PR-015 still overlaps `policy.py` and `config.example.windows.yaml`, but movement since the prior review baseline is Task/authorization documentation only. S02 must re-read current PR-015 semantics immediately before overlapping mutation.

## Mandatory Implementation Guards

1. Every Slice must preserve PR #18 branch/transport identity and re-read PR-018 head plus PR-017 stacked base before mutation.
2. S01 Variant B may use the existing PR-011 verification-only DACL primitive only for bounded diagnosis. Before S01 can checkpoint success, both window objects must prove the exact diagnostic SID absent. Unproven cleanup blocks S01 and forbids S02.
3. S01 must capture the **raw Unity child Windows outcome**. Python/wrapper return success is not discriminator evidence.
4. S02 is eligible only when the durable S01 checkpoint says `hypothesis_confirmed`. A negative or ambiguous S01 requires a new Plan revision.
5. The generic durable window-object identity MUST be restart-reacquirable provider identity. Raw process-local HANDLE values are forbidden as durable identity.
6. Before the first generic DACL grant, the cleanup-required binding must be persisted and read back. The marker means "cleanup may be required", so it stays set across partial grant/failure ambiguity.
7. Clearing the durable binding requires exact SID-absence readback from **both** the bound desktop and window station. No dual readback -> no marker clear -> no terminal success.
8. If a restarted broker cannot prove it reacquired the same durable object identities, leave the scope revoked and fail closed.
9. Existing PR-011 verification trusted-root handshake/timing remains unchanged; generic lifecycle work must not silently migrate verification semantics.
10. Before S02 changes `policy.py` or `config.example.windows.yaml`, re-read PR-015 current head and reconcile any product-semantic overlap.
11. If PR-016 introduces product overlap in the sandbox/session-object boundary before a Slice mutation, stop and reconcile.
12. One explicit `#开发执行 PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1` completes at most one Slice.

## Slice Compilation

Compile exactly:

1. **S01 — Real Windows A/B discriminator.** Reproduce A, apply only existing PR-011 minimum Session-0 read authority for B, capture raw Unity outcome, prove exact diagnostic cleanup, and persist `hypothesis_confirmed` or `hypothesis_rejected`.
2. **S02 — Generic default-off compatibility + durable lifecycle.** Only after confirmed S01, add Host policy/digest semantics, durable pre-grant session-object binding, exact grant/readback, restart-safe cleanup/reacquisition, terminalization integration, negative-rights tests and regression coverage.
3. **S03 — Exact PR-018 candidate Unity/security proof.** Prove Python baseline, Unity no longer returns 0xC0000142, deterministic Unity initialization succeeds, all runtime/session-object authority closes, forbidden rights remain absent, and affected PR-011/PR-012/PR-017 regressions remain green. Do not mutate/replay PR-017.

## Gate Result

~~~yaml
decision: Approved
blocking_findings: []
plan_approved: true_after_slice_set_readback
implementation_authorized: true_after_slice_set_readback
next_stage: implementation
current_slice_after_transition: S01
canonical_next_action: "#开发执行 PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1"
~~~

No SentinelX product code or Host policy is modified by this review.
