# PR-010 — SentinelX Provider Canonical Repository Mutation Firewall V1

## State — Requirement Revision 2

```yaml
project_id: sentinelx-cloud-core
task_id: PR-010-canonical-repository-mutation-firewall-v1
title: SentinelX Provider Canonical Repository Mutation Firewall V1
requirement_revision: 2
development:
  stage: accepted
  gates:
    requirement_ready: true
    plan_approved: true
    acceptance_approved: true
    completion_verified: false
  plan_revision: 4
  implementation_authorized: true
  finalization:
    ready_for_merge: false
    canonical_state_verified: false
    plan_execution_state_verified: false
    evidence_verified: true
    transport_preconditions_verified: false
    blocker: CompletionIntegrationHostOffline
  next_expected_actor: completion_finalizer
transport:
  type: github-pr
  pr_number: 10
  branch: task/canonical-repository-mutation-firewall-v1
  base_branch: main
artifacts:
  requirement_change_impact: docs/reviews/PR-010-canonical-repository-mutation-firewall-v1-requirement-r2-invalidation.md
  plan: docs/plans/PR-010-canonical-repository-mutation-firewall-v1-plan.md
  plan_review: docs/reviews/PR-010-canonical-repository-mutation-firewall-v1-plan-review-r4.md
  execution_slice_set: docs/execution/PR-010-canonical-repository-mutation-firewall-v1-slices.yaml
  acceptance: docs/reviews/PR-010-canonical-repository-mutation-firewall-v1-acceptance-r1.md
  acceptance_checkpoint: docs/checkpoints/PR-010-canonical-repository-mutation-firewall-v1-acceptance-r1-approved-20261003.yaml
  completion_finalization_checkpoint: docs/checkpoints/PR-010-canonical-repository-mutation-firewall-v1-completion-finalization-blocked-20261003.yaml
related_tasks:
  overlap_dependencies:
    - PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1
    - PR-008-provider-execution-profile-tool-surface-alignment-v1
  independent_non_blocking:
    - PR-009-mcp-development-execution-projection-dynamic-tool-contract-v1
external_contract:
  repository: bewaterhere-coder/DevForge
  ref: 9e0ec1aae06690840d8946d39460e7cb28ef36d1
  path: system/canonical-repository-host-mutation-firewall-contract.md
  required_capability: canonical_repository_mutation_firewall_v1
```

## Requirement Revision 2 Change

Production `mcp.sentinelx.app` is an **immutable third-party closed-source transport boundary** for this Task.

PR-010 owns only surfaces implemented and controlled by `sentinelx-cloud-core` / the SentinelX Agent. The Task MUST NOT require, imply, or claim any Hub source, schema, deployment, routing, tool-generation, or capability-projection change.

Missing Hub exposure of `execution_profile`, a dynamic tool, a capability field, or any other MCP projection is an **external integration limitation**, not an implementation, verification, Acceptance, or completion blocker for PR-010 when equivalent Core-owned verification is available.

The security property must hold at the Agent/Core mutation boundary regardless of which existing transport delivered the request.

Required verification authority is therefore:

```text
sentinelx-cloud-core unit evidence
+ SentinelX Core integration evidence
+ Core protocol / hello / capability readback where applicable
+ Windows physical-mutation regression evidence where required
```

The following is explicitly **not** required evidence:

```text
Hub source/schema mutation
Hub deployment
Hub-native dynamic tool generation
Hub-native execution_profile projection
Hub UI/model-facing capability rendering
```

Existing Hub transport may carry requests and responses unchanged, but it owns no canonical-repository protection authority and is not a completion dependency.

## Problem

SentinelX already has strong but incomplete security layers:

1. `file_ops` canonicalizes paths and requires explicit `rw` access for structured filesystem/Git mutation;
2. `mutation_execution` owns scoped-mutation placement, `protected_roots`, sandbox readiness and audit lineage.

Those layers do **not** by themselves prove the DevForge provider contract that a canonical source checkout is physically non-mutable through every Agent/Core mutation surface.

Current failure class:

- broad `file_ops rw` can include a canonical checkout;
- structured edits and Git mutation can otherwise reach that checkout;
- generic `exec` / script processes can mutate indirectly through child processes;
- higher-level workflow correctness does not protect against a lower-level Host mutation primitive;
- transport/projection details must not become the security boundary.

## Goal

Implement a provider-owned, provider-wide canonical repository mutation firewall in `sentinelx-cloud-core` that satisfies `canonical_repository_mutation_firewall_v1` without hard-coding DevForge, a specific host, a repository path, a GitHub owner, or a transport implementation.

For every SentinelX Agent/Core operation capable of materially changing a repository checkout, the provider must either:

- prove the target does not intersect a Host-authoritative canonical repository root and continue through the operation's existing authorization boundary; or
- reject before material mutation with stable fail-closed evidence.

Capability readiness is true only when complete Core mutation-surface coverage is proven.

## Ownership Boundary

SentinelX Core owns:

- Host-authoritative canonical repository inventory and target classification;
- provider-wide mutation admission before handler/process mutation;
- physical process containment or fail-closed process admission;
- capability readiness computation;
- Core protocol/hello capability output through existing transport structures;
- regression tests and diagnostics proving no Agent/Core mutator bypasses the boundary.

DevForge owns:

- the consumer semantics and expected capability/error contract;
- no SentinelX implementation surface.

The third-party Hub owns transport behavior only. It MUST NOT mint, remove, weaken, or be required to prove canonical repository protection authority.

## Required Behavior

### R1 — Host-owned canonical repository inventory

Introduce or derive an explicit Host-authoritative inventory distinct from generic protected roots and ordinary writable project/workspace roots.

Each inventory entry binds at least:

```text
canonical root
repository identity (vcs + authority + path)
canonical branch / source-role metadata when applicable
inventory provenance / readiness evidence
```

Rules:

- caller payload path, cwd, environment variables, branch name, chat/model assertions, and transport fields are evidence only;
- `file_ops rw` never removes canonical protection;
- `protected_roots` MUST NOT be reinterpreted as canonical repository identity when doing so would also block valid execution workspaces;
- path classification canonicalizes traversal/symlinks before intersection testing;
- inability to classify safely is fail-closed for material mutation.

### R2 — Reuse the existing repository identity primitive

Canonical inventory MUST compose the existing `sentinelx_core.mutation_placement.RepositoryIdentity` semantics, or one explicitly shared primitive extracted from it, rather than maintain a second incompatible repository identity model.

The existing S01 implementation in `policy._canonical_repository_identity` is not accepted as final while it diverges from `RepositoryIdentity`, including authority/port behavior. Repository identity normalization must have one provider semantic source.

### R3 — Stable provider-level admission API

Create one reusable firewall/classifier seam consumed by every relevant mutation handler rather than duplicating ad-hoc checks.

Required dispositions are equivalent to:

```text
AllowedNonCanonicalTarget
CanonicalRepositoryMutationBlocked
HostCanonicalMutationFirewallIndeterminate
```

Canonical block or indeterminate failure must occur before the first material mutation or child process capable of mutation.

### R4 — Structured file/edit/upload coverage

Provider enforcement must cover all structured filesystem write paths, including at least:

```text
edit
edit_upload_complete
move
copy destination / overwrite paths
delete
chmod
chown
upload finalization paths that materialize host files
future equivalent structured write operations
```

For move/copy, every material endpoint must be classified with correct read/write semantics. Blocking an edit/delete must not create `.bak.*`, staging, or partial-write side effects in or adjacent to a canonical repository.

### R5 — Structured Git coverage

All structured Git mutation paths must consume the firewall, including `apply_patch` and any future checkout/ref/worktree mutation added to the structured Git operation.

Read-only Git operations remain available. A generic Git operation cannot self-identify as `canonical_sync` to bypass the firewall.

### R6 — Core-owned process fail-closed coverage

`exec`, legacy/unprofiled `script_run`, profiled/scoped script execution, background descendants, timeout paths, and nonzero paths are mutation-capable and must be accounted for by Core.

V1 MUST NOT treat shell/script/path-string parsing as physical security proof.

If SentinelX Core cannot guarantee that an admitted process tree cannot mutate a canonical checkout, then while firewall-ready mode is enabled it MUST either:

- route the operation through an existing physically constrained scoped execution path whose boundary is proven; or
- block that process class fail-closed; or
- keep firewall readiness false.

This decision is Core-owned. It MUST NOT depend on the Hub exposing an `execution_profile` argument or a different MCP tool schema.

No `operator_unrestricted`, legacy unrestricted fallback, command allowlist expansion, or caller-minted authority may bypass canonical protection while the firewall capability is advertised.

### R7 — Authoritative operation-effect registration

Coverage accounting must derive from the same authoritative Core operation registration used for dispatch / effective operation exposure, not from a parallel hand-maintained firewall list.

Every effective model-facing operation must have explicit repository-effect semantics equivalent to:

```text
read_only
structured_mutation
process_mutation
non_repository_mutation
unknown
```

Rules:

- missing/unknown effect metadata makes firewall readiness false;
- required-but-unproven firewall coverage makes readiness false;
- internal-only transport operations are explicitly distinguishable from model-facing operations;
- disabled operations are removed before final effective-surface readiness computation;
- mixed operations such as structured Git classify mutation selectors explicitly.

### R8 — Core capability readiness + existing transport output

`canonical_repository_mutation_firewall_v1` may be advertised by SentinelX Core only when:

- canonical inventory is valid;
- every effective Core mutator is classified;
- every required structured mutation path is covered;
- every process-producing path has a proven physical disposition;
- no unrestricted bypass is active.

The positive/negative readiness decision must be verifiable through Core-owned unit/integration/protocol evidence.

Existing hello/capability/protocol structures may carry this readiness through the existing transport. Hub-native rendering or projection of the field is not required for PR-010 Acceptance.

### R9 — Canonical source exceptions remain dedicated

Generic file/Git/shell/script tools receive no canonical mutation exception.

If SentinelX later supports structured canonical source mechanics, they must be dedicated operations with independent exact repository/branch verification. V1 does not implement a generic `canonical_sync` escape hatch.

### R10 — Execution workspace remains mutable under existing authority

The firewall must not turn an admitted execution workspace into a canonical root merely because both correspond to the same repository identity.

Passing the firewall is exclusion evidence only. Existing scope, audit, sandbox, `file_ops`, Git, execution-profile and transport authorization still apply.

### R11 — Incident regression and immutable-Hub semantics

Freeze at minimum:

```text
canonical main + generic file edit             -> BLOCK
canonical main + backup-producing edit/delete -> BLOCK with no backup side effect
canonical main + structured git apply_patch    -> BLOCK
canonical main + generic process write/switch  -> BLOCK under firewall-ready mode
canonical main + script child/background write -> BLOCK
unknown/indeterminate target classification    -> FAIL CLOSED
execution workspace + valid scoped mutation    -> PASS firewall, then existing authorities
read/list/search/status/diff on canonical      -> PASS
broad parent file_ops rw                       -> DOES NOT OVERRIDE
caller claims canonical_sync on generic op     -> BLOCK
Hub lacks execution_profile projection         -> EXTERNAL LIMITATION, NOT PR-010 BLOCKER
Hub lacks capability-field rendering           -> EXTERNAL LIMITATION, NOT PR-010 BLOCKER
```

## Compatibility / Non-Goals

- Do not modify or require modifications to `mcp.sentinelx.app` Hub source, schema, deployment or tool projection.
- Do not hard-code `D:\\coco`, DevForge, `Cherie_li`, a GitHub owner, or a particular canonical checkout.
- Do not replace `file_ops`; the firewall is an additional denial boundary.
- Do not create a second mutation-scope store, audit journal, sandbox executor or repository identity model when an existing SentinelX primitive can be composed.
- Do not broaden `protected_roots` so valid execution workspaces become unusable.
- Do not weaken `host_mutation_sandbox_v1`, `pre_execution_audit_lineage_v1`, PR-007 scope admission or PR-008 profiled execution semantics.
- Do not auto-expand filesystem permissions or command allowlists.
- Do not implement generic `canonical_sync` in V1.
- Linux/macOS may remain capability-unavailable if equivalent physical enforcement is not proven in V1; unsupported platforms fail closed rather than advertise partial coverage.
- PR-009 is related independent work only and is not a PR-010 implementation, verification, Acceptance, or completion dependency.

## Active-Branch Compatibility Constraint

PR-007 and PR-008 modify mutation-scope / scoped-script / capability-advertisement seams. Before a Slice touches an overlapping file (`client.py`, `handlers/basic.py`, `handlers/scoped_script.py`, `mutation_scope.py`, registry/protocol/capability code, or equivalent), it must re-read the exact latest dependency head, changed-file set, relevant contract, and stage/disposition.

A moving branch is evidence, not implementation authority. Material semantic conflict stops before product mutation.

PR-009 is excluded from this overlap admission gate unless a future exact changed-file readback proves a direct code conflict; its Hub projection objective is never a semantic completion dependency.

## Retained S01 Implementation and Current Blocker

Requirement Revision 2 preserves the already-landed S01 source changes as implementation evidence. They are not rolled back or replayed.

Retained implementation surfaces:

```text
src/sentinelx_core/policy.py
src/sentinelx_core/canonical_repository_firewall.py
tests/test_canonical_repository_firewall.py
```

The previous Hub/tool-projection dynamic verification failure is superseded as a blocker.

The current true S01 blocker is:

```text
existing primitive: sentinelx_core.mutation_placement.RepositoryIdentity
parallel S01 normalizer: sentinelx_core.policy._canonical_repository_identity
required resolution: reuse/share one repository identity semantic and revalidate S01
```

S01 remains incomplete until that consistency issue is resolved and Core-owned verification passes.

## Requirement Readiness Evidence

```yaml
depth: deep
behavior_examples:
  - id: canonical-file-write
    sequence: "operator config exposes a broad parent as file_ops rw -> edit targets a canonical checkout descendant -> Core firewall blocks before edit/backup"
  - id: canonical-process-write
    sequence: "a process-producing Core operation attempts direct or child-process canonical mutation -> Core physical disposition blocks it or firewall readiness remains false"
  - id: workspace-write
    sequence: "same repository has a non-canonical execution workspace -> valid scoped mutation passes firewall and remains governed by existing scope/sandbox/audit authority"
  - id: immutable-hub
    sequence: "Hub does not project execution_profile/capability field -> Core unit/integration/protocol verification remains sufficient -> PR-010 is not blocked by Hub"
invariants:
  - canonical_repository_protection_is_provider_owned
  - hub_is_transport_not_security_authority
  - file_ops_rw_never_overrides_canonical_role
  - repository_identity_semantics_have_one_provider_source
  - every_effective_core_repository_mutator_is_covered_before_capability_advertisement
  - indeterminate_target_or_process_coverage_fails_closed
  - generic_tools_cannot_self_declare_canonical_sync
  - execution_workspace_passage_does_not_grant_mutation_authority
  - external_hub_projection_limitations_are_non_blocking_for_pr010
material_questions: []
disconfirming_cases:
  - "one effective SentinelX Core mutation operation can alter a canonical descendant while the capability is advertised"
  - "protection depends on parsing shell/script text and misses an indirect child-process write"
  - "RepositoryIdentity and canonical inventory normalize the same repository differently"
  - "PR-010 cannot be accepted solely because the third-party Hub omits execution_profile or a capability field despite complete Core-owned evidence"
challenge_completed: true
```

## Acceptance Criteria

- **A1 / R1:** canonical inventory is Host-authoritative, canonicalized and distinguishable from generic protected/workspace roots.
- **A2 / R2:** canonical inventory reuses/shared-composes `RepositoryIdentity`; no second incompatible repository identity model remains.
- **A3 / R3:** one reusable provider firewall seam returns stable allow/block/indeterminate dispositions before mutation.
- **A4 / R4,R5:** structured edit/file/upload/Git mutation surfaces have direct regressions and no canonical backup/partial-write side effects.
- **A5 / R6:** process mutation has Core-owned physical exclusion or fail-closed disposition; shell/string heuristics and missing Hub arguments are not the proof.
- **A6 / R7,R8:** capability readiness is true only on complete effective Core mutation-surface coverage and is verified through Core-owned evidence.
- **A7 / R9,R10:** canonical read-only operations remain usable; execution-workspace mutation remains subject to existing authority after firewall passage.
- **A8 / R11:** full Windows incident matrix passes, including broad-parent-`rw`, indirect child writes and indeterminate classification.
- **A9:** affected SentinelX security/regression suites pass; no unrestricted fallback, permission expansion, duplicate executor/store/audit authority, or Hub modification is introduced.
- **A10:** documentation explains inventory, readiness, errors, platform support, repository-identity reuse, distinction from scoped sandboxing, and immutable third-party Hub boundary.

## Regression Surface

- `src/sentinelx_core/policy.py` — Host-owned inventory/config parsing;
- `src/sentinelx_core/mutation_placement.py` — shared `RepositoryIdentity` semantics;
- `src/sentinelx_core/canonical_repository_firewall.py` — central admission/readiness;
- structured mutation handlers: edit, fsmutate, upload/finalization, structured Git;
- process execution handlers and sandbox composition;
- authoritative registry/effect metadata and mixed-operation classifiers;
- Core capability/hello/protocol structures;
- Windows incident regressions and same-repository execution-workspace allowance;
- documentation/configuration examples and immutable-Hub boundary.