# PR-015 — Direct Codex Development Host Invocation Bridge V1 — Acceptance R1

## Decision

```yaml
task_id: PR-015-direct-codex-development-host-invocation-bridge-v1
requirement_revision: 1
plan_revision: 2
acceptance_revision: 1
result: DecisionRequired
finding_classification: upstream_material_decision
canonical_transport: github-pr
pr_number: 15
canonical_branch: task/direct-codex-development-host-invocation-bridge-v1
evaluated_head_before_acceptance_artifacts: a72394a1e4b6b8a3d004ae17c5335a5bdd55e9a5
verified_product_candidate: a84db15a8770599718a665fd9c201c7b82b3dd91
current_stage: acceptance
gate_transition: not_applied
acceptance_approved: false
completion_verified: false
```

**PR-015 Acceptance R1: DecisionRequired.**

The implementation is technically substantial and all three approved Plan R2 slices are durably complete on the canonical PR transport. However, Acceptance cannot approve the Task because the real direct-Codex host cannot currently produce a persisted successful execution receipt: the installed Codex host performs file edits and verification inside the isolated checkout but does not create a Git commit, leaving the local head at the admitted CAS head. The provider therefore does not publish and correctly returns `implementation_not_persisted`.

Resolving this requires a material architecture/scope decision about persistence ownership. Provider-owned commit-on-publish is not authorized by the current Plan R2 slice scope, while requiring Codex itself to commit changes changes the direct-host handoff/adapter semantics. Acceptance MUST NOT choose either option implicitly.

## Runtime / Transport Consistency

PASS.

- DevForge Runtime: `bewaterhere-coder/DevForge main@f5e4b758e82bfccff76ced5520ed80dfd0872ad4`, version `2.81.0`.
- Acceptance Contract: v1.5.
- Canonical repository: `bewaterhere-coder/sentinelx-cloud-core`.
- Canonical PR: #15.
- Canonical branch: `task/direct-codex-development-host-invocation-bridge-v1`.
- Canonical main: `018b78ca20984176d53fbe90039dc795a7f2742f`.
- Evaluated PR head: `a72394a1e4b6b8a3d004ae17c5335a5bdd55e9a5`.
- Exact product candidate: `a84db15a8770599718a665fd9c201c7b82b3dd91`.
- The commit after the product candidate only persists S03 checkpoint/receipt/Slice Set state.
- GitHub CI, macOS and PR-010/PR-011 verification workflows on the evaluated head are all successful.
- No replacement repository, branch or PR is accepted. No TransportDrift is present.

## Implementation / Verification Evidence

PASS for the implemented boundaries.

- S01, S02 and S03 are all `completed`; there are no pending slices.
- S03 focused verification: `33 passed`.
- Related regression subset: `82 passed`; the documented Windows symlink privilege limitation is pre-existing and is not an S03 regression.
- Real Windows MIC proof observed an in-workspace write and OS-level `EPERM` on the protected sibling.
- Real `@openai/codex 0.154.0` execution ran through the fixed Node + `codex.js` chain under the active-user process substrate.
- Receipt validation now verifies exact Task/Run/Attempt/Slice, canonical repository, PR, canonical branch, actual branch and remote readback.
- Local-only unpersisted runs are correctly fail-closed and never reported as success.
- Persistent project binding remains `direct/codex`.

## Live Deployment Readback

The currently connected Windows Agent is `0.24.1.dev403+g9948eb4d4`.

Fresh `local_api.list` exposes only the existing `devforge_runtime` builtin provider and does **not** expose `devforge_direct_codex`. Live deployment/activation of the PR-015 candidate is therefore not proven in this Acceptance pass.

This is not the primary disposition because the upstream material persistence decision already prevents approval. Acceptance does not install or restart a candidate while that material decision is unresolved.

## Acceptance Matrix

- **AC1 — PASS:** bounded direct-Codex provider/action schema exists with no arbitrary executable/shell/cwd/env/prompt authority.
- **AC2 — PASS at exact-candidate product level:** readiness is fail-closed without required policy/platform/containment proof.
- **AC3 — PASS at candidate physical-proof level:** installed Codex executes non-interactively under the active-user substrate without credential return/persistence.
- **AC4 — PASS:** provider-derived isolated checkout preserves canonical checkout `main + clean`.
- **AC5 — PASS:** physical sibling-write negative proof is enforced by Windows MIC.
- **AC6 — PASS:** exact branch/head mismatch fails before implementation mutation.
- **AC7 — PASS:** deterministic handoff locks Requirement/Plan/Slice and canonical transport; replacement transport is forbidden.
- **AC8 — PARTIAL / BLOCKING:** fixture-host persisted receipt semantics pass in tests, but the **real Codex host** does not commit its work and therefore cannot produce a persisted successful receipt.
- **AC9 — PASS:** timeout/nonzero/malformed receipt/transport drift/local-only persistence failures remain fail-closed.
- **AC10 — PASS:** relevant script_run/devforge_runtime/firewall/verification regressions remain green.
- **AC11 — PASS:** no generic exec, operator_unrestricted, permission widening or Hub mutation was introduced.
- **AC12 — BLOCKED:** the bridge cannot yet demonstrate a real canonical direct/Codex implementation completion path suitable for unblocking PR-013 because real-host work is not persisted to transport, and the deployed Agent currently does not expose the PR-015 provider.

## Blocking Finding

### F1 — Real direct-Codex persistence ownership is unresolved

Classification: `upstream_material_decision`.

Observed real-host sequence:

```text
Codex executes in the isolated checkout
-> Codex changes files / runs verification
-> Codex does not create a commit
-> local_head remains expected_remote_sha
-> provider publish path does not fire
-> receipt = implementation_not_persisted
```

The bridge is behaving truthfully, but the end-to-end direct Development Host objective is not complete.

Two architecture choices are available:

1. **Provider-owned deterministic commit-on-publish (recommended):** after successful bounded Codex execution, the provider verifies the exact workspace/transport, stages only the bounded checkout changes, creates one provider-owned commit with deterministic Task/Run/Slice provenance, then CAS-publishes and independently reads back the remote.
2. **Direct-host-owned commit:** require Codex itself to stage/commit as part of the handoff contract before the provider publish/readback step.

Choice 1 keeps Git persistence inside the bounded provider transport broker and does not depend on model compliance, but it expands the provider's current Plan R2 persistence responsibility and requires an explicit Plan revision/review. Choice 2 keeps persistence with the Development Host but makes successful execution depend on agent behavior and changes the direct adapter handoff semantics.

Acceptance has no authority to choose this material architecture/risk decision.

## Authorization / Gate Effect

- Acceptance does **not** transition to `accepted`.
- Acceptance does **not** transition to `fixing`, because the required correction is not safely expressible under the exact current Approved Plan R2.
- Task remains at the `acceptance` boundary with `acceptance_approved=false`.
- Durable Development Authorization is suspended pending explicit human decision, as required for a new material architecture/scope/risk decision.
- The task-scoped CodeBuddy bootstrap override is non-authoritative because all bound implementation slices are complete and the Task is no longer in the implementation gate.

## Acceptance Result

```text
Acceptance Approved: false
Completion Verified: false
Result: DecisionRequired
Finding Class: upstream_material_decision
Gate Transition: not applied
Current Stage: acceptance
```

No merge, completion, release, deployment or product-code mutation is authorized by this result.
