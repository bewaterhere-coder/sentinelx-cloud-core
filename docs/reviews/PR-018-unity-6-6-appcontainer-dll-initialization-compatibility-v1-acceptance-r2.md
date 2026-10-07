# PR-018 — SentinelX Unity 6.6 AppContainer DLL Initialization Compatibility V1 — Acceptance R2

## Decision

```yaml
task_id: PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1
requirement_revision: 1
plan_revision: 2
acceptance_revision: 2
result: Rejected
finding_classification: inconsistent_evidence
finding_code: AC16CurrentPR011ReadinessContradiction
current_stage: acceptance
gate_transition: not_applied
acceptance_approved: false
completion_verified: false
```

PR-018 Acceptance R2 is **Rejected**.

The prior R1 blocker is now cleared: Requirement R10 / Acceptance Criterion 18 is satisfied by the canonical PR-017 combined-candidate S03 completion receipt. PR-017 integrated the approved PR-018 production subset, replayed S03, and proved Unity 6000.6.4f1 returns `0x00000000` with deterministic version output `6000.6.4f1`.

A different blocker now prevents approval. PR-018 Requirement R9 / Acceptance Criterion 16 requires PR-011 verification regressions to remain green. PR-017 S03 completion recorded `scoped_verification_node_npm_v1_verified=true` for exact agent version `0.24.1.dev473+gf9e07da9c`. Later PR-017 Acceptance R2 read back that same exact agent version twice and observed `available=false`, `verified=false`, reason `Node/npm verification self-check failed (HandlerError)`.

Current required capability failure cannot be overridden by older success evidence. This is therefore `inconsistent_evidence` at the cross-Task regression boundary, not a PR-018 local implementation defect. PR-018 remains at the Acceptance boundary; no `acceptance -> fixing` transition is authorized.

## Acceptance Matrix

```yaml
AC01: pass
AC02: pass
AC03: pass
AC04: pass
AC05: pass_positive_path
AC06: pass
AC07: pass
AC08: pass
AC09: pass
AC10: pass
AC11: pass
AC12: pass
AC13: pass
AC14: pass
AC15: pass
AC16: fail_inconsistent_current_readiness
AC17: pass
AC18: pass
AC19: pass
```

## Evidence

- DevForge Acceptance Contract v1.5: `1c5e96a20d665e68b1f68e18b7d294945e501ec2`.
- PR-018 verified product candidate: `73a52013055a8b3bb70b319a0ed7b7ba832ae0c9`.
- PR-017 integrated candidate: `f9e07da9cc37f6e882c3258280869b415cafcb5c`.
- PR-017 S03 completion receipt blob: `aef10dfe56da8db7ae09aa4d47c29caa1e57b66f`.
- PR-017 Acceptance R2 receipt blob: `6cce15de869cc7ed77f42d37c8d10e13edf18e3e`.
- PR-018 product code and tests are unchanged by this Acceptance.

## Required Recovery

Do not modify PR-018 product code to clear this finding.

1. Continue PR-017 fixing and resolve the current `scoped_verification_node_npm_v1` readiness contradiction.
2. Restore or re-prove current Node/npm scoped verification without weakening AppContainer, network denial, protected-root denial, terminalization, transient-authority cleanup, Job containment, or canonical mutation firewall semantics.
3. Preserve completed PR-017 S03 Unity/cleanup evidence unless the repair materially invalidates it.
4. Re-run PR-017 Acceptance.
5. Re-run `#开发验收 PR-018-unity-6-6-appcontainer-dll-initialization-compatibility-v1`.

No Completion Claim.
