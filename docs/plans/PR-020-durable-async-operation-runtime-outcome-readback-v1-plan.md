# PR-020 — Durable Async Operation Runtime & Outcome Readback V1 — Plan R5

## Status and ownership

```yaml
task_id: PR-020-durable-async-operation-runtime-outcome-readback-v1
requirement_revision: 2
requirement_ref: docs/requirements/PR-020-durable-async-operation-runtime-outcome-readback-v1.md
plan_revision: 5
plan_status: hold_review_pending
plan_approved: false
implementation_authority: false
scope: administrative_HOLD_reconciliation_only
execution_disposition: HOLD
new_execution_slice_set: forbidden
original_pr: 20
original_branch: task/durable-async-operation-runtime-outcome-readback-v1
base_branch: main
original_main_readback: 2e5c69a112323867ee01783521554c43ebd731be
devforge_project_binding: direct/codex
mrs01_program_exit: HOLD
mrs02_admitted: false
```

**This is the proposed Plan R5 for the existing PR #20. It is not an execution Plan and does not authorize the pre-existing R4 implementation Slices.** It records the user's direction to stop timeout-driven Durable Async expansion and waits for independent `#开发评审` to verify and durably acknowledge the HOLD.

## 1. Canonical authority and rationale

- SentinelX `main@2e5c69a112323867ee01783521554c43ebd731be`.
- Completed PR-021 Minimal Runtime ADR `36e0290de039336a8e4ce8561c22c731f12e9602`, capability disposition matrix `05b6906614715e14450a2fd03e0699200e016074`.
- Completed PR-023 five-stage successor roadmap `8a281b60c1b8e9f5d665003a94f4f6b1d906de34`.
- Completed PR-027 MRS-01 Owner-Gate Matrix `7507dff0032f29a99387c25f648508c48a03b6e9`, owner #20 handoff `3b5ef4d066293250ebc8ebbcf549d9b5f14f94cc`.
- DevForge task bootstrap override contract `31fea7271020e76075b2eed656cbeda0ac8fe52b`: active authority expires or becomes invalid when Task leaves the admitted stage, Requirement or Plan changes, or override is explicitly revoked.

**Product decision:** no independent requirement currently validates implementing a new provider-neutral Durable Async Operation Runtime in SentinelX merely to exceed DevForge/Hub's short synchronous dispatch window. DevForge/Guided CLI owns long development work and its receipt handoff; SentinelX continues existing bounded scoped runtime, physical containment and audit. This is not a blanket ban on future separately justified asynchronous *product* capabilities.

## 2. HOLD classification

| Capability or proposal | Plan R5 disposition | Rules |
| --- | --- | --- |
| New DurableOperationRuntime scheduler/store/lifecycle | **HOLD** | No module, API, schema, state migration, GC or source mutation |
| Timeout-driven Direct Codex/CodeBuddy async execution bridge | **HOLD** | Long Agent development lifecycle belongs outside Minimal Runtime |
| Historic Plan R4 S01–S04 and approved Review R4 | **SUPERSEDED HISTORY** | Preserve exact blobs/receipts, no execution/replay |
| Task-scoped `direct:codebuddy` bootstrap | **REVOKED** | No re-admission, fallback, implicit provider change |
| Existing generic Agent background exec/script jobs | **KEEP** | No code or behavior change |
| Existing `pending_results` and result delivery/reconnect/replay | **KEEP** | Do not claim in-flight durable scheduler semantics |
| AppContainer, Job, MutationScope, firewall, ACL and durable audit | **KEEP** | No rights widening, shell fallback or protected-root carveout |
| New independently justified product async need | **NOT ADMITTED** | New evidence, Requirement/Plan/Review and explicit user approval first |

## 3. Exact historical evidence — immutable

The R4 Plan was originally approved for Requirement R1, but that older authority is now superseded for execution.

- Requirement R1 original Git blob: `2c2c33e6b969e271c4acb7277b08cd212f2f3de3`.
- Plan R4 original Git blob: `304cbf2ab58b4fa3835c35b343bd1214565c2920`.
- Plan Review R4 Approved: `docs/reviews/PR-020-durable-async-operation-runtime-outcome-readback-v1-plan-review-r4.md@2082e376c8bda337f5d82eb34785a499d6295a5c`.
- Previous R4 Slice Set original blob: `f461220e206af7935619640b96288a3880381224`; current same file has S01–S04 marked `suspended` and no active Slice.
- Historical `direct:codebuddy` bootstrap admission Receipt: `649747ff84130a7e60b93da15c20b77e917c8bd9`; original active override blob `fbe24326a67fd4620e19b63123b38c4f1fe98c6f`, now revoked with revocation evidence.
- Historical S01 Run `79b9f6f3533c289acbd14b71b3d51fa102cd5ce7` and blocked checkpoint `962e3ea9069a29db3d1eba6a8e423df4c2c214c4`: `WorkspaceMaterializationProviderUnavailable`; `product_mutation_started=false`; `provider_process_started=false`; completed Slices: **none**.
- No old Receipt or Run shall be rewritten to imply it was never admitted or that its failure is currently reproducible. The new HOLD/Revocation Receipt supersedes only future execution authority.

## 4. Only authorized HOLD transition steps

**These are orchestration/readback controls, not executable DevForge product Slices.** No `#开发执行` for this Task is admitted under Plan R5.

1. **G1 — Exact owner readback:** verify same PR #20/branch, current main, Requirement R2, Plan R5, prior R4 blobs and old blocked Run.
2. **G2 — Fail-closed authority:** read the `revoked` bootstrap override, Revocation Receipt, `implementation_authorized=false`, `stage=plan_review`, `plan_approved=false`, R4 Slice Set `suspended`.
3. **G3 — Minimal Runtime non-regression:** independently verify no new product files, Host/permission/project binding changes, or modifications to existing background jobs and `pending_results`. No owner PR #13/#14/#19/#27 edits.
4. **G4 — Owner Plan Review:** approve/reject only the HOLD administrative disposition; persist independent Review/Transition Receipt through the existing DevForge `#开发评审` entry. Reviewer cannot convert administrative approval into S01 implementation approval.
5. **G5 — Program handoff:** publish updated owner HOLD classification to a future MRS-01 gate readback only after G4 decision evidence is durable. While other Owner #13/#14/#19 exits remain missing, `MRS01=HOLD` and `MRS02=false`.

## 5. Safety and abort gates

- `implementation_authorized=true`, active bootstrap, or any current R4 Slice admission after R2/R5 is a **blocking conflict**, not an execution opportunity.
- If GitHub Head/main/Requirement/Plan/override/slice SHA differ from read-back, stop for owner Gate re-review; do not bypass.
- No product code, tests, CI, native Host mutation, service restart, deployment or release; no unrestricted PowerShell or uncontrolled workspace materialization.
- `D:\coco` protected_root remains protected; no allowlist exception/ACL expansion.
- No new Task/branch/PR. All mutations reside only in original PR #20 task-owned `docs/` artifacts.
- Approval may record `OwnerDisposition=HOLD_ACKNOWLEDGED` but never `Plan_R5_implementation_authorized=true`.
- Preserve original DevForge `direct/codex` project binding and its existing Provider/Sandbox gates.

## 6. Review exit

Plan R5 is **Ready for HOLD Plan Review**, not approved; current implementation is stopped by fail-closed owner authority revocation.

Reviewer must separately verify authoritative Task/Plan/Override/Slice Set/Receipt readbacks. If approved, publish a durable Owner HOLD Gate decision, keep product implementation disabled and `MRS02=not admitted`. If rejected, keep the same execution HOLD and revise the existing Task/Plan; never resume historical S01 by default.

```text
#开发评审 PR-020-durable-async-operation-runtime-outcome-readback-v1
```
