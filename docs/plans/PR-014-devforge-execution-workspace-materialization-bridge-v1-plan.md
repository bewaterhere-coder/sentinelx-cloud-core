# PR-014 — SentinelX DevForge Execution Workspace Materialization Bridge V1 — Plan R3

## Plan State

```yaml
task_id: PR-014-devforge-execution-workspace-materialization-bridge-v1
plan_revision: 3
plan_status: ready_for_review
implementation_authority: false
requirement_ref: docs/requirements/PR-014-devforge-execution-workspace-materialization-bridge-v1.md
requirement_revision: 2
requirement_blob_sha: a40d84d4af112308c9f74301813b39bf487eabb5
requirement_change_impact: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-requirement-r2-invalidation.md
prior_plan_revision: 2
prior_plan_blob_sha: bf40efdd1c4804ea6ef5f858e22d2e558fdd8e70
transport:
  type: github-pr
  pr_number: 14
  branch: task/devforge-execution-workspace-materialization-bridge-v1
  base_branch: main
planning_baseline:
  sentinelx_main: 1028030b33f0ea792a884491a431fffe566f6aa5
  task_head_before_plan_r3: e2606cac7e357f786915caa338039d04eb1c7519
  devforge_main: 5efc2d2b1eabe209d599f08ba5f9574771851374
  devforge_release: v2.97.0
project_binding:
  provider: direct
  adapter: codex
  source: explicit_project_binding
completed_evidence_preserved:
  - S01
implementation_authorized: false
```

Plan R3 supersedes Plan R2 because Requirement R2 materially removes the PR-013 completion dependency and narrows PR-014 V1 to bootstrap-safe workspace materialization + Development Host handoff.

No product implementation is authorized until this Plan is reviewed and an exact R3 Slice Set is compiled.

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

### 3.1 Why Host-local implementation cannot be the first R3 mutation path

PR-014 creates the Host-local materialization capability required by current DevForge workspace admission. Requiring a newly materialized Host-local execution workspace to implement S02 would reproduce the same self-host cycle.

### 3.2 Explicit S02 bootstrap execution mode

S02 is therefore predeclared as a **non-Host-local canonical repository-transport bootstrap slice**.

Allowed implementation persistence:

```text
existing GitHub PR #14
+ exact task branch
+ structured repository writes
+ exact remote branch readback
```

Rules:

- no Host-local product workspace is created for S02;
- canonical `main` is read-only;
- no new branch/PR/Task;
- no generic shell/exec/Git clone/worktree;
- no provider fallback selected after an error;
- repository-write bootstrap is declared by this Plan before execution and must be explicitly approved by Plan Review;
- changed product files remain bounded to S02 scope;
- implementation verification uses repo-controlled tests/CI plus later Windows physical S03 evidence;
- this bootstrap mode expires after S02 establishes the reviewed `materialize_workspace` candidate.

This is not a project-binding change. The project registry remains `direct/codex`; the bootstrap is a Slice-specific execution strategy owned by the Approved Plan/DevForge command boundary.

If Plan Review determines this repository-transport bootstrap is not authorized by current DevForge Core, the Plan must be rejected before implementation rather than silently substituting Direct Codex/CodeBuddy/Host Runtime.

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

The formal R3 Slice Set must preserve historical S01 completion and compile only remaining current-plan work.

### S01 — Preserved historical completion

State after R3 review should be represented as completed/reused evidence, not re-executed.

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
bootstrap_mode: canonical_repository_transport
host_local_product_workspace: forbidden
canonical_main_mutation: forbidden
task_branch: task/devforge-execution-workspace-materialization-bridge-v1
repository_write_scope: exact_S02_files_only
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

### Risk H — S02 bootstrap repository-write mode is not currently admitted

Mitigation: Plan Review must explicitly decide this. If rejected, stop at Plan Review; do not silently route to Direct Codex/CodeBuddy/Host Runtime.

## 9. Review questions

Plan Review R3 must explicitly decide:

1. Is the S02 non-Host-local canonical repository-transport bootstrap mode admissible under current DevForge `development.execute` repository.write authority for this self-host case?
2. Does R3 preserve S01 without replay while correctly invalidating old S02/S03 authority?
3. Is the narrow source capsule/materializer seed sufficiently bounded to avoid absorbing PR-013 general transaction/publication ownership?
4. Does the Host-owned ACL handoff avoid both AppContainer-only dead-end access and caller-driven permission expansion?
5. Is exact Git readback sufficient to prove the workspace is usable by a normal user-level Development Host?
6. Are PR-013 state and code treated only as overlap evidence, never as completion gate or replay authority?
7. Can the two remaining slices complete Requirement R2 AC1–AC16 without a hidden dependency on the missing `materialize_workspace` capability?

## 10. Post-plan state

After this Plan is durably persisted/read back:

```yaml
stage: plan_review
requirement_revision: 2
plan_revision: 3
plan_approved: false
implementation_authorized: false
current_slice: null
completed_slices_preserved: [S01]
next_expected_actor: reviewer
```

No R3 execution Slice exists until Plan Review approves R3 and compiles the exact current Slice Set.
