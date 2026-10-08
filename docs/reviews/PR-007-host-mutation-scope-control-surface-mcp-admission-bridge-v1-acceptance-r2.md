# PR-007 — Host Mutation Scope Control Surface & MCP Admission Bridge V1 — Acceptance R2

## Decision

```yaml
task_id: PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1
requirement_revision: 2
plan_revision: 4
acceptance_revision: 2
result: Rejected
finding_classification: repair_local
blocking_finding: A10DocumentationContractDrift
canonical_transport: github-pr
pr_number: 7
canonical_branch: task/host-mutation-scope-control-surface-mcp-admission-bridge-v1
evaluated_head: 0af330cd85a258c2b5d7316993f09ecb4e249bb8
current_stage: fixing
gate_transition: acceptance_to_fixing
acceptance_approved: false
completion_verified: false
```

**PR-007 Acceptance R2: Rejected.**

The revised Agent-owned execution path is functionally and security-wise proven, including real model-facing `sentinel_local_api` execution on the exact Windows candidate. Acceptance is blocked only by A10: operator/help documentation still contains Revision-1 transport truth and does not fully describe the current built-in `devforge_runtime` path.

This finding is `repair_local`. Requirement Revision 2, Plan Revision 4, S06-S08 implementation evidence, canonical transport, and the immutable-Hub architecture remain valid. No requirement or architecture revision is required.

## Runtime / Transport Consistency

PASS.

- DevForge Runtime source of truth: `bewaterhere-coder/DevForge main@7c62f4e2a4ec9d8d22ab6e9c538a269118e95c7c`.
- Acceptance Contract: `contracts/development/acceptance-contract.md` v1.5.
- Canonical repository: `bewaterhere-coder/sentinelx-cloud-core`.
- Canonical PR: #7.
- Canonical branch: `task/host-mutation-scope-control-surface-mcp-admission-bridge-v1`.
- Evaluated head: `0af330cd85a258c2b5d7316993f09ecb4e249bb8`.
- Canonical main remains `f7e878f3497582547e5d52cd33b060cae18d2e84`.
- S06, S07 and S08 completion evidence is on the same canonical Task transport.

No TransportDrift is present.

## Requirement Change Guard

PASS.

Requirement Revision 2 explicitly invalidated the old generic-Hub `mutation_scope` projection objective while retaining S01-S04 as verified prerequisites. Plan Revision 4 is the current approved plan. S05 and Acceptance R1 remain historical Revision-1 evidence and are not reused as current acceptance authority.

## Fresh Verification

### Canonical CI

PASS.

Current PR head `0af330cd85a258c2b5d7316993f09ecb4e249bb8` has:

- `ci` run `37036447660`: success;
- `macos-agent` run `37036447710`: success.

### Live runtime freshness

PASS.

Acceptance-time readback shows:

- Agent version `0.24.1.dev70+gf11491fd4`, matching exact product candidate `f11491fd48199f2dbe958f4dcd54caf1d39d9c5a`;
- `local_api` remains present in `ops_supported`;
- Windows `host_mutation_sandbox_v1` remains `available=true, verified=true`;
- pre-execution audit lineage remains `available=true, verified=true`;
- Host `disabled_ops` remains empty and direct Python was not allowlisted by PR-007.

The S08 terminal scope and live `devforge_runtime` evidence remain current; Acceptance does not replay scoped mutation side effects.

## Acceptance Matrix

### A1 / R1 — PASS

`MutationScopeStore` remains the single provider authority. S06 confirms no duplicate scope store or lifecycle authority was introduced.

### A2 / R2,R4 — PASS

Provider-only provisioning and same-Attempt idempotency are covered by the focused lifecycle suite, including `test_duplicate_provision_is_idempotent_and_cannot_broaden_authority`. S06 verifier passed 62 tests.

### A3 / R2,R3 — PASS

Caller workspace/profile/operation-class authority is rejected. S07 verifies exact outer `RequestContext`, repository/lineage/generation admission, and fail-closed behavior before material mutation. S08 live evidence also observed `HostMutationScopeBindingMismatch` for mismatched attempt lineage.

### A4 / R3,R6 — PASS

Exact binding/revalidation and Windows runtime readiness remain fail closed and verified. Current Host capability readback keeps the mutation sandbox and audit lineage self-check green.

### A5 / R5 — PASS

S08 live execution returned `terminal_state=terminal`; subsequent exact `inspect_scope` returned `state=terminal`. Terminal readback did not reactivate authority.

### A6 / R7,R8 — PASS

S07 proves `execute_scoped` reuses the canonical profiled scoped handler with AppContainer/audit/Job containment, fixed `scoped_mutation`, fixed cleanup, positive response projection, and no shell/exec/Python-allowlist/operator-unrestricted/legacy fallback. Windows security regression matrix passed 15 tests.

### A7 / R9,R10,R11 — PASS

Real model-facing `sentinel_local_api` evidence on the exact known build proved:

```text
list -> describe(devforge_runtime)
-> provision_scope
-> execute_scoped
-> inspect_scope terminal
```

`describe` identified `provider_kind=builtin`, `contract_id=devforge_runtime`, `contract_revision=1`, with five bounded actions. No Hub source/schema/deployment mutation was used.

### A8 / R10,R13 — PASS

Older live Agent evidence returned `unsupported_op` for `local_api` instead of acquiring authority. S06 regression coverage proves configured external `local_apis` retain their existing semantics and an external endpoint named `devforge_runtime` wins deterministically without being shadowed by the builtin provider.

### A9 — PASS

Retained security evidence remains green: scope uniqueness, AppContainer containment, START-before-spawn, terminal closure, and `INCIDENT-20260927-D-ROOT-RECURSIVE-DELETE`. S07 Windows security suite passed 15 tests; current PR-head CI and macOS workflow are also successful.

### A10 / R11,R12 — FAIL — repair_local

The current operator/help story is inconsistent with Requirement Revision 2.

`README.md` still states:

```text
V1 relies on the existing generic Hub operation relay
```

in the `mutation_scope` section. That is Revision-1 transport semantics. Revision 2 explicitly says PR-007 completion must not rely on generic Hub projection of `mutation_scope`; the supported model-facing path is the pre-existing `sentinel_local_api` envelope plus Agent-owned builtin `devforge_runtime`.

The live Help `operations` navigation also exposes `mutation_scope` but omits `local_api` / `devforge_runtime`, so operator-visible guidance does not describe the current accepted route.

Required repair:

1. replace the stale README generic-Hub `mutation_scope` completion claim with the Revision-2 boundary: direct Agent `mutation_scope` may remain an Agent/internal compatibility surface, while model-facing development admission uses existing `sentinel_local_api -> builtin devforge_runtime` and does not require Hub changes;
2. update Help/navigation/operator-facing guidance so `local_api` is discoverable when live and clearly states that builtin `devforge_runtime` is policy-gated Agent authority behind the existing envelope;
3. add/adjust focused tests proving the new help/operator wording is present only when applicable and does not claim mutation readiness merely from dispatchability;
4. keep all existing fail-closed, collision, disabled-op, bounded-response and immutable-Hub semantics unchanged.

No new executor, scope authority, Hub schema, policy widening or runtime bypass is authorized by this repair.

### A11 / R13 — PASS

Legacy/public operations remain available. Capability remains Host-specific, and the prior incompatible Agent remained fail closed rather than inheriting capability from the upgraded Agent.

### A12 — PASS

S06 focused verifier: 62 passed + Ruff success. S07 focused verifier: Ubuntu 64 passed + Ruff success; Windows security 15 passed. Current PR head has fresh `ci` and `macos-agent` success. S01-S04 are retained rather than replayed.

### A13 / R14 — PASS

Static acceptance checks found no `Cherie_li` or `D:\\coco` deployment identity embedded in `src/`. Live host/version/path values are evidence only, not authority inputs.

### A14 / R15 — PASS

PR-008 and PR-009 remain non-blocking related work. The live PR-007 path completed without either task.

## Acceptance Result

```text
Acceptance Approved: false
Completion Verified: false
Result: Rejected
Blocking Finding: A10DocumentationContractDrift
Finding Class: repair_local
Gate Transition: acceptance -> fixing
Current Stage: fixing
```

The implementation must not be merged or marked done from this state. The canonical repair action is `#开发执行 PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1`, which must consume this Acceptance finding on the same PR/branch and then return the Task to Acceptance for a full re-check.
