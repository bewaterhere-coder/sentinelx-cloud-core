# PR-014 — Minimal Short-Mutation Workspace Security Substrate — Plan R8

## Authority and identity

```yaml
task_id: PR-014-devforge-execution-workspace-materialization-bridge-v1
requirement_revision: 4
plan_revision: 8
stage: plan_review
plan_approved: false
implementation_authorized: false
transport: {type: github-pr, pr_number: 14, branch: task/devforge-execution-workspace-materialization-bridge-v1, base_branch: main}
supersedes: Plan R7 / rejected Review R7
retained_historical_slices: [S01, S02]
historical_s02_candidate: 45dc99d15a23c499b4c1500fab60ed5e76475aeb
historical_product_replay: forbidden
```

## Decision

Consume canonical PR-021 Minimal Runtime Boundary V1. PR-014 no longer provides `development.execution_workspace_materialize` as a full Git checkout/Direct Development Host handoff or any long-Agent lifecycle. Retain only explicitly justified bounded short-mutation workspace isolation/security. The R1–R7 long-agent source capsule, bootstrap, user-level ACL handoff and full materializer designs have **no active implementation authority**. Preserve old docs as historical records only.

## Stage 0 — Read-only canonical implementation topology gate (blocking)

1. Fetch current canonical `main` SHA and tree, identify the current authoritative SentinelX implementation repository/path/package, effective Host policy schema, and actual bounded short-mutation call site. Check PR-021's disposition; compare branch and main without replay.
2. Explain source-file absence on main (observed at `cd42e371f18056327c1d8b744f8956a76bc11541`) and whether code intentionally moved or was lost; do not presume restoration. Bind source paths to this new readback.
3. If implementation ownership is not demonstrably resolved, produce a durable `CanonicalMainImplementationSurfaceMismatch` blocker/disposition and **stop before product mutation**. No speculative branch normalization, cherry-pick or broad restore. Same PR #14 remains transport unless a separately approved requirement change supersedes it.
4. Verify actual short-mutation consumer requires a *new* dedicated DevForge workspace placement. If existing canonical substrate suffices, scope the change to evidence/compatibility, not duplicative implementation.

## Proposed bounded slices (conditional; reviewer must compile after gate)

**S03A — Canonical topology and consumer proof (read-only).** Current-main tree/readback, ownership, existing security primitives, short-mutator use case, exact candidate source files and safe integration strategy. Pass required before S03B authorization.

**S03B — Minimal provider security delta (only if S03A passes).** Use existing Host-owned canonical repository inventory and separate effective DevForge execution placement root (preferred `D:\SentinelX\devforge-workspaces`, only if actually admitted); strictly disjoint from `D:\coco` protected root and canonical roots. Maintain path-free semantic identity and exact closed scope. Patch only the current canonical implementation surface actually evidenced by S03A. Never weaken protected roots, carve out or caller-select paths. Repair compatible MutationScope durable-schema reads, preserve `runtime_read_authority_roots`, fail closed on unknown authority-bearing fields. Audit START before writes; AppContainer/ACL/Job where applicable; terminalize authority after bounded readback. Exclude full checkout, source capsule, Development Host handoff/Agent lifecycle.

**S03C — Focused verification and receipt.** Unit checks for placement collision, traversal, drift, protected-root/canonical firewall, schema round-trip and fail-closed, audit ordering, negative access and cleanup; one bounded exact Host proof when authority and environment allow. No CI workflow creation. Physical Host acceptance is separate; receipt required for completion claims.

Review may reject or shrink the conditional slices. `S03B` and `S03C` are *not* currently executable.

## Non-negotiable evidence

- Existing S01/S02 checkpoints, receipts and S02 commit `45dc99d15a23c499b4c1500fab60ed5e76475aeb` remain immutable historical provenance; do not replay or auto-promote.
- PR #14 and current branch retained; canonical `main + clean`; all product edits in admitted DevForge execution workspace after authorization.
- No generic Git/shell/filesystem fallback, caller-supplied root, new MCP broad write projection, credential expansion or permission expansion.
- All changed files and authoritative Host effects require deterministic readback and receipts. Hosted CI non-gating per prior operator choice.
- Failed topology admission yields no product writes.

## Review criteria

Plan Reviewer shall check Requirement R4 priority over historical text; PR-021 compliance; fresh main ownership proof or explicit blocking S03A; independence of Host canonical source and execution placement; durable state migration security; no historical replay; and a correct slice dependency graph. Only explicit Approved Review can authorize a compiled Slice Set; subsequent implementation cannot skip S03A.

## Canonical next action

```text
#开发评审 PR-014-devforge-execution-workspace-materialization-bridge-v1
```
