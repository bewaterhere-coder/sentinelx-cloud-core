# PR-011 Requirement Revision 2 — Change Impact Analysis

## Decision

Requirement Revision 2 changes only the completion/acceptance role of the former AC12 ChatGPTControlShell PR-015 proof.

The downstream PR-015 proof is now **non-gating downstream integration evidence**. PR-011 must be independently acceptable and completable from its own SentinelX evidence: real Windows Host Node/npm verification profile, dependency capsule integrity, offline execution, AppContainer/Job containment, no credential/network widening, audit evidence, and terminal readback.

This is a material Requirement semantic change because it changes the Acceptance/Completion boundary. It does **not** change the product security model, R1-R9 implementation semantics, or the already verified S01-S03 implementation behavior.

## Freshness

```yaml
coco_runtime:
  version: 5.4.5
  revision: 792255a3801d83c14181982ebb787569c18ff348
devforge_runtime:
  version: 2.43.0
  revision: a5e44e7b648b741df02a667621c3a5abe62ea5e7
sentinelx_main: e7064c9bf4fcd15bdb6f5a2678414210c01d1c00
task_head_before_change: 8d0126ee81142411a3a08c10abb39b84f574e2af
transport:
  pr: 11
  branch: task/scoped-verification-toolchain-dependency-capsule-v1
```

## Impact Classification

| Artifact / evidence | Disposition | Reason |
|---|---|---|
| Requirement Revision 1 | Superseded by Revision 2 | AC12 gate semantics changed |
| R1-R9 security/runtime semantics | Preserved | Unaffected by downstream integration gate change |
| R10 / legacy AC12 | Revised | Downstream evidence remains useful but is not a PR-011 gate |
| Plan Revision 3 | Invalidated as current Approved Plan | Exact Requirement binding changed and Step F treated AC12 as required |
| Plan Review R3 approval | Historical only | It approved Requirement Revision 1 / Plan R3 |
| Execution Slice Set Plan R3 | Invalidated as current Slice Set | Current-plan identity changed; must be recompiled only after Plan R4 approval |
| S01 completion receipt/evidence | Preserved / no replay | Implementation and verification do not depend on AC12 |
| S02 completion receipt/evidence | Preserved / no replay | Implementation and verification do not depend on AC12 |
| S03 completion receipt/evidence | Preserved / no replay | Implementation and verification do not depend on AC12 |
| S04 blocked Host-proof checkpoint | Preserved as historical continuation evidence, not completion | S04 never completed; current physical proof remains unresolved |
| S04 implementation candidate in original workspace | Untouched | Requirement revision must not overwrite or replay stopped implementation work |
| S05 | Pending | Remains required after S04 |
| Acceptance evidence | No accepted decision exists to preserve | Future Acceptance evaluates Revision 2 / Plan R4 |
| ChatGPTControlShell PR-015 | Downstream consumer only | Separate Task authority; cannot block PR-011 Completion |

## Plan Reconciliation

Plan Revision 4 preserves Revision 3 Steps A-E and the security/test model unchanged. The required semantic changes are:

1. bind the Plan to Requirement Revision 2 and current SentinelX `main`;
2. remove Step F / PR-015 execution from PR-011 implementation and completion scope;
3. treat PR-015 proof as optional downstream integration evidence after PR-011 is independently accepted;
4. preserve S01-S03 verified completion evidence without replay;
5. keep remaining implementation progression strictly `S04 -> S05`;
6. require a fresh Plan Review before implementation resumes;
7. after Plan R4 approval, compile a new exact Slice Set that imports S01-S03 as already-completed no-replay evidence and contains only S04/S05 as pending work.

## S04 Workspace Safety

The pre-existing stopped S04 workspace is not used for this Requirement/Plan mutation:

```text
D:\coco\workspaces\bewaterhere-coder\sentinelx-cloud-core\pr011-s04-20261005
```

It was observed dirty with unpublished S04 candidate work. This change uses a separate orchestration workspace and does not reset, clean, overwrite, commit, or replay that workspace.

## Resulting Workflow State

```yaml
stage: plan_review
requirement_revision: 2
plan_revision: 4
requirement_ready: true
plan_approved: false
implementation_authorized: false
current_slice_hint: S04
current_slice_state: pending_plan_reapproval
preserved_completed_slices: [S01, S02, S03]
remaining_scope: [S04, S05]
```

No product implementation is authorized by this change.

## Next Canonical Action

```text
#开发评审 PR-011-scoped-verification-toolchain-dependency-capsule-v1
```
