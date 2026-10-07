# PR-019 — SentinelX Stable Baseline & Stabilization Exit Gate V1

## State — Requirement Revision 1

~~~yaml
project_id: sentinelx-cloud-core
task_id: PR-019-stable-baseline-stabilization-exit-gate-v1
requirement_revision: 1
development:
  stage: plan_review
  gates:
    requirement_ready: true
    plan_approved: false
    acceptance_approved: false
    completion_verified: false
  plan_revision: 2
  implementation_authorized: false
  next_expected_actor: reviewer
transport:
  type: github-pr
  pr_number: 19
  branch: task/stable-baseline-stabilization-exit-gate-v1
  base_branch: main
artifacts:
  plan: docs/plans/PR-019-stable-baseline-stabilization-exit-gate-v1-plan.md
  latest_plan_review: docs/reviews/PR-019-stable-baseline-stabilization-exit-gate-v1-plan-review-r1.md
  latest_plan_review_transition_receipt: docs/reviews/PR-019-stable-baseline-stabilization-exit-gate-v1-plan-review-r1-transition-receipt.yaml
  latest_plan_remediation: docs/checkpoints/PR-019-stable-baseline-stabilization-exit-gate-v1-plan-remediation-r2-20261007.yaml
  latest_plan_remediation_transition_receipt: docs/reviews/PR-019-stable-baseline-stabilization-exit-gate-v1-plan-remediation-r2-transition-receipt.yaml
related_tasks:
  evidence_predecessors:
    - PR-011-scoped-verification-toolchain-dependency-capsule-v1
    - PR-012-execute-scoped-explicit-execution-profile-v1
    - PR-015-direct-codex-development-host-invocation-bridge-v1
  current_workload_evidence:
    - PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1
~~~

## Problem

SentinelX currently discovers infrastructure defects while it is simultaneously being used as the development substrate for real repositories. Each newly exposed compatibility gap can therefore be interpreted as another immediate core-development requirement.

Without a finite baseline and an explicit exit rule, the stabilization loop is unbounded:

~~~text
real development
→ expose next missing boundary
→ create another SentinelX task
→ expose the next boundary
→ repeat
~~~

The problem is not that SentinelX must become defect-free. The problem is that there is no canonical distinction between:

1. a failure that makes the current supported development baseline unsafe or unusable; and
2. a defect, compatibility gap, optional capability or future improvement that can remain in backlog while product development continues.

## Goal

Define and implement a finite Windows Stable Baseline plus a read-back-verifiable Stabilization Exit Gate.

The gate must answer one bounded question:

> Is the current SentinelX Host sufficiently safe and functional for the declared V1 development baseline to resume normal product development?

A positive answer does not claim universal compatibility, complete feature coverage, or zero defects.

## V1 Baseline Scope

The V1 baseline is intentionally narrow.

### Platform

~~~text
Windows Host
Git/GitHub repository transport
current canonical SentinelX Agent build
current DevForge project binding
~~~

### Mandatory development capabilities

The gate must consume current Host reality for these already-defined capabilities rather than infer readiness from configuration alone:

1. authenticated/user-scoped Git execution context required by the current transport;
2. `host_mutation_sandbox_v1`;
3. `pre_execution_audit_lineage_v1`;
4. `host_runtime.scoped_verification_node_npm_v1`;
5. `canonical_repository_mutation_firewall_v1`;
6. `development_host.direct_codex_v1`;
7. real scoped Python execution as covered by the existing mutation-runtime physical probe.

The current project binding is `direct/codex`. Optional providers are not mandatory baseline dependencies unless the canonical project/task binding changes.

### Current workload proof

Because the current product-development path requires Unity 6.6, stabilization exit additionally requires one bounded real-Host Unity workload proof against the current accepted SentinelX candidate:

~~~text
Unity 6000.6.4f1
headless/batch/version initialization
no 0xC0000142 / STATUS_DLL_INIT_FAILED
contained execution
terminal authority closure verified
~~~

This is a V1 workload proof, not a promise of arbitrary Unity or arbitrary Windows GUI application compatibility.

## Required Behavior

### R1 — Single aggregate baseline projection

Expose one aggregate, read-only Stable Baseline projection derived from existing capability/readiness evidence.

Recommended feature identity:

~~~text
host_runtime.stable_baseline_v1
~~~

The projection must not become a second authority or readiness state machine.

It may summarize mandatory dependencies, but the existing low-level probes remain authoritative for their own domains.

### R2 — Reuse physical readiness; no duplicate low-level probes

The implementation must reuse existing physical readiness mechanisms, including:

- `mutation_readiness.py` for real AppContainer/ACL/Job/audit/scope execution and terminal closure;
- `verification_readiness.py` for real provider-owned Node/npm verification readiness;
- Direct Codex provider-owned containment/readiness proof;
- canonical repository firewall evidence;
- current Git execution-context capability projection.

Do not create a new probe that independently re-implements AppContainer, ACL, Job, audit, Node/npm, Git or Direct Codex readiness semantics.

A new check is permitted only when no existing authoritative evidence covers a mandatory baseline fact.

### R3 — Finite blocking taxonomy

Every observed gap relevant to stabilization must be classified into exactly one of these dispositions:

~~~yaml
baseline_blocker:
  meaning: prevents safe/reliable use of the declared V1 baseline
  blocks_exit: true

verification_required:
  meaning: mandatory baseline fact is currently unproven or stale
  blocks_exit: true
  automatic_new_feature_task: false

backlog:
  meaning: non-baseline defect, optional provider, broader compatibility, optimization or future capability
  blocks_exit: false
~~~

A finding is a `baseline_blocker` only if at least one is true:

1. a mandatory V1 capability is unavailable or physically unverified;
2. a SentinelX security/mutation boundary required by the baseline is violated or cannot prove closure;
3. an already-declared execution profile used by V1 cannot execute according to its contract;
4. required audit/receipt/read-back evidence cannot be produced;
5. the required current Unity workload proof fails on the candidate being declared stable.

Anything else is backlog by default.

### R4 — Unknown does not mean “build another feature”

Missing or stale evidence for a mandatory baseline item yields `verification_required`.

The system must not translate `verification_required` into automatic capability expansion, permission widening, new provider support, or a new development task.

The next action is evidence acquisition or recovery unless evidence identifies a concrete baseline defect.

### R5 — Stable Baseline projection semantics

The aggregate projection must distinguish at least:

~~~yaml
status: Ready | NotReady | Unverified
mandatory_checks:
  <capability-id>:
    status: verified | unavailable | unverified
blockers: []
verification_required: []
backlog_relevant: []
~~~

Rules:

- `Ready`: all mandatory live capability checks are verified for the current Host/candidate.
- `NotReady`: at least one mandatory check has concrete failing evidence.
- `Unverified`: no concrete failure is proven, but at least one mandatory fact lacks current evidence.
- optional/non-baseline failures must not change `Ready` to `NotReady`.

The projection must be deterministic from current evidence and must fail closed on malformed mandatory evidence.

### R6 — No caller authority expansion

The baseline projection is observation and classification only.

It must not let callers:

- enable disabled mutation capability;
- select AppContainer/ACL/Job authority;
- change Direct Codex sandbox policy;
- alter toolchain roots;
- bypass the canonical repository firewall;
- mark a failed check as verified;
- write a synthetic Ready state.

### R7 — Real DevForge E2E exit proof

A Stable Baseline exit claim requires more than all capability flags being green.

Before this task can be accepted as the stabilization exit, the exact candidate must complete one real DevForge development execution on the canonical task/transport lineage through the configured SentinelX development Host, with read-back-verifiable evidence for:

1. exact Task / PR / branch / admitted head;
2. implementation mutation outside canonical `main`;
3. configured Direct Codex provider/containment proof;
4. relevant tests or verification commands;
5. canonical repository firewall preservation;
6. audit lineage;
7. terminal process/Job/mutation authority closure;
8. published canonical transport result/commit;
9. DevForge execution receipt;
10. Acceptance evaluating the above evidence.

The execution of this PR may satisfy the E2E proof only if it actually traverses the configured SentinelX `direct/codex` Host path and all evidence above is independently read back. A connector-side GitHub edit alone cannot satisfy R7.

### R8 — Unity 6.6 workload proof is an acceptance gate, not a feature-expansion trigger

Acceptance must read current evidence for the bounded Unity 6000.6.4f1 initialization workload.

If the workload fails, the gate reports the concrete current failure as a baseline blocker.

It must not guess another Windows permission, broaden AppContainer authority, or create a compatibility task inside this task.

Any repair remains owned by the task that addresses that concrete defect.

### R9 — Exit receipt

Acceptance of this task must produce a durable Stabilization Exit Receipt or equivalent Acceptance evidence that binds:

- SentinelX candidate commit;
- installed Agent version/build evidence when Host verification is involved;
- mandatory baseline projection/evidence digest;
- exact E2E Task/Run/Attempt/Slice lineage;
- exact E2E canonical transport head/receipt;
- Unity workload proof reference;
- final verdict;
- zero unresolved baseline blockers;
- zero unresolved mandatory `verification_required` items.

No receipt, no stabilization-exit claim.

### R10 — Exit semantics

A successful exit means:

~~~text
SentinelX Stable Baseline V1 = sufficient for declared Windows development baseline
Stabilization Mode = may end
Normal product/game development = may resume
Non-blocking defects = backlog
~~~

It does not mean:

~~~text
all SentinelX features complete
all providers supported
all Windows applications compatible
macOS verified
no future defect can exist
no future baseline regression can occur
~~~

A later regression of a mandatory baseline capability may reopen stabilization, but backlog-only findings must not.

## Non-Goals

This task does not:

- fix PR-018 or any other independent compatibility defect inside PR-019;
- absorb PR-016/PR-017/PR-018 task ownership;
- add macOS to V1;
- require every optional provider, including CodeBuddy, when it is not the canonical project/task execution binding;
- support every shell/toolchain;
- support interactive Unity;
- guarantee arbitrary Windows GUI application compatibility;
- replace existing readiness probes;
- modify DevForge workflow semantics;
- automatically create follow-up development tasks from every failed or unknown check;
- declare SentinelX defect-free.

## Acceptance Criteria

1. one aggregate Stable Baseline V1 projection exists and is read-only;
2. it is derived from authoritative existing readiness/capability evidence;
3. mandatory V1 dependencies are explicit and finite;
4. optional/non-baseline failures do not block exit;
5. missing mandatory evidence yields `Unverified`, not synthetic failure or synthetic success;
6. concrete mandatory failure yields `NotReady` with exact blocker identity;
7. malformed mandatory evidence fails closed;
8. callers cannot set or override readiness;
9. no duplicate low-level AppContainer/ACL/Job/audit/Node/npm/Direct-Codex readiness system is introduced;
10. security/mutation closure failure always blocks exit;
11. current Direct Codex capability is physically verified;
12. current scoped mutation and audit lineage are physically verified;
13. current Node/npm verification capability is physically verified;
14. canonical repository firewall remains verified;
15. current required Git execution context is available;
16. real scoped Python path remains verified;
17. real Unity 6000.6.4f1 bounded initialization proof passes on the accepted candidate;
18. one real DevForge E2E execution through SentinelX Direct Codex has durable read-back-verifiable execution evidence;
19. E2E evidence proves canonical main was not used as the implementation workspace;
20. E2E evidence proves tests/verification and terminal authority closure;
21. Acceptance produces/read-backs the stabilization exit evidence/receipt;
22. zero baseline blockers remain;
23. zero mandatory verification-required items remain;
24. backlog-only findings do not prevent Stable Baseline V1 exit.

## Requirement Readiness

~~~yaml
requirement_ready: true
ui_semantics: NotApplicable
visual_fidelity: NotApplicable
implementation_p0_dependencies: []
acceptance_external_evidence:
  - current Windows Host physical readiness
  - current Direct Codex E2E execution evidence
  - current Unity 6000.6.4f1 workload proof
material_product_decision_pending: false
~~~
