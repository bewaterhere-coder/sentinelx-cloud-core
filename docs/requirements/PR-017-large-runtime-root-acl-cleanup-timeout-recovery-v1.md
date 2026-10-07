# PR-017 — SentinelX Large Runtime Root ACL Cleanup Timeout & Recovery V1

## State — Requirement Revision 1

```yaml
project_id: sentinelx-cloud-core
task_id: PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1
title: SentinelX Large Runtime Root ACL Cleanup Timeout & Recovery V1
requirement_revision: 1
development:
  stage: done
  gates:
    requirement_ready: true
    plan_approved: true
    acceptance_approved: true
    completion_verified: true
  plan_revision: 5
  acceptance_revision: 3
  completion_revision: 1
  implementation_authorized: false
  finalization:
    ready_for_merge: false
    canonical_state_verified: true
    plan_execution_state_verified: true
    evidence_verified: true
    transport_preconditions_verified: true
    integration_verified: true
    integration_ref: f72ac8bfe643cd9fbdea231e4a69f9e88a0595e9
    merge_pending: false
  next_expected_actor: null
  acceptance_disposition: approved_r3
  execution_disposition: completion_r1_verified
  blocking_findings: []
  repair_evidence:
    - Fixing R1 preserved exact product candidate f9e07da9cc37f6e882c3258280869b415cafcb5c and did not replay S03 or Unity.
    - SentinelX service generation reset preserved agent 0.24.1.dev473+gf9e07da9c and did not mutate Host config or permissions.
    - Current host readback twice reports scoped_verification_node_npm_v1 available=true / verified=true with Node, npm, DNS deny, HTTP deny, protected-root deny, terminal cleanup and transient-toolchain-authority cleanup all passing.
    - The prior inconsistent state is attributed to process-generation readiness cache persistence; the original transient HandlerError trigger remains unknown and Acceptance must independently reverify current behavior.
  current_slice: S03
  current_slice_state: completed
  authorization:
    mode: legacy_command_scoped
  completed_slices: [S03]
  historical_completed_evidence:
    - S01
    - S02
transport:
  type: github-pr
  pr_number: 17
  branch: task/large-runtime-root-acl-cleanup-timeout-recovery-v1
  base_branch: main
artifacts:
  plan: docs/plans/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-plan.md
  plan_blob_sha: 25398f342e5f032d8c838f33ee941562c987d15c
  latest_plan_review: docs/reviews/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-plan-review-r5.md
  latest_plan_review_transition_receipt: docs/reviews/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-plan-review-r5-transition-receipt.yaml
  latest_plan_remediation_checkpoint: docs/checkpoints/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-plan-remediation-r5-20261008.yaml
  latest_plan_remediation_transition_receipt: docs/reviews/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-plan-remediation-r5-transition-receipt.yaml
  execution_slice_set: docs/execution/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-slices.yaml
  execution_slice_set_plan_revision: 5
  execution_slice_set_blob_sha: "493f54282df837f3923aa0c986b01b46329ca2ec"
  latest_slice_checkpoint: docs/checkpoints/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-s03-completion-20261008.yaml
  latest_slice_checkpoint_blob_sha: "68e213815b82f9cf99f8cc607034815ae7f29dc6"
  latest_slice_completion_receipt: docs/reviews/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-s03-completion-receipt.yaml
  latest_slice_completion_receipt_blob_sha: "aef10dfe56da8db7ae09aa4d47c29caa1e57b66f"
  latest_integrated_candidate: "f9e07da9cc37f6e882c3258280869b415cafcb5c"
  prior_s03_blocker_checkpoint: docs/checkpoints/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-s03-blocked-exact-candidate-host-activation-unavailable-20261008.yaml
  prior_acceptance_attempt: docs/reviews/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-acceptance-r1-blocked-incomplete-slices-20261008.yaml
  latest_acceptance: docs/reviews/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-acceptance-r3.yaml
  latest_acceptance_blob_sha: 4e22d9537ae9e742c19ee3639c674ed8121995bc
  latest_acceptance_transition_receipt: docs/reviews/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-acceptance-r3-transition-receipt.yaml
  latest_acceptance_transition_receipt_blob_sha: abcd48115684955aacc0d6b79fbb41e16809e9ad
  latest_fixing_execution_checkpoint: docs/checkpoints/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-fixing-r1-readiness-restored-20261008.yaml
  latest_fixing_execution_checkpoint_blob_sha: 3c0119777435813278f111839fcd9f4ff743d80e
  latest_fixing_transition_receipt: docs/reviews/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-fixing-r1-to-acceptance-transition-receipt.yaml
  latest_fixing_transition_receipt_blob_sha: da74adac606ba764f8914a4cd8135af22ac0f0ea
  completion_finalization: docs/reviews/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-completion-finalization-r1.yaml
  completion_finalization_blob_sha: 319aeed703515d3339bff78323f83a35bbf40663
  integration_receipt: docs/reviews/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-integration-receipt-r1.yaml
  integration_receipt_blob_sha: ae7a93de6d4ea782f350f55d40779dc3f2084fd0
  completion_review: docs/reviews/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-completion-r1.md
  completion_review_blob_sha: 66863506fbbc0a8267ae8813f4d6eed990b9cee3
  completion_transition_receipt: docs/reviews/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-completion-transition-receipt-r1.yaml
  completion_transition_receipt_blob_sha: 153d03f20854bcdaf292a09552afb648e87d4074
  completion_checkpoint: docs/checkpoints/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1-completed-20261008.yaml
  completion_checkpoint_blob_sha: 72c9aa311d6248400f4a5d8b374f93918fff69b6
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
