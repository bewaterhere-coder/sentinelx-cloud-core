# PR-014 — SentinelX DevForge Execution Workspace Materialization Bridge V1 — Acceptance R2

## Decision

**DecisionRequired**

This Acceptance round proves exact-candidate activation and live projection, but the mandatory physical materialization gate exposes a material architecture contradiction between Requirement R2 placement semantics and the current Host protection policy.

Acceptance MUST NOT guess or silently weaken either side.

## Canonical Lineage

~~~yaml
task_id: PR-014-devforge-execution-workspace-materialization-bridge-v1
requirement_revision: 2
plan_revision: 6
stage: acceptance
product_candidate: 45dc99d15a23c499b4c1500fab60ed5e76475aeb
canonical_pr: 14
canonical_branch: task/devforge-execution-workspace-materialization-bridge-v1
~~~

## Exact Candidate Activation — PASS

Live Host readback:

~~~yaml
host_id: host_7f0e709ded71ab24
hostname: Cherie_li
agent_version: 0.24.1.dev260+g45dc99d15
candidate_commit_match: true
devforge_runtime_contract_revision: 2
materialize_workspace_present: true
~~~

The prior Acceptance R1 activation blocker is closed.

## Canonical Source Role — PASS

Live canonical checkout:

~~~yaml
path: D:\coco\repos\bewaterhere-coder\sentinelx-cloud-core
branch: main
head: cd42e371f180
ahead: 0
behind: 0
dirty: false
~~~

PR #14 remote identity at the physical call:

~~~yaml
branch: task/devforge-execution-workspace-materialization-bridge-v1
head: 09026c1a90659f05d071a7f2d1588cf539f20304
~~~

## Physical Materialization Call — FAIL CLOSED

Acceptance invoked the path-free structured action:

~~~text
devforge_runtime.materialize_workspace
~~~

with only semantic repository/lineage/source binding fields and no caller-selected destination/workspace path.

Result:

~~~text
internal_error:
DevForge execution placement overlaps a protected/canonical root
~~~

No successful materialization receipt was emitted.

## Root Cause

Requirement R2 freezes the Host DevForge placement derivation as:

~~~text
locations.devforge_workspace_root = D:\coco
execution_root = D:\coco\workspaces
~~~

Current live Host policy independently protects:

~~~text
mutation_execution.protected_roots:
  - D:\coco
  - C:\Users\liqiu
~~~

PR-014 S01 placement implementation correctly fails when the execution root overlaps any protected root.

Therefore:

~~~text
execution_root D:\coco\workspaces
is descendant of protected root D:\coco
→ overlap is structurally guaranteed
→ materialization cannot be admitted
~~~

This is not an activation issue, transient operator issue, or missing permission. It is a contradiction between the frozen R2 placement topology and the live protected-root security topology.

## Why Acceptance Cannot Repair This Locally

The following apparent workarounds are forbidden by Requirement/Plan security invariants:

- remove or narrow `D:\coco` from protected roots;
- carve an execution-workspace exception inside the broad protected root;
- add a broader mutation allowlist;
- fall back to `mutation_execution.workspace_root`;
- caller-select another workspace path;
- use generic git/shell/script_run;
- materialize inside the canonical checkout.

Any of these would change protected authority or violate R2's single Host DevForge placement truth.

A conforming resolution requires a material architecture/Requirement decision about separating the canonical source-root role from the execution-workspace root role.

## Secondary Live Compatibility Finding

The exact candidate's capability self-check also reports:

~~~text
HostMutationScopeCorrupt:
MutationScopeRecord.__init__() got an unexpected keyword argument
'runtime_read_authority_roots'
~~~

This proves the activated exact candidate cannot read at least one existing Host mutation-scope record written by a newer runtime schema.

This is a secondary compatibility issue, not the cause of the first materialization failure (the placement overlap fails earlier), but it must be repaired before final Acceptance because PR-014 requires reuse of the existing durable MutationScopeStore.

A conforming repair should use forward-compatible state read/migration semantics; Acceptance must not delete durable state merely to make the candidate pass.

## Acceptance Matrix

~~~yaml
exact_candidate_activation: PASS
local_api_projection: PASS
path_free_request_shape: PASS
canonical_source_main_clean: PASS
host_owned_placement_derivation: FAIL_ARCHITECTURE_CONFLICT
protected_root_separation: FAIL_ARCHITECTURE_CONFLICT
materialization_scope: NOT_REACHED
audit_start: NOT_REACHED
appcontainer_job_materializer: NOT_REACHED
git_readback: NOT_REACHED
handoff_probe: NOT_REACHED
same_attempt_no_replay: NOT_REACHED
mutation_scope_state_compatibility: FAIL_SECONDARY
hosted_ci: NotEvaluated
acceptance_result: DecisionRequired
acceptance_approved: false
~~~

## Required Material Decision

A new Requirement/Plan revision must choose a topology that preserves both:

1. canonical/source checkout remains protected and source-only;
2. DevForge execution workspace is Host-owned but physically outside the broad canonical/protected root.

The recommended architecture is to separate **source binding** from **execution placement binding**:

~~~text
source role:
  canonical repository inventory / canonical source root
  → D:\coco\repos\...

execution placement:
  dedicated Host-owned DevForge execution root
  → e.g. D:\SentinelX\devforge-workspaces\...
~~~

The execution root must not be caller-controlled and must remain outside protected/canonical roots.

Do **not** solve this by weakening `D:\coco` protection.

The same revision should require forward-compatible MutationScope state read/migration for additive durable-schema fields.

## Safety

No Host policy was changed.
No protected root was narrowed.
No caller path authority was granted.
No generic shell/git/script_run fallback was used.
No product code was changed by Acceptance.
No PR-013 S03 replay occurred.
No CI was invoked.

## Result

~~~yaml
result: DecisionRequired
stage_after: acceptance
acceptance_approved: false
completion_verified: false
product_replay_required: false
material_architecture_decision_required: true
~~~
