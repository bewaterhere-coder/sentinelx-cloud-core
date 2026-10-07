# PR-019 — SentinelX Stable Baseline & Stabilization Exit Gate V1 — Plan Review R1

## Review State

~~~yaml
task_id: PR-019-stable-baseline-stabilization-exit-gate-v1
review_target: plan
requirement_revision: 1
requirement_blob_sha: 8c82674c992c993d4a5f3f2b09ec9ab3dabe34d3
plan_revision: 1
plan_blob_sha: 9526340ce709108b53fd2336aa6ec623d5f3e721
reviewed_task_head: b437e204abf45c38bbda0975616f98e734fc14bc
result: Rejected
finding_classification: plan_local
runtime:
  devforge_version: "2.94.0"
  devforge_revision: 4bbd40c3ce9805b759595827444b7b36c0038708
  review_contract: "1.3"
  slicing_contract: "1.1"
repository_reality:
  canonical_main: 1028030b33f0ea792a884491a431fffe566f6aa5
  canonical_pr: 19
  canonical_branch: task/stable-baseline-stabilization-exit-gate-v1
next_gate: plan_review_rejected
next_expected_actor: planner
~~~

## Decision

**Rejected.**

Requirement Revision 1 is Ready and the finite-baseline direction is accepted. Plan Revision 1 has three P0 implementation-shaping defects that would make the Stabilization Exit Gate either unverifiable or semantically incorrect.

No Requirement rewrite is required. All findings are plan-local.

## F1 — Exact-candidate Host activation/read-back is missing

PR-019 changes SentinelX Agent code, specifically the new Stable Baseline composer and the live `capabilities` projection. S03 then requires the current Host to return:

~~~text
host_runtime.stable_baseline_v1.status = Ready
~~~

and Acceptance requires the installed Agent version/build to be bound to the candidate.

Plan R1 does not define how the exact PR-019 candidate becomes the running Host Agent before that live read-back.

Repository execution through Direct Codex edits and tests an isolated checkout. It does not, by itself, prove that the SentinelX service handling the later `capabilities` request is running the same candidate commit.

Without a candidate activation boundary, S03 could:

- read the previously installed Agent, where the new feature does not exist; or
- read a different installed build and falsely associate that Host result with the PR-019 candidate.

### Required correction

Plan R2 must add an exact-candidate Host activation/verification boundary before live Stable Baseline read-back.

It must freeze:

1. how the exact PR-019 candidate artifact/commit is installed or activated on the Windows Host;
2. how the service/runtime is restarted or reloaded when required;
3. how the installed Agent version/build/candidate identity is read back and bound to PR-019;
4. how failure or identity mismatch fails closed;
5. how rollback/recovery preserves a known-good Host when candidate activation fails;
6. that connector-side GitHub mutation alone cannot satisfy this evidence;
7. that S03 only evaluates `host_runtime.stable_baseline_v1` after exact-candidate identity is proven.

Reuse an existing SentinelX exact-candidate activation pattern if one is already canonical; do not create a parallel deployment authority.

## F2 — B1 uses the wrong authority for Direct Codex transport Git readiness

Plan R1 makes this mandatory:

~~~text
host_runtime.git_execution_context_v1
available = true
operations contains fetch + push
~~~

and treats it as the Git readiness of the current Direct Codex transport.

Current repository reality does not support that equivalence.

The generic capability projection in `handlers/basic.py` derives `host_runtime.git_execution_context_v1.available` from:

~~~text
policy.authenticated_git_enabled
~~~

and projects `push` only when:

~~~text
policy.authenticated_git_allow_push
~~~

But the Direct Codex transport/persistence path calls `run_user_scoped_git` directly through `direct_codex_transport.transport_git`. `DirectCodexPolicy.missing_prerequisites()` does not currently require `authenticated_git_enabled`.

Therefore the Plan can classify the Host `NotReady` because the generic authenticated-Git feature is disabled even while the actual Direct Codex transport can successfully perform its fixed provider-owned Git operations.

That violates the Requirement's intent to classify readiness for the **current transport**, not an adjacent generic capability.

### Required correction

Plan R2 must bind Git readiness to the actual Direct Codex transport path.

Acceptable directions include either:

- define a provider-owned Direct Codex transport Git readiness/preflight projection that reuses the same `run_user_scoped_git` primitive and closed provider-owned transport semantics; or
- keep Git transport proof at the exact E2E receipt boundary and remove the unrelated generic `authenticated_git` feature from the live mandatory composer, if the resulting Requirement traceability remains complete.

Do not silently make generic `authenticated_git` policy mandatory for Direct Codex unless the Plan explicitly chooses and justifies a real provider-contract change and tests the migration/compatibility impact.

The final predicate must observe the path that actually performs canonical branch read/fetch/publish.

## F3 — Plan collapses “unverified” into “failed”, violating the Requirement taxonomy

Requirement R3-R5 explicitly distinguish:

~~~text
concrete mandatory failure
→ baseline_blocker
→ NotReady

mandatory evidence absent/stale/unproven
→ verification_required
→ Unverified
~~~

Plan R1 instead includes cases such as:

~~~text
Direct Codex unverified → NotReady
~~~

This is not valid for the current Direct Codex readiness model.

Current provider readiness can return an unverified state solely because physical containment has not yet been proven for the current process/lineage, for example:

~~~text
direct_codex_containment_unproven
direct_codex_real_sandbox_setup_unproven
~~~

Likewise the canonical repository firewall may be unverified because an effective mutation surface is still unproven rather than because a concrete unsafe condition has been observed.

Treating every `verified=false` or `available=false` as `NotReady` converts missing evidence into a defect and recreates the unbounded stabilization loop this Task exists to stop.

### Required correction

Plan R2 must freeze deterministic cause-aware classification.

At minimum it must distinguish:

- **verification_required / Unverified** — evidence absent, stale, not yet physically proven, or not yet bound to the current candidate/lineage;
- **baseline_blocker / NotReady** — explicit policy/config absence for a mandatory baseline function, concrete runtime/probe failure, concrete security/closure failure, concrete transport failure, or current Unity workload failure.

The mapping must be based on authoritative reason/evidence classes, not only on top-level booleans.

Required tests must include:

1. Direct Codex `containment_unproven` → `Unverified`, not `NotReady`;
2. failed real sandbox setup after an attempted proof → `NotReady`;
3. mandatory policy explicitly disabled → `NotReady`;
4. mandatory evidence missing/malformed without concrete failure → `Unverified`;
5. firewall unproven only because a mandatory provider proof is pending → `Unverified`;
6. firewall concrete uncovered/unsafe mutation class → `NotReady`;
7. current Unity evidence absent → `Unverified`;
8. current Unity concrete failure → `NotReady`.

## Accepted Plan R1 direction

The following design direction is approved and should be preserved in Plan R2:

- one finite `windows_dev_v1` baseline;
- `Ready` explicitly does not mean defect-free;
- one pure aggregate projection rather than a second low-level readiness authority;
- reuse of existing mutation, verification, firewall and Direct Codex physical evidence;
- no caller-writable Ready state;
- no automatic feature expansion from missing evidence;
- backlog findings do not block exit;
- one real DevForge Direct Codex E2E receipt remains required;
- Unity 6000.6.4f1 remains a bounded current-workload acceptance proof;
- PR-019 consumes but does not take ownership of PR-018 repairs;
- No Receipt, No Stabilization Exit.

## Requirement Traceability

~~~yaml
R1_single_aggregate_projection: pass
R2_reuse_physical_readiness: pass_with_F2_correction
R3_finite_blocking_taxonomy: pass_with_F3_correction
R4_unknown_not_feature_expansion: pass_with_F3_correction
R5_projection_semantics: fail_F3
R6_no_caller_authority_expansion: pass
R7_real_devforge_e2e_exit_proof: pass
R8_unity_acceptance_gate_not_feature_trigger: pass
R9_exit_receipt: pass_with_F1_exact_candidate_binding_required
R10_exit_semantics: pass
~~~

## Feasibility / Risk Review

- **Solution direction:** Pass.
- **Scope control:** Pass.
- **Technical feasibility:** Reject until F1/F2 are corrected.
- **Risk handling:** Reject until exact-candidate activation/rollback is frozen.
- **Behavioral verification:** Reject because current S03 cannot prove the live Host is the exact PR-019 candidate.
- **Requirement traceability:** Reject because R4/R5 are violated by boolean-only unverified classification.
- **UX Contract:** NotApplicable.
- **Visual Fidelity:** NotApplicable.
- **Concurrent PR overlap:** No current open PR directly changes `handlers/basic.py`; PR-013 changes `handlers/__init__.py`, PR-017 changes adjacent mutation/readiness behavior. Existing reconciliation guard remains sufficient.

## Gate Result

~~~yaml
decision: Rejected
blocking_findings:
  - PR019ExactCandidateHostActivationMissing
  - DirectCodexTransportGitReadinessAuthorityMismatch
  - UnverifiedVsNotReadyClassificationCollapsed
plan_approved: false
implementation_authorized: false
execution_slice_set: not_compiled
next_stage: plan_review_rejected
next_expected_actor: planner
canonical_next_action: "#开发计划修复 PR-019-stable-baseline-stabilization-exit-gate-v1"
~~~

No SentinelX product code, Host policy, installed Agent, PR-018 state or canonical main is modified by this review.
