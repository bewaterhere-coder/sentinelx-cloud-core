# PR-015 — Requirement Revision 2 / Downstream Impact Analysis

## Disposition

```yaml
task_id: PR-015-direct-codex-development-host-invocation-bridge-v1
change_classification: material_requirement_revision
source_command: "#开发 PR-015-direct-codex-development-host-invocation-bridge-v1 修订当前方案：采用 provider-owned deterministic commit-on-publish ..."
requirement_revision_before: 1
requirement_revision_after: 2
prior_stage: acceptance
new_stage: plan_review
prior_plan_revision: 2
new_plan_revision: 3
prior_acceptance: DecisionRequired
canonical_transport:
  type: github-pr
  repository: bewaterhere-coder/sentinelx-cloud-core
  pr_number: 15
  branch: task/direct-codex-development-host-invocation-bridge-v1
transport_preserved: true
project_binding_preserved: direct/codex
implementation_execution_authorized: false
```

## Human material decision resolved

Acceptance R1 exposed one material architecture decision: the real installed Codex Development Host performs bounded workspace edits and verification but does not create a Git commit. The user has now explicitly selected:

```text
provider-owned deterministic commit-on-publish
```

The direct Development Host still owns implementation edits and verification. SentinelX owns only bounded persistence/transport finalization after the Codex process completes successfully.

This explicit `#开发` command is the upstream human authority for that material decision. No model/provider inference is used.

## Requirement semantic delta

The previous contract stopped after Codex execution and transport readback and treated an uncommitted changed workspace as `implementation_not_persisted`.

Requirement Revision 2 adds one bounded persistence phase:

```text
exact admitted PR/branch/head
-> isolated execution checkout
-> Codex bounded workspace mutation + verification
-> provider revalidates Task/Run/Attempt/Slice + workspace + branch + expected head
-> provider inventories only eligible checkout changes
-> provider creates one deterministic provenance-bound commit
-> ordinary fast-forward publish to the same canonical PR branch
-> independent remote readback
-> persisted direct/codex success receipt
```

The provider does not become the Development Host. It acts as the fixed Git persistence broker for work already produced by Codex.

## Retained evidence

The following R2 evidence remains valid and MUST NOT be replayed merely because the persistence boundary changed:

- S01 bounded `devforge_direct_codex` provider schema, policy/readiness and provider-wide firewall/effect composition;
- S02 isolated workspace derivation, exact transport admission, active-user environment, fixed `@openai/codex` identity, Windows MIC containment and bounded process lifecycle;
- S03 exact Task/Run/Attempt/Slice/repository/PR/branch receipt validation and transport-drift negatives;
- real-host evidence that Codex executes correctly but leaves dirty/uncommitted work in the isolated checkout;
- PR-010 / PR-011 regression compatibility already established by the exact candidates.

These remain historical verified prerequisites for Plan R3.

## Invalidated as current authority

The following are preserved historically but are no longer current execution/acceptance authority:

- Plan R2 as the current Approved Plan;
- the Plan R2 Slice Set as the current executable Slice Set;
- S03 completion as sufficient evidence for final direct/Codex persistence closure;
- Acceptance R1 `DecisionRequired` as the current unresolved decision state.

Acceptance R1 remains the authoritative evidence that motivated Requirement Revision 2. Its material decision is now resolved by the current user command, but Acceptance must be run again after the new persistence slice is implemented and verified.

## New implementation delta

Plan R3 should introduce one new current implementation slice after review:

```text
S04 — Provider-Owned Deterministic Persistence & Canonical Publish Closure
```

S04 may reuse S01–S03 verified prerequisites. It must not replay or rewrite them unless implementation reality proves a retained assumption stale.

Formal executable Slice Set compilation remains Plan Review-owned. This impact record may describe the proposed S04 delta but does not authorize implementation.

## Security invariants preserved

The revision MUST NOT introduce:

```text
generic Git or shell surface
caller-supplied git argv/pathspec/commit message
replacement branch or PR
force push
canonical checkout mutation
caller-selected workspace
permission or credential expansion
operator_unrestricted
Hub mutation
provider rebinding
automatic retry after uncertain publish
```

Provider persistence is restricted to the already-derived isolated checkout and exact canonical branch/head lineage.

## Authorization / workflow effect

The prior Durable Development Authorization was correctly suspended at Acceptance R1. The present explicit registered `#开发` command resolves the material decision and may reactivate the same Task-scoped authorization for Requirement Revision 2.

Because Plan R2 is invalidated as current authority, the authorization's old Plan binding must be cleared until Plan R3 is approved. Transport binding remains unchanged.

The Task returns to `plan_review` only after Requirement R2 and Plan R3 are durably persisted and read back. No implementation is authorized by this requirement-revision command.

No completion claim.
