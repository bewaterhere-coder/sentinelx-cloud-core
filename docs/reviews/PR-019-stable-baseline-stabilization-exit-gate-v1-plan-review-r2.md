# PR-019 — SentinelX Stable Baseline & Stabilization Exit Gate V1 — Plan Review R2

## Review State

~~~yaml
task_id: PR-019-stable-baseline-stabilization-exit-gate-v1
review_target: plan
requirement_revision: 1
requirement_blob_sha: b0f28dc9bc6b553487eca04636e95b854e90927b
plan_revision: 2
plan_blob_sha: 4aff64a35c00d3e854fc63046faf3045caddaf0b
reviewed_task_head: 3f13e0c0b1383c24217fa919447342b2086b9e88
result: Approved
runtime:
  devforge_version: "2.95.0"
  devforge_revision: 162337cc2fffa710d49a9cd38ab4cc8643f09ffb
  review_contract: "1.3"
  slicing_contract: "1.1"
repository_reality:
  canonical_main: 1028030b33f0ea792a884491a431fffe566f6aa5
  canonical_pr: 19
  canonical_branch: task/stable-baseline-stabilization-exit-gate-v1
  pr017_head: 3858c7d0e46295d5e0dc184bb21e76da7c963346
  pr018_head: 5c1c97542aa9f23f52bdb892918d72767779f1a8
next_gate: implementation
next_expected_actor: implementer
~~~

## Decision

**Approved.**

Plan R2 closes all three Plan Review R1 findings without changing Requirement Revision 1, Task identity, canonical PR #19 transport, project binding or SentinelX security authority.

The Plan now has a finite implementation and verification boundary:

- exact-candidate live Host identity is proven before live Stable Baseline evidence is consumed;
- Direct Codex Git readiness follows its actual user-scoped Git primitive rather than unrelated generic authenticated-Git policy;
- local Git-context proof and remote GitHub publication proof are explicitly separate;
- missing/stale/not-yet-attempted evidence is distinct from concrete failed evidence;
- current Unity/Host blockers are classified, not silently absorbed as PR-019 feature scope.

## Review Checks

- **Solution direction: Pass.** The aggregate remains a pure evidence composer over existing readiness authorities.
- **Scope control: Pass.** PR-019 does not take ownership of PR-016/017/018 repairs, macOS, optional providers, arbitrary GUI compatibility, self-update authority or generic execution widening.
- **Technical feasibility: Pass.** Current Direct Codex transport already routes fixed provider-owned Git argv through `transport_git -> run_user_scoped_git`; a bounded non-network context probe can reuse the exact primitive.
- **Cause-aware evidence feasibility: Pass.** Current Direct Codex code retains only verified containment proof and clears failed proof state; preserving a separate sanitized last-probe disposition is the minimum necessary observation repair and does not grant authority.
- **Exact-candidate activation: Pass.** PR-015 already established the existing Windows venv exact-ref install -> SentinelX restart -> live Agent version/build read-back pattern. R2 reuses it instead of inventing Agent self-update.
- **Git authority separation: Pass.** The local user-scoped Git context probe proves process/context availability only; actual remote read/fetch/push remains E2E-receipt-owned.
- **Requirement R3-R5 semantics: Pass.** R2 explicitly distinguishes `verification_required / Unverified` from `baseline_blocker / NotReady` using cause-aware evidence.
- **Behavioral verification: Pass.** Ready cannot be produced from unit tests or capability booleans alone; exact candidate, live Host projection, real Direct Codex remote E2E, Unity workload and terminal closure are all required.
- **Security boundary: Pass.** No generic Git argv, caller environment, Host-policy mutation, permission widening, credential exposure, AppContainer escape or Job breakaway is authorized.
- **UX Contract: NotApplicable.**
- **Visual Fidelity: NotApplicable.**
- **Concurrent PR-017: Pass with reconciliation guard.** PR-017 changes mutation/policy internals but does not currently modify `handlers/basic.py` or `handlers/direct_codex.py`; PR-019 must not import unmerged PR-017 product code merely to make baseline green.
- **Concurrent PR-018: Pass with evidence-only guard.** PR-018 currently contains Task/evidence artifacts and remains independently owned. Its live Host/Unity findings may make S03 Unverified/NotReady but do not expand PR-019 implementation scope.
- **Concurrent PR-016: Pass.** Current PR-016 contains no product-code overlap with S01/S02.
- **Transport consistency: Pass.** PR #19 remains open/draft on the original branch over canonical main.

## R1 Finding Closure

~~~yaml
PR019ExactCandidateHostActivationMissing:
  status: closed
  evidence: Plan R2 S03.A/B freezes exact candidate and reuses exact-ref Windows install/restart/live-version readback with rollback identity verification.

DirectCodexTransportGitReadinessAuthorityMismatch:
  status: closed
  evidence: Plan R2 B5/S01 binds local readiness to actual run_user_scoped_git primitive; remote publication is separately E2E-owned.

UnverifiedVsNotReadyClassificationCollapsed:
  status: closed
  evidence: Plan R2 freezes not_attempted/stale/missing -> Unverified and attempted concrete failure/required-policy-disabled -> NotReady.
~~~

## Mandatory Implementation Guards

1. Preserve PR #19 Task/branch/PR transport identity for every Slice.
2. Before each Slice, re-read current PR-019 head, canonical main, exact Plan R2, this Slice Set and relevant overlapping open PRs.
3. Any semantic Plan/Requirement/transport drift invalidates the current Slice admission.
4. Do not cherry-pick or absorb unmerged PR-017/PR-018 product changes merely to satisfy the Stable Baseline.
5. S01 may add only the minimum sanitized Direct Codex readiness observation needed to distinguish `not_attempted / failed / verified`; it must not add a second authorization state machine.
6. The user-scoped Git context probe must be fixed/provider-owned, non-network, non-mutating, bounded and credential-non-projecting.
7. Local Git-context success MUST NOT be interpreted as GitHub remote publication success.
8. S02 must preserve every existing feature ID/meaning and must not make generic `host_runtime.git_execution_context_v1` an accidental Direct Codex prerequisite.
9. S03 must freeze the exact product candidate before live activation and reject live evidence from any other installed build.
10. S03 may pause at the existing external/operator exact-ref activation boundary; no self-update bypass is authorized.
11. A current Host/Unity concrete failure is evidence for `NotReady`, not authority for PR-019 to repair the owning subsystem.
12. Missing/stale/not-yet-attempted required evidence is `verification_required / Unverified`, not a defect claim.
13. Planning-time GitHub connector writes never satisfy the real Direct Codex E2E requirement.
14. One explicit `#开发执行 PR-019-stable-baseline-stabilization-exit-gate-v1` completes at most one Slice.
15. No Stabilization Exit claim without exact candidate + live Ready projection + remote E2E + Unity proof + terminal closure + durable exit receipt.

## Slice Compilation

Compile exactly:

1. **S01 — Direct Codex cause-aware transport-context readiness + Stable Baseline composer.**
2. **S02 — Capabilities integration + affected security/regression coverage.**
3. **S03 — Exact product candidate freeze/activation + live Stable Baseline + PR-019 remote E2E + Unity evidence + stabilization-exit evidence.**

Dependencies are linear: `S01 -> S02 -> S03`.

## Gate Result

~~~yaml
decision: Approved
blocking_findings: []
plan_approved: true_after_slice_set_readback
implementation_authorized: true_after_slice_set_readback
next_stage: implementation
current_slice_after_transition: S01
canonical_next_action: "#开发执行 PR-019-stable-baseline-stabilization-exit-gate-v1"
~~~

No SentinelX product code, Host policy, installed Agent, PR-017/PR-018 state, or canonical main is modified by this review.
