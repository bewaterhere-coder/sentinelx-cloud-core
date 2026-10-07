# PR-015-direct-codex-development-host-invocation-bridge-v1 — Plan R4

Requirement: `docs/requirements/PR-015-direct-codex-development-host-invocation-bridge-v1.md`, revision 2.

Status: **Pending Plan Review**. No implementation authorization.

## 0. Planning baseline

```yaml
sentinelx_main: 018b78ca20984176d53fbe90039dc795a7f2742f
planning_task_head_before_r3: d67923bd7df7f45186f6852c414d2cc74f5321d6
devforge_main: fb05202b03fb5e3d0147b9b30f43b49c2404b072
devforge_version: 2.81.0
project_execution_binding:
  provider: direct
  adapter: codex
canonical_transport:
  repository: bewaterhere-coder/sentinelx-cloud-core
  pr: 15
  branch: task/direct-codex-development-host-invocation-bridge-v1
requirement_revision: 2
prior_plan_revision: 3
prior_acceptance: DecisionRequired
material_decision:
  selected: provider_owned_deterministic_commit_on_publish
```

Requirement Revision 2 is a material architecture/scope change produced by the explicit user `#开发` command after Acceptance R1. The exact Task and canonical transport are preserved.

## R4 remediation delta

Plan R4 preserves Requirement Revision 2 and the provider-owned deterministic commit-on-publish direction. It changes only the two Plan-local boundaries rejected by Plan Review R3:

1. **Candidate-tree authority:** the Codex-owned checkout index is never trusted. Candidate construction uses a provider-owned temporary index seeded from the exact admitted parent tree, and eligible file content is converted to Git objects through no-filter plumbing before the candidate tree is written.
2. **Candidate identity / crash recovery:** every commit-SHA input is frozen in a durable provider recovery journal before commit creation. Same-attempt recovery reconstructs or verifies the exact same candidate SHA across pre-publish and uncertain-publish interruption points.

No Requirement Revision 3 is introduced. S01-S03 remain retained verified prerequisites. Only the S04 persistence delta remains proposed for implementation after Plan R4 approval.


## 1. Retained implementation baseline

Plan R4 does **not** replay S01-S03. Their verified implementation remains the baseline:

- bounded `devforge_direct_codex` builtin provider and closed model-facing schema;
- direct/codex execution identity preserved;
- provider-wide local-api repository-effect/firewall composition;
- fixed active-user `@openai/codex` + Node/`codex.js` execution chain;
- isolated provider-derived checkout;
- exact PR/branch/expected-head admission;
- real Windows MIC containment and bounded process-tree lifecycle;
- active-user environment reuse through `CreateEnvironmentBlock`;
- exact Task/Run/Attempt/Slice/repository/PR/branch receipt validation;
- fail-closed malformed receipt, local-only, timeout and transport-drift behavior.

Historical product candidate: `a84db15a8770599718a665fd9c201c7b82b3dd91`.

Acceptance R1's real-host finding is retained as the disconfirming fixture: Codex edits and verifies successfully but does not commit, so persistence must be provider-owned.

## 2. R4 architecture delta

### D13 — Provider-owned persistence broker

After Codex exits successfully, `devforge_direct_codex` performs one bounded persistence phase before any success receipt.

The persistence broker is **not** a generic Git interface and is not model-facing. It accepts no caller Git argv, pathspec, commit message, remote URL, author identity, branch or executable.

Required sequence:

```text
Codex process success
-> revalidate isolated workspace identity
-> verify actual branch == canonical branch
-> verify local HEAD == expected_remote_sha before provider commit
-> re-read remote canonical branch == expected_remote_sha
-> inventory eligible worktree/index delta
-> construct one provider-owned commit
-> ordinary fast-forward push to exact canonical branch
-> independent remote readback
-> persisted direct/codex receipt
```

If any precondition changes, fail closed before publication.

### D14 — Provider-owned candidate tree; checkout index is untrusted

The Codex execution checkout's current Git index is **implementation-host state, not provider authority**. The provider MUST NOT use that index as the source of the candidate tree and MUST NOT rely on `git add` against that index to enforce the eligible path boundary.

Candidate construction uses a provider-owned temporary index/state file outside the implementation candidate set.

Required sequence:

```text
verify local HEAD == expected_remote_sha
-> inventory worktree delta against expected_remote_sha
-> validate eligible relative paths/modes/types
-> create provider temporary index outside candidate worktree artifacts
-> seed temporary index from expected_remote_sha tree
-> materialize blobs for eligible paths with no-filter plumbing
-> apply only provider-validated path updates/deletions to temporary index
-> write candidate tree
-> verify candidate tree against eligible inventory + exclusions
```

Candidate authority rules:

- ignore any pre-existing staged state in the Codex-owned checkout index;
- unmerged state in the checkout or temporary index fails closed;
- unsupported gitlink/submodule mode/add/delete/update fails closed in V1;
- every eligible path is repository-relative, canonicalized and proven inside the exact execution checkout;
- symlink entries are represented only as validated Git symlink objects; following a symlink outside the checkout to obtain content is forbidden;
- provider control/recovery/log/evidence artifacts are outside the candidate set and are explicitly rejected if they appear in the candidate tree;
- deletions are derived from the validated delta, never from caller pathspecs;
- executable/symlink/regular-file modes are derived from validated repository/worktree evidence and checked against the candidate tree;
- the final candidate tree must equal: exact admitted parent tree plus exactly the provider-validated eligible delta.

### No-filter / no-external-execution rule

Candidate blob/tree construction must not invoke repository/user-controlled clean/smudge/process filters, hooks, signing, aliases, fsmonitor helpers, pagers, editors or interactive prompts.

The preferred implementation path is fixed Git plumbing equivalent to:

```text
temporary GIT_INDEX_FILE
git read-tree <expected-parent>
git hash-object -w --no-filters --stdin   # provider supplies exact validated bytes
git update-index --index-info/cacheinfo    # provider-generated entries only
git write-tree
git commit-tree                            # fixed metadata; no commit hooks/signing
```

Exact subprocess spelling is implementation-owned, but the selected commands must be fixed provider operations and must be invoked with provider-owned config/environment clamps sufficient to disable external execution surfaces, including at minimum:

- hooks disabled via provider-owned empty hooks path / plumbing that does not run commit hooks;
- commit/tag signing disabled;
- fsmonitor disabled;
- pager/editor disabled;
- terminal prompting disabled;
- no caller/repository alias expansion;
- no shell command boundary.

Because blob creation uses `--no-filters`, repository `.gitattributes` filter/process drivers do not get execution authority during persistence.

The provider records `eligible_change_count`, normalized path-set digest and candidate tree SHA in recovery/receipt evidence without returning secret environment data.

### D15 — Fixed Git persistence primitives and config clamp

Persistence uses a closed internal Git broker only. It is not model-facing and accepts no caller Git argv, pathspec, commit message, author, timestamp, config key, remote URL or branch.

Allowed semantic operations are limited to:

```text
fixed remote readback
validated worktree inventory
provider temporary-index/tree construction
provider deterministic commit-object construction
provider-local candidate ref update
ordinary fast-forward push exact candidate -> exact canonical branch
independent remote readback
```

The broker reuses the existing fixed active-user Git credential/context boundary only for operations that require authenticated remote access. Credential values are never copied, returned or logged.

All local candidate construction is executed without shell wrappers and with provider-owned configuration clamps. Hooks, signing, filters, fsmonitor, editor/pager and terminal prompt execution are not authority sources.

No generic Git helper/API is registered with the model or exposed to arbitrary callers.

### D16 — Durable deterministic candidate identity and recovery journal

The provider creates exactly one candidate commit identity for one admitted Run/Attempt[/Slice] when eligible changes exist.

A provider recovery journal is stored **outside the implementation commit candidate set** under provider-owned execution state keyed by the exact repository/Task/Run/Attempt/Slice identity.

Before candidate commit creation, the provider MUST atomically persist and read back a `prepared` record containing every non-tree commit-SHA input:

```yaml
identity:
  repository:
  task_id:
  run_id:
  attempt_id:
  slice_id:
transport:
  canonical_pr:
  canonical_branch:
  expected_remote_sha:
commit_identity:
  fixed_author_name:
  fixed_author_email:
  fixed_committer_name:
  fixed_committer_email:
  author_date_utc_seconds:
  committer_date_utc_seconds:
  timezone: "+0000"
  message_bytes_digest:
  serialization_version:
state: prepared
```

The provider-owned timestamp is created once for the attempt **before any candidate commit object is created**, persisted atomically, read back, and then reused forever for that same attempt. A retry must never sample a new timestamp for an existing attempt identity.

After candidate-tree construction and before `commit-tree`, the provider atomically persists/read-backs:

```yaml
state: tree_ready
candidate_tree_sha:
eligible_paths_digest:
```

The candidate commit is then a pure deterministic function of:

```text
parent = expected_remote_sha
tree = candidate_tree_sha
author/committer identity = fixed provider constants/versioned identity
author/committer dates = prepared journal values
message bytes = fixed serialization(Task/Run/Attempt/Slice)
```

After commit-object creation, the provider computes/verifies the exact SHA and persists `candidate_ready` with `candidate_commit_sha`.

### Same-attempt recovery state machine

Recovery is fail-closed and same-attempt only:

1. **prepared, no tree recorded** — candidate may be rebuilt from current validated worktree; no commit identity existed yet.
2. **tree_ready, commit SHA absent** — use the recorded tree + prepared metadata to reconstruct the bit-identical candidate commit SHA. Do not resample metadata.
3. **candidate_ready, local execution ref not updated** — verify the recorded candidate object/tree/parent/provenance and update only the provider-owned execution ref.
4. **local candidate ref ready, no publish intent** — revalidate remote == expected head, then persist `publish_intent` before the first push.
5. **publish_intent / push outcome uncertain** — do not create another commit and do not automatically push again. Perform remote readback only:
   - remote == candidate -> persist `published`;
   - remote == expected head -> persist/return `publication_uncertain_or_not_observed`; no automatic retry;
   - remote == other -> `DirectCodexTransportDrift`.
6. **published** — verify remote still equals candidate and return/reconstruct the same persisted receipt; never create a second candidate.

The recovery journal is not chat/session state, is not part of the implementation commit, and is durably written/read back before crossing each externally meaningful boundary.

Focused verification must prove that the same attempt yields a bit-identical candidate SHA across all interruption points above and cannot manufacture a second candidate commit.

### D17 — CAS-style publication without force

Immediately before publication, re-read the canonical remote branch and require:

```text
remote_head == expected_remote_sha
candidate_parent == expected_remote_sha
actual_branch == canonical_branch
```

Before the first push, the provider MUST persist/read back the recovery journal state `publish_intent` with the exact candidate SHA and expected remote head. This is the durable boundary used to distinguish a never-attempted push from an uncertain externally visible push.

Publication uses an ordinary fast-forward push only.

Forbidden:

- `--force`;
- `--force-with-lease`;
- replacement branch/PR;
- alternate remote;
- tag transport;
- automatic merge/rebase.

If the remote moves, return `DirectCodexTransportDrift`. A local provider-created candidate may remain diagnostic evidence but is not a success receipt.

After push, independently read the remote branch. Success requires:

```text
remote_head_readback == provider_candidate_sha
```

No automatic retry is permitted after an uncertain externally visible push. When recovery observes `publish_intent`, it performs remote readback before any further mutation. Readback decides whether the exact candidate landed; if publication is not observed, the attempt remains non-success and requires an explicit higher-level recovery/new attempt rather than a hidden second push.

### D18 — Receipt extension

The structured result/receipt adds bounded persistence evidence:

```yaml
persistence:
  mode: provider_owned_commit_on_publish
  base_head:
  eligible_change_count:
  changed_paths_digest:
  candidate_commit:
  commit_provenance_digest:
  published: true|false
transport:
  canonical_pr:
  canonical_branch:
  actual_branch:
  expected_remote_sha:
  remote_head_readback:
  consistent:
```

A valid persisted success requires provider `direct`, adapter `codex`, exact identity echo, exact canonical transport, candidate commit creation, ordinary publish and remote readback consistency.

A no-change outcome and an unpersisted dirty-worktree outcome remain distinct from persisted implementation success.

## 3. Security and authority constraints

Plan R4 preserves all R2 security boundaries.

The implementation MUST NOT:

- enable generic `exec`;
- expose generic Git or shell operations;
- accept caller Git argv/pathspec/commit metadata;
- use `operator_unrestricted`;
- mutate the canonical checkout;
- create replacement branch/PR;
- force push;
- widen filesystem or command allowlists;
- copy/read/log credentials;
- modify the production Hub;
- reinterpret the project binding as `host-runtime`;
- duplicate PR-013 `repository_transaction_v1` authority.

The persistence broker is exact-task transport finalization for the direct/Codex adapter only.

## 4. Current implementation delta

Plan Review should compile exactly one new current implementation slice if R4 is approved:

### Proposed S04 — Provider-Owned Deterministic Persistence & Canonical Publish Closure

Expected product surfaces:

- `src/sentinelx_core/direct_codex_persistence.py` or equivalent bounded internal module;
- focused changes in `handlers/direct_codex.py`;
- focused changes in `direct_codex_result.py`;
- reuse/minimal extension of `direct_codex_transport.py` / `user_git.py` fixed primitives;
- focused direct-Codex persistence tests.

Authorized implementation delta:

- provider-derived eligible-change inventory;
- fixed deterministic commit construction;
- exact-parent candidate creation;
- ordinary fast-forward canonical publish;
- independent remote readback;
- persistence receipt fields and negatives;
- exact-candidate real Windows direct/Codex persistence proof.

Historical S01-S03 implementation should not be rewritten except where a minimal interface change is required to compose S04.

## 5. Verification strategy

### Focused deterministic tests

Required cases:

1. dirty eligible checkout -> one provider candidate commit with exact parent;
2. pre-staged excluded path in the Codex-owned index does **not** enter the provider candidate tree;
3. provider temporary index is seeded from the exact admitted parent and contains only validated eligible delta;
4. repository/user configured clean/smudge/process filters cannot execute during candidate blob/tree construction;
5. hooks/signing/fsmonitor/editor/pager/terminal prompts cannot execute through the persistence path;
6. provider control/recovery artifacts are not committed;
7. unmerged index/worktree state fails closed;
8. unsupported gitlink/submodule mutation fails closed;
9. symlink/path traversal cannot read or commit content outside the execution checkout;
10. canonical checkout branch/head/index/worktree metadata remain unchanged;
11. remote head drift before publish fails without push;
12. ordinary push succeeds only to the exact canonical branch;
13. remote readback mismatch fails receipt validation;
14. no eligible changes does not manufacture an empty implementation commit;
15. malformed persistence receipt fails;
16. local dirty/uncommitted work cannot be success;
17. same admitted attempt reconstructs a **bit-identical candidate SHA** after interruption at `prepared`, `tree_ready`, `candidate_ready` and local-ref-ready boundaries;
18. crash after `publish_intent` performs readback only and never creates another candidate or automatic second push;
19. remote readback after uncertain push correctly distinguishes candidate published / base still present / transport drift;
20. existing S01-S03 direct-Codex, firewall, scoped-verification and user-scoped Git regressions remain green.

### Physical Windows proof

The exact candidate must run the real installed `@openai/codex` against a bounded fixture repository/branch and prove:

```text
real Codex modifies isolated checkout
-> provider inventories exact change
-> provider creates candidate commit
-> provider ordinary-pushes to exact fixture canonical branch
-> remote readback == candidate
-> receipt provider=direct / adapter=codex / persisted=true
-> canonical checkout unchanged
```

The physical proof must also run a remote-drift negative and prove no replacement transport/force path is used.

### Canonical GitHub transport

Implementation execution itself remains on PR #15. Completion of S04 requires product-code side effects and its receipt on that exact branch.

## 6. Bootstrap execution boundary

The persistent project binding remains:

```yaml
provider: direct
adapter: codex
```

The previous CodeBuddy override is expired and bound to Plan R2. It cannot be reused.

Because the direct/Codex bridge cannot yet persist its own implementation work, an approved Plan R4 may require a **new explicit Task-scoped bootstrap override** bound to Plan R4 and its reviewed Slice Set:

```text
#开发引导执行 PR-015-direct-codex-development-host-invocation-bridge-v1 direct:codebuddy
```

That command is not authorized by this Plan and must be invoked explicitly after Plan Review approval.

No fallback target is allowed.

## 7. Acceptance boundary after S04

A fresh `#开发验收` must evaluate Requirement Revision 2 against the exact product candidate.

Acceptance must include:

1. exact candidate tests/regressions;
2. live Windows Agent activation when separately admitted;
3. live `local_api.list/describe` exposure of `devforge_direct_codex`;
4. real active-user Codex invocation;
5. physical workspace containment negative proof;
6. real provider-owned candidate commit and ordinary canonical publish;
7. exact PR/branch/head remote readback;
8. valid persisted direct/Codex receipt;
9. canonical checkout `main + clean` readback;
10. PR-013 direct/Codex provider-admission recovery proof without Task/Plan/Slice/project-binding change.

Acceptance R1 is historical evidence only and cannot approve Requirement Revision 2.

## 8. Risks and fail-closed handling

### Repository-controlled Git behavior

Risk: hooks/signing/config could execute unintended behavior during commit.

Mitigation: fixed provider Git primitives, explicit hook/signing disablement, no shell, no caller config, focused adversarial tests.

### Dirty provider artifacts

Risk: handoff/log/control files could leak into the implementation commit.

Mitigation: keep provider artifacts outside candidate worktree where practical; derive and validate eligible path inventory; verify staged tree before commit.

### Publish race

Risk: remote branch moves between Codex completion and publication.

Mitigation: exact remote read before commit/publish, exact parent, ordinary fast-forward push, independent readback, no retry after uncertainty.

### Duplicate persistence on recovery

Risk: interrupted same-attempt recovery creates multiple commits.

Mitigation: stable provenance + persisted candidate identity; detect/reuse exact prior candidate instead of recommitting.

### Scope expansion

Risk: persistence broker becomes a generic Git executor.

Mitigation: private fixed operations only, no model-facing Git fields, no generic command projection, provider identity remains direct/Codex.

## 9. Plan Review questions

Plan Review R4 must specifically verify:

- the Codex-owned checkout index is explicitly untrusted and cannot inject pre-staged paths;
- provider candidate construction uses a temporary provider-owned index/tree seeded from the exact admitted parent;
- eligible file bytes reach Git objects through a no-filter path and external filters/hooks/signing/fsmonitor/editor/pager/prompt surfaces cannot execute;
- the final candidate tree is proven to equal parent + exactly the validated eligible delta;
- every commit-SHA input is frozen before commit creation or is derivable from canonical attempt identity;
- recovery journal state is outside the candidate set and durably read back before commit/publication boundaries;
- same-attempt recovery reconstructs the bit-identical candidate SHA across all defined interruption windows;
- `publish_intent` prevents hidden automatic re-push after uncertain publication;
- provider-owned persistence remains consistent with Requirement R2 and does not become a generic Git surface;
- ordinary fast-forward publication plus independent readback satisfies the canonical transport CAS requirement without force;
- retained S01-S03 evidence remains valid and only S04 is newly implementation-authorized after approval;
- a new Plan-R4-bound bootstrap override is required before S04 execution.

Approval must compile a new current Slice Set for Plan R4. This Plan does not self-approve and does not authorize implementation.
