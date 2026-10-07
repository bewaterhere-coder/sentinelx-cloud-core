# PR-014 — SentinelX DevForge Execution Workspace Materialization Bridge V1 — Plan R5

## Plan State

```yaml
task_id: PR-014-devforge-execution-workspace-materialization-bridge-v1
plan_revision: 5
plan_status: ready_for_review
implementation_authority: false
requirement_ref: docs/requirements/PR-014-devforge-execution-workspace-materialization-bridge-v1.md
requirement_revision: 2
requirement_blob_sha: 5f3911e49e92722ffd2723aaa14e75e7bc00d9c0
requirement_change_impact: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-requirement-r2-invalidation.md
prior_plan_revision: 4
prior_plan_blob_sha: 2c930c0f9dc8c901691ebd8819f1f0bd19d6dc50
superseded_plan_review_ref: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-plan-review-r4.md
superseded_plan_review_blob_sha: 3de8413c84733f8c233762965e3500cc3c307608
superseded_slice_set_ref: docs/execution/PR-014-devforge-execution-workspace-materialization-bridge-v1-plan-r4-slices.yaml
superseded_slice_set_blob_sha: c8786d85e081986e3d3c4ed7ede2f290a8756f7e
replan_trigger_ref: docs/checkpoints/PR-014-devforge-execution-workspace-materialization-bridge-v1-harness-bootstrap-blocked-20261008.yaml
transport:
  type: github-pr
  pr_number: 14
  branch: task/devforge-execution-workspace-materialization-bridge-v1
  base_branch: main
planning_baseline:
  sentinelx_main: 1028030b33f0ea792a884491a431fffe566f6aa5
  task_head_before_plan_r5: 8e30a2b3a3c35f9ad9ca90449b8e0dec6b39439a
  devforge_main: 050d9c9559a173a3e0b37fcd2a9db702b6b5a7e6
  devforge_release: v2.98.0
project_binding:
  provider: direct
  adapter: codex
  source: explicit_project_binding
completed_evidence_preserved:
  - S01
implementation_authorized: false
```

Plan R5 is a user-directed implementation replan that preserves Requirement R2 and S01 completed evidence while replacing the blocked R4 execution-entry design.

R4 proved that Harness bootstrap is not bootstrap-safe for this Task today: Harness itself requires `incremental_execution.slice_v1`, whose completion path participates in the cycle `PR-014 → PR-229 → PR-020 → PR-014`.

R5 removes all PR-229 and PR-020 prerequisites from PR-014. The S02 seed is implemented through DevForge's existing explicit Task-scoped bootstrap boundary, using a direct Development Adapter and canonical repository persistence without a Host-local execution workspace.

## R5 Replan Delta — bootstrap-safe repository projection without Harness or workspace ingress

Plan R5 changes no Requirement R2 semantics, product scope, Host placement policy, canonical transport, S01 evidence, security boundary, PR-013 ownership split, or final materialize-workspace behavior.

It replaces only the bootstrap execution entry.

### Dependency cycle being removed

~~~text
R4:
PR-014 S02
→ Harness bootstrap
→ incremental_execution.slice_v1
→ PR-229
→ durable async / PR-020 dependency
→ PR-014 materialization dependency
→ cycle
~~~

R5:

~~~text
Requirement R2
→ Approved Plan R5 exact revision/digest
→ exact R5 Slice Set compiled/read back
→ Task stage = implementation
→ explicit #开发引导执行 PR-014-devforge-execution-workspace-materialization-bridge-v1 direct:codebuddy
→ bootstrap contract verifies exact self-host relation + registered/current direct target
→ later explicit #开发执行
→ exact S02 only
→ direct Development Host reads canonical PR
→ structured repository.write persists only exact S02 source/test files to PR #14 branch
→ exact branch/commit readback + existing repository-hosted verification evidence
→ S02 completion receipt
→ implementation execution complete
→ Acceptance owns exact-candidate Windows physical materialization verification
~~~

### Authority rules

- project binding remains `direct/codex`;
- canonical Direct/Codex remains the blocked provider for the self-host relation because its normal Host-local implementation path requires `development.execution_workspace_materialize`;
- the bootstrap target is `direct:codebuddy`, a different registered Development Adapter, selected only by the explicit Task-scoped bootstrap override;
- target registration/availability is NOT assumed by this Plan and must be proven by the later bootstrap command;
- the override is the execution authority; GitHub/repository transport is persistence only;
- DevForge `repository.write` may be used only after the active override is re-read and only for exact S02 source/test paths on canonical PR #14 branch;
- no local execution workspace is created for S02 seed implementation;
- no Harness contract/invocation is used;
- no `incremental_execution.slice_v1` consumer capability is required because the execution target is direct, not Harness;
- no `development.execution_workspace_materialize` capability is required to implement the seed because the seed is persisted through canonical repository APIs, not a Host-local mutation workspace;
- no PR-020 durable async operation is required: seed persistence consists of bounded repository writes with commit/branch readback and externally observable verification receipts;
- no generic Git, shell, `script_run`, generic filesystem write, caller-selected Host path, Host-policy expansion, credential expansion, permission expansion or write-scope expansion is authorized;
- bootstrap execution cannot modify `main`, create/replace branch or PR, modify workflow files, or migrate transport;
- PR-013 S03 remains forbidden to replay.

### R4 evidence treatment

The R4 approved review, R4 Slice Set, and blocked Harness bootstrap receipt remain historical evidence.

They MUST NOT authorize R5 execution because Plan revision drift invalidates the R4 Slice Set and the R4 bootstrap target assumption.

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

## 3. Bootstrap-safe S02 implementation mode

### 3.1 Verified self-host relation

The canonical project binding remains:

~~~yaml
provider: direct
adapter: codex
~~~

The current canonical Direct/Codex self-host path requires the exact capability PR-014 creates:

~~~text
blocked provider = direct/codex
missing capability X = development.execution_workspace_materialize
this exact Task = PR-014
delivers capability X
~~~

This is a valid Task-Scoped Bootstrap Execution Override relation. Provider preference is not the reason for the override.

### 3.2 Explicit direct CodeBuddy bootstrap entry

After Plan R5 is approved and the exact R5 Slice Set is compiled/read back, S02 has this mandatory precondition:

~~~text
#开发引导执行 PR-014-devforge-execution-workspace-materialization-bridge-v1 direct:codebuddy
~~~

Admission must durably prove:

1. exact Task identity;
2. Task stage = `implementation`;
3. Requirement Revision 2;
4. exact Approved Plan R5 revision/digest;
5. exact current R5 Slice Set and S02;
6. unchanged project binding `direct/codex`;
7. exact canonical PR #14 + exact task branch;
8. self-host relation above;
9. `direct:codebuddy` is a registered/current target;
10. the target is currently available;
11. current execution environment exposes only the repository read/write/observe surfaces required by the seed;
12. no replacement branch/PR, fallback, permission expansion, credential expansion, Host-policy mutation or write-scope expansion.

The bootstrap command creates authority only. It does not execute S02.

If CodeBuddy is unavailable or cannot satisfy exact repository-projection constraints, bootstrap fails before product mutation. No fallback target is pre-authorized.

### 3.3 Repository-projection bootstrap boundary

S02 seed implementation intentionally does **not** require a Host-local execution workspace.

Allowed execution mechanics:

~~~yaml
development_host: direct:codebuddy
canonical_transport: github-pr
repository: bewaterhere-coder/sentinelx-cloud-core
canonical_pr: 14
canonical_branch: task/devforge-execution-workspace-materialization-bridge-v1
read_surface: repository.read
write_surface: repository.write
write_mode: exact_branch_structured_persistence
expected_head_compare_and_set: required
post_write_branch_readback: required
workflow_observe: existing_repository_verification_only
local_workspace_required: false
~~~

The direct Development Host may inspect canonical source through repository reads, reason about the exact S02 patch, and persist source/test changes through structured repository writes.

Repository API availability is not provider authority. The active Task-scoped bootstrap override is authority.

### 3.4 Seed write scope

The R5 Plan Review/Slice Set must freeze the exact S02 path allowlist. It may include only the minimal materialization implementation and focused tests required by D1–D10, expected primarily under:

~~~text
src/sentinelx_core/devforge_workspace_source.py
src/sentinelx_core/devforge_workspace_materializer.py
src/sentinelx_core/devforge_workspace_materialization.py
src/sentinelx_core/handlers/devforge_runtime.py
src/sentinelx_core/handlers/__init__.py
src/sentinelx_core/user_git.py
src/sentinelx_core/windows_mutation_sandbox.py
tests/test_devforge_workspace_*.py
tests/test_devforge_runtime_local_api.py
focused directly-related tests
~~~

Any additional production path requires explicit Slice-bound justification before mutation.

Always forbidden for bootstrap seed execution:

~~~text
generic git
git clone
git worktree
shell
script_run
generic host filesystem edit/write
caller-selected local path
workflow-file modification
main-branch write
replacement branch
replacement PR
Host policy/allowlist change
credential mutation
permission expansion
write-scope expansion
PR-013 S03 replay
~~~

### 3.5 Verification without PR-020

The seed path contains no long-running Host execution whose lost transport response would require PR-020.

Every material persistence step must be recoverable by canonical readback:

~~~text
expected PR-head SHA
→ bounded repository write
→ returned commit SHA
→ re-read PR #14 head
→ re-read changed file blobs
~~~

Existing repository-hosted CI/checks MAY be consumed as verification evidence only when they run against the exact resulting PR head. S02 bootstrap may not modify CI workflows or inject an ad-hoc generic shell job.

Lost write/check response is reconciled by GitHub branch/check readback before retry. Blind replay is forbidden.

## 4. Technical design

### D0 — Bootstrap seed versus runtime materialization boundary

R5 separates **how the seed code is persisted** from **what the seed code is allowed to do at runtime**.

Bootstrap seed persistence:

~~~text
direct:codebuddy
→ repository.read
→ structured repository.write to exact PR branch
→ readback
~~~

Runtime `materialize_workspace` behavior after the candidate is activated:

~~~text
path-free local_api request
→ Host-owned placement
→ source evidence/capsule
→ Host-owned mutation scope
→ durable pre-execution audit START
→ existing AppContainer/Job sandbox
→ contained materializer
→ exact Git readback
→ temporary-authority closure
→ Host-owned handoff access
→ receipt
~~~

The bootstrap persistence route MUST NOT become a runtime workspace-materialization fallback.

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

Existing PR-013 evidence already showed ordinary `git clone` inside the AppContainer can fail with Windows DLL initialization. R5 does not retry that design.

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

R5 preserves one bounded **Host-owned handoff transition** after successful materialization.

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

The formal R5 Slice Set must preserve historical S01 completion and compile exactly one remaining implementation Slice.

### S01 — Preserved historical completion

State after R5 review is completed/reused evidence, never re-executed.

Evidence:

~~~text
docs/checkpoints/PR-014-devforge-execution-workspace-materialization-bridge-v1-s01-completion-20261005.yaml
~~~

Before S02 mutation, current canonical main must be compared against relevant S01 placement/scope/sandbox seams. A material semantic conflict stops at a Decision Boundary; it does not authorize S01 replay.

### S02 — Bootstrap-safe minimal materialize_workspace seed

Objective:

Implement the smallest complete path-free `devforge_runtime.materialize_workspace` candidate that reuses S01 and satisfies the runtime safety design D1–D10, while implementation persistence itself uses no Host-local execution workspace.

Execution mode:

~~~yaml
bootstrap_required_before_s02: true
bootstrap_target: direct:codebuddy
bootstrap_command: "#开发引导执行 PR-014-devforge-execution-workspace-materialization-bridge-v1 direct:codebuddy"
bootstrap_mode: implementation_bootstrap
project_binding_remains: direct/codex
harness_required: false
incremental_execution_slice_consumer_required: false
execution_workspace_materialize_required_for_seed_persistence: false
canonical_transport: github-pr
canonical_pr: 14
task_branch: task/devforge-execution-workspace-materialization-bridge-v1
seed_persistence:
  repository_read: allowed
  repository_write: exact_S02_paths_only
  expected_head_cas: required
  readback: required
  local_workspace: forbidden
generic_git: forbidden
shell: forbidden
script_run: forbidden
generic_host_filesystem_write: forbidden
caller_host_path_authority: forbidden
provider_fallback: forbidden
~~~

S02 implementation scope remains the D1–D10 materialization design, including:

- Host-derived canonical source role;
- exact repository/ref/commit verification;
- provider-private immutable source capsule;
- trusted contained checkout materializer;
- preserved S01 placement/scope/sandbox;
- durable pre-execution audit ordering;
- bounded Host-owned ACL/handoff transition;
- closed path-free `materialize_workspace` local_api schema;
- materialization receipt and same-Attempt no-replay;
- explicit PR-013 non-dependency.

S02 bootstrap verification must prove before Slice completion:

1. active `direct:codebuddy` bootstrap override was durably read back before the first source mutation;
2. every source mutation occurred only on canonical PR #14 task branch through structured repository persistence;
3. no write targeted canonical `main`;
4. exact before/after PR-head SHA and changed blobs were read back;
5. changed paths remained inside the exact R5 S02 allowlist;
6. no workflow file, Host policy, credential, permission or project binding changed;
7. no generic Git/shell/`script_run`/generic Host filesystem path was used;
8. no Harness invocation or Harness Slice capability was used;
9. no PR-020 durable async runtime was required;
10. no PR-013 S03 replay or unmerged PR-013 import occurred;
11. focused code/schema/tests for D1–D10 are present and internally coherent;
12. existing repository-hosted verification evidence for the exact PR head is read back when available/required by repository policy;
13. deterministic static/import/schema failures block completion and are repaired only within the same exact Slice/write scope;
14. completion receipt binds exact Task/Plan/Slice/PR branch/head/changed paths and verification evidence.

S02 completion is an implementation checkpoint, not physical Windows Acceptance.

After S02 is the only remaining implementation Slice and is verified complete, implementation execution is complete. The Task may advance to Acceptance under the normal owning command.

No S03 implementation Slice exists in R5.

## 6. Acceptance mapping

Requirement R2 acceptance mapping:

- AC1–AC3 → preserved S01 + S02 closed schema/placement-path negatives.
- AC4–AC6 → S02 source role/source acquisition/capsule implementation evidence plus Acceptance live negatives.
- AC7–AC9 → S02 audit/materializer/receipt implementation plus Acceptance runtime readback.
- AC10 → Acceptance physical Host-owned handoff + registered Development Host usability probe.
- AC11 → S02 deterministic no-replay implementation tests + Acceptance physical retry/readback.
- AC12 → S02 bootstrap receipt must prove completion without PR-013/PR-229/PR-020 completion.
- AC13 → S02 regression evidence + Acceptance exact-candidate regression checks.
- AC14 → **Acceptance** performs Windows physical integration on the exact S02 candidate.
- AC15 → code inventory in S02/Acceptance proves no PR-013 multi-operation/publication ownership was absorbed.
- AC16 → S02 bootstrap receipt + Acceptance readback prove no Host policy/allowlist widening, no generic fallback and no independent Codex requirement.

### Acceptance exact-candidate physical gate

Acceptance MUST NOT infer AC8/AC10/AC14 from source or CI alone.

It must use the existing separately authorized exact-candidate activation/verification workflow and persist/read back evidence equivalent to:

~~~text
exact S02 PR-head candidate
→ activate/install exact candidate through existing protected workflow
→ installed candidate commit/version readback
→ capabilities/local_api.describe readback
→ path-free materialize_workspace benign request
→ Host-derived placement readback
→ source capsule/scope/audit/AppContainer/Job evidence
→ exact Git HEAD/branch/origin/clean readback
→ temporary-authority closure
→ user-level Development Host handoff probe
→ same-identity retry no-replay
→ canonical source main + clean
→ security regressions
~~~

Acceptance verification MUST NOT use generic git/shell/`script_run` as a workspace-materialization fallback and MUST NOT replay PR-013 S03.

## 7. Security / authority invariants

R5 preserves:

1. caller_never_selects_execution_workspace_path
2. caller_never_selects_source_checkout_path
3. caller_never_selects_remote_url_or_credentials
4. caller_never_selects_sid_acl_or_write_roots
5. exact_source_commit_is_immutable_authority
6. canonical_source_worktree_remains_main_and_clean
7. no_audit_start_no_runtime_workspace_write
8. materializer_runs_inside_existing_appcontainer_job_boundary
9. temporary_materializer_authority_is_closed_before_handoff
10. handoff_access_is_host_owned_not_caller_owned
11. canonical_repository_firewall_remains_effective
12. retry_never_replays_verified_materialization
13. pr013_is_not_completion_dependency
14. pr013_s03_replay_is_forbidden
15. unmerged_pr013_code_import_is_forbidden
16. canonical_main_is_not_implementation_workspace
17. bootstrap_seed_persistence_requires_explicit_task_override
18. repository_write_is_persistence_not_provider_authority
19. bootstrap_seed_has_no_host_local_workspace
20. harness_and_pr229_are_not_pr014_dependencies
21. pr020_is_not_pr014_seed_dependency
22. generic_git_shell_script_run_fallback_is_forbidden
23. seed_write_scope_is_exact_and_cannot_expand
24. no_receipt_no_completion_claim

## 8. Risks and mitigations

### Risk A — Repository projection is mistaken for execution authority

Mitigation: only explicit `#开发引导执行 ... direct:codebuddy` creates Task authority. Repository APIs are persistence mechanics after override readback.

### Risk B — Direct target secretly requires a local workspace

Mitigation: bootstrap/execute preflight must prove the selected target can satisfy the R5 repository-projection tool surface without creating a Host-local workspace. Otherwise stop before mutation; no fallback.

### Risk C — Structured writes drift across commits

Mitigation: bind every mutation window to expected current PR-head/file blob identity, then re-read exact PR head and changed blobs. Drift forces re-read/recompile before another write.

### Risk D — Seed write scope becomes a generic repository mutation channel

Mitigation: R5 Slice Set freezes exact source/test path allowlist; workflow/config/credential/security metadata paths are denied unless explicitly part of the reviewed S02 product change.

### Risk E — Lack of local test execution hides syntax/integration failure

Mitigation: require deterministic source/schema review and consume existing repository-hosted verification against exact PR head. Acceptance still performs exact-candidate physical proof; no source-only Acceptance claim.

### Risk F — Product seed accidentally bypasses S01 sandbox

Mitigation: D0 explicitly separates seed persistence from runtime behavior. Runtime action must route through preserved S01 placement/scope/sandbox/audit/firewall. Repository projection is never a runtime fallback.

### Risk G — Canonical source object acquisition mutates source worktree

Mitigation: D1–D4 preserve pre/post branch/status/HEAD readback and only fixed provider-owned Git operations inside product runtime; no bootstrap executor Git commands.

### Risk H — AppContainer cleanup leaves workspace unusable

Mitigation: D7 Host-owned handoff transition + Acceptance user-level Git probe.

### Risk I — PR-013 lands during R5

Mitigation: compare only canonical merged semantics. No unmerged import and no PR-013 S03 replay.

### Risk J — PR-229 or PR-020 changes independently

Mitigation: they are not admission dependencies for R5. Later canonical improvements may be reused only if they are already merged and do not alter Requirement R2 semantics.

## 9. Review questions

Plan Review R5 must explicitly decide:

1. Does `direct:codebuddy` under the existing Task-scoped bootstrap contract provide valid execution authority without changing project binding?
2. Is the self-host relation still exact: canonical Direct/Codex needs `development.execution_workspace_materialize`, and PR-014 delivers it?
3. Does direct-adapter execution avoid the Harness `incremental_execution.slice_v1` requirement without weakening DevForge one-execute/one-Slice semantics?
4. Is structured repository persistence sufficient to implement the S02 seed without creating a Host-local execution workspace?
5. Is repository.write clearly persistence only, with authority coming from the active bootstrap override?
6. Are exact PR-head CAS, path allowlist and readback sufficient to prevent transport/write-scope drift?
7. Does S02 avoid generic git/shell/`script_run`/filesystem bootstrap and all caller path authority?
8. Can the D1–D10 product runtime still satisfy Requirement R2 without using the bootstrap persistence route as a runtime fallback?
9. Is moving Windows physical proof from S03 implementation into Acceptance valid while still preventing source-only acceptance?
10. Does the one-pending-Slice R5 model allow the bootstrap override to become unnecessary after S02 implementation completes?
11. Are PR-013, PR-229 and PR-020 all non-gating for R5 S02 bootstrap completion?
12. Does R5 preserve S01 evidence without replay and correctly invalidate the R4 Slice Set?
13. Are current DevForge v2.98.0 bootstrap/slicing contracts sufficient without inventing a new bootstrap capability or Development Gate?

## 10. Post-plan state

After this Plan is durably persisted/read back:

~~~yaml
stage: plan_review
requirement_revision: 2
plan_revision: 5
plan_approved: false
implementation_authorized: false
current_slice: null
current_slice_set: null
completed_slices_preserved: [S01]
superseded_slice_set: plan-r4
bootstrap_override_state: absent
next_expected_actor: reviewer
~~~

No R5 execution Slice Set exists until Plan Review approves R5 and compiles/read-backs the exact current Slice Set.

If R5 is approved, the canonical next execution-authority command is expected to be:

~~~text
#开发引导执行 PR-014-devforge-execution-workspace-materialization-bridge-v1 direct:codebuddy
~~~

That command still must prove the target is registered/current/available before any implementation mutation.
