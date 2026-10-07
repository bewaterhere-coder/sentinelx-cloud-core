# PR-016 — SentinelX Scoped Verification Node/npm TypeScript AppContainer Drive-Root Compatibility V1

## State — Requirement Revision 1

```yaml
project_id: sentinelx-cloud-core
task_id: PR-016-scoped-verification-node-npm-typescript-appcontainer-drive-root-compatibility-v1
title: SentinelX Scoped Verification Node/npm TypeScript AppContainer Drive-Root Compatibility V1
requirement_revision: 1
development:
  stage: implementation
  gates:
    requirement_ready: true
    plan_approved: true
    acceptance_approved: false
    completion_verified: false
  plan_revision: 1
  implementation_authorized: true
  next_expected_actor: implementer
  blocking_findings: []
  current_slice: S01
  current_slice_state: pending
  authorization:
    mode: legacy_command_scoped
  continuation_checkpoint:
    ref: docs/checkpoints/PR-016-scoped-verification-node-npm-typescript-appcontainer-drive-root-compatibility-v1-s01-window-3-blocked-direct-codex-model-20261007.yaml
transport:
  type: github-pr
  pr_number: 16
  branch: task/scoped-verification-node-npm-typescript-appcontainer-drive-root-compatibility-v1
  base_branch: main
artifacts:
  plan: docs/plans/PR-016-scoped-verification-node-npm-typescript-appcontainer-drive-root-compatibility-v1-plan.md
  latest_plan_review: docs/reviews/PR-016-scoped-verification-node-npm-typescript-appcontainer-drive-root-compatibility-v1-plan-review-r1.md
  latest_plan_review_transition_receipt: docs/reviews/PR-016-scoped-verification-node-npm-typescript-appcontainer-drive-root-compatibility-v1-plan-review-r1-transition-receipt.yaml
  execution_slice_set: docs/execution/PR-016-scoped-verification-node-npm-typescript-appcontainer-drive-root-compatibility-v1-slices.yaml
  development_start_receipt: docs/checkpoints/PR-016-scoped-verification-node-npm-typescript-appcontainer-drive-root-compatibility-v1-development-start-20261006.yaml
  provisional_bootstrap: docs/checkpoints/scoped-verification-node-npm-typescript-appcontainer-drive-root-compatibility-v1-provisional-bootstrap.md
related_tasks:
  predecessor:
    - PR-011-scoped-verification-toolchain-dependency-capsule-v1
  downstream_consumer:
    - bewaterhere-coder/ChatGPTControlShell#15
```

## Problem

PR-011 established a provider-owned, offline Node/npm verification environment inside the Windows AppContainer boundary. Its readiness projection currently reports `host_runtime.scoped_verification_node_npm_v1.available=true` and `verified=true`.

A real downstream verification of ChatGPTControlShell PR-015 S01 exposed a compatibility gap that the current self-check does not detect:

```text
npm ci --offline
→ PASS

npm run typecheck
→ tsc --noEmit
→ Node.js v24.19.0
→ Error: EPERM: operation not permitted, lstat 'D:\\'
```

The failure occurs before TypeScript source checking. It is a Windows AppContainer path-resolution failure while Node canonicalizes a path beneath the provider-owned verification workspace.

## Repository Reality

Canonical `main@018b78ca20984176d53fbe90039dc795a7f2742f` already contains the PR-011 scoped verification implementation.

Relevant current behavior in `src/sentinelx_core/windows_mutation_sandbox.py`:

- the exact execution workspace receives the scoped AppContainer authority;
- `_grant_workspace_traverse()` grants transient non-inheriting `FILE_TRAVERSE` to workspace ancestors;
- ancestor discovery uses `_verification_toolchain_traverse_ancestors()`;
- that helper stops before the filesystem anchor/drive root;
- on a workspace under `D:\SentinelX\...`, `D:\SentinelX` and deeper parents may receive traversal authority, but `D:\` is excluded;
- `FILE_READ_ATTRIBUTES` is already defined by the Windows sandbox module;
- terminalization already owns revocation of transient workspace-traverse authority.

The observed `lstat 'D:\\'` failure is therefore consistent with an unadmitted drive-root metadata/traversal dependency, while the actual execution cwd remains inside the isolated provider workspace.

This Task must validate that diagnosis through real Windows proof rather than assume the exact access mask solely from the error string.

## Goal

Make real Node/npm package-local TypeScript execution work inside the existing scoped verification AppContainer while preserving the existing security model:

```text
provider-owned exact workspace
+ immutable source/capsule/toolchain admission
+ no network
+ no canonical repository access
+ minimum transient path-resolution authority
→ npm run typecheck / package-local binaries succeed
```

The solution must not move development execution back into `D:\coco` or grant broad read access to the D: volume.

## Required Behavior

### R1 — Provider-derived drive-root path-resolution authority

When an admitted Windows scoped verification workspace requires an AppContainer to resolve its absolute path, the provider may grant only the minimum transient metadata/traversal authority required on the exact filesystem ancestor chain, including the drive anchor when real proof shows it is necessary.

The caller must not select or supply ancestor paths, ACL masks, drive roots, or authorization targets.

The implementation must prove the minimum effective mask. The expected candidate is bounded non-inheriting directory path-resolution authority such as `FILE_TRAVERSE` plus only the metadata bit required by Node realpath/lstat behavior; broader read/list/write/execute inheritance is forbidden.

### R2 — No volume-wide read authority

Admitting the drive anchor must not grant authority to enumerate or read arbitrary sibling trees on that volume.

At minimum, real Windows negative proof must preserve denial for:

- canonical/protected roots such as `D:\coco`;
- unrelated sibling directories outside the exact workspace lineage;
- file-content reads outside admitted provider roots;
- creation, modification or deletion outside the exact workspace.

No inheriting ACE may be used on the drive root for this compatibility fix.

### R3 — Exact transient lifecycle and fail-closed revocation

Any new ancestor/drive-root AppContainer ACE must be:

- bound to the exact scope generation/AppContainer SID;
- granted only after durable scoped authority exists;
- tracked as transient runtime authority;
- revoked on normal terminalization;
- revoked on activation/materialization/spawn failure;
- read back/provable as absent after terminalization.

Cleanup ambiguity or residual authority must fail closed and prevent a successful completion claim.

### R4 — Compose the existing sandbox

The fix must compose `WindowsMutationSandbox`, existing scope lifecycle, audit lineage, workspace ACL and verification runtime.

It must not introduce:

- a second executor;
- a second AppContainer identity model;
- a second scope store;
- unrestricted shell fallback;
- `operator_unrestricted`;
- provider fallback;
- a new caller-controlled filesystem authority surface.

### R5 — Readiness must cover the real compatibility boundary

The `host_runtime.scoped_verification_node_npm_v1` readiness self-check must not report verified readiness when the configured AppContainer cannot perform the path-resolution behavior required by real Node/npm package-local execution.

Extend the physical readiness proof so that this class of drive-root/ancestor compatibility regression fails readiness deterministically before a downstream Task reaches `npm run typecheck`.

The readiness probe must remain bounded and must not require network access or canonical-repository access.

### R6 — Real dependency-backed TypeScript proof

Acceptance must include a real Windows AppContainer proof using Node 24-compatible behavior that exercises a package-local executable path equivalent to:

```text
npm ci --offline
npm run typecheck
→ tsc --noEmit
```

A synthetic test that only launches `node --version` or `npm --version` is insufficient.

The downstream ChatGPTControlShell PR-015 S01 scenario SHOULD be replayed after provider activation as integration evidence, but SentinelX acceptance must remain independently reproducible from a bounded fixture.

### R7 — Preserve PR-011 security properties

The fix must preserve all PR-011 guarantees:

- immutable source snapshot and dependency capsule integrity binding;
- provider-owned toolchain identity;
- offline/no-network execution;
- no credential inheritance;
- exact-workspace mutation authority;
- Job containment/no breakaway;
- canonical/protected repository denial;
- bounded verification evidence;
- terminal residual-authority closure.

## Non-Goals

This Task does not:

- grant general read permission to `D:\`;
- grant inherited RX on a volume root;
- make `D:\coco` readable to the AppContainer;
- relocate SentinelX mutation workspaces into `D:\coco`;
- enable network fallback for npm;
- change source snapshot/dependency capsule semantics;
- modify the closed-source `mcp.sentinelx.app` Hub;
- implement ChatGPTControlShell PR-015 itself;
- broaden generic `runtime_read_roots`.

## Acceptance Criteria

The Task is acceptable only when all of the following are evidenced on real Windows:

1. a scoped Node/npm verification fixture completes `npm ci --offline`;
2. the same scope completes a real package-local TypeScript `npm run typecheck`;
3. the AppContainer can perform the minimum required absolute-path/drive-root metadata resolution;
4. it still cannot enumerate/read arbitrary `D:\` sibling content or `D:\coco`;
5. it still cannot write outside the exact execution workspace;
6. the exact transient ancestor/drive-root authority is removed after terminalization and read back as absent;
7. failure-path cleanup also removes any newly introduced transient authority;
8. readiness self-check detects the compatibility boundary and reports verified only when the real path-resolution prerequisite passes;
9. existing PR-011 scoped verification, sandbox, audit, firewall and no-network regressions remain green;
10. no unrestricted/provider/canonical-checkout fallback is used.

## Requirement Readiness

```yaml
requirement_ready: true
material_product_decision_pending: false
requirement_artifact_bundle: not_required
ui_semantic_resolution: not_applicable
visual_fidelity: not_applicable
current_task_p0_dependencies: []
```
