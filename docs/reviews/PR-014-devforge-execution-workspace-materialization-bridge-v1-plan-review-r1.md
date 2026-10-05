# PR-014 — SentinelX DevForge Execution Workspace Materialization Bridge V1 — Plan Review R1

## Review State

```yaml
task_id: PR-014-devforge-execution-workspace-materialization-bridge-v1
review_target: plan
requirement_revision: 1
requirement_blob_sha: c5656ab7115ac28a40882501281571a458864df4
plan_revision: 1
plan_blob_sha: 62fe1ab6643d6c6e958e5e78725a3e0ef493a34d
reviewed_task_head: 51969567c8f23c24a9d6b27bb2fca50d3e09f5cf
result: Rejected
finding_classification: plan_local
runtime:
  devforge_version: v2.41.0
  devforge_revision: 902a9d71b425753928c01904be1e9b2b60f0c3fe
  project_development_workflow: "2.1"
  review_contract: "1.3"
repository_reality:
  canonical_main: e7064c9bf4fcd15bdb6f5a2678414210c01d1c00
  pr_013:
    state: open_draft
    stage: plan_review
    head: 32cd89bdc3430596409329c676e18d36dddffc1b
    changed_files: docs_only
  pr_012: merged_done
  pr_010: merged_canonical_baseline
next_gate: plan_review_rejected
next_expected_actor: planner
```

## Scope Reviewed

- Canonical Requirement Revision 1 and Plan Revision 1 on PR #14.
- Current `sentinelx-cloud-core/main@e7064c9bf4fcd15bdb6f5a2678414210c01d1c00`.
- Current Host workspace evidence: effective DevForge root and scoped-mutation root are distinct.
- Current `WindowsMutationSandbox` exact-workspace admission behavior.
- Current DevForge `execution-workspace-materialization-contract.md` and Review Contract v1.3.
- Current PR #13 Requirement/Plan/disposition and changed-file set.
- DevForge runtime drift from v2.40.0 to v2.41.0; the changed Runtime files are deployment/production-verification surfaces and do not alter the reviewed Plan Review or execution-workspace-materialization contracts.

## Decision

**Rejected / Changes Requested.**

The Plan has the right high-level ownership direction: Host-derived DevForge placement, exact immutable source commit, provider-owned scope/audit/sandbox authority, canonical checkout preservation, exact read-back, and no generic fallback.

However, R1 still leaves three implementation-shaping authority gaps unresolved. Each can change whether the design is physically executable or whether it duplicates an active security-sensitive provider transaction path. Implementation Ready cannot be granted until they are frozen.

## Blocking Finding F1 — Placement Receipt lifecycle is not concretely preserved before scope minting

### Evidence

DevForge's canonical materialization contract is explicit:

```text
No Placement Receipt, No Workspace Materialization.
```

The canonical order is:

```text
resolve Host layout
→ compile execution placement
→ persist/retain Placement Receipt
→ verify exact target
→ provision Host-owned scope
→ revalidate scope
→ durable audit START
→ materialize
```

Plan R1 D1 says the provider resolver emits `DevforgeWorkspacePlacementEvidence`, but D3 exposes `placement_expectation` as optional and D6 only says `compare placement expectation if supplied`; D6 does not freeze durable placement-evidence retention before `provision_scope`.

An optional external comparison receipt is acceptable as non-authoritative caller evidence, but the provider still must create/retain the exact Placement Receipt required by DevForge before scope authority is minted. A post-materialization receipt cannot retroactively satisfy this precondition.

### Required remediation

Plan R2 must freeze one exact pre-materialization placement-evidence flow:

1. independently resolve current Host binding;
2. derive the deterministic DevForge target;
3. materialize a provider-owned/DevForge-compatible Placement Receipt with policy/state/operation/repository/role/target/compliance evidence;
4. if caller supplies DevForge placement evidence, compare it against the independently derived receipt and fail closed on mismatch;
5. only after the exact current receipt is retained/read back may the provider mint/revalidate the scope.

Caller path fields remain non-authoritative. This is a Plan-local sequencing clarification and does not require new Requirement semantics.

## Blocking Finding F2 — The proposed DevForge path is currently outside the Windows mutation sandbox's admitted root

### Evidence

Plan R1 intentionally keeps these Host facts distinct:

```text
DevForge execution root = D:\coco\workspaces
legacy mutation_execution.workspace_root = D:\SentinelX\mutation-workspaces
```

That is correct as a truth-model goal, but the current Windows sandbox implementation hard-binds physical workspace activation to `policy.workspace_root`:

```python
root = _normal_path(self.policy.workspace_root)
workspace = _normal_path(Path(record.exact_workspace))
if not _is_relative_to(workspace, root) or workspace == root:
    raise HostMutationSandboxPathViolation("exact workspace escaped provider root")
```

Therefore merely teaching `MutationScopeStore` to seal `D:\coco\workspaces\...` cannot work: sandbox activation rejects the workspace before it is created. The current Host policy also treats the existing scoped-mutation root as the sandbox root, so a provider-selected placement strategy in the scope store alone is insufficient.

Plan R1 lists `windows_mutation_sandbox.py` only as a possible operation-closure surface and does not freeze how a DevForge-derived execution root becomes an independently admitted sandbox root without rewriting legacy `mutation_execution.workspace_root`, weakening protected/canonical boundaries, or creating caller-controlled path authority.

### Required remediation

Plan R2 must define the physical sandbox-root admission model, including:

- how the provider derives and verifies a DevForge sandbox root from `locations.devforge_workspace_root/workspaces`;
- how `WindowsMutationSandbox` receives that provider-selected root without accepting a caller root/path;
- how reparse/final-path checks are anchored to that exact DevForge execution root;
- how parent-directory traversal/ACL requirements are satisfied without granting AppContainer general access to `D:\coco` or canonical repositories;
- how protected-root/canonical-firewall semantics remain intact;
- how legacy scopes continue to use `mutation_execution.workspace_root` unchanged;
- a Windows physical negative test proving a scope cannot select another provider root.

A Host configuration rewrite or file/ACL allowlist expansion is not an acceptable hidden prerequisite unless separately authorized by an owning Host-configuration contract.

## Blocking Finding F3 — PR-014 still retains a duplicate implementation fallback for PR-013-owned transaction/materializer semantics

### Evidence

PR #13 is still an active Draft at Plan Review, head `32cd89bdc3430596409329c676e18d36dddffc1b`. Its current changed-file set is documentation-only, but Plan R2 already owns the provider repository-transaction design for:

- exact source broker/materializer;
- scope-bound AppContainer materialization;
- multi-operation transaction lifecycle / operation closure;
- legacy one-shot compatibility;
- source credential boundary;
- later publication semantics.

PR-014 correctly says it must not copy unmerged PR-013 code. But D3/D5 still allows PR-014, when PR-013 has not landed, to create a "minimum internal transaction abstraction" and the "smallest safe canonical provider component" needed for materialization and repeated scoped execution. S03 also owns retained-operation closure if no canonical primitive exists.

Those fallback clauses leave two competing provider transaction implementations possible on the same security-sensitive surfaces (`mutation_scope`, `scoped_script`, `windows_mutation_sandbox`, `devforge_runtime`). The distinction "no publication" does not remove the overlap: materialization and retained scope lifecycle are the core shared primitives.

### Required remediation

Plan R2 must make the ownership split executable rather than advisory:

- PR-014 may independently implement the DevForge-specific placement/receipt/scope-binding adapter surface that PR-013 does not own.
- Repository source acquisition/materializer and multi-operation operation-closure/transaction primitives must be consumed only from canonical `main` once PR-013 (or an equivalent separately verified canonical capability) lands.
- If those canonical primitives are absent, S02/S03 stop at an explicit dependency boundary; PR-014 must not implement a substitute transaction/materializer path.
- Slice admission must name the exact dependency evidence required before S02/S03 mutate overlapping files.
- If PR-013 changes its ownership or is cancelled, Plan remediation/re-review is required before PR-014 expands scope.

This preserves independent S01 progress while preventing two parallel security authorities from being implemented and reconciled later.

## Non-blocking observations

### DevForge runtime drift

Plan R1 records DevForge v2.40.0 / `1dc76ed...`; current runtime is v2.41.0 / `902a9d71...`. The 23-commit delta is confined to deployment/production-verification surfaces plus version/manifest reconciliation. The current Review Contract remains v1.3 and the execution-workspace materialization contract remains v1.0, so the runtime drift does not itself invalidate Requirement/Plan semantics. Plan R2 should update the baseline for auditability.

### Exact source identity and Acceptance boundary

`source_binding.expected_commit`, real HEAD/repository read-back, Windows physical proof, legacy one-shot regression coverage, and live Agent activation being Acceptance-owned are adequate directions and should be preserved.

## Requirement Traceability Assessment

- R1/R2/R3: direction valid, but F1/F2 block the exact provider/DevForge placement authority composition.
- R4/R6/R9/R12/R13/R14: Plan direction is adequate in substance.
- R5/R7/R8/R10/R11: blocked by F2/F3 until the physical sandbox root and canonical transaction/materializer dependency are frozen.
- AC1/AC3/AC5/AC7/AC8: require F1/F2 remediation.
- AC6/AC9/AC10/AC13: require F2/F3 remediation and canonical dependency evidence.

No Requirement semantic change is required by these findings. All findings are `plan_local`.

## Gate Result

```text
Plan Review: Rejected
Current Gate: plan_review_rejected
Implementation Authorized: false
Execution Slice Set: not compiled
Requirement Revision: 1 unchanged
Plan Revision Reviewed: 1
```

No product implementation, Host policy mutation, Agent activation/restart, generic fallback, PR-013 code import, or Execution Slice is authorized by this review.

Canonical next action:

```text
#开发计划修复 PR-014-devforge-execution-workspace-materialization-bridge-v1
```
