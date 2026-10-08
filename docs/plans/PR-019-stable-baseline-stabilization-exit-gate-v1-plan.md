# PR-019 SentinelX Stable Baseline & Stabilization Exit Gate V1 — Plan R2

## Status

~~~yaml
task_id: PR-019-stable-baseline-stabilization-exit-gate-v1
plan_revision: 2
plan_status: ready_for_review
implementation_authority: false
requirement_ref: docs/requirements/PR-019-stable-baseline-stabilization-exit-gate-v1.md
requirement_revision: 1
prior_plan_revision: 1
rejected_review_ref: docs/reviews/PR-019-stable-baseline-stabilization-exit-gate-v1-plan-review-r1.md
transport:
  type: github-pr
  pr_number: 19
  branch: task/stable-baseline-stabilization-exit-gate-v1
  base: main
repository_baseline:
  main_sha: 1028030b33f0ea792a884491a431fffe566f6aa5
~~~

## R2 Remediation Delta

Plan R2 preserves Requirement Revision 1 and repairs only the three Plan Review R1 findings.

### F1 resolved — exact PR-019 candidate activation is explicit

PR-019 changes SentinelX Agent code, so source/CI success cannot prove the live Windows service runs the same bytes.

R2 reuses the canonical PR-015 activation pattern:

~~~text
exact candidate commit
→ install exact ref into C:\ProgramData\SentinelX\.venv using the existing Windows SentinelX pip install workflow
→ restart SentinelX service
→ reconnect and read live Agent version/build
→ require deterministic binding to the exact candidate
→ only then consume live capabilities/readiness
~~~

Rules:

- never install moving main;
- freeze exact candidate identity before activation;
- activation is external Host/operator evidence, not GitHub connector evidence;
- if current provider security boundaries cannot mutate the installed runtime, S03 pauses for the existing operator installation workflow rather than adding self-update authority;
- Host policy is not silently changed by activation;
- install/restart/version mismatch fails closed;
- rollback uses the same existing installation workflow to restore the previously observed known-good exact Agent build, followed by restart and version read-back;
- no stabilization-exit claim is allowed until candidate identity and live version are independently read back.

### F2 resolved — Direct Codex Git readiness follows the actual transport primitive

Plan R1 incorrectly treated host_runtime.git_execution_context_v1 as mandatory Direct Codex transport evidence.

R2 removes that generic feature as an independent blocker for the direct/codex baseline.

The actual Direct Codex path is authoritative:

~~~text
direct_codex_transport.transport_git
→ run_user_scoped_git
→ active interactive Windows user token
→ fixed provider-owned Git argv
~~~

R2 extends the existing Direct Codex physical readiness proof with one bounded, non-network, non-repository-mutating Git execution-context probe using the same primitive, for example a provider-owned git --version invocation rooted at the derived workspace.

Sanitized projection may add:

~~~yaml
transport_context:
  kind: user_scoped_git_v1
  probe_attempted: true
  verified: true
  non_interactive: true
  credential_material_exposed: false
~~~

This proves only that the actual active-user Git primitive can start. It does not claim remote GitHub authentication/publication.

Exact remote read/fetch/publish authority is proven only by the real Direct Codex E2E receipt in S03, where the provider performs canonical branch read, independent checkout acquisition, deterministic commit, ordinary fast-forward push and independent remote read-back.

The generic host_runtime.git_execution_context_v1 feature remains visible for its own contract but does not decide the Direct Codex Stable Baseline.

### F3 resolved — cause-aware Unverified versus NotReady

R2 does not infer failure from a top-level boolean alone.

Mandatory checks resolve to:

~~~yaml
verified:
  baseline_disposition: verified

verification_required:
  baseline_disposition: Unverified
  blocks_exit: true
  defect_proven: false

baseline_blocker:
  baseline_disposition: NotReady
  blocks_exit: true
  defect_proven: true
~~~

Required classification examples:

~~~text
Direct Codex proof not yet attempted
or containment_unproven without failed-attempt evidence
→ Unverified / verification_required

Direct Codex real sandbox setup attempted and failed
→ NotReady / baseline_blocker

mandatory Host policy explicitly disabled
→ NotReady / baseline_blocker

mandatory projection missing/malformed with no concrete failed probe
→ Unverified / verification_required

firewall unproven only because a mandatory provider proof is pending
→ Unverified / verification_required

firewall concrete uncovered/unsafe mutation class
→ NotReady / baseline_blocker

Unity evidence absent/stale
→ Unverified / verification_required

Unity current real probe concretely fails
→ NotReady / baseline_blocker
~~~

Where an existing provider collapses not-yet-proven and attempted-failure into the same reason, R2 permits the minimum sanitized evidence repair inside that provider. This evidence is observational only and does not become a second authorization state machine.

## Objective

Implement the smallest Stable Baseline aggregation/classification layer over existing SentinelX readiness evidence, add only the minimum Direct Codex evidence needed for cause-aware readiness, then use real PR-019 DevForge execution plus exact-candidate Windows/Unity evidence to decide whether stabilization may end.

A failure found by S03 is classified and returned to its owning task. PR-019 does not broaden permissions to make the gate green.

## Technical Decision

Recommended new pure module:

~~~text
src/sentinelx_core/stable_baseline.py
~~~

Recommended live projection:

~~~text
capabilities.execution_features["host_runtime.stable_baseline_v1"]
~~~

Architecture:

~~~text
existing physical probes/providers
  ├─ host_mutation_sandbox_v1
  ├─ pre_execution_audit_lineage_v1
  ├─ scoped_verification_node_npm_v1
  ├─ canonical_repository_mutation_firewall_v1
  └─ development_host.direct_codex_v1
       ├─ containment / real Codex sandbox proof
       └─ actual user-scoped Git primitive context proof
        ↓
stable_baseline.py
pure predicate validation + cause-aware classification
        ↓
host_runtime.stable_baseline_v1
        ↓
exact-candidate Host activation/read-back
+ real Direct Codex remote E2E receipt
+ Unity workload evidence
        ↓
DevForge Acceptance / Stabilization Exit Receipt
~~~

The composer owns no Host mutation, permission admission, external execution, durable Ready flag, second readiness cache, or automatic follow-up Task creation.

## Frozen V1 Live Mandatory Predicates

### B1 — Scoped mutation runtime

host_mutation_sandbox_v1 must prove available=true, verified=true, platform=windows_appcontainer_v1, self_check=verified, runtime_read_execute=true, terminal_non_active=true and residual_authority_absent=true.

A returned physical probe failure is a concrete blocker. Missing/malformed aggregate evidence without a failed probe is Unverified.

### B2 — Audit lineage

pre_execution_audit_lineage_v1 must remain bound to host_mutation_sandbox_v1, carry the same verified physical readiness, and preserve START/SPAWN/FINISH plus terminal authority closure.

### B3 — Node/npm verification

host_runtime.scoped_verification_node_npm_v1 must prove available=true, verified=true, platform=windows_appcontainer_v1, self_check=verified, profile_id=node_npm, toolchain_kind=node_npm_v1 and non-empty toolchain_digest.

Explicit missing mandatory profile/toolchain configuration or an attempted physical verification failure is NotReady. Merely absent/stale aggregate evidence is Unverified.

### B4 — Canonical repository mutation firewall

canonical_repository_mutation_firewall_v1 must ultimately prove available=true, verified=true, inventory_ready=true, effective_surface_ready=true, platform_supported=true and uncovered_classes empty.

Cause-aware handling:

- pending/unproven mandatory provider proof only → Unverified;
- concrete unknown/uncovered/unsafe mutation surface → NotReady.

### B5 — Direct Codex + actual Git execution context

development_host.direct_codex_v1 must ultimately prove available=true, verified=true and:

~~~yaml
transport_context:
  kind: user_scoped_git_v1
  verified: true
  non_interactive: true
  credential_material_exposed: false
~~~

The provider proof remains authoritative for real Codex workspace-write setup, workspace containment, protected-sibling refusal, Job/process closure and exact derived workspace.

The generic host_runtime.git_execution_context_v1 feature is not an independent B5 prerequisite.

### B6 — Platform

The Host must be Windows. Other platforms are outside windows_dev_v1.

## Remote Git Transport Proof Boundary

The live aggregate projection does not claim remote publication authority from a local Git-context probe.

For GitHub PR transport, S03 E2E must independently prove:

~~~text
exact canonical branch remote-head read
→ independent checkout acquisition/fetch
→ Direct Codex implementation
→ provider-owned deterministic commit
→ ordinary fast-forward push
→ independent remote-head read-back
~~~

Concrete remote read/auth/push failure during the exact E2E run is a baseline blocker.

No current-candidate E2E attempt, or stale E2E evidence for another candidate, is verification_required.

## Result Model

Recommended projection:

~~~yaml
available: true
verified: true
status: Ready
baseline_id: windows_dev_v1
mandatory_checks:
  host_mutation_sandbox_v1:
    status: verified
  pre_execution_audit_lineage_v1:
    status: verified
  host_runtime.scoped_verification_node_npm_v1:
    status: verified
  canonical_repository_mutation_firewall_v1:
    status: verified
  development_host.direct_codex_v1:
    status: verified
    transport_context: verified
blockers: []
verification_required: []
~~~

Rules:

- Ready requires all live B1-B6 checks verified;
- NotReady requires at least one concrete mandatory failure;
- Unverified means no concrete failure is proven but required evidence is missing, stale or not yet physically attempted;
- if both Unverified and concrete blockers exist, top-level status is NotReady while both lists stay explicit;
- optional failures do not alter the result;
- malformed mandatory evidence is Unverified unless independently valid concrete failure evidence is present.

## Cause-Aware Direct Codex Evidence

Current Direct Codex readiness can lose the distinction between not yet proven and proof attempted but failed.

R2 permits the minimum repair to expose sanitized probe disposition:

~~~yaml
proof:
  attempted: false
  disposition: not_attempted
transport_context:
  probe_attempted: false
  verified: false
~~~

After a failed physical attempt:

~~~yaml
proof:
  attempted: true
  disposition: failed
  failure_class: <bounded provider-owned reason>
~~~

No raw paths, credentials, command output, full ACL or provider-private data are projected.

This is process-local observation only; it does not authorize execution or replace E2E/Acceptance receipts.

## S01 — Direct Codex evidence repair + Stable Baseline composer

Likely files:

~~~text
src/sentinelx_core/handlers/direct_codex.py
src/sentinelx_core/stable_baseline.py
tests/test_direct_codex_provider.py
tests/test_direct_codex_execution.py
tests/test_stable_baseline.py
~~~

S01.1 extends the existing Direct Codex physical readiness lifecycle with one fixed non-network user-scoped Git context probe using the same run_user_scoped_git / transport_git primitive.

Constraints:

- provider-owned argv only;
- no caller input;
- no network;
- no repository mutation;
- no credential projection;
- bounded timeout;
- exact derived workspace context;
- sanitized pass/failure evidence only.

S01.2 preserves sanitized not_attempted / failed / verified physical-probe disposition without adding durable authority.

S01.3 implements immutable B1-B6 predicates and cause-aware classification.

Required tests:

1. all B1-B6 verified → Ready;
2. mandatory projection absent → Unverified;
3. malformed mandatory projection without concrete failure → Unverified;
4. mutation physical probe concrete failure → NotReady;
5. Node/npm mandatory profile explicitly absent → NotReady;
6. Node/npm aggregate evidence missing → Unverified;
7. Direct Codex containment_unproven with attempted=false → Unverified;
8. Direct Codex real sandbox setup attempted and failed → NotReady;
9. Direct Codex policy explicitly disabled → NotReady;
10. actual user-scoped Git context probe pending → Unverified;
11. actual user-scoped Git context probe attempted and failed → NotReady;
12. generic host_runtime.git_execution_context_v1 disabled does not itself block a verified Direct Codex baseline;
13. firewall pending solely on Direct Codex proof → Unverified;
14. firewall concrete uncovered mutation class → NotReady;
15. optional unavailable features do not change Ready;
16. no provider path/credential/raw ACL projection;
17. composer performs no mutation or external I/O.

## S02 — Capabilities integration + regressions

Likely files:

~~~text
src/sentinelx_core/handlers/basic.py
tests/test_stable_baseline.py
tests/test_capabilities_policy_evidence.py
tests/test_verification_readiness.py
tests/test_devforge_runtime_local_api.py
tests/test_direct_codex_provider.py
~~~

Refactor handle_capabilities only as required to:

1. build existing sanitized execution-feature projections once;
2. consume B1-B6;
3. append host_runtime.stable_baseline_v1;
4. preserve existing feature IDs and meanings;
5. preserve Direct Codex/firewall/mutation/verification ownership;
6. preserve disabled-op semantics;
7. prevent recursive self-consumption;
8. prevent generic authenticated-Git policy from becoming an accidental Direct Codex dependency;
9. preserve cause-aware classification.

No Host policy is changed by S02.

## S03 — Exact candidate activation + live Host + E2E + Unity exit evidence

S03 is evidence/verification work and must not widen product authority.

### S03.A Freeze exact product candidate

Before activation:

- identify exact PR-019 product candidate after S01/S02 product code;
- distinguish later DevForge control-artifact commits from product bytes;
- require no post-candidate product drift;
- bind candidate SHA into S03 checkpoint.

### S03.B Exact-candidate Windows activation

Reuse the existing PR-015 pattern:

~~~text
observe current known-good installed Agent version
→ install exact PR-019 candidate ref into C:\ProgramData\SentinelX\.venv using existing Windows pip install workflow
→ restart SentinelX
→ reconnect
→ read live Agent version/build
→ require deterministic candidate binding
~~~

No new Agent self-update capability is authorized.

If existing security boundaries cannot perform the install:

~~~text
S03 = blocked_external_activation
next actor = operator
same Task / same Slice identity retained
~~~

After operator activation, resume the same S03 evidence flow; do not replay S01/S02.

Failure handling:

- do not claim candidate active;
- do not consume live baseline projection;
- persist activation failure evidence;
- restore prior known-good exact Agent build with the same install workflow when needed;
- restart and read back rollback identity;
- fail closed if candidate or rollback identity cannot be proven.

### S03.C Live projection

Only after exact candidate identity is proven, read capabilities(detail=full).

Require host_runtime.stable_baseline_v1.status = Ready plus exact B1-B6 evidence.

Evidence from a different Agent build is invalid.

### S03.D Real PR-019 Direct Codex remote E2E

At least one PR-019 implementation Slice must have traversed configured SentinelX direct/codex and must bind:

- PR-019 Task / PR / branch / admitted remote head;
- Run / Attempt / Slice;
- provider direct / adapter codex;
- containment and actual user-scoped Git context proof;
- isolated workspace;
- tests/verification;
- provider-owned deterministic persistence;
- ordinary fast-forward publication;
- independent remote read-back;
- terminal process/Job/authority closure.

Concrete remote Git failure is NotReady. No current-candidate E2E attempt is verification_required.

Planning-time GitHub connector writes do not satisfy this proof.

### S03.E Repository safety

Prove canonical main was not used as implementation workspace, firewall stayed verified, no unverified mutation surface remained, no residual provider workspace authority remained, and the canonical checkout is main + clean when that checkout is part of the live environment.

### S03.F Unity workload

Consume current real-Host Unity 6000.6.4f1 headless/batch/version evidence.

~~~text
absent/stale/different-candidate evidence
→ verification_required / Unverified

current exact-candidate probe concretely fails
→ baseline_blocker / NotReady

current exact-candidate probe succeeds with containment + closure
→ verified
~~~

PR-019 never widens Unity authority or guesses another permission.

### S03.G Exit classification

The only Ready exit is:

~~~yaml
exact_candidate_activation: verified
baseline_live_projection: Ready
direct_codex_remote_e2e: verified
unity_workload: verified
unresolved_baseline_blockers: []
unresolved_verification_required: []
backlog_findings: allowed
exit_verdict: Ready
~~~

## Acceptance / Stabilization Exit Receipt

Development Acceptance must evaluate:

1. Requirement Revision 1;
2. Approved Plan and exact Slice Set;
3. S01/S02 implementation/test receipts;
4. exact product candidate SHA;
5. exact-candidate Windows install/restart/version read-back;
6. live B1-B6 projection;
7. exact PR-019 Direct Codex remote E2E lineage;
8. current Unity workload;
9. security/authority closure.

Approved evidence must bind equivalent data:

~~~yaml
kind: sentinelx_stabilization_exit_receipt
baseline_id: windows_dev_v1
candidate_commit: <exact product candidate>
host_agent_version: <observed exact build>
activation:
  install_ref: <candidate>
  restart_verified: true
  live_identity_verified: true
baseline_projection_digest: <digest>
e2e:
  task_id: PR-019-stable-baseline-stabilization-exit-gate-v1
  run_id: <observed>
  attempt_id: <observed>
  slice_id: <observed>
  admitted_remote_head: <observed>
  published_head: <observed>
  remote_readback_verified: true
unity_workload_ref: <observed>
baseline_blockers: []
verification_required: []
verdict: Ready
~~~

No Receipt, No Stabilization Exit.

## Verification Strategy

Focused tests cover Direct Codex readiness/probe disposition, actual user-scoped Git context, Stable Baseline composer, capabilities projection, mutation readiness, Node/npm readiness, canonical firewall and devforge_runtime regressions.

CI-only evidence cannot satisfy S03.

Real Host evidence is required for exact candidate activation/version read-back, physical AppContainer readiness, Node/npm readiness, Direct Codex real sandbox setup, actual user-scoped Git context, PR-019 remote read/fetch/publish/read-back, Unity workload and terminal authority closure.

## Slice Proposal

Plan Review should compile exactly:

~~~text
S01 — Direct Codex cause-aware/actual Git-context readiness evidence
      + Stable Baseline pure composer
      + unit coverage

S02 — capabilities integration
      + affected regression coverage

S03 — freeze exact product candidate
      + existing Windows exact-ref activation/restart/version read-back
      + live Stable Baseline projection
      + PR-019 Direct Codex remote E2E reconciliation
      + Unity V1 workload evidence
      + stabilization-exit evidence
~~~

One explicit #开发执行 remains bounded by normal one-Slice semantics.

S03 may pause at the external operator activation boundary without changing Slice identity. Resume continues S03 evidence acquisition and does not replay S01/S02.

## Cross-Task Ownership

PR-019 may consume PR-018 evidence but must not mutate PR-018 Requirement/Plan/Slice state, execute PR-018 repairs, mark PR-018 complete, or widen Unity authority because S03 is red.

PR-016/PR-017 remain independently owned.

An open Task/PR is not itself a baseline blocker; only current mandatory V1 evidence is authoritative.

## Concurrent Reconciliation

Before each Slice:

- re-read PR-019 head and current main;
- re-read overlapping open PRs touching handlers/basic.py, handlers/direct_codex.py, readiness modules or operation registry;
- preserve PR #19 branch/transport identity;
- stop on material overlap changing predicates/readiness ownership;
- preserve Direct Codex provider contract and deterministic persistence semantics.

Before S03 additionally re-read installed Host Agent version and current PR-018 Unity evidence.

## Risks

### RSK-1 — Composer becomes a second authority
Mitigation: pure sanitized evidence composition only.

### RSK-2 — Ready is interpreted as defect-free
Mitigation: finite windows_dev_v1 identity and explicit backlog semantics.

### RSK-3 — Missing evidence becomes another feature project
Mitigation: cause-aware verification_required and no automatic Task creation.

### RSK-4 — Generic authenticated-Git policy creates a false Direct Codex blocker
Mitigation: actual run_user_scoped_git primitive is provider-owned evidence; remote authority remains E2E-owned.

### RSK-5 — Local Git-context probe is mistaken for remote publication proof
Mitigation: local context and remote E2E are separate mandatory evidence surfaces.

### RSK-6 — Live evidence comes from wrong Agent bytes
Mitigation: exact-ref install, restart and live version binding before capabilities consumption.

### RSK-7 — Self-host activation deadlock causes permission bypass
Mitigation: reuse existing external/operator install workflow; no self-update authority.

### RSK-8 — Failed proof is misclassified as unknown
Mitigation: sanitized not_attempted / failed / verified provider disposition.

### RSK-9 — Unity failure expands PR-019
Mitigation: classify only; repair remains with owning Task.

## Plan Review Questions

1. Does exact-candidate activation close the source/CI-to-live-Host identity gap without self-update authority?
2. Does Direct Codex Git readiness observe the actual user-scoped Git primitive?
3. Is local Git-context readiness correctly separated from remote fetch/push E2E proof?
4. Does cause-aware classification preserve Requirement R3-R5 Unverified versus NotReady semantics?
5. Does S03 remain evidence-only for PR-018/Unity repair ownership?
6. Does Acceptance enforce exact candidate + live projection + remote E2E + Unity + closure before Stabilization Exit?
