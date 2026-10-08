# PR-014 R6 — Source ownership and security-runtime decision

Decision class: **RECONCILIATION_FIRST / NO PRODUCT MUTATION**.

Evidence: approved S04A readback `docs/execution/PR-014-devforge-execution-workspace-materialization-bridge-v1-s04a-readback-20261008.md`, prior completed negative S03A, GitHub main `cd42e371f18056327c1d8b744f8956a76bc11541` and PR #14 mergeability=false.

## Frozen disposition

1. **Canonical source ownership is unresolved.** Main lacks the historic Python implementation files. Before restoring anything, read the current main tree and provenance/history, release/build publication mappings, and installed runtime package origin. The installed version `0.24.1.dev260+g45dc99d15` and old PR branch are not equivalent proof of current canonical source ownership. If source ownership cannot be proved, stop at `DecisionRequired` and choose an explicit reviewed owner/source repair separate from product changes.
2. **Actual runtime security readiness is failing.** Installed Host reports `host_mutation_sandbox_v1=false` and `pre_execution_audit_lineage_v1=false` with `MutationScopeRecord.__init__ unexpected runtime_read_authority_roots`. Record preservation is mandatory. Repair must target schema-compatible read/migration after a canonical implementation baseline is identified, preserve known additive authority values, and fail closed on unknown authority-bearing fields. No data deletion, scope widening or version downgrade as a bypass.
3. **Independent execution placement is not admitted.** Host still projects `locations.devforge_workspace_root=D:\coco`; new separate execution root `locations.devforge_execution_workspace_root` is missing. Never remove or carve out `D:\coco` protection. A future Host-owned independent root outside protected/canonical areas requires separately reviewed policy deployment and physical readback; no caller path authority.
4. **Short-mutation consumer:** builtin `devforge_runtime.execute_scoped` exists in local API contract rev 2 but no demonstrated safe consumer/need for a new workspace materialization path. Without concrete evidence of a missing bounded capability, prefer `NoAdditionalProductDeltaNeeded`/HOLD rather than reconstructing full checkout or Development Host handoff.
5. **Sequence:** (a) read-only source provenance and current product ownership, (b) read-only installed schema/effective Host config and consumer contract, (c) decision receipt selecting no-delta or narrowly scoped security repair, (d) *new* Reviewed Plan for any product/Host change, (e) focused tests/real Host receipt. No S01/S02 replay, cherry-pick, broad rebase, generic shell or long Agent loop.

## Security and scope invariants

Retain PR-021 minimal short-operation runtime boundary, canonical main + clean, independent Host bindings, MutationScope fail-closed state, audit START, AppContainer/Job, canonical repository firewall and No Receipt No Completion Claim. PR #14 stays the transport; historical S01/S02/S03A/S04A are evidence only. No product/Host/main mutation is authorized by this decision.

Result: `DecisionRequired / Blocked pending canonical source ownership and security repair authorization`.
