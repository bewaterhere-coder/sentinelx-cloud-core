# PR-018 — SentinelX Unity 6.6 AppContainer DLL Initialization Compatibility V1 — Acceptance R1

## Decision

```yaml
task_id: PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1
requirement_revision: 1
plan_revision: 2
acceptance_revision: 1
result: Rejected
finding_classification: external_blocker
finding_code: AC18CombinedPR017S03ReplayMissing
canonical_transport: github-pr
pr_number: 18
canonical_branch: task/unity-6-6-appcontainer-dll-initialization-compatibility-v1
evaluated_head_before_acceptance_artifacts: 60220ad7910c65301ec3e2ac77f50d9291e0313e
verified_product_candidate: 73a52013055a8b3bb70b319a0ed7b7ba832ae0c9
verified_live_source_ref: 86bc881265ee3fb2ab388170a16e627caf6d723e
stacked_base_ref: 3858c7d0e46295d5e0dc184bb21e76da7c963346
current_stage: acceptance
gate_transition: not_applied
acceptance_approved: false
completion_verified: false
```

**PR-018 Acceptance R1: Rejected.**

PR-018 repository-local implementation, regression evidence, and exact real-Windows Unity proof are sufficient for Acceptance Criteria 1–17 and 19. Acceptance cannot approve because Requirement R10 / Acceptance Criterion 18 is still unsatisfied: the verified PR-018 candidate has not been integrated into the current PR-017 canonical branch, and PR-017 S03 has not been replayed against the combined candidate.

This is an `external_blocker` at the cross-Task integration boundary, not a PR-018 local implementation defect. No `acceptance -> fixing` transition is authorized. PR-018 remains at the Acceptance boundary until PR-017 integration/replay evidence exists and Acceptance is repeated.

## Runtime / Transport Consistency

PASS.

- DevForge Acceptance Contract: v1.5, current canonical blob `1c5e96a20d665e68b1f68e18b7d294945e501ec2`.
- DevForge current main observed during Acceptance: `9551d38b1d70b5bfb3f692725e8f5c70b74693a6`.
- Canonical repository: `bewaterhere-coder/sentinelx-cloud-core`.
- Canonical PR: #18, branch `task/unity-6-6-appcontainer-dll-initialization-compatibility-v1`.
- Evaluated head before Acceptance artifacts: `60220ad7910c65301ec3e2ac77f50d9291e0313e`.
- Verified product candidate: `73a52013055a8b3bb70b319a0ed7b7ba832ae0c9`.
- Compare from the verified product candidate to the evaluated head contains only Requirement / Slice / checkpoint / receipt documentation. No product or test drift is present.
- PR #18 remains open on the canonical transport.

## Requirement / Plan / Slice Guard

PASS.

- Requirement Revision 1 is current.
- Plan Revision 2 is current and Approved.
- S01, S02 and S03 are completed.
- All current Plan slices are complete.
- No PR-017 Task state, branch, Slice, or acceptance artifact was mutated by PR-018 execution.
- S03 completion receipt explicitly stops before cross-Task integration and records `pr017_s03_replayed: false`.

## Positive Acceptance Evidence

### AC1 — PASS

PR-018 is stacked on the exact reviewed PR-017 baseline `3858c7d0e46295d5e0dc184bb21e76da7c963346`.

### AC2 — PASS

S01 Variant A reproduced the exact Unity initialization failure:

```text
0xC0000142 / STATUS_DLL_INIT_FAILED
```

### AC3 — PASS

Variant B differed only by the frozen PR-011 Session-0 read authority.

### AC4 — PASS

The raw child discriminator proved the hypothesis: with the exact approved Session-0 masks Unity changed from `0xC0000142` to `0x00000000`.

### AC5 — PASS / positive-path non-applicable

The hypothesis was positive; no false-hypothesis product generalization occurred.

### AC6 — PASS

Generic compatibility is Host-owned and default off:

```yaml
runtime_session_object_read_enabled: false
```

### AC7 — PASS

Callers cannot select enablement, SID, Session, Window Station, Desktop, or access masks.

### AC8 — PASS

The effective Session-0 masks exactly equal the frozen R4 bounds:

- Window Station: `0x00020103`
- Desktop: `0x00020041`

### AC9 — PASS

Live evidence observed one non-inheriting ACE on each shared object with `flags=0`; no broader interactive/session rights were observed.

### AC10 — PASS

Real post-cleanup readback proved the exact Unity scope AppContainer SID absent from both the Window Station and Desktop.

### AC11 — PASS

Durable cleanup remains fail-closed: the binding is persisted before grant, non-null binding blocks terminal closure, restart identity mismatch remains revoked, and cleanup/readback must succeed before the marker clears.

### AC12 — PASS

The setting participates in placement/policy identity; focused tests verify digest change when the setting changes.

### AC13 — PASS

The exact real Unity probe no longer returns `0xC0000142`:

```text
0x00000000
```

### AC14 — PASS

Deterministic real Unity initialization proof passed:

```text
Unity.exe -version
stdout: 6000.6.4f1
returncode: 0
```

### AC15 — PASS

Final closure is physically and structurally proven:

- exact previous AppContainer SID absent from Window Station;
- exact previous AppContainer SID absent from Desktop;
- exact previous AppContainer SID absent from Unity runtime root;
- both proof scopes read back `terminal`;
- post-proof `host_mutation_sandbox_v1` self-check reports `terminal_non_active=true` and `residual_authority_absent=true`;
- runtime policy was restored to default-off after proof.

### AC16 — PASS

Affected PR-011 verification/security regressions remain green. Final Host readback reports `host_runtime.scoped_verification_node_npm_v1.available=true, verified=true`.

### AC17 — PASS

Affected PR-017 ACL/recovery semantics remain covered by the final candidate's Windows regression suite. The final PR-018 candidate run `37662137958` completed successfully with **88 passed**, including mutation policy, scope, Windows sandbox and scoped-execution coverage.

### AC18 — FAIL — external blocker

Requirement R10 and Acceptance Criterion 18 require:

```text
PR-018 accepted candidate
→ integrate into PR-017 canonical branch
→ replay PR-017 S03 against combined candidate
→ satisfy PR-017 S03
```

Fresh canonical PR-017 readback during this Acceptance shows:

```yaml
pr_number: 17
head: db1f29c727d619942921438cffff154f49b6b694
stage: implementation
current_slice: S03
current_slice_state: blocked
completed_slices: [S01, S02]
latest_s03_blocker: Unity child 0xC0000142
s03_completion_receipt: absent
```

Therefore no combined PR-018-on-PR-017 replay exists and AC18 is not satisfied.

Classification: `external_blocker` / `AC18CombinedPR017S03ReplayMissing`.

This is not `repair_local`: changing PR-018 product code cannot satisfy a requirement that explicitly depends on the PR-017 canonical integration/replay boundary.

### AC19 — PASS

No unrestricted or interactive-session fallback was introduced. Current Host readback confirms:

- `operator_unrestricted_enabled=false`;
- `host_mutation_sandbox_v1.verified=true`;
- `job_no_breakaway=true`;
- canonical repository mutation firewall verified.

## Current Live Host Evidence

PASS for PR-018 local behavior.

```yaml
agent_version: 0.24.1.dev484+g86bc88126
host_mutation_sandbox_v1:
  available: true
  verified: true
  runtime_session_object_read_enabled: false
scoped_verification_node_npm_v1:
  available: true
  verified: true
pre_execution_audit_lineage_v1:
  available: true
  verified: true
canonical_repository_mutation_firewall_v1:
  available: true
  verified: true
```

Temporary S03 proof authority has been removed.

## Required Recovery

Do not modify PR-018 product code merely to clear this finding.

Required cross-Task sequence:

1. Reconcile PR-017 Requirement/Plan with PR-018 as the approved compatibility dependency.
2. Integrate the verified PR-018 product candidate into the **canonical PR-017 branch** without replaying PR-017 S01/S02.
3. Replay PR-017 S03 against the combined candidate.
4. Persist PR-017 S03 completion evidence proving its R8.3 / Unity boundary is satisfied.
5. Re-run `#开发验收 PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1` and evaluate AC18 against that durable evidence.

Forbidden recovery:

- alternate PR-017 branch/PR;
- silently treating the isolated PR-018 S03 proof as PR-017 S03;
- merging PR-018 to main to bypass the stacked integration gate;
- reopening PR-018 implementation/fixing without a new local finding;
- weakening AppContainer, Job, runtime-root cleanup, or Session-0 cleanup requirements.

## Acceptance Result

```text
Acceptance Approved: false
Completion Verified: false
Result: Rejected
Finding: AC18CombinedPR017S03ReplayMissing
Finding Class: external_blocker
Gate Transition: not applied
Current Stage: acceptance
```

PR-018 must not be merged or marked done from this state.

Canonical recovery condition: PR-017 canonical branch contains the verified PR-018 compatibility candidate and PR-017 S03 has a durable successful replay receipt.

No Completion Claim.
