# PR-011 — Scoped Verification Toolchain & Dependency Capsule V1

## State — Requirement Revision 2

```yaml
project_id: sentinelx-cloud-core
task_id: PR-011-scoped-verification-toolchain-dependency-capsule-v1
title: Scoped Verification Toolchain & Dependency Capsule V1
requirement_revision: 2
development:
  stage: implementation
  gates:
    requirement_ready: true
    plan_approved: true
    acceptance_approved: false
    completion_verified: false
  plan_revision: 6
  implementation_authorized: true
  next_expected_actor: implementer
  blocking_findings: []
  current_slice: S03R
  current_slice_state: pending
  authorization:
    mode: legacy_command_scoped
transport:
  type: github-pr
  pr_number: 11
  branch: task/scoped-verification-toolchain-dependency-capsule-v1
  base_branch: main
artifacts:
  plan: docs/plans/PR-011-scoped-verification-toolchain-dependency-capsule-v1-plan.md
  plan_revision: 6
  plan_blob_sha: fc59575081f3d35b7195711961ed387bc7a56fb2
  prior_plan_revision: 5
  prior_plan_blob_sha: 39e2056c924b4ca9ba73211921001aff408e99a6
  prior_plan_archive: docs/plans/PR-011-scoped-verification-toolchain-dependency-capsule-v1-plan-r5.md
  execution_slice_set: docs/execution/PR-011-scoped-verification-toolchain-dependency-capsule-v1-slices.yaml
  execution_slice_set_status: current_plan_r6_readback_verified
  execution_slice_set_blob_sha: d0d92b5c4766f0520818403e885ab9a02951d451
  prior_execution_slice_set_blob_sha: b0e92968c7a082cba6dce251bc3ff5ba50b334e8
  latest_plan_change_impact: docs/reviews/PR-011-scoped-verification-toolchain-dependency-capsule-v1-plan-r5-real-host-descendant-process-impact-analysis.md
  latest_plan_remediation: docs/checkpoints/PR-011-scoped-verification-toolchain-dependency-capsule-v1-plan-remediation-r6-20261006.yaml
  latest_plan_remediation_transition_receipt: docs/reviews/PR-011-scoped-verification-toolchain-dependency-capsule-v1-plan-remediation-r6-transition-receipt.yaml
  latest_plan_review: docs/reviews/PR-011-scoped-verification-toolchain-dependency-capsule-v1-plan-review-r6.md
  latest_plan_review_blob_sha: 7c166bae043228f4c6e2c8bb643cfe4b3fc2fa78
  latest_plan_review_disposition: approved_current
  prior_plan_review: docs/reviews/PR-011-scoped-verification-toolchain-dependency-capsule-v1-plan-review-r5.md
  latest_slice_completion_checkpoint: docs/checkpoints/PR-011-scoped-verification-toolchain-dependency-capsule-v1-s02r-completion-20261006.yaml
  latest_slice_completion_receipt: docs/reviews/PR-011-scoped-verification-toolchain-dependency-capsule-v1-s02r-completion-receipt.yaml
  s04_blocked_checkpoint: docs/checkpoints/PR-011-scoped-verification-toolchain-dependency-capsule-v1-s04-blocked-host-execution-surface-20261005.yaml
  requirement_change_impact: docs/reviews/PR-011-scoped-verification-toolchain-dependency-capsule-v1-requirement-r2-impact-analysis.md
  development_start_receipt: docs/checkpoints/PR-011-scoped-verification-toolchain-dependency-capsule-v1-development-start-20261003.yaml
related_tasks:
  satisfied_integration_dependency:
    - PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1
  overlap_reconciliation:
    - PR-010-canonical-repository-mutation-firewall-v1
  downstream_consumer:
    - bewaterhere-coder/ChatGPTControlShell#15
```

## Problem

SentinelX scoped mutation on Windows already provides a strong AppContainer boundary: provider-owned exact workspace placement, exact-workspace write ACL, bounded runtime read roots, Job containment, pre-spawn audit lineage, and fail-closed terminalization.

That boundary is currently insufficient for real development verification involving Node/npm:

- the scoped environment can execute the provider's Python runtime used by the sandbox path;
- Host-installed Node/npm such as `C:\Program Files\nodejs` is intentionally not readable inside the AppContainer unless the provider explicitly grants it;
- the scoped environment does not have general DNS/network access and must not gain arbitrary network merely to run verification;
- package dependencies are therefore unavailable unless a trusted dependency source is explicitly provisioned;
- callers must not solve this by passing Host filesystem paths, mounting the canonical checkout, inheriting Git/SSH/GitHub credentials, widening the command allowlist, or using `operator_unrestricted`.

This blocks legitimate dependency-backed checks such as `npm run typecheck` and `npm run check` even when the project implementation itself is already correct.

The concrete downstream trigger is ChatGPTControlShell PR-015 S01, whose implementation is checkpointed but cannot obtain the required real dependency-backed MCP package verification receipt from the current scoped runtime.

## Repository Reality — Revision 2 Refresh

Canonical `main@e7064c9bf4fcd15bdb6f5a2678414210c01d1c00` already provides:

- provider-owned `MutationScopeStore` lifecycle and builtin `devforge_runtime` through the merged PR-007 path;
- Windows AppContainer sandbox activation, exact-workspace write authority, Job containment and pre-execution audit lineage;
- the merged PR-010 canonical repository mutation firewall;
- the merged and live-verified PR-012 explicit `execution_profile=scoped_mutation` contract;
- fail-closed scoped execution and terminal residual-authority closure.

Canonical `main` does **not** yet provide the accepted PR-011 completion surface:

- a canonical accepted Node/npm verification readiness capability;
- completed real-Windows S04 physical proof for the current PR-011 candidate;
- the S05 bounded `verification` selector on canonical `devforge_runtime.execute_scoped`;
- a completed live Agent readback of profile/toolchain/capsule/offline/audit/terminal evidence for PR-011.

The existing PR-011 S01-S03 implementation receipts are verified no-replay evidence on the Task branch. S04 has a blocked Host-proof checkpoint and unpublished local candidate; it is not complete and must be reconciled after the revised Plan is approved.

Production `mcp.sentinelx.app` remains a closed-source external transport boundary and is not modifiable by this Task.

## Goal

Add a provider-owned **Scoped Verification Environment** that can run deterministic Node/npm verification inside the existing Windows AppContainer boundary without exposing canonical repositories or arbitrary Host/network authority.

The target shape is:

```text
DevForge / admitted caller
→ existing provider-owned Scope
→ logical verification profile (for example `node_npm`)
→ provider resolves trusted toolchain + dependency capsule
→ exact execution workspace
→ Windows AppContainer
→ offline dependency-backed npm verification
→ bounded output + audit/verification evidence
```

The caller chooses only a logical profile and integrity expectations. Host filesystem paths, executable locations, dependency-cache locations, credentials and network authority remain provider-owned or unavailable.

## Required Behavior

### R1 — Provider-owned verification profiles

Extend the Host mutation policy with a versioned verification-profile model. A caller may reference a logical profile identifier but MUST NOT supply toolchain roots, executable paths, cache roots, capsule roots, ACL targets or network endpoints.

V1 must support a Node/npm profile sufficient to run `node`, `npm`, local package scripts and package-local binaries.

Profile resolution must fail closed when:

- the profile is absent/disabled;
- configured roots are missing or non-canonicalizable;
- the resolved toolchain does not match the declared kind/version contract;
- a profile root overlaps a forbidden provider/canonical/protected boundary;
- the profile would require credential inheritance or unrestricted execution.

### R2 — Read/execute toolchain authority only

The AppContainer may receive the minimum provider-owned read/execute authority required for the selected toolchain. It MUST NOT receive write authority to the installed Host toolchain.

The implementation must preserve:

- exact-workspace-only mutation authority;
- existing reparse/final-path validation;
- no direct canonical-repository access;
- no direct caller-selected Host path access;
- no Git/SSH/GitHub credential inheritance.

A generic `runtime_read_roots` grant is not by itself sufficient evidence that a Node/npm verification profile was admitted; the selected profile identity and resolved toolchain evidence must be explicit.

### R3 — Integrity-bound offline dependency capsule

V1 must define an immutable provider-owned dependency capsule for Node/npm verification. A capsule must carry a versioned manifest and cryptographic identity sufficient to bind it to the dependency input it claims to satisfy, including at least the relevant package-lock digest.

The provider must validate the capsule before execution. Cache/capsule miss, manifest mismatch, lockfile-digest mismatch, tampering or unsupported capsule revision must fail closed.

The runtime must not fetch missing packages from the public Internet as a fallback.

Capsule creation/provisioning may be an explicit provider/operator build step, but scoped execution itself must consume only an already admitted capsule. Automatic arbitrary-network package acquisition is outside V1.

### R4 — Workspace-local verification materialization

Any mutable npm cache/log/temp state needed by verification must live inside the exact execution workspace.

If a provider-owned capsule is immutable/read-only, the provider may materialize a bounded workspace-local verification cache after durable operation START and before the mutating child process runs. This materialization must be:

- derived only from the admitted capsule;
- confined to the exact workspace;
- included in audit/verification evidence;
- cleaned/terminalized under existing Scope lifecycle semantics.

The solution MUST NOT grant the AppContainer write permission to the provider's immutable capsule store.

### R5 — No network widening

Selecting a verification profile MUST NOT enable arbitrary DNS, Internet, LAN or loopback network authority for the AppContainer.

Node/npm verification must succeed using the admitted toolchain and dependency capsule. Missing dependencies are an explicit verification-environment failure, not a reason to turn networking on.

### R6 — Scoped executor composition, not a second executor

Verification profiles must compose the existing scoped-script/AppContainer/scope/audit execution path. The Task MUST NOT introduce a second process executor, scope authority, audit journal or sandbox implementation.

The existing `python3`, `powershell` and `pwsh` scoped paths remain compatible when no verification profile is requested.

### R7 — `devforge_runtime` integration boundary

The canonical builtin `devforge_runtime.execute_scoped` action may expose an optional bounded verification selector.

Required characteristics:

- transport remains the existing generic `sentinel_local_api` envelope;
- action `describe` publishes the current parameter schema dynamically from the Agent;
- no production Hub schema/source/deployment change is required;
- the caller supplies a logical profile and integrity identifiers only, never Host paths;
- the adapter continues to call the one existing scoped executor;
- explicit `execution_profile=scoped_mutation` remains required and regression-compatible.

PR-007, PR-010 and PR-012 are canonical dependencies already merged into `main`; PR-011 consumes those seams directly and MUST NOT duplicate their scope store, sandbox, firewall, executor, audit authority, or execution-profile contract.

### R8 — Verification evidence and readiness

A successful profiled verification result must expose bounded machine-readable evidence sufficient to identify:

- verification profile id + contract revision;
- resolved toolchain kind/version and integrity/provenance digest;
- dependency capsule id/revision/digest;
- expected and verified package-lock digest;
- execution Scope/audit operation identity;
- offline/no-network mode;
- terminal Scope state.

Do not expose credential material, arbitrary Host paths or package contents in the receipt.

Node/npm verification readiness must be separately discoverable and fail closed. Absence of a Node/npm profile MUST NOT incorrectly make the base scoped-mutation runtime unavailable.

### R9 — Configuration and migration safety

Existing Hosts with no verification-profile configuration retain current behavior.

Adding V1 support must not:

- auto-admit Host-installed Node/npm;
- infer a profile from `PATH`;
- convert arbitrary `runtime_read_roots` into executable verification profiles;
- change existing `operator_unrestricted`, legacy-unprofiled or direct `exec` semantics;
- widen `file_ops`, `allowed_commands`, credential context or network policy.

### R10 — Downstream integration evidence (non-gating)

After PR-011 is independently accepted and an accepted provider build is activated on a Windows Host with an admitted Node/npm verification profile and matching dependency capsule, downstream consumers may use the capability to produce real dependency-backed Node/npm receipts.

The intended downstream integration evidence is to resume ChatGPTControlShell PR-015 S01 and obtain:

```text
mcp npm run typecheck
mcp npm run check
```

without exposing the canonical ChatGPTControlShell checkout to the AppContainer and without replaying already verified PR-015 implementation side effects.

This evidence is cross-repository downstream validation only. It does not transfer ChatGPTControlShell Task authority into PR-011, and it is **not required** for PR-011 Acceptance, Completion, merge eligibility, or `completion_verified=true`.

## Scope

### In scope

- verification-profile policy/configuration model;
- provider-owned Node/npm toolchain resolution;
- immutable dependency-capsule manifest/integrity validation;
- bounded capsule materialization into exact workspace when required;
- safe profiled environment composition for Node/npm;
- scoped-executor integration using existing sandbox/scope/audit authority;
- Node/npm-specific readiness/capability evidence;
- admitted canonical `devforge_runtime.execute_scoped` integration;
- unit, Windows integration, negative-security and live read-back coverage;
- operator documentation and example configuration;
- an explicit provider-side capsule preparation/validation utility if required by the Plan, provided it is not model-facing execution authority.

### Out of scope

- modifying `mcp.sentinelx.app` Hub source/schema/deployment;
- generic network egress from AppContainer;
- arbitrary package-manager support beyond Node/npm V1;
- arbitrary caller-selected toolchain/cache/capsule paths;
- mounting or exposing canonical repositories to verification scopes;
- inheriting Git/GitHub/SSH/npm credentials into verification scopes;
- `operator_unrestricted` fallback;
- widening generic `exec`, `script_run`, `file_ops` or command allowlists;
- silently downloading missing dependencies;
- replacing DevForge execution-workspace materialization semantics;
- changing ChatGPTControlShell PR-015 Requirement/Plan/implementation.

## Requirement Challenge

The Plan/implementation must explicitly disconfirm the following failure modes:

1. **Toolchain ACL becomes a write escape.** AppContainer can mutate Host Node/npm installation or another provider runtime root.
2. **Capsule becomes an authority smuggling path.** A caller can name an arbitrary directory or inject executable content through capsule metadata.
3. **Lockfile mismatch produces false verification.** A capsule for dependency set A is accepted for package-lock B.
4. **Offline mode silently becomes networked mode.** npm reaches registry/proxy/DNS when capsule content is missing.
5. **Credential environment leaks.** npm/Git/SSH/GitHub auth state from the broker appears inside the scope.
6. **Workspace containment regresses.** npm lifecycle scripts or descendants escape exact workspace/Job containment.
7. **Readiness lies.** capability is advertised when Node/npm or the configured capsule store is not physically usable by AppContainer.
8. **Canonical runtime lineage is bypassed.** implementation duplicates or bypasses the merged PR-007/PR-010/PR-012 execution, scope, firewall or explicit-profile seams.
9. **Canonical repository firewall regresses.** verification-profile changes weaken PR-010 canonical-repository mutation firewall semantics.
10. **Base sandbox compatibility regresses.** existing non-profiled scoped Python/PowerShell tests fail because verification-profile support became mandatory.

## Acceptance Criteria

- **AC1:** A configured Windows test Host resolves `verification_profile=node_npm` through provider policy to a fixed provider-owned Node/npm toolchain; caller-supplied path fields are rejected.
- **AC2:** AppContainer can execute `node --version` and `npm --version` through the profile while write attempts to the toolchain root fail.
- **AC3:** A fixture package with a matching admitted dependency capsule completes `npm ci --offline` (or an equivalent deterministic offline install/materialization step) and package-local `npm run typecheck/test/check` without network access.
- **AC4:** Capsule miss, tamper, unsupported manifest revision, expected/actual package-lock digest mismatch and wrong profile all fail closed before a successful verification receipt can be emitted.
- **AC5:** DNS/Internet remains unavailable during profiled verification; no proxy/registry credential or Host user profile is inherited.
- **AC6:** Exact-workspace and Job containment remain effective for npm lifecycle descendants; canonical/protected repository roots remain inaccessible/non-mutable.
- **AC7:** Unprofiled scoped Python/PowerShell behavior and base `host_mutation_sandbox_v1` readiness remain regression-compatible.
- **AC8:** A separately gated Node/npm verification capability/readiness surface is false when configuration/runtime admission is incomplete and true only after a real AppContainer self-check.
- **AC9:** With the admitted canonical `devforge_runtime` seam, `sentinel_local_api describe devforge_runtime` shows the bounded verification selector and a live `execute_scoped` call returns profile/toolchain/capsule/offline/audit evidence without Hub changes.
- **AC10:** Repository tests include policy parsing, path/overlap validation, capsule integrity, environment sanitization, AppContainer ACL, offline execution, descendant containment, readiness, local-api integration and negative security cases.
- **AC11:** Existing CI plus relevant Windows physical-sandbox tests pass; no canonical checkout is used as a mutation workspace.
- **AC12 (non-gating downstream evidence):** After PR-011 has independently satisfied AC1–AC11 and completed its own Acceptance/Completion flow, ChatGPTControlShell PR-015 may consume the accepted capability to obtain real dependency-backed `mcp npm run typecheck` and `mcp npm run check` receipts. This evidence is desirable downstream integration proof but is not required to approve or complete PR-011; PR-015 remains the sole authority for its own completion claim.

## Foundation / UI / Visual Boundaries

```yaml
requirement_artifact_bundle: not_required
ui_semantic_resolution: not_applicable
visual_fidelity: not_applicable
current_task_p0_dependencies: []
satisfied_integration_dependency:
  - PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1
```

Core policy/capsule/sandbox implementation and `devforge_runtime` integration must be planned against current canonical `main@e7064c9bf4fcd15bdb6f5a2678414210c01d1c00`. PR-010 is merged canonical firewall reality, and PR-012's explicit `execution_profile=scoped_mutation` contract is canonical and must remain regression-compatible.

There is no user-facing UI requirement. Security/readiness diagnostics are evidence surfaces, not product UI.
