# PR-014-devforge-execution-workspace-materialization-bridge-v1 — Plan R2

Requirement: `docs/requirements/PR-014-devforge-execution-workspace-materialization-bridge-v1.md`, revision 1 (unchanged).

Status: **Pending Plan Review**. No implementation authorization.

Supersedes Plan R1 and remediates Plan Review R1 findings F1–F3 without changing Requirement semantics.

## 0. Planning baseline

```yaml
sentinelx_main: e7064c9bf4fcd15bdb6f5a2678414210c01d1c00
devforge_runtime:
  version: 2.41.0
  revision: 902a9d71b425753928c01904be1e9b2b60f0c3fe
  workflow: project_development@2.1
pr012_explicit_execution_profile: merged_canonical
pr010_canonical_repository_firewall: merged_canonical
pr013_repository_materialization_publication:
  pr: 13
  state: open_draft
  stage: implementation
  current_slice: S01_pending
  observed_head: 1d98951425b148f04d3981830996b2da24d97a60
  current_changed_files: task_artifacts_only
  relationship: canonical_dependency_owner_for_repository_transaction_materializer_and_operation_closure
local_canonical_checkout:
  path_role: canonical_source
  branch: main
  observed_head: e7064c9bf4fcd15bdb6f5a2678414210c01d1c00
  dirty: true
  note: observed_existing_line_ending_drift_only; no cleanup authorized by this Plan
```

Canonical Host evidence remains:

```text
locations.devforge_workspace_root = D:\coco
mutation_execution.workspace_root = D:\SentinelX\mutation-workspaces
```

These concrete values are Host execution evidence only and are not persisted as Project or Runtime truth.

## 1. Planning objective

Implement only the DevForge-specific placement/receipt/root-binding bridge that is missing between the existing DevForge placement contract and SentinelX Host authority.

Target composition:

```text
semantic repository + Task/Run/Attempt identity
        ↓
resolve effective Host DevForge workspace binding
        ↓
derive deterministic DevForge execution target
        ↓
persist + read back provider-owned Placement Receipt
        ↓
compare optional caller/DevForge placement evidence
        ↓
provider-owned DevForge sandbox-root binding
        ↓
provision/revalidate existing Host mutation scope
        ↓
[only after canonical PR-013 dependency exists]
repository_transaction_v1 materialization + operation closure
        ↓
DevForge materialization receipt projection
        ↓
same-workspace scoped execution
        ↓
explicit terminalization/readback
```

PR-014 does **not** own a repository source broker, repository transaction state machine, AppContainer source materializer, operation-closure primitive, credential transport, publication broker or CAS push path. Those shared primitives are owned by PR-013 and may be consumed only after they are canonical on `main`.

## 2. Plan Review R1 remediation summary

| Finding | R2 disposition |
| --- | --- |
| F1 Placement Receipt lifecycle | Closed in Plan: provider persists and read-backs an immutable DevForge-compatible Placement Receipt before any mutation scope mint/revalidation; optional caller evidence is comparison-only. |
| F2 DevForge sandbox root not physically admitted | Closed in Plan: add a provider-generated `DevforgeSandboxRootBinding` derived only from the current Host binding; Windows sandbox root selection becomes provider-strategy based, legacy root remains default, and no caller root/path is accepted. |
| F3 duplicate PR-013 fallback | Closed in Plan: all repository source acquisition/materializer and multi-operation transaction/operation-closure implementation fallback clauses are removed. S02/S03 have an explicit canonical dependency gate and stop before mutation while PR-013 is not merged/verified. |

## 3. Architecture decisions

### D1 — Host-derived DevForge placement remains distinct from legacy mutation placement

Add a focused module:

```text
src/sentinelx_core/devforge_workspace_placement.py
```

It consumes only provider-owned current Host configuration plus normalized repository/semantic identity.

Authoritative Host input:

```text
Policy.locations["devforge_workspace_root"].path
```

Derived layout:

```text
workspace_root = current Host binding
execution_root = workspace_root / "workspaces"
exact_workspace = execution_root / owner / repository / task_or_evolution_id / attempt_id
```

Rules:

1. Host binding missing, malformed, relative or platform-incompatible → fail closed;
2. owner/repository/scope/attempt are validated as single path segments;
3. `execution_root` must be a strict descendant of `workspace_root`;
4. `exact_workspace` must be a strict descendant of `execution_root`;
5. caller paths never alter derivation;
6. `mutation_execution.workspace_root` remains the legacy/non-DevForge scoped-mutation root and is not rewritten;
7. no Host configuration mutation is part of this Task.

### D2 — Durable Placement Receipt is created and read back before scope minting

This closes F1.

Add an evidence-only provider store, conceptually:

```text
DevforgeWorkspacePlacementReceiptStore
```

The store lives under provider-owned SentinelX state, not under the repository, canonical checkout or execution workspace. Its location is provider configuration/internal state and is never caller input.

A Placement Receipt contains equivalent immutable fields:

```yaml
receipt_id: <provider opaque id>
policy: host-workspace-layout-repository-placement-v1
state: PlacementResolved
operation: execution_workspace
repository: <normalized owner/repository>
repository_identity_digest: <digest>
semantic_identity_digest: <digest>
placement_role: execution_root
workspace_root_digest: <digest>
execution_root_digest: <digest>
target_path: <Host evidence only>
target_digest: <digest>
placement_compliant: true
binding_generation: <provider generation>
issued_at: <timestamp>
```

Exact sequence is frozen:

```text
resolve current Host binding
→ derive deterministic target
→ validate strict-descendant and protected/canonical separation
→ persist Placement Receipt atomically
→ read back exact receipt id/digests/target
→ compare optional DevForge/caller placement evidence
→ only then provision/revalidate Host mutation scope
```

Caller placement evidence remains optional and non-authoritative. A mismatch returns `WorkspacePlacementMismatch` before scope creation. A stale provider receipt whose Host-binding generation/digest no longer matches current Host reality cannot be reused.

Same exact semantic/Attempt retry may return the already persisted current Placement Receipt when all sealed inputs and current Host binding still match; it does not create a competing receipt/authority.

### D3 — Provider-owned DevForge sandbox-root binding

This closes the first half of F2.

Add an internal immutable binding produced from the current Placement Receipt, conceptually:

```yaml
DevforgeSandboxRootBinding:
  kind: devforge_execution_root_v1
  placement_receipt_ref: <provider receipt id>
  host_binding_digest: <digest>
  execution_root: <provider-private Host path>
  execution_root_digest: <digest>
  exact_workspace_digest: <digest>
```

The model-facing request cannot supply this object, its kind, root, digest or strategy.

For DevForge bridge operations the provider recomputes the root from current `locations.devforge_workspace_root/workspaces`, verifies it against the current Placement Receipt and emits the binding internally.

For legacy `scoped_script` operations no DevForge binding exists; the effective sandbox root remains `mutation_execution.workspace_root` exactly as on canonical `main`.

### D4 — Mutation scope seals placement strategy/root identity without caller authority

The existing `MutationScopeStore` remains the only scope authority store.

R2 permits a narrow provider-only placement seam so the store can consume a provider-generated placement/binding object rather than always calling the legacy digest placement resolver itself.

The scope immutable authority must seal equivalent facts:

```text
placement_kind = devforge_execution_workspace_v1 | legacy_mutation_workspace_v1
placement_receipt_ref (DevForge only)
repository_identity_digest
semantic_identity_digest
exact_workspace / exact_workspace_digest
sandbox_root_digest
placement policy/generation digest
protected/canonical inventory digest
Attempt/lease identity
provider-fixed operation authority
```

The raw sandbox root is not accepted from caller JSON and need not be exposed as mutable scope input. Revalidation recomputes the provider strategy from current Host configuration and requires the same receipt/root/workspace digests.

For repository transaction operation classes and multi-operation scope state, PR-014 consumes canonical PR-013 semantics only after the dependency gate in D8 is satisfied.

### D5 — Windows sandbox root admission is provider-strategy based

This closes the physical contradiction identified by F2.

Refactor `WindowsMutationSandbox` root resolution into an internal provider boundary equivalent to:

```python
resolve_sandbox_root(record, provider_binding) -> Path
```

Selection rules:

```text
legacy scope
  → root = policy.mutation_execution.workspace_root

DevForge bridge scope
  → require provider-generated DevforgeSandboxRootBinding
  → independently re-resolve current Host DevForge execution_root
  → require root digest == scope/root binding digest
  → require exact workspace strict descendant of that root
```

`WindowsMutationSandbox.activate()` receives only the provider-resolved binding through trusted internal composition. No model/local-api field carries a root/path selector.

Before activation:

- the selected execution root must exist and be a directory; PR-014 does not create/repair role roots or rewrite Host configuration;
- root/final paths are canonicalized and checked for reparse/junction escape;
- root must remain a strict descendant of the current Host workspace root;
- exact workspace must not overlap a canonical repository root or protected root;
- canonical-repository firewall classification remains determinate/non-canonical for the target.

If the Host role root is absent or unsafe, return a bounded provider-unavailable/root-admission result. Do not fall back to `mutation_execution.workspace_root`.

### D6 — Parent traversal and ACL authority stay operation-scoped

This closes the second half of F2.

The AppContainer must not receive general read/list/write access to `D:\coco`, repository roots, user profile or canonical checkout.

The Windows implementation must first test whether the scope-derived AppContainer identity can traverse the already configured ancestor chain to the exact workspace while remaining unable to enumerate/read/write sibling protected roots.

If existing ACLs are insufficient, the provider may install only operation-scoped **traverse-only** ancestor authority needed to reach the DevForge execution root/exact workspace, subject to all of these constraints:

1. grant is provider-generated after durable operation START, never caller-requested;
2. grant is non-inheriting or otherwise bounded so it cannot become read/list/write authority for sibling trees;
3. no ACE grants repository/canonical root read/write authority;
4. previous ACL state is captured before mutation;
5. operation closure restores the exact previous ACL state;
6. restoration is read back before the operation can be considered closed;
7. cleanup failure revokes/terminalizes fail closed.

If a platform cannot provide traverse without broader authority, DevForge-root sandbox activation fails closed. V1 must not widen `file_ops`, command allowlists, canonical ACLs or Host policy as a workaround.

Physical negative tests must prove the sandbox process cannot enumerate/read `repository_root`/canonical siblings and cannot select another root despite having access to its exact execution workspace.

### D7 — Exact source identity remains immutable

`source_binding.expected_commit` remains a mandatory full Git commit SHA.

Successful materialization must prove:

```text
materialized repository identity == admitted repository identity
workspace HEAD == expected_commit
```

Logical ref/branch is only comparison/transport evidence.

PR-014 does not implement source acquisition. It passes exact source identity into the canonical repository transaction materializer only after D8 is satisfied.

### D8 — PR-013 is a hard canonical dependency for shared transaction/materializer primitives

This closes F3.

Current observed PR-013 state at remediation:

```yaml
pr: 13
head: 1d98951425b148f04d3981830996b2da24d97a60
stage: implementation
current_slice: S01_pending
plan_revision: 2
plan_approved: true
implementation_authorized: true
```

PR-013 owns and is the only planned implementation source for:

```text
repository_transaction_v1 admission/state
provider source acquisition/snapshot
AppContainer/Job repository materializer
repository_execute multi-operation transaction lifecycle
operation closure between bounded operations
source credential boundary
publication freezer/broker/CAS (not consumed by PR-014 except shared transaction state where unavoidable)
```

PR-014 is forbidden to implement substitutes for those primitives.

#### Canonical dependency evidence required before S02/S03

All must be true and read back immediately before the slice mutates product code:

```text
PR #13 is merged into sentinelx-cloud-core/main
PR-013 canonical Task state reports acceptance_approved=true and completion_verified=true
current main contains the accepted PR-013 merge/integration result
current main exposes repository_transaction_v1 + provider materializer + operation-closure semantics required by the slice
legacy scoped_script compatibility evidence from PR-013 remains canonical
no Requirement/ownership change transfers those primitives away from PR-013
```

If any item is false:

```text
S02/S03 admission = BlockedByDependency
product mutation for that slice = forbidden
```

No generic fallback, local reimplementation, cherry-pick/copy of unmerged PR-013 code, permission widening or provider switch is permitted.

If PR-013 is cancelled or materially changes ownership, PR-014 must return to Plan remediation/re-review before scope can expand.

### D9 — Bounded materialization action is an adapter over canonical transaction capability

After D8 is satisfied, add/complete the DevForge-facing structured action, conceptually:

```yaml
materialize_workspace:
  repository: {vcs, authority, path}
  lineage: {project_id, task_id, run_id, attempt_id, slice_id?}
  workspace_purpose: implementation | fixing | verification | repair | resume | evolution | release | finalization
  source_binding:
    expected_commit: <full sha>
    transport_ref: <optional comparison evidence>
  placement_expectation: <optional compare-only evidence>
```

Forbidden schema fields include any caller-controlled destination/root/cache/staging/operation-class/credential/Git-argv field.

The action composes:

```text
provider Placement Receipt readback
→ DevforgeSandboxRootBinding
→ canonical repository_transaction_v1 provision/revalidation
→ durable audit START
→ canonical PR-013 materializer
→ repository/HEAD/isolation readback
→ DevForge materialization receipt projection
```

No new executor or source broker is created.

### D10 — Materialization receipt projection

Successful DevForge projection contains equivalent evidence:

```yaml
state: Materialized
capability: development.execution_workspace_materialize
placement_policy: host-workspace-layout-repository-placement-v1
placement_role: execution_root
placement_receipt_ref: <provider ref>
placement_ref: <scope/provider ref>
target_path: <Host evidence only>
repository_identity: <verified normalized identity>
source_commit: <verified exact commit>
scope_ref:
scope_generation:
scope_digest:
sandbox_root_digest:
audit_operation_id:
scope_revalidated: true
audit_started: true
execution_profile: scoped_mutation
workspace_exists_readback: true
git_root_match: true
head_match: true
workspace_isolation_verified: true
canonical_source_mutated: false
generic_bypass_used: false
operator_unrestricted_used: false
```

Concrete paths remain execution evidence only and are never persisted into Project Binding/Development Project Registry truth.

### D11 — Same-workspace lifecycle consumes canonical PR-013 operation closure

PR-014 does not implement a retained-scope lifecycle.

After D8 is satisfied, the DevForge adapter binds later `execute_scoped` requests to the same canonical repository transaction/workspace and consumes PR-013 operation closure semantics.

Required behavior:

- transaction must already be materialized/current;
- `execute_scoped` retains explicit `execution_profile=scoped_mutation`;
- relative cwd remains beneath the sealed repository workspace and cannot target provider control state or another workspace;
- each successful non-terminal operation must close Job/PID/temporary ACL authority before another operation begins;
- provider transaction remains current only according to canonical transaction state;
- nonzero/timeout/containment/audit/cleanup failure follows canonical fail-closed transaction behavior;
- legacy non-transaction `scoped_script` continues its one-shot auto-terminalization unchanged.

At the real Attempt boundary:

```text
revalidate same transaction/scope
→ explicit terminalize_scope
→ read back exact same scope + generation
→ require terminal | revoked | expired
```

### D12 — Canonical source checkout preservation

No step in PR-014 switches, resets, cleans, fetches into, checks out into, or uses the canonical checkout as a mutation workspace.

Acceptance must compare before/after:

```text
repository identity
canonical branch
HEAD
working-tree cleanliness
```

A concurrent external canonical change invalidates preservation proof rather than being silently attributed to the bridge.

The current local canonical checkout is observed dirty from pre-existing line-ending drift. This Plan does not authorize cleanup/reset. Any implementation entry contract that requires canonical `main + clean` remains a hard guard and may block execution until independently resolved.

## 4. Planned change surface

### Independently owned by PR-014

```text
src/sentinelx_core/devforge_workspace_placement.py                 # new: derivation + Placement Receipt evidence/store
src/sentinelx_core/devforge_workspace_materialization.py           # DevForge adapter/coordinator only
src/sentinelx_core/mutation_scope.py                               # narrow provider-generated placement/root binding seam only if required
src/sentinelx_core/windows_mutation_sandbox.py                     # provider root-selection/traverse binding seam only
focused placement/root/scope tests
```

### Allowed only after D8 canonical dependency gate

```text
src/sentinelx_core/handlers/devforge_runtime.py                    # materialize_workspace projection/routing
src/sentinelx_core/handlers/scoped_script.py                       # DevForge transaction lookup/composition only
canonical repository-transaction/materializer modules              # consume/adapt; do not duplicate
repository transaction tests                                       # adapter/regression only
Windows physical materialization/lifecycle tests
```

### Explicitly not owned by PR-014

```text
provider source snapshot/broker implementation
AppContainer repository-source materializer implementation
repository transaction state machine implementation
operation-closure primitive implementation
publication freezer/broker/CAS push
credential transport implementation
```

No DevForge repository file is changed by this Task.

## 5. Slice proposal

Execution Slice Set is compiled only after Plan approval.

### S01 — DevForge Placement Receipt + provider sandbox-root binding

Independent of PR-013 product implementation.

Owns:

- resolve/validate `devforge_workspace_root`;
- derive deterministic DevForge execution target;
- persist/read back provider-owned Placement Receipt before any scope minting;
- optional external placement comparison;
- define provider-generated DevForge sandbox-root binding and digest;
- add the narrow provider-placement/root selection seams needed by scope/sandbox composition without repository materialization;
- prove legacy placement/root behavior unchanged;
- no repository source hydration and no multi-operation transaction implementation.

Entry guard:

- re-read current SentinelX main and PR-013 state/head/files;
- if PR-013 has begun overlapping product mutation on the exact S01 lines, stop before conflicting mutation and reconcile/repair Plan rather than overwrite;
- local canonical checkout mutation remains forbidden; use admitted execution workspace/provider path only.

Exit evidence:

```text
Placement Receipt exists + readback before scope-admission seam is invoked
same semantic identity/current Host binding → same target receipt
caller path cannot retarget receipt/root
DevForge root != legacy mutation root and both strategies remain distinct
DevForge exact workspace validates beneath provider-selected execution root
alternate/caller-selected root is rejected
legacy scoped_script continues to resolve policy.workspace_root
no repository transaction/materializer/operation-closure code added
```

### S02 — DevForge materialization adapter over canonical PR-013 capability

Hard dependency: D8 satisfied.

Owns only:

- bind current Placement Receipt/root binding into canonical repository transaction scope;
- expose bounded `materialize_workspace` schema/routing;
- pass immutable expected commit to canonical materializer;
- compose audit/sandbox/materialization/readback evidence;
- project DevForge materialization receipt;
- retry/readback adapter behavior.

Before any S02 product mutation, persist/read back dependency evidence that PR-013 is merged/accepted/completed and that required canonical primitives are present on current main.

If dependency is not satisfied, S02 stops `BlockedByDependency` with no substitute implementation.

### S03 — Same-workspace execution + explicit terminal proof adapter

Hard dependency: D8 satisfied and S02 complete.

Owns only:

- resolve canonical repository transaction from DevForge workspace binding;
- route repeated bounded `execute_scoped` operations to the same sealed workspace;
- consume canonical operation closure between successful operations;
- enforce relative cwd confinement;
- explicit terminalize/readback at Attempt boundary;
- regression proof that legacy one-shot `scoped_script` still terminalizes after one operation;
- Windows physical integration fixture using canonical PR-013 primitives.

PR-014 must not implement operation closure itself.

Live Agent installation/restart remains Acceptance-owned, not an implementation slice.

## 6. Verification strategy

### S01 placement/receipt/root

- missing/relative/malformed Host binding fails closed;
- segment traversal/separator/drive/UNC injection rejected;
- deterministic target and strict-descendant proof;
- provider Placement Receipt persisted/read back before scope seam call;
- stale Host-binding generation invalidates receipt reuse;
- optional external placement mismatch rejects before scope;
- DevForge sandbox root derived only from Host binding/receipt;
- caller root/path/strategy fields are absent from schema and internal APIs exposed to model;
- alternate root binding fails;
- reparse/final-path checks anchor to DevForge execution root;
- parent traversal authority does not permit sibling canonical/repository enumeration/read/write;
- transient traversal ACL, if required, restores exact prior ACL and is read back;
- legacy sandbox root behavior remains unchanged.

### S02 materialization adapter

- exact dependency receipt for canonical PR-013 is present before adapter mutation;
- `local_api.describe` exposes bounded materialization schema without destination/root/credential/operation-class fields;
- scope exact workspace/root/placement receipt are mutually consistent;
- durable audit START precedes exact workspace materialization;
- wrong repo/ref/SHA, stale/foreign scope, placement/root mismatch reject;
- exact materialized repository HEAD equals expected commit;
- pre-existing unbound/non-empty workspace fails closed;
- verified retry converges by durable readback and does not repeat materialization;
- credential unavailable returns bounded failure with no generic fallback;
- canonical checkout before/after is unchanged by bridge operation.

### S03 lifecycle

- materialize once;
- execute bounded operation A;
- read back zero operation process/Job/temporary ACL authority while transaction remains current;
- execute bounded operation B against the same workspace/scope/transaction;
- caller cannot retarget cwd/workspace;
- explicit terminalize;
- read back same scope/generation terminal/revoked/expired;
- third execution rejected;
- legacy one-shot scoped-script still terminal after one execution.

### Regression suites

Focused regressions include:

```text
mutation placement/scope
Windows mutation sandbox
pre-execution audit lineage
canonical repository firewall
devforge_runtime local_api
scoped script execution
PR-012 explicit execution profile
canonical PR-013 repository transaction/materialization/operation closure once dependency exists
```

Windows-only physical claims require real Windows evidence; mocks are supporting evidence only.

## 7. Acceptance boundary

Implementation completion proves code/tests on exact Task transport only.

Acceptance additionally requires an independently activated accepted Agent candidate and connected-host evidence:

```text
local_api.describe shows bounded materialize_workspace
Host binding resolves current DevForge root
provider Placement Receipt is durably read back before scope authority
harmless fixture materializes at exact DevForge path
HEAD/repository/isolation readback passes
sandbox cannot read/list canonical sibling roots
canonical source before/after unchanged
2 sequential same-workspace scoped operations pass
operation authority is closed between operations
explicit terminalization/readback passes
path/root injection, stale scope, wrong SHA, audit failure negatives fail closed
```

No production Hub change is required; existing `sentinel_local_api` transport remains the boundary.

## 8. Safety / non-goals

Forbidden:

- caller-selected sandbox/workspace root;
- generic shell/exec/script fallback;
- generic `sentinel_git clone(dest=...)` as DevForge authority;
- direct worktree bypass;
- `operator_unrestricted`;
- `file_ops`/command allowlist widening;
- permanent or broad ACL grant to `D:\coco`, canonical repository roots or user profile;
- canonical checkout mutation/repair;
- credential exposure to AppContainer/model;
- provider switch;
- production Hub mutation;
- source broker/materializer implementation owned by PR-013;
- repository transaction/operation-closure implementation owned by PR-013;
- publication/push/CAS implementation;
- copy/cherry-pick of unmerged PR-013 code as implementation authority;
- cross-repository DevForge contract mutation;
- live Agent restart/install inside implementation slices;
- independent Codex requirement;
- new Development Gate/stage.

## 9. Requirement traceability

| Requirement | Planned coverage |
| --- | --- |
| R1–R3 | D1–D4, S01 placement/receipt/root binding |
| R4 | D7, S02 exact source adapter |
| R5 | D4 + D8 canonical transaction dependency + S02 |
| R6 | D9/S02 audit-before-materialization composition |
| R7–R8 | D8–D9; canonical PR-013 materializer only |
| R9 | D10/S02 receipt projection |
| R10–R11 | D11/S03 canonical operation closure + terminalization |
| R12 | D12 + S02/S03 preservation evidence |
| R13 | S02 durable retry/readback |
| R14 | D8 + Safety/Non-goals |
| AC1/AC3/AC5/AC7/AC8 | S01/S02 physical and durable evidence |
| AC6/AC9/AC10/AC13 | S02/S03 only after PR-013 canonical dependency |
| AC14 | global Plan invariants |

## 10. Plan review questions

Plan Review R2 must reject if any of these remain unresolved:

1. Is the provider-owned Placement Receipt persisted/read back before scope minting, rather than merely projected after materialization?
2. Does the DevForge sandbox-root strategy physically permit `<devforge_workspace_root>/workspaces/...` while preserving legacy `mutation_execution.workspace_root` behavior?
3. Can parent traversal be provided/verified without giving the AppContainer sibling canonical/repository read/write authority or requiring Host policy/allowlist widening?
4. Does S01 remain independently owned by PR-014 while S02/S03 hard-stop until canonical PR-013 transaction/materializer/operation-closure evidence exists?
5. Is there any remaining clause allowing PR-014 to implement a substitute source broker/materializer or retained-scope transaction lifecycle? If yes, reject.
6. Are Windows physical tests sufficient to prove root confinement, receipt-before-scope ordering and no mock-only substitution?

Canonical next action after this remediated Plan is persisted and read back:

```text
#开发评审 PR-014-devforge-execution-workspace-materialization-bridge-v1
```
