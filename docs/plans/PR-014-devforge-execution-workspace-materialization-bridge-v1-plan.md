# PR-014 — Plan R9: Read-only Canonical Topology Reconciliation

## Binding
```yaml
task_id: PR-014-devforge-execution-workspace-materialization-bridge-v1
requirement_revision: 4
plan_revision: 9
status: ready_for_plan_review
implementation_authorized: false
canonical_pr: 14
branch: task/devforge-execution-workspace-materialization-bridge-v1
historical_s01_s02: evidence_only_no_replay
candidate: 45dc99d15a23c499b4c1500fab60ed5e76475aeb
```

## Scope and decision

This Plan remedies rejected R8 finding `IncompleteExecutableSliceAdmission`. It contains **one independently verifiable read-only slice, S03A only**. No conditional S03B/S03C implementation is approved, proposed as an executable slice, or silently inherited from R8. This is a governance/evidence investigation under Requirement R4 and canonical PR-021 Minimal Runtime Boundary V1. PR #14 branch and Task identity remain unchanged.

## Exact proposed slice S03A — Canonical topology and bounded-consumer evidence

```yaml
slice_id: S03A
objective: Prove current canonical runtime source ownership, repository topology, and necessity of additional short-mutation workspace placement.
depends_on: []
allowed_effects: [repository.read, canonical_git_metadata_read, documentation_only_receipt_write_on_existing_pr_branch]
forbidden_effects: [product_mutation, host_mutation, main_mutation, rebase, cherry_pick, source_restoration, shell_fallback, source_capsule, materialize_workspace, direct_agent_bootstrap, s01_s02_replay]
outputs:
  - current-main-implementation-topology-readback
  - short-mutation-consumer-necessity-matrix
  - branch-main-integration-disposition
  - durable-s03a-decision-and-evidence-receipt
checkpoint_required: true
```

### Deterministic procedure

1. Read exact current GitHub `main` SHA, tree, build/package entrypoints, source directories and PR-021 Architecture; compare PR #14 branch lineage and mergeability. Record source absence/movement without guessing deletion rationale.
2. Find the **actual authoritative installed/canonical product implementation location** and how current Host policy, MutationScope, AppContainer/Job, audit and canonical mutation firewall map to it. Distinguish evidence, historical branch code, active installed runtime and current `main`. Do not infer one from another. If unavailable, record `CanonicalMainImplementationSurfaceMismatch` as unresolved.
3. Identify an actual bounded synchronous short-mutation consumer, with source/capability contract and why existing policy/runtime cannot serve it; distinguish necessary dedicated DevForge execution placement from obsolete user-level Development Host handoff.
4. Produce one evidence table listing exact current refs, missing paths, dependency ownership, protected-root policy constraints, and whether separate Host-owned source and execution placement are necessary. Evaluate MutationScope known additive field `runtime_read_authority_roots` compatibility as research only.
5. Persist evidence/decision receipt to this PR branch, then read back exact blob/commit. Outcome must be one of `TopologyAndConsumerProven`, `NoAdditionalProductDeltaNeeded`, or `DecisionRequired/Blocked`, with justification and explicit safe integration/disposition. If unresolved, stop; **no product mutation**.
6. S03A completion denotes completion of **this reconnaissance Plan only**, not overall Task completion or acceptance of the original materialization bridge. Any subsequent source mutation requires a separately revised Plan, Review, compiled Slice Set, and explicit implementation authority on a verified canonical source surface.

### Verification

- Exact GitHub current-main SHA and relevant tree/file/commit references read back; exact PR head and divergence evidence.
- Consumer evidence must identify actual bounded API/call site or explicitly fail; negative findings are permitted as valid read-only results.
- Every claimed Host effective policy fact is backed by current authoritative policy readback; otherwise mark `unverified`.
- Receipt includes identity, current source refs, observed topology, decision, unknowns, no mutation declaration and transport commit/blob readback.
- Cross-check historical S01/S02 artifacts and `45dc99d15a23c499b4c1500fab60ed5e76475aeb` as provenance only.
- No edits to product source, current main, Host configuration, CI workflows or permissions.

## R8 finding closure

`IncompleteExecutableSliceAdmission` is addressed at **Plan-local** level by removing conditional S03B/S03C from the active slice scope. The Review may compile a one-slice S03A Slice Set with no unproven product-path dependencies. The unresolved real-world topology remains the subject of S03A, not an excuse to preapprove product mutation.

## Preserved invariants

Host-owned canonical source vs independent DevForge placement, no weakening `D:\coco` protected root, no carve-outs or caller paths, exact mutation scope and durable schema migration semantics, audit START, AppContainer/Job and firewall remain Requirement R4 obligations **for any future mutation**, but are not implemented in S03A. Historical R8 rejection, prior plans, receipts and candidates remain immutable.

## Next action

```text
#开发评审 PR-014-devforge-execution-workspace-materialization-bridge-v1
```
