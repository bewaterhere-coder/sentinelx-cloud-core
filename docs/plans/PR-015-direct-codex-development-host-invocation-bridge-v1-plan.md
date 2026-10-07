# PR-015-direct-codex-development-host-invocation-bridge-v1 — Plan R6

Requirement: `docs/requirements/PR-015-direct-codex-development-host-invocation-bridge-v1.md`, revision 2.

Status: **Accepted / Ready for Merge**. Plan R6 was approved; implementation, Acceptance R8, and merge finalization are verified. Semantic Plan content below is historical design intent.

## 0. Planning baseline

```yaml
sentinelx_main: 018b78ca20984176d53fbe90039dc795a7f2742f
planning_task_head_before_r3: d67923bd7df7f45186f6852c414d2cc74f5321d6
devforge_main: 748004cc3ec3932e5c4106e0d62ff06b19c5f883
devforge_version: 2.81.0
project_execution_binding:
  provider: direct
  adapter: codex
canonical_transport:
  repository: bewaterhere-coder/sentinelx-cloud-core
  pr: 15
  branch: task/direct-codex-development-host-invocation-bridge-v1
requirement_revision: 2
prior_plan_revision: 5
prior_acceptance: DecisionRequired
material_decision:
  selected: provider_owned_deterministic_commit_on_publish
```

Requirement Revision 2 is a material architecture/scope change produced by the explicit user `#开发` command after Acceptance R1. The exact Task and canonical transport are preserved.

## R6 remediation delta

Plan R6 preserves Requirement Revision 2 and every Plan R5 boundary already accepted by review. It changes only the checkout/persistence authority mismatch rejected by Plan Review R5.

Core rule:

```text
the first worktree checkout
AND
later provider clean/staging
MUST use one frozen provider-owned canonicalization authority snapshot
```

Remote clone/fetch may continue to use the fixed active-user authenticated Git transport because those steps only acquire repository objects/refs and do not materialize the implementation worktree. Before the first `checkout`, the provider switches to a local materialization boundary that:

- captures and validates the allowlisted safe checkout-normalization scalars;
- freezes versioned attribute authority from the exact admitted parent tree;
- disables system/global attribute authority;
- rejects any effective custom/external `filter` assignment across tracked paths before worktree materialization;
- clamps hooks, fsmonitor, recursive submodule materialization, editor/pager and prompt execution;
- persists/read-backs the snapshot before checkout;
- reuses exactly the same snapshot during provider temporary-index clean conversion after Codex.

V1 conservatively treats any Codex modification to a versioned `.gitattributes` file as unsupported and fails closed before persistence. This preserves the same attribute semantics on both sides of the checkout/clean round trip rather than guessing how to invert bytes produced under an older attribute set.

No Requirement Revision 3 is introduced. S01-S03 remain retained verified prerequisites. Only S04 remains proposed after Plan R6 approval.

## 1. Retained implementation baseline

Plan R6 does **not** replay S01-S03. Their verified implementation remains the baseline:

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

## 2. R6 architecture delta

### D12.1 — Shared pre-checkout / persistence canonicalization authority

The existing S02 remote bootstrap remains valid for remote admission and object acquisition, but Plan R6 extends it before the first worktree checkout.

#### Phase A — Authenticated object acquisition only

The active-user fixed Git transport may perform only the remote/object steps required to establish the exact independent repository and admitted branch/head, for example:

```text
clone --no-checkout / fetch
-> remote head readback
-> require remote_head == expected_remote_sha
```

No implementation worktree is materialized in this phase.

#### Phase B — Freeze provider canonicalization authority before checkout

Before `git checkout` or any equivalent worktree materialization, the provider MUST:

1. create provider-owned execution-state locations outside the implementation candidate set for:
   - a temporary inspection index;
   - an empty global attributes file;
   - an empty hooks directory;
   - the canonicalization snapshot;
2. read only the allowlisted effective scalar values needed for supported checkout/clean semantics:
   - `core.autocrlf`;
   - `core.eol`;
   - `core.safecrlf`;
   - `core.checkRoundtripEncoding` only when supported `working-tree-encoding` semantics require it;
3. validate each captured value against the provider's closed schema and normalize unset/default states deterministically;
4. persist/read-back those values as the attempt's immutable normalization snapshot;
5. seed the provider inspection index from the exact `expected_remote_sha` tree without checkout;
6. require `.git/info/attributes` to be absent or empty;
7. disable system attributes and redirect global attributes to the provider-owned empty file for all local materialization inspection;
8. enumerate the exact parent tree's tracked paths from the inspection index and resolve effective attributes from the expected tree using fixed non-executing attribute inspection;
9. reject the repository before checkout if **any tracked path** has an effective `filter` attribute other than unspecified/unset;
10. digest and persist/read-back:
    - the exact versioned `.gitattributes` blob/path set from `expected_remote_sha`;
    - the effective supported attribute projection required for checkout/clean equivalence;
    - the empty `.git/info/attributes` proof;
    - the normalization snapshot.

Attribute inspection must not execute filters. A temporary index seeded from the expected tree plus fixed `check-attr --cached`/equivalent semantics is an acceptable design.

#### Phase C — Provider-clamped checkout

Only after Phase B is durably verified may the provider materialize the worktree.

Checkout must use the frozen snapshot and provider-owned clamps:

- system Git config excluded for local materialization;
- global Git config excluded for local materialization after the safe snapshot has been captured;
- system attributes disabled;
- global attributes redirected to the provider-owned empty file;
- provider-owned empty hooks path;
- `core.fsmonitor=false`;
- `submodule.recurse=false`;
- commit/tag signing disabled where relevant;
- pager/editor disabled;
- terminal prompting disabled;
- no shell wrapper;
- no caller-supplied config;
- replay only the frozen safe normalization scalars required for checkout semantics.

Versioned `.gitattributes` from the exact admitted tree remain the only repository attribute authority used for checkout.

Because every effective `filter` assignment was rejected before checkout and filter-driver configuration is not imported as local materialization authority, no repository/user custom clean/smudge/process filter may execute while creating the Codex worktree.

The provider then verifies exact branch/head and persists a `checkout_materialized` state containing the canonicalization snapshot digest.

#### Phase D — Same snapshot after Codex

Before persistence, the provider MUST prove:

- actual branch/head still satisfy the admitted direct-Codex transport rules;
- `.git/info/attributes` remains absent/empty;
- the frozen safe scalar snapshot digest is unchanged;
- the expected-tree attribute snapshot remains authoritative;
- no versioned `.gitattributes` path was added, deleted or modified by Codex.

A versioned `.gitattributes` change is `DirectCodexUnsupportedAttributeMutation` in V1 and cannot be committed through the persistence broker.

Only then may D14 candidate clean conversion proceed, using the exact same frozen snapshot and expected-tree attribute authority.



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

### D14 — Provider-owned candidate tree using the frozen checkout authority

The Codex execution checkout's Git index remains **untrusted implementation-host state**. Candidate authority uses a provider-owned temporary index seeded from the exact admitted parent.

Plan R6 does not capture a new clean policy after Codex. It reuses the exact D12.1 snapshot that was persisted **before checkout**.

#### D14.1 — Shared snapshot admission

Before candidate construction, require all of:

```text
checkout_snapshot_digest == persisted_pre_checkout_snapshot_digest
expected_attribute_snapshot_digest == persisted_expected_attribute_snapshot_digest
.git/info/attributes == absent_or_empty
no versioned .gitattributes mutation
local HEAD / actual branch satisfy admitted transport invariants
```

Any mismatch fails closed before candidate object creation.

#### D14.2 — Local candidate configuration clamp

Candidate materialization uses the same local materialization authority as checkout:

- system/global Git configuration excluded for local candidate construction after the safe snapshot has been captured;
- system attributes disabled;
- global attributes redirected to the same provider-owned empty file;
- expected-tree versioned `.gitattributes` are the only repository attribute authority;
- `.git/info/attributes` absent/empty;
- hooks path provider-owned empty;
- signing disabled;
- fsmonitor disabled;
- pager/editor disabled;
- terminal prompts disabled;
- submodule recursion disabled;
- no shell wrapper;
- no caller Git config;
- replay only the exact frozen safe normalization scalars.

The provider re-resolves effective attributes for every eligible path under this same snapshot and again requires `filter` to be unspecified/unset.

Supported builtin clean semantics remain:

- text/eol normalization;
- binary/no-text behavior;
- builtin `ident`;
- supported Git `working-tree-encoding` conversion.

Any unsupported/custom clean semantic fails closed.

#### D14.3 — Candidate construction

Required sequence:

```text
verify shared pre-checkout snapshot identity
-> inventory worktree delta against expected_remote_sha
-> reject any versioned .gitattributes mutation
-> validate eligible relative paths/modes/types
-> create provider temporary GIT_INDEX_FILE outside candidate set
-> seed temporary index from expected_remote_sha tree
-> stage only provider-derived literal eligible paths
   using Git builtin path-aware clean conversion under the frozen checkout snapshot
-> write candidate tree
-> verify candidate tree == parent tree + exactly validated canonical eligible delta
```

The fixed staging operation may use `git add`/equivalent builtin index update against the provider temporary index because custom filter attributes were rejected before checkout and revalidated before persistence, while execution-producing config surfaces remain clamped.

The Codex-owned original index is never candidate authority.

#### D14.4 — Canonicalization invariants

The provider MUST prove:

1. an unchanged tracked file whose Windows worktree representation differs only because of the frozen checkout's CRLF expansion re-materializes to the **same parent blob SHA**;
2. a real edit to such a CRLF worktree file produces canonical content with the semantic edit but without whole-file line-ending churn;
3. binary paths preserve exact bytes and do not receive text normalization;
4. supported `working-tree-encoding` paths round-trip under the same pre-checkout snapshot;
5. custom/external filter attributes cannot execute at checkout or persistence time;
6. versioned `.gitattributes` mutation is rejected in V1 rather than changing clean authority mid-attempt;
7. normalization/attribute snapshot drift between checkout and persistence fails closed.

The receipt/recovery evidence records the shared canonicalization snapshot digest, expected-attribute digest, eligible path digest and candidate tree SHA without exposing user environment or credentials.

### D15 — Fixed Git persistence primitives and config clamp

Persistence uses a closed internal Git broker only. It is not model-facing and accepts no caller Git argv, pathspec, commit message, author, timestamp, config key, remote URL or branch.

Allowed semantic operations are limited to:

```text
fixed pre-checkout safe-config snapshot read
fixed expected-tree attribute inspection before checkout
provider-clamped local checkout
fixed remote readback
validated worktree inventory
provider temporary-index construction
provider-clamped builtin clean staging of exact eligible paths
provider deterministic commit-object construction
provider-local candidate ref update
ordinary fast-forward push exact candidate -> exact canonical branch
independent remote readback
```

Checkout and local candidate construction both exclude arbitrary system/global materialization authority and replay the same frozen allowlisted checkout-normalization snapshot needed to preserve canonical clean semantics.

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
  pre_checkout_snapshot_digest:
  expected_attribute_snapshot_digest:
  checkout_materialized_under_snapshot: true
  info_attributes_empty: true
  versioned_gitattributes_unchanged: true
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

Plan R6 preserves all R2 security boundaries.

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

Plan Review should compile exactly one new current implementation slice if R6 is approved:

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

1. clone/fetch obtains the exact admitted commit without materializing the worktree;
2. provider captures and validates the safe normalization scalars **before checkout** and persists/read-backs the snapshot;
3. provider inspection index is seeded from `expected_remote_sha` before checkout;
4. effective custom `filter` on any tracked path in expected-tree `.gitattributes` fails closed before its marker process can execute during checkout;
5. global/system attributes are neutralized for checkout and non-empty `.git/info/attributes` blocks checkout;
6. checkout runs under provider clamps with empty hooks path, fsmonitor off, submodule recursion off, no pager/editor/prompt and no arbitrary user config authority;
7. parent LF blob + checkout-induced Windows CRLF worktree under the frozen snapshot re-materializes to the exact parent blob SHA;
8. one-line semantic edit in that CRLF worktree file yields canonical LF content with only the semantic edit;
9. binary fixture preserves exact bytes with no text normalization;
10. supported `working-tree-encoding` fixture round-trips under the same frozen snapshot;
11. Codex modification/add/delete of any versioned `.gitattributes` path fails closed before candidate construction;
12. snapshot/attribute drift between checkout and persistence fails closed;
13. pre-staged excluded path in the Codex-owned index does not enter the provider candidate tree;
14. provider temporary candidate index is seeded from the exact admitted parent and contains only validated canonical eligible delta;
15. hooks/signing/fsmonitor/editor/pager/terminal prompts cannot execute through the persistence path;
16. provider control/recovery artifacts are not committed;
17. unmerged index/worktree state fails closed;
18. unsupported gitlink/submodule mutation fails closed;
19. symlink/path traversal cannot read or commit content outside the execution checkout;
20. canonical checkout branch/head/index/worktree metadata remain unchanged;
21. remote head drift before publish fails without push;
22. ordinary push succeeds only to the exact canonical branch;
23. remote readback mismatch fails receipt validation;
24. no eligible changes does not manufacture an empty implementation commit;
25. malformed persistence receipt fails;
26. local dirty/uncommitted work cannot be success;
27. same admitted attempt reconstructs a **bit-identical candidate SHA** after interruption at `prepared`, `tree_ready`, `candidate_ready` and local-ref-ready boundaries;
28. crash after `publish_intent` performs readback only and never creates another candidate or automatic second push;
29. remote readback after uncertain push correctly distinguishes candidate published / base still present / transport drift;
30. existing S01-S03 direct-Codex, firewall, scoped-verification and user-scoped Git regressions remain green.

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

The physical proof must additionally prove the shared boundary end to end:

- a repository fixture with a custom `filter` attribute is rejected before checkout and its marker process never runs;
- a normal tracked text fixture is materialized as Windows CRLF under the frozen pre-checkout snapshot while the parent Git blob is LF;
- the unchanged path canonicalizes back to the exact parent blob SHA under the same snapshot;
- a one-line real edit remains LF-canonical without whole-file EOL churn;
- changing a versioned `.gitattributes` file during the Codex run fails closed before persistence.

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

Because the direct/Codex bridge cannot yet persist its own implementation work, an an approved Plan R6 may require a **new explicit Task-scoped bootstrap override** bound to Plan R6 and its reviewed Slice Set:

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

Plan Review R6 must specifically verify:

- remote clone/fetch object acquisition is separated from first worktree materialization;
- the safe canonicalization snapshot is captured, validated and durably read back before checkout;
- expected-tree attributes are inspected from provider-owned pre-checkout state without executing filters;
- any effective custom `filter` on any tracked path blocks checkout before external execution;
- system/global attribute authority is neutralized and `.git/info/attributes` cannot influence checkout;
- checkout and persistence use the same frozen safe normalization + expected-tree attribute authority;
- hooks/fsmonitor/submodule recursion/editor/pager/prompt and arbitrary user materialization config are clamped during checkout;
- versioned `.gitattributes` mutation is deliberately unsupported in V1 so checkout/clean semantics cannot diverge mid-attempt;
- Windows CRLF checkout bytes canonicalize back to the parent LF blob when unchanged and small edits do not become whole-file churn;
- the Codex-owned index remains untrusted and provider candidate construction still uses a temporary index seeded from the exact admitted parent;
- every commit-SHA input remains frozen before candidate creation and same-attempt recovery remains bit-identical;
- `publish_intent` still prevents hidden automatic re-push after uncertain publication;
- provider-owned persistence remains a bounded direct/Codex transport broker rather than a generic Git surface;
- retained S01-S03 evidence remains valid and only S04 is newly implementation-authorized after approval;
- a new Plan-R6-bound bootstrap override is required before S04 execution.

Approval must compile a new current Slice Set for Plan R6. This Plan does not self-approve and does not authorize implementation.
