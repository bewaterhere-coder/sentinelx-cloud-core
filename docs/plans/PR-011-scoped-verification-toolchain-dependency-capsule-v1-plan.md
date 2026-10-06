# PR-011 — Scoped Verification Toolchain & Dependency Capsule V1 — Plan

## Plan State

```yaml
plan_revision: 6
task_id: PR-011-scoped-verification-toolchain-dependency-capsule-v1
requirement_revision: 2
status: completed
review_state: approved
implementation_authorized: false
execution_state: all_slices_completed
acceptance_state: approved
transport:
  type: github-pr
  pr_number: 11
  branch: task/scoped-verification-toolchain-dependency-capsule-v1
  base_branch: main
repository_baseline: e7064c9bf4fcd15bdb6f5a2678414210c01d1c00
task_head_at_remediation_entry: d14451836293640407d80a6fc32405bd3a2b17b8
runtime_provenance:
  devforge_version: "2.51.0"
  devforge_main_sha: 7e5a098473d89f88a69066a9bc88d1213b2f7e49
  devforge_runtime_blob_sha: 54eb9e4f0c79620357bc2cf1b8d06d6af9771d6d
  review_contract_version: "1.3"
  review_contract_blob_sha: e8fe92cf1e98c3f7eb5bd60277bde8b42b381df7
remediation_source:
  rejected_review_ref: docs/reviews/PR-011-scoped-verification-toolchain-dependency-capsule-v1-plan-review-r5.md
  rejected_review_blob_sha: 889a632e21b1b3bfeda4e72dd06bb6ee37fb7dad
  rejected_finding: PR011-R5-F1-remediation-provenance-and-gate-transition-inconsistent
impact_analysis: docs/reviews/PR-011-scoped-verification-toolchain-dependency-capsule-v1-plan-r5-real-host-descendant-process-impact-analysis.md
prior_plan:
  revision: 5
  blob_sha: 39e2056c924b4ca9ba73211921001aff408e99a6
  archive_ref: docs/plans/PR-011-scoped-verification-toolchain-dependency-capsule-v1-plan-r5.md
prior_execution_slice_set:
  blob_sha: b0e92968c7a082cba6dce251bc3ff5ba50b334e8
  status: stale_due_real_host_descendant_process_disproof
```

## 1. Revision 6 Decision

Revision 6 is a **workflow/provenance-only Plan remediation** of the rejected Revision 5 Plan.

The latest rejected Plan Review classified the substantive Revision 5 architecture as acceptable but non-authorizable because the prior remediation was persisted with stale DevForge 2.43.0 provenance and an invalid `implementation -> plan_review` transition.

Revision 6 addresses exactly that finding:

1. it binds remediation to the current durable Task at `plan_review_rejected`;
2. it binds to the latest rejected Plan Review R5 and its exact blob;
3. it records fresh canonical DevForge 2.51.0 main/runtime/review-contract provenance;
4. it preserves Requirement Revision 2 without semantic change;
5. it preserves PR #11 and the existing task branch;
6. it preserves the complete substantive R5 architecture, evidence dispositions, security boundaries and proposed post-review repair sequence;
7. it compiles no new Execution Slice Set and grants no implementation authority;
8. after durable Plan readback, the owning `#开发计划修复` transition is only `plan_review_rejected -> plan_review`.

No product implementation is authorized by Revision 6 itself.

The technical remediation sequence remains exactly the Revision 5 sequence:

```text
S01 preserved / no replay
→ S02R toolchain minimum-authority repair
→ S03R real-Host descendant-process repair
→ S04 readiness/capability physical proof
→ S05 devforge_runtime projection + live readback
```

## 2. Preserved Canonical Boundaries

Revision 5 preserves these non-negotiable boundaries:

- PR-007 provider-owned `devforge_runtime` and one `MutationScopeStore`;
- PR-010 canonical repository mutation firewall;
- PR-012 explicit `execution_profile=scoped_mutation` contract;
- one Windows AppContainer sandbox implementation;
- one no-breakaway Job containment path;
- one `MutationAuditJournal`;
- exact execution-workspace mutation authority only;
- no caller-selected Host executable/toolchain/cache/capsule path;
- no network/DNS widening;
- no Git/SSH/GitHub/npm credential inheritance;
- no generic `exec`, generic shell, allowlist expansion or `operator_unrestricted` fallback;
- no production `mcp.sentinelx.app` Hub mutation.

If real descendant execution cannot be repaired inside these boundaries, implementation must fail closed and return to Requirement review rather than weaken them.

## 3. Evidence Validity After Real-Host Disproof

### S01 — preserved / no replay

The following remain valid:

- provider-owned logical verification profile;
- SourceUnderTestSnapshot identity/manifest binding;
- DependencyCapsule/package-lock integrity contract;
- deterministic ToolchainManifest identity;
- bounded path/resource/final-path validation.

No S01 side effect is reopened.

### S02 — partial evidence preserved / repair required

Preserved:

- verification intent sealed before SPAWN;
- source/capsule materialization inside the exact workspace;
- wrong source/capsule/lock/toolchain rejection before successful execution;
- terminal cleanup and residual-authority checks;
- provider stores remain non-writable.

Invalidated seam:

- provider-toolchain reachability may not be implemented by recursively rewriting every ancestor ACL.

The prior S02 completion receipt remains historical evidence, but it is not completion authority for the repaired ACL seam.

### S03 — partial evidence preserved / completion authority invalidated

Preserved:

- verification-specific environment sanitization;
- caller PATH/proxy/credential rejection;
- workspace-local cache/temp/home configuration;
- cwd confinement;
- sealed verification evidence and post-run integrity contracts;
- unprofiled scoped-runtime regression evidence not dependent on descendant Node/npm execution.

Invalidated seam:

- real descendant process creation from the AppContainer root Python runner;
- therefore real Node/npm descendant execution and npm lifecycle-descendant containment are not yet proven on the target Windows Host.

The prior S03 completion receipt remains historical evidence only for unaffected behavior.

### S04 — incomplete / unpublished

S04 never completed. The dirty execution workspace contains exploratory candidate changes from physical diagnosis. Those changes are not authoritative and must not be published wholesale.

Only changes that match the approved R5 repair Slice and pass fresh entry reconciliation may be reused.

### S05 — not started

No S05 evidence is affected because S05 has not begun.

## 4. R5 Repair Architecture

### 4.1 Toolchain ACL rule

The provider-owned toolchain ACL contract becomes:

```text
protected/system ancestors:
  never mutated merely for toolchain reachability

admitted toolchain root:
  transient AppContainer RX only
  no write
  exact configured provider root only

insufficient existing ancestor traversal:
  readiness fails closed
  no parent ACL widening
```

This repair stays inside the existing `WindowsMutationSandbox` toolchain authority path.

### 4.2 Descendant-process root-cause gate

Before Node/npm is re-tested, the repaired runtime must prove the smallest real descendant:

```text
AppContainer root python
→ child python using the same constrained token/process tree
→ child exits
→ child remains inside the same no-breakaway Job
→ terminal readback shows zero residual processes/authority
```

The implementation investigation is limited to the existing Windows spawn boundary, including:

- AppContainer root creation attributes;
- inherited process/token semantics;
- stdio/handle inheritance and runner plumbing;
- Job assignment/inheritance;
- Windows child-process policy attributes or accidental restrictions;
- environment and executable accessibility required for a child process to initialize.

The repair MUST NOT solve this by:

- breakaway from the Job;
- launching descendants outside AppContainer;
- broker-side unrestricted fan-out;
- a second executor;
- caller-minted process authority;
- generic Host shell/exec fallback.

### 4.3 Node/npm proof only after the minimal child passes

After the minimal child process is physically proven, the same real Host must prove:

1. direct admitted `node --version`;
2. direct admitted npm CLI version execution;
3. deterministic offline dependency-backed npm operation;
4. package scripts and lifecycle descendants remain in the no-breakaway Job;
5. DNS/HTTP/network fallback remains unavailable;
6. protected/canonical roots remain inaccessible/non-mutable;
7. no broker/user credentials leak into the scope;
8. terminalization removes transient toolchain authority.

A CI-only pass is insufficient for this physical boundary.

## 5. Post-Review Execution Sequence

If and only if Plan R5 is Approved, orchestration compiles a new exact Slice Set bound to Requirement R2 + Plan R5.

The new sequence is:

### S01 — imported completed

State: `completed / preserved_no_replay`.

No implementation replay.

### S02R — toolchain minimum-authority repair

Objective:

Repair provider-toolchain ACL reachability so real stable toolchains can be admitted without modifying protected/system ancestors.

Authorized scope:

- `src/sentinelx_core/windows_mutation_sandbox.py`;
- focused ACL/read-execute tests;
- stable-toolchain physical fixture;
- operator documentation only as required by the repaired contract.

Required proof:

- no ACL mutation on `C:\Program Files` or other protected ancestor merely for toolchain reachability;
- admitted toolchain root receives only transient RX;
- toolchain write remains denied;
- insufficient traversal fails closed;
- terminalization removes the exact transient grant;
- prior S02 unaffected integrity/materialization tests remain passing.

Prior S02 evidence is reused where unaffected; the entire S02 slice is not replayed.

### S03R — descendant-process execution repair

Depends on: S02R.

Objective:

Repair the existing Windows AppContainer/Job scoped execution path so descendant process creation is physically valid without containment widening.

Required proof order:

1. minimal `python -> python` real-Host descendant probe passes;
2. descendant process is observed inside the no-breakaway Job;
3. direct admitted Node and npm process creation passes;
4. offline npm/package-script/lifecycle descendants pass;
5. process tree quiesces and terminalizes without residual authority;
6. existing unprofiled Python/PowerShell/Pwsh scoped behavior remains regression-compatible.

The repaired implementation must continue to use the one existing sandbox/scope/audit authority.

Prior S03 evidence is reused only for unaffected environment/integrity behavior.

### S04 — readiness/capability + complete real-Windows proof

Depends on: S03R.

Objective:

Expose separately gated Node/npm verification readiness only after the repaired physical execution path is proven.

Required proof:

- false for absent/incomplete/unusable profile;
- base scoped-mutation readiness unaffected by verification-profile absence;
- real AppContainer Node/npm/offline verification succeeds;
- network/credential/protected-root denial holds;
- transient authority absent after terminalization;
- post-readiness toolchain tamper fails request-time validation;
- PR-010/PR-012 regressions pass;
- capability evidence remains bounded and path/credential safe.

### S05 — canonical devforge_runtime projection + live readback

Depends on: S04.

Objective remains the bounded verification selector on the existing canonical `devforge_runtime.execute_scoped` action.

Required properties:

- explicit `execution_profile=scoped_mutation` remains required;
- logical profile/source/capsule/integrity identifiers only;
- one existing scoped handler;
- Agent-owned `describe` schema;
- live execution returns bounded profile/toolchain/capsule/offline/audit/terminal evidence;
- no Hub modification or duplicate execution authority.

## 6. Dirty S04 Workspace Disposition

The existing workspace:

```text
D:\coco\workspaces\bewaterhere-coder\sentinelx-cloud-core\pr011-s04-20261005
```

contains exploratory unpublished repairs produced during physical diagnosis.

R6 rules (preserving R5 substance):

- do not reset or clean it before evidence capture/reconciliation;
- do not publish it wholesale;
- do not treat its current product diff as an approved implementation;
- S02R/S03R implementers may selectively reuse minimal changes only after exact comparison against current remote Task head, current main and the approved R6 Slice;
- generated `.devforge-*`, pytest temp trees and copied toolchain fixtures are never product artifacts.

## 7. Downstream PR-015 Boundary

ChatGPTControlShell PR-015 remains non-gating downstream evidence only.

PR-011 may be Accepted/Completed from SentinelX-owned evidence after S02R, S03R, S04 and S05 satisfy their gates. PR-011 must not mutate or complete PR-015.

## 8. Requirement Traceability

| Requirement / AC | R6 disposition |
|---|---|
| R1 | S01 preserved |
| R2 | S02R repairs minimum toolchain authority |
| R3-R4 | S01/S02 preserved evidence + regressions |
| R5 | S03R/S04 network denial |
| R6 | S03R must repair descendants inside the one scoped executor |
| R7 | S05 |
| R8 | S04 + S05 |
| R9 | regressions across S02R-S05 |
| R10 / AC12 | non-gating downstream only |
| AC1 | S01 + S02R |
| AC2 | S02R + S03R physical proof |
| AC3 | S03R offline npm proof |
| AC4 | preserved S01/S02 negative evidence + regressions |
| AC5 | S03R/S04 |
| AC6 | S03R decisive real-Host descendant containment proof |
| AC7 | S03R regressions |
| AC8 | S04 |
| AC9 | S05 |
| AC10-AC11 | S02R-S05 test/physical matrix |

## 9. Slice Compilation Rules After Approval

The post-review Slice Set must:

- import S01 as completed/no-replay;
- preserve prior S02/S03 receipts as partial historical evidence only;
- create S02R and S03R as new repair Slices;
- sequence exactly `S02R -> S03R -> S04 -> S05`;
- mark the Plan R4 Slice Set stale and non-authorizing;
- preserve one explicit `#开发执行` invocation → at most one Slice;
- retain PR #11 and the existing Task branch;
- fail closed on material main/Task/Host runtime drift.

No new R6 Slice Set may be compiled before Plan Review approval.

## 10. Revision 6 Review Questions

The reviewer must explicitly determine:

1. Does the real-Host `PYTHON_CHILD_START` evidence materially invalidate S03 descendant-execution completion authority?
2. Does the `C:\Program Files` ACL failure materially reopen only the S02 toolchain-authority seam rather than all S02 work?
3. Is Requirement R2 unchanged, with the defect correctly classified as Plan/implementation rather than Requirement drift?
4. Does S02R enforce minimum provider-toolchain authority without protected ancestor ACL widening?
5. Does S03R diagnose and repair descendant creation inside the existing AppContainer/Job path without adding a second executor or breakaway?
6. Are unaffected S01/S02/S03 artifacts preserved without replay while invalidated completion claims are removed from execution authority?
7. Is the only authorized post-review sequence `S02R -> S03R -> S04 -> S05`?
8. Does the Plan fail closed back to Requirement review if descendant execution cannot be made compatible with the existing security invariants?

9. Is the remediation now bound to current DevForge 2.51.0 provenance and the exact rejected R5 review?
10. Is the current Task transition provenance valid for `plan_review_rejected -> plan_review`, with no self-approval or Slice compilation?

Plan approval remains reviewer-owned. Revision 6 does not authorize implementation until Plan Review approval and exact R6 Slice Set readback are complete.
