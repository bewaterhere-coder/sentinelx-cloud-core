# PR-011 — Scoped Verification Toolchain & Dependency Capsule V1 — Plan

## Plan State

```yaml
plan_revision: 4
task_id: PR-011-scoped-verification-toolchain-dependency-capsule-v1
requirement_revision: 2
status: proposed
review_state: pending
implementation_authorized: false
transport:
  type: github-pr
  pr_number: 11
  branch: task/scoped-verification-toolchain-dependency-capsule-v1
  base_branch: main
repository_baseline: e7064c9bf4fcd15bdb6f5a2678414210c01d1c00
task_head_before_requirement_r2: 8d0126ee81142411a3a08c10abb39b84f574e2af
requirement_change_impact: docs/reviews/PR-011-scoped-verification-toolchain-dependency-capsule-v1-requirement-r2-impact-analysis.md
prior_plan:
  revision: 3
  blob_sha: 048d3a56386f035cb723df18d4f55b67500bb16b
prior_execution_slice_set:
  blob_sha: 8939452081926ea03c69044b3ef2537bf7050a9d
  status: stale_requires_recompile_after_plan_r4_review
```

## 1. Revision 4 Decision

Revision 4 is a narrow reconciliation for Requirement Revision 2. The immutable Revision 3 Plan identified by `prior_plan.blob_sha` is incorporated by reference for all security, verification, implementation and test semantics not explicitly changed here.

Revision 4 changes only the following material boundaries:

1. ChatGPTControlShell PR-015 is removed from PR-011 Acceptance/Completion gating. It remains optional downstream integration evidence after PR-011 independently completes.
2. Repository/runtime reality is refreshed to current SentinelX `main@e7064c9bf4fcd15bdb6f5a2678414210c01d1c00` and DevForge 2.43.0.
3. The old Plan R3 Execution Slice Set is stale because its exact Requirement/Plan binding changed. A replacement Slice Set may be compiled only after Plan R4 approval.
4. Verified S01-S03 completion receipts remain valid no-replay evidence. They are not invalidated by the AC12 gate change.
5. The only remaining implementation scope is `S04 -> S05`.

No product implementation is authorized by this Plan revision itself.

## 2. Current Canonical Reality

Current SentinelX `main` already contains and owns these canonical seams:

- PR-007 provider-owned `devforge_runtime` and MutationScope lifecycle;
- PR-010 canonical repository mutation firewall;
- PR-012 explicit `execution_profile=scoped_mutation` schema/admission/propagation contract;
- existing Windows AppContainer + Job containment and MutationAuditJournal authority.

Production `mcp.sentinelx.app` remains an immutable third-party transport boundary. Plan R4 does not require or authorize Hub changes.

PR-011 remote head before Requirement Revision 2 was `8d0126ee81142411a3a08c10abb39b84f574e2af`. That head persists the S04 blocked Host-proof checkpoint. S04 is not completed and no S04 product candidate was published to the Task branch.

The stopped S04 execution workspace:

```text
D:\coco\workspaces\bewaterhere-coder\sentinelx-cloud-core\pr011-s04-20261005
```

was observed dirty with unpublished candidate work. Requirement/Plan reconciliation must not reset, clean, overwrite, publish, or replay that workspace before the revised Plan/Slice lineage is approved and revalidated.

## 3. Preserved Implementation and Evidence

The Requirement Revision 2 change does not alter R1-R9 behavior or the implementation mechanisms already proven by S01-S03.

The following remain valid no-replay evidence:

### S01 — completed / preserved

Provider-owned verification policy and pure integrity/admission contracts:

- logical Node/npm verification profile;
- SourceUnderTestSnapshot identity/manifest binding;
- DependencyCapsule integrity and package-lock binding;
- deterministic ToolchainManifest identity;
- bounded resource/path/final-path validation.

### S02 — completed / preserved

Composition into the existing audit + AppContainer pre-SPAWN path:

- verification intent sealed into existing audit START evidence;
- admitted source/capsule materialization before SPAWN;
- source/lock/toolchain validation before process creation;
- minimum transient toolchain authority;
- bounded cleanup and terminal authority removal.

### S03 — completed / preserved

Real offline Node/npm descendant execution through the existing scoped executor:

- workspace-local sealed launchers;
- offline npm cache/configuration;
- credential/proxy/user-profile stripping;
- exact-workspace cwd confinement;
- Job containment;
- post-run integrity readback;
- regression compatibility for unprofiled Python/PowerShell/Pwsh execution.

No S01-S03 side effect may be replayed merely because Requirement/Plan lineage advanced to R2/R4.

## 4. Remaining Implementation Scope

### S04 — Node/npm readiness + real Windows physical proof

Objective remains the prior Plan R3 Step D / Slice S04 behavior.

Required completion evidence must prove on the real Windows Host under the admitted `D:\coco\workspaces` boundary:

- separately gated `host_runtime.scoped_verification_node_npm_v1` readiness (or exact approved equivalent);
- valid provider-owned Node/npm profile and dependency capsule;
- actual AppContainer `node` and `npm` execution;
- deterministic offline dependency-backed verification;
- DNS/HTTP/network fallback remains unavailable;
- canonical/protected roots remain inaccessible/non-mutable;
- no Git/SSH/GitHub/npm credential inheritance;
- descendants remain in the existing no-breakaway Job;
- transient toolchain ACL/authority is absent after terminalization;
- post-readiness toolchain tamper fails request-time validation;
- PR-010 firewall and PR-012 explicit execution-profile regressions remain passing.

Before any S04 product mutation, the implementer must reconcile the unpublished stopped S04 candidate against current `main`, Requirement R2, approved Plan R4, and the newly compiled Slice Set. Only unaffected candidate work may be reused; verified S01-S03 work is never replayed.

### S05 — canonical `devforge_runtime` verification projection + live readback

Objective remains the prior Plan R3 Step E / Slice S05 behavior.

Extend only the existing canonical `devforge_runtime.execute_scoped` seam with the bounded verification selector. The caller may supply logical/integrity identifiers only; Host paths, executable locations, cache paths, network endpoints, credentials and authority fields remain forbidden.

Required properties:

- explicit `execution_profile=scoped_mutation` remains mandatory;
- existing scope/repository/lineage bindings remain mandatory;
- the one existing scoped executor, MutationScopeStore, Windows sandbox and audit journal are reused;
- `sentinel_local_api describe devforge_runtime` projects the current selector from Agent-owned schema;
- a live admitted call returns bounded source/toolchain/capsule/offline/audit/terminal evidence;
- unprofiled `execute_scoped` and lifecycle actions remain regression-compatible;
- no Hub modification, generic shell/exec fallback, permission widening, `operator_unrestricted`, caller-selected Host path, or duplicate execution authority is introduced.

## 5. Downstream PR-015 Boundary

ChatGPTControlShell PR-015 is a downstream consumer with separate Task authority.

It is **not**:

- a PR-011 implementation Slice;
- a PR-011 Acceptance gate;
- a PR-011 merge prerequisite;
- a PR-011 Completion prerequisite.

After PR-011 independently satisfies its own Acceptance/Completion requirements and an accepted Agent build is activated, a separately authorized PR-015 continuation may run `mcp npm run typecheck` and `mcp npm run check` through the accepted capability. That evidence belongs to PR-015's workflow and may be retained as downstream integration confidence only.

No PR-011 Slice may execute, mutate, complete, or claim authority over PR-015.

## 6. Security / Architecture Invariants

Revision 4 preserves all prior security invariants:

- no second process executor;
- no second scope store;
- no second audit journal;
- no second sandbox implementation;
- no canonical repository mutation workspace;
- no caller-selected toolchain/source/cache/capsule Host path;
- no arbitrary network/DNS fallback;
- no Host credential inheritance;
- no generic command-allowlist widening;
- no `operator_unrestricted` fallback;
- no production Hub mutation;
- no duplication or bypass of canonical PR-007/PR-010/PR-012 seams.

## 7. Verification Matrix

Plan R3's pure/unit, scoped integration, `devforge_runtime` integration and physical Windows test matrix remains normative.

For Revision 4 completion, the decisive remaining evidence is:

```text
S04:
real Windows Host
+ admitted Node/npm profile
+ admitted dependency capsule
+ offline dependency-backed execution
+ AppContainer/Job containment
+ network/credential denial
+ protected-root denial
+ terminal authority cleanup

S05:
Agent-owned describe schema
+ explicit scoped_mutation profile
+ bounded verification selector
+ live execute_scoped evidence
+ scope/audit/terminal readback
+ legacy regression compatibility
```

PR-015 evidence is intentionally absent from this completion matrix.

## 8. Requirement Traceability Delta

| Requirement | Revision 4 disposition |
|---|---|
| R1-R6 | Preserved from Plan R3 and verified S01-S03 evidence |
| R7 | Remaining S05 canonical `devforge_runtime` integration |
| R8 | Remaining S04 readiness + S05 evidence/readback |
| R9 | Preserved compatibility/security regression surface |
| R10 | Non-gating downstream integration follow-up only |
| AC1-AC8, AC10-AC11 | S04 plus preserved S01-S03 evidence as applicable |
| AC9 | S05 live Agent schema/execution readback |
| AC12 | Non-gating; not part of PR-011 Acceptance/Completion eligibility |

## 9. Post-Review Slice Compilation

If and only if Plan R4 is Approved, orchestration compiles a new exact Execution Slice Set bound to Requirement R2 + Plan R4.

That Slice Set must:

- import S01, S02 and S03 as `completed` using their existing verified receipts/checkpoints;
- mark those completed Slices as no-replay evidence;
- expose S04 as the first pending Slice;
- expose S05 as pending and dependent on S04;
- remove the old `AC12_requires_separately_authorized_PR015_evidence` completion gate;
- preserve one explicit `#开发执行` invocation → at most one Slice;
- retain the current PR #11 / task branch transport identity.

The old Plan R3 Slice Set remains historical evidence only and cannot authorize new implementation after Requirement R2.

## 10. Revision 4 Review Questions

The reviewer must explicitly determine:

1. Is the AC12/PR-015 proof now unambiguously non-gating and outside PR-011 implementation/completion scope?
2. Are R1-R9 security and verification semantics preserved?
3. Are canonical PR-007 scope/executor, PR-010 firewall and PR-012 explicit-profile seams reused rather than duplicated?
4. Do S01-S03 completion receipts remain valid no-replay evidence under the narrow Requirement change?
5. Is the stopped S04 candidate correctly treated as unpublished/incomplete and subject to reconciliation before reuse?
6. Is the only remaining implementation sequence exactly `S04 -> S05`?
7. Does the proposed post-review Slice compilation preserve completed evidence while invalidating only the stale Plan R3 execution binding?
8. Can PR-011 be independently Accepted/Completed from SentinelX-owned real-Windows verification and live Agent readback evidence without invoking PR-015?

Plan approval remains reviewer-owned. Plan R4 does not authorize implementation until current Plan Review approval and exact post-review Slice Set readback are complete.
