---
task_id: PR-023-minimal-runtime-successor-roadmap-v1
title: SentinelX Minimal Runtime Successor Roadmap V1
project_id: sentinelx-cloud-core
repository: bewaterhere-coder/sentinelx-cloud-core
requirement_revision: 1
development:
  stage: plan_review
  gates:
    requirement_ready: true
    plan_approved: false
    acceptance_approved: false
    completion_verified: false
  plan_revision: 1
  implementation_authorized: false
  blocking_findings: []
  next_expected_actor: reviewer
transport:
  type: github-pr
  pr_number: 23
  branch: task/minimal-runtime-successor-roadmap-v1
  base_branch: main
artifacts:
  plan: docs/plans/PR-023-minimal-runtime-successor-roadmap-v1-plan.md
  provisional_bootstrap: docs/checkpoints/minimal-runtime-successor-roadmap-v1-provisional-bootstrap.md
  authority_architecture: docs/architecture/sentinelx-minimal-runtime-boundary-v1.md
  authority_disposition_matrix: docs/architecture/sentinelx-capability-disposition-matrix-v1.md
  authority_predecessor_requirement: docs/requirements/PR-021-minimal-runtime-complexity-reduction-boundary-v1.md
requirement_readiness:
  result: Ready
  refinement_depth: Standard
  ui_semantics:
    applicability: NotApplicable
  visual_fidelity:
    applicability: NotApplicable
---

# Requirement

## Problem

PR-021 froze SentinelX's target architecture as a secure, bounded, short-duration local capability bridge and explicitly rejected further expansion of SentinelX into a long-running development-Agent lifecycle owner.

PR-021 also froze one primary five-step successor sequence, but that sequence is currently architecture guidance rather than a durable execution roadmap with per-step ownership, dependency gates, active-work reconciliation, entry/exit criteria, and retirement preconditions.

Without a canonical successor roadmap, existing open development lineages can continue to pull SentinelX back toward the architecture PR-021 rejected. In particular, open work includes runtime materialization, Direct Codex/CodeBuddy execution, stabilization requirements, Durable Async lifecycle work, and compatibility/security work with different relationships to the Minimal Runtime boundary.

The next development decision must therefore be sequencing and reconciliation, not another execution-runtime feature.

## Goal

Create one durable, fresh-session-recoverable **SentinelX Minimal Runtime Successor Roadmap V1** that turns PR-021's frozen five-step successor sequence into an actionable program while preserving strict ownership and safety boundaries.

The roadmap must:

1. preserve PR-021 as architectural authority;
2. inventory current open SentinelX development lineages against current canonical `main`;
3. classify each material active lineage as continue, reshape, hold, supersede-candidate, close-candidate, or independent/non-conflicting, with evidence;
4. define exactly five ordered successor stages;
5. define the owning repository/runtime and entry/exit evidence for each stage;
6. make cross-repository boundaries explicit, especially DevForge-owned project-binding changes;
7. prevent Direct Codex / long-Agent-specific retirement before replacement, binding migration, and Minimal Runtime proof are accepted;
8. define which follow-on work requires separate DevForge Tasks rather than being implemented by this roadmap task.

This task is planning/control-plane work. It does not itself implement the successor runtime changes.

## Canonical Authority

This task inherits, and MUST NOT reinterpret, the accepted PR-021 architecture:

- `docs/architecture/sentinelx-minimal-runtime-boundary-v1.md`
- `docs/architecture/sentinelx-capability-disposition-matrix-v1.md`
- `docs/requirements/PR-021-minimal-runtime-complexity-reduction-boundary-v1.md`
- PR #21 acceptance/completion evidence.

The following frozen rule remains authoritative:

> SentinelX owns security, projection, bounded short execution, and verifiable read-back. SentinelX does not own the lifecycle of long-running development Agents.

The Hub/local_api request window remains a short interaction/control-plane window, not a long development job budget.

## Frozen Primary Successor Sequence

The roadmap MUST preserve exactly this primary order:

### MRS-01 — Active Work Reconciliation

Reconcile open/active SentinelX work against the Minimal Runtime architecture before creating new runtime expansion.

At minimum, the roadmap must evaluate every currently open SentinelX PR at the task's evidence baseline.

Known fixed architectural constraints:

- PR-014: current long-Agent/workspace-bootstrap direction must not continue blindly; preserve reusable security/workspace-isolation substrate while reshaping or holding orchestration-specific work.
- PR-019: stabilization evidence remains valuable, but the Stable Baseline must not permanently require a SentinelX-owned long-Agent Direct Codex lifecycle.
- PR-020: Durable Async Runtime remains HOLD as a development-timeout solution unless a new independent non-development requirement reopens it.
- PR-021: completed predecessor / architecture authority; never treated as active implementation work.

The roadmap may classify other open PRs as compatible, independent, reshape-required, or hold-required only from repository evidence.

This stage does not authorize closing, merging, rebasing, editing, or superseding those PRs.

### MRS-02 — Provider-Neutral Guided CLI Routing & Handoff

Define and implement, through a separate successor Task, the provider-neutral guided/semi-interactive CLI route for long or duration-uncertain development work.

The handoff contract must carry at least:

- repository identity;
- canonical DevForge Task ID;
- PR / branch identity when applicable;
- workflow stage;
- exact Requirement reference/revision;
- exact Approved Plan reference/revision when applicable;
- Slice / Run / Attempt identity when applicable;
- allowed mutation scope;
- forbidden actions;
- verification requirements;
- expected commit / receipt / read-back evidence;
- explicit statement that handoff text grants no new authority.

The user/local CLI owns the long process lifetime. ChatGPT/DevForge resumes only from returned durable evidence.

Short bounded work remains eligible for SentinelX direct execution when the Minimal Runtime resolver admits it.

### MRS-03 — DevForge Execution Binding Migration

After guided CLI routing is accepted, migrate the `sentinelx-cloud-core` DevForge project execution binding away from SentinelX-owned Direct Codex long-Agent lifecycle semantics.

The current canonical DevForge project registry binds SentinelX to `provider: direct`, `adapter: codex`.

This migration is **DevForge-owned cross-repository state**. The SentinelX roadmap may define the requirement and dependency, but this task MUST NOT directly mutate `bewaterhere-coder/DevForge`.

Migration must preserve:

- canonical repository identity;
- Task/PR/branch transport authority;
- isolated execution workspace requirements where applicable;
- No Receipt, No Completion Claim;
- returned commit / receipt / read-back validation;
- no silent provider fallback.

### MRS-04 — SentinelX Minimal Runtime Proof

Prove the target boundary on real Host reality after MRS-01 through MRS-03 are accepted.

The proof must demonstrate that SentinelX is sufficient for its retained responsibilities without requiring a long-Agent execution lifecycle.

At minimum the proof must cover:

- structured local capability projection;
- bounded read;
- bounded file mutation;
- short command execution;
- short verification;
- Host Mutation Scope;
- applicable sandbox/AppContainer/ACL/Job confinement;
- fail-closed audit lineage;
- canonical repository mutation protection;
- exact effect/operation classification sufficient for safety decisions;
- receipt/read-back verification;
- correct routing of long/uncertain development work to guided CLI rather than synchronous Hub ownership.

The proof is a product/runtime sufficiency gate, not a claim that SentinelX has no defects.

### MRS-05 — Long-Agent Surface Retirement Program

Only after MRS-01 through MRS-04 are accepted may retirement/simplification of long-Agent-specific SentinelX surfaces begin.

Retirement must occur through explicit per-capability DevForge Tasks and preserve component-level preconditions from the PR-021 disposition matrix.

No broad delete/refactor task may collapse all `DEPRECATE` or `SIMPLIFY` items into one unreviewed mutation.

Direct Codex removal is forbidden until:

- guided CLI replacement is accepted;
- DevForge execution binding migration is accepted;
- PR-019 baseline conflict is reconciled;
- Minimal Runtime proof is accepted;
- equivalent evidence/read-back behavior exists for any reusable validation semantics being removed or extracted.

## Active Work Reconciliation Output

The roadmap implementation must include a revisioned matrix for all open SentinelX PRs visible at the implementation evidence baseline.

Each row must include:

- PR / Task identity;
- current stage/state;
- relationship to PR-021 architecture;
- disposition;
- preserved evidence/assets;
- blocking conflict, if any;
- required successor stage;
- whether the PR itself may continue before the successor roadmap stage is complete;
- explicit note that classification is not mutation authority.

The matrix must distinguish:

- security/bounded-runtime work that remains valid;
- long-Agent orchestration work that conflicts with Minimal Runtime ownership;
- independent compatibility work;
- historical evidence that should be preserved even when its original target is superseded.

## Scope

In scope:

- documentation and durable roadmap artifacts;
- current repository / PR reality inventory;
- dependency graph and ordering;
- owner/repository boundaries;
- successor Task candidate definitions;
- entry and exit gates;
- retirement preconditions;
- architecture-conflict reconciliation rules;
- acceptance evidence for the roadmap itself.

Out of scope:

- product source changes under `src/`;
- test implementation changes;
- active PR merge/close/edit/rebase operations;
- SentinelX Agent deployment/restart;
- Hub or production mutation;
- DevForge repository mutation;
- project execution-binding mutation;
- Direct Codex removal;
- PR-020 implementation;
- automatic creation/start of all successor Tasks;
- release;
- workspace GC;
- GitHub Actions / repository-hosted CI additions or workflow changes.

## Non-Goals

This task does not:

- redesign PR-021 architecture;
- re-open whether Hub should own long development jobs;
- require zero async/background capability in SentinelX;
- deprecate generic `jobs.py` / pending-result delivery solely because they are asynchronous;
- weaken Host Mutation Scope, sandbox, audit, firewall, permission, or receipt boundaries;
- impose an arbitrary wall-clock threshold for "short";
- make DevForge Slice identity equal to one Hub request;
- move DevForge workflow ownership into SentinelX;
- claim successor Tasks are complete merely because roadmap entries exist.

## Requirement Rules

R1. PR-021 architecture and disposition matrix are authoritative predecessor evidence.

R2. Exactly one primary five-step successor order must be produced: MRS-01 → MRS-02 → MRS-03 → MRS-04 → MRS-05.

R3. MRS-01 must reconcile current open work before new long-runtime implementation is admitted.

R4. MRS-02 must be provider-neutral; CodeBuddy/Codex may be examples/consumers, not semantic owners.

R5. Guided CLI text is context/identity transfer only and never expands execution authority.

R6. Direct-short SentinelX capability remains valid for genuinely bounded work.

R7. MRS-03 is DevForge-owned cross-repository mutation and must require a separate owning-repository Task.

R8. MRS-04 must prove retained security and read-back semantics physically enough to support the Minimal Runtime claim.

R9. MRS-05 may not start before MRS-01..MRS-04 are accepted.

R10. DEPRECATE/HOLD classifications do not themselves authorize deletion, disablement, merge, close, or binding mutation.

R11. Generic background execution/delivery is evaluated by its independent product requirement, not automatically removed.

R12. No Receipt, No Completion Claim applies to every successor implementation and to this roadmap task's own durable artifacts.

R13. Canonical `main` must remain free of unreviewed task mutation; this task uses PR #23 transport only.

R14. No GitHub Actions / CI workflow may be created or modified to satisfy this task.

R15. Successor-resolution output may recommend exactly one primary next Task direction, but this roadmap task must not auto-start it.

## Acceptance Criteria

AC1. A canonical Minimal Runtime Successor Roadmap artifact exists and is read-back verified.

AC2. The roadmap cites PR-021 ADR, disposition matrix, Requirement, and completion evidence as authority.

AC3. The roadmap contains exactly five ordered primary stages matching MRS-01..MRS-05.

AC4. Every stage has owner, target repository/runtime, prerequisites, entry gate, exit evidence, and prohibited shortcuts.

AC5. A current open-PR reconciliation matrix exists for the SentinelX evidence baseline.

AC6. PR-014 is explicitly prevented from blindly continuing long-Agent/workspace-bootstrap scope while reusable security substrate is preserved.

AC7. PR-019 is explicitly reconciled so SentinelX stability does not permanently depend on SentinelX-owned Direct Codex long-Agent lifecycle.

AC8. PR-020 is explicitly HOLD for development-timeout motivation and cannot progress unchanged under this roadmap.

AC9. Guided CLI contract requirements include identity, scope, forbidden actions, verification and returned evidence without granting new authority.

AC10. Direct-short routing remains part of the target runtime for bounded work.

AC11. DevForge execution-binding migration is explicitly identified as cross-repository DevForge-owned work and is not mutated by this task.

AC12. Minimal Runtime proof criteria cover projection, bounded execution, mutation scope, sandbox/confinement, audit, firewall/effect truth, and receipt/read-back.

AC13. No Direct Codex / long-Agent-specific retirement is authorized before MRS-01..MRS-04 acceptance.

AC14. Retirement is decomposed into explicit component/capability Tasks rather than one broad deletion.

AC15. No product source, test source, deployment, active related PR, DevForge binding, or GitHub Actions workflow is mutated by this task.

AC16. The roadmap and evidence are recoverable from a fresh session without relying on chat history.

## Strongest Counterargument

A unified Durable Async Runtime could preserve full end-to-end automation and remove manual guided-CLI steps.

That remains technically coherent, but PR-021 already adjudicated the ownership trade-off: using Durable Async primarily to keep long development Agents inside SentinelX would add lifecycle persistence, restart reconciliation, replay/outcome state, provider adaptation, and scheduler-like responsibilities to the bridge.

This task therefore treats PR-020 as HOLD unless a distinct non-development product requirement independently proves the need.

## Risks

- Existing PRs may contain mixed security substrate and obsolete long-Agent orchestration; coarse closure could discard useful work.
- A guided CLI successor could accidentally become provider-specific and recreate Direct Codex coupling outside SentinelX.
- DevForge binding migration could be attempted before equivalent returned-evidence validation exists.
- "Minimal" could be misread as removing security controls. Security complexity is explicitly preserved.
- Open PR reality may drift after this Requirement; implementation must re-read current state before writing the roadmap.

## Completion Boundary

Successful `#开发` for this task means only:

- canonical Task identity frozen as `PR-023-minimal-runtime-successor-roadmap-v1`;
- Requirement Revision 1 durable/read-back verified;
- Plan R1 durable/read-back verified;
- PR #23 / branch lineage verified;
- stage = `plan_review`;
- `requirement_ready=true`;
- `plan_approved=false`;
- next expected actor = reviewer.

It does not implement the roadmap or any successor runtime change.
