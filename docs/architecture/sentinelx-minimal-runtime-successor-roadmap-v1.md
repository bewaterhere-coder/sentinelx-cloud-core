# SentinelX Minimal Runtime Successor Roadmap V1

Status: **S02 Active Work Reconciliation frozen; five-stage program detail not yet materialized**

Task: `PR-023-minimal-runtime-successor-roadmap-v1`

Requirement: Revision 1

Approved Plan: Revision 1

Architecture authority:

- `docs/architecture/sentinelx-minimal-runtime-boundary-v1.md`
- `docs/architecture/sentinelx-capability-disposition-matrix-v1.md`
- `docs/requirements/PR-021-minimal-runtime-complexity-reduction-boundary-v1.md`

## 1. S02 Evidence Baseline

~~~yaml
sentinelx_main: cd42e371f18056327c1d8b744f8956a76bc11541
open_prs: [13, 14, 16, 19, 20, 23]
devforge_runtime:
  version: "2.103.0"
  revision: ebc25425160790950bd4d4500186652d3bf52416
devforge_project_binding:
  provider: direct
  adapter: codex
  source: explicit_project_binding
predecessor:
  task: PR-021-minimal-runtime-complexity-reduction-boundary-v1
  state: done
  architecture_status: frozen
~~~

The S02 baseline refresh detected one material drift after S01:

- PR #14 advanced from the S01 snapshot to Requirement Revision 5 / Plan Revision 10 at `plan_review`.
- The current PR #14 state already consumes the Minimal Runtime conflict as a replanning concern, but still records `CanonicalMainImplementationSurfaceMismatch`.
- S02 therefore classifies PR #14 from its current durable state, not from the older S01 task snapshot.

No other open-PR identity changed between the S01 baseline and the S02 refresh.

## 2. Disposition Semantics

The roadmap uses only the Requirement-approved active-lineage dispositions:

| Disposition | Meaning in this roadmap |
| --- | --- |
| **continue** | The current task direction is compatible with the Minimal Runtime boundary and may proceed under its own DevForge authority. |
| **reshape** | Valuable evidence or substrate exists, but the active task scope must be narrowed/replanned before further conflicting product mutation. |
| **hold** | Stop implementation/expansion in the current direction. Historical evidence remains valid; reentry needs new evidence or a new/revised independent requirement. |
| **supersede-candidate** | The task may eventually be replaced by a successor lineage, but classification alone does not create/close that lineage. |
| **close-candidate** | The task may eventually be closed after its evidence is preserved and the owning workflow authorizes closure. |
| **independent/non-conflicting** | The task addresses a retained security/compatibility concern that does not depend on SentinelX owning long development-Agent lifecycle. |

A disposition is **planning/control-plane evidence only**. It does not authorize merge, close, rebase, branch rewrite, source deletion, binding mutation, deployment, release, or permission expansion.

## 3. Active Work Reconciliation Matrix

| PR / Task | Current durable state | Relation to PR-021 | Disposition | Evidence/assets to preserve | Blocking conflict | Required successor stage | May continue before successor stage is complete? | Mutation-authority note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **#13 — PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1** | `implementation`; Plan R2 approved; S01/S02 completed; S03 pending; head `4a3f8e35...` | Mixed. Provider-owned repository transaction, AppContainer, audit, firewall, CAS publication are valuable bounded-security concepts; current Plan also owns an end-to-end repository materialize → execute → publish lifecycle that predates PR-021 and can outgrow a short control-plane operation. | **reshape** | Completed S01/S02 receipts; exact-source acquisition; AppContainer materializer; repository firewall/audit composition; immutable publication capsule; fixed-plumbing CAS/read-back design. | Current S03/S04 direction assumes SentinelX owns repository execution/publication lifecycle without an explicit post-PR-021 direct-short workload bound. That can recreate duration-uncertain orchestration inside SentinelX. | **MRS-01** | **Planning/read-only reconciliation only. Product continuation should wait until the retained bounded repository-transaction/security subset is explicitly proven compatible with direct-short routing.** | This matrix does not edit or invalidate PR #13. |
| **#14 — PR-014-devforge-execution-workspace-materialization-bridge-v1** | `plan_review`; Requirement R5; Plan R10; `plan_approved=false`; completed historical S01/S02/S03A evidence; `CanonicalMainImplementationSurfaceMismatch`; head `a69610a8...` | Explicit PR-021 conflict already recognized. PR-021 requires retaining only minimal short-mutation workspace isolation/security substrate and holding/removing long-Agent/Direct Development Host bootstrap objectives. | **reshape** | Historical S01/S02 receipts; preserved candidate `45dc99d15a23c499b4c1500fab60ed5e76475aeb`; protected-root separation; Host-owned placement; MutationScope binding; AppContainer/Job confinement; no-caller-path authority; additive durable-schema migration evidence. | Current canonical implementation topology no longer matches historical branch surfaces, and long-Agent/bootstrap semantics cannot be carried forward by inertia. | **MRS-01** | **Yes for Requirement/Plan review and read-only source-ownership reconciliation. No new product mutation until an approved retained Minimal Runtime target is bound to current canonical source ownership.** | Historical candidate/code provenance is evidence, not automatic merge/replay authority. |
| **#16 — PR-016-scoped-verification-node-npm-typescript-appcontainer-drive-root-compatibility-v1** | `implementation`; Plan R1 approved; S01 pending; head `c26de0e9...` | Security/compatibility work inside retained scoped verification and AppContainer boundary. No evidence that the Requirement requires SentinelX to own a long development-Agent lifecycle. | **independent/non-conflicting** | Real Node/npm/TypeScript `D:\\` EPERM reproduction; scoped verification readiness evidence; filesystem traversal/AppContainer compatibility constraints. | No Minimal Runtime architecture conflict proven. Runtime execution must still obey direct-short vs guided-CLI routing based on actual workload shape. | **MRS-01** | **Yes, under its existing DevForge authority, provided execution mode remains fail-closed and long/uncertain verification is not forced through SentinelX synchronously.** | Classification grants no extra authority beyond PR #16's own approved Task. |
| **#19 — PR-019-stable-baseline-stabilization-exit-gate-v1** | `implementation`; Plan R2 approved; S01 pending; candidate `4ffb2dc3...` published; verification blocked by Host Mutation Scope schema incompatibility; head `f13dfe87...` | Stabilization evidence is valuable, but the current baseline explicitly contains Direct Codex readiness/E2E assumptions. PR-021 says stability must not permanently depend on SentinelX-owned long-Agent Direct Codex lifecycle. | **reshape** | Stable-baseline criteria; candidate `4ffb2dc312fac8d1030eb521641f6c61c33f11f0`; exact-candidate activation model; Host Mutation Scope corruption/terminalization evidence; security-critical short-runtime readiness checks. | Baseline semantics still treat Direct Codex lifecycle as mandatory evidence. Completion unchanged would fossilize an architecture dependency PR-021 intends to retire. | **MRS-01** | **Only evidence-preserving/security-critical stabilization work may continue. Stable-baseline completion must wait for a revised baseline that separates retained short-runtime security from long-Agent Direct Codex lifecycle.** | Existing evidence remains historical truth even if the baseline is reshaped. |
| **#20 — PR-020-durable-async-operation-runtime-outcome-readback-v1** | `implementation`; Plan R4 approved; S01 pending; blocked by `WorkspaceMaterializationProviderUnavailable`; bootstrap target `direct:codebuddy`; head `96d4ad00...` | Directly adjudicated by PR-021. Durable Async is not justified as the solution for development work outliving Hub/local_api; generic background delivery remains independently valid. | **hold** | Durable operation identity, retention/tombstone, restart reconciliation, duplicate suppression, outcome-unknown/read-back design; blocked dependency evidence; any future independent non-development rationale. | Current Requirement is explicitly driven by long development-operation timeout/lifecycle ownership and would make SentinelX own additional scheduler/durability state machines. | **MRS-01** | **No product implementation in the current development-timeout direction. Read-only evidence preservation is allowed. Reentry requires a distinct independently justified non-development requirement.** | HOLD is not deletion or PR-close authority. |
| **#23 — PR-023-minimal-runtime-successor-roadmap-v1** | `implementation`; Plan R1 approved; S01 completed; S02 executing; head at S02 start `c035fa71...` | Direct successor control-plane task authorized to reconcile current work and materialize the already-frozen PR-021 sequence. | **continue** | Requirement R1; Plan R1; Review R1; S01 inventory/receipt; S02 reconciliation evidence. | No architecture conflict identified. Must remain documentation/control-plane only and must not mutate other PRs or DevForge binding. | **MRS-01** | **Yes. This task is the MRS-01 reconciliation/roadmap authority and may continue its own Slices.** | It may classify other PRs but cannot mutate them. |

## 4. Cross-Cutting Reconciliation Decisions

### 4.1 Security and bounded-runtime substrate remains admissible

The following categories remain compatible with the Minimal Runtime when they serve bounded direct operations and preserve existing safety invariants:

- provider-owned workspace placement/isolation;
- Mutation Scope binding;
- AppContainer/ACL/Job confinement;
- fail-closed audit;
- canonical repository firewall;
- exact operation/effect classification;
- scoped verification;
- canonical commit/receipt/read-back verification;
- provider-neutral evidence normalization.

Compatibility is **not** automatic authority to keep every historical implementation path.

### 4.2 Long-Agent orchestration cannot survive by historical dependency

Historical dependencies from PR #13/#14/#19/#20 do not override PR-021.

In particular:

- Direct CodeBuddy/Codex bootstrap is not a retained SentinelX core goal;
- duration-uncertain execution does not become direct-short merely because it is inside a DevForge Slice;
- repository/workspace materialization is retained only where independently needed for bounded secure mutation;
- current DevForge `direct/codex` project binding remains operational reality until a separate DevForge-owned migration occurs;
- no Direct Codex removal occurs during this reconciliation task.

### 4.3 Generic async/background behavior remains independently owned

PR-020 HOLD does not deprecate:

- `jobs.py`;
- `pending_results.py`;
- independent background delivery/replay behavior.

Those capabilities remain governed by their own product requirements.

## 5. S02 Decision Boundary

S02 freezes the reconciliation dispositions above.

It **does not yet materialize** the detailed five-stage successor program. That belongs to S03 under the Approved Plan.

The already-authoritative order remains referenced, but S02 does not expand its stage owner/entry/exit/task-candidate definitions:

~~~text
MRS-01 → MRS-02 → MRS-03 → MRS-04 → MRS-05
~~~

S03 is the only next Slice authorized to materialize those stage details.
