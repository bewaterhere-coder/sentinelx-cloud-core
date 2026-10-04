# PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1 — Plan R1

Requirement: `docs/requirements/PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1.md`, revision 1.

Status: **Pending Plan Review**. No implementation authorization.

## 1. Planning objective

Implement one bounded provider-owned repository transaction path that composes the existing SentinelX mutation scope, Windows AppContainer sandbox, canonical-repository firewall, audit lineage and user-scoped Git execution context.

The target lifecycle is:

```text
exact repository + source ref/SHA + Task/Run/Attempt[/Slice]
→ provider resolves current repository/transport evidence
→ provision/revalidate Host-owned scope
→ provider obtains an immutable exact-source snapshot/capsule
→ durable materialization START
→ hydrate exact Host-owned workspace inside the admitted scoped boundary
→ verify exact source + isolation
→ execute through the existing scoped executor
→ publication_pending
→ broker validates exact workspace delta + exact Task ref + expected remote SHA
→ create bounded checkpoint commit
→ push with CAS semantics
→ remote readback
→ durable publication receipt
→ terminalize scope
```

The caller never supplies a Host workspace/cache/mirror path and never receives Git credentials or canonical-checkout authority.

## 2. Architecture decisions

### D1 — Repository transaction is an explicit scope profile, not generic Git

Introduce an explicit repository-transaction semantic bound to the existing mutation authority rather than reusing generic `sentinel_git`, `script_run`, filesystem copy or caller-selected Git clone.

The transaction record must bind at minimum:

```yaml
repository_identity
project_id
task_id
run_id
attempt_id
slice_id: optional
scope_id
scope_generation
workspace_id
source_ref
expected_source_sha
publication_ref: optional
expected_remote_sha: optional
state
materialization_evidence
execution_evidence
publication_evidence
```

The record is provider-owned durable state. Caller fields are comparison inputs only where explicitly allowed.

The preferred implementation is a new focused repository-transaction module composed with `MutationScopeStore`; do not overload the immutable mutation-scope digest with mutable transaction progress fields unless review proves a safe versioned migration.

### D2 — Source acquisition is broker-owned; workspace hydration remains scoped

Do not solve the downstream failure by granting AppContainer access to the canonical checkout or by running `git clone` inside AppContainer.

Use a two-boundary design:

```text
Host broker boundary
  └─ resolve exact remote repository + source SHA
  └─ obtain immutable provider-owned source snapshot/capsule
       ↓ read-only admitted artifact
Scoped mutation boundary
  └─ materialize verified snapshot into exact Host-owned workspace
```

The Host broker may use existing user-scoped Git execution to obtain source objects, but it must not expose the user environment, credential helper, SSH agent, token material, arbitrary repository config or a caller-selected cache path to the scoped process.

The snapshot/capsule representation must be immutable for the transaction and integrity-bound to the verified source SHA. Its storage location is provider-owned. It must not be interpreted as executable authority.

Workspace writes derived from the snapshot must occur only after scope revalidation and durable operation START, inside the same OS-enforced scoped mutation boundary used by current Host mutation semantics. This preserves DevForge's `development.execution_workspace_materialize` ordering rather than treating a broker copy as an unrestricted filesystem shortcut.

### D3 — Materializer is provider code, not repository code

Add a provider-controlled materialization helper that consumes only the admitted immutable source snapshot/capsule and writes only into the exact scoped workspace.

It must validate before/while materializing:

- exact source SHA/digest binding;
- no absolute/traversal paths;
- no escape through symlink/junction/reparse behavior;
- no alternate-data-stream target semantics on Windows;
- no special-file/device semantics outside the supported regular-file/directory/symlink policy;
- deterministic file-mode/metadata handling where relevant;
- final workspace root equals the scope-sealed exact workspace;
- canonical/source checkout is not the target.

A materialization result is successful only after exact-workspace existence/readback and exact-source evidence are persisted.

### D4 — Extend `devforge_runtime` with bounded repository actions

Extend the existing Agent-owned `devforge_runtime` local API contract with bounded repository-transaction actions. Proposed names:

```text
materialize_repository
publish_checkpoint
inspect_repository_transaction
```

Exact names may change during Plan Review, but the semantic split is mandatory:

- `materialize_repository`: exact repo/ref/SHA + current scope/lineage, no Host paths;
- `inspect_repository_transaction`: read-only transaction/readback state;
- `publish_checkpoint`: exact current transaction + target ref + expected remote SHA + bounded commit metadata, no arbitrary Git argv.

`execute_scoped` remains the sole scoped process execution action. No second generic executor is introduced.

`local_api.describe` must publish closed schemas dynamically from the Agent. Production Hub source/schema changes remain out of scope.

### D5 — Repository transaction lifecycle is multi-operation; legacy one-shot execution is unchanged

Current `execute_scoped` terminalizes its scope after one execution. Repository materialization + execution + publication requires an explicit longer transaction lifecycle.

Add a repository-transaction lifecycle equivalent to:

```text
provisioned
→ materialized
→ executing
→ executed
→ publication_pending
→ published
→ terminal
```

Rules:

1. legacy `purpose=scoped_script` remains one-shot and retains existing automatic terminalization;
2. repository-transaction scopes are explicitly admitted for the required operation classes only;
3. successful repository-scoped execution does not silently terminalize before publication; instead it closes the process/Job, removes active process authority, and transitions durable transaction state to `publication_pending` while retaining only the minimum provider authority needed for bounded publication;
4. no child/background process survives the execution boundary;
5. execution failure/containment failure terminalizes or revokes the scope and publication is forbidden;
6. TTL/revocation continues to fail closed;
7. an expired/terminal transaction can never be reactivated by caller input.

The implementation must separate **process mutation authority** from the later **broker publication authority** so `publication_pending` does not imply a live AppContainer process or reusable arbitrary workspace write capability.

### D6 — Publication uses a dedicated fixed-semantics Git broker

Publication must not reuse generic model-facing Git mutation as authority. Add a focused provider-owned publication broker, preferably in a new module layered over existing user-scoped Git execution primitives.

The broker must consume only transaction-owned workspace/repository/ref state and fixed Git semantics. It must not accept arbitrary Git argv.

Required hardening:

- no shell;
- no force push in V1;
- no repository-controlled `pre-commit`, `commit-msg`, `pre-push` or other hooks;
- disable/ignore local/global aliases that could rewrite fixed verbs;
- disable external clean/smudge/process filters or reject repositories requiring them for publication correctness;
- no signing helper/GPG/SSH signing invocation;
- no interactive prompts;
- sanitized bounded output;
- no credential material in state/receipt;
- fixed target branch/ref sealed to transaction admission;
- exact expected remote SHA required before write;
- remote re-probe immediately before push;
- push and subsequent remote readback must resolve the exact expected produced commit.

Where ordinary porcelain semantics would execute repository-controlled behavior, prefer fixed Git plumbing or explicit safe config overrides.

### D7 — Publication is compare-and-swap and idempotent

Before creating/pushing a checkpoint:

1. inspect transaction state and exact workspace;
2. revalidate repository + lineage + scope generation + transport target;
3. verify current remote ref equals `expected_remote_sha`;
4. compute/stage the exact workspace delta under fixed broker semantics;
5. create at most one intended checkpoint commit;
6. persist produced commit SHA before remote write;
7. push non-force from expected old SHA to produced commit;
8. read back remote ref;
9. mark `published` only when readback exactly equals the produced commit.

Retry rules:

- if durable evidence already shows successful readback, return the existing result without a new commit/push;
- if push result is uncertain, first read the exact remote ref; if it equals the produced commit, reconcile success without replay;
- if remote remains at expected old SHA, a bounded retry may be considered only under the same current transaction authority and exact produced commit;
- if remote is any third value, fail closed as transport drift/conflict;
- never regenerate a different commit merely because response/readback was lost.

### D8 — Failure semantics remain operation-scoped and fail closed

Materialization failures produce no successful workspace binding and no publication.

Execution failures produce no automatic publication.

Publication outcomes classify at minimum:

```text
remote head drift              → blocked/conflict
credential unavailable/rejected→ blocked
transport timeout/reset        → interrupted/uncertain
push acknowledged + readback   → published
push response lost             → publication_uncertain, readback-first resume
```

No failure broadens permissions, swaps provider, mutates canonical checkout or enables a generic fallback.

For a terminalized transaction with no verified external publication side effect, a later DevForge Resume may create a new Attempt under the same Run per DevForge Resume semantics; SentinelX itself must not mint replacement DevForge Run/Attempt identities.

### D9 — Audit lineage covers materialize, execute and publish as one transaction

Extend durable evidence so all repository-transaction operations correlate to the same repository + semantic lineage + scope generation.

Materialization evidence should identify source/ref/SHA and integrity proof. Execution reuses current process audit. Publication records expected old SHA, produced commit, push outcome and readback SHA.

Receipt projection must omit provider cache paths, credential identifiers and raw interactive-user environment data.

### D10 — Parallel task overlap is reconciled at implementation admission

PR-011 is complementary and must remain independently consumable: repository materialization may later provide the source workspace that PR-011's Node/npm verification profile consumes, but this Task must not duplicate dependency-capsule/toolchain semantics.

PR-012 overlaps `devforge_runtime.py`. Before S01 implementation, re-read canonical `main` and PR-012 status. If PR-012 has merged, build on its explicit `execution_profile` contract. If not merged, keep this Task's branch isolated and avoid importing unmerged task code merely to reduce conflicts.

PR-010 firewall semantics are mandatory baseline and must remain passing.

## 3. Proposed implementation slices

Formal Execution Slice Set is compiled only after Plan approval.

### S01 — Repository Transaction Model + Local API Admission

Objective: create durable repository-transaction identity/state, exact scope binding, closed local-api schemas and idempotent state transitions without yet performing source hydration or remote publication.

Likely surfaces:

- new `src/sentinelx_core/repository_transaction.py`;
- `src/sentinelx_core/mutation_scope.py` only for explicit operation-class/lifecycle composition where necessary;
- `src/sentinelx_core/handlers/devforge_runtime.py`;
- Agent wiring for the new bounded services;
- `tests/test_devforge_runtime_local_api.py`;
- new focused repository-transaction tests;
- mutation-scope regression tests.

Verification:

- caller path fields rejected;
- foreign/stale/terminal scope rejected;
- exact repository/lineage binding enforced;
- transaction state is durable/idempotent;
- legacy `scoped_script` lifecycle unchanged;
- `describe` exposes only bounded path-free schemas;
- PR-012 overlap is explicitly reconciled against current main before mutation.

### S02 — Exact Source Snapshot + Scoped Workspace Materialization

Objective: obtain an integrity-bound exact source snapshot through provider-owned Git transport and hydrate it inside the exact scoped workspace without canonical-checkout access.

Likely surfaces:

- new provider source-snapshot/materializer module(s);
- existing user-scoped Git helper only where fixed source acquisition can safely reuse it;
- Windows sandbox/ACL code only where a narrow read-only snapshot grant is required;
- mutation audit evidence;
- integration/security tests.

Verification:

- exact source SHA verified independently;
- materialization succeeds without AppContainer canonical-checkout access;
- snapshot path cannot be caller-selected;
- traversal/reparse/ADS escape tests fail closed;
- wrong repo/ref/SHA or scope produces no successful materialization;
- exact workspace readback/isolation proven;
- canonical checkout remains unchanged and protected.

### S03 — Repository-Scoped Execution Retention + CAS Publication Broker

Objective: allow a successful repository-scoped execution to reach `publication_pending`, then publish one exact checkpoint with user-scoped Git credentials through fixed no-hook/no-filter/no-signing semantics.

Likely surfaces:

- scoped execution lifecycle composition;
- repository transaction state machine;
- new fixed publication broker module;
- `src/sentinelx_core/user_git.py` only for bounded reusable primitives, without creating a generic run-as-user API;
- audit/receipt projection;
- remote/CAS/idempotency tests.

Verification:

- successful process exits leave no active child/Job authority;
- legacy one-shot calls still terminalize exactly as before;
- remote head CAS is mandatory;
- malicious hooks/filters/aliases/signing helpers are not executed;
- credentials never enter AppContainer/receipt;
- duplicate/retry after verified push is no-op/readback reconciliation;
- uncertain push is readback-first and never blindly replayed;
- remote drift creates no overwrite.

### S04 — Windows Physical E2E + Activation + Downstream Unblock Proof

Objective: prove the accepted capability on a real Windows Host and then prove it resolves the original downstream blocker without transferring downstream Task authority.

Verification sequence:

1. install/activate the exact accepted SentinelX candidate through the approved Agent update path;
2. `sentinel_capabilities` confirms firewall/sandbox/audit and repository transaction readiness;
3. `local_api.describe devforge_runtime` exposes current bounded materialize/publish actions;
4. controlled fixture: provision → materialize exact source → scoped mutation → publish checkpoint → remote readback → terminalize;
5. negative physical tests: wrong SHA, stale scope, remote drift and no-hook guarantees;
6. resume `ChatGPTControlShell` `run-pr013-s01-001` / S01 under its own explicit `#开发执行` authority and verify repository materialization now reaches the implementation/verification boundary without generic fallback.

The downstream PR-013 execution is acceptance evidence only; this SentinelX Task cannot mutate or complete the downstream Task without that Task's own command authority.

## 4. Write scope

Expected source write scope:

- `src/sentinelx_core/handlers/devforge_runtime.py`;
- new focused repository transaction/materialization/publication modules;
- `src/sentinelx_core/mutation_scope.py` where operation-class/lifecycle support is required;
- `src/sentinelx_core/mutation_audit.py` only for new bounded evidence types;
- `src/sentinelx_core/windows_mutation_sandbox.py` only for narrow snapshot-read/materialization enforcement;
- `src/sentinelx_core/user_git.py` only for safe fixed Git primitives that remain Git-specific;
- Agent composition/capability code required to wire the services;
- focused unit/integration/Windows tests;
- config example/README/operator docs required to activate or inspect the capability.

Forbidden write scope:

- production Hub repository/source/deployment;
- downstream ChatGPTControlShell source/task artifacts;
- canonical Host checkouts as implementation workspaces;
- unrelated SentinelX operations or allowlists.

## 5. Security and correctness risks

1. **Broker becomes a canonical-write bypass.** Materialization/publication code must consume scope/transaction authority and exact transport evidence, not arbitrary path/Git arguments.
2. **Snapshot becomes executable authority.** Treat it as immutable content with integrity verification; never source scripts/config from it in broker context.
3. **Archive/tree extraction escape.** Validate traversal, reparse/symlink/ADS semantics before successful hydration evidence.
4. **Git config executes repository code.** Publication must neutralize hooks, aliases, filters and signing helpers or use safe plumbing.
5. **Long-lived scope weakens containment.** No active process/Job survives execution; repository transaction state does not equal arbitrary write authority.
6. **Uncertain push duplicates side effects.** Persist produced commit before push and reconcile by exact remote readback first.
7. **PR-011/012 branch overlap causes hidden dependency.** Revalidate `main` and current task heads at every implementation slice; never assume unmerged code.
8. **Credentials leak across boundary.** User-scoped Git stays broker-only and output/evidence is sanitized.
9. **Materialization trusts branch names.** Exact SHA is mandatory and independently verified.
10. **Legacy scoped calls regress.** Regression tests must prove unchanged one-shot terminalization and fail-closed behavior.

## 6. Verification strategy

### Unit/contract

- repository transaction durable state and transition table;
- repository/lineage/scope binding;
- closed local-api schemas and invalid-field rejection;
- source-ref/SHA verification;
- snapshot integrity and extraction safety;
- publication no-hook/no-alias/no-filter/no-signing configuration;
- CAS and idempotency/uncertain-result reconciliation;
- credential/output redaction.

### Existing regressions

At minimum rerun affected suites covering:

- `test_devforge_runtime_local_api.py`;
- mutation scope admission/handler/registry;
- mutation audit;
- scoped script execution;
- canonical repository firewall + structured firewall;
- Windows mutation sandbox;
- user-scoped Git + Git network failure classification.

Then run the applicable full repository test suite on the exact Task transport.

### Physical Windows acceptance

Mocks do not satisfy materialization/publication acceptance. At S04, capture actual Host receipts for exact workspace materialization, AppContainer execution, user-scoped Git publication, remote CAS/readback and terminal scope closure.

## 7. Completion boundary

This Plan does not authorize implementation, Agent installation, service restart, production deployment, Hub mutation or downstream ChatGPTControlShell execution.

Implementation begins only after `#开发评审 PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1` approves the current Plan and the formal execution Slice Set is compiled/read back.
