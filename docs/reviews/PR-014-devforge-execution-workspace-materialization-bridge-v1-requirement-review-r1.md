# PR-014 — SentinelX DevForge Execution Workspace Materialization Bridge V1 — Requirement Review R1

## Decision

```yaml
task_id: PR-014-devforge-execution-workspace-materialization-bridge-v1
review_mode: Review + Refine
result: Ready
requirement_revision: 1
ui_semantics: NotApplicable
material_questions: []
```

The reviewed requirement is ready for Planning after adopting two material refinements discovered during standalone review:

1. materialization binds an immutable `source_binding.expected_commit`; placement identity alone is not enough to define checkout contents;
2. DevForge workspace execution uses an explicit provider-owned multi-operation Attempt lifecycle so materialization may be followed by multiple bounded executions before explicit terminalization, while legacy one-shot `scoped_script` execution remains unchanged.

## Design understanding

The requirement closes the boundary between DevForge's existing Host workspace placement/materialization contract and SentinelX's real Host authority:

```text
DevForge semantic placement
→ SentinelX Host-owned placement
→ exact scope/workspace binding
→ durable audit START
→ sandboxed repository materialization
→ exact HEAD/isolation readback
→ DevForge materialization receipt
→ same-workspace scoped execution
→ explicit terminal scope readback
```

This is not a request for a generic clone API or for adding a caller-selected path parameter. The bridge must make DevForge placement evidence and SentinelX scope authority identify the same exact workspace.

## Provider evidence reviewed

### Existing reusable primitives

Current canonical provider code already supplies:

- `mutation_placement.resolve_placement` and `revalidate_placement` for provider-owned future-workspace evidence;
- `MutationScopeStore` for durable repository/lineage/workspace binding, generation, uniqueness and terminalization;
- durable mutation audit START/FINISH lineage;
- `WindowsMutationSandbox.activate` with AppContainer, exact ACL and Job enforcement;
- `devforge_runtime` scope lifecycle plus `execute_scoped` with explicit `execution_profile=scoped_mutation`;
- structured Git clone mechanics with fixed argv, timeout, non-empty destination protection and transaction-owned partial-clone cleanup.

The provider therefore does not need a second scope store, executor, audit journal or sandbox.

## Findings and adopted refinements

### BLOCKER-01 — DevForge placement and provider placement are not currently the same rule

Current Host configuration identifies:

```text
locations.devforge_workspace_root = D:\coco
```

DevForge derives:

```text
D:\coco\workspaces\<owner>\<repo>\<scope>\<attempt>
```

Current SentinelX `mutation_execution.workspace_root` is separately configured and `resolve_placement` derives digest-based workspaces beneath that root.

**Adopted refinement:** PR-014 bridge placement is derived from the effective DevForge Host binding and exact semantic identity. Legacy `mutation_execution.workspace_root` remains valid for non-DevForge scoped mutation but is not DevForge placement authority.

### BLOCKER-02 — Exact source revision was missing

Repository + Task/Evolution + Attempt determines placement but not repository contents. A branch may move between admission and creation.

**Adopted refinement:** `source_binding.expected_commit` is mandatory immutable source identity. Success requires readback `workspace HEAD == expected_commit`.

### IMPORTANT-01 — Existing one-shot execution lifecycle conflicts with same-Attempt workspace reuse

Current scoped execution terminalizes its scope after one execution. DevForge materialized workspaces need materialize → execute 0..N → explicit terminalization.

**Adopted refinement:** repository/workspace bridge uses an explicit provider-owned multi-operation transaction lifecycle. Legacy `scoped_script` retains current one-shot behavior; there is no caller-selectable generic "keep scope open" switch.

### IMPORTANT-02 — Generic clone mechanics are reusable but their authority model is not

Existing structured clone accepts caller `dest`, so it cannot itself implement `development.execution_workspace_materialize`.

**Adopted refinement:** a bounded `devforge_runtime` materialization action derives destination only from Host/provider authority. Existing Git/source mechanics may be refactored/reused internally but caller destination authority is forbidden.

### IMPORTANT-03 — Safe private-source acquisition must fail closed

Scoped AppContainer execution intentionally strips reusable Git/SSH credential authority. Private-source materialization cannot be solved by injecting credentials into the sandbox.

**Adopted refinement:** provider-owned authenticated source acquisition is used only if safely available; otherwise return a stable source-credential/provider-unavailable failure and do not fall back to generic script/exec/clone.

### RESOLVED-01 — Audit-before-create is already an existing provider pattern

`WindowsMutationSandbox.activate` already requires scope revalidation and durable START binding before creating the exact workspace. The bridge must compose this path rather than reproduce it.

### RESOLVED-02 — No new DevForge Gate / no independent Codex requirement

The consumer capability already exists as `development.execution_workspace_materialize`; this Task is a provider bridge. No new workflow stage or independent Codex prerequisite is required.

## Active-task overlap review

PR #13 (`PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1`) is currently open at Plan Review and overlaps repository source materialization and multi-operation transaction lifecycle.

This review does not treat semantic similarity as Task identity. PR-014 remains a distinct Task because the user explicitly initiated a new requirement and DevForge Task identity defaults to isolation.

The ownership boundary is:

```text
PR-014:
  DevForge Host placement alignment
  development.execution_workspace_materialize bridge evidence
  exact DevForge execution-root path binding
  same-workspace execution/terminalization evidence

PR-013:
  general repository transaction source broker/materializer
  scoped publication/checkpoint/push and CAS readback
```

PR-014 must reuse equivalent PR-013 primitives only after they become canonical on `main`; unmerged PR-013 code is evidence, not implementation authority. Plan Review and implementation admission must re-read the exact current PR-013 state before touching overlap surfaces.

## Acceptance challenge

The requirement is considered wrong if any accepted implementation can:

- materialize under a path different from current DevForge placement while claiming bridge success;
- use caller path data as write authority;
- report Materialized without exact HEAD/repository/isolation readback;
- write before durable START;
- use a stale/foreign/terminal scope;
- mutate/switch the canonical checkout to create development state;
- expose credentials to the AppContainer/model;
- auto-terminalize the transaction after the first successful non-terminal operation;
- weaken legacy one-shot terminalization;
- copy unmerged PR-013 implementation or fall back to generic mutation.

## Readiness

**Ready.**

The canonical Requirement Revision 1 incorporates the material review findings and has no unresolved product/security decision. Planning must keep the PR-013 overlap boundary explicit and fail closed if the exact provider composition is not yet canonical.