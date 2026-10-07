# PR-015-direct-codex-development-host-invocation-bridge-v1 — Plan R3

Requirement: `docs/requirements/PR-015-direct-codex-development-host-invocation-bridge-v1.md`, revision 2.

Status: **Pending Plan Review**. No implementation authorization.

## 0. Planning baseline

```yaml
sentinelx_main: 018b78ca20984176d53fbe90039dc795a7f2742f
planning_task_head_before_r3: d67923bd7df7f45186f6852c414d2cc74f5321d6
devforge_main: cf995df50d392aafdba7d48d27fb5dacab492ecb
devforge_version: 2.81.0
project_execution_binding:
  provider: direct
  adapter: codex
canonical_transport:
  repository: bewaterhere-coder/sentinelx-cloud-core
  pr: 15
  branch: task/direct-codex-development-host-invocation-bridge-v1
requirement_revision: 2
prior_plan_revision: 2
prior_acceptance: DecisionRequired
material_decision:
  selected: provider_owned_deterministic_commit_on_publish
```

Requirement Revision 2 is a material architecture/scope change produced by the explicit user `#开发` command after Acceptance R1. The exact Task and canonical transport are preserved.

## 1. Retained implementation baseline

Plan R3 does **not** replay S01-S03. Their verified implementation remains the baseline:

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

## 2. R3 architecture delta

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

### D14 — Eligible change inventory

The provider derives the path inventory from the exact isolated checkout.

Rules:

- no caller-selected paths;
- repository metadata outside the worktree is never eligible;
- provider control/evidence artifacts are excluded from the implementation commit;
- unmerged index state fails closed;
- unsupported gitlink/submodule mutation fails closed in V1;
- paths must canonicalize inside the execution checkout;
- no symlink/path traversal may escape the checkout;
- changed-path inventory and a digest are recorded in the bounded receipt;
- if there are no eligible implementation changes, do not fabricate an empty implementation commit.

Provider-owned runtime artifacts should be placed outside the commit candidate set where practical rather than relying only on ignore rules.

### D15 — Fixed Git persistence primitives

Persistence uses fixed provider-owned Git mechanics only.

Implementation SHOULD add a narrow internal module such as `direct_codex_persistence.py` and reuse the existing fixed Git transport/user-context substrate rather than expose a new command surface.

Allowed semantic operations are limited to:

```text
status/inventory
stage provider-derived eligible paths
write tree / create commit
update local execution ref
ordinary push exact candidate -> exact canonical branch
remote readback
```

No shell wrapper, caller argv, hooks, interactive prompt, commit signing, force push or arbitrary Git config is permitted.

Hooks/signing must be explicitly disabled for provider-created commits. Git credential material remains inside the existing fixed user-scoped Git boundary and is never returned or logged.

### D16 — Deterministic commit construction

The provider creates exactly one commit for one successful Run/Attempt[/Slice] when eligible changes exist.

Deterministic inputs include:

- parent = admitted `expected_remote_sha`;
- exact resulting tree;
- fixed provider-owned author/committer identity;
- exact Task/Run/Attempt/Slice provenance;
- fixed provider-generated commit-message format;
- provider-owned timestamp/provenance value that is persisted for the attempt and reused on same-attempt recovery.

Caller/Codex free text does not control commit metadata.

A representative message shape is:

```text
devforge(<task-id>/<slice-id>): persist direct-codex run <run-id>/<attempt-id>
```

Exact serialization is implementation-owned but must be stable and testable.

Same-attempt recovery must detect an already-created candidate commit and must not manufacture duplicate commits.

### D17 — CAS-style publication without force

Immediately before publication, re-read the canonical remote branch and require:

```text
remote_head == expected_remote_sha
candidate_parent == expected_remote_sha
actual_branch == canonical_branch
```

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

No automatic retry is permitted after an uncertain externally visible push. Readback decides whether the exact candidate landed.

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

Plan R3 preserves all R2 security boundaries.

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

Plan Review should compile exactly one new current implementation slice if R3 is approved:

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
2. caller has no way to choose Git argv/pathspec/message/remote/branch;
3. provider control artifacts are not committed;
4. unmerged index fails closed;
5. unsupported gitlink/submodule mutation fails closed;
6. hooks/signing cannot execute during provider commit;
7. canonical checkout branch/head/index/worktree metadata remain unchanged;
8. remote head drift before publish fails without push;
9. ordinary push succeeds only to the exact canonical branch;
10. remote readback mismatch fails receipt validation;
11. same-attempt recovery does not create a duplicate candidate;
12. no eligible changes does not manufacture an empty implementation commit;
13. malformed persistence receipt fails;
14. local dirty/uncommitted work cannot be success;
15. existing S01-S03 direct-Codex, firewall, scoped-verification and user-scoped Git regressions remain green.

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

Because the direct/Codex bridge cannot yet persist its own implementation work, an approved Plan R3 may require a **new explicit Task-scoped bootstrap override** bound to Plan R3 and its reviewed Slice Set:

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

Acceptance R1 is historical evidence only and cannot approve R2.

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

Plan Review must specifically verify:

- provider-owned persistence is consistent with Requirement R2 and does not redefine Codex as transport owner;
- fixed Git operations do not create a generic execution surface;
- commit candidate path inventory excludes provider artifacts and fail-closes unsafe Git states;
- ordinary fast-forward publication is sufficient for the CAS requirement without force;
- exact receipt semantics prove persisted transport state;
- retained S01-S03 evidence is still valid and need not be replayed;
- only the new S04 delta is implementation-authorized after approval;
- a new R3-bound bootstrap override is required before S04 execution.

Approval must compile a new current Slice Set for Plan R3. This Plan does not self-approve and does not authorize implementation.
