# PR-010 — SentinelX Provider Canonical Repository Mutation Firewall V1 — Plan Review R3

## Review State

```yaml
task_id: PR-010-canonical-repository-mutation-firewall-v1
review_target: plan
requirement_revision: 2
plan_revision: 3
result: Rejected
classification: plan_local
reviewed_task_head: 90a22a0b14c83ef695796b70bde403b7e8ce37c9
planning_baseline_main: f7e878f3497582547e5d52cd33b060cae18d2e84
next_gate: plan_review_rejected
next_expected_actor: planner
implementation_authorized: false
```

## Decision

**Rejected.** Requirement Revision 2 and Plan Revision 3 correctly move PR-010 to a Core-owned security and verification boundary, treat `mcp.sentinelx.app` as immutable third-party transport, retain S01 without replay, remove PR-009 as a completion dependency, and preserve fail-closed process semantics.

Two plan-local P0 gaps remain before implementation can resume. Neither requires a Requirement change, Hub modification, permission expansion, or rollback of retained S01 implementation.

## Blocking Findings

### F1 — `local_api` endpoint/action effects are not covered by the authoritative provider-wide effect model

**Classification:** `plan_local`

Requirement R7/R8 and the DevForge consumer contract require firewall readiness to be false whenever any effective model-facing operation has unknown repository mutation effect or required-but-unproven coverage.

Current Core reality makes `local_api` a material case, not a hypothetical future operation:

- `handlers.build_registry()` conditionally exposes `local_api` as a model-facing Agent operation;
- configured `local_api` actions can call arbitrary Host-local HTTP/JSON-RPC endpoints declared by operator YAML;
- `local_api` also has a `run_as` relay path that can spawn a helper process under another local identity;
- PR-007 Requirement/Plan Revision 2/3 intends to add built-in `devforge_runtime` lifecycle and scoped execution under the same `local_api` operation.

Plan Revision 3 makes operation registration the authoritative coverage source and explicitly handles mixed structured Git selectors, but it does not define equivalent endpoint/action-level effect semantics for `local_api`.

An op-level classification is insufficient unless it fails closed for every configured/built-in endpoint/action combination. Marking all `local_api` as `non_repository_mutation` would be unsound; marking the whole op permanently `unknown` would make the firewall capability unavailable on the exact Hosts where PR-007 exposes `devforge_runtime`, defeating the intended composition.

**Required correction:** Plan Revision 4 must make mixed-operation coverage generic enough to classify `local_api` endpoint/action effects, with an invariant equivalent to:

```text
local_api is effectively exposed
AND any configured or built-in endpoint/action has missing/unknown repository effect
→ canonical_repository_mutation_firewall_v1 readiness = false
```

For `devforge_runtime.execute_scoped`, coverage may compose the existing scoped execution/sandbox/audit authority rather than duplicate it. Existing external local APIs must be explicitly classified or remain fail-closed for firewall readiness; operator configuration alone must not implicitly prove `non_repository_mutation`.

S02/S03/S04 entry/verification must include this surface where relevant. PR-007 remains an exact-readback overlap dependency before changing `local_api`, registry, scoped execution, or capability semantics.

### F2 — S01 completion does not require compatibility verification for existing `RepositoryIdentity` consumers

**Classification:** `plan_local`

Requirement R2 correctly requires one provider repository identity semantic. Plan D1 permits modifying `sentinelx_core.mutation_placement.RepositoryIdentity` or extracting a shared primitive, and S01 explicitly tests credential stripping, authority/port behavior, `.git`, traversal, and invalid identities.

However `RepositoryIdentity.canonical` already participates in mutation placement, scope binding/digests, scoped execution, readiness, and Windows sandbox composition. A semantic change can therefore alter existing repository binding behavior outside the new firewall tests.

The current S01 completion rule requires only the shared identity semantic plus focused S01 unit verification. That is insufficient for a shared security primitive before S02 proceeds.

**Required correction:** S01 verification must include focused compatibility/regression coverage for existing identity consumers, at minimum the current mutation-placement / mutation-scope / scoped-script binding paths that depend on `RepositoryIdentity.canonical`. The Plan need not run the entire repository suite in S01, but it must prove that the identity repair does not silently change valid existing scope/repository binding semantics or stored digest expectations without an explicit compatibility decision.

## Non-Blocking Review Notes

### N1 — Immutable Hub boundary is correct

Requirement R2 / Plan R3 correctly treat the Hub as transport-only. Missing Hub `execution_profile`, dynamic-tool, or capability rendering is external diagnostic information and not PR-010 implementation/verification/Acceptance authority when required Core-owned evidence exists.

### N2 — Requirement Change Invalidation is correct

Plan R2 approval and Revision-2 slice authorization are correctly invalidated as current authority while retaining historical review evidence and already-landed S01 source implementation. No verified work is replayed or rolled back.

### N3 — Core process fail-closed direction is sound

The Plan correctly refuses shell/script/path-string heuristics as physical proof and requires arbitrary unprofiled process mutation to be blocked, physically constrained through existing authority, or to keep firewall readiness unavailable.

### N4 — Authoritative registry direction is sound

Using the dispatch/effective exposure registration as the coverage source avoids a parallel hand-maintained firewall operation list. F1 extends this same principle to mixed operation selectors/endpoints; it does not replace the design.

### N5 — Dependency reconciliation is correctly placed

PR-007 and PR-008 remain exact-readback overlap dependencies before mutation of shared Core seams. PR-009 is correctly independent/non-blocking unless a future exact changed-file readback proves a direct code conflict.

### N6 — Canonical main has not drifted

Canonical `main` remains `f7e878f3497582547e5d52cd33b060cae18d2e84`; the review rejection is plan-local, not caused by main drift.

## Requirement Traceability Assessment

- R1: **planned adequately** — Host-owned canonical inventory remains distinct from generic protected/workspace roots.
- R2: **direction correct, verification incomplete** — one shared identity semantic is required, but existing consumer compatibility must be part of S01 completion (F2).
- R3-R6: **planned adequately** — reusable classifier, structured mutation ordering, Git coverage, and Core-owned process fail-closed semantics are explicit.
- R7-R8: **not implementation-ready** — authoritative coverage is defined for operations and mixed Git selectors but does not yet close `local_api` endpoint/action effects (F1).
- R9-R11: **planned adequately**, subject to F1 because PR-007's `devforge_runtime` is intentionally delivered through `local_api`.

## Gate Result

```text
Plan Review R3: Rejected
Requirement Revision: 2
Plan Revision: 3
Plan Approved: false
Implementation Authorized: false
Next Gate: plan_review_rejected
Next Actor: planner
```

## Required Next Command

```text
#开发计划修复 PR-010-canonical-repository-mutation-firewall-v1
```
