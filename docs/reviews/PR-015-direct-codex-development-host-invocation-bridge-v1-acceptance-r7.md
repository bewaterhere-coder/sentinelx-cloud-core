# PR-015 — Direct Codex Development Host Invocation Bridge V1 — Acceptance R7

## Decision

```yaml
task_id: PR-015-direct-codex-development-host-invocation-bridge-v1
requirement_revision: 2
plan_revision: 6
acceptance_revision: 7
result: Rejected
finding_classification: repair_local
finding_code: direct_codex_workspace_acl_handoff_incompatible_with_codex_sandbox
canonical_transport: github-pr
pr_number: 15
canonical_branch: task/direct-codex-development-host-invocation-bridge-v1
evaluated_head_before_acceptance_artifacts: 080d31229b614c8fc753117fa7152618e4ff1e50
verified_product_candidate: d441e95b6eb65834f52ffdb42026e7328f5c9478
current_stage_before_transition: acceptance
target_stage: fixing
acceptance_approved: false
completion_verified: false
```

**PR-015 Acceptance R7: Rejected.**

The previous containment-lifecycle defect is repaired. The exact candidate is active
as `0.24.1.dev518+gd441e95b6`, production `execute_task` now provider-owns the
physical containment proof, and live `devforge_direct_codex` readiness reaches
`available=true / verified=true`.

The remaining live end-to-end failure is implementation-local. SentinelX creates
the isolated execution workspace under `D:\SentinelX\devforge-workspaces` as
the service identity, then launches the real Codex Development Host under the
active interactive user as required by R5/R10. Codex's Windows
`workspace-write` sandbox setup attempts to grant its exact sandbox
group/capability write ACE on that provider-created workspace and fails with:

```text
write ACE grant failed on
D:\SentinelX\devforge-workspaces\3ee95b7e76d50bbd\67438159c72bd2a5
SetNamedSecurityInfoW failed: 5
```

The real Codex session therefore cannot create PowerShell, bash, or cmd processes
and terminates fail-closed with `setup refresh had errors`.

This is not transport drift, project-binding drift, model unavailability, or a
generic external outage. The verification fixture remote was read successfully,
the exact Codex session started with `gpt-5.6-sol`, and failure occurs at the
ACL handoff between the provider-owned workspace and the selected Codex
workspace-write sandbox. R10 requires the selected Codex execution mode itself
to mutate its exact workspace before readiness is advertised.

## Live Evidence

- exact candidate: `0.24.1.dev518+gd441e95b6`;
- live readiness after provider-owned proof: `available=true / verified=true`;
- verification-only fixture: `bewaterhere-coder/devforge-harness#230`;
- fixture branch: `fixture/pr015-ac12-direct-codex-live-20261007`;
- fixture remote head remains `f19dbe1ef072596129884e05797936632f0fb850`;
- Attempt 3 used `gpt-5.6-sol` and started a real Codex session in the provider-derived workspace;
- Codex sandbox log records `SetNamedSecurityInfoW failed: 5` on the exact workspace;
- fixture PR remained unchanged; no commit/push/receipt was manufactured;
- canonical `sentinelx-cloud-core` checkout remains `main + clean`, ahead/behind 0/0;
- DevForge project binding remains `direct/codex`.

## Acceptance Matrix

- **AC1 — PASS**
- **AC2 — FAIL / REPAIR_LOCAL:** readiness is verified although the selected real Codex workspace-write sandbox cannot establish workspace write authority.
- **AC3 — FAIL / REPAIR_LOCAL:** exact active-user Codex starts but cannot execute implementation commands because workspace ACL setup fails.
- **AC4 — PASS**
- **AC5 — PARTIAL / REPAIR_LOCAL:** the surrogate MIC negative proof passes, but it does not prove the actual selected Codex workspace-write sandbox can mutate the exact workspace.
- **AC6 — PASS**
- **AC7 — PASS**
- **AC8 — FAIL / REPAIR_LOCAL:** the real fixture cannot reach provider commit/push/readback/persisted receipt.
- **AC9 — PASS**
- **AC10 — PASS**
- **AC11 — PASS**
- **AC12 — FAIL / REPAIR_LOCAL**

## Required Repair

1. Make the provider-derived exact execution workspace compatible with the selected
   active-user Codex `workspace-write` sandbox using exact-workspace bounded
   authority only, with no broad permission/write-scope expansion.
2. Ensure the real Codex sandbox can establish its required workspace write ACL
   while the canonical-like protected sibling remains non-writable.
3. Make readiness/self-check prove the selected Codex execution mode's actual
   workspace-write setup rather than only a surrogate child-integrity write probe.
4. Preserve credential separation, closed schema, canonical `main + clean`,
   no generic shell/run-as-user surface, and no Hub mutation.
5. Rerun the verification-only fixture through real Codex -> provider commit ->
   ordinary fast-forward push -> remote readback -> valid persisted receipt, then
   prove PR-013 direct/Codex admission without executing PR-013 S03 or changing
   its Task identity/project binding.

No new Requirement or architecture decision is required.
