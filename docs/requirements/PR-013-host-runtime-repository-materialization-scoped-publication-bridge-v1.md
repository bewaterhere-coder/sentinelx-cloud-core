---
task_id: PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1
title: SentinelX Host Runtime Repository Materialization & Scoped Publication Bridge V1
project_id: sentinelx-cloud-core
repository: bewaterhere-coder/sentinelx-cloud-core
requirement_revision: 1
development:
  stage: implementation
  gates:
    requirement_ready: true
    plan_approved: true
    acceptance_approved: false
    completion_verified: false
  plan_revision: 2
  implementation_authorized: true
  latest_plan_review: approved_round_2
  latest_plan_remediation: plan_r2_remediation_r1
  blocking_findings: []
  execution_disposition: active
  next_expected_actor: implementer
  current_slice: S03
  current_slice_state: pending
  completed_slices: [S01, S02]
  authorization:
    mode: legacy_command_scoped
artifacts:
  plan: docs/plans/PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1-plan.md
  latest_plan_review: docs/reviews/PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1-plan-review-r2.md
  prior_plan_review: docs/reviews/PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1-plan-review-r1.md
  latest_plan_remediation: docs/checkpoints/PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1-plan-remediation-r1.yaml
  execution_slice_set: docs/execution/PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1-slices.yaml
  latest_slice_checkpoint: docs/checkpoints/PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1-s02-completion-20261005.yaml
  latest_slice_completion_receipt: docs/reviews/PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1-s02-completion-receipt.yaml
transport:
  type: github-pr
  pr_number: 13
  branch: task/host-runtime-repository-materialization-scoped-publication-bridge-v1
  base_branch: main
requirement_readiness:
  result: Ready
  ui_semantics:
    applicability: NotApplicable
---

# Requirement

## Problem and concrete trigger

Canonical `main@dbf4bfc9ebcdbde2374d41e6825b613d46aa87f2` provides provider-owned mutation scope, exact workspace placement, Windows AppContainer confinement, pre-execution audit lineage, canonical-repository mutation firewall, the builtin `devforge_runtime` endpoint, and user-scoped Git execution.

The current `devforge_runtime` surface exposes only scope lifecycle actions plus `execute_scoped`. It does not hydrate an admitted repository/ref into the exact Host-owned workspace and does not publish a verified scoped-workspace checkpoint back to the canonical Task transport.

This gap is now proven by a real downstream execution of `bewaterhere-coder/ChatGPTControlShell` PR #13 S01:

- scope provisioning/revalidation succeeded with firewall, sandbox and audit capabilities verified;
- `git clone` attempted inside the required AppContainer failed before repository materialization with Windows status `0xC0000142`;
- a second attempt using sandbox Python to copy the canonical checkout failed with `WinError 5` because the protected canonical checkout is intentionally unreadable from the AppContainer;
- both attempts terminalized with zero source-checkout mutation, zero implementation commit and zero push;
- the blocked Run therefore requires a provider-owned source materialization and publication surface, not permission widening or generic execution fallback.

## Goal

Add a provider-owned **Repository Transaction Bridge** to the existing Host Runtime path so DevForge can:

```text
admit exact repository + source revision + Task/Run/Attempt lineage
→ provision/revalidate Host-owned mutation scope
→ materialize the exact admitted source into the scope-bound exact workspace
→ execute through the existing scoped AppContainer executor
→ verify workspace result
→ checkpoint/publish through a bounded Host Git broker
→ compare-and-swap remote readback
→ terminalize scope with durable evidence
```

The AppContainer must still receive neither canonical-checkout authority nor reusable Git credentials. The model/caller must still receive no arbitrary Host path authority.

## Required behavior

### R1 — Provider-owned repository transaction identity

Repository materialization/publication must bind to the existing normalized repository identity and exact semantic lineage:

- `project_id`;
- `task_id`;
- `run_id`;
- `attempt_id`;
- optional `slice_id`;
- repository `vcs + authority + path`;
- exact admitted source revision/commit;
- exact Task transport target when publication is requested.

Caller-supplied absolute workspace, checkout, cache, mirror, staging or canonical-source paths are forbidden as authority.

### R2 — Exact source revision admission

The caller may identify a logical source ref and expected commit SHA, but the provider must independently resolve and verify the exact remote/repository identity before materialization.

Materialization must fail closed on ref/SHA mismatch, repository identity mismatch, ambiguous remote identity, unavailable required source object, stale scope, or transport drift.

No branch-name-only checkout is sufficient evidence.

### R3 — Materialization is scope-bound

Repository hydration is allowed only after:

1. canonical repository firewall admission;
2. exact Host placement resolution;
3. `host_mutation_sandbox_v1.provision_scope`;
4. scope revalidation against repository + lineage + placement;
5. durable operation START evidence.

The provider derives the exact workspace from scope authority. The caller never chooses the destination.

Successful materialization must prove the workspace exists at the exact sealed placement, is isolated from the canonical checkout, and contains the exact admitted source revision before implementation mutation continues.

### R4 — Canonical checkout remains protected

The canonical/source checkout may be used only as read-only identity/evidence where existing contracts permit it. This Task must not solve materialization by granting the AppContainer broad read access to canonical repositories or by allowing generic writes/fetches/commits in canonical checkouts.

Canonical repository mutation firewall remains authoritative across every existing mutation-capable surface.

### R5 — Broker-owned source transport

Git/network/credential work needed to obtain the exact source must occur through a bounded provider-owned repository broker outside caller script semantics.

The broker must not expose credentials, credential-helper state, SSH agent material, tokens, reusable secret identifiers or the interactive-user environment to the scoped child process or model response.

The implementation may use a provider-owned mirror/snapshot/cache/capsule internally, but its location and lifecycle are provider authority, not caller input.

### R6 — Workspace mutation remains exact-scope only

Materialization must not create a second unrestricted write surface. Files derived from the admitted source may be written only to the exact Host-owned workspace bound to the current scope.

Any helper process or provider materialization step must be constrained to the exact transaction target and must not become a generic copy/clone primitive.

Symlink/reparse traversal, archive traversal, alternate data streams, path escape and unexpected special-file semantics must fail closed before successful materialization evidence.

### R7 — Existing scoped executor is reused

Implementation execution continues through the existing `scoped_mutation` AppContainer/Job/audit path. This Task must not add a second general script/process executor.

Existing non-repository `scoped_script` behavior remains backward compatible.

If a repository transaction needs a longer-lived scope than current one-shot execution, the provider must introduce an explicit transaction state machine rather than silently weakening automatic terminalization for legacy calls.

### R8 — Publication is a bounded repository operation

Publication must operate only on a previously materialized, scope-bound repository transaction whose lineage and admitted transport remain current.

The provider must:

- inspect/validate the workspace result before publication;
- bind publication to the exact canonical Task branch/ref;
- require an expected remote head / compare-and-swap fence;
- create at most the intended checkpoint commit from the exact workspace delta;
- push without force in V1 unless a separately authorized contract later adds force semantics;
- read back the remote branch head and require exact expected commit match before success;
- expose commit/push/readback evidence without credential material.

A remote-head change after admission must fail closed rather than overwrite another writer.

### R9 — Repository-controlled executable hooks are not publication authority

The publication broker must not execute repository-controlled Git hooks, credential scripts, arbitrary aliases, external clean/smudge filters, signing helpers or shell wrappers merely to checkpoint/push the workspace.

Use fixed bounded Git/plumbing semantics or equivalent provider-owned logic. Repository configuration that would introduce executable behavior must be ignored, overridden safely, or rejected.

### R10 — Scope lifecycle and failure atomicity

Repository transaction lifecycle must make these states distinguishable at minimum:

```text
provisioned
→ materialized
→ executing / executed
→ publication_pending
→ published
→ terminal
```

Equivalent state names are acceptable if semantics are explicit.

A failed materialization publishes nothing. A failed execution publishes nothing automatically. A failed publication must not replay a previously verified push. Timeout/cancel/containment failure must preserve fail-closed terminalization semantics.

Legacy one-shot `execute_scoped` calls must retain their current terminalization behavior.

### R11 — Audit and receipts

Durable evidence must correlate repository transaction events to the same repository + Task/Run/Attempt/slice + scope generation.

A successful end-to-end receipt must identify, without exposing secrets:

- repository identity digest;
- source ref + verified source SHA;
- scope/workspace identity and generation;
- materialization operation/audit reference;
- execution operation/audit reference(s);
- materialized-source digest or equivalent exact-revision proof;
- publication target ref;
- expected remote SHA;
- produced commit SHA;
- push result;
- remote readback SHA;
- source/canonical checkout mutation = false;
- generic bypass = false;
- `operator_unrestricted` = false;
- terminal scope state.

No receipt means no completion claim.

### R12 — Model-facing structured contract

The capability is projected through the existing Agent-owned `devforge_runtime` local API contract. Production `mcp.sentinelx.app` remains an immutable external transport boundary.

The Agent may add bounded actions such as repository materialization/publication or an equivalent transaction contract. The final action schema must be dynamically discoverable through `local_api.describe` and must not expose Host paths or credential controls.

### R13 — No fallback escalation

Any materialization/publication failure must not fall back to:

- generic `script_run`;
- generic `exec`/shell;
- generic filesystem copy/edit;
- generic `sentinel_git` mutation pretending to be scoped authority;
- caller-selected checkout paths;
- canonical checkout mutation;
- `operator_unrestricted`;
- file/command allowlist expansion;
- AppContainer access to user Git credentials;
- production Hub changes.

### R14 — Composition with current parallel work

PR-011 (`Scoped Verification Toolchain & Dependency Capsule V1`) is complementary: it supplies deterministic dependency-backed verification inside a scoped workspace and explicitly does not own repository workspace materialization.

PR-012 (`execute_scoped Explicit Execution Profile`) is not a semantic prerequisite but overlaps the `devforge_runtime` schema surface. Implementation must revalidate current `main` and reconcile exact overlap before mutation; neither Task may silently overwrite the other's transport.

PR-010 canonical repository firewall remains a mandatory security dependency and must not regress.

## Acceptance criteria

- **AC1:** `local_api.describe devforge_runtime` exposes a bounded repository-transaction materialization contract without caller-controlled Host destination paths.
- **AC2:** A valid repository identity + expected source ref/SHA + active scope materializes the exact source into the Host-derived exact workspace and returns exact-revision/readback evidence.
- **AC3:** Wrong repository, wrong ref/SHA, stale/foreign scope, wrong lineage, caller path injection and placement mismatch all fail before successful materialization.
- **AC4:** Materialization does not mutate the canonical checkout and does not make the canonical checkout generally readable/writable by the AppContainer.
- **AC5:** The existing scoped executor can operate on the materialized repository while preserving AppContainer, Job, audit and credential-sanitization guarantees.
- **AC6:** A valid publication request creates one checkpoint commit from the exact admitted workspace, pushes only to the exact admitted Task ref under expected-remote-SHA CAS, and verifies remote readback.
- **AC7:** Remote-head drift, credential failure, transport failure, dirty/conflicting publication state and branch mismatch produce no overwrite and no fallback method escalation.
- **AC8:** Publication executes no repository-controlled hooks/aliases/filters/signing helpers and leaks no credential/environment material.
- **AC9:** Duplicate/retried publication after a verified push converges via durable evidence/readback and does not create a second commit/push.
- **AC10:** Legacy one-shot `scoped_script` execution remains compatible and auto-terminalizes exactly as before.
- **AC11:** Canonical-repository firewall, scope-store uniqueness, AppContainer confinement, pre-execution audit lineage and user-scoped Git regressions remain passing.
- **AC12:** Windows integration coverage proves materialize → scoped mutation → checkpoint/push → remote readback on a benign fixture repository, including negative-security cases.
- **AC13:** After an accepted Agent build is activated, the blocked `ChatGPTControlShell` PR #13 S01 Run can resume under the same Run/Slice lineage, materialize its admitted source without canonical-checkout access, and reach its implementation verification boundary without generic fallback. This cross-repository proof does not transfer ChatGPTControlShell Task authority into this Task.

## Scope

### In scope

- repository-transaction scope semantics and durable transaction state;
- provider-owned exact source/ref resolution;
- safe repository materialization into exact scope workspace;
- provider-owned source mirror/snapshot/capsule mechanics if required;
- scoped workspace publication/checkpoint broker;
- expected-remote-SHA CAS and remote readback;
- fixed no-hook/no-executable-repository-config Git semantics;
- local-api action schema and integration;
- durable audit/receipt evidence;
- Windows integration and negative-security tests;
- operator/configuration documentation required to activate the capability.

### Out of scope

- modifying or deploying `mcp.sentinelx.app` Hub;
- generic Git client redesign;
- arbitrary repository hosting providers beyond what current repository identity/user-scoped Git semantics can safely support in V1;
- caller-selected workspace/mirror/cache paths;
- arbitrary force push;
- merge/rebase/cherry-pick orchestration;
- production deployment/release of unrelated repositories;
- exposing credentials to AppContainer/model;
- broad canonical-checkout read/write ACLs;
- replacing PR-011 verification-profile/dependency-capsule work;
- changing downstream ChatGPTControlShell Requirement/Plan semantics.

## Requirement challenge

The Plan/implementation must explicitly disconfirm at least these failure modes:

1. materialization secretly writes/fetches into the canonical checkout;
2. caller path fields can retarget the exact workspace or provider cache;
3. a stale/foreign scope can materialize or publish another Attempt's repository;
4. source branch name matches but source commit differs from admitted SHA;
5. provider staging archive/snapshot path traversal escapes the exact workspace;
6. publication runs malicious Git hooks/filters/aliases from repository config;
7. interactive-user credentials leak into AppContainer, logs or receipts;
8. remote head changes after admission and publication overwrites it anyway;
9. a retry after verified push creates another commit or repeats the push;
10. transaction support weakens legacy one-shot scope terminalization;
11. PR-011/PR-012 overlap is treated as permission to import or overwrite unmerged task state;
12. failure triggers generic shell/Git/copy fallback.

## Refinement evidence

Normal path: exact repository + exact remote SHA + exact scope materializes one isolated workspace, existing scoped execution mutates/tests it, publication creates one bounded checkpoint, CAS push succeeds, remote readback matches, and scope terminalizes with receipts.

Boundary path: source materializes and execution succeeds, but remote head advances before publication; publication stops with zero overwrite and preserves evidence for safe resume.

Counterexample: letting `execute_scoped` read `D:\\coco\\repos\\...` directly or giving it Git credentials would appear to unblock development but violates the canonical repository and credential boundaries, so it is not an acceptable implementation.

Readiness: the required behavior is materially defined; no unresolved product decision blocks planning. UI/visual fidelity is not applicable. Current readiness-profile absence is non-blocking for this established project.