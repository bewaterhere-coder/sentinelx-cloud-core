# PR-015 — Direct Codex Development Host Invocation Bridge V1 — Plan Review R2

## Review State

```yaml
task_id: PR-015-direct-codex-development-host-invocation-bridge-v1
review_target: plan
requirement_revision: 1
task_blob_sha: cdcc319199be67c95d5150d18e9135b5eb21019c
plan_revision: 2
plan_blob_sha: b1414f58e31e69fd5718479d04eb6b7e9e8475bd
prior_review_blob_sha: b727a988c2f5c90dc16f26d996e26ee5d3fa6b55
plan_remediation_transition_blob_sha: 10f2890422e17813e3c7973fb0eebbcddfc27a81
reviewed_task_head: a0060f236be471cfe330dad56f3900c9d4ff2c59
result: Approved
runtime:
  devforge_version: 2.69.0
  devforge_revision: a32dc7cc533bc5d9cb1b52b3477c654951b6d0cb
  project_development_workflow: "2.1"
  review_contract: "1.3"
  bootstrap_override_contract: "1.0"
repository_reality:
  canonical_main: 018b78ca20984176d53fbe90039dc795a7f2742f
  transport_pr: 15
  transport_branch: task/direct-codex-development-host-invocation-bridge-v1
  project_execution_binding:
    provider: direct
    adapter: codex
next_gate: implementation
next_expected_actor: bootstrap_operator
```

## Decision

**Approved.**

Plan Revision 2 closes both Plan Review R1 P0 findings without changing Requirement Revision 1 or canonical transport.

Approval authorizes compilation of the exact S01-S03 Execution Slice Set only. It does not create the Task-scoped bootstrap override, execute CodeBuddy or Codex, mutate Host policy, activate/restart a live Agent, change the project binding, modify production Hub, or perform product implementation.

Because this is a verified self-hosting repair, Implementation Ready has one additional admission step before the first Slice may execute: the explicit Task-scoped bootstrap command bound to the Approved Plan and compiled Slice Set.

## R1 Finding Re-evaluation

### F1 — BootstrapExecutionStrategyIncomplete

**Closed.**

R2 freezes exactly one intended bootstrap target:

```text
direct:codebuddy
```

The target is appropriate at Plan level because:

- DevForge has a CodeBuddy Development Adapter;
- CodeBuddy is a direct Development Host, not a replacement execution-control plane;
- the global Development Host Canonical Transport Enforcement Contract applies to any Development Host and requires exact existing repository/PR/branch identity, no fallback branch/PR and canonical/actual transport receipt consistency;
- current Windows Host Reality shows a CodeBuddy installation and a current-user DevForge rule surface;
- R2 does not treat installation as final mutation authority: it requires the later explicit `#开发引导执行` admission to re-check target registration, actual availability, exact Task/Approved Plan/Slice Set, canonical PR #15/branch, write-scope preservation and no permission expansion before the override may become active.

The local `buddycn` executable is an editor CLI and is **not** promoted by this review into an agent RPC or generic process authority. Direct-adapter execution may use the normal DevForge external Thin Execution Pointer boundary. If current runtime cannot actually hand off to CodeBuddy under that boundary, the bootstrap command must return `BootstrapTargetUnavailable` or the more specific fail-closed reason. It must not fall back.

The self-host relation is valid:

```text
canonical project provider requires direct/Codex invocation
+ current ChatGPT/DevForge path lacks that bounded invocation capability
+ this exact Task implements that bounded invocation capability
=> Task-Scoped Bootstrap Override is applicable after Plan approval
```

Approval itself does not create that override.

### F2 — DirectCodexFirewallCompositionIncomplete

**Closed.**

R2 explicitly binds the new builtin provider to the existing PR-010 operation-effect machinery.

Current Core already has the needed composition seam:

```text
local_api
→ make_local_api_effect_classifier / make_local_api_effect_inventory
→ _builtin_effect(provider, action, selector)
→ provider.repository_effect(action)
```

and unknown/missing builtin effect metadata already fails closed.

R2 now requires S01 to use one effective builtin provider map for both model-reachable `local_api` dispatch and canonical repository-firewall feature/readiness computation, and to add deterministic effect metadata for both the existing `devforge_runtime` builtin and the new `devforge_direct_codex` builtin.

This fixes the actual coverage gap without creating a second inventory or weakening PR-010.

## Review Checks

### Solution direction

**Pass.** The Plan adds a dedicated bounded builtin provider through the existing `sentinel_local_api` envelope, while keeping Codex as Development Host and SentinelX as transport/policy enforcement.

### Scope control

**Pass.** No production Hub change, generic `exec`, generic run-as-user primitive, arbitrary command/shell/argv/cwd/env/prompt field, operator-unrestricted mode, project rebinding, PR-013/PR-014 capability duplication, replacement PR or replacement branch is authorized.

### Technical feasibility

**Pass with implementation-entry guards.**

The Plan uses existing Core seams rather than inventing parallel infrastructure:

- builtin `local_api` provider registration;
- current policy/readiness model;
- current operation-effect registry;
- current user-scoped Git support;
- Windows active-user execution mechanics that may be factored only behind fixed provider-owned brokers;
- Codex's installed non-interactive execution mode;
- exact canonical GitHub PR transport.

Any implementation-time assumption that depends on live Host reality has a specific fail-closed validation point before the corresponding mutation.

### Security boundary

**Pass.**

R2 requires:

- fixed verified executable chain;
- no credential material projection;
- provider-derived isolated workspace;
- canonical checkout protection;
- physical workspace-positive/protected-sibling-negative proof;
- bounded process lifecycle;
- exact transport CAS/readback;
- provider-wide firewall effect visibility;
- no automatic provider fallback.

### Requirement traceability

**Pass.**

- R1/R2/R6/R9 map to dedicated provider identity, closed schema and deterministic handoff.
- R3/R4/R10/R14 map to policy/readiness, fixed executable identity, sandbox proof and no generic-execution expansion.
- R5 maps to active-user identity with credential non-disclosure.
- R7/R8 map to derived workspace and exact canonical transport bootstrap.
- R11/R12/R13 map to bounded process lifecycle, structured receipt/readback and fail-closed failure taxonomy.
- R15 maps to explicit PR-011/PR-013/PR-014 ownership separation.

### Verification realism

**Pass.**

Mock/unit evidence is not allowed to replace the physical Windows isolation proof or live direct-Codex invocation evidence. S03 and Acceptance retain those boundaries explicitly.

### Runtime drift

**Pass.**

Plan R2 recorded DevForge `a13b1113...`. Current DevForge is v2.69.0 at `a32dc7cc...`.

The intervening commits are release metadata/receipt/roadmap reconciliation and version projection only. The only `system/runtime-router.yaml` semantic diff is `version: 2.68.0 -> 2.69.0`. Review, bootstrap-override and task-execution semantics used by this Plan remain unchanged.

## Slice Compilation Guidance

Compile exactly three ordered Slices:

1. **S01 — Provider Contract, Policy, Readiness & Firewall Effect Composition**
2. **S02 — Isolated Workspace, Exact Transport Bootstrap & Bounded Codex Execution**
3. **S03 — Direct Adapter Receipt & Self-Host Recovery Proof**

Rules:

- one explicit `#开发执行` completes at most one Slice;
- S02 depends on S01; S03 depends on S02;
- before every Slice, re-read current `main`, PR #15 head, Approved Plan R2, Slice Set, active bootstrap override and canonical transport;
- material Requirement/Plan drift fails closed;
- exact PR #15 / branch remains the only implementation transport;
- bootstrap target failure does not fall back;
- implementation does not install/restart the production/live Agent;
- Acceptance owns live activation and final deployed proof.

## Bootstrap Entry Requirement

The Task is now Implementation Ready, but the persistent project binding remains `direct/codex`, whose current invocation bridge is the capability being implemented.

Therefore the required next command is not ordinary `#开发执行` yet. The only allowed bootstrap authority request is:

```text
#开发引导执行 PR-015-direct-codex-development-host-invocation-bridge-v1 direct:codebuddy
```

That command must bind to this exact Approved Plan R2 digest and the compiled Slice Set. Without a verified active override receipt, a subsequent implementation execution remains blocked by the normal provider resolution.

## Gate Result

```text
Plan Review R2: Approved
Requirement Revision: 1
Plan Revision: 2
Plan Approved: true
Execution Slice Set: required and compiled by this review transition
Next Gate: implementation
Next Slice: S01
Bootstrap Override: required before first Slice
Next Actor: bootstrap_operator
```

No product implementation or bootstrap override is executed by this review.
