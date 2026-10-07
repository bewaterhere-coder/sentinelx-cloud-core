# PR-015-direct-codex-development-host-invocation-bridge-v1 — Plan R5

Requirement: `docs/requirements/PR-015-direct-codex-development-host-invocation-bridge-v1.md`, revision 2.

Status: **Pending Plan Review**. No implementation authorization.

## 0. Planning baseline

```yaml
sentinelx_main: 018b78ca20984176d53fbe90039dc795a7f2742f
planning_task_head_before_r3: d67923bd7df7f45186f6852c414d2cc74f5321d6
devforge_main: 329438b69ab0946175b805788b0412384e343e0b
devforge_version: 2.81.0
project_execution_binding:
  provider: direct
  adapter: codex
canonical_transport:
  repository: bewaterhere-coder/sentinelx-cloud-core
  pr: 15
  branch: task/direct-codex-development-host-invocation-bridge-v1
requirement_revision: 2
prior_plan_revision: 4
prior_acceptance: DecisionRequired
material_decision:
  selected: provider_owned_deterministic_commit_on_publish
```

Requirement Revision 2 is a material architecture/scope change produced by the explicit user `#开发` command after Acceptance R1. The exact Task and canonical transport are preserved.

## R5 remediation delta

Plan R5 preserves Requirement Revision 2, the provider-owned deterministic commit-on-publish direction, and all boundaries accepted in Plan R4. It changes only the canonical blob-materialization gap rejected by Plan Review R4.

Core rule:

```text
external repository/user process authority is forbidden
BUT
Git-safe canonical clean semantics must still be preserved
```

R5 therefore replaces raw `hash-object --no-filters` worktree-byte hashing with a provider-owned temporary-index staging path that uses Git's builtin path-aware clean conversion **only after** all external/custom clean filters are rejected and all nonessential Git config/attribute sources are clamped.

To invert the exact Windows checkout representation safely, the provider captures the small allowlisted checkout-normalization configuration (`core.autocrlf`, `core.eol`, `core.safecrlf`) immediately after exact checkout bootstrap and before Codex starts. That snapshot is provider-owned execution evidence and is reused during candidate materialization/recovery.

No Requirement Revision 3 is introduced. S01-S03 remain retained verified prerequisites. Only S04 remains proposed after Plan R5 approval.

## 1. Retained implementation baseline

Plan R5 does **not** replay S01-S03. Their verified implementation remains the baseline:

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

## 2. R5 architecture delta

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

### D14 — Provider-owned candidate tree with safe canonical clean conversion

The Codex execution checkout's Git index remains **untrusted implementation-host state**. Candidate authority uses a provider-owned temporary index seeded from the exact admitted parent.

R5 additionally freezes how worktree bytes become canonical Git blobs on Windows.

#### D14.1 — Checkout-normalization snapshot before Codex

Immediately after the exact execution checkout is established and before Codex starts, the provider reads only the following safe scalar Git settings under the active-user Git context:

```text
core.autocrlf
core.eol
core.safecrlf
```

Unset values are normalized to their Git defaults. No arbitrary config keys are accepted or returned.

The provider persists/read-backs this normalization snapshot outside the implementation candidate set and binds it to the exact repository/Task/Run/Attempt/Slice + expected head.

The persistence phase reuses this exact snapshot; it does not reread mutable global values and does not allow Codex/caller values to override it.

#### D14.2 — Attribute/config authority clamp

Candidate materialization runs with provider-owned local Git configuration isolation:

- system attributes disabled;
- global attributes file redirected to a provider-owned empty file;
- system/global Git config excluded for local candidate construction except the explicitly replayed safe normalization snapshot;
- `.git/info/attributes` must be absent or empty; otherwise V1 fails closed;
- hooks path is provider-owned empty;
- signing disabled;
- fsmonitor disabled;
- pager/editor disabled;
- terminal prompts disabled;
- no shell wrapper;
- no caller Git config.

Versioned repository `.gitattributes` files remain product input because they are part of the candidate worktree/tree.

For every eligible path, before staging the provider resolves the effective attributes through fixed path-aware Git attribute inspection under the same clamped attribute source.

If effective `filter` is anything other than unspecified/unset, V1 fails closed **before any clean filter can execute**.

Supported builtin clean semantics include:

- text/eol normalization;
- binary/no-text behavior;
- builtin `ident` behavior when applicable;
- Git-supported `working-tree-encoding` conversion.

Any unsupported/custom clean semantic or process-backed filter fails closed rather than silently hashing raw bytes.

#### D14.3 — Candidate construction

Required sequence:

```text
verify local HEAD == expected_remote_sha
-> verify normalization snapshot identity
-> inventory worktree delta against expected_remote_sha
-> validate eligible relative paths/modes/types
-> verify unversioned attribute sources are absent/disabled
-> resolve/freeze effective eligible-path attributes
-> reject any external/custom filter semantics
-> create provider temporary GIT_INDEX_FILE outside candidate set
-> seed temporary index from expected_remote_sha tree
-> stage only provider-derived literal eligible paths into that temporary index
   using Git builtin path-aware clean conversion under the clamped normalization snapshot
-> write candidate tree
-> verify candidate tree == parent tree + exactly validated canonical eligible delta
```

The fixed staging operation may use `git add`/equivalent builtin index update against the provider temporary index because external process filters have already been rejected and execution-producing config surfaces are clamped.

The Codex-owned original index is never read as candidate authority.

#### D14.4 — Canonicalization invariants

The provider MUST prove:

1. an unchanged tracked file whose Windows worktree representation differs only because of checkout-induced CRLF expansion re-materializes to the **same parent blob SHA**;
2. a real edit to such a CRLF worktree file produces canonical content with the semantic edit but without whole-file line-ending churn;
3. binary paths preserve exact bytes and do not receive text normalization;
4. supported `working-tree-encoding` paths are converted by Git's builtin clean semantics, not a caller/external process;
5. custom/external filter attributes fail before filter execution;
6. a change to versioned `.gitattributes` is included only as an eligible product change and its effective attribute snapshot is digested/revalidated before candidate tree finalization;
7. any normalization/attribute snapshot drift during persistence fails closed.

The provider records the normalization snapshot digest, effective-attribute digest, eligible path digest and candidate tree SHA in recovery/receipt evidence without exposing user environment or credentials.

### D15 — Fixed Git persistence primitives and config clamp

Persistence uses a closed internal Git broker only. It is not model-facing and accepts no caller Git argv, pathspec, commit message, author, timestamp, config key, remote URL or branch.

Allowed semantic operations are limited to:

```text
fixed safe-config snapshot read
fixed effective-attribute inspection
fixed remote readback
validated worktree inventory
provider temporary-index construction
provider-clamped builtin clean staging of exact eligible paths
provider deterministic commit-object construction
provider-local candidate ref update
ordinary fast-forward push exact candidate -> exact canonical branch
independent remote readback
```

Local candidate construction excludes arbitrary system/global configuration and replays only the allowlisted checkout-normalization snapshot needed to preserve canonical clean semantics.

Remote authenticated publication continues to reuse the existing fixed active-user Git credential/context boundary. Credential values are never copied, returned or logged.

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
clean_semantics:
  checkout_normalization_snapshot_digest:
  effective_attributes_digest:
  info_attributes_empty: true
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

The candidate tree is valid only when its recorded normalization/attribute digests still match. The candidate commit is then a pure deterministic function of:

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

Plan R5 preserves all R2 security boundaries.

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

Plan Review should compile exactly one new current implementation slice if R5 is approved:

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

1. provider captures `core.autocrlf/core.eol/core.safecrlf` after checkout and reuses the same snapshot during persistence;
2. parent LF blob + checkout-induced Windows CRLF worktree with no semantic edit re-materializes to the exact parent blob SHA;
3. one-line semantic edit in that CRLF worktree file yields canonical LF blob content with only the semantic edit, not whole-file EOL churn;
4. binary fixture preserves exact bytes with no text normalization;
5. supported `working-tree-encoding` fixture round-trips through Git builtin clean conversion deterministically;
6. effective custom `filter` attribute fails closed before its marker process can execute;
7. global/system attributes are disabled for local candidate construction and non-empty `.git/info/attributes` fails closed;
8. pre-staged excluded path in the Codex-owned index does not enter the provider candidate tree;
9. provider temporary index is seeded from the exact admitted parent and contains only validated canonical eligible delta;
10. hooks/signing/fsmonitor/editor/pager/terminal prompts cannot execute through the persistence path;
11. provider control/recovery artifacts are not committed;
12. unmerged index/worktree state fails closed;
13. unsupported gitlink/submodule mutation fails closed;
14. symlink/path traversal cannot read or commit content outside the execution checkout;
15. normalization/attribute snapshot drift during persistence fails closed;
16. canonical checkout branch/head/index/worktree metadata remain unchanged;
17. remote head drift before publish fails without push;
18. ordinary push succeeds only to the exact canonical branch;
19. remote readback mismatch fails receipt validation;
20. no eligible changes does not manufacture an empty implementation commit;
21. malformed persistence receipt fails;
22. local dirty/uncommitted work cannot be success;
23. same admitted attempt reconstructs a **bit-identical candidate SHA** after interruption at `prepared`, `tree_ready`, `candidate_ready` and local-ref-ready boundaries;
24. crash after `publish_intent` performs readback only and never creates another candidate or automatic second push;
25. remote readback after uncertain push correctly distinguishes candidate published / base still present / transport drift;
26. existing S01-S03 direct-Codex, firewall, scoped-verification and user-scoped Git regressions remain green.

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

The physical proof must additionally use a tracked text fixture whose Windows worktree representation is CRLF while the parent Git blob is LF. It must prove an unchanged path canonicalizes to the parent blob SHA and a one-line real edit remains LF-canonical without whole-file EOL churn.

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

Because the direct/Codex bridge cannot yet persist its own implementation work, an approved Plan R5 may require a **new explicit Task-scoped bootstrap override** bound to Plan R5 and its reviewed Slice Set:

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

Plan Review R5 must specifically verify:

- the Codex-owned checkout index remains explicitly untrusted;
- provider candidate construction still uses a temporary provider-owned index seeded from the exact admitted parent;
- safe checkout normalization config is captured before Codex and replayed deterministically during persistence;
- system/global attribute/config execution authority is clamped and `.git/info/attributes` cannot silently influence candidate semantics;
- effective custom `filter` attributes are rejected before any external process can execute;
- Git builtin text/eol, binary, ident and supported working-tree-encoding clean semantics remain available;
- Windows CRLF checkout bytes canonicalize back to the parent LF blob when semantically unchanged;
- a small real edit does not become whole-file EOL churn;
- the final candidate tree is proven to equal parent + exactly the validated canonical eligible delta;
- every commit-SHA input remains frozen before candidate creation or derivable from canonical attempt identity;
- recovery journal state remains outside the candidate set and same-attempt recovery reconstructs the bit-identical candidate SHA;
- `publish_intent` continues to prevent hidden automatic re-push after uncertain publication;
- provider-owned persistence remains a bounded direct/Codex transport broker rather than a generic Git surface;
- retained S01-S03 evidence remains valid and only S04 is newly implementation-authorized after approval;
- a new Plan-R5-bound bootstrap override is required before S04 execution.

Approval must compile a new current Slice Set for Plan R5. This Plan does not self-approve and does not authorize implementation.
