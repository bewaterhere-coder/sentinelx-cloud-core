# PR-010 — Requirement Revision 2 Change Impact / Downstream Invalidation

## Decision

Requirement Revision 2 is a **material requirement/acceptance-boundary change** because it changes what may constitute implementation, verification, and Acceptance authority:

- `mcp.sentinelx.app` is frozen as an immutable third-party closed-source transport boundary;
- Hub projection gaps are external integration limitations, not PR-010 blockers;
- Core-owned unit/integration/protocol evidence is the verification authority;
- PR-009 is no longer a blocking dependency;
- S01's repository-identity composition finding remains the true current blocker.

Per DevForge Requirement Change Invalidation semantics, downstream artifacts are reused only where their assumptions remain compatible with Requirement Revision 2.

## Baseline

```yaml
task_id: PR-010-canonical-repository-mutation-firewall-v1
prior_requirement_revision: 1
prior_requirement_blob: d19545d07c1607760b8af50e876657d3a615738f
prior_plan_revision: 2
prior_plan_status: approved
prior_plan_review: docs/reviews/PR-010-canonical-repository-mutation-firewall-v1-plan-review-r2.md
prior_plan_approval_checkpoint: docs/checkpoints/PR-010-canonical-repository-mutation-firewall-v1-plan-review-r2-approved-20261002.yaml
prior_execution_slice_set: docs/execution/PR-010-canonical-repository-mutation-firewall-v1-slices.yaml
prior_task_head: 000df47dd59e749e1d9526b83232c11d780c4423
canonical_main_observed: f7e878f3497582547e5d52cd33b060cae18d2e84
s01_implementation_head: 62b9fba588fac58161c909e8622278d791c07a92
transport:
  pr_number: 10
  branch: task/canonical-repository-mutation-firewall-v1
  preserved: true
```

## Change Classification

```yaml
requirement_semantics_changed: true
product_goal_changed: false
security_property_changed: false
implementation_target_changed: false
verification_authority_changed: true
acceptance_boundary_changed: true
external_dependency_model_changed: true
transport_changed: false
```

The product/security objective remains provider-wide canonical repository mutation exclusion. The material change is the ownership and evidence boundary: SentinelX Core must prove the property itself, while the Hub is transport-only and cannot be a required implementation or verification surface.

## Propagation Matrix

| Artifact / Evidence | Disposition | Reason |
| --- | --- | --- |
| Requirement Revision 1 | Superseded | Revision 2 freezes Hub and changes verification/Acceptance authority. |
| Plan Revision 2 | **Invalidated as current execution authority** | It contains projection-oriented verification language and was approved against Requirement Revision 1. |
| Plan Review R1/R2 | Retained historical evidence | Review reasoning remains auditable but cannot approve Plan Revision 3. |
| R2 remediation + approval checkpoint | Retained historical evidence | No replay/deletion; approval does not transfer to materially revised requirement lineage. |
| Execution Slice Set Revision 2 | **Invalidated as implementation authorization** | Slice semantics/verification need Revision 2 lineage, especially S01 and S04. |
| S01 source implementation | **Retained; do not replay or roll back** | Inventory/firewall implementation remains aligned with the product goal. |
| S01 static compile observation | Retained as historical observation, not completion receipt | Code will change to resolve repository-identity composition and must be reverified. |
| S01 Hub `execution_profile_required` dynamic blocker | **Superseded / non-blocking** | External Hub tool projection is outside PR-010 completion authority. |
| S01 `RepositoryIdentity` composition finding | **Retained and promoted as active blocker** | It is a Core design-consistency problem and directly conflicts with the no-duplicate identity invariant. |
| S02/S03 intended implementation semantics | Retained conceptually, replanned under Revision 3 | Structured/process Core enforcement remains required; verification must be Core-owned. |
| S04 `Capability readiness + projection composition` | **Invalidated/replaced** | Replaced by `Core Capability Readiness + Existing Transport Projection`; Hub modification/rendering is not required. |
| S05 incident/security regression goal | Retained, verification wording revised | Core/Windows evidence remains required; Hub projection evidence is not. |
| Acceptance approval | No reusable approval exists | `acceptance_approved=false`; Revision 2 Acceptance will use new lineage. |
| Completion evidence | No reusable completion exists | `completion_verified=false`. |
| PR-009 dependency | **Removed as blocking dependency** | Hub dynamic projection work is independent/non-blocking for PR-010. |
| PR-007/PR-008 overlap gates | Retained | They still touch Core mutation/capability seams and require exact readback before overlapping mutation. |
| PR transport / Task identity | Retained | Same Task, branch and PR remain canonical transport. |

## S01 Retained State

The following already-landed S01 surfaces remain in place:

```text
src/sentinelx_core/policy.py
src/sentinelx_core/canonical_repository_firewall.py
tests/test_canonical_repository_firewall.py
```

No verified external side effect is replayed.

Historical checkpoint:

`docs/checkpoints/PR-010-canonical-repository-mutation-firewall-v1-s01-verification-blocked-20261002.yaml`

is retained unchanged. Its Hub-projection blocker is no longer current authority, while its Core finding remains current:

```text
existing primitive:
  sentinelx_core.mutation_placement.RepositoryIdentity
parallel implementation:
  sentinelx_core.policy._canonical_repository_identity
risk:
  divergent normalization semantics, including authority/port behavior
required repair:
  reuse/share one provider repository identity primitive
```

S01 is therefore **implementation_retained_revalidation_required**, not `not_started`, not complete, and not rolled back.

## Revised Gate State

```yaml
requirement_revision: 2
requirement_ready: true
plan_revision: 3
plan_status: ready_for_review
plan_approved: false
implementation_authorized: false
current_gate: plan_review
active_slice: none
acceptance_approved: false
completion_verified: false
```

Implementation does not resume until Plan Revision 3 is reviewed and approved through the normal DevForge Plan Review gate.

## Verification Authority After Revision 2

Accepted PR-010 evidence may come from:

1. focused SentinelX Core unit tests;
2. SentinelX Core integration tests;
3. Core protocol/hello/capability readback through repo-controlled code/fixtures;
4. repository CI on the exact task head where available;
5. Windows physical mutation/regression evidence required by the firewall contract.

The following may be recorded diagnostically but cannot block PR-010 by themselves:

- Hub not exposing `execution_profile`;
- Hub not projecting a dynamic tool;
- Hub not rendering a capability field;
- Hub model-facing schema lag;
- any other closed-source transport projection mismatch.

If a required Core-owned verification channel is unavailable, that remains a legitimate verification blocker. The revision does not waive Core verification.

## Dependency Reconciliation

- PR-007 and PR-008 remain exact-readback overlap dependencies before mutation on shared Core seams.
- PR-009 is independent/non-blocking and is not part of PR-010 completion lineage.
- No Hub mutation, deployment, schema change, permission expansion, unrestricted fallback, or new execution authority is authorized by this Requirement change.

## Required Successor

Plan Revision 3 must be reviewed before implementation resumes.

```text
#开发评审 PR-010-canonical-repository-mutation-firewall-v1
```
