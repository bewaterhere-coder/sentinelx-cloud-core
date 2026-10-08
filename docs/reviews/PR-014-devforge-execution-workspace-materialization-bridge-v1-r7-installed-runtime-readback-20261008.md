# PR-014 R7 — Updated installed runtime readback

Date: 2026-10-08. Read-only Host capability FULL result, no Host product mutations.

Canonical main GitHub SHA: `5d9286b22f46ae8bdf6d983b6366da0da3f1323e`; PR branch divergent (142 ahead, 600 behind). Installed operational Windows Host: `0.24.1.dev791+g5d9286b22`. Version suffix matches canonical main commit prefix but precise package build provenance and canonical source tree ownership still require readback.

## New facts
- `host_mutation_sandbox_v1`: available=true, verified=true, all Windows AppContainer/ACL/Job/audit/scope checks passed.
- `pre_execution_audit_lineage_v1`: available=true, verified=true, audit before resume verified.
- Historical `runtime_read_authority_roots` error is **not observed on the new runtime's self-check**. This does not yet prove every historical durable record migration or permit destructive repair.
- `canonical_repository_mutation_firewall_v1`: available=false, verified=false; `reason=local_api:direct_codex_containment_unproven`; uncovered class `local_api:direct_codex_containment_unproven`.
- `devforge_workspace_root=D:\coco` remains legacy location and does not establish independent Host-owned execution placement outside `D:\coco`; a dedicated execution-root binding is not shown in effective location readback.
- Local API surface changed from legacy `devforge_runtime` revision 2 to revision 1; `devforge_direct_codex` revision 1 now exposed. Direct Codex containment must not be inferred from mere exposure.

## Current decision
```yaml
result: DecisionRequired/Blocked
previous_mutation_scope_failure: not_observed_in_new_self_check
sandbox_and_audit_readiness: PASS
canonical_firewall_readiness: FAIL
new_blocker: local_api:direct_codex_containment_unproven
separate_execution_root_admitted: unverified
canonical_source_build_provenance: unverified
product_mutation_authorized: false
host_mutation_authorized: false
canonical_main_mutation_authorized: false
```

Required next phase: read-only verify current main source ownership/build mapping, direct_codex containment contract and canonical mutation firewall policy projection, and independent execution root. Do not invoke Direct Codex, scoped mutations or workspace materialization while firewall fails. Preserve S01-S05A evidence; do not replay. No weakening or carve-out of `D:\coco` protection, no caller-select workspace, no durable scope deletion.
