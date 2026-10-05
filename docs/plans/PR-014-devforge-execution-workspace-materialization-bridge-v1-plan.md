# PR-014-devforge-execution-workspace-materialization-bridge-v1 — Plan R1

Requirement: `docs/requirements/PR-014-devforge-execution-workspace-materialization-bridge-v1.md`, revision 1.

Status: **Pending Plan Review**. No implementation authorization.

## 0. Planning baseline

```yaml
sentinelx_main: e7064c9bf4fcd15bdb6f5a2678414210c01d1c00
devforge_runtime:
  version: 2.40.0
  revision: 1dc76ed0bcc1a70a2c5a860cd7a99aedd5d7820a
  workflow: project_development@2.1
pr012_explicit_execution_profile: merged_canonical
pr010_canonical_repository_firewall: merged_canonical
pr013_repository_materialization_publication:
  pr: 13
  state: open_draft
  stage: plan_review
  observed_head: 32cd89bdc3430596409329c676e18d36dddffc1b
  relationship: overlapping_upstream_candidate
```

Canonical Host evidence observed during requirement review:

```text
locations.devforge_workspace_root = D:\coco
mutation_execution.workspace_root = D:\SentinelX\mutation-workspaces
```

These values are Host execution evidence only. No machine path is persisted as project/runtime truth by this Plan.

## 1. Planning objective

Implement a SentinelX provider bridge that makes one DevForge execution workspace identity mean the same thing across:

```text
DevForge layout/placement admission
SentinelX Host placement
MutationScopeStore authority
Windows mutation sandbox activation
repository materialization
execute_scoped workspace resolution
materialization receipt
scope terminalization
```

The bridge must not create a second executor, second scope store, second audit journal, second canonical-firewall implementation, or caller-controlled clone path.

The bridge is intentionally narrower than PR-013 publication work. PR-014 owns DevForge placement/materialization conformance and evidence; PR-013 owns general repository transaction acquisition/publication semantics. Equivalent repository-source materializer primitives that become canonical through PR-013 are reused, not copied.

## 2. Architecture decisions

### D1 — Separate DevForge placement from legacy scoped-script placement without duplicating Host truth

Introduce a focused provider placement resolver for DevForge execution workspaces. Recommended new module:

```text
src/sentinelx_core/devforge_workspace_placement.py
```

It consumes existing `Policy.locations` and existing `RepositoryIdentity` / semantic lineage primitives.

Authoritative input:

```text
policy.locations["devforge_workspace_root"].path
```

Derived layout:

```text
workspace_root = bound Host value
execution_root = workspace_root / "workspaces"
exact_workspace = execution_root / owner / repository / task_or_evolution_id / attempt_id
```

Rules:

1. location missing/malformed/relative/platform-incompatible → fail closed;
2. owner/repository/scope/attempt must each be one safe path segment;
3. exact workspace must be a strict descendant of `execution_root`;
4. provider independently derives the path; caller path evidence never changes it;
5. existing `mutation_execution.workspace_root` remains unchanged for legacy/non-DevForge scoped mutation;
6. no Host config rewrite is part of this Task.

The resolver emits a provider-owned `DevforgeWorkspacePlacementEvidence` (exact naming may vary) containing stable placement policy/version, normalized root/target evidence, repository identity digest and semantic/attempt binding.

### D2 — Scope binding gains an explicit DevForge placement strategy, not caller path authority

Current `MutationScopeStore.provision_scope()` derives placement through the generic digest-based `resolve_placement()` path. PR-014 must allow a provider-selected placement strategy for the DevForge bridge while preserving all existing scope uniqueness/lifecycle semantics.

Preferred design:

```text
MutationScopeStore
  └─ receives provider-generated PlacementEvidence
     OR a provider-owned placement resolver callback/strategy
```

The caller must never submit `exact_workspace`, placement digest, operation-class set or placement strategy directly.

The scope record continues to seal:

```text
repository_identity_digest
semantic_identity_digest
placement_ref / generation / policy digest
exact_workspace / digest
protected inventory
Attempt key
unique lease key
allowed operation classes
```

A DevForge bridge scope is minted only after the provider has independently derived the current DevForge exact workspace. Revalidation recomputes the same provider strategy and fails on drift.

Legacy `scoped_script` scope provisioning remains byte/behavior compatible and continues using its existing placement path unless an explicit existing canonical provider contract says otherwise.

### D3 — Distinguish DevForge workspace purpose from SentinelX operation class

Add a bridge-specific provider admission object rather than overloading existing `purpose=scoped_script` with values such as `implementation` or `release`.

The model-facing action may use a request shape equivalent to:

```yaml
materialize_workspace:
  repository: {vcs, authority, path}
  lineage: {project_id, task_id, run_id, attempt_id, slice_id?}
  workspace_purpose: implementation | fixing | verification | repair | resume | evolution | release | finalization
  source_binding:
    expected_commit: <full sha>
    transport_ref: <optional evidence>
  placement_expectation: <optional compare-only DevForge placement evidence>
```

No Host path is accepted as mutation authority.

Provider-side fixed operation classes are derived internally. PR-014 must not expose an `allowed_operation_classes` request field.

If PR-013 lands a canonical `repository_transaction_v1` scope lifecycle before implementation, compose that lifecycle and add only the DevForge placement/receipt bridge. If it has not landed, PR-014 may define only the minimum internal transaction abstraction needed for materialization and repeated scoped execution, but MUST NOT implement publication or copy PR-013 unmerged source-broker code.

### D4 — Exact source commit is mandatory

`source_binding.expected_commit` is a full immutable Git commit SHA.

The source-materialization provider must prove:

```text
normalized materialized repository identity == admitted repository identity
workspace HEAD == expected_commit
```

A logical transport ref may be comparison evidence but is not sufficient source identity.

Source acquisition must use one canonical provider-owned repository materializer/broker. No materialization path may invoke generic `sentinel_git clone(dest=caller_path)`.

### D5 — Repository materializer composition boundary

PR-014 defines an internal provider seam such as:

```python
RepositoryWorkspaceMaterializer.materialize(
    *, scope_record, repository, expected_commit, audit_context
) -> MaterializationReadback
```

The seam is narrow and authority-bearing inputs are provider-owned.

Implementation priority:

1. if a repository source broker/materializer from PR-013 (or equivalent) is merged to current `main`, adapt/reuse it;
2. otherwise implement only the smallest safe canonical provider component necessary for source acquisition/materialization, but do not duplicate publication, CAS push or credential-broker functionality owned by PR-013;
3. if safe authenticated/private source acquisition cannot be composed without importing unmerged PR-013 work, return/retain a provider-unavailable boundary and do not broaden credentials/permissions.

Any service-side source snapshot/capsule path remains provider-private and caller-invisible.

### D6 — Materialization sequence reuses scope + audit + sandbox

The model-facing `materialize_workspace` action sequence is frozen:

```text
validate closed request schema
→ normalize repository + lineage + purpose + expected_commit
→ derive current DevForge Host placement
→ compare placement expectation if supplied
→ canonical-firewall classify source/target roles
→ provision or resolve exact current bridge scope
→ revalidate exact scope + placement
→ construct provider-owned materialization audit intent
→ persist durable OPERATION_STARTED
→ activate existing mutation sandbox for exact workspace
→ invoke canonical repository materializer under admitted provider boundary
→ verify repository root / identity / exact HEAD
→ verify workspace final path / no reparse escape / isolation
→ verify canonical checkout source-role evidence remains unchanged
→ persist materialization FINISH/readback evidence
→ persist provider transaction/materialization state
→ return bounded materialization receipt
```

The first material mutation must occur after durable START.

If current `WindowsMutationSandbox.activate()` creates the exact workspace directory during activation, that remains conforming only because activation is already bound to durable START; repository-source hydration still occurs after activation and remains scoped to the exact workspace.

### D7 — Bounded materialization receipt is provider evidence, not new DevForge truth

Add a receipt projection returned through `devforge_runtime` containing equivalent fields:

```yaml
state: Materialized
capability: development.execution_workspace_materialize
placement_policy: host-workspace-layout-repository-placement-v1
placement_role: execution_root
placement_ref: <provider ref>
target_path: <Host evidence only>
repository_identity: <normalized>
source_commit: <exact sha>
scope_ref:
scope_generation:
scope_digest:
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

Concrete paths are returned only as execution evidence. No registry/project binding persistence is performed by SentinelX.

### D8 — Multi-operation Attempt scope is explicit and provider-owned

The bridge must support:

```text
materialized
→ executing
→ materialized/executed-current
→ executing
→ ...
→ terminalizing
→ terminal
```

The exact state names may reuse a canonical transaction state machine that lands from PR-013.

The provider, not the caller, decides whether a successful operation closes only its Job/process/temporary ACL authority while retaining the Attempt transaction.

Requirements:

- each successful non-terminal execution fully closes process/Job/operation-specific authority;
- scope/transaction stays current only when provider state explicitly admits another bounded operation;
- no generic `keep_open` / `cleanup=false` flag grants retained scope authority;
- nonzero execution, timeout, containment/audit cleanup failure may revoke/terminalize fail closed;
- TTL, placement generation drift and explicit revocation remain authoritative;
- legacy one-shot `scoped_script` still auto-terminalizes exactly as before.

`execute_scoped` must resolve cwd/workspace from the same provider transaction; caller relative cwd remains bounded beneath that workspace and cannot retarget to another workspace/control namespace.

### D9 — Explicit terminalization and readback

At terminal Attempt boundary:

```text
revalidate current bridge scope
→ terminalize_scope
→ inspect/read back exact same scope + generation
→ require terminal | revoked | expired
```

No completion receipt is valid while the scope reads `provisioned` or `active`.

A terminal Attempt cannot mint fresh authority through retry with the same Attempt identity; existing Attempt-index guard remains authoritative.

### D10 — Canonical checkout preservation evidence

PR-014 does not modify canonical checkout state to create an execution workspace.

Acceptance/physical integration must snapshot canonical source evidence before and after:

```text
repository identity
canonical branch
HEAD
working-tree cleanliness
```

Expected:

```text
branch unchanged
HEAD unchanged unless an independently authorized external canonical update occurred
working tree clean
workspace path != canonical checkout
```

If canonical state changes concurrently, the test must distinguish external drift from bridge mutation and fail closed rather than claim preservation without evidence.

### D11 — PR-013 overlap admission is mandatory

Current PR-013 observed head:

```text
32cd89bdc3430596409329c676e18d36dddffc1b
```

Before Plan approval, and again before every implementation Slice that touches any overlapping surface, re-read:

```text
PR-013 state/head
current changed-file set
current Requirement/Plan disposition
current main
```

Likely overlap surfaces include:

```text
src/sentinelx_core/handlers/devforge_runtime.py
src/sentinelx_core/mutation_scope.py
src/sentinelx_core/mutation_placement.py
src/sentinelx_core/handlers/scoped_script.py
src/sentinelx_core/windows_mutation_sandbox.py
repository transaction/source materializer modules if created
related tests
```

Rules:

- unmerged PR-013 implementation cannot be copied/cherry-picked as authority;
- equivalent merged primitives must be reused;
- direct incompatible overlap stops before product mutation and requires Plan remediation/review rather than ad-hoc conflict resolution;
- PR-014 does not add publication/push scope merely because PR-013 contains it.

## 3. Planned change surface

Expected primary product files, subject to Plan Review overlap reconciliation:

```text
src/sentinelx_core/devforge_workspace_placement.py                 # new
src/sentinelx_core/devforge_workspace_materialization.py           # new bridge/coordinator
src/sentinelx_core/handlers/devforge_runtime.py                    # bounded action/schema/projection
src/sentinelx_core/mutation_scope.py                               # provider-selected placement/transaction binding seam
src/sentinelx_core/mutation_placement.py                           # shared evidence/refactor only if required
src/sentinelx_core/handlers/scoped_script.py                       # transaction composition only; preserve legacy path
src/sentinelx_core/windows_mutation_sandbox.py                     # operation closure/composition only if canonical primitive absent
```

Possible canonical repository-materializer adapter files depend on the exact current main after PR-013 reconciliation. Do not pre-create a duplicate generic source broker.

Tests:

```text
tests/test_devforge_workspace_placement.py                         # new
tests/test_devforge_workspace_materialization.py                   # new
tests/test_devforge_runtime_local_api.py                           # schema/routing regressions
tests/test_mutation_scope.py                                       # exact placement/same-attempt authority
tests/test_scoped_script_execution.py                              # same-workspace vs legacy one-shot behavior
Windows physical sandbox/materialization integration tests         # exact existing suite location resolved at implementation
```

Documentation:

```text
docs/devforge-execution-workspace-materialization-bridge-v1.md
config.example.windows.yaml                                       # documentation only if bridge binding/readiness needs explanation
```

No DevForge repository file is changed by this Task.

## 4. Slice proposal

The canonical Execution Slice Set is created only after Plan approval. Proposed implementation partition:

### S01 — DevForge Host placement alignment + scope binding seam

Owns:

- Host `devforge_workspace_root` resolution/validation;
- deterministic `<root>/workspaces/<owner>/<repo>/<scope>/<attempt>` derivation;
- compare-only placement expectation;
- provider-selected scope placement seam and revalidation;
- no filesystem materialization yet;
- focused unit tests and legacy placement regressions.

Exit evidence:

```text
same semantic identity → deterministic DevForge path
caller path cannot influence authority
placement mismatch/escape fails closed
scope record exact_workspace == provider-derived DevForge target
legacy scoped_script placement unaffected
```

### S02 — Bounded materialization action + exact-source/readback receipt

Owns:

- `devforge_runtime.materialize_workspace` closed schema/describe/call routing;
- exact `expected_commit` source binding;
- composition with canonical repository materializer/broker;
- durable audit START before materialization;
- exact sandbox/workspace source hydration;
- exact HEAD/repository/isolation readback;
- materialization state + receipt;
- retry/non-empty/mismatch/partial-failure behavior.

Admission condition:

```text
re-read PR-013 exact state/head/files
reuse any equivalent canonical materializer that has reached main
no unmerged-code import
```

If no safe canonical source materializer can satisfy S02 without duplicating an active PR-013 implementation or widening credential authority, S02 stops `BlockedByContext/Tool` before product mutation beyond independently valid non-overlap work.

### S03 — Same-workspace bounded execution lifecycle + terminal proof

Owns:

- bridge transaction lookup from `execute_scoped`;
- provider-selected retained-operation closure;
- multiple successful bounded executions on same exact workspace;
- relative cwd confinement;
- fail-closed failure/timeout/cleanup behavior;
- explicit terminalization/readback;
- legacy one-shot scoped-script compatibility regressions;
- Windows physical end-to-end fixture evidence.

Live Agent installation/restart is **not** an implementation Slice. Physical accepted-build activation and model-facing live proof belong to Acceptance after implementation evidence is complete.

## 5. Verification strategy

### Static/schema/unit

- Host binding absent/relative/malformed/platform-invalid;
- safe segment validation (`.`, `..`, separators, drive/UNC injection);
- deterministic path derivation and strict descendant proof;
- caller placement mismatch/path injection rejected;
- source commit full-SHA validation;
- `local_api.describe` contains bounded materialization schema and no destination-path authority;
- operation-class authority cannot be caller-selected;
- legacy `provision_scope(purpose=scoped_script)` / `execute_scoped` contract unchanged.

### Scope/audit/sandbox integration

- exact workspace stored in scope and read back;
- generation/TTL/Attempt/semantic drift rejects;
- audit START identity exactly matches current scope/workspace;
- no workspace write on START failure;
- AppContainer/Job/ACL closure evidence remains complete;
- terminal scope cannot reactivate.

### Repository materialization

- benign repository exact commit materializes and `rev-parse HEAD` equals admitted SHA;
- wrong SHA/ref/repository fails;
- pre-existing unbound non-empty target fails;
- partial source acquisition/materialization never returns Materialized;
- verified retry returns/readbacks prior durable result without duplicate creation;
- credential unavailable has explicit bounded result and no fallback.

### Canonical preservation

Before/after readback on fixture canonical checkout:

```text
branch
HEAD
working tree clean
repository identity
```

No bridge-created state may require branch switching/reset/cleaning in canonical checkout.

### Multi-operation lifecycle

- materialize once;
- execute bounded operation A successfully;
- verify process/Job/temporary authority closed while transaction remains current;
- execute bounded operation B successfully on same exact workspace;
- explicit terminalize;
- terminal readback exact same scope/generation;
- third execution attempt rejected;
- legacy one-shot scope still terminal after one execution.

### Regression suites

Run focused existing suites for:

```text
mutation placement/scope
Windows mutation sandbox
pre-execution audit lineage
canonical repository firewall
devforge_runtime local_api
scoped script execution
user-scoped Git/source transport where reused
```

Plus repository generic CI/macOS checks appropriate to changed surfaces. Windows-only physical behavior must not be accepted from mocks alone.

## 6. Acceptance boundary

Implementation completion proves code/tests on exact Task transport.

Acceptance additionally requires an independently activated accepted Agent build and real connected-host evidence:

```text
local_api.describe shows materialize_workspace
Host binding resolves current DevForge root
harmless fixture materializes at exact DevForge path
HEAD/repository/isolation readback passes
canonical source before/after unchanged
2 sequential same-workspace scoped operations pass
explicit terminalization/readback passes
path injection/stale scope/wrong SHA/audit failure negatives fail before success
```

No production Hub change is required; the existing `sentinel_local_api` envelope remains transport.

## 7. Safety / non-goals

Forbidden during this Task:

- generic shell/exec fallback;
- direct caller-selected `sentinel_git clone` as materialization authority;
- direct worktree creation bypass;
- `operator_unrestricted`;
- file_ops/command allowlist widening;
- canonical checkout mutation/repair;
- credential exposure to AppContainer/model;
- provider switch;
- production Hub source/deploy mutation;
- publication/push/CAS features already owned by PR-013;
- copying unmerged PR-013 implementation;
- cross-repository DevForge contract mutation;
- live Agent restart/install inside implementation slices;
- independent Codex requirement;
- new Development Gate/stage.

## 8. Plan review questions

Plan Review must specifically decide whether R1 is implementable with the ownership split above and must reject if any of these remain unresolved:

1. Does the proposed provider-selected placement seam preserve existing legacy scope revalidation/generation semantics without caller path authority?
2. Is `locations.devforge_workspace_root` consumed as Host configuration without silently rewriting `mutation_execution.workspace_root`?
3. Is the PR-013 overlap boundary concrete enough to prevent duplicate repository source materializer / transaction implementation?
4. Does multi-operation scope closure leave zero process/ACL authority between operations while preserving the Attempt transaction?
5. Can exact source materialization satisfy private-source security without credential exposure or fallback?
6. Are Acceptance physical proofs sufficient to distinguish provider materialization from a mock-only technical proxy?

Canonical next action after this Plan is persisted and read back:

```text
#开发评审 PR-014-devforge-execution-workspace-materialization-bridge-v1
```