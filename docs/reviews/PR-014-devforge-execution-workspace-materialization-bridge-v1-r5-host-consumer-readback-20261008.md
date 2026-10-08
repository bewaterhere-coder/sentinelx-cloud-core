# PR-014 — Requirement R5 Host/Consumer Reality Readback

2026-10-08; read-only SentinelX and GitHub connector observation.

## Canonical repository
- `bewaterhere-coder/sentinelx-cloud-core main@cd42e371f18056327c1d8b744f8956a76bc11541`.
- PR #14 existing branch is 116 commits ahead / 598 behind, no approved merge. Historical S03A readback established critical product paths absent on main.
- Current canonical implementation ownership and a merge-safe authoritative product source tree remain **unresolved**. Do not restore from PR branch or assume package lineage based on its code.

## Actual Host evidence
- Connected operational Windows host `Cherie_li`, label `windows`, agent version `0.24.1.dev260+g45dc99d15` (version read back from `sentinel_list_hosts` and `sentinel_capabilities`).
- `sentinel_local_api.list` shows one builtin endpoint `devforge_runtime`, contract revision 2.
- `sentinel_local_api.describe(devforge_runtime)` exposes six bounded actions: `provision_scope`, `revalidate_scope`, `inspect_scope`, `terminalize_scope`, `execute_scoped`, `materialize_workspace`.
- A **real candidate short-mutation consumer surface** therefore exists: `execute_scoped` declares closed `scoped_mutation` profile, `scope_ref`, semantic repository and lineage, interpreter/content, and optional bounded execution fields. Actual invocation/application need, policy effectiveness, filesystem placement and behavior remain **unproven**.
- `materialize_workspace` is still projected by installed legacy S02-version runtime. Its exposure does **not** authorize using it as the R5 target or establish adherence to PR-021.
- Capability summary: 57 commands, 2 locations, 4 file_ops paths, 3 writable paths; summary does not disclose exact protected/placement root values. Effective policy values and durable MutationScope compatibility are **unverified**; no live mutation/provision invoked.

## Disposition
```yaml
canonical_implementation_source_owner: unresolved
actual_host_runtime: observed
short_mutation_api_surface: observed_execute_scoped
short_mutation_consumer_necessity: unproven
new_devforge_workspace_substrate_need: unproven
legacy_long_agent_materialization: hold
product_mutation: forbidden
task_decision: DecisionRequired/Blocked
```

Any follow-on Plan must first establish the owner of the canonical *current* implementation, read effective host policy and a proven short-operation use case; only then decide between **NoAdditionalProductDeltaNeeded** versus a narrow approved security delta. No product code modification until a separate review, no replay of S01/S02 candidate `45dc99d15a23c499b4c1500fab60ed5e76475aeb`.
