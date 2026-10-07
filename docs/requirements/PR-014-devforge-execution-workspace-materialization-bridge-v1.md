---
task_id: PR-014-devforge-execution-workspace-materialization-bridge-v1
title: SentinelX DevForge Execution Workspace Materialization Bridge V1
project_id: sentinelx-cloud-core
repository: bewaterhere-coder/sentinelx-cloud-core
requirement_revision: 4
development:
  stage: plan_review
  gates:
    requirement_ready: true
    plan_approved: false
    acceptance_approved: false
    completion_verified: false
  plan_revision: 8
  latest_plan_review: rejected_round_7
  prior_plan_review: approved_round_6
  latest_plan_remediation: requirement_r4_architecture_reconciliation
  prior_plan_remediation: plan_r2_remediation_r1
  implementation_authorized: false
  blocking_findings: []
  current_slice: null
  current_slice_state: null
  completed_slices: [S01, S02]
  pending_slices: []
  implementation_execution_complete: false
  formal_acceptance_performed: false
  acceptance_disposition: superseded_by_requirement_r3_replan
  acceptance_blocker: null
  acceptance_blocker_detail: null
  material_architecture_decision_required: false
  material_architecture_decision: accepted_dual_host_owned_source_and_execution_binding
  secondary_acceptance_finding: planned_repair_in_requirement_r3
  exact_candidate_activation_required: false
  latest_acceptance_checkpoint: docs/checkpoints/PR-014-devforge-execution-workspace-materialization-bridge-v1-acceptance-r2-decision-required-20261008.yaml
  latest_acceptance_review: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-acceptance-r2.md
  completed_slices_preserved: [S01]
  preserved_completed_candidate_slices: [S02]
  preserved_s02_product_candidate: 45dc99d15a23c499b4c1500fab60ed5e76475aeb
  s02_product_mutation_replay: forbidden
  prior_plan_revision: 6
  prior_slice_set_status: invalidated_by_requirement_revision_4
  requirement_change_impact: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-requirement-r4-change-impact.md
  bootstrap_required_before_current_slice: false
  bootstrap_target: null
  bootstrap_command: null
  bootstrap_admission_status: not_required_no_pending_slice
  bootstrap_override_state: expired_by_requirement_revision_3
  prior_bootstrap_override: docs/overrides/PR-014-devforge-execution-workspace-materialization-bridge-v1-bootstrap-execution-override.yaml
  latest_bootstrap_receipt: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-bootstrap-execution-override-r1-receipt.yaml
  execution_disposition: requirement_r4_replanned_no_implementation
  execution_blocker: null
  execution_failure_state: null
  execution_failure_reason: null
  latest_execution_run: docs/execution/PR-014-devforge-execution-workspace-materialization-bridge-v1-s02-run-001.yaml
  latest_execution_checkpoint: docs/checkpoints/PR-014-devforge-execution-workspace-materialization-bridge-v1-s02-completion-20261008.yaml
  preserved_s02_completion_receipt: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-s02-completion-receipt.yaml
  latest_s02_reconciliation_receipt: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-s02-r6-reconciliation-receipt.yaml
  prior_bootstrap_receipt: docs/checkpoints/PR-014-devforge-execution-workspace-materialization-bridge-v1-harness-bootstrap-blocked-20261008.yaml
  superseded_slice_set_status: invalidated_by_requirement_revision_4
  planned_pending_delta_slice: null
  next_expected_actor: reviewer
  canonical_next_action: "#开发评审 PR-014-devforge-execution-workspace-materialization-bridge-v1"
  authorization:
    mode: legacy_command_scoped
artifacts:
  requirement_review: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-requirement-review-r1.md
  requirement_change_impact: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-requirement-r3-change-impact.md
  plan: docs/plans/PR-014-devforge-execution-workspace-materialization-bridge-v1-plan.md
  latest_plan_review: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-plan-review-r7.md
  latest_plan_review_transition_receipt: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-plan-review-r7-transition-receipt.yaml
  prior_plan_review: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-plan-review-r6.md
  prior_plan_review_transition_receipt: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-plan-review-r6-transition-receipt.yaml
  superseded_plan_review: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-plan-review-r5.md
  superseded_plan_review_transition_receipt: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-plan-review-r5-transition-receipt.yaml
  latest_plan_remediation: docs/checkpoints/PR-014-devforge-execution-workspace-materialization-bridge-v1-plan-remediation-r4-20261008.yaml
  latest_plan_remediation_transition_receipt: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-plan-remediation-r4-transition-receipt.yaml
  latest_replan: docs/checkpoints/PR-014-devforge-execution-workspace-materialization-bridge-v1-replan-r8-20261008.yaml
  latest_replan_transition_receipt: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-replan-r7-transition-receipt.yaml
  execution_slice_set: null
  superseded_execution_slice_set: docs/execution/PR-014-devforge-execution-workspace-materialization-bridge-v1-plan-r6-slices.yaml
  latest_execution_run: docs/execution/PR-014-devforge-execution-workspace-materialization-bridge-v1-s02-run-001.yaml
  latest_execution_checkpoint: docs/checkpoints/PR-014-devforge-execution-workspace-materialization-bridge-v1-s02-completion-20261008.yaml
  preserved_s02_completion_receipt: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-s02-completion-receipt.yaml
  superseded_execution_slice_set: docs/execution/PR-014-devforge-execution-workspace-materialization-bridge-v1-plan-r5-slices.yaml
  prior_plan_review: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-plan-review-r5.md
  prior_plan_remediation: docs/checkpoints/PR-014-devforge-execution-workspace-materialization-bridge-v1-plan-remediation-r1.yaml
  prior_execution_slice_set: docs/execution/PR-014-devforge-execution-workspace-materialization-bridge-v1-slices.yaml
  prior_plan_review_transition_receipt: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-plan-review-r2-transition-receipt.yaml
  requirement_change_impact: docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-requirement-r2-invalidation.md
  latest_slice_checkpoint: docs/checkpoints/PR-014-devforge-execution-workspace-materialization-bridge-v1-s02-completion-20261008.yaml
  latest_gate_transition: docs/checkpoints/PR-014-devforge-execution-workspace-materialization-bridge-v1-implementation-to-acceptance-transition-receipt.yaml
  latest_acceptance_checkpoint: docs/checkpoints/PR-014-devforge-execution-workspace-materialization-bridge-v1-acceptance-r2-decision-required-20261008.yaml
transport:
  type: github-pr
  pr_number: 14
  branch: task/devforge-execution-workspace-materialization-bridge-v1
  base_branch: main
requirement_readiness:
  result: Ready
  depth: deep
  requirement_revision: 4
  revision_reason: pr021_minimal_runtime_short_mutation_reconciliation
  prior_plan_revalidation_required: true
  material_questions: []
  ui_semantics:
    applicability: NotApplicable
  challenge_completed: true
---

# Requirement

## Requirement Revision 4 — Canonical effective scope (2026-10-08)

**Normative precedence:** This section supersedes all incompatible R1–R3 body clauses, including old R2/R3 Goal, R4/R7 source materialization, Development Host handoff, `devforge_runtime.materialize_workspace` as a required deliverable, and the legacy acceptance criteria wherever they imply long-Agent/bootstrap lifecycle. Historical sections below are preserved exclusively for lineage and may not be used as implementation authority. PR-021's frozen `docs/architecture/sentinelx-minimal-runtime-boundary-v1.md` on canonical main is controlling architecture.

### Retained problem and outcome

For explicit bounded short Host mutation, SentinelX may need a provider-owned, isolated workspace placement and confinement substrate. PR-014 retains **only** the minimum demonstrably needed to admit, scope, audit, execute, read back, and terminalize a small synchronous mutation. It shall not build a generic Git materializer or a user-level development workspace lifecycle by inertia. If an existing canonical runtime already supplies the relevant primitive, reuse it and make no duplicate system.

### Required security invariants

1. Source and execution placement are **independent Host-owned bindings**. The Host's admitted canonical source inventory resolves protected `D:\coco\repos\<owner>\<repository>` (current Windows topology); an independently configured dedicated execution root (preferred `D:\SentinelX\devforge-workspaces`, if actually admitted by effective Host policy) is outside all protected/canonical roots. Neither path is caller-selectable. Host effective policy, not this example, is authority.
2. `D:\coco` protection may never be reduced, removed or circumvented by carve-outs/allowlists. No fallback to `mutation_execution.workspace_root` or legacy `locations.devforge_workspace_root=D:\coco` is permitted for the DevForge execution role. Do not mutate canonical `main` or operate on its tree as a workspace.
3. The provider derives and validates path identity from closed semantic inputs, rejects traversal/symlinks/overlap/binding drift, and seals exact operation/write scope into the canonical durable MutationScope lifecycle **before any write**. Scope authority must not be widened by migration, retry or restart.
4. Durable MutationScope records must parse/migrate known compatible additive fields including `runtime_read_authority_roots`, preserve their values on read/write, and fail closed for unknown authority-bearing fields; do not delete/reset the store as a repair.
5. Durable audit START precedes mutation; provider-owned AppContainer/ACL/Job confinement, canonical mutation firewall, structured readback, failure cleanup and authority terminalization remain mandatory wherever the bounded operation requires them. No generic shell/Git clone/worktree/filesystem bypass is admissible.
6. Caller controls no concrete workspace path, SID, ACL, executable, credential, source-cache path or mutation operation class. Provider-local effects remain typed and bounded; no new broad MCP Tool Projection.

### Explicit removal / HOLD

No PR-014 implementation authority exists for long-running CodeBuddy/Codex Agents, Direct Development Host bootstrap, handoff ACL normalization for user-level Agents, Development Host execution lifecycle, provider-owned Git source capsule or general source hydration, reusable checkout materialization, retained multi-operation transactions, long build/test orchestration, task scheduling, and durable long-operation recovery. Former `development.execution_workspace_materialize` full checkout/handoff receipt is not an acceptance deliverable. Any independently necessary short-mutation source access must be narrowly rejustified and reviewed, not inherited from S02.

### Canonical product-source topology and admission

At R4 drafting, canonical `main@cd42e371f18056327c1d8b744f8956a76bc11541` did **not** contain `src/sentinelx_core/policy.py`, `src/sentinelx_core/mutation_scope.py`, `src/sentinelx_core/handlers/devforge_runtime.py`, `pyproject.toml` or `README.md`, although the old PR branch did. This is an observed mismatch, not authorization to restore or cherry-pick source. **The first gate of R8 must re-read fresh current main and establish actual authoritative implementation ownership/topology.** If current main still has no canonical implementation surface, block product mutation and require a separately reviewed topology/disposition decision on the same Task; never resurrect the historical tree solely to pass the Plan.

### Acceptance

AC-R4-1: Proven bounded short-mutation consumer need; no Agent lifecycle or implicit generic materialization.

AC-R4-2: Independent Host source/placement policy and protected-root non-overlap; fail closed for missing/drifting Host bindings, no caller path authority.

AC-R4-3: Exact durable scope and additive-state compatibility without authority widening; audit START before write; AppContainer/Job containment where relevant; terminalization and negative-access evidence.

AC-R4-4: Exact short-operation receipt and readback; failure never claims completion without evidence.

AC-R4-5: Main topology ownership resolved before code writes; integration strategy reviewed rather than old branch replay; no unauthorized CI/Host side effects.

### Historical evidence disposition

S01 completion evidence, S02 completion/reconciliation receipts and candidate `45dc99d15a23c499b4c1500fab60ed5e76475aeb` are preserved as **historical evidence only**. No S01/S02 product mutation replay, no automatic candidate promotion, no new PR/branch, no mutation on canonical main. Previous Plan R7, its rejected Review R7 and all prior Slice Sets are superseded execution authority. Any new slice requires separate Plan approval.

---

## Revision 2 — Bootstrap-safe cycle-break delta

Requirement Revision 2 is an explicit same-Task semantic revision requested through `#开发 PR-014-devforge-execution-workspace-materialization-bridge-v1 ...`.

R2 keeps the completed R1/S01 placement, scope-binding and Windows sandbox work as historical verified evidence, but changes the remaining Task boundary:

- PR-014 V1 must be able to complete independently of PR-013 merge/acceptance/completion.
- The first remaining deliverable is a **bootstrap-safe minimal `materialize_workspace` projection** sufficient to create a compliant isolated DevForge execution workspace for a registered Development Host.
- PR-014 may implement a narrow provider-owned source acquisition/capsule/materializer seed needed for that one materialization boundary.
- PR-014 must not copy or replay unmerged PR-013 implementation and must not absorb PR-013 publication, general repository-transaction, retained multi-operation or operation-closure ownership.
- After PR-013 later becomes canonical, PR-014-compatible code may consume that canonical backend through a normal future convergence/refactor; PR-013 is no longer a completion dependency for this Task.
- The prior Approved Plan R2 and its pending S02/S03 execution authority are stale under Requirement R2 and must not be executed.
- Completed S01 evidence is preserved and must not be replayed merely because the Requirement changed.

This revision is specifically intended to break the self-host cycle:

```text
PR-020 needs compliant execution workspace
→ PR-014 must provide materialize_workspace
→ PR-014 must no longer wait for PR-013 completion
→ PR-013 S03 remains untouched / no blind replay
```

## Problem

DevForge already defines deterministic Host workspace placement and the canonical capability `development.execution_workspace_materialize`. A caller supplies semantic execution identity; the Host owns concrete roots and must derive the execution workspace. A Placement Receipt is evidence only and does not itself grant filesystem authority.

SentinelX already has provider-owned mutation placement, durable mutation scope, pre-execution audit lineage, Windows AppContainer/Job confinement, canonical-repository mutation firewall and the bounded `devforge_runtime` local API. Acceptance R2 proved that canonical-source protection and DevForge execution placement must be separate Host-owned bindings.

Current canonical/source role:

```text
Host canonical repository inventory
→ D:\coco\repos\<owner>\<repository>
→ protected + source-only
```

Required DevForge execution placement role:

```text
locations.devforge_execution_workspace_root
→ preferred current Host value: D:\SentinelX\devforge-workspaces
→ outside D:\coco protected_root
→ exact workspace derived only from semantic execution identity
```

`mutation_execution.workspace_root` remains valid for legacy/non-DevForge scoped-mutation behavior but is not a DevForge execution-placement authority.

The provider must prove that canonical source binding, execution placement binding, Placement Receipt, MutationScope and the materialized checkout remain mutually consistent without weakening the canonical/protected source root. The existing `devforge_runtime` endpoint also lacks a bounded DevForge workspace-materialization operation that creates an exact repository checkout and returns the evidence required by `development.execution_workspace_materialize`.

A generic `git clone(dest=...)`, direct `git worktree add`, generic script/shell execution or a caller-supplied workspace path is not a conforming solution because those paths do not bind DevForge placement admission to provider-owned scope/audit/sandbox authority.

## Goal

Add a minimal SentinelX **DevForge Execution Workspace Materialization Bridge** that composes the already-completed PR-014 S01 placement/scope/sandbox primitives and provides one bootstrap-safe, path-free repository materialization operation.

The R2 target lifecycle is:

```text
repository + Task/Evolution scope + Run/Attempt[/Slice]
+ exact expected source ref + immutable expected commit
        ↓
resolve current Host DevForge workspace binding
        ↓
derive/read back DevForge Placement Receipt
        ↓
resolve Host-owned canonical source role / provider source transport
        ↓
verify repository identity + canonical-source main/clean role
        ↓
acquire exact immutable commit into provider-owned source cache/capsule
        ↓
provision + revalidate materialization scope bound to exact future workspace
        ↓
persist durable audit START
        ↓
run provider-generated AppContainer/Job materializer
        ↓
read back exact repository identity + source commit + isolation
        ↓
close temporary materializer process / AppContainer authority
        ↓
normalize and verify Host-owned Development Host handoff access
        ↓
emit development.execution_workspace_materialize receipt
```

The canonical/source checkout remains source-only and must stay on its canonical branch with a clean working tree. It may be used only as a Host-derived, read-only source-role anchor/object source under the bounded provider acquisition rules below; it is never the mutation workspace.

PR-014 R2 ends at compliant workspace materialization + handoff. General retained multi-operation `execute_scoped` transaction lifecycle and scoped publication remain PR-013 ownership.

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

### R2 — Independent Host-owned source and execution placement bindings

Canonical source role and execution placement role are distinct Host-owned authorities.

Canonical source binding is resolved from the effective Host canonical-repository inventory / registered canonical repository role:

```text
canonical_source = Host canonical repository inventory for admitted owner/repository
expected current topology = D:\coco\repos\<owner>\<repository>
```

The canonical source remains inside the broad protected root, source-only, canonical branch + clean, and never becomes an execution workspace.

DevForge execution placement is resolved independently from the dedicated effective policy location:

```text
locations.devforge_execution_workspace_root
```

For the current Windows Host, the preferred binding is:

```text
D:\SentinelX\devforge-workspaces
```

The provider derives:

```text
execution_root = locations.devforge_execution_workspace_root
exact_workspace = <execution_root>/<owner>/<repository>/<task-or-evolution-id>/<attempt-id>
```

Owner, repository, scope and Attempt segments must be validated as single safe path segments. The exact workspace must be a strict descendant of the execution root.

The execution root and exact workspace MUST be disjoint from every configured protected root and canonical repository root. In particular, the current broad `D:\coco` protection MUST NOT be removed, narrowed or bypassed.

The following are forbidden resolutions:

- removing or shrinking `D:\coco` from `protected_roots`;
- carving an exception/allowlist inside `D:\coco`;
- caller-selected source or execution paths;
- silently falling back to `mutation_execution.workspace_root`;
- silently continuing to use legacy `locations.devforge_workspace_root=D:\coco` as PR-014 execution placement truth;
- creating a second caller-visible placement authority.

Missing/malformed source binding, missing/malformed execution binding, protected-root overlap, canonical-root overlap or binding drift returns fail closed before scope minting or filesystem creation.

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

MutationScope durable-state reads MUST be forward-compatible with additive schema evolution without deleting or blindly discarding durable authority state.

Required semantics:

- parse current known fields through the current canonical record schema;
- recognize and migrate known additive fields from newer compatible schema generations, including `runtime_read_authority_roots`;
- preserve additive fields across read/write round-trips so a current runtime does not silently erase newer durable evidence;
- treat absent additive fields using explicit backward-compatible defaults;
- distinguish `schema_unsupported` from `state_corrupt`;
- unknown additive fields that can affect mutation/read/permission authority MUST fail closed until explicitly understood/migrated;
- terminal/historical records may be inspected and preserved without reactivating authority;
- deleting the durable store or dropping fields is never a compatibility repair.


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

### R8 — Bootstrap-safe provider source acquisition

Source acquisition is provider authority, not caller script authority.

The bootstrap-safe seed may use a narrow provider-owned Git source broker with these constraints:

1. derive the canonical source checkout from the current Host DevForge workspace binding and normalized repository identity; caller paths are forbidden;
2. verify the derived source checkout is the expected repository/origin, is on the canonical branch, and has a clean worktree before it participates;
3. bind source identity to both a safe logical ref and immutable `source_binding.expected_commit`; success always requires the exact commit;
4. first reuse an already-present exact Git object when available;
5. when an object is missing, a provider-owned bounded fetch MAY acquire only the admitted repository/ref/commit through the verified source remote/credential boundary without switching the source worktree, changing its checked-out branch, or exposing credentials;
6. if provider credentials/transport are unavailable, fail closed with `WorkspaceSourceCredentialUnavailable` or a more specific stable source-acquisition reason;
7. build an immutable provider-private source capsule/manifest from the exact commit, with digest/read-back evidence, before any workspace write;
8. caller/model never receives SSH keys, tokens, credential-helper state, raw remote authority, or a provider-private capsule path as executable authority.

The seed broker is not a general repository transaction engine. It does not publish, push, merge, retain an open repository transaction, or grant arbitrary Git argv.

PR-013 code must not be copied/imported while unmerged. Equivalent PR-013 functionality may become a future canonical backend only after it lands on `main`.

### R9 — AppContainer/Job repository materializer

The material workspace must be written by a provider-generated, bounded materializer running under the existing Windows AppContainer/Job boundary after durable audit START.

The materializer consumes only provider-sealed capsule/manifest evidence plus the exact scope/workspace binding. It must:

- reject traversal, reparse, ADS, special-file and manifest/digest mismatch;
- create the exact repository worktree and the minimum Git metadata/object state needed for later normal Development Host Git use;
- configure repository identity/remote only from provider-verified source evidence, never a caller remote URL;
- initialize the admitted logical branch/ref only when provider source read-back proves it resolves to the exact expected commit;
- write only inside the exact admitted execution workspace;
- leave no caller-controlled executable, target path, credential, ACL or operation-class surface.

Using generic `git clone` inside AppContainer is not required and is not a fallback; the trusted materializer may construct the checkout from provider-owned immutable source evidence.

### R10 — Dedicated bounded materialize_workspace action

The Agent-owned `devforge_runtime` endpoint must expose a bounded path-free action equivalent to:

```text
materialize_workspace
```

Its request accepts semantic repository/lineage/workspace-purpose/source identity only. It must not accept destination/root/SID/ACL/credential/Git-argv/operation-class fields.

The action must compose the completed S01 placement/scope/sandbox primitives, R8 source acquisition and R9 materializer, and return bounded receipt evidence. It must be discoverable through `local_api.describe`.

Most importantly, this action is **not gated on PR-013 merged/accepted/completion-verified state**. PR-013 absence is not a blocker for the bootstrap seed.

### R11 — Materialization read-back and receipt

Success requires real read-back, not process exit status.

The receipt must provide equivalent evidence:

```yaml
execution_workspace_materialization:
  state: Materialized
  capability: development.execution_workspace_materialize
  placement_policy: host-workspace-layout-repository-placement-v1
  placement_role: execution_root
  target_path: <Host evidence only>
  repository_identity: <verified normalized identity>
  source_ref: <verified logical ref>
  source_commit: <verified exact commit>
  source_capsule_digest: <provider evidence>
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
  materializer_containment_verified: true
  materializer_authority_closed: true
  development_host_handoff_ready: true
  canonical_source_mutated: false
  generic_bypass_used: false
  operator_unrestricted_used: false
```

Concrete Host paths remain invocation/receipt evidence only and must not become Project Binding or Development Project Registry truth.

### R12 — Development Host handoff

The bootstrap seed exists to hand an isolated Git workspace to a registered Development Host such as the task-scoped `direct:codebuddy` consumer.

Temporary AppContainer/materializer authority must be closed after materialization. The provider must then establish/read back a Host-owned handoff access state derived from the configured DevForge workspace policy, not from caller-provided SID/ACL data.

The handoff must prove:

- the exact workspace remains the admitted workspace;
- no AppContainer/temporary materializer identity remains with unintended authority;
- the registered Development Host can consume the workspace under the Host's existing workspace identity/access model;
- canonical/source checkout protection remains intact;
- no ancestor/root ACL widening or caller-selected principal is introduced.

If safe handoff access cannot be proven, return fail closed and do not emit `development_host_handoff_ready: true`.

### R13 — Canonical source preservation

Before and after source acquisition/materialization, the canonical/source checkout must remain source-only.

Acceptance must prove equivalent facts:

```text
canonical checkout branch remains canonical branch
canonical working tree remains clean
canonical HEAD/worktree is not switched for materialization
execution workspace != canonical checkout
caller cannot select source checkout path
```

A provider-owned bounded fetch/object acquisition may update provider/source Git object metadata only when admitted by R8; it must not switch/reset/checkout/merge the canonical working tree or create a worktree from it.

Direct `git worktree add` remains forbidden for this bridge.

### R14 — Retry, partial failure and idempotent read-back

Same Attempt retry rules:

- absent target + current exact scope may materialize once;
- an existing workspace with a matching durable materialization receipt, repository identity, exact source commit and current scope/placement binding may converge through read-back;
- a non-empty/unbound/mismatched workspace fails closed;
- partial materialization cleanup may remove only transaction-owned/attempt-owned partial output;
- failure to prove cleanup/residue state prevents a `Materialized` claim;
- verified successful materialization is not replayed merely because the caller retries.

### R15 — No fallback escalation

Placement, source, scope, audit, sandbox, materialization or handoff failure must never fall back to:

```text
generic script_run
generic exec/shell
generic sentinel_git clone with caller dest
direct git worktree add
generic filesystem edit/copy
operator_unrestricted
file_ops / command allowlist expansion
provider switch
caller-selected ACL/SID/root
canonical checkout mutation
production Hub modification
blind PR-013 S03 replay
```

### R16 — PR-013 convergence without dependency

PR-013 remains the owner of general repository transaction/materialization/publication and retained multi-operation execution lifecycle.

PR-014 R2 is allowed to own only the minimum source-acquisition/capsule/materializer behavior necessary for `development.execution_workspace_materialize`.

If PR-013 later lands equivalent canonical primitives on `main`, a later compatibility/refactor may replace PR-014's seed backend with those canonical primitives. That convergence is not a prerequisite for PR-014 R2 completion and does not authorize importing unmerged PR-013 code.

## Active overlap and ownership boundaries

### PR-013 — Repository Materialization & Scoped Publication Bridge

PR #13 (`PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1`) remains related but is **not a completion dependency** for Requirement R2.

Ownership is frozen as:

```text
PR-014 R2 owns:
- DevForge Host placement alignment and Placement Receipt consumption;
- bootstrap-safe exact-commit source acquisition/capsule sufficient only for workspace materialization;
- bounded AppContainer/Job materialize_workspace projection;
- materialization read-back receipt;
- safe Development Host handoff.

PR-013 owns:
- general repository_transaction_v1 lifecycle;
- general retained multi-operation repository execution lifecycle;
- operation closure across repeated scoped operations;
- scoped publication/checkpoint/push and publication CAS;
- generalized repository source/materialization backend after it becomes canonical.
```

Rules:

- PR-014 must not copy/import unmerged PR-013 code.
- PR-014 must not execute or replay PR-013 S03.
- PR-013 being open, pending, paused, unaccepted or unmerged must not block PR-014 R2's bootstrap seed.
- If PR-013 becomes canonical during PR-014 implementation, perform impact reconciliation and reuse only already-merged canonical primitives where compatible; do not silently widen PR-014 scope.

### PR-012 / PR-010

PR-012 explicit `execution_profile=scoped_mutation` and PR-010 canonical repository firewall are merged canonical baselines and must not regress.

### DevForge repository boundary

DevForge v2.40.0 already defines Host workspace layout, `development.execution_workspace_materialize`, scope-before-materialization, audit-before-materialization, receipt and no-bypass semantics.

This SentinelX Task must consume those contracts. It does not authorize cross-repository mutation of `bewaterhere-coder/DevForge`. If Acceptance discovers a real consumer-contract defect rather than a provider defect, that is a separate explicit DevForge change.

## Acceptance criteria

- **AC1:** With Host canonical source binding `<C>` and independent Host execution binding `execution_root=<E>`, repository `<owner>/<repo>`, scope/task `<S>` and Attempt `<A>`, provider independently derives exactly `<E>/<owner>/<repo>/<S>/<A>`, proves `<E>`/workspace are outside all protected/canonical roots, and binds scope authority to that exact future workspace while `<C>` remains protected and source-only.
- **AC2:** `local_api.describe devforge_runtime` exposes a bounded `materialize_workspace` action with no caller-controlled writable destination/root/SID/ACL/credential/Git-argv/operation-class fields.
- **AC3:** Caller path injection, DevForge/provider placement mismatch, path escape, malformed identity and caller-selected source checkout all fail before material workspace creation.
- **AC4:** Wrong repository/ref/commit, unavailable provider source credential, stale/expired/foreign scope, scope binding drift and source-capsule mismatch fail closed with no successful receipt and no generic fallback.
- **AC5:** Provider derives and verifies the canonical source role from Host canonical-repository inventory independently of execution placement; source worktree remains under its protected canonical root, canonical branch + clean, and is never used as the mutation workspace.
- **AC6:** Provider-owned exact-commit acquisition creates/read-backs immutable source evidence without exposing credentials or accepting caller remote/path authority.
- **AC7:** Durable audit START precedes the first material workspace write; audit-start failure leaves no successful workspace materialization state.
- **AC8:** A valid request causes the AppContainer/Job materializer to create the exact admitted Git repository checkout in the exact Host-derived execution workspace, and read-back proves repository identity + logical ref + exact commit + isolation.
- **AC9:** Materialization receipt contains provider-owned scope/placement/source-capsule/audit/containment/read-back evidence consumable by DevForge `development.execution_workspace_materialize`.
- **AC10:** Temporary AppContainer/materializer authority is closed and Host-owned handoff access is read back as usable by the registered Development Host without caller SID/ACL/root selection or ancestor/root permission widening.
- **AC11:** Retry after verified materialization converges by durable read-back and does not recreate/overwrite the checkout; mismatched pre-existing content fails closed.
- **AC12:** PR-014 bootstrap seed completes and verifies while PR-013 remains unmerged/unaccepted/incomplete; no PR-013 S03 replay and no unmerged PR-013 code import is used.
- **AC13:** Canonical firewall, mutation-scope, audit-lineage, AppContainer/Job, explicit-execution-profile and completed PR-014 S01 regressions remain passing.
- **AC14:** Windows physical integration proves placement → source acquisition/capsule → scope → audit START → AppContainer/Job materialization → exact Git HEAD readback → temporary-authority closure → Development Host handoff on a benign repository fixture.
- **AC15:** General retained multi-operation `execute_scoped` transaction lifecycle, operation closure and publication are not required for PR-014 R2 completion and remain PR-013 ownership.
- **AC16:** No independent Codex requirement, no new Development Gate, no production Hub modification, no Host policy/allowlist widening and no generic Git/shell/file fallback are introduced.
- **AC17:** Existing MutationScope durable records containing compatible additive schema fields (including `runtime_read_authority_roots`) are read/migrated/preserved without deletion or authority widening; unsupported authority-bearing additive fields fail closed as schema incompatibility rather than being discarded or misclassified as corrupt state.

## Scope

### In scope

- preserve/read-back completed PR-014 S01 placement/root/scope/sandbox evidence without replay;
- independent Host-owned canonical source-role resolution from canonical repository inventory;
- dedicated Host-owned DevForge execution placement binding outside protected/canonical roots;
- MutationScope additive durable-schema forward-compatible read/migration;
- bounded provider exact-ref/exact-commit object acquisition;
- provider-private immutable source capsule/manifest and digest evidence;
- narrow trusted repository materializer under existing AppContainer/Job containment;
- path-free `devforge_runtime.materialize_workspace` schema/routing;
- materialization receipt compatible with `development.execution_workspace_materialize`;
- temporary materializer/AppContainer authority closure and Host-owned Development Host handoff read-back;
- idempotent retry/residue handling;
- Windows physical verification and security regressions;
- impact reconciliation if PR-013 becomes canonical while this Task is in flight.

### Out of scope

- general `repository_transaction_v1` lifecycle;
- retained multi-operation `execute_scoped` transaction/operation closure;
- repository publication, push/checkpoint orchestration or publication CAS;
- generic source broker API for arbitrary callers;
- exposing or mutating Git credentials, SSH agents, tokens or credential-helper configuration;
- importing/copying unmerged PR-013 code;
- replaying PR-013 S03;
- caller-selected Host path/root/SID/ACL/operation class;
- direct `git worktree add`, generic shell/script/Git/filesystem fallback;
- canonical checkout branch switching/reset/merge;
- production Hub modification;
- Host policy/allowlist/permission widening;
- new Development Gate or cross-repository DevForge mutation.

## Requirement challenge / disconfirmation

### Revision 3 challenge result

Acceptance R2 physically activated exact candidate `45dc99d15a23c499b4c1500fab60ed5e76475aeb` and proved two material facts:

1. deriving execution placement under `D:\coco\workspaces` is structurally incompatible with the independent broad `D:\coco` protected-root invariant;
2. the exact candidate cannot read a newer durable MutationScope record containing additive field `runtime_read_authority_roots`.

The Human decision accepts the recommended architecture:

```text
protected canonical source binding
  !=
dedicated Host-owned execution placement binding
```

and explicitly preserves `D:\coco` protection. The alternative of protected-root narrowing/carve-out is rejected.


### Revision 2 challenge result

The prior R1/R2-plan dependency shape was challenged against the live self-host execution block discovered by PR-020. The rejected assumption is:

```text
PR-014 materialize_workspace may wait for PR-013 canonical completion
```

That assumption produces a circular bootstrap dependency and is therefore removed.

Alternatives rejected:

1. **Blindly retry PR-013 S03** — forbidden because no verified terminal outcome exists for the prior uncertain attempt.
2. **Use generic Git worktree/clone/shell** — violates current DevForge execution-workspace materialization contract and canonical-source mutation boundaries.
3. **Use canonical checkout as CodeBuddy workspace** — violates canonical `main + clean` source role.
4. **Copy PR-013 unmerged materializer** — violates ownership/transport authority and creates hidden forked semantics.
5. **Wait for PR-013 before PR-014** — preserves the cycle and cannot unblock PR-020.

Selected R2 direction is the minimum independent seed: exact-commit provider source capsule + contained materializer + Host-owned handoff, with all generalized transaction/publication semantics left in PR-013.

No unresolved material product decision remains for Requirement R2.



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