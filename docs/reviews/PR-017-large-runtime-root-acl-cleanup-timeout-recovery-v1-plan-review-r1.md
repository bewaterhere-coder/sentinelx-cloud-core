# PR-017 — Plan Review R1

## Review State

```yaml
task_id: PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1
review_target: plan
requirement_revision: 1
requirement_blob_sha: f48f43c20c51f71ea6707af2d2386aad11bce51c
plan_revision: 1
plan_blob_sha: 3d5cb55362a4b97ee157caed6d3539df02acb0fc
reviewed_task_head: 55f1a2a741442b34d3f8a45b1ecc322fb281fc38
result: Approved
runtime:
  devforge_version: "2.88.0"
  devforge_revision: 602afe2cf30feac3032a0095b55ac4cb1a7cdab6
  provenance: canonical_release_and_main_readback
next_gate: implementation
next_expected_actor: implementer
```

## Decision

**Approved.**

Plan Revision 1 addresses the observed large-runtime-root Windows AppContainer ACL timeout at the existing `WindowsMutationSandbox` boundary. It does not redesign `execute_scoped`, create a second executor, weaken AppContainer containment or bypass the current two-phase scope lifecycle.

The Plan is approved with mandatory implementation-entry guards for current concurrent work and one explicit residual-authority readback requirement compiled into the Slice Set.

## Review Checks

- **Root cause / solution direction: Pass.** The fixed `timeout=20` is the exact observed failure seam. A provider-owned bounded runtime ACL timeout is the smallest policy-level correction.
- **Provider authority: Pass.** The timeout remains Host configuration only; callers cannot select the timeout or runtime roots.
- **Grant + cleanup symmetry: Pass.** Applying the bound to both runtime-root grant and removal avoids fixing only the terminal path while leaving grant vulnerable to the same fixed ceiling.
- **Timeout classification: Pass.** `TimeoutExpired` must become deterministic sandbox-domain evidence rather than a generic `internal_error`.
- **Partial-grant ambiguity: Pass.** The Plan correctly recognizes that a failed/timed-out grant cannot be treated as proof that no ACL authority exists. The attempted root must be compensation-cleanup eligible even before a successful-grant list append.
- **Lifecycle recovery: Pass.** Existing `MutationScopeStore.terminalize_scope()` already provides `revoked -> retry cleanup -> terminal`; no new lifecycle state is justified.
- **Residual-authority closure: Pass with mandatory implementation guard.** Normal runtime-root removal and compensation removal must read back the exact root and prove the scope AppContainer SID is absent before closure can report no residual authority. An `icacls` zero exit code alone is not sufficient evidence.
- **Policy drift: Pass.** The timeout materially affects mutation execution and may participate in the provider policy/placement digest. Existing stale-policy cleanup semantics must remain usable for old scopes.
- **Backward compatibility: Pass.** Default 20 seconds preserves current behavior until an operator explicitly opts into a larger bounded value.
- **Verification-toolchain isolation: Pass.** PR-011 `/T /C` verification-toolchain ACL behavior is not widened by default; helper refactoring must retain its existing timeout semantics unless separately justified.
- **Real Host acceptance: Pass.** Unity 6.6 is a valid physical large-runtime proof, but is not made a permanent SentinelX product dependency.
- **PR-015 concurrency: Pass with reconciliation guard.** PR-015 currently modifies `src/sentinelx_core/policy.py` and `config.example.windows.yaml`. PR-017 S01 must re-read/rebase/reconcile those files before mutation if PR-015 moves or merges; Direct Codex policy semantics must not be overwritten.
- **PR-016 concurrency: Pass with serialization guard.** PR-016 S01 is authorized and plans changes to `src/sentinelx_core/windows_mutation_sandbox.py`, although its current PR head has not yet mutated that product file. PR-017 and PR-016 must not concurrently mutate this file. Any PR-016 product-code movement requires explicit reconciliation before PR-017 continues.
- **Slice decomposition: Pass.** `S01 -> S02 -> S03` separates policy/error semantics, authority recovery, and physical acceptance.

## Mandatory Implementation Guards

1. Before every PR-017 Slice mutation, re-read canonical `main`, PR-017 head, PR-015 head/state and PR-016 head/state.
2. If PR-015 has changed/merged `policy.py` or `config.example.windows.yaml` since this review, reconcile those changes before PR-017 mutation.
3. If PR-016 has introduced product changes in `windows_mutation_sandbox.py`, stop and reconcile/serialize; do not independently implement over a stale sandbox baseline.
4. Runtime ACL cleanup success requires exact-root SID readback. No readback -> no residual-authority closure -> no terminal success claim.
5. Grant failure/timing ambiguity must attempt compensation on the exact attempted runtime root; failed compensation remains fail-closed.
6. Each explicit `#开发执行` may complete at most one Slice.

## Slice Compilation

Compile exactly:

1. **S01 — Policy & ACL operation contract.** Add bounded Host policy, policy digest participation, deterministic timeout classification, configured timeout propagation, exact-root removal readback, and focused unit tests.
2. **S02 — Grant compensation & lifecycle recovery.** Close partial-grant ambiguity, prove compensation/readback, preserve revoked state on ambiguity, and prove terminalization retry.
3. **S03 — Physical large-runtime proof & regression closure.** Run affected security regressions and real Windows scoped Python/PowerShell/Unity proof with exact SID absence after terminalization.

## Gate Result

```yaml
decision: Approved
blocking_findings: []
plan_approved: true_after_slice_set_readback
implementation_authorized: true_after_slice_set_readback
next_stage: implementation
current_slice_after_transition: S01
canonical_next_action: "#开发执行 PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1"
```

No SentinelX product code or Host policy is modified by this review.
