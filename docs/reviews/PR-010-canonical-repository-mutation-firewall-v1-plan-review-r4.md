# PR-010 — SentinelX Provider Canonical Repository Mutation Firewall V1 — Plan Review R4

## Review State

```yaml
task_id: PR-010-canonical-repository-mutation-firewall-v1
review_target: plan
requirement_revision: 2
plan_revision: 4
result: Approved
reviewed_task_head: 72267bdc2803bb9a0ea91aa782ffdc880e77d212
planning_baseline_main: f7e878f3497582547e5d52cd33b060cae18d2e84
current_main_at_review: f7e878f3497582547e5d52cd33b060cae18d2e84
next_gate: implementation
next_expected_actor: implementer
implementation_authorized: true
```

## Decision

**Approved.** Plan Revision 4 closes both plan-local findings from Review R3 while preserving Requirement Revision 2, the immutable third-party Hub boundary, Core-owned verification authority, retained S01 implementation, and fail-closed provider-wide mutation semantics.

Approval authorizes implementation only through the durable Revision-4 Execution Slice Set. It does not authorize Acceptance, merge, release, production Host activation, Hub modification/deployment, unrestricted execution, permission expansion, generic `canonical_sync`, or mutation of a canonical checkout.

## R3 Finding Closure

### F1 — `local_api` endpoint/action effects were outside provider-wide coverage

**Status: Closed.**

Revision 4 generalizes authoritative effect accounting from a flat top-level op classification into an operation plus bounded Core-owned suboperation model. Mixed operations now require a fail-closed suboperation classifier. The Plan explicitly covers:

```text
git       -> operation selector
local_api -> endpoint + action
```

The required invariant is explicit:

```text
effective model-facing op/suboperation
AND repository effect is missing/unknown
→ canonical_repository_mutation_firewall_v1 readiness = false
```

`local_api` is not globally assumed safe because it is structured. `list`/`describe` are separately read-only; `call` resolves endpoint/action effect. Configured external endpoint/actions default to `unknown` unless a bounded Core-validated effect contract exists. Operator naming/configuration is not security proof. `run_as`/relay process behavior participates in coverage accounting. PR-007 `devforge_runtime.execute_scoped`, when present, may compose the existing scoped execution/sandbox/audit authority instead of duplicating it.

This closes the provider-wide gap without creating a second hand-maintained firewall operation list.

### F2 — Shared `RepositoryIdentity` compatibility verification was incomplete

**Status: Closed.**

S01 now requires focused compatibility evidence for existing consumers of repository identity semantics, including:

- mutation placement repository binding;
- mutation-scope repository/semantic binding and digest behavior;
- scoped-script repository binding;
- relevant Windows mutation-sandbox identity behavior.

If the shared normalization repair changes an existing valid repository/scope binding or persisted digest expectation, S01 must stop at a Decision Boundary and persist an explicit compatibility/migration decision. It cannot silently proceed to S02.

## Review Checks

### Requirement lineage

**Pass.** Review is against Requirement Revision 2 and Plan Revision 4. Prior R2 approval is retained only as historical evidence and is not reused as authority.

### Immutable Hub boundary

**Pass.** No Slice requires source/schema/deployment/tool/capability-rendering changes to `mcp.sentinelx.app`. Missing Hub projection remains external diagnostic information only when equivalent Core-owned verification is available.

### Provider-wide effect completeness

**Pass.** The authoritative dispatch/effective-exposure path remains the coverage source of truth. Unknown top-level operations and unknown nested selectors/actions mechanically remove readiness.

### Process fail-closed semantics

**Pass.** Arbitrary process mutation cannot coexist with advertised firewall readiness without physical exclusion. Shell/script/path-string parsing is not accepted as proof, and unrestricted/allowlist-expansion fallback remains forbidden.

### Dependency reconciliation

**Pass.** PR-007 and PR-008 remain exact-readback overlap dependencies at each relevant Slice entry. Review-time observations are not later mutation authority.

At review time:

```yaml
pr_007:
  head: 221c7b870e9305847a94b7d947a870dbe6aa28ab
  stage: implementation
  overlap_observed:
    - src/sentinelx_core/client.py
    - src/sentinelx_core/handlers/__init__.py
    - src/sentinelx_core/handlers/basic.py
    - src/sentinelx_core/handlers/mutation_scope.py
    - src/sentinelx_core/handlers/scoped_script.py
    - src/sentinelx_core/mutation_scope.py
pr_008:
  head: f7594c468d764ad85c0dc508ad47f009c89793c1
  stage: acceptance
  overlap_observed:
    - src/sentinelx_core/executor.py
    - src/sentinelx_core/handlers/basic.py
    - src/sentinelx_core/handlers/scoped_script.py
```

PR-007 moved after Plan R4 remediation, which confirms the need for dynamic per-Slice reconciliation. The movement does not invalidate the Plan because stale dependency SHAs are explicitly forbidden as implementation authority.

### Slice boundaries

**Pass.** One manual `#开发执行` invocation remains bounded to at most one Slice. S01 retains already-landed implementation without replay, S02 introduces authoritative top-level/nested effect accounting, S03 closes process/mixed-operation physical disposition, S04 composes Core readiness/protocol output, and S05 freezes incident/security/documentation evidence.

## Gate Result

```text
Plan Review R4: Approved
Requirement Revision: 2
Plan Revision: 4
Plan Approved: true
Implementation Authorized: true
Next Gate: implementation
Next Slice: S01
Next Actor: implementer
```

## Next Command

```text
#开发执行 PR-010-canonical-repository-mutation-firewall-v1
```
