# PR-014 — SentinelX DevForge Execution Workspace Materialization Bridge V1 — Plan R7

## Plan State

```yaml
task_id: PR-014-devforge-execution-workspace-materialization-bridge-v1
plan_revision: 7
plan_status: ready_for_review
implementation_authority: false
requirement_ref: docs/requirements/PR-014-devforge-execution-workspace-materialization-bridge-v1.md
requirement_revision: 3
requirement_blob_sha: 3df1b5b9809fdd4ab0ac121aad7f0c004ad1a627
requirement_change_impact: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-requirement-r3-change-impact.md
prior_plan_revision: 6
prior_plan_blob_sha: 4fc74fba9d787120798d5ed6a4f04b7da9cb6a5f
superseded_plan_review_ref: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-plan-review-r6.md
superseded_plan_review_blob_sha: c9798c848dc2769f0ccd9ae7c6fc5e8aeec9a026
superseded_slice_set_ref: docs/execution/PR-014-devforge-execution-workspace-materialization-bridge-v1-plan-r6-slices.yaml
superseded_slice_set_blob_sha: f332c20ca398507a635f0c4abc6a1f43117c8dc6
replan_trigger_ref: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-acceptance-r2.md
transport:
  type: github-pr
  pr_number: 14
  branch: task/devforge-execution-workspace-materialization-bridge-v1
  base_branch: main
planning_baseline:
  sentinelx_main: cd42e371f18056327c1d8b744f8956a76bc11541
  task_head_before_plan_r7: bd49d5cad275f16f5abec8d3e026a616d30c1af3
  devforge_main: e0ea49441c410a7008fbcd61f1782d90f014a773
  devforge_release: v2.103.0
project_binding:
  provider: direct
  adapter: codex
  source: explicit_project_binding
completed_evidence_preserved:
  - S01
  - S02_product_candidate_45dc99d15a23c499b4c1500fab60ed5e76475aeb
  - S02_completion_checkpoint
  - S02_completion_receipt
  - S02_r6_reconciliation_receipt
implementation_authorized: false
```
## R7 Architecture Repair — independent source/placement binding + durable scope schema compatibility

Acceptance R2 physically activated exact candidate `45dc99d15a23c499b4c1500fab60ed5e76475aeb` and exposed two material issues:

1. `D:\coco\workspaces` is structurally inside broad protected root `D:\coco`, so the previous placement topology must fail closed;
2. existing durable MutationScope state may contain compatible additive fields written by newer runtimes (observed: `runtime_read_authority_roots`) that the R5/R6 candidate cannot deserialize.

The Human decision accepts the Acceptance R2 recommendation.

### R7 topology

~~~text
canonical source binding
  Host canonical repository inventory
  → D:\coco\repos\<owner>\<repository>
  → protected + source-only

execution placement binding
  locations.devforge_execution_workspace_root
  → preferred Host value D:\SentinelX\devforge-workspaces
  → outside every protected/canonical root
  → exact workspace derived from semantic identity only
~~~

These are two independent Host-owned bindings.

The old `locations.devforge_workspace_root=D:\coco` value is not a PR-014 execution placement authority after R3/R7.

### Protected-root invariant

R7 MUST NOT solve placement by weakening protection.

Forbidden:

~~~text
remove D:\coco from protected_roots
narrow D:\coco protected_root
carve out D:\coco\workspaces
add a broad allowlist exception
caller-select execution path
fallback to mutation_execution.workspace_root
materialize in canonical checkout
~~~

### MutationScope durable-state compatibility

R7 repairs the reader/migration boundary rather than deleting state.

Required:

- known additive fields are parsed/migrated with explicit defaults;
- `runtime_read_authority_roots` is understood and preserved;
- additive fields survive read/write round-trip;
- unknown authority-bearing fields fail as schema incompatibility, not silently ignored;
- durable state deletion is forbidden as a repair;
- existing nonterminal authority is never widened during migration.

### Evidence preservation

R7 does not invalidate the fact that S01/S02 implementation work occurred.

Preserve:

~~~text
S01 historical completion evidence
S02 product candidate 45dc99d15a23c499b4c1500fab60ed5e76475aeb
S02 completion checkpoint/receipt
S02 R6 reconciliation evidence
147 passed / 1 skipped / 0 failed
9/9 changed blobs byte-identical
~~~

But R7 introduces one **delta repair Slice** because the physical Acceptance findings require new code.

No S01 or S02 product mutation may be replayed.


## R6 Verification Policy Repair — CI removed from this Task gate

Plan R6 is a verification-policy-only revision. It does not change Requirement R2, the S02 implementation design, product scope, canonical transport, security boundaries, or the completed S02 product candidate.

Preserved implementation evidence:

~~~yaml
s02_product_candidate: 45dc99d15a23c499b4c1500fab60ed5e76475aeb
s02_product_mutation_replay: forbidden
s02_changed_blob_readback: byte_identical_all_9_changed_blobs
s02_deterministic_suite:
  passed: 147
  skipped: 1
  failures: 0
s02_completion_checkpoint: docs/checkpoints/PR-014-devforge-execution-workspace-materialization-bridge-v1-s02-completion-20261008.yaml
s02_completion_receipt: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-s02-completion-receipt.yaml
~~~

### Hosted CI policy for PR-014 R6

Repository-hosted CI is **NotEvaluated and NonGating** for this Task.

Reason:

- current canonical `main` has no `.github/workflows/**` surface;
- the operator explicitly does not authorize CI spending for this Task;
- creating or modifying a workflow merely to satisfy PR-014 would expand scope and create an unrelated billing/execution dependency.

Therefore:

~~~yaml
repository_hosted_ci:
  applicability: NotEvaluated
  gating: false
  required_for_s02_completion: false
  required_for_acceptance: false
  create_or_modify_workflow_for_task: forbidden
~~~

R6 completion evidence for S02 is:

~~~text
exact product candidate 45dc99d...
+ exact changed-blob readback
+ deterministic suite 147 passed / 1 skipped / 0 failed
+ preserved security/authority evidence
+ mandatory Acceptance physical exact-candidate gate
~~~

The Acceptance physical gate remains unchanged and is the authoritative real-runtime proof for AC8, AC10 and AC14.

### Reconciliation rule

R6 MUST NOT re-run or rewrite the completed S02 product mutation.

After R6 approval, the R6 Slice Set must represent:

~~~text
S01 = completed / reused
S02 = completed / reused from candidate 45dc99d...
pending implementation slices = none
~~~

The S02 completion checkpoint/receipt may be reused only after the reviewer verifies they remain compatible with R6. Reconciliation is artifact-state synchronization, not implementation replay.


Plan R6 inherits the R5 bootstrap-safe implementation design and preserves Requirement R2, S01 evidence, and the completed S02 product candidate. R6 changes only the verification/completion policy described above.

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
workflow_observe: not_required_for_task_completion
local_workspace_required: false
~~~

The direct Development Host may inspect canonical source through repository reads, reason about the exact S02 patch, and persist source/test changes through structured repository writes.

Repository API availability is not provider authority. The active Task-scoped bootstrap override is authority.

### 3.4 Seed write scope

The R6 Plan Review/Slice Set must preserve the exact S02 path allowlist. It may include only the minimal materialization implementation and focused tests required by D1–D10, expected primarily under:

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

Repository-hosted CI/checks are not evaluated and are non-gating for PR-014 R6. S02 MUST NOT add or modify CI workflows or inject an ad-hoc generic shell job merely to obtain hosted verification.

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

### D1 — Independent Host-owned canonical source role

PR-014 must not accept a caller source path.

For repository `owner/repo`, resolve the source checkout from the current Host canonical repository inventory / registered canonical repository binding, independently from DevForge execution placement.

Current expected topology:

~~~text
canonical_source = D:\coco\repos\<owner>\<repo>
~~~

Admission verifies:

- normalized repository identity;
- source checkout matches the Host canonical repository inventory;
- source checkout exists;
- source checkout origin normalizes to the admitted repository;
- checked-out branch is canonical `main`;
- working tree is clean;
- source checkout remains inside its protected canonical root;
- source checkout != execution workspace;
- source checkout is never switched/reset/merged for materialization.

Concrete source path remains Host evidence only.

### D1A — Dedicated Host-owned execution placement

Execution placement is resolved only from:

~~~text
locations.devforge_execution_workspace_root
~~~

Preferred current Windows Host value:

~~~text
D:\SentinelX\devforge-workspaces
~~~

Derivation:

~~~text
execution_root = locations.devforge_execution_workspace_root
exact_workspace = <execution_root>/<owner>/<repository>/<task-or-evolution-id>/<attempt-id>
~~~

The provider must prove before scope minting:

- execution root is absolute and Host-configured;
- exact workspace is a strict descendant of execution root;
- execution root/exact workspace do not overlap any `protected_roots`;
- execution root/exact workspace do not overlap any canonical repository root;
- no caller path participates in derivation;
- legacy `locations.devforge_workspace_root` does not override this binding;
- `mutation_execution.workspace_root` does not become a second DevForge placement truth.

Placement receipt generation/binding digest must bind this dedicated execution-root authority.

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

### D6A — MutationScope durable schema compatibility

The current `MutationScopeRecord.from_json` strict constructor path must be replaced with an explicit version-compatible projection/migration boundary.

Required design:

1. split persisted JSON into known canonical fields and additive fields;
2. normalize current tuple/list fields exactly as today;
3. migrate explicitly supported additive fields, including `runtime_read_authority_roots`;
4. preserve supported additive fields in durable round-trip serialization;
5. provide backward-compatible defaults when an additive field is absent;
6. distinguish malformed data from unsupported schema;
7. fail closed on unknown additive fields that may carry mutation/read/permission authority;
8. allow safe inspection/terminalization of historical records without reactivating or widening authority;
9. never delete/reinitialize the store solely because a newer additive field exists.

Migration verification must include durable read → migration/normalization → durable write/readback without losing scope identity, digest-bound authority, lease/index binding or terminalization safety.

### D7 — Development Host handoff ACL transition

Current Windows sandbox cleanup intentionally removes AppContainer authority and leaves broker-only exact ACL. That is insufficient when the next consumer is a user-level Development Host.

R5 preserves one bounded **Host-owned handoff transition** after successful materialization.

Rules:

- capture/derive expected DevForge workspace inheritance/access from the dedicated Host-owned execution-root ancestry before temporary exact ACL is installed;
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

Plan R7 preserves completed historical work and adds exactly one delta repair Slice.

### S01 — Preserved historical completion

State: completed/reused.

Evidence remains:

~~~text
docs/checkpoints/PR-014-devforge-execution-workspace-materialization-bridge-v1-s01-completion-20261005.yaml
~~~

S01 is not replayed.

### S02 — Preserved completed materialize_workspace seed

State: completed/reused historical implementation evidence.

Candidate:

~~~text
45dc99d15a23c499b4c1500fab60ed5e76475aeb
~~~

Preserved evidence:

~~~text
docs/checkpoints/PR-014-devforge-execution-workspace-materialization-bridge-v1-s02-completion-20261008.yaml
docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-s02-completion-receipt.yaml
docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-s02-r6-reconciliation-receipt.yaml
~~~

S02 product mutation is not replayed.

### S03 — Dual-binding placement + MutationScope schema compatibility delta

Objective:

Repair only the Acceptance R2 architecture findings while preserving all other S01/S02 semantics.

Expected product scope:

~~~text
src/sentinelx_core/devforge_workspace_placement.py
src/sentinelx_core/devforge_workspace_source.py
src/sentinelx_core/devforge_workspace_materialization.py
src/sentinelx_core/mutation_scope.py
src/sentinelx_core/handlers/devforge_runtime.py              # only if binding/receipt projection requires it

tests/test_devforge_workspace_placement.py
tests/test_devforge_workspace_source.py
tests/test_devforge_workspace_materialization.py
tests/test_mutation_scope_admission.py
tests/test_mutation_scope_handler.py
tests/test_mutation_scope_registry.py
tests/test_devforge_runtime_local_api.py                     # only if projection changes
~~~

S03 must implement and verify:

1. source role resolution from Host canonical repository inventory, not execution placement root;
2. execution root from `locations.devforge_execution_workspace_root`;
3. preferred Windows Host topology `D:\SentinelX\devforge-workspaces`;
4. strict protected/canonical-root separation with no carve-out;
5. no caller path or legacy-root fallback;
6. Placement Receipt/binding generation semantics over the new dedicated execution root;
7. existing source main+clean/read-only role unchanged;
8. MutationScope additive-field compatible read/migration;
9. explicit support/preservation of `runtime_read_authority_roots`;
10. unsupported authority-bearing additive fields fail closed as schema incompatibility;
11. no durable state deletion;
12. no authority widening during migration;
13. existing S01/S02 firewall/audit/AppContainer/Job/no-replay behavior remains intact;
14. deterministic focused regression evidence;
15. no hosted CI requirement and no workflow creation/modification.

Execution authority and exact write scope are compiled only after Plan Review.

No additional product slice is planned after S03. Windows physical proof remains Acceptance-owned.

## 6. Acceptance mapping

Requirement R3 acceptance mapping:

- AC1 → S03 dual-binding placement derivation + protected/canonical-root separation + live physical readback.
- AC2–AC4 → preserved S02 closed schema/failure behavior plus S03 placement/schema regressions.
- AC5 → S03 canonical source resolution from Host canonical repository inventory; source remains protected main+clean.
- AC6 → preserved S02 source acquisition/capsule evidence.
- AC7–AC12 → preserved S02 runtime design plus post-S03 physical Acceptance.
- AC13 → S03 regressions must preserve firewall/scope/audit/AppContainer/Job invariants.
- AC14 → Acceptance repeats the full Windows physical integration with the repaired candidate.
- AC15–AC16 → ownership/no-bypass boundaries remain unchanged.
- AC17 → S03 durable MutationScope forward-compatible migration tests + live existing-state readback.

### Acceptance exact-candidate physical gate

After S03 completion, Acceptance must activate the exact repaired candidate and prove:

~~~text
canonical source binding
  = protected D:\coco\repos\...

execution placement binding
  = dedicated Host-owned root outside D:\coco
  = expected D:\SentinelX\devforge-workspaces

→ path-free materialize_workspace
→ exact Host-derived workspace under dedicated root
→ MutationScope existing-state read/migration succeeds
→ audit START before first workspace write
→ AppContainer/Job materialization
→ exact Git HEAD/branch/origin/clean readback
→ temporary-authority closure
→ Development Host handoff
→ same-attempt no replay
→ canonical source main + clean
~~~

Acceptance must additionally prove:

- `D:\coco` remains in protected roots unchanged;
- no carve-out/allowlist exception exists;
- caller cannot select either source or execution path;
- existing newer MutationScope record is not deleted to obtain success;
- hosted CI remains NotEvaluated/NonGating.

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

### Risk A — New execution root weakens protected-root policy

Mitigation: the new root is outside protected/canonical roots. R7 explicitly forbids removing/narrowing `D:\coco` or adding carve-outs.

### Risk B — Two Host bindings become two caller authorities

Mitigation: both bindings are Host-owned. Source comes from canonical repository inventory; execution root comes from dedicated policy location. Caller selects neither.

### Risk C — Legacy root silently remains authoritative

Mitigation: S03 must prove `locations.devforge_workspace_root` and `mutation_execution.workspace_root` cannot override PR-014 execution placement.

### Risk D — Forward compatibility silently drops authority fields

Mitigation: known additive authority fields are explicitly migrated/preserved; unknown authority-bearing fields fail closed as unsupported schema.

### Risk E — Migration widens existing MutationScope authority

Mitigation: migration cannot alter scope identity, lease/index binding, immutable authority digest semantics or operation classes; any widening is a blocker.

### Risk F — Durable state is deleted to escape schema incompatibility

Mitigation: state deletion/reinitialization is explicitly forbidden and Acceptance must prove existing durable state survives.

### Risk G — Historical S01/S02 work is replayed

Mitigation: both remain preserved evidence. Only S03 may mutate product code after R7 approval.

### Risk H — Physical proof is replaced by deterministic tests

Mitigation: Acceptance must repeat exact-candidate Windows materialization on the new topology and existing durable state.

### Risk I — Hosted CI becomes a hidden dependency

Mitigation: hosted CI remains NotEvaluated/NonGating and workflow creation/modification is forbidden.

## 9. Review questions

Plan Review R7 must explicitly decide:

1. Does Requirement R3 legitimately separate canonical source binding from execution placement binding without weakening source protection?
2. Is `locations.devforge_execution_workspace_root` a single Host-owned execution placement truth for PR-014?
3. Is preferred `D:\SentinelX\devforge-workspaces` outside all current protected/canonical roots?
4. Are removal/narrowing of `D:\coco`, carve-outs and caller path authority explicitly forbidden?
5. Can canonical source resolution use Host canonical repository inventory without depending on execution-root ancestry?
6. Does S03 avoid silently falling back to legacy `devforge_workspace_root` or `mutation_execution.workspace_root`?
7. Does the MutationScope migration design preserve known additive fields and fail closed on unsupported authority-bearing fields?
8. Does migration preserve existing durable authority/index/digest semantics without deletion or widening?
9. Are S01/S02 completion artifacts still valid historical evidence while S03 is the only new implementation delta?
10. Is `45dc99d...` preserved as the pre-repair candidate without being presented as final R7 Acceptance candidate?
11. Does Acceptance retain real Windows proof after S03 instead of relying on source/tests?
12. Are PR-013/PR-020/PR-229 and hosted CI still non-gating?

## 10. Post-plan state

After this Plan is durably persisted/read back:

~~~yaml
stage: plan_review
requirement_revision: 3
plan_revision: 7
plan_approved: false
implementation_authorized: false
current_slice: null
current_slice_set: null
completed_slices_preserved: [S01, S02]
preserved_pre_repair_candidate: 45dc99d15a23c499b4c1500fab60ed5e76475aeb
s01_s02_product_replay: forbidden
planned_pending_delta_slice: S03
superseded_slice_set: plan-r6
bootstrap_override_state: absent
next_expected_actor: reviewer
~~~

No R7 Slice Set exists until Plan Review approves R7.

If R7 is approved, the reviewer must compile:

~~~text
S01 completed/reused
S02 completed/reused historical evidence
S03 pending delta repair
~~~

Only S03 may perform new product mutation. Acceptance resumes only after S03 completes and the mechanical implementation→acceptance transition is re-established.
