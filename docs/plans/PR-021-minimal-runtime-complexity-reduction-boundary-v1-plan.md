# PR-021 SentinelX Minimal Runtime & Complexity Reduction Boundary V1 — Plan R1

## Status

~~~yaml
task_id: PR-021-minimal-runtime-complexity-reduction-boundary-v1
plan_revision: 1
plan_status: accepted_finalization_ready
implementation_authority: false
execution:
  completed_slices: [S01, S02, S03, S04]
  implementation_execution_complete: true
  acceptance_approved: true
  finalization_ready: true
  integration_transport: github-pr
  canonical_pr: 21
  finalization_receipt: docs/checkpoints/PR-021-minimal-runtime-complexity-reduction-boundary-v1-premerge-finalization-r2-receipt.yaml
  current_main_revalidated_sha: f72ac8bfe643cd9fbdea231e4a69f9e88a0595e9
requirement_ref: docs/requirements/PR-021-minimal-runtime-complexity-reduction-boundary-v1.md
requirement_revision: 1
transport:
  type: github-pr
  pr_number: 21
  branch: task/minimal-runtime-complexity-reduction-boundary-v1
  base: main
repository_baseline:
  main_sha: 1028030b33f0ea792a884491a431fffe566f6aa5
runtime:
  devforge_version: 2.99.0
  devforge_revision: 395949ff447df412c0db9c5e4e5ae6fb043bb6f2
scope:
  product_source_mutation: forbidden
  architecture_documentation_only: true
~~~

## Objective

Freeze the smallest defensible SentinelX runtime boundary before any further long-running execution bridge work.

This Plan deliberately does **not** implement the simplification. It produces the decision artifacts that make later simplification safe and auditable:

1. current capability inventory;
2. Architecture Decision;
3. KEEP / SIMPLIFY / DEPRECATE / HOLD matrix;
4. one successor implementation order.

No production source deletion, runtime behavior change, project binding change or production Hub change is allowed in this task.

## Planning decision

The product boundary is already selected by Requirement Revision 1:

~~~text
short bounded local work
→ SentinelX direct execution is allowed

CodeBuddy / Codex / large build / long test / large refactor /
duration-uncertain development execution
→ guided / semi-interactive local CLI
→ user runs locally
→ durable commit / receipt / read-back returned
→ ChatGPT / DevForge continues
~~~

The Plan therefore does not compare “fully automated Hub long-task orchestration” and “guided CLI” as equal product options. It records Durable Async automation as the strongest counterevidence and verifies that the chosen boundary remains safe.

## Deliverables

### D1 — Architecture Decision

Target:

~~~text
docs/architecture/sentinelx-minimal-runtime-boundary-v1.md
~~~

Required sections:

- Context
- Problem statement
- Decision
- Minimal Runtime responsibilities
- Explicit non-responsibilities
- Direct-short vs guided-CLI resolution
- Security invariants
- DevForge ownership boundary
- Hub window semantics
- Long-running task handoff contract
- Consequences
- Strongest counterargument
- Risks / assumptions / unknowns
- Migration implications
- Successor order
- Revisioned evidence baseline

### D2 — Capability Disposition Matrix

Target:

~~~text
docs/architecture/sentinelx-capability-disposition-matrix-v1.md
~~~

Each material entry must include:

| Field | Meaning |
| --- | --- |
| Capability / component | Stable name or source path |
| Current responsibility | What it owns today |
| Evidence | Main source / open Task / PR evidence |
| Runtime class | security / projection / short-exec / verification / orchestration / long-agent / delivery |
| Disposition | KEEP / SIMPLIFY / DEPRECATE / HOLD |
| Why | Decision rationale |
| Dependency impact | What depends on it |
| Safe next action | no-op / narrow / retire later / split successor |
| Removal precondition | Evidence required before deletion/disable |
| Owner after boundary | SentinelX / DevForge / guided CLI / external provider |

The matrix is decision authority for successor planning, not automatic deletion authority.

### D3 — Active-task impact section

The ADR/matrix must explicitly cover:

- PR-014 DevForge Execution Workspace Materialization Bridge V1;
- PR-020 Durable Async Operation Runtime & Outcome Readback V1;
- PR-229 / DevForge `incremental_execution.slice_v1` dependency relation;
- PR-015-derived Direct Codex runtime currently on main;
- direct CodeBuddy invocation/projection direction;
- PR-019 Stable Baseline relation.

### D4 — Minimal successor order

Exactly one primary sequence, with conditional alternatives only where evidence is still missing.

The order must prefer stopping unnecessary work before adding replacement code.

## Evidence baseline and read-only inventory

### Canonical SentinelX baseline

~~~text
bewaterhere-coder/sentinelx-cloud-core
main@1028030b33f0ea792a884491a431fffe566f6aa5
~~~

### DevForge baseline used for workflow separation

~~~text
bewaterhere-coder/DevForge
main@395949ff447df412c0db9c5e4e5ae6fb043bb6f2
version 2.99.0
workflow project_development v2.1
~~~

Current DevForge contract facts to preserve:

- `#开发` owns Requirement + Planning;
- planning/review remain orchestration-side;
- implementation is separately authorized;
- `incremental_execution.slice_v1` is an execution/workflow capability and does not require SentinelX to own a long-running request;
- one bounded execution invocation may complete at most one Slice;
- no verified receipt means no completion claim.

### SentinelX evidence set

At minimum read and inventory:

~~~text
src/sentinelx_core/handlers/direct_codex.py
src/sentinelx_core/direct_codex_acl.py
src/sentinelx_core/direct_codex_discovery.py
src/sentinelx_core/direct_codex_handoff.py
src/sentinelx_core/direct_codex_persistence.py
src/sentinelx_core/direct_codex_result.py
src/sentinelx_core/direct_codex_transport.py
src/sentinelx_core/direct_codex_workspace.py

src/sentinelx_core/handlers/devforge_runtime.py
src/sentinelx_core/local_api.py
src/sentinelx_core/handlers/local_api.py
src/sentinelx_core/jobs.py
src/sentinelx_core/pending_results.py

src/sentinelx_core/mutation_scope.py
src/sentinelx_core/mutation_audit.py
src/sentinelx_core/mutation_sandbox.py
src/sentinelx_core/windows_mutation_sandbox.py
src/sentinelx_core/operation_registry.py
src/sentinelx_core/canonical_repository_firewall.py

src/sentinelx_core/verification_execution.py
src/sentinelx_core/verification_profile.py
src/sentinelx_core/verification_readiness.py
src/sentinelx_core/verification_runtime.py
src/sentinelx_core/handlers/scoped_script.py
~~~

Open task/PR evidence:

~~~text
PR #14 — DevForge Execution Workspace Materialization Bridge V1
PR #19 — Stable Baseline & Stabilization Exit Gate V1
PR #20 — Durable Async Operation Runtime & Outcome Readback V1
~~~

Merged/current lineage evidence:

~~~text
PR-015 Direct Codex Development Host Invocation Bridge V1
~~~

DevForge-side incremental execution evidence is resolved from current DevForge main contract rather than treated as SentinelX implementation authority.

## Preliminary disposition hypotheses

These are review hypotheses only. D2 freezes the final disposition after the evidence pass.

### Strong KEEP candidates

- mutation scope authority;
- fail-closed mutation audit;
- AppContainer / ACL / Job containment;
- canonical repository mutation firewall;
- operation/effect registry needed for repository safety;
- bounded structured local_api projection;
- read-back/receipt verification;
- short scoped verification machinery that is actually used by the minimal runtime.

Reason: these are security or verification boundaries, not long-task orchestration.

### Strong HOLD candidates

- PR-020 unchanged implementation;
- new Durable Async development-Agent runtime work;
- CodeBuddy direct Hub invocation projection;
- further timeout-extension work intended to keep Agent development inside Hub;
- PR-014 implementation steps that exist only to bootstrap long CodeBuddy/Codex execution.

Reason: continuing these before architecture disposition would increase exactly the complexity this task is meant to control.

### Strong DEPRECATE candidates

Subject to dependency proof:

- Direct Codex execution lifecycle as a core SentinelX responsibility;
- Codex-specific discovery / persistence / transport / workspace lifecycle surfaces that have no short bounded use after guided CLI exists;
- task-scoped long-Agent bootstrap semantics exposed through SentinelX.

Deprecation means “freeze new dependence and plan later retirement”; no code is removed in PR-021.

### SIMPLIFY candidates

Subject to evidence:

- DevForge runtime local_api surface: retain only bounded structured operations needed for short local control/security/verification;
- workspace materialization: retain only if short safe mutation requires provider-owned isolated workspace creation;
- background jobs: preserve legitimate generic/non-development value while preventing them from becoming the default DevForge long-Agent path;
- verification runtime: retain minimal short verification substrate, avoid embedding long test orchestration.

## Critical architecture questions to resolve in D1/D2

### Q1 — Is execution workspace materialization security substrate or orchestration substrate?

Decision test:

- if isolated workspace creation is required to prevent canonical/main mutation during short bounded writes, KEEP/SIMPLIFY;
- if a path exists only to stage a long development Agent, HOLD/DEPRECATE that path.

No generic “workspace materialization is complex” argument is sufficient to remove a security boundary.

### Q2 — Does PR-020 have independent non-development product value?

Decision test:

- if a currently supported SentinelX product capability genuinely requires durable long-running operation truth independent of development Agents, split/narrow the requirement;
- if the only material driver is keeping DevForge/Codex execution alive beyond the Hub window, HOLD/DEPRECATE PR-020 under this boundary.

Existing `jobs.py` / `pending_results.py` must be evaluated before inventing a second lifecycle.

### Q3 — What remains of Direct Codex after guided CLI?

Decision test:

- CLI owns long Codex process lifecycle;
- DevForge owns Task/Plan/Slice semantics;
- SentinelX may still own short security/readback operations around returned evidence;
- Codex-specific execution code with no remaining bounded responsibility becomes a retirement candidate.

### Q4 — How does incremental slicing interact with guided CLI?

Decision:

`incremental_execution.slice_v1` remains a DevForge workflow concept.

A Slice is **not** evidence that it fits the Hub window.

Resolver behavior:

~~~text
current DevForge slice
↓
bounded + short + locally executable?
├─ yes → SentinelX direct-short path
└─ no / uncertain → guided CLI handoff for that exact slice/task context
~~~

No timeout extension follows from “one slice per execute”.

## Execution mode resolution to freeze

The ADR must define a deterministic preference order:

~~~text
1. Read-only / pure analysis possible without Host mutation?
   → ChatGPT / repository read path

2. Authorized mutation/verification is bounded and short?
   → SentinelX direct-short path

3. Requires CodeBuddy or Codex Agent?
   → guided CLI

4. Large build/test/refactor or uncertain duration?
   → guided CLI

5. Long background work has independent non-development product requirement?
   → evaluate its owning capability separately; do not inherit DevForge automation by default
~~~

A caller may not select “increase timeout” as a routing mode.

## Guided CLI handoff minimum contract

The ADR must specify that a generated handoff contains:

~~~yaml
repository:
task_id:
transport:
  type:
  pr:
  branch:
stage:
requirement:
  ref:
  revision:
plan:
  ref:
  revision:
current_slice: optional
allowed_scope:
forbidden_actions:
verification:
expected_return_evidence:
  - commit_or_patch_identity
  - test_or_verification_result
  - provider_receipt_when_applicable
  - canonical_transport_readback
~~~

The handoff is a user-executable command/task package. It does not claim that SentinelX executed the long task.

## Implementation slices

This is a documentation-only task. No Slice may modify `src/`, `tests/`, runtime installation, Host policy or production Hub state.

### S01 — Evidence inventory

Objective:

Create a revisioned inventory of current main components and active task lineages.

Actions:

1. read current main source paths listed above;
2. read PR-014/019/020 canonical artifacts;
3. resolve current DevForge incremental slicing semantics from DevForge main;
4. map dependencies and ownership;
5. record unknowns explicitly.

Output is working evidence for D1/D2; it may be embedded in the final matrix rather than persisted as a third artifact.

Verification:

- every matrix candidate has at least one canonical evidence source;
- no disposition is based only on chat history;
- no external mutation.

### S02 — Freeze Architecture Decision

Create:

~~~text
docs/architecture/sentinelx-minimal-runtime-boundary-v1.md
~~~

Must resolve Q1-Q4 and record:

- selected boundary;
- counterevidence;
- consequences;
- security invariants;
- execution-mode resolver;
- guided CLI handoff contract;
- migration/successor rules.

Verification:

- Requirement R1-R13 traced;
- no source deletion authorized;
- no capability disposition contradicts security invariants.

### S03 — Freeze Capability Disposition Matrix

Create:

~~~text
docs/architecture/sentinelx-capability-disposition-matrix-v1.md
~~~

Required minimum groups:

1. core projection/read;
2. short execution;
3. mutation security;
4. repository safety;
5. verification;
6. background delivery;
7. DevForge bridge;
8. workspace materialization;
9. direct Codex;
10. CodeBuddy direct projection;
11. Durable Async proposal;
12. incremental slicing relation.

Verification:

- all four dispositions have precise semantics;
- every DEPRECATE/HOLD item states what remains safe today;
- retirement preconditions prevent premature deletion;
- PR-014/020/229 relation is explicit.

### S04 — Successor ordering and acceptance evidence

Finalize the ADR with exactly one primary minimalization sequence.

Expected shape, subject to S01-S03 evidence:

~~~text
A. stop/hold architecture-conflicting active work
B. add minimal guided-CLI routing/handoff
C. prove short direct SentinelX path still works
D. narrow or retire long-Agent-specific bridges
E. only then delete obsolete code in separate tasks
~~~

Verification:

- sequence does not require parallel risky removals;
- each deletion/simplification is a future explicit DevForge Task;
- PR-021 itself remains documentation-only.

## Test / verification strategy

No product test suite is required merely to write the ADR, but the documentation must use repository read-back verification.

Required command-completion evidence:

1. Requirement Revision 1 read back from PR branch;
2. Plan R1 read back from PR branch;
3. Architecture Decision exists and is read back after implementation;
4. Disposition Matrix exists and is read back after implementation;
5. PR diff contains no `src/` or `tests/` product mutation;
6. PR diff contains no production Hub/deployment mutation;
7. active PRs are not silently closed/merged;
8. canonical `main` remains unchanged by task creation/implementation.

Acceptance later should inspect the final PR changed-file list and fail if product source is present.

## Risks

### Risk A — Overcorrecting and removing security structure

Mitigation: security-vs-orchestration classification is mandatory before disposition.

### Risk B — Guided CLI loses identity/evidence

Mitigation: exact Task/PR/branch/Requirement/Plan/Slice and expected receipt/read-back fields are part of the handoff contract.

### Risk C — PR-020 solves a real non-development need

Mitigation: PR-020 is not automatically deleted; matrix must test independent product value and allow a narrowed successor if proven.

### Risk D — “Short” is estimated incorrectly

Mitigation: CodeBuddy/Codex and explicitly large/uncertain classes route to CLI regardless of optimistic estimate. Direct execution is only for bounded work with a clear short verification path.

### Risk E — Existing PR dependencies make immediate closure unsafe

Mitigation: PR-021 outputs disposition and successor order only; it does not close branches or rewrite active Task history.

## Strongest counterargument

PR-020 offers a coherent fully automated architecture:

~~~text
admit durable operation
→ return handle
→ run long Agent
→ persist status/receipt
→ reconnect/read back
~~~

This would preserve end-to-end automation.

The Architecture Decision must acknowledge that benefit, then compare it against the state machines and ownership SentinelX must absorb: admission, durable operation identity, lifecycle persistence, restart recovery, outcome-unknown reconciliation, retention, duplicate suppression, provider adapters and security composition.

The decision is accepted only if guided CLI demonstrates a materially smaller ownership surface while preserving DevForge evidence and SentinelX security.

## Explicit non-authority

Plan approval will not authorize:

- deletion of Direct Codex source;
- disabling any provider;
- implementation of guided CLI;
- PR-014 closure/merge;
- PR-020 closure/merge;
- PR-019 stabilization exit;
- DevForge Runtime mutation;
- project binding mutation;
- production Hub changes;
- timeout increases;
- CodeBuddy/Codex Agent execution through Hub;
- release/deployment.

Each successor requires its own explicit DevForge Task.

## Post-plan state

~~~yaml
requirement_ready: true
plan_ready: true
plan_approved: false
implementation_authorized: false
next_stage: plan_review
next_expected_actor: reviewer
canonical_next_action: "#开发评审 PR-021-minimal-runtime-complexity-reduction-boundary-v1"
~~~
