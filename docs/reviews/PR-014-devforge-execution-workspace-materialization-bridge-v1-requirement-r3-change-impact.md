# PR-014 — Requirement R3 Change Impact

## Decision Source

Acceptance R2 returned `DecisionRequired` after exact-candidate physical execution proved a structural conflict:

~~~text
canonical/protected source root: D:\coco
old execution placement:        D:\coco\workspaces
protected root:                 D:\coco
~~~

The Human decision accepts the recommended architecture and explicitly forbids weakening `D:\coco` protection.

## Requirement Change

Requirement Revision 3 changes only these material semantics:

1. canonical source role and DevForge execution placement become independent Host-owned bindings;
2. canonical source remains resolved from the protected canonical-repository inventory under `D:\coco\repos\...`;
3. DevForge execution placement uses dedicated `locations.devforge_execution_workspace_root`, preferred current Host value `D:\SentinelX\devforge-workspaces`;
4. execution placement must be outside every protected/canonical root;
5. MutationScope durable-state read/migration must support compatible additive schema evolution, including `runtime_read_authority_roots`, without deleting state or widening authority.

All other Requirement R2 safety/behavior boundaries remain authoritative.

## Explicitly Preserved Invariants

- `D:\coco` protected root is not removed or narrowed;
- no carve-out/allowlist exception under `D:\coco`;
- no caller-selected source or execution path;
- no generic Git/shell/script_run/filesystem fallback;
- no canonical checkout mutation;
- Host-owned MutationScope, audit, AppContainer/Job and firewall boundaries remain required;
- PR-013 S03 replay remains forbidden;
- hosted CI remains NotEvaluated/NonGating.

## Artifact Impact

Current execution authority invalidated by Requirement R3:

~~~text
Plan R6
Plan R6 Review approval
Plan R6 Slice Set as current execution authority
Acceptance R2 current Gate decision
~~~

Preserved as historical implementation evidence:

~~~text
S01 completion evidence
S02 candidate 45dc99d15a23c499b4c1500fab60ed5e76475aeb
S02 completion checkpoint/receipt
S02 R6 reconciliation receipt
147 passed / 1 skipped / 0 failed
9/9 changed product/test blobs byte-identical
Acceptance R2 exact-candidate activation/live projection evidence
~~~

Historical evidence preservation does not authorize replay.

## Required New Plan Shape

Plan R7 must preserve S01/S02 and compile, after approval, one delta repair Slice:

~~~text
S01 completed/reused
S02 completed/reused historical implementation
S03 pending: dual-binding placement + MutationScope schema compatibility
~~~

No current R7 Slice Set exists before Plan Review approval.

## Result

~~~yaml
requirement_revision: 3
requirement_ready: true
plan_revision_required: 7
prior_plan_r6_current_authority: invalidated
s01_s02_historical_evidence_preserved: true
s01_s02_product_replay: forbidden
next_gate: plan_review
~~~
