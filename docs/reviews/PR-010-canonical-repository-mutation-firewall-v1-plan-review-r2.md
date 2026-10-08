# PR-010 — SentinelX Provider Canonical Repository Mutation Firewall V1 — Plan Review R2

## Review State

```yaml
task_id: PR-010-canonical-repository-mutation-firewall-v1
review_target: plan
plan_revision: 2
result: Approved
reviewed_task_head: bb4eadab487bdd56ff16f317a8296177787c2b82
planning_baseline_main: f7e878f3497582547e5d52cd33b060cae18d2e84
current_main_at_review: f7e878f3497582547e5d52cd33b060cae18d2e84
next_gate: implementation
next_expected_actor: implementer
implementation_authorized: true
```

## Decision

**Approved.** Plan Revision 2 closes both blocking findings from Review R1 without weakening Requirement semantics, introducing a second operation inventory, or allowing stale dependency state to authorize overlapping mutation.

Approval authorizes implementation only through the compiled durable Execution Slice Set. It does not authorize Acceptance, merge, release, production Host activation, DevForge modification, unrestricted process fallback, caller-owned canonical inventory, generic `canonical_sync`, or mutation of a local canonical checkout.

## R1 Finding Closure

### F1 — Provider-wide capability coverage lacked a fail-closed operation-classification source of truth

**Status: Closed by Plan Revision 2.**

Current canonical SentinelX reality uses `handlers.build_registry()` as the dispatch truth, and `capabilities.ops_supported` is derived from that registry specifically to avoid hand-maintained drift. Revision 2 now preserves that architectural property while extending the authoritative registration seam with operation exposure, repository-effect class, and firewall-coverage semantics.

The required fail-closed invariant is explicit:

```text
new model-facing op registered
AND repository effect missing/unknown
→ firewall readiness false
→ canonical_repository_mutation_firewall_v1 not advertised
```

Revision 2 also handles the non-trivial registry cases that Review R1 required:

- internal-only transport operations are explicitly distinct from model-facing operations;
- read-only operations are explicitly distinguishable from mutators and do not need fake mutation enforcement;
- mixed operations such as structured Git classify mutation selectors rather than exempting the whole operation because one selector is read-only;
- `disabled_ops` affects the effective dispatch surface before final readiness accounting;
- required-but-unproven firewall coverage fails provider-wide readiness.

This is implementation-shaping and testable, rather than a best-effort documentation list.

### F2 — Dependency readback was scheduled after a Slice could already touch overlapping files

**Status: Closed by Plan Revision 2.**

Revision 2 moves dependency reconciliation to a per-Slice **pre-mutation** admission rule. Before any Slice changes a file overlapping PR-007/PR-008 semantics, execution must re-read the exact current dependency head, changed-file set, relevant contract/artifact revision, and dependency stage, then persist a no-loss composition decision.

The rule now applies before S03 touches `handlers/scoped_script.py`, `handlers/basic.py`, `client.py`, mutation-scope code or equivalent profiled-execution/capability seams. S02 is also covered when its registry changes overlap PR-007 `handlers/__init__.py` semantics. S04 repeats reconciliation on later drift.

The need is confirmed by live review-time movement:

```yaml
pr_007:
  head: d7dd47d1ad253e62c8c8ad5b194c9f94cfc536d3
  state: implementation
  moving: true
pr_008:
  head: f7594c468d764ad85c0dc508ad47f009c89793c1
  state: acceptance
```

These values are observations only. The approved Plan explicitly forbids treating planning/review-time SHAs as later implementation authority.

## Review Checks

### Solution direction

**Pass.** Host-owned canonical repository inventory is distinct from `file_ops rw`, generic `protected_roots`, execution workspace identity, and caller-provided repository/path claims.

### Scope control

**Pass.** V1 is limited to provider-side canonical exclusion, readiness/advertisement, incident regression and documentation. It does not add a generic canonical-sync escape hatch, a second mutation-scope store, a second audit system, or Hub-owned deployment behavior.

### Technical feasibility

**Pass.** Structured mutators already centralize path resolution/dispatch sufficiently for a central classifier to compose with them. Generic process surfaces are not falsely claimed safe; V1 may fail-close arbitrary unprofiled process mutation under firewall-ready mode rather than inventing shell-string parsing as a security boundary.

### Risk handling

**Pass.** The Plan addresses over-blocking through explicit firewall-ready mode, prevents partial capability advertisement, requires admission before backups/material side effects, and treats moving dependency conflict as a Decision Boundary rather than silent transplantation.

### Requirement traceability

**Pass.** R1–R10 map to S01–S05 and the verification matrix. Provider-wide completeness, physical process exclusion, no-backup-on-block, broad-parent-rw non-override, workspace separation and fake-canonical-sync rejection all have observable verification paths.

### Behavioral verification

**Pass.** Acceptance evidence includes real Windows process/child behavior and the canonical incident family; internal flags or string parsing are not accepted as proxies for physical exclusion.

## Implementation Entry Evidence

Review-time repository facts:

```yaml
canonical_main: f7e878f3497582547e5d52cd33b060cae18d2e84
pr_010_reviewed_head: bb4eadab487bdd56ff16f317a8296177787c2b82
pr_007_observed_head: d7dd47d1ad253e62c8c8ad5b194c9f94cfc536d3
pr_008_observed_head: f7594c468d764ad85c0dc508ad47f009c89793c1
```

Current overlap evidence includes:

```text
PR-007:
  src/sentinelx_core/client.py
  src/sentinelx_core/handlers/__init__.py
  src/sentinelx_core/handlers/basic.py
  src/sentinelx_core/handlers/mutation_scope.py
  src/sentinelx_core/handlers/scoped_script.py
  src/sentinelx_core/mutation_scope.py

PR-008:
  src/sentinelx_core/executor.py
  src/sentinelx_core/handlers/basic.py
  src/sentinelx_core/handlers/scoped_script.py
```

The Execution Slice Set therefore carries dynamic dependency reconciliation as an implementation admission rule, not a one-time review fact.

## Execution Authorization

Plan Review R2 authorizes compilation/execution of the durable slices in:

`docs/execution/PR-010-canonical-repository-mutation-firewall-v1-slices.yaml`

Execution remains bounded and incremental:

1. S01 — canonical inventory and central admission seam;
2. S02 — authoritative operation-effect registry and structured mutator integration;
3. S03 — process mutation fail-closed boundary;
4. S04 — capability readiness and projection composition;
5. S05 — incident regression, security suite and documentation.

One manual `#开发执行` invocation may complete at most one Slice. Each Slice must satisfy its own dependency-overlap entry gate before product-code mutation.

## Gate Result

```text
Plan Review R2: Approved
Plan Revision: 2
Plan Approved: true
Implementation Authorized: true
Next Gate: implementation
Next Actor: implementer
```

## Next Command

```text
#开发执行 PR-010-canonical-repository-mutation-firewall-v1
```
