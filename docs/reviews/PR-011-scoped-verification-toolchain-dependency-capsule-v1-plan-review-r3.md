# PR-011 — Scoped Verification Toolchain & Dependency Capsule V1 — Plan Review R3

## Review State

```yaml
task_id: PR-011-scoped-verification-toolchain-dependency-capsule-v1
review_target: plan
requirement_revision: 1
task_blob_sha: cdef3e146a30189ff7c03c5b32a522bf69a7efdc
plan_revision: 3
plan_blob_sha: 048d3a56386f035cb723df18d4f55b67500bb16b
reviewed_task_head: a5ed6270df074a16681db552d561f5e5227b6d79
result: Approved
runtime:
  devforge_version: v2.36.0
  devforge_revision: fa2aa714e7c93dfe66b9cf4c7ebed414e341ab58
  project_development_workflow: "2.1"
  review_contract: "1.3"
  slicing_contract: "1.1"
next_gate: implementation
next_expected_actor: implementer
```

## Scope Reviewed

- canonical Requirement Revision 1 and durable Task state at `plan_review` / Plan Revision 3;
- canonical Plan Revision 3 plus frozen Plan Revision 2 security details incorporated by reference;
- Round-1 F1/F2 findings and Round-2 F3 finding;
- R2 remediation and R3 durable Task-state repair evidence;
- current remote `sentinelx-cloud-core/main@df9252fd4305eed361d8dc84e04da90222cd622e`;
- PR-011 ancestry: `behind_by=0`, merge-base `df9252fd...`;
- PR-007: done + merged canonical baseline;
- PR-010: accepted but unmerged; completion finalization currently blocked by Host offline;
- DevForge `main@fa2aa714e7c93dfe66b9cf4c7ebed414e341ab58` / v2.36.0.

## Decision

**Approved.**

Plan Revision 3 is implementation-shaped, scope-controlled, traceable to R1–R10, and preserves the existing SentinelX scope/AppContainer/audit authority rather than introducing a second executor or a generic Host/network escape.

No unresolved material product, architecture, transport, permission, credential, or security decision remains in the Plan.

## Finding Re-evaluation

### F1 — Source-under-test truth binding: CLOSED

The Plan binds verification to an immutable `SourceUnderTestSnapshot` containing exact repository/transport revision identity, source manifest digest and package-lock digest. Provider/broker materialization occurs into the exact workspace, and the materialized source manifest plus `package-lock.json` digest must be verified before the first profiled process can SPAWN.

This makes the verification receipt about the exact admitted source revision rather than an arbitrary script-created workspace. Wrong source head, manifest, lockfile, traversal/reparse or source tamper all have explicit negative verification paths.

### F2 — Toolchain/capsule integrity and resource bounds: CLOSED

The Plan freezes a deterministic ToolchainManifest/digest, provider-generated workspace-local launcher shims, request-time integrity verification before START and again before SPAWN, immutable dependency-capsule manifests, offline-only execution, explicit default/hard resource ceilings and partial-copy cleanup.

Execution cannot resolve a caller-selected or PATH-shadowed Host npm launcher, and cached readiness is not used as request-time integrity authority.

### F3 — Stale repository baseline / merged PR-007 dependency: CLOSED

Plan Revision 3 uses canonical `main@df9252fd...`, treats merged PR-007 `devforge_runtime.py` as baseline code, and converts the former external dependency Step E into an ordinary canonical integration step. The same PR-011 branch was ancestry-refreshed and current comparison remains `behind_by=0`.

The Plan also explicitly requires implementation-entry reread/reconciliation of PR-010 and forbids copying its unmerged implementation. PR-010 remaining unmerged therefore does not invalidate the current Plan.

## Current-Reality Assessment

### PR-010

PR-010 has advanced to `accepted / unmerged / blocked_finalization` because the Windows Host is offline. This is not a new Plan defect:

- it remains unmerged exactly as Revision 3 anticipates;
- PR-011 must reread it before every implementation mutation;
- if PR-010 merges, PR-011 must refresh ancestry and consume canonical firewall/inventory primitives;
- if it remains unmerged, PR-011 must not copy its implementation;
- no verification profile may become canonical-repository write authority.

### Windows Host availability

Host offline status is an execution/verification availability constraint, not an architecture ambiguity. Physical AppContainer/readiness/live-Agent tests have explicit observation methods and must fail closed when the Host is unavailable. No implementation success may substitute mock-only evidence for those required physical checks.

## Requirement Traceability

- R1: provider-owned logical verification profiles — policy/profile slice.
- R2: read/execute-only toolchain authority — sandbox/materialization slice.
- R3: immutable lock-bound dependency capsule — profile + materialization slices.
- R4: mutable state only inside exact workspace — sandbox/materialization slice.
- R5: no network widening — scoped execution + physical verification.
- R6: reuse existing scoped executor/scope/audit — sandbox/execution/integration slices.
- R7: merged canonical `devforge_runtime.execute_scoped` integration — final integration slice.
- R8: bounded evidence + separately gated readiness — audit/readiness/integration slices.
- R9: migration/base-runtime compatibility — regression checks across all slices.
- R10: downstream PR-015 proof — Acceptance evidence boundary under separate PR-015 authority, not PR-011 mutation authority.

## Slice Compilation Guidance

The approved implementation decomposition should preserve these meaningful verification boundaries:

1. pure policy/contracts and deterministic manifest/admission logic;
2. audit + sandbox pre-SPAWN materialization and transient ACL closure;
3. scoped Node/npm environment and real offline execution semantics;
4. readiness/capability/docs plus real Windows physical verification;
5. canonical `devforge_runtime` schema/adapter integration and live Agent readback.

The cross-repository ChatGPTControlShell PR-015 proof is **not** a PR-011 implementation Slice because PR-011 does not own authority to mutate or complete that Task. It remains a required Acceptance evidence input when separately authorized and available.

## Gate Result

```text
Plan Review: Approved
Plan Revision: 3
Implementation Authorized: pending exact Slice Set durable read-back
Execution Slice Set: required before Task transition
```

No implementation Slice is executed by this review.
