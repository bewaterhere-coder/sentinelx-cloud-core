# PR-014 — Requirement Revision 2 Change Impact / Downstream Invalidation

## Decision

Requirement Revision 2 is a **material requirement / dependency / acceptance-boundary change**.

It removes the circular requirement that PR-014 S02/S03 wait for PR-013 canonical completion and narrows PR-014 V1 to:

```text
DevForge placement/scope/sandbox foundation
+ bootstrap-safe exact-commit source acquisition/capsule
+ bounded materialize_workspace
+ Development Host handoff
```

General retained multi-operation repository execution lifecycle and publication remain PR-013 ownership.

The prior Approved Plan R2 and its pending S02/S03 execution authority are therefore invalid as current implementation authority.

## Baseline

```yaml
task_id: PR-014-devforge-execution-workspace-materialization-bridge-v1
prior_requirement_revision: 1
prior_requirement_blob: 6c25edc8b3449c6ed51fadbe28ff330b7ea9be5e
current_requirement_revision: 2
current_requirement_blob: a40d84d4af112308c9f74301813b39bf487eabb5
prior_plan_revision: 2
prior_plan_blob: bf40efdd1c4804ea6ef5f858e22d2e558fdd8e70
prior_plan_status: approved
prior_plan_review: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-plan-review-r2.md
prior_execution_slice_set: docs/execution/PR-014-devforge-execution-workspace-materialization-bridge-v1-slices.yaml
prior_slice_set_blob: 9304d6a219bc8f70e29484961c1dc308d99faa98
prior_task_head_before_revision: 0bd1062396b5471cb44d36dc20cc8f31c08bcf1b
requirement_r2_commit: c6a21deeaa2e13886e20a45d3c1d1c9f3d6dc578
canonical_main_observed: 1028030b33f0ea792a884491a431fffe566f6aa5
devforge_main_observed: 5efc2d2b1eabe209d599f08ba5f9574771851374
devforge_latest_release: v2.97.0
transport:
  pr_number: 14
  branch: task/devforge-execution-workspace-materialization-bridge-v1
  preserved: true
```

## Change Classification

```yaml
requirement_semantics_changed: true
product_goal_changed: false
security_properties_changed: false
dependency_model_changed: true
implementation_boundary_changed: true
acceptance_boundary_changed: true
transport_changed: false
task_identity_changed: false
pr_identity_changed: false
```

The security goal remains unchanged: path-free Host-owned placement, provider-owned scope, durable pre-execution audit, AppContainer/Job containment, canonical source preservation and no generic fallback.

The material change is that PR-014 now owns a narrow bootstrap-safe source capsule/materializer seed rather than waiting for PR-013 general transaction/materializer completion.

## Propagation Matrix

| Artifact / Evidence | Disposition | Reason |
| --- | --- | --- |
| Requirement Revision 1 | Superseded | R2 changes dependency and completion boundary. |
| Plan Revision 2 | **Invalidated as current execution authority** | S02/S03 are gated on PR-013 completion and include retained multi-operation semantics no longer required by PR-014 R2. |
| Plan Review R1/R2 | Retained historical evidence | Review reasoning remains auditable but cannot approve Plan R3. |
| Plan R2 remediation / transition receipts | Retained historical evidence | Approval cannot transfer across material Requirement revision. |
| Execution Slice Set Plan R2 | **Invalidated as current implementation authorization** | S02/S03 dependency and scope changed. |
| S01 implementation | **Preserve; do not replay or roll back** | Placement Receipt, DevForge root binding, provider scope seam and Windows sandbox-root work remain aligned with R2. |
| S01 completion checkpoint | Retained current-compatible evidence subject to entry revalidation | It is historical completion evidence and must not be re-executed merely due to R2. |
| Prior S02 | Replaced by bootstrap-safe materialize_workspace seed | No PR-013 completion dependency. |
| Prior S03 | Replaced by Windows physical / handoff / regression closure | General repeated execute_scoped lifecycle returns to PR-013 ownership. |
| PR-013 dependency | **Removed as blocking dependency** | PR-013 may later provide a canonical backend but is not required for PR-014 completion. |
| PR-013 S03 | No replay authority | R2 explicitly forbids blind replay/import. |
| PR transport / Task identity | Preserve | Same Task, branch and PR remain canonical. |
| Acceptance approval | None reusable | acceptance_approved remains false. |
| Completion evidence | None reusable | completion_verified remains false. |

## Preserved S01 Evidence

Preserve without replay:

```text
src/sentinelx_core/devforge_workspace_placement.py
src/sentinelx_core/devforge_workspace_materialization.py
focused placement/root/scope tests
Windows root-confinement evidence
```

Canonical historical checkpoint:

```text
docs/checkpoints/PR-014-devforge-execution-workspace-materialization-bridge-v1-s01-completion-20261005.yaml
```

S01 remains evidence that the provider can derive and seal the DevForge execution root/workspace into existing mutation scope/sandbox authority. R2 adds the missing source materialization + handoff boundary on top.

## Self-Host Bootstrap Execution Boundary

The remaining bootstrap seed cannot require the Host-local execution workspace capability it is creating.

Plan R3 must therefore explicitly review one predeclared non-Host-local implementation segment for S02:

```text
existing PR #14 branch
+ structured canonical repository transport writes
+ no Host-local product workspace
+ no canonical-main mutation
+ CI / focused verification readback
```

This is not an error-driven fallback. It is an explicit Plan-level bootstrap mechanism that must be approved before S02 implementation.

Once the exact candidate exposes `materialize_workspace`, Host-local physical verification/activation proceeds under the normal SentinelX/DevForge security boundaries.

## Revised Gate State

After Plan R3 is durably persisted and read back:

```yaml
requirement_revision: 2
requirement_ready: true
plan_revision: 3
plan_status: ready_for_review
plan_approved: false
implementation_authorized: false
current_gate: plan_review
active_slice: none
completed_slices_preserved: [S01]
acceptance_approved: false
completion_verified: false
```

## Required Successor

Plan Revision 3 must be reviewed before any new product implementation.

```text
#开发评审 PR-014-devforge-execution-workspace-materialization-bridge-v1
```
