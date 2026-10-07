# PR-015 — Direct Codex Development Host Invocation Bridge V1 — Plan Review R3

## Review State

```yaml
task_id: PR-015-direct-codex-development-host-invocation-bridge-v1
review_target: plan
requirement_revision: 2
requirement_blob_sha: 3cdd78a871ba3ad9165836f77190893421568142
plan_revision: 3
plan_blob_sha: 6552329d7fc07526569956db8ebee477fcd08af3
reviewed_task_head: f726b5d04f65d429593b519f89d8db158e345904
result: Rejected
finding_classification: plan_local
runtime:
  devforge_version: 2.81.0
  devforge_revision: fb05202b03fb5e3d0147b9b30f43b49c2404b072
  review_contract: "1.3"
repository_reality:
  canonical_main: 018b78ca20984176d53fbe90039dc795a7f2742f
  canonical_pr: 15
  canonical_branch: task/direct-codex-development-host-invocation-bridge-v1
  project_provider: direct
  project_adapter: codex
next_gate: plan_review_rejected
next_expected_actor: planner
```

## Decision

**Rejected.**

Requirement Revision 2 is Ready and the selected provider-owned deterministic commit-on-publish direction is accepted. Plan R3 has two implementation-shaping P0 gaps that must be closed before Implementation Ready.

No Requirement rewrite is requested.

## F1 — Candidate-tree trust boundary is incomplete

Plan R3 correctly requires provider-derived eligible paths and exclusion of provider control artifacts, but D13-D15 still describe the candidate as being built from the existing worktree/index state:

```text
inventory eligible worktree/index delta
-> stage provider-derived eligible paths
-> write tree / create commit
```

The existing Git index is inside the Codex execution checkout and can already contain staged entries created by the Development Host. That index therefore cannot be treated as provider authority.

Without an explicit clean candidate-index boundary, a pre-staged path can survive path filtering or influence the resulting tree even when the provider intends to stage only the validated eligible set.

Plan R4 must freeze the candidate-tree construction boundary:

1. do **not** trust the Codex-owned/current checkout index as candidate authority;
2. construct the candidate using a provider-owned temporary index or equivalent isolated plumbing state seeded from the exact admitted parent tree;
3. populate that candidate index/tree only from the provider-validated eligible path set;
4. verify the resulting tree contains no excluded provider artifact, unmerged entry, unsupported gitlink/submodule transition, or path outside the exact checkout;
5. ensure repository/user Git configuration cannot invoke external clean/smudge filters, hooks, signing, credential prompts, aliases, fsmonitor or other repository-controlled process execution during candidate construction;
6. either use plumbing that bypasses filters (for example a no-filter blob/tree construction path) or explicitly prove the selected fixed Git sequence cannot execute those external mechanisms;
7. add adversarial tests with a pre-staged excluded file and configured filter/hook/signing surfaces proving they cannot enter or execute through the persistence path.

The actual worktree remains implementation input from Codex. The candidate index/tree must be provider-owned evidence.

## F2 — Deterministic commit recovery identity is incomplete

D16 says the commit uses a "provider-owned timestamp/provenance value that is persisted for the attempt and reused on same-attempt recovery", but it does not freeze where that value comes from or how recovery works across the critical crash windows.

This matters because Git commit SHA includes author/committer metadata and timestamps. A crash after candidate creation but before persistence-state checkpointing could cause the same Run/Attempt to create a second different commit.

Plan R4 must define a deterministic/recoverable identity protocol:

1. every commit-SHA input must be derivable from canonical attempt inputs or from provider state that is durably written **before** candidate creation;
2. the author/committer identity, author/committer dates, parent, tree and message serialization must be stable for the same admitted Run/Attempt/Slice;
3. same-attempt retry before publication must reconstruct or verify the exact same candidate SHA rather than create another candidate;
4. recovery after "commit created / local ref not updated", "local ref updated / push not attempted", and "push outcome uncertain" must be explicitly defined;
5. after an uncertain push, remote readback remains authoritative and no second push/commit is attempted until the exact candidate publication state is resolved;
6. candidate/recovery state must live outside the implementation commit candidate set and must not depend on mutable chat/session state;
7. focused tests must prove same-attempt bit-identical candidate reconstruction and no duplicate candidate across each interruption point.

A merely "persisted timestamp" without a pre-commit durability/reconstruction rule is not sufficient.

## Accepted Plan R3 direction

The following should be preserved in Plan R4:

- provider-owned deterministic commit-on-publish;
- Codex remains the Development Host;
- project binding remains direct/codex;
- S01-S03 remain retained verified prerequisites and are not replayed;
- exactly one new implementation delta slice is expected;
- no generic Git/shell model-facing surface;
- no caller Git argv/pathspec/message/remote/branch;
- no canonical checkout mutation;
- no replacement branch/PR;
- no force or force-with-lease;
- ordinary fast-forward publication only;
- remote-head CAS/readback;
- no empty commit to manufacture success;
- no automatic retry after uncertain external publication;
- previous CodeBuddy override remains expired and cannot be reused.

## Gate Result

```text
Plan Review R3: Rejected
Requirement Revision: 2 / Ready
Plan Revision: 3 / Rejected
Plan Approved: false
Implementation Authorized: false
Formal Plan R3 Slice Set: not compiled
Current Gate: plan_review_rejected
Next Actor: planner
```

No product implementation, new bootstrap override, live Agent mutation, transport mutation or Acceptance action is authorized by this review.

## Required Plan R4 delta

1. freeze a provider-owned candidate index/tree construction path independent from the Codex-controlled checkout index and external Git execution surfaces;
2. freeze deterministic candidate-SHA/recovery semantics across all pre-publish and uncertain-publish interruption points.

No Requirement Revision 3 is needed.
