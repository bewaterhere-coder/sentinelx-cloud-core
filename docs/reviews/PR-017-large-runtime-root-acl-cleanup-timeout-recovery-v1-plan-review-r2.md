# PR-017 — Large Runtime Root ACL Cleanup Timeout & Recovery V1 — Plan Review R2

## Review State

```yaml
task_id: PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1
review_target: plan
requirement_revision: 1
requirement_blob_sha: c69f8872d76c7e2ca9de2b7795f0e27593a1c60f
plan_revision: 2
plan_blob_sha: 350b3c07778f5a6f5bd1eb78bf50e375fde8a94e
reviewed_task_head: 4c6bcfad78ed6c0f9e14e71921af558a4023419d
result: Rejected
runtime:
  devforge_main: 15f6e62263931531ab9a2298766fee43611afcbc
  review_contract_version: "1.3"
  review_contract_blob_sha: e8fe92cf1e98c3f7eb5bd60277bde8b42b381df7
  slicing_contract_version: "1.1"
  slicing_contract_blob_sha: d173ce7aa909def855b4fe3899e9a3da54b6a330
  artifact_state_transition_contract_version: "1.1"
  artifact_state_transition_contract_blob_sha: 4af7d9b41313f43bf4cc1fb3ab7927de722718ed
next_gate: plan_review_rejected
next_expected_actor: planner
```

## Decision

**Rejected.**

Plan R2 has the correct high-level direction: preserve PR-017 S01/S02 completion evidence, consume PR-018 only as the Unity/AppContainer compatibility dependency, keep the canonical PR-017 transport, and replay only PR-017-owned S03 / R8.3.

The Plan cannot enter Implementation because its frozen integration payload is not actually a production-only payload. It freezes exact PR-018 candidate blobs that still contain S01 diagnostic-only surfaces. Importing them verbatim would copy PR-018/S01-specific behavior into PR-017 even though PR-017 does not need or own that diagnostic path.

This is a Plan-scope correction. Requirement Revision 1 remains valid and no Requirement semantic change is required.

## Review Checks

### Solution direction — PASS

The combined-candidate approach correctly resolves the prior ownership boundary:

```text
PR-017 completed S01/S02
+ verified PR-018 compatibility production semantics
→ PR-017-owned S03 replay
```

This preserves R8.3 rather than weakening it.

### Requirement traceability — PASS

The revised S03 still observes the real Requirement behavior:

- scoped Python remains functional;
- real Unity 6000.6.4f1 initializes through the scoped boundary;
- cleanup completes under the bounded timeout;
- scope reaches terminal;
- exact AppContainer SID is absent after terminalization;
- PR-011 / PR-012 / Job / firewall / audit semantics remain verified.

### S01/S02 preservation — PASS

Fresh repository reconciliation proves the PR-017 current head has no product/test drift relative to the PR-018 stacked base; only PR-017 documentation moved after that base.

Therefore S01 and S02 completion receipts MAY remain canonical and MUST NOT be replayed merely because S03 consumes the compatibility dependency.

The combined S03 still must run the affected regression set, so product-level invalidation will be detected before completion.

### Cross-Task transport separation — PASS

Plan R2 correctly forbids:

- merging the PR-018 branch wholesale;
- importing PR-018 docs/checkpoints/receipts/task state;
- importing the PR-018-only workflow;
- advancing PR-018 from a PR-017 Slice;
- treating isolated PR-018 S03 proof as PR-017 S03 completion evidence.

### Integration payload minimality — FAIL

Finding: `PR018DiagnosticSeamIncludedInIntegrationPayload`.

The frozen 12-blob payload includes:

```text
src/sentinelx_core/handlers/scoped_script.py
candidate blob: 1b8c05b14658f3ffb71e08fbd23851391132b5cf
```

A direct diff against the current PR-017 blob proves the entire semantic delta is PR-018/S01 paired-diagnostic behavior:

- consumes `PR018_S01_PAIRED_DIAGNOSTIC`;
- hard-binds to Task `PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1`;
- hard-binds to Slice `S01`;
- creates `.pr018-s01-paired` markers;
- invokes `enable_pr018_paired_session_read()`;
- emits `SENTINELX_PR018_PAIRED_DIAGNOSTIC`;
- reads back `pr018_paired_session_absence()`.

None of those behaviors is required by PR-017 S03, PR-018 S02 production compatibility, or the default-off generic Session-0 lifecycle.

The only non-marker syntactic change in that diff is `dict(payload.get("env") or {})`, which exists to permit removal of the diagnostic env marker before the child environment is materialized.

Therefore this file is not a necessary PR-017 integration payload member and must not be projected.

### Mixed production/diagnostic sandbox blob — FAIL

Finding: `PR018DiagnosticMethodsEmbeddedInWindowsSandboxBlob`.

The frozen blob:

```text
src/sentinelx_core/windows_mutation_sandbox.py
candidate blob: c5a9ae35b8324adffc31ce9ed6cbbf9ebe172bde
```

contains both the required production compatibility implementation and these PR-018/S01-only methods:

```text
enable_pr018_paired_session_read(...)
pr018_paired_session_absence(...)
```

Those methods are exact-lineage diagnostic helpers for the already-completed PR-018 S01 discriminator. They are not part of the generic default-off Session-0 compatibility contract consumed by PR-017.

Because production and diagnostic code are mixed in one candidate blob, the current `exact_12_blob_projection` rule is too coarse. Implementation MUST NOT silently import the whole blob and MUST NOT independently invent which lines to strip.

Plan remediation must freeze a deterministic production-subset integration artifact.

### Test payload — PASS WITH REMEDIATION NOTE

The PR-018 candidate's Windows sandbox tests include production lifecycle coverage needed by the combined candidate. One test remains named:

```text
test_pr018_session_masks_are_exact_frozen_read_only_values
```

Its semantics are generic production invariants, not S01 diagnostic behavior. This naming is not independently blocking, but Plan remediation SHOULD rename or rebind it to a non-Task-specific production invariant when compiling the production subset.

## Required Plan R3 Corrections

Plan remediation MUST keep Requirement Revision 1 and canonical PR #17 unchanged, then make the minimum integration correction:

1. Replace `exact_12_blob_projection` with a **production-subset integration** rule.
2. Remove `src/sentinelx_core/handlers/scoped_script.py` from the integration payload entirely; preserve the current PR-017 blob `4580475ba9bd8ba5301b579ee11a584abbd75d4b`.
3. For `windows_mutation_sandbox.py`, define a deterministic integration source that contains the PR-018 production compatibility changes but excludes:
   - `enable_pr018_paired_session_read(...)`;
   - `pr018_paired_session_absence(...)`;
   - any other PR-018/S01-only paired-diagnostic surface.
4. Do not let the implementation host infer the strip operation from prose. Persist the exact production-subset patch/blob identity or a mechanically reproducible source definition during Plan remediation.
5. Preserve all other required generic production semantics:
   - Host-owned `runtime_session_object_read_enabled`, default false;
   - policy digest/readiness participation;
   - durable `SessionObjectReadBinding`;
   - persist-before-grant;
   - exact `0x00020103 / 0x00020041` masks;
   - restart-safe identity reacquisition;
   - dual exact-SID absence before marker clear;
   - fail-closed terminalization;
   - verification trusted-root behavior;
   - runtime-root ACL timeout/recovery from PR-017.
6. Preserve S01 and S02 as completed; do not replay them.
7. Recompile only S03 after the corrected Plan is approved.
8. S03 must still create fresh PR-017-owned combined-candidate evidence. PR-018 receipts remain dependency evidence only.

## Rejected Findings

```yaml
findings:
  - id: PR018DiagnosticSeamIncludedInIntegrationPayload
    severity: blocking
    scope: plan
    affected_file: src/sentinelx_core/handlers/scoped_script.py
    correction: exclude the candidate blob and preserve the PR-017 version

  - id: PR018DiagnosticMethodsEmbeddedInWindowsSandboxBlob
    severity: blocking
    scope: plan
    affected_file: src/sentinelx_core/windows_mutation_sandbox.py
    correction: freeze a deterministic production-subset integration source that excludes PR-018/S01 paired-diagnostic methods
```

## Gate Result

```yaml
decision: Rejected
requirement_revision: 1
requirement_change_required: false
plan_revision_reviewed: 2
plan_approved: false
implementation_authorized: false
stage_after: plan_review_rejected
current_slice: S03
s01_state: completed
s02_state: completed
s03_r1_state: blocked_historical
r2_slice_set_compiled: false
canonical_next_action: "#开发计划修复 PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1"
```

No product code, tests, Host policy, PR-018 state, PR-017 S01/S02 evidence, or canonical main is mutated by this review.
