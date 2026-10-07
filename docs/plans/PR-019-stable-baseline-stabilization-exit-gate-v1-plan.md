# PR-019 SentinelX Stable Baseline & Stabilization Exit Gate V1 — Plan R1

## Status

~~~yaml
task_id: PR-019-stable-baseline-stabilization-exit-gate-v1
plan_revision: 1
plan_status: ready_for_review
implementation_authority: false
requirement_ref: docs/requirements/PR-019-stable-baseline-stabilization-exit-gate-v1.md
requirement_revision: 1
transport:
  type: github-pr
  pr_number: 19
  branch: task/stable-baseline-stabilization-exit-gate-v1
  base: main
repository_baseline:
  main_sha: 1028030b33f0ea792a884491a431fffe566f6aa5
~~~

## Objective

Implement the smallest Stable Baseline aggregation/classification layer over existing SentinelX readiness evidence, then use real PR-019 DevForge execution evidence plus current Windows/Unity evidence to decide whether stabilization may end.

This Plan does not repair unrelated blockers. A concrete failure discovered during verification is classified and returned to its owning task.

## Technical Decision

Add a pure aggregation module, recommended at:

~~~text
src/sentinelx_core/stable_baseline.py
~~~

Expose its sanitized result through:

~~~text
capabilities.execution_features["host_runtime.stable_baseline_v1"]
~~~

Architecture:

~~~text
existing physical readiness/providers
  -> sanitized execution feature projections
  -> stable_baseline pure composer
  -> host_runtime.stable_baseline_v1
  -> DevForge Acceptance + E2E receipts + Unity workload evidence
  -> Stabilization Exit Receipt
~~~

The composer owns no Host mutation, no permission admission, no external execution, no durable Ready flag, and no second readiness cache.

## Frozen Mandatory Predicates

### B1 — Git execution context

host_runtime.git_execution_context_v1 must have:

~~~yaml
available: true
context_class: user_scoped
non_interactive: true
credential_material_exposed: false
operations:
  contains: [fetch, push]
~~~

The deprecated Git alias is not an independent baseline dependency.

### B2 — Scoped mutation runtime

host_mutation_sandbox_v1 must have:

~~~yaml
available: true
verified: true
platform: windows_appcontainer_v1
self_check: verified
checks.runtime_read_execute: true
checks.terminal_non_active: true
checks.residual_authority_absent: true
~~~

All existing physical checks remain authoritative.

### B3 — Audit lineage

pre_execution_audit_lineage_v1 must remain bound to host_mutation_sandbox_v1 and carry the same verified physical readiness.

### B4 — Node/npm verification

host_runtime.scoped_verification_node_npm_v1 must have:

~~~yaml
available: true
verified: true
platform: windows_appcontainer_v1
self_check: verified
profile_id: node_npm
toolchain_kind: node_npm_v1
toolchain_digest: non_empty
~~~

### B5 — Canonical repository mutation firewall

canonical_repository_mutation_firewall_v1 must have:

~~~yaml
available: true
verified: true
inventory_ready: true
effective_surface_ready: true
platform_supported: true
uncovered_classes: []
~~~

### B6 — Direct Codex development host

development_host.direct_codex_v1 must have available=true and verified=true.

Its existing provider-owned containment proof remains authoritative, including real Codex workspace-write setup, workspace containment, protected-root refusal and process-tree closure.

### B7 — Platform

The Host must be Windows. Other platforms are outside V1 and cannot report this V1 projection Ready.

## Result Model

The composer returns a deterministic shape containing:

~~~yaml
available: true
verified: true
status: Ready
baseline_id: windows_dev_v1
mandatory_checks: {}
blockers: []
verification_required: []
~~~

Classification:

- concrete false/failing authoritative evidence -> NotReady + baseline_blocker;
- missing/malformed/stale mandatory evidence without concrete failure -> Unverified + verification_required;
- optional features are not consumed and cannot block V1.

No provider-private paths, credentials, raw ACLs or unrelated internal evidence may be projected.

## S01 — Pure composer and classification tests

Likely files:

~~~text
src/sentinelx_core/stable_baseline.py
tests/test_stable_baseline.py
~~~

Implement immutable baseline requirements and pure composition logic.

Required tests:

1. all mandatory predicates satisfied -> Ready;
2. concrete mandatory unavailability -> NotReady with exact blocker;
3. mandatory feature absent -> Unverified;
4. malformed mandatory mapping -> Unverified;
5. mutation available but unverified -> NotReady;
6. Node/npm profile/toolchain evidence missing -> Unverified;
7. firewall inventory/effective-surface failure -> NotReady;
8. Direct Codex unverified -> NotReady;
9. Git missing push -> NotReady;
10. credential exposure true -> NotReady;
11. deprecated Git alias cannot satisfy the canonical check;
12. optional unavailable feature does not alter Ready;
13. no provider path/credential projection;
14. composer performs no mutation or external I/O.

S01 does not change existing low-level readiness modules.

## S02 — Capabilities integration and regressions

Likely files:

~~~text
src/sentinelx_core/handlers/basic.py
tests/test_stable_baseline.py
tests/test_capabilities_policy_evidence.py
tests/test_verification_readiness.py
tests/test_devforge_runtime_local_api.py
~~~

Refactor handle_capabilities only as required to:

1. build existing canonical execution features once;
2. pass the sanitized mapping to the composer;
3. append host_runtime.stable_baseline_v1;
4. preserve every existing feature ID and meaning;
5. preserve Direct Codex/firewall/mutation/verification probe ownership;
6. preserve disabled-op semantics;
7. prevent recursive self-consumption.

Focused verification must prove the projection changes only with authoritative dependency evidence and no caller can supply or override readiness.

## S03 — Current Host, E2E and Unity exit evidence

S03 performs evidence/verification only. It must not widen product authority to make the gate pass.

Before S03 re-read the current PR-019 head, Approved Plan/Slice Set, current main, installed SentinelX Agent build, current capabilities(full), current Unity evidence, and completed PR-019 execution receipts.

### A. Live projection

Require:

~~~text
host_runtime.stable_baseline_v1.status = Ready
~~~

plus exact mandatory dependency evidence.

### B. Real PR-019 DevForge execution lineage

At least one PR-019 implementation Slice must have traversed the configured SentinelX direct/codex Host and provide read-back-verifiable evidence binding:

- PR-019 Task / branch / admitted head;
- Run / Attempt / Slice;
- provider direct, adapter codex;
- provider-owned containment;
- isolated implementation mutation;
- tests/verification;
- deterministic commit/publish;
- canonical PR head read-back;
- terminal process/Job/authority closure.

Planning-time GitHub connector writes do not satisfy this E2E requirement.

### C. Repository safety

Prove implementation did not use canonical main as mutation workspace, the canonical repository firewall stayed verified, no unverified mutation surface was introduced, and no residual provider workspace authority remains.

### D. Unity V1 workload

Read current real-Host proof for Unity 6000.6.4f1 headless/batch/version initialization.

Require:

- raw outcome is not 0xC0000142 / STATUS_DLL_INIT_FAILED;
- deterministic initialization success;
- AppContainer/Job containment preserved;
- terminal authority closure proven.

Absent Unity proof -> verification_required.
Concrete Unity failure -> baseline_blocker.

PR-019 must not repair the failure; repair remains with its owning task.

### E. Exit classification

The only Ready exit is:

~~~yaml
baseline_live_projection: Ready
e2e_devforge_execution: verified
unity_workload: verified
unresolved_baseline_blockers: []
unresolved_verification_required: []
backlog_findings: allowed
exit_verdict: Ready
~~~

Any other result blocks the exit claim but does not automatically authorize feature expansion.

## Acceptance / Exit Receipt

Development Acceptance must evaluate:

1. Requirement Revision 1;
2. exact Approved Plan and Slice Set;
3. implementation/test receipts;
4. live baseline projection;
5. exact PR-019 Direct Codex E2E lineage;
6. current Unity V1 workload evidence;
7. security/authority closure.

Approved Acceptance must durably bind equivalent evidence:

~~~yaml
kind: sentinelx_stabilization_exit_receipt
baseline_id: windows_dev_v1
candidate_commit: <exact candidate>
host_agent_version: <observed>
baseline_projection_digest: <digest>
e2e:
  task_id: PR-019-stable-baseline-stabilization-exit-gate-v1
  run_id: <observed>
  attempt_id: <observed>
  slice_id: <observed>
  canonical_head: <observed>
unity_workload_ref: <observed evidence>
baseline_blockers: []
verification_required: []
verdict: Ready
~~~

This is workflow evidence, never caller-writable runtime state.

## Verification Strategy

Unit/integration verification covers the composer, capabilities projection, mutation readiness, verification readiness, canonical firewall, Direct Codex readiness, and devforge_runtime regressions.

CI-only success cannot satisfy S03. Real Host evidence is required for AppContainer readiness, Node/npm readiness, Direct Codex containment/setup, PR-019 E2E publish, Unity workload, and terminal authority closure.

## Slice Proposal

Plan Review should compile exactly:

~~~text
S01 — Stable Baseline composer + classification unit coverage

S02 — capabilities integration + regression coverage

S03 — exact current Host baseline projection
      + PR-019 Direct Codex E2E receipt reconciliation
      + Unity V1 workload evidence
      + stabilization-exit evidence
~~~

Each explicit #开发执行 remains bounded by normal DevForge one-Slice semantics.

## Cross-Task Ownership

PR-019 may consume PR-018 evidence but must not modify PR-018 Requirement/Plan/Slice state, execute PR-018 repairs, mark PR-018 complete, or widen Unity authority because S03 is red.

PR-016/PR-017 likewise remain independently owned. Their existence alone is not a baseline blocker; only current mandatory V1 evidence determines the gate.

## Concurrent Reconciliation

Before every Slice:

- re-read PR-019 head and current main;
- re-read overlapping open PRs touching handlers/basic.py, readiness modules or operation registry;
- preserve PR #19 branch/transport identity;
- stop on material overlap that changes a mandatory predicate or readiness ownership.

PR-019 remains based on canonical main and is not stacked on another task by default.

## Risks

### RSK-1 — Aggregate becomes a second readiness authority

Mitigation: pure composer over existing sanitized authoritative projections; no low-level probes, state store or cache.

### RSK-2 — Ready is mistaken for bug-free

Mitigation: baseline ID and finite predicates are explicit; backlog findings do not block exit.

### RSK-3 — Missing evidence creates another feature project

Mitigation: verification_required is first-class and explicitly does not authorize capability expansion.

### RSK-4 — E2E is faked by planning-time connector writes

Mitigation: Acceptance requires a real implementation Slice through SentinelX Direct Codex with provider-owned receipts.

### RSK-5 — Unity expands PR-019 scope

Mitigation: S03 only classifies/read-backs Unity evidence; repair remains with the concrete owning task.

### RSK-6 — Git feature cannot publish

Mitigation: V1 requires both fetch and push in the user-scoped execution context.

## Plan Review Questions

1. Is host_runtime.stable_baseline_v1 correctly modeled as a pure projection rather than new authority?
2. Are B1-B7 minimum sufficient predicates for the current Windows/direct-Codex baseline?
3. Is Git push correctly mandatory for the current PR transport?
4. Is S03 correctly separated from PR-018 repair ownership?
5. Does Acceptance enforce No Receipt, No Stabilization Exit without moving DevForge workflow semantics into SentinelX?
