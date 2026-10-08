# SentinelX Minimal Runtime Successor Roadmap V1

Status: **S04 retirement/safety gates frozen; S05 final verification pending**

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

At the S02 checkpoint, the detailed five-stage successor program was **not yet materialized**. The later S03 section below now carries that separately authorized program detail.

The already-authoritative order remains referenced, but S02 does not expand its stage owner/entry/exit/task-candidate definitions:

~~~text
MRS-01 → MRS-02 → MRS-03 → MRS-04 → MRS-05
~~~

Only S03, under its separately invoked command, was authorized to materialize those stage details; S02 did not pre-execute S03.


## 6. Five-Stage Successor Program — S03

### Program authority and exactly one primary order

PR-021 Step 1–5 is binding. This section **expands the existing frozen sequence**; it does not define an alternative roadmap.

~~~text
MRS-01 Active Work Reconciliation
    ↓ accepted reconciliation evidence
MRS-02 Provider-Neutral Guided CLI Routing & Handoff
    ↓ accepted routing/handoff evidence
MRS-03 DevForge Execution Binding Migration
    ↓ accepted project-binding migration read-back
MRS-04 SentinelX Minimal Runtime Proof
    ↓ accepted physical proof and security receipts
MRS-05 Long-Agent Surface Retirement Program
~~~

**Gate semantics:** `proposed`, `documented`, `implemented`, `reviewed`, and `accepted` are not interchangeable. A stage's exit requires its *own* owning DevForge Task acceptance/finish evidence where applicable. A successor proposal in this roadmap does not instantiate, approve, execute, or complete that Task.

**Evidence rule:** A Task or Slice completion claim requires its own canonical receipt and transport read-back; the roadmap's acceptance alone never proves an external successor implementation. DevForge owns Task/Plan/Slice/Run/Attempt identity and stage progression. SentinelX is the secure short-duration local bridge. Long or duration-uncertain local Agent/process lifetime belongs to the local CLI operator/provider.

### MRS-01 — Active Work Reconciliation

| Field | Frozen program contract |
| --- | --- |
| Problem solved | Existing PR #13/#14/#19/#20 implementation directions can retain long-development lifecycle ownership, even after PR-021 accepted the smaller SentinelX boundary. |
| Owner | **DevForge Task owners for each affected SentinelX PR**, with PR-021 architecture as reviewer authority; no central roadmap Task may rewrite another PR. |
| Repository / runtime authority | **`bewaterhere-coder/sentinelx-cloud-core`** for per-PR Requirements/Plans/decisions; **DevForge `project_development`** for each independent Gate and lineage. Same-repository successor work; this Task is documentation-only. |
| Prerequisites | PR-021 `done` and architecture/disposition evidence readable; live `main`/open-PR evidence and S01/S02 matrix read back; latest per-PR drift consumed before decision. |
| Allowed scope | Separate DevForge Requirement/Plan reviews, evidence preservation and approved minimal-scope reconciliation for #13/#14/#19/#20; independent #16 may continue under its own authority. |
| Forbidden scope | Silent merge/close/rebase/supersession; code replay; invalidation or deletion of historical receipts; continuing #20 as a development timeout solution; reinstating long-Agent bootstrap by relabeling a Slice as short. |
| Entry gate | PR-021 accepted architecture is canonical and each affected PR's exact current Task/Plan/receipt lineage is verified. |
| Exit/acceptance evidence | Separate durable owning-task decisions: #13's bounded repository-transaction/security target resolved; #14's retained short-mutation workspace substrate and current-main source ownership resolved with historical candidate preserved; #19's stable baseline no longer permanently depends on SentinelX-owned Direct Codex lifecycle; #20's development-timeout direction durably HOLD/reconciled. Each has owner-scoped review/receipt and read-back. #16 remains independently scoped. |
| Dependency | Program entry / no predecessor stage. MRS-02 depends on the accepted reconciliation exit; #23 S02 matrix alone is **not** sufficient evidence. |
| Candidate follow-on DevForge Task | **SentinelX Minimal Runtime Active-Lineage Reconciliation & Owner-Gate Closure V1** — same repository, governance/evidence-only first; each actual PR change remains under its own Task. |
| Current status | **Documented, not accepted as program exit.** PR #23 freezes the matrix; individual affected PR Gate transitions are not performed here. |

A `reshape` disposition is not an instruction to delete work. It authorizes a later owning-Task reviewer to separate:

- **Retained substrate:** Host-owned workspace placement, protected-root firewall, Mutation Scope, AppContainer/ACL/Job isolation, fail-closed audit, scoped read/write, short verification and commit/receipt/read-back semantics.
- **Architecture-conflicting scope:** DevForge/Codex/CodeBuddy long-Agent lifecycle, direct Host bootstrap, unbounded in-Hub repository execution, or Durable Async developed mainly to mask request timeouts.
- **Unresolved topology:** PR #14's source-tree mismatch cannot be resolved by replaying historical `45dc99d...` code into canonical `main`.

### MRS-02 — Provider-Neutral Guided CLI Routing & Handoff

| Field | Frozen program contract |
| --- | --- |
| Problem solved | A DevForge development Slice may be duration-uncertain; SentinelX's short Hub/local_api control window must not become the lifetime owner of Codex, CodeBuddy, full builds, or long tests. |
| Owner | **DevForge execution-routing/orchestration contract owner** for mode classification and handoff; local CLI/operator owns the actual long process; SentinelX only provides eligible bounded Host capabilities. |
| Repository / runtime authority | **`bewaterhere-coder/DevForge`**, `project_development` execution routing and handoff contracts, through a **separate DevForge-owned Task**. Cross-repository dependency relative to this SentinelX roadmap. Any SentinelX-side short projection adjustment requires its own separately scoped SentinelX Task. |
| Prerequisites | MRS-01 owning-Task reconciliation exit accepted/read back; current DevForge execution-routing and Slice contracts resolved; provider-neutral handoff/evidence schema approved before provider adapters. |
| Allowed scope | Deterministic mode resolver + handoff emitter; provider-specific CLI examples as consumers; exact scope/lineage validation; returned commit/receipt/read-back ingestion and no-replay decision. |
| Forbidden scope | Direct Codex deletion; mutating project binding in this stage; treating CLI text as authorization; automatically executing the shell command; recreating a DevForge long-Agent job scheduler in SentinelX; extending Hub timeout to avoid routing. |
| Entry gate | MRS-01 accepted; current Task/Plan/Slice and provider safety capabilities admit the proposed operation; ambiguity or unknown duration fails closed to guided handoff/decision instead of guessing direct-short. |
| Exit/acceptance evidence | DevForge accepted routing Task with deterministic representative cases: read-only → read path; bounded authorized short Host mutation/verification → SentinelX direct-short; Codex/CodeBuddy/large build/long test/duration-uncertain work → `GuidedCLIRequired` plus complete handoff; exact returned commit/receipt/remote read-back validated; unsupported provider, stale Task/Plan, or unsafe mutation scope fails closed; handoff does not grant authority. |
| Dependency | MRS-01 → **MRS-02** → MRS-03. |
| Candidate follow-on DevForge Task | **Provider-Neutral Guided CLI Execution Routing & Deterministic Handoff V1** — DevForge repository, separate Task. |
| Current status | **Not implemented or accepted by PR #23.** |

#### MRS-02 minimum handoff contract

The provider-neutral handoff contains **all** of the following, or explicitly marks legitimately non-applicable optional identity fields:

~~~yaml
handoff:
  repository_identity: exact_canonical_repository
  task_id: exact_devforge_task
  transport:
    pr_number: exact_when_applicable
    task_branch: exact_when_applicable
    base_branch: canonical
  workflow_stage: exact_current_stage
  requirement:
    ref: exact_current_ref
    revision: exact_current_revision
  plan:
    ref: exact_approved_ref_when_applicable
    revision: exact_approved_revision_when_applicable
    digest: verified_when_execution_authorized
  execution:
    slice_id: exact_when_applicable
    run_id: exact_when_applicable
    attempt_id: exact_when_applicable
    execution_mode: guided_cli
    provider: selected_eligible_cli_consumer
  authority:
    allowed_mutation_scope: explicit_and_verified
    forbidden_actions: explicit
    canonical_main_mutation: forbidden
    credential_expansion: forbidden
    destructive_operation_escalation: forbidden
  verification:
    required_checks: exact_plan_scoped
    expected_returned_commit: exact_identity_when_produced
    expected_receipt: exact_schema_and_lineage
    expected_remote_readback: required_for_external_publication
  authority_statement: >
    Handoff text transfers context and execution identity only.
    It grants no permission, credential, filesystem, workflow,
    release or destructive-action authority.
~~~

A complete generated CLI package must also state where the user's separately authorized provider executes, what evidence is returned, how the original DevForge Task/Run resumes, and what to do when a receipt is absent or the result is uncertain. **The host never treats "command printed" as "command executed".**

#### MRS-02 direct-short remains first-class

The resolver uses **workload shape and verified capability**, not an arbitrary clock cut-off:

- read-only retrieval: read path;
- bounded scope, short target, admitted sandbox/audit, finite output and short verification: SentinelX direct-short;
- long/uncertain Agent execution, large refactor, dependency installation, broad integration, Unity/build/test: guided local CLI.

DevForge Slice identity is **not** proof that execution is short; a Slice can still require guided CLI. No implicit provider fallback is allowed once an execution attempt selects a provider.

### MRS-03 — DevForge Execution Binding Migration

| Field | Frozen program contract |
| --- | --- |
| Problem solved | Canonical DevForge project registry still binds `sentinelx-cloud-core` to `provider: direct / adapter: codex`, anchoring runtime execution to a lifecycle excluded from the target SentinelX core. |
| Owner | **DevForge project-binding and provider-resolution authority owner** through its canonical development workflow. |
| Repository / runtime authority | **`bewaterhere-coder/DevForge`** `system/development-project-registry.yaml` and current binding/resolution contracts; **cross-repository mutation owned by DevForge, not by PR #23 or a SentinelX Task.** |
| Prerequisites | MRS-02 provider-neutral routing and returned-evidence validation accepted/read back; MRS-01 active-work reconciliation accepted; explicit binding migration Requirement and current registry SHA read back. |
| Allowed scope | Separately reviewed project-binding migration; provider-resolution semantics; migration/rollback evidence; live admission proving direct-short vs guided CLI routes. |
| Forbidden scope | Changing the registry from this SentinelX PR; implicit migration by Local-First defaults; silent fallback to direct/codex; weakening canonical main firewall, isolated workspace, scope, audit, transport identity or completion receipts; Direct Codex source removal. |
| Entry gate | MRS-02 replacement capability accepted and the migration Task has exact DevForge project registry/plan authority. |
| Exit/acceptance evidence | Approved/implemented/accepted DevForge migration Task; before/after exact registry blob SHA + read-back; stable `sentinelx-cloud-core` repository identity; bounded operation routes to SentinelX direct-short; long development work routes to guided CLI; stale/unavailable provider is fail-closed; Task/PR/branch/Requirement/Plan/Slice/Run/Attempt and returned commit/receipt/read-back remain invariant; isolated execution workspace constraints and rollback path are verified. |
| Dependency | MRS-02 → **MRS-03** → MRS-04. |
| Candidate follow-on DevForge Task | **SentinelX Project Execution Binding Migration to Guided CLI Routing V1** — DevForge repository, separate Task. |
| Current status | **Not migrated by PR #23.** Current observed binding is `direct/codex` (`source: explicit_project_binding`). |

MRS-03 must select the exact new binding **from accepted MRS-02 contracts**; this roadmap does not invent or pre-register a new `provider` or `adapter` token.

### MRS-04 — SentinelX Minimal Runtime Proof

| Field | Frozen program contract |
| --- | --- |
| Problem solved | Documentation and provider migration alone cannot prove that the remaining SentinelX Host bridge is safe and sufficient for bounded, short-duration tasks. |
| Owner | **SentinelX runtime/security and Windows Host verification owners**, with DevForge acceptance consuming independent physical read-back evidence. |
| Repository / runtime authority | **`bewaterhere-coder/sentinelx-cloud-core`** through a separate verification DevForge Task; exact installed Host/Agent candidate evidence and operator-approved activation where required. Same-repository verification scope; external Host effects must use their own approved admission/receipts. |
| Prerequisites | MRS-01, MRS-02, and MRS-03 exits accepted; exact installed candidate and current Host policy/authority state independently read back; safe isolated physical fixture and rollback prepared when relevant. |
| Allowed scope | Physical bounded read/write/short command/short verification; controlled negative tests; exact scoped Host admission/terminalization; projection/audit/firewall/effect/read-back proof; long/uncertain routing negative case. |
| Forbidden scope | Reintroducing long-Agent lifecycle to make proof pass; bypassing AppContainer, ACL, Job, Mutation Scope, audit or canonical main firewall; unrestricted shell/file mutation; guessing Host readiness from source/CI; claiming proof from mocks or an unactivated candidate; retiring Direct Codex in the proof Task. |
| Entry gate | Accepted routing and migrated binding evidence; explicit proof Task approval; live exact-candidate Host capabilities, permissions and fixture boundaries admitted. |
| Exit/acceptance evidence | Independently verified real Host results and receipt/read-back for every minimum proof case below; fail-closed negatives and rollback/terminal authority evidence; acceptance explicitly says whether retained minimal runtime is sufficient **without** long development-Agent lifecycle. Any failed mandatory proof leaves MRS-04 unaccepted and retirement blocked. |
| Dependency | MRS-03 → **MRS-04** → MRS-05. |
| Candidate follow-on DevForge Task | **SentinelX Minimal Runtime Host Sufficiency & Security Proof V1** — SentinelX repository, separate Task. |
| Current status | **No physical Minimal Runtime proof is claimed by this documentation Task.** |

#### MRS-04 minimum real-Host proof matrix

| Proof | Observation / negative guard |
| --- | --- |
| Structured local capability projection | Live list/describe/call or equivalent closed projection returns truthful schemas and bounded errors. |
| Bounded read | Admitted exact read target and output; unauthorized path fails closed. |
| Bounded file mutation | Mutation only inside admitted scope; canonical checkout/protected root remains unchanged. |
| Short command execution | Exact admitted executable/arguments and finite output; prohibited operation cannot launch. |
| Short focused verification | Admitted exact test/verification target; unsupported/uncertain workload routes to CLI rather than silently widening. |
| Host Mutation Scope | Correct scope binding, lifecycle, durable state and terminalization; residual scope authority is disproved by read-back. |
| AppContainer / ACL / Job confinement | Real applicable Windows sandbox/process control proves isolation, quiescence and cleanup; no unrestricted fallback. |
| Fail-closed audit lineage | Mutation-critical audit record durable before applicable side effect; missing audit blocks mutation. |
| Canonical repository firewall | Canonical `main` protected; explicit task execution workspace remains isolated; no caller-selected unsafe write path. |
| Operation/effect classification | Actual mutation effect is correctly represented for read/write/execute/firewall decisions; unknown effects fail closed. |
| Receipt and independent read-back | Returned Task/Run/Attempt/Slice/commit evidence matches durable canonical transport and actual Host outcome; uncertain outcome is not blindly replayed. |
| Long/uncertain routing | Representative CodeBuddy/Codex/full build/test is routed to provider-neutral guided CLI rather than an extended synchronous Hub-owned lifecycle. |

The proof is a sufficiency gate, **not** a blanket claim of zero defects or evidence for unrelated workloads. Source-level and CI evidence may support it but cannot substitute for required live Host observations.

### MRS-05 — Long-Agent Surface Retirement Program

| Field | Frozen program contract |
| --- | --- |
| Problem solved | After safe replacement/migration, obsolete Direct Codex and long-Agent-specific orchestration surfaces must be removed or narrowed without losing reusable security, handoff or evidence semantics. |
| Owner | **SentinelX capability/module owners** under individually approved DevForge Tasks; DevForge retains workflow, binding and receipt validation ownership. |
| Repository / runtime authority | **`bewaterhere-coder/sentinelx-cloud-core`** for separately scoped component source changes; any DevForge contract or project-registry changes remain DevForge-owned cross-repository Tasks. |
| Prerequisites | **MRS-01, MRS-02, MRS-03, and MRS-04 accepted and read back**; PR-019 baseline reconciliation separately verified; equivalent provider-neutral returned-evidence/read-back behavior proven before removing reusable Codex-specific validation; per-component consumers and disposition matrix revalidated. |
| Allowed scope | Separate capability-level reviewed retirement/SIMPLIFY Tasks, exact dependency/read-back inventory, safety regression and physical negative proof as applicable, orderly removal after consumer migration. |
| Forbidden scope | Broad delete/rewrite of all DEPRECATE items in one Task; deleting Direct Codex before the four accepted exits; deleting generic jobs/pending-results merely for async behavior; removing Host Mutation Scope, AppContainer, ACL/Job, audit or firewall by claiming they are "complex"; closing historical PRs without their owning Task authority; no-receipt completion claims. |
| Entry gate | Current acceptance/receipt artifacts for MRS-01 through MRS-04 all verified with no unresolved material conflict; candidate capability has exact consumer/read-back proof and its own approved Requirement/Plan. |
| Exit/acceptance evidence | Per-capability acceptance/merge receipts, before/after references, dependency and capability projection read-back, retained security negative tests, equivalent commit/receipt validation, no obsolete binding consumers, and no orphaned live authority. Program closes only after every explicitly admitted retirement Task is independently accepted or an explicit HOLD is recorded. |
| Dependency | MRS-04 → **MRS-05**. No retirement stage may bypass any earlier accepted exit. |
| Candidate follow-on DevForge Task | **Direct Codex Lifecycle Retirement & Provider-Neutral Evidence Extraction V1** — SentinelX repository as a future **program umbrella**, decomposed into separate capability-level DevForge Tasks before any source mutation. |
| Current status | **Not authorized to start.** This roadmap is not retirement permission. |

The PR-021 component matrix remains the retirement-disposition authority; this S03 program adds dependency and ownership gates only. S04 will freeze the no-shortcut retirement safety gates and concrete component-level prerequisites. **Nothing is removed in S03.**

## 7. S03 Completion Boundary

S03 completion requires this stage contract to be durable/readable on PR #23 and verified against the Approved Plan. It does **not**:

- complete MRS-01..MRS-05 program execution;
- accept or start any candidate successor Task;
- mutate `bewaterhere-coder/DevForge` or its project-binding registry;
- edit/rebase/close/merge PR #13/#14/#16/#19/#20;
- perform physical Host proof;
- remove Direct Codex or implement PR-020;
- change `src/`, `tests/`, `.github/workflows/`, deployment or release.

**Next Slice in this Task:** S04 — Retirement and Safety Gates. S04 must be separately authorized and will not be executed by the S03 command.


## 8. S04 Retirement and Safety Gates — No-Shortcut Contract

This section is an additional **fail-closed admission contract** under PR-021's frozen architecture and capability disposition. It does not implement the five stages, create their candidate Tasks, authorize an acceptance claim, delete source, change the DevForge project binding, close/merge another PR, install/restart an Agent or release SentinelX.

### 8.1 Retirement admission predicate

~~~text
Admit(MRS-05 exact-capability retirement)
  := ACCEPTED_AND_READBACK(MRS-01)
   ∧ ACCEPTED_AND_READBACK(MRS-02)
   ∧ ACCEPTED_AND_READBACK(MRS-03)
   ∧ ACCEPTED_AND_READBACK(MRS-04)
   ∧ VERIFIED(PR-019 baseline reconciliation)
   ∧ VERIFIED(equivalent provider-neutral evidence and actual consumers)
   ∧ APPROVED(exact component-level DevForge Task and Plan)
   ∧ VERIFIED(current canonical source ownership and Host security admission)
~~~

**All conditions are cumulative and cannot be waived by the roadmap.** Missing, stale, untrusted, contradictory or unreachable authority/receipt evidence is a blocker. A proposal, code review, S03 roadmap or source-level CI cannot substitute for an accepted owner-scoped successor result. In particular, MRS-05 depends on independently **accepted** MRS-01, MRS-02, MRS-03 and MRS-04 with durable read-back; the fact that this roadmap describes all five is not acceptance of any stage.

| Retirement gate | Required evidence and owner | Fail-closed response / forbidden shortcut |
| --- | --- | --- |
| **RG-01 — Reconciled active lineage** | MRS-01 owning DevForge Task acceptance/read-back; separately authorized #13/#14/#19/#20 decisions. #14 security-only source ownership resolved, #19 baseline revised, #20 development-timeout Durable Async HOLD durable; earlier candidates and receipts preserved. | Block architecture-conflicting expansion; PR #23 matrix alone cannot mutate, approve or close another PR. |
| **RG-02 — Guided CLI replacement accepted** | MRS-02 DevForge-owned acceptance of provider-neutral mode resolver, deterministic handoff, exact Task/PR/branch/Requirement/Plan/Slice/Run scope, forbidden actions, verification, returned commit/receipt/remote read-back; negative and no-authority-transfer cases. | Block migration/retirement. No Hub timeout extension, CodeBuddy/Codex Hub lifecycle, hidden generic background long-Agent path or automatic CLI invocation as a substitute. |
| **RG-03 — Binding migration accepted** | MRS-03 DevForge-owned Task receipt and before/after registry SHA/read-back showing migration of \`sentinelx-cloud-core\` from explicit \`direct/codex\` to the exact accepted MRS-02 routing; fail-closed provider selection and rollback evidence. | Block Minimal Runtime acceptance/retirement. No silent fallback to \`direct/codex\` or registry mutation from this SentinelX PR. |
| **RG-04 — Physical Minimal Runtime proof accepted** | MRS-04 separately accepted exact live Host/candidate evidence for structured projection, bounded read/write/short command/short verification, Mutation Scope admission/terminalization, AppContainer/ACL/Job, durable audit, operation/effect truth, canonical firewall, receipt/read-back and guided CLI routing of long work. | Block all retirement. Source tests, a mock, or Agent self-report cannot replace physical proof. Preserve previous approved service state. |
| **RG-05 — PR-019 stabilization baseline reconciled** | Exact PR-019 or successor owner-scoped Requirement/Plan/Acceptance receipt/read-back that protects security and short-runtime readiness **without requiring** the deprecated SentinelX-owned Direct Codex long-Agent lifecycle; preserve PR-019 candidate \`4ffb2dc312fac8d1030eb521641f6c61c33f11f0\` and Host Mutation Scope blocker findings. | Block Direct Codex retirement even if guided CLI exists. No history erasure or permanent long-Agent baseline requirement. |
| **RG-06 — Equivalent returned-evidence validation** | Compare old and new exact Task/PR/branch/Requirement/Plan/Slice/Run/Attempt, produced commit, expected remote SHA, CAS/non-force publication, uncertain-outcome independent read-back, receipt schema, stale/replayed result rejection and verified no-replay semantics. | Block removal of reusable Codex handoff, transport, result and receipt semantics until provider-neutral equivalence is accepted. No wholesale delete. |
| **RG-07 — Component-level Task only** | Exact consumer/dependency inventory, canonical current-main source ownership, independently approved DevForge Requirement/Plan/Slice, safe isolated candidate, acceptance Receipt, regression/negative proof and transport read-back for each retired/narrowed capability. | No global retirement Task authorizes all source removal; no automatic replay/cherry-pick of PR #14 candidate \`45dc99d15a23c499b4c1500fab60ed5e76475aeb\`. |
| **RG-08 — Retained security and external effects** | Read back Host-owned protected root/execution placement, no caller-selected path, canonical checkout \`main + clean\`, scope/ACL/Job/AppContainer, fail-closed audit, effect classification, firewall, terminalization/no residual authority and effect-specific Receipt. | Any missing security or Host Receipt blocks mutation. No protected \`D:\\coco\` carve-out, permission weakening, unrestricted shell fallback, silent credential change or unsafe canonical write. |

**Sequence invariants:** MRS-01 accepted before MRS-02; MRS-02 before MRS-03; MRS-03 before MRS-04; MRS-04 before MRS-05. RG-05 through RG-08 are *additional* necessary retirement gates, not alternative successor routes. Any new material architecture requirement must reenter the appropriate DevForge Requirement/Plan review instead of amending an accepted receipt.

### 8.2 Exact future component/capability Task boundaries

These are **descriptive candidate Task titles, not created Tasks**. The PR-021 Capability Disposition Matrix remains the authoritative classification.

| Future candidate DevForge Task | Disposition | Component and specific pre-removal / narrowing proof |
| --- | --- | --- |
| **Direct Codex Execution Provider Lifecycle Retirement V1** | **DEPRECATE** | \`handlers/direct_codex.py\`; all RG-01..08, zero remaining binding/consumer dependencies, accepted local-CLI replacement, physical security proof and PR-019 reconciliation. |
| **Codex ACL and Workspace Lifecycle Retirement V1** | **DEPRECATE** | \`direct_codex_acl.py\` and \`direct_codex_workspace.py\`; preserve generic short-mutation workspace isolation, Host-owned placement, ACL/Job/AppContainer and protected-root separation; prove no bounded consumer. |
| **Codex Discovery Retirement V1** | **DEPRECATE** | \`direct_codex_discovery.py\`; accepted CLI-side provider discovery/identity/error cases and no remaining SentinelX bounded dependency. |
| **Codex Persistence/Publication Lifecycle Retirement V1** | **DEPRECATE** | \`direct_codex_persistence.py\`; provider-neutral commit-production owner plus exact CAS/remote read-back/no-replay/receipt verification proven independently. |
| **Provider-Neutral Handoff Extraction V1** | **SIMPLIFY** | \`direct_codex_handoff.py\`; preserve complete identity/scope/forbidden-action/verification fields and no-authority-transfer semantics in accepted MRS-02 successor. |
| **Provider-Neutral Result and Receipt Verification V1** | **SIMPLIFY** | \`direct_codex_result.py\`; replacement has equivalent receipt/lineage validation, rejects missing/stale/forged results and independently checks return evidence. |
| **Canonical Transport and Read-back Extraction V1** | **SIMPLIFY** | \`direct_codex_transport.py\`; preserve PR/branch/expected-SHA/CAS/non-force and independently verified remote state; remove Codex-only bootstrap coupling after replacement. |
| **Bounded DevForge Host Bridge Narrowing V1** | **SIMPLIFY** | \`handlers/devforge_runtime.py\`; identify actual short-operation consumers and retain Host Mutation Scope, sandbox, audit, scoped execute, read-back. Remove only separately proven unneeded long-Agent surface. |
| **Short-Mutation Workspace Security Substrate Narrowing V1** | **SIMPLIFY** | PR #14 \`devforge_workspace_placement.py\` / \`devforge_workspace_materialization.py\` historical lineage; current canonical source topology and exact bounded consumers must be verified first. Historical candidate is evidence only. |

No single Task may interpret \`DEPRECATE\` as permission to delete every component. Each candidate independently requires its own DevForge Gate, changed-path scope and Receipt. If a component remains a live consumer dependency, it stays installed until the accepted replacement and safe retirement proof exist. If a candidate cannot prove a safe narrower owner, record HOLD rather than manufacture completion.

### 8.3 PR-021 KEEP / SIMPLIFY security boundary

**KEEP** at the semantic capability level, independent of module location:

- \`local_api.py\`, \`handlers/local_api.py\`: structured closed bounded projection and truthful availability;
- \`mutation_scope.py\`: Host-owned Mutation Scope admission, durable state, forward-compatible safe read/migration for additive schema fields, exact terminalization and no residual authority;
- \`mutation_audit.py\`: fail-closed audit recorded before mutation/process start;
- \`mutation_sandbox.py\`, \`windows_mutation_sandbox.py\`: AppContainer/ACL/Job confinement, exact scoped grants, revocation and no unrestricted fallback;
- \`operation_registry.py\`, \`canonical_repository_firewall.py\`: complete operation/effect classification, unknown-effect failure, protected canonical repo/main;
- \`verification_profile.py\`, \`verification_execution.py\`, \`verification_readiness.py\`, \`verification_runtime.py\`, \`handlers/scoped_script.py\`: admitted short verification and scoped mutation, without converting a Slice into a long Agent job.

**SIMPLIFY**, not indiscriminately delete: \`handlers/devforge_runtime.py\` as bounded Host bridge; generic \`handlers/exec.py\` and \`handlers/script.py\` with current independent consumers intact; PR #14 workspace security substrate as proved for short mutation; provider-neutral extracted handoff/transport/result verification.

**KEEP existing generic asynchronous capabilities:** \`jobs.py\`, \`pending_results.py\`, \`client.py\` background delivery and independent generic exec/script background consumers. The Minimal Runtime decision rejects **Hub-owned long development-Agent execution**, not all background execution. The PR #20 development-timeout-driven Durable Async proposal remains **HOLD**; that classification does not deprecate generic background completion/replay merely because it is asynchronous. Independent non-development running-job durability needs a new reviewed Requirement with a real consumer; no inherited authorization.

DevForge core slicing and Harness Slice consumption remain workflow/consumer responsibilities outside SentinelX's long-process lifecycle. One Slice need not fit a Hub request; its workload decides direct-short versus guided CLI.

### 8.4 Drift and fail-closed recovery

Before any future capability retirement, re-read canonical \`main\`, exact owner Task/PR/Plan, successor receipts, DevForge binding, actual Host authority, effect/receipt evidence and live consumers. **Stop** if any of these are missing, ambiguous, changed or contradicted:

1. Architecture or source ownership drift; unapproved long-Agent dependency; unresolved PR #14 current-main topology or PR #19 baseline.
2. Route/authority drift: unreviewed project binding, hidden direct/codex fallback, CLI instruction mistaken for permission, stale Task/Plan/Slice/Run/Attempt.
3. Security drift: reduced protected roots, caller-chosen workspace, corrupt MutationScope schema, audit/ACL/Job/AppContainer/terminalization gap, unknown effect, or canonical checkout write.
4. Evidence drift: missing produced commit/expected remote SHA, uncertain push without independent read-back, absent real Host proof, receipt mismatch or missing completion Receipt.
5. Scope drift: attempted bulk deletion, generic background jobs retired without independent proof, PR #14 historical code replayed, PR #20 resumed as a development timeout solution.

A blocked gate leaves the previously admitted provider/capability untouched: no silent disable/uninstall/restore/merge/rebase/credential change/permission widening. Resolve the cause through the owning Task's reviewed DevForge flow with evidence preserved; do not bypass the security boundary to make a task pass.

### 8.5 S04 verification and non-authority

~~~yaml
s04_gate_freeze:
  primary_sequence: [MRS-01, MRS-02, MRS-03, MRS-04, MRS-05]
  mrs05_requires_independent_accepted_readback: [MRS-01, MRS-02, MRS-03, MRS-04]
  pr019_baseline_reconciliation_required: true
  equivalent_commit_receipt_remote_readback_validation_required: true
  exact_component_devforge_tasks_required: true
  generic_async_background_deprecated_due_to_async_alone: false
  pr021_keep_and_simplify_security_preserved: true
  bulk_source_deletion_authorized: false
  project_binding_mutation_authorized: false
  direct_codex_disable_or_source_removal_authorized: false
  live_host_deployment_mutation_authorized: false
  candidate_successor_tasks_created: false
  next_task_slice: S05
~~~

S04 freezes documentation and safety gates only. S05 separately evaluates the whole roadmap against Requirement AC1–AC16 and performs final artifact/read-back verification. **S04 does not pre-execute S05.**
