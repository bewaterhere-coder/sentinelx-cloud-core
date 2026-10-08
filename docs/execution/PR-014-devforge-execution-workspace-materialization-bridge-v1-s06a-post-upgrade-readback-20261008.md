# PR-014 S06A — Post-upgrade read-only security/placement readback

Requirement R7 / Approved Plan R12 / S06A. No product or Host mutation.

## Current identity

- GitHub canonical main: `5d9286b22f46ae8bdf6d983b6366da0da3f1323e`.
- Existing PR #14 branch: ahead 150, behind 600; historic branch not authority for canonical current main.
- Connected Windows Host version: `0.24.1.dev791+g5d9286b22`; version prefix agrees with main but exact build provenance and source ownership are not proven.

## Live bounded Host readback

- `host_mutation_sandbox_v1`: available=true, verified=true; AppContainer/ACL/Job/scope/audit checks all true.
- `pre_execution_audit_lineage_v1`: available=true, verified=true; audit-before-resume checked.
- Earlier `runtime_read_authority_roots` parse failure: not observed on the installed updated runtime self-check; historical record not deleted.
- `canonical_repository_mutation_firewall_v1`: available=false, verified=false; `effective_surface_ready=false`, reason `local_api:direct_codex_containment_unproven`.
- `devforge_direct_codex` builtin projection rev 1, feature `development_host.direct_codex_v1`, describe readiness `available=false, verified=false`, `reason=direct_codex_containment_unproven`. `execute_task` is projected with closed structured repository/lineage/development/transport fields, **but was not invoked**; projection does not prove confinement.
- Effective locations: legacy `devforge_workspace_root=D:\coco`, config at `C:\ProgramData\SentinelX\config.yaml`. Independent Host-owned `devforge_execution_workspace_root` not exposed/verified; `D:\coco` protected-root separation cannot be asserted.
- No approved live bounded short-mutation consumer or evidence that a new full workspace materializer is required.
- Current-main Python product-source provenance unresolved (earlier branch/main mismatch); no restore, cherry-pick or rebase.

## Decision

```yaml
result: DecisionRequired/Blocked
reason: DirectCodexContainmentUnprovenAndIndependentPlacementNotAdmitted
sandbox_audit: PASS
mutation_scope_old_parse_failure: not_observed
canonical_firewall: FAIL
direct_codex_readiness: FAIL
independent_execution_root: unverified
canonical_source_provenance: unverified
product_mutation_authorized: false
host_mutation_authorized: false
canonical_main_mutation_authorized: false
```

The next disposition must be a separately reviewed, ownership-bound security remediation focused on `direct_codex_containment_unproven` and provider-owned placement only if demonstrably necessary. PR-021's no-long-Agent-host-lifecycle boundary remains controlling. Repeating the expired MutationScope repair is not justified by current self-check. No product completion claim, no S01-S05A replay, no protected-root carve-out.
