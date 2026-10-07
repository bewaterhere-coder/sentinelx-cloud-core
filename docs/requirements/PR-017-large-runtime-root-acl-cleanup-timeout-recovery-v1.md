# PR-017 — SentinelX Large Runtime Root ACL Cleanup Timeout & Recovery V1

## State — Requirement Revision 1

```yaml
project_id: sentinelx-cloud-core
task_id: PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1
title: SentinelX Large Runtime Root ACL Cleanup Timeout & Recovery V1
requirement_revision: 1
development:
  stage: plan_review_rejected
  gates:
    requirement_ready: true
    plan_approved: false
    acceptance_approved: false
    completion_verified: false
  plan_revision: 4
  implementation_authorized: false
  next_expected_actor: planner
  blocking_findings:
    - Plan Review R4 verified the production-subset manifest, all CAS guards, derived blob identities, diagnostic-seam exclusion, scoped_script.py preservation, S01/S02 historical completion evidence, and S03/R8.3 traceability.
    - Plan Review R4 rejected only StalePlanR3AuthorityReferences: two current authority statements still bind execution/slice compilation to already-rejected Plan R3. Plan remediation must rebind those statements to the current Plan revision without changing technical semantics.
    - Requirement Revision 1 remains unchanged. S01 and S02 remain canonically completed historical evidence and must not be replayed. No product mutation or Slice recompilation is authorized until the corrected Plan is reviewed and approved.
  current_slice: S03
  current_slice_state: blocked
  authorization:
    mode: legacy_command_scoped
  completed_slices:
    - S01
    - S02
transport:
  type: github-pr
  pr_number: 17
  branch: task/large-runtime-root-acl-cleanup-timeout-recovery-v1
  base_branch: main
artifacts:
  plan: docs/plans/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-plan.md
  latest_plan_review: docs/reviews/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-plan-review-r4.md
  latest_plan_review_transition_receipt: docs/reviews/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-plan-review-r4-transition-receipt.yaml
  latest_plan_revision_checkpoint: docs/checkpoints/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-plan-revision-r2-pr018-integration-20261008.yaml
  latest_plan_revision_transition_receipt: docs/reviews/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-plan-revision-r2-transition-receipt.yaml
  latest_plan_remediation_checkpoint: docs/checkpoints/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-plan-remediation-r3-20261008.yaml
  latest_plan_remediation_transition_receipt: docs/reviews/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-plan-remediation-r3-transition-receipt.yaml
  latest_plan_remediation_checkpoint_r4: docs/checkpoints/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-plan-remediation-r4-20261008.yaml
  latest_plan_remediation_transition_receipt_r4: docs/reviews/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-plan-remediation-r4-transition-receipt.yaml
  execution_slice_set: docs/execution/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-slices.yaml
  latest_slice_checkpoint: docs/checkpoints/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-s03-blocked-unity-dll-initialization-20261007.yaml
  latest_slice_completion_receipt: docs/reviews/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-s02-repair-completion-receipt-r4.yaml
  latest_slice_invalidation: docs/reviews/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-s02-live-invalidation-r3.md
  latest_s03_blocker_review: docs/reviews/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-s03-unity-appcontainer-compatibility-blocker-r1.md
  latest_acceptance_attempt: docs/reviews/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-acceptance-r1-blocked-incomplete-slices-20261008.yaml
related_tasks:
  predecessor:
    - PR-012-execute-scoped-explicit-execution-profile-v1
    - PR-011-scoped-verification-toolchain-dependency-capsule-v1
  integration_dependency:
    - PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1@73a52013055a8b3bb70b319a0ed7b7ba832ae0c9
  downstream_consumer:
    - DemonTD/CLIENT-CODE-ARCHITECTURE-BASELINE-V1/C01
```

## Problem

SentinelX Windows scoped mutation currently grants transient AppContainer read/execute authority to each configured `mutation_execution.runtime_read_roots`.

The current implementation uses one helper for runtime-root ACL mutation:

```python
def _run_icacls(args: list[str]) -> None:
    subprocess.run(
        ["icacls", *args],
        ...,
        timeout=20,
    )
```

A real DemonTD Unity 6.6 verification exposed that the fixed 20 second ceiling is too small for a large immutable runtime tree.

Current Host evidence:

```text
execute_scoped + python3
→ PASS

runtime_read_roots includes:
  C:\ProgramData\SentinelX\.venv
  C:\Python314
  C:\Windows\System32\WindowsPowerShell\v1.0
  C:\Program Files\Unity\Hub\Editor\6000.6.4f1

PowerShell/AppContainer initialization blocker
→ no longer the primary failure

terminal runtime ACL cleanup
→ icacls <Unity root> /remove:g <AppContainer SID>
→ timeout after 20 seconds
→ scope remains revoked
```

The manually observed failed scope correctly stayed fail-closed in `revoked` state rather than being published as `terminal`.

The residual SID was then cleaned manually by the operator.

## Repository Reality

Canonical baseline:

```text
main@018b78ca20984176d53fbe90039dc795a7f2742f
```

Relevant current behavior:

- `MutationExecutionPolicy` has no provider-owned ACL operation timeout.
- `_run_icacls()` hard-codes `timeout=20`.
- `_grant_runtime_read()` grants `(OI)(CI)(RX)` on the exact configured runtime root.
- `_remove_runtime_read()` removes the exact AppContainer SID from the runtime root.
- `WindowsMutationSandbox.activate()` tracks successfully granted runtime roots for rollback.
- a runtime-root grant that times out before it is appended to the successfully-granted list can be ambiguous: Windows may already have partially applied/propagated ACL changes even though the Python call raised before the root was recorded for cleanup.
- `MutationScopeStore.terminalize_scope()` already implements two-phase terminalization:
  `active/provisioned -> revoked -> OS cleanup -> terminal`.
- cleanup failure already leaves the scope durably `revoked`.
- retrying terminalization from `revoked` is already supported by the existing lifecycle and must be preserved.

This Task must repair timeout/recovery semantics without weakening AppContainer containment.

## Goal

Make large immutable runtime roots usable by scoped mutation while preserving fail-closed authority closure:

```text
provider-owned bounded ACL timeout
+ exact runtime-root authority
+ partial-grant compensation
+ revoked-on-ambiguous-cleanup
+ deterministic terminalization retry
→ large runtime execution without false terminal success
```

## Required Behavior

### R1 — Provider-owned runtime ACL operation timeout

Add a Host-owned policy value for runtime-root ACL operations.

Canonical requirement:

```yaml
mutation_execution:
  runtime_acl_timeout_seconds: <bounded integer>
```

Rules:

- default preserves current behavior unless explicitly configured;
- value is Host policy only, never caller-controlled;
- value must be bounded;
- invalid/non-integer/out-of-range values fail configuration load;
- callers cannot override it in `script_run`, `execute_scoped`, lineage, environment, or verification payloads.

Recommended V1 bounds:

```text
minimum: 5 seconds
maximum: 600 seconds
default: 20 seconds
```

The exact bounds may be adjusted during Plan Review only with evidence.

### R2 — Runtime-root grant and cleanup use the bounded policy

The configured timeout must apply to both:

- runtime-root ACL grant;
- runtime-root ACL removal.

Do not silently reuse a larger timeout for unrelated executors, network operations or arbitrary subprocesses.

Verification-toolchain ACL behavior introduced by PR-011 remains unchanged unless a concrete shared-helper compatibility need is demonstrated.

### R3 — Deterministic timeout classification

`subprocess.TimeoutExpired` from runtime-root `icacls` must not escape as generic `internal_error`.

The failure must be translated into a stable sandbox-domain error with:

- operation class: grant or cleanup;
- exact runtime root;
- configured timeout;
- no credential/secret leakage.

Cleanup timeout must be classified as residual-authority ambiguity, because SentinelX cannot prove that the AppContainer SID has been fully revoked.

### R4 — Partial grant must compensate or remain fail-closed

A runtime ACL grant may time out after Windows has partially applied or propagated the ACE.

Therefore, if grant fails or times out:

1. SentinelX must attempt compensating removal of the exact scope AppContainer SID from that same runtime root;
2. it must not assume "grant raised" means "no authority exists";
3. if compensation succeeds and closure is provable, the activation may fail normally with no residual authority;
4. if compensation cannot be proved, the scope must remain revoked / residual authority must be surfaced;
5. no unrestricted retry or alternate executor is allowed.

The exact root being attempted must be cleanup-eligible even if the grant operation did not return success.

### R5 — Preserve two-phase terminalization and retry recovery

Do not add a new lifecycle state.

Existing semantics remain authoritative:

```text
provisioned/active
      ↓ revoke admission
revoked
      ↓ authoritative OS cleanup
terminal
```

If cleanup times out or fails:

- the scope must remain `revoked`;
- no successful FINISH/terminal closure may be fabricated;
- a later explicit terminalization retry may complete cleanup;
- only authoritative residual-authority readback may permit `terminal`.

### R6 — Policy drift must be observable

The new runtime ACL timeout affects mutation execution semantics and must participate in the provider-owned policy identity/digest used for mutation placement/scope admission.

Changing the timeout must therefore be detectable as Host policy drift for future admission.

Cleanup of already-issued scopes must remain possible under the existing stale-policy cleanup rule.

### R7 — No security-boundary widening

This Task must not:

- enable `exec`;
- enable `operator_unrestricted`;
- disable AppContainer;
- broaden `protected_roots`;
- grant `C:\Windows` or `C:\Program Files` wholesale unless already explicitly configured by the operator;
- add caller-selected runtime roots;
- create a second executor;
- create a second scope store;
- treat timeout as success;
- mark a revoked scope terminal without residual-authority closure.

### R8 — Large-runtime real Windows proof

Acceptance must include a real Windows proof with a runtime root large enough to exceed or meaningfully exercise the previous 20 second cleanup boundary.

The current target is:

```text
C:\Program Files\Unity\Hub\Editor\6000.6.4f1
```

or a bounded equivalent fixture if the real Unity installation cannot be used during automated acceptance.

Real Host evidence must prove:

1. scoped Python remains functional;
2. PowerShell scoped execution remains fail-closed/functional according to the configured runtime roots;
3. Unity runtime process can be launched through the scoped boundary far enough to perform the intended batch probe;
4. cleanup completes under the configured bounded timeout;
5. scope reaches `terminal`;
6. the exact AppContainer SID is absent from the runtime root after terminalization.

### R9 — Regression compatibility

Preserve:

- `host_mutation_sandbox_v1` readiness;
- PR-011 Node/npm scoped verification;
- PR-012 explicit execution-profile contract;
- exact workspace ACL isolation;
- Job/no-breakaway containment;
- canonical repository firewall semantics;
- audit START/SPAWN/FINISH ordering;
- revoked-on-cleanup-failure behavior.

## Non-Goals

This Task does not:

- redesign `execute_scoped`;
- redesign the mutation scope state machine;
- make Unity a built-in SentinelX verification profile;
- solve general Windows application compatibility under AppContainer;
- alter DemonTD code;
- add a generic shell fallback;
- pre-authorize persistent AppContainer access to all runtime roots;
- optimize all ACL operations in SentinelX.

## Acceptance Criteria

The Task is acceptable only when all are evidenced:

1. default runtime ACL timeout remains backward compatible;
2. valid configured timeout is accepted;
3. invalid/out-of-range timeout fails config load;
4. timeout participates in provider policy digest / drift detection;
5. runtime-root grant uses the configured timeout;
6. runtime-root cleanup uses the configured timeout;
7. `TimeoutExpired` becomes deterministic sandbox-domain evidence, not generic internal error;
8. simulated partial-grant timeout triggers compensating cleanup for the exact attempted root;
9. compensation failure remains fail-closed with residual authority/revoked scope;
10. terminal cleanup timeout leaves the scope `revoked`;
11. a later terminalization retry can reach `terminal` after real cleanup succeeds;
12. exact AppContainer SID is absent after successful terminalization;
13. existing Windows sandbox tests remain green;
14. PR-011 verification regressions remain green;
15. real Windows large-runtime-root proof passes;
16. no unrestricted or caller-controlled fallback is introduced.

## Requirement Readiness

```yaml
requirement_ready: true
material_product_decision_pending: false
requirement_artifact_bundle: not_required
ui_semantic_resolution: not_applicable
visual_fidelity: not_applicable
current_task_p0_dependencies: []
```
