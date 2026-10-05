---
task_id: PR-014-devforge-execution-workspace-materialization-bridge-v1
title: SentinelX DevForge Execution Workspace Materialization Bridge V1
project_id: sentinelx-cloud-core
repository: bewaterhere-coder/sentinelx-cloud-core
requirement_revision: 1
development:
  stage: plan_review_rejected
  gates:
    requirement_ready: true
    plan_approved: false
    acceptance_approved: false
    completion_verified: false
  plan_revision: 1
  latest_plan_review: rejected_round_1
  implementation_authorized: false
  blocking_findings:
    - F1-placement-receipt-pre-scope
    - F2-devforge-sandbox-root-admission
    - F3-pr013-transaction-overlap
  next_expected_actor: planner
  authorization:
    mode: legacy_command_scoped
artifacts:
  requirement_review: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-requirement-review-r1.md
  plan: docs/plans/PR-014-devforge-execution-workspace-materialization-bridge-v1-plan.md
  latest_plan_review: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-plan-review-r1.md
transport:
  type: github-pr
  pr_number: 14
  branch: task/devforge-execution-workspace-materialization-bridge-v1
  base_branch: main
requirement_readiness:
  result: Ready
  depth: deep
  material_questions: []
  ui_semantics:
    applicability: NotApplicable
  challenge_completed: true
---

# Requirement

## Problem

DevForge already defines deterministic Host workspace placement and the canonical capability `development.execution_workspace_materialize`. A caller supplies semantic execution identity; the Host owns concrete roots and must derive the execution workspace. A Placement Receipt is evidence only and does not itself grant filesystem authority.

SentinelX already has provider-owned mutation placement, durable mutation scope, pre-execution audit lineage, Windows AppContainer/Job confinement, canonical-repository mutation firewall and the bounded `devforge_runtime` local API. However the current Host configuration exposes two different workspace placement realities:

```text
DevForge Host binding:
locations.devforge_workspace_root = D:\coco
→ DevForge execution_root = D:\coco\workspaces

SentinelX scoped-mutation placement:
mutation_execution.workspace_root = D:\SentinelX\mutation-workspaces
→ <workspace_root>/<repository-digest>/<semantic-digest>
```

The provider therefore cannot yet prove that a DevForge Placement Receipt, a SentinelX mutation scope and the real materialized execution checkout all identify the same Host workspace. The existing `devforge_runtime` endpoint also lacks a bounded DevForge workspace-materialization operation that creates an exact repository checkout and returns the evidence required by `development.execution_workspace_materialize`.

A generic `git clone(dest=...)`, direct `git worktree add`, generic script/shell execution or a caller-supplied workspace path is not a conforming solution because those paths do not bind DevForge placement admission to provider-owned scope/audit/sandbox authority.

## Goal

Add a minimal SentinelX **DevForge Execution Workspace Materialization Bridge** that composes existing provider authority instead of creating a second executor, scope store or sandbox.

The target lifecycle is:

```text
repository + Task/Evolution scope + Run/Attempt[/Slice] + workspace purpose
+ exact expected source commit
        ↓
resolve current Host DevForge workspace binding
        ↓
derive DevForge execution placement independently on Host
        ↓
compare optional DevForge placement evidence
        ↓
provision scope bound to the exact derived future workspace
        ↓
revalidate scope
        ↓
persist durable audit START
        ↓
materialize exact isolated repository checkout as first scoped mutation
        ↓
read back repository identity + path + HEAD + isolation
        ↓
emit materialization receipt
        ↓
execute_scoped on the same provider-owned workspace for 0..N bounded operations
        ↓
explicit terminalize_scope at Attempt terminal boundary
        ↓
terminal-state readback
```

The canonical/source checkout must remain the canonical source role (`main + clean` for current DevForge-managed repositories) and must not become the mutation workspace.

## Required behavior

### R1 — Semantic-only materialization request

The model/caller may supply only semantic identity and source identity needed to determine the workspace and source revision:

```yaml
repository:
  vcs: git
  authority: <host>
  path: <owner/repository>
lineage:
  project_id: <project>
  task_id: <task-or-evolution-id>
  run_id: <run>
  attempt_id: <attempt>
  slice_id: <optional>
workspace_purpose: implementation | fixing | verification | repair | resume | evolution | release | finalization
source_binding:
  expected_commit: <immutable full commit sha>
  transport_ref: <optional comparison evidence>
```

Caller-controlled writable target fields are forbidden as authority, including equivalents of:

```text
dest
target_path
workspace_path
execution_workspace
checkout_path
worktree_path
cache_path
staging_path
```

If a DevForge Placement Receipt is supplied, its concrete path is comparison evidence only. It never overrides Host derivation.

### R2 — Host-owned DevForge placement derivation

For this bridge, SentinelX must derive current placement from the effective Host DevForge workspace binding rather than from a second independent DevForge placement root.

For SentinelX V1 the binding is the effective policy location:

```text
locations.devforge_workspace_root
```

The provider derives:

```text
workspace_root = locations.devforge_workspace_root
execution_root = <workspace_root>/workspaces
exact_workspace = <execution_root>/<owner>/<repository>/<task-or-evolution-id>/<attempt-id>
```

Owner, repository, scope and Attempt segments must be validated as single safe path segments. The exact workspace must be a strict descendant of the derived execution root.

`mutation_execution.workspace_root` may remain valid for legacy/non-DevForge scoped-mutation behavior, but it must not silently become a second DevForge execution-placement truth.

Missing/malformed Host binding returns a fail-closed provider-unavailable/configuration result before scope minting or filesystem creation.

### R3 — DevForge/Provider placement equality

When DevForge provides placement evidence, SentinelX independently recomputes the current Host target and requires normalized equality.

Mismatch returns:

```text
WorkspacePlacementMismatch
```

Target escape returns:

```text
WorkspacePlacementEscape
```

No mismatch authorizes retargeting to the caller path, the legacy provider workspace root, a temporary sibling or the canonical checkout.

### R4 — Exact immutable source identity

Placement identity and source identity are separate.

The workspace location is derived from repository/task/attempt semantics, while repository contents are bound to an immutable `source_binding.expected_commit`.

A logical branch/ref may be used only as transport evidence. Successful materialization must prove:

```text
materialized repository identity == admitted repository identity
workspace HEAD == source_binding.expected_commit
```

Branch-name-only equality is insufficient.

Wrong/missing source object, repository identity mismatch or ref/SHA mismatch returns a bounded source-materialization failure and creates no successful receipt.

### R5 — Provider-owned scope before materialization

The exact workspace must be sealed into provider-owned mutation authority before any workspace creation.

The provider must reuse the existing `MutationScopeStore` / scope lifecycle and bind equivalent facts:

```text
repository identity
project/task/run/attempt[/slice]
exact workspace
placement generation / binding digest
protected/canonical inventory
fixed allowed operation class(es)
```

The caller must not select or widen operation classes.

The bridge must distinguish DevForge `workspace_purpose` from SentinelX operation-class purpose. Existing `purpose=scoped_script` semantics must not be overloaded to mean implementation/fixing/release/etc.

### R6 — Audit START before first workspace write

After scope provision and revalidation, durable audit START must exist before the first material workspace mutation, including directory creation, repository-source hydration, checkout or equivalent materialization write.

The bridge must reuse the existing audit journal and sandbox binding. It must not create a second audit path.

Audit persistence/binding failure returns fail closed before successful filesystem materialization evidence.

### R7 — Dedicated bounded materialization action

The Agent-owned `devforge_runtime` endpoint must expose a bounded materialization action or equivalent structured contract.

The action must:

- accept no caller destination path;
- resolve the exact workspace from current Host/provider authority;
- consume exact source identity;
- reuse existing scope/audit/sandbox primitives;
- reuse a canonical provider-owned repository materializer/broker when available;
- never become a generic clone/copy primitive;
- return bounded provider evidence rather than credential material or arbitrary Host path authority.

The action must be discoverable through `local_api.describe`.

### R8 — Repository source acquisition boundary

Private/public source acquisition is provider authority, not caller script authority.

The bridge must not solve private repository materialization by exposing SSH keys, credential-helper state, tokens or the interactive-user environment to the AppContainer/model.

If the current provider cannot safely acquire the exact source under its bounded repository transport, return a stable fail-closed result such as:

```text
WorkspaceSourceCredentialUnavailable
```

No generic script/exec/clone fallback is permitted.

If PR-013 or another canonical provider component supplies the repository source broker/materializer before this Task implements the bridge, this Task must consume that canonical capability instead of reimplementing or copying unmerged code.

### R9 — Materialization read-back and receipt

Success requires real read-back, not only process exit status.

The receipt must provide equivalent evidence:

```yaml
execution_workspace_materialization:
  state: Materialized
  capability: development.execution_workspace_materialize
  placement_policy: host-workspace-layout-repository-placement-v1
  placement_role: execution_root
  target_path: <Host evidence only>
  repository_identity: <verified normalized identity>
  source_commit: <verified exact commit>
  scope_ref:
  scope_generation:
  scope_digest:
  placement_ref:
  scope_revalidated: true
  audit_operation_id:
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

Concrete Host paths remain invocation/receipt evidence only and must not become Project Binding or Development Project Registry truth.

### R10 — Same-workspace bounded execution lifecycle

A DevForge materialized workspace is an Attempt-scoped transaction, not a one-shot script scratch directory.

After successful materialization, later bounded `execute_scoped` operations must resolve the exact workspace from provider-owned scope/transaction authority and must not accept caller retargeting.

Before every later material mutation boundary, revalidate at least:

```text
scope current + generation current
placement binding current
workspace binding current
repository binding current
canonical firewall determinate/non-canonical
required audit lineage
```

Successful non-terminal execution in this bridge must not automatically destroy the whole Attempt authority needed by subsequent bounded operations.

Legacy non-transaction `scoped_script` behavior must retain its existing one-shot auto-terminalization semantics. If the provider needs a multi-operation transaction state machine, it must be explicit and provider-owned rather than a caller-selectable "keep scope open" flag.

### R11 — Explicit terminal boundary

At the real Attempt terminal boundary the provider performs explicit terminalization and read-back:

```text
terminalize_scope
→ inspect/read back same scope + generation
→ terminal | revoked | expired
```

A terminal/revoked/expired scope cannot be reactivated.

Successful Host mutation completion evidence requires terminal read-back; `provisioned` or `active` is not a terminal completion state.

### R12 — Canonical source preservation

Before and after materialization/bridge execution, the canonical/source checkout must remain source-only.

For the current DevForge-managed canonical role, acceptance must prove equivalent facts:

```text
canonical checkout branch remains canonical branch
canonical working tree remains clean
canonical HEAD is not switched merely to create the execution workspace
workspace != canonical checkout
```

The bridge must not use direct `git worktree add` if doing so mutates canonical checkout metadata outside the admitted scoped transaction. A future dedicated canonical-source mechanism would require separate explicit authority.

### R13 — Retry, partial failure and idempotent read-back

Same Attempt retry rules:

- absent target + current exact scope may materialize once;
- an existing workspace with a matching durable materialization receipt, repository identity, exact source commit and current transaction binding may converge through idempotent read-back;
- a non-empty/unbound/mismatched workspace fails closed;
- partial materialization cleanup may remove only transaction-owned partial output;
- failure to prove cleanup/residue state prevents a `Materialized` claim;
- verified successful side effects are not replayed merely because the caller retries.

### R14 — No fallback escalation

Placement, source, scope, audit, sandbox or materialization failure must never fall back to:

```text
generic script_run
generic exec/shell
generic sentinel_git clone with caller dest
direct git worktree add
generic filesystem edit/copy
operator_unrestricted
file_ops / command allowlist expansion
provider switch
canonical checkout mutation
production Hub modification
```

## Active overlap and ownership boundaries

### PR-013 — Repository Materialization & Scoped Publication Bridge

PR #13 (`PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1`) is currently an active Draft Task at Plan Review and materially overlaps repository-source materialization plus multi-operation transaction lifecycle.

This Task has distinct ownership:

```text
PR-014 owns:
- alignment of SentinelX DevForge placement with effective Host DevForge workspace binding;
- exact DevForge execution-root path semantics;
- bridge from DevForge placement/materialization admission to provider scope authority;
- materialization receipt shape/evidence required by development.execution_workspace_materialize;
- explicit proof that later scoped execution stays bound to that same DevForge workspace.

PR-014 does NOT own:
- general scoped publication/checkpoint/push;
- repository publication CAS;
- a second repository credential broker;
- a second source snapshot/materializer when an equivalent implementation becomes canonical through PR-013.
```

Before Plan approval and again before implementation touching overlapping provider files, read the exact current PR-013 head, changed files and disposition. Unmerged PR-013 code is evidence only and must not be copied as implementation authority. If equivalent source-materialization/lifecycle primitives land on `main`, reuse them.

### PR-012 / PR-010

PR-012 explicit `execution_profile=scoped_mutation` and PR-010 canonical repository firewall are merged canonical baselines and must not regress.

### DevForge repository boundary

DevForge v2.40.0 already defines Host workspace layout, `development.execution_workspace_materialize`, scope-before-materialization, audit-before-materialization, receipt and no-bypass semantics.

This SentinelX Task must consume those contracts. It does not authorize cross-repository mutation of `bewaterhere-coder/DevForge`. If Acceptance discovers a real consumer-contract defect rather than a provider defect, that is a separate explicit DevForge change.

## Acceptance criteria

- **AC1:** With effective Host binding `workspace_root=<W>`, repository `<owner>/<repo>`, scope/task `<S>` and Attempt `<A>`, provider independently derives exactly `<W>/workspaces/<owner>/<repo>/<S>/<A>` and binds scope authority to that exact future workspace.
- **AC2:** `local_api.describe devforge_runtime` exposes the bounded materialization contract without caller-controlled writable destination fields.
- **AC3:** Caller path injection, DevForge/provider placement mismatch, path escape and malformed identity all fail before material workspace creation.
- **AC4:** Wrong source commit/ref/repository, unavailable source credential, stale/expired/foreign scope and scope binding drift fail closed with no successful materialization receipt and no generic fallback.
- **AC5:** Durable audit START precedes the first material workspace write; audit-start failure leaves no successful workspace materialization state.
- **AC6:** A valid request materializes the exact admitted repository source into the exact Host-derived execution workspace and read-back proves repository identity + exact HEAD + isolation.
- **AC7:** Canonical checkout remains canonical branch + clean and is never used as the mutation workspace.
- **AC8:** Materialization receipt contains provider-owned scope/placement/audit/read-back evidence consumable by the existing DevForge `development.execution_workspace_materialize` contract.
- **AC9:** At least two successful bounded operations may run against the same materialized Attempt workspace under the same provider transaction binding without caller retargeting; legacy one-shot `scoped_script` semantics remain unchanged.
- **AC10:** Explicit terminalization then reads back the same scope/generation in terminal/revoked/expired state; terminal authority cannot be reactivated.
- **AC11:** Retry after verified materialization converges by read-back and does not recreate/overwrite the checkout; mismatched pre-existing content fails closed.
- **AC12:** Canonical firewall, mutation-scope, audit-lineage, AppContainer/Job and explicit-execution-profile regression suites remain passing.
- **AC13:** Windows physical integration proves placement → scope → audit START → materialization → exact HEAD readback → multiple same-workspace bounded executions → terminal scope readback on a benign fixture repository.
- **AC14:** No independent Codex requirement, no new Development Gate, no production Hub modification and no permission/allowlist expansion are introduced.

## Scope

### In scope

- SentinelX DevForge workspace placement alignment using effective Host workspace binding;
- safe path-segment validation and provider/DevForge placement comparison;
- provider-owned scope binding to exact DevForge execution workspace;
- bounded materialization local-api action/composition;
- exact source-commit binding and source acquisition failure semantics;
- materialization read-back and receipt;
- same-workspace multi-operation transaction composition required by DevForge;
- explicit terminal scope read-back;
- tests and operator/provider documentation;
- overlap reconciliation with canonical PR-013 results if/when they land.

### Out of scope

- generic publication/checkpoint/push (owned by PR-013);
- generic Git redesign;
- arbitrary caller-selected Host paths;
- migration/deletion of existing historical workspaces;
- automatic canonical checkout repair;
- Host file_ops/allowlist expansion;
- exposing user credentials to AppContainer/model;
- production `mcp.sentinelx.app` Hub modification;
- cross-repository DevForge Runtime mutation;
- independent Codex requirement;
- new Development Gate or lifecycle stage.

## Requirement challenge / disconfirmation

The Plan and implementation must actively disconfirm at least these cases:

1. SentinelX still materializes under `mutation_execution.workspace_root` instead of the effective DevForge execution root while claiming compatibility.
2. A caller path or stale Placement Receipt can retarget provider scope authority.
3. A branch name matches but the workspace HEAD differs from the admitted immutable commit.
4. Audit START is recorded only after directory/checkout creation.
5. A stale/foreign/terminal scope can materialize or mutate another Attempt's workspace.
6. `execute_scoped` can switch to another cwd/workspace outside the sealed binding.
7. successful transaction execution still auto-terminalizes after the first operation and prevents a second bounded operation.
8. legacy one-shot scoped execution loses its existing terminalization behavior.
9. canonical checkout branch/working tree changes during materialization.
10. private-source failure causes generic clone/script/exec fallback.
11. PR-013 unmerged code is copied or treated as canonical authority.
12. a retry after successful materialization repeats destructive/verified side effects.

## Refinement evidence

Normal example:

```text
Host binding D:\coco
repository bewaterhere-coder/Example
Task PR-014-example
Attempt 1
→ provider derives D:\coco\workspaces\bewaterhere-coder\Example\PR-014-example\1
→ exact commit C materializes there
→ readback HEAD=C
→ two scoped operations use the same sealed workspace
→ explicit terminalization reads terminal
```

Boundary example: the same semantic request arrives with a DevForge receipt pointing to another path. Provider derivation wins; mismatch is rejected before filesystem creation.

Counterexample: accepting `dest=D:\tmp\x` or silently using `D:\SentinelX\mutation-workspaces` would make the operation convenient but breaks the DevForge/Host authority binding, so it is non-conforming.

Readiness decision: **Ready**. The prior review's two material gaps are now frozen: exact immutable `source_binding.expected_commit`, and a provider-owned multi-operation Attempt lifecycle that preserves legacy one-shot behavior. No unresolved material decision remains before Planning.