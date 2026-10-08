# PR-014 S05A — Canonical source and secure runtime disposition

Date: 2026-10-08. Requirement R6 / Plan R11 / approved S05A only.

## Updated canonical evidence

Fresh GitHub main at `5d9286b22f46ae8bdf6d983b6366da0da3f1323e`, PR #14 task branch 138 ahead / 600 behind. The earlier S03A main snapshot `cd42e371f18056327c1d8b744f8956a76bc11541` is superseded as freshness evidence, not erased. No authoritative current-main Python source ownership or deployment/build provenance is established by GitHub metadata readback. This is **unverified**; historic PR code and installed runtime are not source ownership proof.

## Current live Host readback

Connected operational Windows Host version `0.24.1.dev260+g45dc99d15`.

Full capabilities reports:
- `locations.devforge_workspace_root=D:\coco` (legacy); **no** `locations.devforge_execution_workspace_root` binding in effective locations.
- `host_mutation_sandbox_v1.available=false, verified=false`.
- Reason: `HostMutationScopeCorrupt: invalid scope record: MutationScopeRecord.__init__() got an unexpected keyword argument 'runtime_read_authority_roots'`.
- `canonical_repository_mutation_firewall_v1.available=true, verified=true`.
- Previously read devforge_runtime contract revision 2 exposes `execute_scoped`; actual safe short-mutation consumer/use case and required separate workspace substrate remain unverified.
- Installed version is a deployment fact, not evidence of canonical GitHub main source or binary/source equality.

## Security repair contract (decision only)

- **FIRST** identify canonical implementation owner and installed package provenance, exact implementation files and modern durable-state schema; do not resurrect old PR branch files.
- **THEN** only under a new reviewed product Plan, repair backward/forward compatible MutationScope parsing for known additive `runtime_read_authority_roots`, preserve its current stored values and unknown authority-bearing field fail-closed, never reset/delete the durable store or silently widen authority.
- Independently bind protected canonical source and a Host-owned execution workspace root outside `D:\coco`; do not carve out/narrow `D:\coco` or trust caller paths, and validate audit START, AppContainer/ACL/Job and terminalization before any mutation.
- A working `execute_scoped` projection alone does not establish that new DevForge checkout materialization, source capsule or Development Host handoff belongs in minimal SentinelX. Those objectives remain HOLD per PR-021.

## Disposition

```yaml
result: DecisionRequired/Blocked
reason: CanonicalSourceOwnershipUnverifiedAndMutationScopeReadinessFailed
narrow_repair_candidate: supported_by_host_failure_but_not_implementation_authorized
source_owner: unverified
installed_package_source_mapping: unverified
short_mutation_consumer_need: unverified
independent_execution_root: missing
product_mutation_authorized: false
host_mutation_authorized: false
canonical_main_mutation_authorized: false
historical_slices_replay: forbidden
```

S05A may conclude with negative decision evidence; PR-014 product completion is NOT claimed. No Host mutation, no CI, no rebase, no broad source recovery. Preserve S01/S02/S03A/S04A receipts and historical candidate `45dc99d15a23c499b4c1500fab60ed5e76475aeb`.
