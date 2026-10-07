# PR-014 — SentinelX DevForge Execution Workspace Materialization Bridge V1 — Plan R4

## Plan State

```yaml
task_id: PR-014-devforge-execution-workspace-materialization-bridge-v1
plan_revision: 4
plan_status: ready_for_review
implementation_authority: false
requirement_ref: docs/requirements/PR-014-devforge-execution-workspace-materialization-bridge-v1.md
requirement_revision: 2
requirement_blob_sha: 58d7ea1388e843665e5dda34f3cc2f645f2240d3
requirement_change_impact: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-requirement-r2-invalidation.md
prior_plan_revision: 3
prior_plan_blob_sha: bf44533eec62652b4d252b629c9498df596f43cd
rejected_review_ref: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-plan-review-r3.md
rejected_review_blob_sha: 05046c0e4eddda02ddbad7574d64c68921bc99e4
transport:
  type: github-pr
  pr_number: 14
  branch: task/devforge-execution-workspace-materialization-bridge-v1
  base_branch: main
planning_baseline:
  sentinelx_main: 1028030b33f0ea792a884491a431fffe566f6aa5
  task_head_before_plan_r4: d8aebe540f4cdbb81409bb45e6dd5878fa6379ee
  devforge_main: 9551d38b1d70b5bfb3f692725e8f5c70b74693a6
  devforge_release: v2.97.0
project_binding:
  provider: direct
  adapter: codex
  source: explicit_project_binding
completed_evidence_preserved:
  - S01
implementation_authorized: false
```

Plan R4 preserves the Requirement R2 / Plan R3 technical design and closes Plan Review R3 finding `BootstrapExecutionAuthorityUndefined`.

Plan R4 makes one authority correction: S02 execution is owned by an explicit task-scoped Harness bootstrap override. GitHub PR #14 remains only the locked canonical transport/persistence target.

No product implementation is authorized until this Plan is reviewed, an exact R4 Slice Set is compiled/read back, and the explicit Harness bootstrap admission succeeds.

## R4 Remediation Delta — explicit Harness bootstrap authority

Plan R4 changes no Requirement R2 semantics, product scope, security boundary, transport identity, source-capsule design, materializer design, Development Host handoff semantics, or PR-013 ownership split.

It closes only:

~~~text
BootstrapExecutionAuthorityUndefined
~~~

The authoritative execution chain is frozen as:

~~~text
Requirement R2
→ Approved Plan R4 exact revision/digest
→ exact R4 Slice Set compiled/read back
→ Task stage = implementation
→ explicit #开发引导执行 PR-014-devforge-execution-workspace-materialization-bridge-v1 harness
→ bootstrap contract verifies self-host relation + registered/current Harness target
→ Harness capability/readiness + exact sliced locked-transport contract verified
→ active Task-scoped implementation_bootstrap override persisted/read back
→ later explicit #开发执行
→ at most S02
~~~

Authority rules:

- project binding remains `direct/codex`;
- the Task-scoped override has higher resolution priority only while valid and active;
- GitHub PR #14 / exact task branch are transport and persistence identity, not execution-provider authority;
- `repository.write` may be used only as an implementation persistence mechanic inside the admitted Harness execution boundary;
- orchestration MUST NOT directly implement S02 through repository API merely because repository writes are technically available;
- Harness owns its internal Development Host/model/context/workspace mechanics under its own contract; Plan R4 does not select or persist those internals;
- because slicing is active, the resolved Harness consumer must provide verified `incremental_execution.slice_v1` compatibility for exact S02;
- Harness must preserve exact PR #14 / exact task branch locked transport and exact S02 write scope;
- if Harness is unavailable, stale, unregistered, lacks required Slice capability, cannot preserve locked transport, or requires the missing PR-014 materialization capability as an ingress prerequisite, bootstrap admission fails closed before product mutation;
- no fallback target is pre-authorized;
- a different target requires a new explicit `#开发引导执行` and full bootstrap admission;
- bootstrap command itself performs no Slice execution.

## 1. Planning objective

Complete PR-014 independently of PR-013 by building the smallest provider-owned path that can create a real isolated Git execution workspace from semantic identity only:

```text
S01 preserved placement/scope/sandbox foundation
        ↓
Host-derived canonical source role
        ↓
provider-owned exact-ref/exact-commit acquisition
        ↓
immutable Git object/worktree source capsule
        ↓
durable scope + audit START
        ↓
AppContainer/Job trusted materializer
        ↓
exact Git checkout readback
        ↓
close temporary sandbox/materializer authority
        ↓
restore Host-owned workspace handoff access
        ↓
user-scoped Git readback
        ↓
development.execution_workspace_materialize receipt
```

The resulting workspace must be directly consumable by registered user-level Development Hosts such as task-scoped `direct:codebuddy`, without caller-selected path, SID, ACL, credential or operation-class authority.

## 2. R2 change impact / preserved work

### 2.1 Preserve S01 without replay

The following completed S01 semantics remain current-compatible:

- `locations.devforge_workspace_root` → DevForge execution-root derivation;
- durable provider Placement Receipt;
- `DevforgeSandboxRootBinding`;
- `DevforgeMutationScopeStore` reuse of the canonical scope authority store;
- provider-selected DevForge sandbox root;
- Windows AppContainer/ACL/Job confinement;
- caller path/root/strategy rejection;
- canonical-like sibling negative-access proof;
- legacy `mutation_execution.workspace_root` / ordinary `scoped_script` compatibility.

Historical completion checkpoint:

```text
docs/checkpoints/PR-014-devforge-execution-workspace-materialization-bridge-v1-s01-completion-20261005.yaml
```

S01 is not re-executed merely because Requirement R2 exists.

Before S02 product mutation, implementation must read current main and reconcile any canonical changes touching the preserved S01 files. Mechanical compatibility fixes are allowed within S02 only when required to preserve R2 semantics; a material semantic conflict stops before mutation.

### 2.2 Invalidate old S02/S03 authority

Plan R2 S02/S03 are not executable because they:

- hard-gate on PR-013 merged/accepted/completion-verified state;
- assume canonical `repository_transaction_v1`/materializer/operation-closure;
- require retained multi-operation lifecycle now outside PR-014 R2 completion scope.

Their historical artifacts remain audit evidence only.

## 3. Self-host bootstrap implementation mode

### 3.1 Why canonical Direct/Codex cannot own S02 entry

PR-014 creates the compliant execution-workspace materialization capability required by the current canonical Direct/Codex self-host path. Requiring Direct/Codex to obtain that missing capability before it can implement S02 reproduces the cycle.

This establishes the bootstrap relation required by the Task-Scoped Bootstrap Execution Override Contract:

~~~text
canonical provider = direct/codex
requires capability X = development.execution_workspace_materialize
this exact Task = PR-014
delivers capability X
~~~

Provider preference or convenience is not the reason for the override.

### 3.2 Explicit S02 Harness bootstrap entry

After Plan R4 is approved and the exact R4 Slice Set is compiled/read back, S02 has this mandatory precondition:

~~~text
#开发引导执行 PR-014-devforge-execution-workspace-materialization-bridge-v1 harness
~~~

Successful bootstrap admission must durably prove:

1. exact Task identity and stage `implementation`;
2. Requirement Revision 2;
3. exact Approved Plan R4 revision/digest;
4. exact current R4 Slice Set and current Slice S02;
5. unchanged project binding `direct/codex`;
6. exact PR #14 + exact task branch transport lock;
7. verified self-host relation above;
8. Harness is a registered/current target;
9. Harness is live/available;
10. Harness consumer can carry `incremental_execution.slice_v1` for exact S02;
11. required canonical transport/write-scope constraints are expressible;
12. no replacement branch/PR, provider fallback, permission expansion, credential expansion, Host-policy mutation or write-scope expansion.

The bootstrap command creates authority only. It does not execute S02.

### 3.3 Canonical transport is persistence, not authority

S02 implementation must persist to:

~~~text
repository = bewaterhere-coder/sentinelx-cloud-core
canonical PR = #14
canonical branch = task/devforge-execution-workspace-materialization-bridge-v1
replacement PR = forbidden
replacement branch = forbidden
fallback transport = forbidden
~~~

Structured repository writes remain allowed only when requested/mediated by the admitted Harness execution contract and within exact S02 write scope.

Forbidden:

- orchestration directly writing S02 implementation and treating repository writes as Development Host execution;
- using GitHub repository API availability as provider authority;
- falling back to canonical Direct/Codex, CodeBuddy, Host Runtime or another provider after Harness failure;
- generic `git clone`, `git worktree`, shell or filesystem bootstrap outside the admitted Harness boundary;
- changing the project binding to Harness.

### 3.4 Harness internal execution boundary

Harness owns its internal execution strategy after ingress. Plan R4 MUST NOT select or encode:

- Development Host identity;
- model/provider identity behind Harness;
- reasoning effort;
- context provider;
- ModelRouter decision;
- Harness workspace mechanism.

Harness may use its own contract-compliant workspace isolation mechanics. It must not require DevForge orchestration to create a Host-local PR-014 execution workspace through the missing `materialize_workspace` capability before ingress.

If current Harness cannot satisfy that boundary, return a blocked bootstrap/execution result and perform zero product mutation.

## 4. Technical design

### D1 — Host-derived canonical source role

PR-014 must not accept a caller source path.

For repository `owner/repo`, derive the source role from current Host DevForge binding:

```text
workspace_root = locations.devforge_workspace_root
repository_root = <workspace_root>/repos
canonical_source = <repository_root>/<owner>/<repo>
```

Admission verifies:

- normalized repository identity;
- expected repository path;
- source checkout exists;
- source checkout origin normalizes to the admitted repository;
- checked-out branch is canonical `main`;
- working tree is clean;
- source checkout != execution workspace;
- source checkout is never switched/reset/merged for materialization.

Concrete source path remains Host evidence only.

### D2 — Exact source identity

Materialization request remains path-free and source-bounded:

```yaml
repository:
  vcs: git
  authority: github.com
  path: owner/repo
lineage:
  project_id:
  task_id:
  run_id:
  attempt_id:
  slice_id:
workspace_purpose:
source_binding:
  expected_ref: refs/heads/<safe-logical-ref>
  expected_commit: <full immutable commit sha>
```

`expected_ref` is authority-bearing source identity, not a remote URL.

Provider independently verifies:

```text
remote expected_ref -> expected_commit
local/provider object -> expected_commit
object format supported
```

V1 supports the repository object format explicitly proven by tests. Unsupported object format fails closed rather than synthesizing hashes.

### D3 — Reuse existing user-scoped Git only as provider transport

Use `sentinelx_core.user_git` as the existing Windows provider-owned Git credential/execution context.

No shell is introduced.

Bounded operations may include provider-generated equivalents of:

- verify source repository/origin/branch/clean;
- `ls-remote` exact expected ref when remote proof is required;
- fixed exact-ref fetch when the object is absent;
- `cat-file` / `ls-tree` / `rev-parse` exact object inspection;
- export exact object/worktree evidence into a provider-selected private capsule path.

Rules:

- caller cannot supply Git argv;
- caller cannot supply remote URL;
- credentials remain inside the active user Git context;
- prompts stay disabled;
- redaction remains active;
- source credential failure maps to stable bounded source-acquisition failure;
- source worktree branch/working tree remains unchanged.

### D4 — Provider-private immutable source capsule

Add a provider-owned source capsule abstraction, recommended module:

```text
src/sentinelx_core/devforge_workspace_source.py
```

The capsule is stored under Agent/provider state, never under caller file_ops/upload space, and contains only bounded materialization inputs/evidence.

Recommended semantic contents:

```text
repository identity
expected_ref
expected_commit
object format
tree manifest
relative worktree entries
Git object payloads required by exact commit
minimal verified remote/ref metadata
content/object digests
capsule manifest digest
```

The provider may create the capsule by reading exact Git objects from the verified source repository/provider cache and converting them to deterministic materializer input.

Capsule requirements:

- no credential material;
- no caller-controlled absolute paths;
- size/file-count ceilings;
- traversal/special-file/symlink/submodule semantics explicit and fail closed when unsupported;
- durable manifest write/readback before workspace materialization;
- exact commit/tree/object hashes independently verified;
- immutable/read-only grant to the materializer;
- temporary grant removed/read back after materialization.

The capsule is not a repository transaction ledger and grants no publication authority.

### D5 — Trusted Git checkout materializer without generic clone

Existing PR-013 evidence already showed ordinary `git clone` inside the AppContainer can fail with Windows DLL initialization. R3 does not retry that design.

Instead, use a provider-generated trusted materializer under the existing AppContainer/Job boundary.

Recommended implementation seam:

```text
src/sentinelx_core/devforge_workspace_materializer.py
```

The materializer:

1. receives only provider-sealed capsule + exact workspace binding;
2. validates manifest/capsule digest;
3. validates every relative path and object;
4. writes worktree files;
5. writes minimal Git metadata/object storage needed for a normal Git checkout;
6. writes `.git/HEAD`, exact branch ref and remote config only from provider-verified source identity;
7. verifies no write escapes exact workspace;
8. never invokes generic network Git;
9. never reads credentials;
10. returns bounded materializer evidence.

A valid result must satisfy normal Git readback after handoff:

```text
git rev-parse --show-toplevel == exact workspace
git rev-parse HEAD == expected_commit
git branch --show-current == admitted logical branch
git remote get-url origin normalizes to admitted repository
git status --porcelain == clean
```

### D6 — Scope and audit ordering

Reuse S01 `DevforgeMutationScopeStore` and `DevforgeWindowsMutationSandbox`.

Required order:

```text
placement receipt durable/read back
→ source capsule durable/read back
→ provision DevForge materialization scope
→ revalidate scope
→ durable OPERATION_STARTED
→ sandbox activate
→ materializer spawn
→ materializer finish/readback
→ workspace Git readback
→ temporary materializer authority closure
→ handoff normalization/readback
→ receipt
```

No workspace directory/source write may occur before durable START.

Allowed operation class for the seed is provider-fixed. Caller operation-class selection remains forbidden.

### D7 — Development Host handoff ACL transition

Current Windows sandbox cleanup intentionally removes AppContainer authority and leaves broker-only exact ACL. That is insufficient when the next consumer is a user-level Development Host.

R3 adds one bounded **Host-owned handoff transition** after successful materialization.

Rules:

- capture/derive expected DevForge workspace inheritance/access from Host-owned execution-root ancestry before temporary exact ACL is installed;
- after materializer process/Job closes, remove AppContainer/temporary grants;
- restore/re-enable only the Host-derived normal DevForge workspace ACL/inheritance state;
- no caller SID, user name, ACL string or permission mask input;
- no ancestor/root ACL widening;
- re-read DACL/final path;
- prove no foreign AppContainer SID remains;
- use user-scoped Git readback in the exact workspace as the V1 user-level Development Host access probe;
- if handoff probe fails, materialization is not `handoff_ready`.

This transition is workspace-local and does not grant authority outside the exact admitted execution workspace.

### D8 — Bounded local_api projection

Extend builtin `devforge_runtime` with:

```text
materialize_workspace
```

Schema is closed and path-free.

Allowed request fields are limited to semantic repository/lineage/workspace-purpose/source binding and optional comparison-only DevForge placement evidence when needed.

Forbidden request fields include:

```text
dest
target_path
workspace_path
checkout_path
worktree_path
cache_path
staging_path
remote_url
credential
token
ssh_key
sid
acl
allowed_write_roots
protected_roots
operation_classes
executable
argv
```

Provider action metadata classifies it as repository/process mutation with canonical firewall coverage proven through S01 scope/sandbox path.

### D9 — Receipt and retry

Persist/read back provider materialization state sufficient to converge exact same-Attempt retry.

Same identity + same source commit + verified complete workspace:

```text
read back
→ return same materialization evidence
→ no replay
```

Same Attempt with changed source/ref/repository/placement:

```text
conflict
→ zero materializer replay
```

Partial/unbound/mismatched target fails closed. Cleanup may touch only provider/Attempt-owned residue and must itself be proven before another materialization attempt.

### D10 — PR-013 relationship

PR-013 is not a gate.

During every slice entry, read its current state only for overlap awareness.

If equivalent PR-013 primitives become canonical on `main` before S02 mutation:

- compare semantics;
- reuse only canonical merged primitives when that reduces duplication without changing Requirement R2;
- do not import unmerged branch code;
- do not replay PR-013 S03;
- material semantic conflict is a Decision Boundary.

General repository transaction, repeated scoped operation closure and publication remain PR-013-owned even after PR-014 completes.

## 5. Implementation slices to compile after approval

The formal R4 Slice Set must preserve historical S01 completion and compile only remaining current-plan work.

### S01 — Preserved historical completion

State after R4 review should be represented as completed/reused evidence, not re-executed.

Evidence:

```text
docs/checkpoints/PR-014-devforge-execution-workspace-materialization-bridge-v1-s01-completion-20261005.yaml
```

No new S01 Run is authorized.

### S02 — Bootstrap-safe source capsule + materialize_workspace

Objective:

Implement the independent seed that turns the preserved S01 placement/scope/sandbox foundation into a path-free exact Git execution-workspace materialization action.

Primary files:

- `src/sentinelx_core/devforge_workspace_source.py` new;
- `src/sentinelx_core/devforge_workspace_materializer.py` new;
- `src/sentinelx_core/devforge_workspace_materialization.py`;
- `src/sentinelx_core/handlers/devforge_runtime.py`;
- `src/sentinelx_core/handlers/__init__.py`;
- `src/sentinelx_core/user_git.py` only for bounded provider source/handoff helpers;
- `src/sentinelx_core/windows_mutation_sandbox.py` or the DevForge subclass only for bounded Host-owned handoff ACL transition;
- focused tests.

Execution mode:

```yaml
bootstrap_required_before_s02: true
bootstrap_target: harness
bootstrap_command: "#开发引导执行 PR-014-devforge-execution-workspace-materialization-bridge-v1 harness"
bootstrap_mode: implementation_bootstrap
project_binding_remains: direct/codex
required_harness_capability: incremental_execution.slice_v1
canonical_transport: github-pr
canonical_pr: 14
task_branch: task/devforge-execution-workspace-materialization-bridge-v1
repository_write_role: persistence_only_inside_admitted_harness_execution
repository_write_scope: exact_S02_files_only
harness_internal_host_selection: opaque
harness_internal_workspace_strategy: opaque
canonical_main_mutation: forbidden
generic_shell_git_workspace_bootstrap: forbidden
provider_fallback: forbidden
```

S02 verification must prove at least:

1. source role path is Host-derived, never caller-provided;
2. wrong origin/branch/dirty source checkout fails closed;
3. exact ref/commit mismatch fails closed;
4. missing object uses only bounded provider Git acquisition or stable credential/transport failure;
5. capsule excludes secrets and is digest-bound;
6. traversal/reparse/ADS/special unsupported entries fail closed;
7. local_api schema has no writable path/credential/SID/ACL/argv authority;
8. scope + durable audit precede first workspace write;
9. materializer runs AppContainer + no-breakaway Job;
10. exact Git checkout readback matches repository/ref/commit;
11. canonical source branch/worktree remain unchanged;
12. temporary source/materializer/AppContainer grants are closed;
13. Host-owned ACL handoff + user-scoped Git probe succeeds on Windows fixture;
14. retry converges without rematerialization;
15. legacy `scoped_script`, canonical firewall, S01 placement/scope/sandbox regressions pass;
16. no PR-013 transaction/publication code is imported.

S02 completion candidate must be durable on PR #14 and exact remote branch read back.

### S03 — Windows physical self-host closure + exact-candidate activation

Depends on S02.

Objective:

Prove the exact S02 candidate can physically provide the missing `development.execution_workspace_materialize` surface on the Windows Host and leave a workspace consumable by a user-level Development Host.

Required flow:

```text
exact S02 candidate
→ existing admitted candidate install/activation workflow
→ installed Agent version/commit readback
→ capabilities readback
→ local_api.describe devforge_runtime
→ materialize_workspace exact benign fixture
→ exact path/source/scope/audit/containment receipt
→ user-scoped Git handoff probe
→ retry no-replay
→ canonical source main+clean readback
→ security regression
```

S03 must prove:

- `materialize_workspace` is live and discoverable;
- request remains path-free;
- exact workspace is under Host DevForge execution root;
- expected commit and clean Git state read back;
- CodeBuddy-equivalent active interactive user Git access succeeds;
- canonical checkout remains `main + clean`;
- no generic Git/worktree/shell/file fallback was used;
- no Host policy/allowlist/credential expansion occurred;
- PR-013 S03 was not executed/replayed;
- PR-013 current state is informational only, not a gate.

If live activation requires a separately protected install/restart authority, use that existing workflow and persist its receipt. No activation receipt means no S03 completion claim.

## 6. Acceptance mapping

Requirement R2 acceptance mapping:

- AC1–AC3 → preserved S01 + S02 placement/schema negatives.
- AC4–AC6 → S02 source broker/capsule.
- AC7–AC9 → S02 audit/materializer/receipt.
- AC10 → S02 handoff + S03 physical user-level readback.
- AC11 → S02 unit/integration retry + S03 physical retry.
- AC12 → S02/S03 PR-013-independent execution evidence.
- AC13 → S02/S03 regression suite.
- AC14 → S03 Windows physical E2E.
- AC15 → code inventory proves no retained multi-operation/publication implementation.
- AC16 → policy/transport/security readback.

Acceptance cannot rely solely on unit tests for AC10/AC14.

## 7. Security / authority invariants

R3 must preserve:

1. caller_never_selects_execution_workspace_path
2. caller_never_selects_source_checkout_path
3. caller_never_selects_remote_url_or_credentials
4. caller_never_selects_sid_acl_or_write_roots
5. exact_source_commit_is_immutable_authority
6. canonical_source_worktree_remains_main_and_clean
7. no_audit_start_no_workspace_write
8. materializer_runs_inside_existing_appcontainer_job_boundary
9. temporary_materializer_authority_is_closed_before_handoff
10. handoff_access_is_host_owned_not_caller_owned
11. canonical_repository_firewall_remains_effective
12. retry_never_replays_verified_materialization
13. pr013_is_not_completion_dependency
14. pr013_s03_replay_is_forbidden
15. unmerged_pr013_code_import_is_forbidden
16. canonical_main_is_not_implementation_workspace
17. non_host_local_s02_bootstrap_is_predeclared_not_error_fallback
18. no_receipt_no_completion_claim

## 8. Risks and mitigations

### Risk A — Source capsule accidentally becomes a general source broker

Mitigation: private provider module, closed local_api schema, exact repo/ref/commit only, no caller paths/URLs/argv, no publication API.

### Risk B — Git object reconstruction produces a worktree but invalid Git metadata

Mitigation: exact Git readback after handoff is mandatory; materializer completion alone cannot produce success.

### Risk C — Canonical source object acquisition mutates working tree

Mitigation: pre/post branch + status + HEAD readback; only bounded object/ref transport operations allowed; checkout/reset/merge/worktree operations forbidden.

### Risk D — AppContainer cleanup leaves workspace inaccessible to CodeBuddy

Mitigation: explicit Host-owned ACL handoff transition plus user-scoped Git probe before `handoff_ready=true`.

### Risk E — ACL handoff becomes permission expansion

Mitigation: derive only from Host execution-root inheritance/access; no caller principal/mask; no ancestor changes; exact DACL/final-path readback.

### Risk F — Current main has drifted since S01

Mitigation: before S02 mutation compare current canonical main on S01/handler/user_git/sandbox surfaces. Preserve S01 semantic results; stop on material conflict.

### Risk G — PR-013 lands during execution

Mitigation: impact reconciliation only; use merged canonical primitive if compatible, never import unmerged code or replay S03.

### Risk H — Harness bootstrap target unavailable or incompatible

Mitigation: availability/capability is not assumed by Plan prose. After Plan approval + exact Slice Set compilation, explicit `#开发引导执行 ... harness` must verify registered/current Harness, exact Slice support, locked transport compatibility and unchanged authority. Failure stops before product mutation with no fallback.

### Risk I — Repository write capability is mistaken for execution authority

Mitigation: Plan R4 explicitly defines repository API/write as persistence mechanics only inside admitted Harness execution. Orchestration cannot implement S02 directly through repository writes.

### Risk J — Harness internally depends on the capability being created

Mitigation: bootstrap admission/execution must prove Harness can execute exact S02 without requiring PR-014 `materialize_workspace` as its ingress prerequisite. Otherwise fail closed; do not create a generic Host workspace.

## 9. Review questions

Plan Review R4 must explicitly decide:

1. Does the explicit `#开发引导执行 ... harness` precondition close `BootstrapExecutionAuthorityUndefined` without changing the project binding?
2. Is the self-host relation exact: canonical Direct/Codex needs the materialization capability and PR-014 delivers that same capability?
3. Is GitHub PR #14 correctly treated only as locked transport/persistence rather than execution-provider authority?
4. Does Harness remain Host/model/context/workspace opaque while still requiring verified `incremental_execution.slice_v1` compatibility for S02?
5. Does Harness failure stop before mutation with no fallback to direct/codex, CodeBuddy, Host Runtime or orchestration-side repository writes?
6. Does R4 preserve S01 without replay while correctly invalidating old R2 S02/S03 authority?
7. Is the narrow source capsule/materializer seed sufficiently bounded to avoid absorbing PR-013 general transaction/publication ownership?
8. Does the Host-owned ACL handoff avoid both AppContainer-only dead-end access and caller-driven permission expansion?
9. Is exact Git readback sufficient to prove the workspace is usable by a normal user-level Development Host?
10. Are PR-013 state and code treated only as overlap evidence, never as completion gate or replay authority?
11. Can S02/S03 complete Requirement R2 AC1–AC16 without any hidden dependency on the missing `materialize_workspace` capability at S02 ingress?

## 10. Post-plan state

After this Plan is durably persisted/read back:

```yaml
stage: plan_review
requirement_revision: 2
plan_revision: 4
plan_approved: false
implementation_authorized: false
current_slice: null
completed_slices_preserved: [S01]
next_expected_actor: reviewer
```

No R4 execution Slice exists until Plan Review approves R4 and compiles the exact current Slice Set. After that, S02 still cannot execute until the explicit Harness bootstrap override is admitted and read back.
