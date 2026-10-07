# PR-014 — SentinelX DevForge Execution Workspace Materialization Bridge V1 — Plan Review R5

## Review State

~~~yaml
task_id: PR-014-devforge-execution-workspace-materialization-bridge-v1
review_target: plan
requirement_revision: 2
requirement_blob_sha: 921df3474f35f4dd3ea3c71efd7f1f7912fcd0b2
plan_revision: 5
plan_blob_sha: ff8581ec026a0d123ae89d9595271397429145c0
reviewed_task_head: 09706da134a5a3075dee76c69304debaf89ec09a
result: Approved
runtime:
  devforge_revision: 050d9c9559a173a3e0b37fcd2a9db702b6b5a7e6
  devforge_release: v2.98.0
  review_contract: "1.3"
  slicing_contract: "1.1"
  bootstrap_override_contract: "1.1"
repository_reality:
  canonical_main: 1028030b33f0ea792a884491a431fffe566f6aa5
  canonical_pr: 14
  canonical_branch: task/devforge-execution-workspace-materialization-bridge-v1
next_gate: implementation
next_expected_actor: implementer
~~~

## Decision

**Approved.**

Plan R5 removes the circular bootstrap dependency without changing Requirement R2 semantics or weakening the runtime materialization security boundary.

The approved execution-entry chain is:

~~~text
Approved Plan R5
→ exact R5 Slice Set
→ implementation
→ explicit #开发引导执行 PR-014-devforge-execution-workspace-materialization-bridge-v1 direct:codebuddy
→ verified Task-scoped implementation_bootstrap override
→ later #开发执行
→ exact S02 only
~~~

The bootstrap target is a direct Development Adapter, so the Harness-specific `incremental_execution.slice_v1` consumer requirement does not apply. DevForge still owns the canonical Slice Set and one-execute/one-Slice semantics.

## Direct CodeBuddy Target Evidence

The `direct:codebuddy` target is not a newly invented target class.

Canonical precedent exists in merged SentinelX PR-015 evidence:

~~~text
docs/reviews/PR-015-direct-codex-development-host-invocation-bridge-v1-bootstrap-execution-override-r1-receipt.yaml
~~~

That receipt proves:

~~~yaml
source_command: "#开发引导执行 PR-015-direct-codex-development-host-invocation-bridge-v1 direct:codebuddy"
status: Admitted
target:
  provider: direct
  adapter: codebuddy
project_binding:
  provider: direct
  adapter: codex
  mutated: false
~~~

The current bootstrap command must still freshly verify target registration and availability. Historical precedent proves target semantics/registration model, not current liveness.

## Self-Host Relation

The self-host relation remains exact:

~~~text
canonical provider = direct/codex
normal Host-local implementation path needs development.execution_workspace_materialize
PR-014 implements development.execution_workspace_materialize
~~~

Using a different direct adapter for this exact bootstrap Task is self-host recovery, not provider preference.

## Repository-Projection Boundary

R5 correctly separates execution authority from persistence mechanics.

Authority:

~~~text
active Task-scoped bootstrap override
~~~

Persistence:

~~~text
repository.read / structured repository.write
→ exact repository
→ exact PR #14
→ exact task branch
→ expected-head compare/readback
~~~

Repository API availability alone grants no implementation authority.

S02 seed execution must not create a Host-local implementation workspace. It may not use generic Git, shell, script_run or generic Host filesystem mutation.

## Slice / Direct Adapter Composition

The canonical slicing contract requires one explicit `#开发执行` to complete at most one Slice.

The Harness-specific consumer capability:

~~~text
incremental_execution.slice_v1
~~~

is required only when the resolved provider is Harness.

For R5, DevForge/orchestration keeps exact S02 Slice identity and scopes the direct CodeBuddy handoff to that single Slice. The direct adapter must return canonical implementation evidence for that exact Task/Plan/Slice/transport; it does not need the Harness execution-contract extension.

No unsliced whole-Plan fallback is authorized.

## Implementation Verification Feasibility

Repository-only seed persistence remains technically verifiable.

Current PR #14 head already has repository-hosted verification surfaces, including:

- `ci`;
- `macos-agent`;
- existing firewall/security workflows.

At reviewed head, `ci` and `macos-agent` have successful exact-head runs.

After S02 writes, completion requires fresh verification bound to the resulting exact PR head. Old successful runs cannot be reused as proof for the new code.

If required repository-hosted checks are unavailable, failed, stale or not bound to the exact S02 head, S02 cannot complete.

## Runtime Firewall Boundary

No change to `src/sentinelx_core/operation_registry.py` is required by design.

The existing registry already queries builtin providers through:

~~~text
provider.repository_effect(action)
~~~

R5 S02 may implement provider-owned effect metadata in `handlers/devforge_runtime.py` for the new `materialize_workspace` action and test it through the existing operation-registry/firewall test surfaces.

The new runtime action must remain fail-closed until its repository/process effect and firewall coverage are proven.

## Acceptance Physical Verification

Moving Windows exact-candidate proof from an implementation S03 Slice into Acceptance is valid.

Acceptance Contract v1.5 owns Requirement satisfaction and behavioral/real evidence after implementation completion.

Existing SentinelX acceptance precedent demonstrates the intended fail-closed semantics:

- PR-012 Acceptance blocked when exact candidate could not be activated;
- PR-015 Acceptance repeatedly blocked when exact live Agent candidate was not active;
- PR-015 Acceptance later approved only after exact candidate activation and live readback were proven.

Therefore Acceptance may not invent install authority. If exact-candidate activation requires a separately protected/operator workflow and that authority is unavailable, Acceptance remains blocked. It must not substitute source/CI evidence for AC8, AC10 or AC14.

## Dependency Closure

R5 S02 implementation admission does not require completion of:

~~~text
PR-013
PR-020
PR-229
Harness incremental_execution.slice_v1
development.execution_workspace_materialize itself
~~~

PR-013 remains overlap/ownership evidence only and S03 replay remains forbidden.

PR-020 and PR-229 may evolve independently but are not R5 bootstrap gates.

## S01 Preservation

Historical S01 completion remains reusable because Requirement R2 preserves the same placement, Host-derived root, mutation-scope and sandbox foundation.

Evidence:

~~~text
docs/checkpoints/PR-014-devforge-execution-workspace-materialization-bridge-v1-s01-completion-20261005.yaml
~~~

S01 is completed/reused and must not be replayed.

Before S02 mutation, execution must re-read current canonical main and compare relevant S01 seams. Material conflict stops before mutation.

## Exact R5 Slice Compilation

Compile:

~~~text
S01 — completed / preserved
  ↓
S02 — pending / bootstrap-safe minimal materialize_workspace seed
~~~

No S03 implementation Slice exists.

S02 is the only remaining implementation Slice.

## Exact S02 Product Write Allowlist

The direct Development Host may mutate only these product/test paths for S02:

~~~text
src/sentinelx_core/devforge_workspace_source.py
src/sentinelx_core/devforge_workspace_materializer.py
src/sentinelx_core/devforge_workspace_materialization.py
src/sentinelx_core/handlers/devforge_runtime.py
src/sentinelx_core/handlers/__init__.py
src/sentinelx_core/user_git.py
src/sentinelx_core/windows_mutation_sandbox.py

tests/test_devforge_workspace_source.py
tests/test_devforge_workspace_materializer.py
tests/test_devforge_workspace_materialization.py
tests/test_devforge_runtime_local_api.py
tests/test_devforge_workspace_placement.py
tests/test_user_scoped_git.py
tests/test_windows_mutation_sandbox.py
tests/test_operation_effect_registry.py
tests/test_canonical_repository_firewall.py
tests/test_canonical_repository_firewall_readiness.py
~~~

New files in this list may be created if required.

Any additional production/test path is outside current S02 execution authority and requires an upstream Plan/Slice decision before mutation.

Task-owned checkpoint/review/receipt artifacts remain orchestration-owned and are not part of CodeBuddy product write authority.

## Explicitly Forbidden S02 Mutation

~~~text
.github/workflows/**
canonical main
replacement branch / PR
generic git / clone / worktree
shell / exec / script_run
generic Host filesystem mutation
caller-selected Host path/root
Host policy / allowlist
credentials
permissions
write-scope expansion
project binding
Requirement / Plan / Gate
PR-013 S03
unmerged PR-013 code
~~~

## Review Matrix

~~~yaml
solution_direction: pass
requirement_r2_semantics_preserved: pass
scope_control: pass
technical_feasibility: pass
dependency_cycle_removed: pass
self_host_relation: pass
direct_codebuddy_target_semantics: pass
direct_codebuddy_current_availability: deferred_to_bootstrap_admission
repository_write_is_persistence_only: pass
repository_only_seed_no_host_workspace: pass
one_execute_one_slice: pass
harness_slice_dependency_removed: pass
pr229_dependency_removed: pass
pr020_dependency_removed: pass
pr013_completion_dependency_removed: pass
s01_preservation_without_replay: pass
runtime_host_owned_placement: pass
mutation_scope_preserved: pass
pre_execution_audit_preserved: pass
appcontainer_job_sandbox_preserved: pass
canonical_firewall_preserved: pass
caller_path_authority_forbidden: pass
permission_credential_write_scope_expansion_forbidden: pass
exact_pr_transport_lock: pass
exact_head_readback: pass
existing_ci_verification_surface: pass
windows_physical_proof_owned_by_acceptance: pass
source_only_acceptance_forbidden: pass
acceptance_activation_unavailable_behavior: blocked_not_approved
ux_contract: NotApplicable
visual_fidelity: NotApplicable
blocking_findings: []
~~~

## Gate Result

~~~yaml
decision: Approved
plan_approved: true_after_exact_slice_set_readback
implementation_authorized: true_after_exact_slice_set_readback
next_stage: implementation
current_slice_after_transition: S02
bootstrap_required_before_current_slice: true
bootstrap_target: direct:codebuddy
canonical_next_action: "#开发引导执行 PR-014-devforge-execution-workspace-materialization-bridge-v1 direct:codebuddy"
~~~

No product implementation, CodeBuddy invocation, Host mutation, candidate activation, PR-013 replay, project-binding change, canonical-main mutation, release, deployment or production action is performed by this review.
