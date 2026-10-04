# PR-010 — SentinelX Provider Canonical Repository Mutation Firewall V1 — Plan Review R1

## Review State

```yaml
task_id: PR-010-canonical-repository-mutation-firewall-v1
review_target: plan
plan_revision: 1
result: Rejected
classification: plan_local
reviewed_task_head: b7de40dc2e16f35959f4ef147c89c40b1c18a788
planning_baseline_main: f7e878f3497582547e5d52cd33b060cae18d2e84
next_gate: plan_review_rejected
next_expected_actor: planner
implementation_authorized: false
```

## Decision

**Rejected.** The security direction is correct, Requirement traceability is strong, and the Plan correctly refuses shell/script text heuristics as physical enforcement. Two plan-local P0 gaps remain before implementation can be authorized.

No Requirement semantic change is required. Both findings can be repaired within the existing Task and PR transport.

## Blocking Findings

### F1 — Provider-wide capability coverage has no fail-closed operation classification source of truth

**Classification:** `plan_local`

Requirement R7 and the DevForge consumer contract require `canonical_repository_mutation_firewall_v1` to disappear whenever any exposed model-facing mutation surface is outside enforcement.

Current SentinelX `build_registry()` is the runtime source of truth for exposed Agent operations, but it currently stores only `op -> handler`. `capabilities.ops_supported` is intentionally derived from the registry because hand-maintained operation lists have already drifted. There is no current registry metadata that classifies an operation as read-only, structured mutation, process mutation, internal-only, or firewall-covered.

Plan V1 says readiness is composed from "registered operation coverage" and that an uncovered mutator removes the capability, but it does not define the durable mechanism that makes a newly registered mutation-capable op fail closed by default. A separately hand-maintained firewall list would recreate the exact drift class the registry comments say SentinelX already eliminated for `ops_supported`.

**Required correction:** Plan Revision 2 must make operation-effect classification part of the authoritative operation registration/readiness path, or define an equivalently fail-closed mechanism with this invariant:

```text
new model-facing op is registered
AND its mutation/read-only effect class is missing or unknown
→ canonical_repository_mutation_firewall_v1 readiness = false
```

The mechanism must distinguish internal-only transport operations from model-facing operations and must not require every read-only op to carry mutation enforcement.

### F2 — Exact dependency readback is scheduled after an earlier slice may touch overlapping files

**Classification:** `plan_local`

The Requirement correctly says any implementation touching `client.py`, `handlers/basic.py`, `handlers/scoped_script.py`, `mutation_scope.py` or equivalent overlap must re-read the exact latest PR-007/PR-008 heads first.

Plan V1 places the explicit active-branch reconciliation admission under S04, but S03 covers profiled/scoped script execution and may need to modify `handlers/scoped_script.py` or related capability/process seams before S04 runs. That ordering contradicts P0-C and could transplant stale semantics.

The risk is live, not hypothetical: PR-007 has advanced since Task creation and is currently at head `82876e92eb41394c85337aea1573b6d435faf590`, while PR-008 remains at `f7594c468d764ad85c0dc508ad47f009c89793c1`.

**Required correction:** move exact dependency-head/readback reconciliation to an entry gate that executes before the first slice that may touch an overlapping file. This can be a global implementation-entry gate or per-slice admission; it must not wait until S04 if S03 can touch the overlap.

## Non-Blocking Review Notes

### N1 — Canonical inventory separation is sound

The Plan correctly keeps canonical repository identity distinct from generic `protected_roots` and from caller-supplied repository/path evidence. This satisfies the authority direction of Requirement R1.

### N2 — Generic process fail-closed semantics are acceptable for V1

The Plan's choice to block arbitrary unprofiled process execution under firewall-ready mode unless physical canonical exclusion is independently proven is consistent with R5/R6 and the DevForge contract. Compatibility is preserved because legacy hosts may retain generic process behavior only while the provider-wide firewall capability remains unavailable.

### N3 — Structured-mutator ordering is sound

For explicit-path mutation, the Plan correctly requires firewall admission before backup creation, staging finalization, patch application, metadata change, or other material side effects. The no-`.bak` incident regression is appropriately explicit.

### N4 — Current planning baseline has not drifted

Canonical `main` remains `f7e878f3497582547e5d52cd33b060cae18d2e84`; PR-010 still targets that exact base. The rejection is therefore not caused by canonical-main drift.

## Requirement Traceability Assessment

- R1/R2: **planned adequately** — Host-owned inventory plus one reusable classifier/admission seam are explicit.
- R3/R4: **planned adequately** — structured filesystem/Git mutation ordering and regressions are explicit.
- R5/R6: **planned adequately** — arbitrary process mutation cannot rely on string heuristics and must fail closed or use existing scoped physical containment.
- R7: **not yet implementation-ready** — provider-wide completeness is stated, but the authoritative fail-closed operation classification mechanism is underspecified (F1).
- R8/R9/R10: **planned adequately**, subject to dependency-order repair in F2 for overlapping implementation seams.

## Gate Result

```text
Plan Review R1: Rejected
Plan Revision: 1
Plan Approved: false
Implementation Authorized: false
Next Gate: plan_review_rejected
Next Actor: planner
```

## Required Next Command

```text
#开发计划修复 PR-010-canonical-repository-mutation-firewall-v1
```
