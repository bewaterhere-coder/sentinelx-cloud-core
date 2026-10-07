---
task_id: PR-015-direct-codex-development-host-invocation-bridge-v1
title: SentinelX Direct Codex Development Host Invocation Bridge V1
project_id: sentinelx-cloud-core
repository: bewaterhere-coder/sentinelx-cloud-core
requirement_revision: 2
development:
  stage: acceptance
  implementation_execution_complete: true
  gates:
    requirement_ready: true
    plan_approved: true
    acceptance_approved: false
    completion_verified: false
  plan_revision: 6
  implementation_authorized: true
  latest_plan_review: approved_round_6
  latest_plan_remediation: r6_applied
  review_disposition: approved
  next_expected_actor: operator
  acceptance_disposition: blocked_external_activation
  blocking_findings:
    - Exact PR-015 candidate is now active on the live Host as 0.24.1.dev499+g02eb3de2e in session sess_5306a4882c3f.
    - Live Host config C:\\ProgramData\\SentinelX\\config.yaml has no direct_codex block; local_api.describe(devforge_direct_codex) fails closed with endpoint_not_available and requires explicit direct-codex Host policy opt-in.
    - Requirement R3 requires explicit Host policy opt-in and Plan R6 requires live activation only when separately admitted; #开发验收 does not implicitly grant that Host-policy mutation.
    - AC12 remains blocked until separately admitted Host opt-in exposes devforge_direct_codex, one live persisted direct/Codex run succeeds, and PR-013 direct/Codex provider admission succeeds without Task/Plan/Slice/project-binding change.
  authorization:
    mode: durable
    ref: docs/authorizations/PR-015-direct-codex-development-host-invocation-bridge-v1-development-authorization.yaml
artifacts:
  plan: docs/plans/PR-015-direct-codex-development-host-invocation-bridge-v1-plan.md
  plan_blob_sha: 2bcea2a44f88e51c8b9378ba6297b61897e638da
  latest_plan_review: docs/reviews/PR-015-direct-codex-development-host-invocation-bridge-v1-plan-review-r6.md
  latest_plan_review_blob_sha: 5e6ff106b7d5befcae4fccc77d83ddae3c674764
  prior_plan_review_r5: docs/reviews/PR-015-direct-codex-development-host-invocation-bridge-v1-plan-review-r5.md
  prior_plan_review_r4: docs/reviews/PR-015-direct-codex-development-host-invocation-bridge-v1-plan-review-r4.md
  prior_plan_review_r3: docs/reviews/PR-015-direct-codex-development-host-invocation-bridge-v1-plan-review-r3.md
  prior_plan_review: docs/reviews/PR-015-direct-codex-development-host-invocation-bridge-v1-plan-review-r2.md
  historical_plan_review_r1: docs/reviews/PR-015-direct-codex-development-host-invocation-bridge-v1-plan-review-r1.md
  latest_plan_remediation: docs/checkpoints/PR-015-direct-codex-development-host-invocation-bridge-v1-plan-remediation-r6-20261007.yaml
  prior_plan_remediation_r5: docs/checkpoints/PR-015-direct-codex-development-host-invocation-bridge-v1-plan-remediation-r5-20261007.yaml
  prior_plan_remediation_r4: docs/checkpoints/PR-015-direct-codex-development-host-invocation-bridge-v1-plan-remediation-r4-20261007.yaml
  prior_plan_remediation: docs/checkpoints/PR-015-direct-codex-development-host-invocation-bridge-v1-plan-remediation-r2-20261006.yaml
  prior_execution_slice_set: docs/execution/PR-015-direct-codex-development-host-invocation-bridge-v1-slices.yaml
  requirement_change_impact: docs/reviews/PR-015-direct-codex-development-host-invocation-bridge-v1-requirement-r2-impact-analysis.md
  historical_slice_impact_r3: docs/execution/PR-015-direct-codex-development-host-invocation-bridge-v1-plan-r3-slice-impact.yaml
  historical_slice_impact_r4: docs/execution/PR-015-direct-codex-development-host-invocation-bridge-v1-plan-r4-slice-impact.yaml
  prior_slice_impact: docs/execution/PR-015-direct-codex-development-host-invocation-bridge-v1-plan-r5-slice-impact.yaml
  approved_slice_impact: docs/execution/PR-015-direct-codex-development-host-invocation-bridge-v1-plan-r6-slice-impact.yaml
  current_execution_slice_set: docs/execution/PR-015-direct-codex-development-host-invocation-bridge-v1-plan-r6-slices.yaml
  current_execution_slice_set_blob_sha: 8aeb1892a4b3a5d61ae8747b3067b87b4f97b23c
  latest_slice_checkpoint: docs/checkpoints/PR-015-direct-codex-development-host-invocation-bridge-v1-s04-completion-20261007.yaml
  latest_slice_checkpoint_blob_sha: c1191c57146ea35efd821f1d2b234c506fa25fba
  latest_slice_completion_receipt: docs/reviews/PR-015-direct-codex-development-host-invocation-bridge-v1-s04-completion-receipt.yaml
  latest_slice_completion_receipt_blob_sha: bb842ee9179d94a9661be67114f32a84950a93a6
  exact_product_candidate: 02eb3de2ec9c137b3285398e555f1e037b574965
  implementation_evidence_head: 783af5cacdaab9b325c48e2bbd4acded63109b02
  execution_reconciliation_receipt: docs/reviews/PR-015-direct-codex-development-host-invocation-bridge-v1-s04-execution-reconciliation-receipt.yaml
  execution_reconciliation_receipt_blob_sha: bd1a9d9b9c12b8c001d60845ef831b2be8b50dd4
  implementation_to_acceptance_transition_receipt: docs/reviews/PR-015-direct-codex-development-host-invocation-bridge-v1-implementation-to-acceptance-transition-receipt.yaml
  implementation_to_acceptance_transition_receipt_blob_sha: 31291ffb38ee22dbcfd4a5020198a1ceb6be940c
  latest_acceptance_checkpoint: docs/checkpoints/PR-015-direct-codex-development-host-invocation-bridge-v1-acceptance-r4-host-opt-in-blocked-20261007.yaml
  latest_acceptance_checkpoint_blob_sha: fb5faa527569a2c6271e2428cc93b20077968c93
  prior_slice_checkpoint: docs/checkpoints/PR-015-direct-codex-development-host-invocation-bridge-v1-s03-completion-20261007.yaml
  prior_slice_completion_receipt: docs/reviews/PR-015-direct-codex-development-host-invocation-bridge-v1-s03-completion-receipt.yaml
  prior_acceptance: docs/reviews/PR-015-direct-codex-development-host-invocation-bridge-v1-acceptance-r1.md
  prior_acceptance_checkpoint: docs/checkpoints/PR-015-direct-codex-development-host-invocation-bridge-v1-acceptance-r1-decision-required-20261007.yaml
  acceptance_invalidation: docs/reviews/PR-015-direct-codex-development-host-invocation-bridge-v1-acceptance-r1-invalidation-r2.md
  planning_checkpoint: docs/checkpoints/PR-015-direct-codex-development-host-invocation-bridge-v1-requirement-r2-plan-r3-ready-for-review-20261007.yaml
implementation_entry:
  bootstrap_required: true
  intended_target: direct:codebuddy
  override_state: expired
  override_ref: docs/overrides/PR-015-direct-codex-development-host-invocation-bridge-v1-bootstrap-execution-override.yaml
  override_blob_sha: cc39aae1ec928c07dfac5b25e30185977a15a18a
  override_receipt_ref: docs/checkpoints/PR-015-direct-codex-development-host-invocation-bridge-v1-bootstrap-override-r6-20261007.yaml
  prior_override_ref: docs/overrides/PR-015-direct-codex-development-host-invocation-bridge-v1-bootstrap-execution-override.yaml
  effective_provider: null
  project_binding_fallback:
    provider: direct
    adapter: codex
  explicit_command: "#开发引导执行 PR-015-direct-codex-development-host-invocation-bridge-v1 direct:codebuddy"
transport:
  type: github-pr
  pr_number: 15
  branch: task/direct-codex-development-host-invocation-bridge-v1
  base_branch: main
requirement_readiness:
  result: Ready
  depth: deep
  ui_semantics:
    applicability: NotApplicable
  refinement_evidence:
    canonical_main_at_creation: 018b78ca20984176d53fbe90039dc795a7f2742f
    project_binding: direct/codex
    live_host_codex_package_observed: "@openai/codex 0.154.0"
    live_host_codex_shim_observed: "active-user npm codex.cmd -> node + @openai/codex/bin/codex.js"
    current_blocker: null
    implementation_execution_complete: true
    all_current_plan_slices_completed: true
    bootstrap_override_expired_by_slice_completion: true
    pr013_relation: related_unblocker_not_same_task
---

# Requirement

## Problem

The DevForge project binding for `sentinelx-cloud-core` remains explicitly:

```yaml
execution_binding:
  provider: direct
  adapter: codex
```

Requirement Revision 1 and Plan R2 delivered the bounded Agent-owned `devforge_direct_codex` bridge, isolated execution workspace, active-user Codex invocation, containment, exact transport admission and structured receipt validation.

Acceptance R1 then exposed the remaining end-to-end gap on the real host: the installed Codex Development Host performs implementation edits and verification inside the isolated checkout but does not create a Git commit. The checkout therefore remains dirty at the admitted head; provider publication does not fire; the bridge correctly returns `implementation_not_persisted`.

The persistence owner must be deterministic and cannot depend on model compliance. At the same time, the repair must not create a generic Git/shell surface, replacement transport, force push, canonical-checkout mutation, permission expansion or provider rebinding.

`repository_transaction_v1` remains owned by PR-013, and production `mcp.sentinelx.app` remains an immutable external transport boundary.

## Goal

Complete the existing direct/Codex bridge by adding **provider-owned deterministic commit-on-publish** after successful bounded Codex execution:

```text
DevForge Task/Plan/Slice authority
+ direct/codex provider identity
+ canonical PR/branch/expected-head lock
+ active-user Codex authentication context
+ isolated DevForge execution workspace
+ bounded non-interactive Codex invocation
+ provider-owned deterministic commit of eligible checkout changes
+ ordinary fast-forward publication to the same canonical PR branch
+ independent remote readback
+ persisted direct/codex receipt
```

Codex remains the Development Host. SentinelX remains the bounded invocation, persistence and transport enforcement layer and does not reinterpret the project binding as `host-runtime`.

## Scope

V1 targets Windows because the concrete blocker is a LocalSystem SentinelX service plus an installed active-user Codex CLI.

The bridge is projected through the existing model-facing `sentinel_local_api` envelope as an Agent-owned builtin provider. Hub source/schema/deployment changes are out of scope.

The implementation may introduce a private Windows active-user process primitive only if it remains non-model-facing and can be called only by fixed, policy-owned brokers. It must not become a generic run-as-user or arbitrary command primitive.

## Required behavior

### R1 — Preserve direct/Codex execution identity

A successful invocation represents:

```text
execution provider = direct
development adapter = codex
development host = Codex
capability transport = SentinelX Agent builtin local_api
```

The bridge MUST NOT report or persist `host-runtime` as the execution provider merely because SentinelX carries the invocation.

### R2 — Agent-owned structured projection

The bridge MUST be discoverable through existing `local_api.list/describe/call`.

V1 SHOULD use a dedicated builtin provider identity such as `devforge_direct_codex` rather than widening generic `script_run` or `exec`.

Production Hub modification is forbidden.

### R3 — Explicit Host policy opt-in

The provider is unavailable unless the Host explicitly opts in to direct Codex execution.

Readiness MUST fail closed when any required component is absent, including supported platform, active user session, Codex executable identity, workspace root, or required sandbox behavior.

Tool/provider availability is not inferred merely because a `codex.cmd` file exists.

### R4 — Fixed executable identity; no shell wrapper authority

The caller MUST NOT supply an executable path, shell, command string, arbitrary argv, Node path, npm path, or Codex package path.

On Windows the provider MUST resolve and verify the active user's installed Codex package and execute a fixed provider-owned chain equivalent to:

```text
verified node executable
+ verified @openai/codex/bin/codex.js
+ provider-owned codex exec arguments
```

A `.cmd`/PowerShell shim may be inspected for discovery evidence but MUST NOT turn `cmd.exe /c <caller text>` or PowerShell into the execution boundary.

Version is runtime evidence, not project binding. The observed `@openai/codex 0.154.0` is not a permanent version pin.

### R5 — Active-user identity without credential exposure

Codex MUST run under the active interactive Windows user's token/environment so it can reuse that user's existing Codex login state.

The Agent MUST NOT read, return, persist, log, copy, or proxy Codex tokens, ChatGPT credentials, browser cookies, API keys, SSH keys, credential-helper secrets, or equivalent authentication material.

No caller-supplied credential/environment fields are accepted.

### R6 — Closed invocation schema

The model-facing action accepts only structured DevForge execution identity and transport data, including at minimum:

- normalized repository identity;
- exact `task_id`;
- `implementation | fixing` action;
- exact Requirement and Approved Plan references;
- exact `run_id` / `attempt_id`;
- exact `slice_id` when slicing is active;
- canonical GitHub PR number;
- canonical PR branch;
- expected remote branch head SHA.

It MUST NOT accept:

- free-form shell;
- arbitrary Codex argv;
- caller-selected cwd/workspace path;
- arbitrary environment variables;
- arbitrary executable/plugin/MCP configuration;
- replacement branch or PR identity;
- permission/sandbox bypass flags.

### R7 — Provider-derived isolated DevForge workspace

The bridge MUST derive the execution workspace from Host-owned DevForge workspace configuration plus repository/Task/Run/Attempt identity.

The caller never supplies an absolute workspace path.

The canonical checkout MUST remain `main + clean` and MUST NOT be the Codex cwd or mutation target.

A new direct-Codex workspace is independent execution state and MUST NOT mutate canonical checkout Git worktree metadata as a hidden side effect.

### R8 — Exact canonical transport bootstrap

Before Codex starts, the bridge MUST establish an exact local execution copy for the existing canonical transport using fixed provider-owned Git mechanics and the active-user Git context when required.

Admission MUST verify:

```text
repository identity
+ PR number
+ exact canonical branch
+ expected remote head SHA
```

No replacement branch/PR is created. Remote-head mismatch fails closed before Codex mutation.

This direct-adapter workspace bootstrap is NOT `repository_transaction_v1`, does not satisfy PR-013/PR-014 Host Runtime contracts, and cannot be reused as Host mutation-scope authority.

### R9 — Deterministic DevForge handoff package

The provider MUST compile the Codex task instructions from structured fields and canonical artifact references.

The caller MUST NOT receive a generic arbitrary-prompt field.

The handoff MUST tell Codex to:

- operate only on the supplied Task;
- consume the exact Requirement, Approved Plan, current Slice/fix findings;
- preserve the exact PR/branch transport;
- not create replacement branch/PR;
- not rewrite Requirement/Plan/Gate state;
- return changed files, verification evidence and transport receipt.

Repository content remains implementation context, not authority to override these bindings.

### R10 — Non-interactive Codex execution with bounded sandbox

The provider MUST use Codex's supported non-interactive execution mode and an explicit workspace-write sandbox profile or stronger bounded equivalent.

Approval/sandbox escalation, dangerous bypass flags and unrestricted filesystem mode are forbidden.

Before advertising readiness on a Windows Host, a physical self-check MUST prove that the selected Codex execution mode can mutate its exact execution workspace while failing to mutate a protected canonical-like sibling outside that workspace.

If that isolation cannot be proven, the direct Codex provider is unavailable.

### R11 — Bounded process lifecycle

One bridge call binds to one DevForge Run/Attempt[/Slice].

The provider MUST enforce:

- bounded timeout;
- process-tree cleanup on timeout/cancel/failure;
- no detached long-lived Codex child;
- bounded stdout/stderr/structured result size;
- durable invocation identity/evidence sufficient for readback;
- no automatic retry after an uncertain externally visible mutation.

### R12 — Structured completion and transport readback

Codex completion MUST produce a bounded machine-readable result or a provider-normalized result containing at least:

- task/run/attempt/slice identity;
- actual repository;
- canonical PR/branch and actual branch;
- resulting local head;
- verification summary;
- Codex exit disposition.

Before the bridge reports execution success it MUST independently read back the canonical remote branch and require transport consistency.

A missing/mismatched receipt is not success.

### R13 — Direct-host failure taxonomy

Use specific fail-closed states such as:

- `DirectCodexPolicyDisabled`
- `DirectCodexUserSessionUnavailable`
- `DirectCodexExecutableUnavailable`
- `DirectCodexExecutableIdentityMismatch`
- `DirectCodexWorkspaceAdmissionFailed`
- `DirectCodexTransportDrift`
- `DirectCodexSandboxUnavailable`
- `DirectCodexInvocationFailed`
- `DirectCodexTimeout`
- `DirectCodexReceiptInvalid`

Failure MUST NOT switch execution provider automatically.

### R14 — No generic-execution expansion

This Task MUST NOT solve the problem by:

- enabling generic `exec`;
- making `script_run` an arbitrary direct-host launcher;
- adding caller-supplied shell/argv/cwd/env;
- enabling `operator_unrestricted`;
- widening command/file allowlists;
- exposing a generic run-as-user primitive;
- allowing direct writes in canonical checkout;
- modifying production Hub.

### R15 — Composition with existing work

- PR-013 remains an independent Task and keeps ownership of Host Runtime `repository_transaction_v1`.
- PR-014 remains an independent Task and keeps ownership of Host Runtime DevForge execution-workspace materialization.
- PR-011 verification/toolchain semantics on current `main` remain canonical and must not regress.
- PR-010 canonical repository mutation firewall remains mandatory for existing SentinelX operations.
- This Task may unblock PR-013's **direct/Codex Development Host admission**, but it does not change PR-013's Plan, Slice or transport.

## Requirement Revision 2 — Provider-Owned Deterministic Commit-on-Publish

Acceptance R1 proved that the real installed Codex Development Host can perform bounded edits and verification inside the isolated execution checkout but does not create a Git commit. Requirement Revision 2 resolves persistence ownership explicitly: after a successful Codex run, the bounded `devforge_direct_codex` provider owns deterministic local persistence and canonical publication of the exact checkout changes.

### R16 — Provider-owned deterministic persistence and publication

When Codex exits successfully and the isolated checkout contains eligible implementation changes, the provider MUST:

1. revalidate exact repository, Task, Run, Attempt, Slice, workspace, canonical PR, canonical branch and expected remote head;
2. independently require that the canonical remote branch still equals the admitted `expected_remote_sha` before persistence/publication;
3. derive the candidate path set from the isolated checkout itself; the caller cannot supply Git argv, pathspecs, commit message, author identity, remote URL or branch;
4. exclude provider control/evidence artifacts from the implementation commit and fail closed on unmerged state, unsupported gitlinks/submodule mutation, repository metadata mutation or any path that escapes the isolated checkout;
5. use only fixed provider-owned Git primitives with shell execution, hooks, signing and interactive prompts disabled;
6. create exactly one provenance-bound commit whose parent is the admitted expected head and whose Task/Run/Attempt/Slice identity is deterministically represented in provider-owned commit metadata/message;
7. publish only by ordinary fast-forward push to the existing canonical PR branch; replacement transport and force push are forbidden;
8. independently read back the remote branch and require it to equal the provider-created candidate commit before returning success;
9. never mutate the canonical checkout and never widen filesystem, credential, permission or execution authority;
10. never automatically retry an uncertain externally visible publication. After uncertainty, readback determines whether the candidate was published.

If Codex leaves dirty/uncommitted eligible work and the provider cannot complete this bounded persistence protocol, the result remains fail-closed and MUST NOT be reported as successful canonical execution.

If the checkout contains no eligible implementation change, the provider MUST NOT fabricate an empty implementation commit merely to manufacture a success receipt; the result contract must distinguish a verified no-change outcome from persisted implementation.

The provider's persistence role does not change execution identity:

```text
execution provider = direct
development adapter = codex
development host = Codex
transport/persistence broker = SentinelX devforge_direct_codex
```

## Acceptance criteria

- **AC1:** `local_api.describe` exposes one bounded direct-Codex provider/action with no arbitrary command/executable/cwd/env/prompt fields.
- **AC2:** Provider readiness is absent/false when Host opt-in, active-user session, Codex executable identity, workspace binding or physical sandbox proof is unavailable.
- **AC3:** On an admitted Windows Host, exact installed Codex executes non-interactively under the active user's identity without SentinelX returning credential material.
- **AC4:** The provider creates/uses only the derived DevForge execution workspace; canonical checkout remains unchanged and `main + clean`.
- **AC5:** A physical negative test proves Codex cannot write a canonical-like protected sibling outside the exact workspace.
- **AC6:** Exact PR/branch/expected-head mismatch fails before implementation mutation.
- **AC7:** Codex receives the exact Requirement/Plan/Slice transport lock and cannot obtain a replacement transport from the bridge.
- **AC8:** One real direct/Codex fixture execution that produces eligible changes is deterministically committed by the provider, fast-forward published to the exact canonical PR branch, independently read back, and returns a valid persisted receipt with exact Task/Run/Attempt/Slice and transport identity.
- **AC9:** Timeout/nonzero/malformed receipt/transport drift returns a specific failure and no success claim.
- **AC10:** Existing `script_run`, `devforge_runtime`, mutation-scope, repository firewall and verification tests remain passing.
- **AC11:** No generic `exec`, no `operator_unrestricted`, no allowlist/permission widening, no Hub mutation.
- **AC12:** After live activation, the bridge can complete one real persisted direct/Codex execution end to end and `#开发执行 PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1` can pass direct/Codex provider admission without changing PR-013 Task identity or project binding.

## Requirement Challenge

### Challenge 1 — Why not just enable `sentinel_exec codex`?

Rejected. That creates or expands a generic command surface and does not preserve the direct-adapter execution contract.

### Challenge 2 — Why not call `codex.cmd` through `script_run`?

Rejected. `script_run` is currently governed by Host mutation execution-profile policy; using it as a wrapper bypass would collapse two distinct execution-provider boundaries.

### Challenge 3 — Why not change the project binding to `host-runtime`?

Rejected. The current project binding is explicitly `direct/codex`; PR-014 also shows the Host Runtime workspace path is a separate incomplete capability. Provider substitution is not a repair.

### Challenge 4 — Why active-user execution?

The installed Codex login is user-scoped while SentinelX runs as a service identity. A fixed active-user broker is the narrowest way to reuse existing authentication without copying credentials.

### Challenge 5 — Why not make the active-user broker generic?

Rejected. A generic run-as-user primitive would become a privilege/credential-context expansion surface. Only fixed Codex and existing fixed Git brokers may use any shared internal token mechanics.

## Bootstrap implementation note

This Task repairs the exact capability needed by the current `direct/codex` project binding to execute it. After Plan approval, implementation admission SHOULD evaluate DevForge's Task-Scoped Bootstrap Execution Override contract rather than weakening the project binding or inventing a fallback.

The bootstrap override itself requires its own explicit canonical command and is not granted by this Requirement.

## Non-goals

- replacing DevForge's Codex adapter;
- changing the project-wide execution binding;
- implementing a generic coding-agent launcher;
- implementing arbitrary shells or run-as-user commands;
- modifying Codex itself;
- implementing PR-013 repository transactions;
- implementing PR-014 Host Runtime workspace materialization;
- modifying production Hub;
- production release/deployment.
