# PR-010 — SentinelX Provider Canonical Repository Mutation Firewall V1

## State

```yaml
project_id: sentinelx-cloud-core
task_id: PR-010-canonical-repository-mutation-firewall-v1
title: SentinelX Provider Canonical Repository Mutation Firewall V1
development:
  stage: plan_review_rejected
  gates:
    requirement_ready: true
    plan_approved: false
    acceptance_approved: false
    completion_verified: false
  latest_plan_review: rejected_round_1
  review_disposition: plan_local
  next_expected_actor: planner
transport:
  type: github-pr
  pr_number: 10
  branch: task/canonical-repository-mutation-firewall-v1
  base_branch: main
artifacts:
  plan: docs/plans/PR-010-canonical-repository-mutation-firewall-v1-plan.md
  plan_review: docs/reviews/PR-010-canonical-repository-mutation-firewall-v1-plan-review-r1.md
related_tasks:
  - PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1
  - PR-008-provider-execution-profile-tool-surface-alignment-v1
  - PR-009-mcp-development-execution-projection-dynamic-tool-contract-v1
external_contract:
  repository: bewaterhere-coder/DevForge
  ref: 7c28d0dc2b6dc98ad23ac9bf1e2ea3c5b68c6372
  path: system/canonical-repository-host-mutation-firewall-contract.md
  required_capability: canonical_repository_mutation_firewall_v1
```

## Problem

SentinelX already has two strong but incomplete security layers:

1. `file_ops` canonicalizes paths and requires explicit `rw` access for structured filesystem/Git mutation;
2. `mutation_execution` owns scoped-mutation placement, `protected_roots`, sandbox readiness and audit lineage.

Those layers do **not** currently prove the DevForge provider contract that a canonical source checkout is physically non-mutable through every model-facing Host mutation surface.

Current `main` reality shows the gap:

- `MutationExecutionPolicy.protected_roots` exists, but it is scoped-mutation policy rather than a provider-wide canonical-repository inventory;
- `edit`, destructive filesystem operations and structured Git patch mutation admit writes primarily through `file_ops rw`;
- `exec` admits an allowlisted command and then runs a shell without a canonical-repository target firewall;
- legacy/unprofiled `script_run` is intentionally more powerful than `exec` and is not bounded by `allowed_commands`;
- upload/edit-upload paths are mutation surfaces and must not become an alternate write path;
- a broad OS/file allowlist such as `D:\coco = rw` can therefore coexist with a canonical checkout under that tree and still permit a bypass around DevForge semantic checkout-role admission.

The result is the exact failure class observed in the DevForge canonical-repository incident: a higher-level workflow can be correct while a lower-level Host mutation primitive can still physically change the canonical checkout.

## Goal

Implement a provider-owned, provider-wide canonical repository mutation firewall that satisfies the DevForge consumer contract `canonical_repository_mutation_firewall_v1` without hard-coding DevForge, a host name, a repository path, or one caller/runtime.

For every model-facing SentinelX operation capable of materially changing a repository checkout, the provider must either:

- prove the target does not intersect a Host-authoritative canonical repository root and continue through the operation's existing authorization boundary; or
- reject before material mutation with stable fail-closed evidence.

Capability advertisement is allowed only when coverage is complete for the provider's exposed mutation surface.

## Ownership Boundary

SentinelX owns:

- Host-authoritative canonical repository inventory and target classification;
- provider-wide mutation admission before handler/process mutation;
- OS-enforced containment where target inference alone cannot prove safety;
- capability readiness/advertisement and diagnostic evidence;
- regression tests proving no model-facing mutator bypasses the boundary.

DevForge owns the consumer semantics and expected capability/error contract. This Task MUST NOT modify DevForge or claim that a DevForge release is completed.

The Hub/MCP projection may carry operations to SentinelX, but MUST NOT mint or remove canonical repository protection authority.

## Required Behavior

### R1 — Host-owned canonical repository inventory

Introduce or derive an explicit Host-authoritative inventory that can distinguish canonical repository roots from generic protected roots and ordinary writable project/workspace roots.

The inventory must bind at least:

```text
canonical root
repository identity (vcs + authority + path, when available)
canonical branch / source-role metadata when applicable
inventory provenance / readiness evidence
```

Rules:

- caller payload path, cwd, environment variables, branch name, chat memory and model assertions are evidence only;
- `file_ops rw` never removes canonical protection;
- generic `mutation_execution.protected_roots` MUST NOT be reinterpreted as canonical repository identity if doing so would also block unrelated execution workspaces;
- path classification must canonicalize traversal/symlinks before intersection testing;
- inability to classify safely is fail-closed for material mutation.

### R2 — Stable provider-level admission API

Create one reusable firewall/classifier seam consumed by every relevant mutation handler rather than duplicating ad-hoc checks.

Required dispositions are equivalent to:

```text
AllowedNonCanonicalTarget
CanonicalRepositoryMutationBlocked
HostCanonicalMutationFirewallIndeterminate
```

The canonical-block result must occur before the first material mutation or child process that could mutate the protected checkout.

### R3 — Structured file/edit/upload coverage

Provider enforcement must cover all structured filesystem write paths, including at least:

```text
edit
edit_upload_complete
move
copy destination / overwrite paths
delete
chmod
chown
upload finalization paths that can materialize outside staging
future equivalent file-write operations
```

For move/copy, every material endpoint must be classified with correct read/write semantics. Backup creation must not create `.bak.*` artifacts inside or adjacent to a canonical repository when the original mutation is blocked.

### R4 — Structured Git coverage

All structured Git mutation paths must consume the firewall, including `apply_patch` and any future checkout/ref/worktree mutation added to the structured Git operation.

Read-only Git operations remain available.

A generic Git operation must not self-identify as `canonical_sync` to bypass the firewall.

### R5 — `exec` / shell process coverage

`exec` is mutation-capable even when its command prefix is allowlisted. The firewall must therefore provide **physical** canonical-write exclusion for commands/process trees that cannot be safely proven read-only by structured target arguments.

V1 MUST NOT claim provider-wide capability based only on shell-string/path heuristics. If the provider cannot guarantee that an admitted `exec` process and descendants cannot mutate a canonical repository, capability readiness stays unavailable or that execution class is blocked under firewall mode.

### R6 — legacy and profiled `script_run` coverage

Unprofiled/legacy `script_run`, profiled/scoped mutation execution, background children, and timeout/nonzero paths must preserve canonical exclusion.

Scoped execution may reuse existing sandbox/protected-root mechanisms where they prove the same physical boundary, but `canonical_repository_mutation_firewall_v1` remains a distinct readiness claim from `host_mutation_sandbox_v1` and `pre_execution_audit_lineage_v1`.

No `operator_unrestricted` or legacy compatibility path may bypass canonical protection while the firewall capability is advertised.

### R7 — Capability readiness and advertisement

Advertise:

```text
canonical_repository_mutation_firewall_v1
```

only when SentinelX can prove provider-wide coverage for every currently exposed model-facing mutation surface capable of targeting repository paths.

If one relevant mutator is unprotected, readiness is false and the capability must not be advertised as verified.

Diagnostics must identify uncovered operation classes without exposing sensitive host paths unnecessarily.

### R8 — Canonical source exceptions remain dedicated

Generic file/Git/shell/script tools receive no canonical mutation exception.

If SentinelX later supports structured canonical source mechanics, they must be dedicated operations with independent exact repository/branch verification. V1 does not require implementing `canonical_sync`; read/readback may remain available through existing read-only operations.

### R9 — Execution workspace remains mutable under existing authority

The firewall must not turn the repository's admitted execution workspace into a canonical root merely because both belong to the same repository identity.

Passing the firewall is exclusion evidence only. Existing scope, audit, sandbox, `file_ops`, Git, execution-profile and transport authorization still apply.

### R10 — Incident regression and fail-closed semantics

Freeze at minimum these cases:

```text
canonical main + generic file edit             -> BLOCK
canonical main + backup-producing edit/delete -> BLOCK with no backup side effect
canonical main + structured git apply_patch    -> BLOCK
canonical main + generic git switch via exec   -> BLOCK
canonical main + script child/background write -> BLOCK
unknown/indeterminate target classification    -> FAIL CLOSED
execution workspace + valid scoped mutation    -> PASS existing boundaries
read/list/search/status/diff on canonical      -> PASS
broad parent file_ops rw                       -> DOES NOT OVERRIDE
caller claims canonical_sync on generic op     -> BLOCK
```

## Compatibility / Non-Goals

- Do not hard-code `D:\coco`, DevForge, `Cherie_li`, a GitHub owner, or a particular canonical checkout.
- Do not replace `file_ops`; the firewall is an additional denial boundary.
- Do not create a second mutation-scope store, audit journal, sandbox executor or repository identity model when an existing SentinelX primitive can be composed.
- Do not make `protected_roots` so broad that valid execution workspaces become unusable.
- Do not weaken `host_mutation_sandbox_v1`, `pre_execution_audit_lineage_v1`, PR-007 scope admission or PR-008 profiled execution semantics.
- Do not claim production Hub changes.
- Do not auto-expand filesystem permissions or command allowlists.
- Do not implement a generic `canonical_sync` escape hatch in V1.
- Linux/macOS may remain capability-unavailable if equivalent physical enforcement cannot be proven in V1; unsupported platforms must fail closed rather than advertise partial coverage.

## Active-Branch Compatibility Constraint

PR-007 and PR-008 currently modify mutation-scope / scoped-script / capability-advertisement seams. Before implementation touches an overlapping file (`client.py`, `handlers/basic.py`, `handlers/scoped_script.py`, `mutation_scope.py` or equivalent), the exact latest dependency head and semantic contract must be re-read.

A moving branch is not implicit implementation authority. Rebase/merge strategy is decided only after plan approval and exact dependency readback.

## Requirement Readiness Evidence

```yaml
depth: deep
behavior_examples:
  - id: canonical-file-write
    sequence: "operator config exposes a broad parent as file_ops rw -> edit targets a canonical checkout descendant -> firewall blocks before edit/backup"
  - id: canonical-process-write
    sequence: "allowlisted exec or script attempts to write canonical file through a child process -> physical enforcement blocks the write; no semantic string-parser bypass is accepted"
  - id: workspace-write
    sequence: "same repository has a non-canonical execution workspace -> valid scoped mutation passes firewall and remains governed by existing scope/sandbox/audit authority"
invariants:
  - canonical_repository_protection_is_provider_owned
  - file_ops_rw_never_overrides_canonical_role
  - every_model_facing_repository_mutator_is_covered_before_capability_advertisement
  - indeterminate_target_or_process_coverage_fails_closed
  - generic_tools_cannot_self_declare_canonical_sync
  - execution_workspace_passage_does_not_grant_mutation_authority
  - provider_capability_is_distinct_from_scoped_mutation_capabilities
material_questions: []
disconfirming_cases:
  - "one exposed mutation operation can still alter a canonical descendant while capability is advertised"
  - "protection depends on parsing shell/script text and misses an indirect child-process write"
  - "broad protected-root configuration blocks normal execution workspaces rather than identifying canonical checkouts"
  - "blocking a canonical delete/edit still leaves a .bak or partial mutation"
challenge_completed: true
```

## Acceptance Criteria

- **A1 / R1:** canonical inventory is Host-authoritative, canonicalized and distinguishable from generic protected/workspace roots.
- **A2 / R2:** one reusable provider firewall seam returns stable allow/block/indeterminate dispositions before mutation.
- **A3 / R3,R4:** structured edit/file/upload/Git mutation surfaces have direct regression coverage and no canonical backup/partial-write side effects.
- **A4 / R5,R6:** process-based mutation (`exec`, script, background/child) has OS-enforced or equivalently physical canonical exclusion; string heuristics alone are insufficient.
- **A5 / R7:** capability advertisement is true only when the complete exposed mutation surface is covered and readiness is proven.
- **A6 / R8,R9:** canonical read-only operations remain usable; execution-workspace mutation still works only under existing authority.
- **A7 / R10:** the full incident matrix passes on Windows, including broad-parent-`rw`, indirect child write and indeterminate classification.
- **A8:** current SentinelX security/regression suite remains passing; no unrestricted fallback or permission expansion is introduced.
- **A9:** provider documentation explains inventory configuration/discovery, readiness, error semantics, platform support and the distinction from scoped mutation sandboxing.

## Regression Surface

- `src/sentinelx_core/policy.py` — Host-owned inventory/config parsing and canonicalization;
- structured mutation handlers: edit, fsmutate, upload/finalization, structured Git;
- process mutation handlers: exec and script/scoped-script paths;
- capability/readiness advertisement and client hello projection;
- mutation scope/sandbox interaction;
- Windows process-tree/AppContainer/ACL behavior;
- configuration examples, README/security/threat-model documentation;
- active PR-007/PR-008 overlap and drift reconciliation.