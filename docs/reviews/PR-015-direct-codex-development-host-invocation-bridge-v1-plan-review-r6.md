# PR-015 — Direct Codex Development Host Invocation Bridge V1 — Plan Review R6

## Review State

```yaml
task_id: PR-015-direct-codex-development-host-invocation-bridge-v1
review_target: plan
requirement_revision: 2
requirement_blob_sha: da925b61d2badd548d4310d96666dd55f9480067
plan_revision: 6
plan_blob_sha: 2bcea2a44f88e51c8b9378ba6297b61897e638da
reviewed_task_head: 3f7decad66dbb9daf24387eb0cc25dd76d3d539e
result: Approved
runtime:
  devforge_version: 2.82.0
  devforge_revision: e16948004601829813f19dbef4cf3cc018606ff9
  review_contract: "1.3"
  slicing_contract: "1.1"
  bootstrap_override_contract: "1.0"
repository_reality:
  canonical_main: 018b78ca20984176d53fbe90039dc795a7f2742f
  canonical_pr: 15
  canonical_branch: task/direct-codex-development-host-invocation-bridge-v1
  project_provider: direct
  project_adapter: codex
next_gate: implementation
next_expected_actor: implementer
```

## Decision

**Approved.**

Requirement Revision 2 remains Ready. Plan R6 closes the final Plan-local checkout/persistence canonicalization-authority gap without changing Requirement semantics or canonical transport.

Approval authorizes compilation of exactly one current implementation Slice:

```text
S04 — Provider-Owned Deterministic Persistence & Canonical Publish Closure
```

S01-S03 remain historical verified prerequisites from the prior Plan lineage and are not replayed or re-authorized as current executable Slices.

Approval does not create the Task-scoped CodeBuddy bootstrap override, execute product implementation, mutate the live Agent, change the project binding, modify the production Hub, widen permissions, or alter canonical transport.

## R5 Finding Re-evaluation

### F1 — CheckoutCanonicalizationAuthorityIncomplete

**Closed.**

Plan R6 moves the canonicalization/filter trust boundary before the first worktree materialization.

It now requires:

- remote clone/fetch object acquisition without worktree checkout;
- capture and durable readback of the allowlisted safe normalization snapshot before checkout;
- provider inspection index seeded from exact `expected_remote_sha`;
- expected-tree effective attribute inspection before checkout;
- rejection of any effective custom `filter` assignment across tracked paths before an external filter can execute;
- system/global attribute authority neutralized;
- `.git/info/attributes` absent/empty;
- provider-clamped checkout with hooks/fsmonitor/submodule recursion/editor/pager/prompt disabled;
- exact same frozen snapshot reused for later provider temporary-index clean staging;
- versioned `.gitattributes` mutation rejected in V1;
- snapshot/attribute drift between checkout and persistence fail-closed.

This makes checkout and clean conversion one reversible provider-owned canonicalization contract rather than two unrelated Git environments.

## Review Checks

### Solution direction

**Pass.**

Provider-owned deterministic commit-on-publish remains the correct closure for the real-host finding that Codex edits and verifies but does not create a commit.

Codex remains the Development Host. SentinelX remains the bounded invocation/persistence/transport enforcement layer.

### Scope control

**Pass.**

Plan R6 does not authorize:

- generic Git/shell/exec projection;
- caller Git argv/pathspec/commit metadata;
- force or force-with-lease;
- replacement branch/PR;
- canonical checkout mutation;
- permission/credential expansion;
- project rebinding;
- production Hub mutation;
- duplication of PR-013 repository transaction authority.

### Candidate-tree authority

**Pass.**

The Codex-owned checkout index is explicitly untrusted.

Candidate construction uses a provider-owned temporary index seeded from the exact admitted parent tree and only provider-validated eligible paths.

Versioned `.gitattributes` mutation is deliberately unsupported in V1, preventing mid-attempt clean-semantics changes.

### Checkout / clean canonicalization

**Pass.**

R6 now freezes one pre-checkout canonicalization snapshot and reuses it during persistence.

The planned verification observes the actual required behavior:

- custom filter marker process cannot execute at checkout;
- Windows CRLF checkout representation re-canonicalizes to exact parent LF blob when semantically unchanged;
- one-line semantic edit remains canonical without whole-file EOL churn;
- binary content is not text-normalized;
- supported working-tree-encoding remains deterministic.

### Deterministic candidate identity / recovery

**Pass.**

The provider recovery journal freezes all commit-SHA inputs before candidate creation and defines explicit recovery states through `prepared`, `tree_ready`, `candidate_ready`, local-ref-ready, `publish_intent`, and `published`.

Same-attempt recovery must reconstruct the bit-identical candidate SHA.

After uncertain publication, remote readback is authoritative and automatic re-push is forbidden.

### Publication semantics

**Pass.**

Publication is ordinary fast-forward only, with exact parent/head checks, exact canonical branch, no alternate remote, no merge/rebase and no force mode.

Success requires independent remote readback equal to the provider candidate SHA.

### Verification realism

**Pass.**

The Plan requires:

- focused adversarial tests;
- real Windows checkout/filter negative proof;
- real CRLF roundtrip proof;
- real active-user Codex fixture;
- real provider-owned commit;
- exact fixture branch ordinary push;
- independent remote readback;
- canonical checkout unchanged.

Mock-only evidence cannot satisfy these physical boundaries.

### Retained evidence / no replay

**Pass.**

S01-S03 remain valid historical prerequisites:

- S01 provider/policy/firewall contract;
- S02 workspace, active-user Codex, containment and exact transport bootstrap;
- S03 identity/receipt/readback and real-host non-persistence finding.

Plan R6 changes only the persistence closure and the checkout materialization controls needed by S04.

### Runtime drift

**Pass.**

Plan R6 recorded DevForge 2.82.0 at `748004cc...`. Current DevForge remains 2.82.0 at `e1694800...`.

The intervening Runtime delta is unrelated evolution documentation and does not change Plan Review, slicing, bootstrap override, durable authorization, or execution semantics used here.

## Slice Compilation Guidance

Compile exactly one current Slice:

### S04 — Provider-Owned Deterministic Persistence & Canonical Publish Closure

It must include:

- pre-checkout canonicalization snapshot and expected-tree filter admission;
- provider-clamped checkout;
- provider-owned temporary candidate index;
- exact canonical clean staging;
- recovery journal;
- deterministic commit identity;
- ordinary fast-forward publication;
- independent readback;
- persistence receipt extension;
- real Windows/direct-Codex physical proof.

Historical S01-S03 references may appear as prerequisite evidence only. They are not current executable Slice states.

## Bootstrap Entry Requirement

The project binding remains:

```yaml
provider: direct
adapter: codex
```

The repaired persistence capability is required for the canonical provider to execute this exact S04 to completion, so the self-host relation remains valid.

The prior CodeBuddy override was bound to Plan R2 and is expired. It cannot be reused.

After this review compiles and read-backs the exact R6 Slice Set, the only admissible bootstrap authority request is:

```text
#开发引导执行 PR-015-direct-codex-development-host-invocation-bridge-v1 direct:codebuddy
```

That command must bind the exact Plan R6 blob and exact R6 Slice Set. This review does not create the override.

## Gate Result

```text
Plan Review R6: Approved
Requirement Revision: 2 / Ready
Plan Revision: 6 / Approved
Plan Approved: true
Current Slice Set: compile exact R6 S04 set
Next Gate: implementation
Current Slice: S04 / pending
Bootstrap Override: required before S04 execution
Next Expected Actor: implementer
```

No product implementation or bootstrap override is executed by this review.
