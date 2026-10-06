# PR-015-direct-codex-development-host-invocation-bridge-v1 — Plan R2

Requirement: `docs/requirements/PR-015-direct-codex-development-host-invocation-bridge-v1.md`, revision 1.

Status: **Pending Plan Review**. No implementation authorization.

## 0. Planning baseline

```yaml
sentinelx_main: 018b78ca20984176d53fbe90039dc795a7f2742f
devforge_main: a13b1113fb3b5938199bad1bf45539eb311ae531
project_execution_binding:
  provider: direct
  adapter: codex
canonical_transport:
  repository: bewaterhere-coder/sentinelx-cloud-core
  pr: 15
  branch: task/direct-codex-development-host-invocation-bridge-v1
live_windows_evidence:
  sentinelx_service_identity: service_context
  active_user_codex_installed: true
  observed_package: "@openai/codex 0.154.0"
  shim_shape: "codex.cmd -> node + @openai/codex/bin/codex.js"
  bootstrap_codebuddy_installation_detected: true
  bootstrap_codebuddy_devforge_user_rule_detected: true
current_failure:
  code: DirectCodexExecutionSurfaceUnavailable
related_tasks:
  PR-013: direct_codex_admission_blocked
  PR-014: host_runtime_workspace_bridge_separate
```

The observed Codex version is evidence only. V1 must discover a compatible installed Codex at runtime and fail closed if its supported invocation contract is unavailable.

## R2 remediation delta

Plan R2 makes only the two corrections required by Plan Review R1. Requirement Revision 1 and the rest of the architecture remain unchanged.

### R2-F1 — Concrete self-host bootstrap path

The one intended bootstrap execution target is:

```text
direct:codebuddy
```

Rationale:

- DevForge already defines the direct CodeBuddy Development Adapter;
- current Windows Host Reality has a CodeBuddy installation and a current-user DevForge rule surface;
- the CodeBuddy adapter is bound to the same canonical transport enforcement contract as Codex and therefore can preserve the exact existing PR #15 / branch rather than creating a replacement transport;
- CodeBuddy is used only as a Task-scoped bootstrap Development Host for this self-host repair. The persistent project binding remains `direct/codex`.

Plan approval does not create this override.

After Plan R2 approval and Slice Set compilation, the only admitted bootstrap request is:

```text
#开发引导执行 PR-015-direct-codex-development-host-invocation-bridge-v1 direct:codebuddy
```

That command must freshly prove, before any implementation mutation:

1. Task remains at `implementation` and Plan R2 is the exact Approved Plan;
2. the current Slice Set is exact and readable;
3. `direct:codebuddy` is still a registered DevForge execution target;
4. current Host Reality still exposes an available CodeBuddy Development Host;
5. exact Requirement/Plan/current Slice pointers can be handed off;
6. canonical transport remains repository `bewaterhere-coder/sentinelx-cloud-core`, PR #15 and branch `task/direct-codex-development-host-invocation-bridge-v1`;
7. the target can write only the exact canonical task transport and cannot create a replacement branch/PR;
8. no permission, write-scope, credential or project-binding expansion is required;
9. durable bootstrap override read-back succeeds.

Failure returns the exact bootstrap contract failure such as `BootstrapTargetUnavailable`, `BootstrapTargetUnregistered`, `BootstrapTransportConflict` or `BootstrapScopeExpansion`.

There is no automatic fallback to Host Runtime, Harness, Codex-through-shell, Cursor, another direct adapter, generic Git or another PR.

The active bootstrap override may remain authoritative for S01-S03. S03 must nevertheless exercise the newly implemented direct-Codex bridge as the **product under test** so the repaired canonical provider path is proven before the override expires when all bound slices complete.

### R2-F2 — Provider-wide firewall/effect composition

The new builtin provider is part of the effective model-facing `local_api` surface and therefore must be represented in PR-010 provider-wide repository-effect readiness.

S01 must use the existing `operation_registry` builtin-provider effect protocol rather than create a second safety inventory.

Required composition:

```text
effective builtin provider map
  ├─ devforge_runtime
  └─ devforge_direct_codex
        ↓
same map supplied to local_api dispatch
AND same map supplied to canonical_repository_mutation_firewall_feature/readiness
        ↓
make_local_api_effect_inventory / classifier
        ↓
provider.repository_effect(action)
        ↓
unknown or uncovered action => readiness false
```

S01 must make the current builtin providers explicit participants in this protocol. In particular:

- `devforge_runtime` must expose deterministic repository-effect metadata for every currently available action;
- lifecycle-only scope actions classify as non-repository mutation;
- `devforge_runtime.execute_scoped` classifies as process mutation with proven coverage only through its existing scoped-mutation containment;
- `devforge_direct_codex.execute_task` classifies as process mutation and may be effective/ready only when its exact sandbox/canonical-checkout containment path is proven;
- a missing/invalid `repository_effect` implementation remains fail-closed;
- adding a future builtin process action without effect metadata must make provider-wide effective-surface readiness false;
- the exact builtin provider map used for model-reachable `local_api` dispatch must also be the map consumed by canonical firewall feature/readiness computation.

This is a composition repair, not a weakening of PR-010 readiness.

## 1. Architecture

### D1 — Dedicated builtin provider

Add a dedicated Agent-owned builtin `local_api` provider, provisionally named:

```text
devforge_direct_codex
```

Do not add a new top-level Hub/MCP tool. Reuse `sentinel_local_api` list/describe/call exactly as PR-007 established for `devforge_runtime`.

External configured local-api name collision remains authoritative under existing local-api rules.

### D2 — Closed action schema

V1 exposes one state-changing action equivalent to:

```yaml
execute_task:
  repository:
    vcs:
    authority:
    path:
  lineage:
    project_id:
    task_id:
    run_id:
    attempt_id:
    slice_id:
  development:
    action: implementation | fixing
    requirement_ref:
    plan_ref:
    findings_ref:
  transport:
    type: github-pr
    pr_number:
    branch:
    expected_remote_sha:
```

All objects are closed-schema.

No fields for executable path, argv, prompt, shell, cwd, workspace path, environment, model, reasoning effort, sandbox bypass, approval override, credentials or replacement transport.

### D3 — Policy-owned direct-Codex readiness

Extend Host policy with a narrow direct-development-host section or equivalent immutable parsed structure.

Policy owns:

- enabled/disabled;
- DevForge workspace root/binding reference;
- supported platform;
- bounded timeout/result limits;
- optional provider-owned executable discovery constraints.

Caller data never owns those values.

Capabilities/readiness advertise a feature such as:

```text
development_host.direct_codex_v1
```

only after live prerequisites are verified.

### D4 — Private active-user process substrate

Do not use `sentinel_exec`, generic `script_run`, `cmd /c <caller text>`, PowerShell, or a caller-selected executable.

Implement a Codex-specific Windows runner. If low-level WTS/user-token code is factored from `user_git.py`, the extracted primitive remains private/internal and accepts a provider-built executable + argv only. It is never registered as an operation or local-api action.

The runner obtains:

- active console user token;
- active-user environment block;
- bounded inherited handles only;
- captured stdout/stderr or provider-owned structured output files.

It never serializes the environment or credential values into result/audit state.

### D5 — Verified Codex executable chain

On Windows, discovery resolves the active user's npm Codex installation and verifies package identity before execution.

Prefer direct execution of:

```text
node.exe
<verified @openai/codex>/bin/codex.js
exec
<provider-owned flags>
```

rather than invoking the `.cmd` shim through a shell.

Verification includes package identity, required file existence/final paths and a supported non-interactive CLI contract. Package version remains evidence.

### D6 — Independent direct-host workspace

Derive workspace from the configured DevForge execution root and exact:

```text
repository identity
+ task_id
+ run_id
+ attempt_id
(+ slice_id)
```

The workspace is never caller selected.

Do not use `git worktree add` against the canonical checkout because that mutates canonical `.git/worktrees` metadata. Use an independent execution checkout/copy whose creation does not modify canonical checkout.

Direct-host workspace identity is evidence for the direct provider only. It must not be projected as PR-013 mutation-scope authority or PR-014 Host Runtime materialization authority.

### D7 — Fixed transport bootstrap

Before Codex invocation, use fixed Git mechanics under the active-user context to obtain the exact existing canonical PR branch.

Required admission:

1. normalize repository identity;
2. resolve repository remote from trusted project/Host inventory;
3. read remote canonical branch head;
4. require `remote_head == expected_remote_sha`;
5. create/fetch independent execution checkout;
6. checkout exactly the canonical task branch;
7. require local HEAD equals expected remote head;
8. verify canonical source checkout was not mutated.

No replacement branch, force push, remote URL override, hooks-based bootstrap or caller Git argv.

Any shared Windows user-token helper remains internal and does not turn `user_git.py` into a general user process API.

### D8 — Deterministic Codex handoff

Generate the Codex input from canonical structured fields, not arbitrary caller prompt.

The provider-generated instruction names:

- exact Task ID;
- exact Requirement/Plan/fix finding paths;
- exact current Slice;
- exact PR and branch;
- one-execute/one-slice constraint;
- forbidden replacement branch/PR;
- required verification and receipt shape.

Codex reads repository artifacts inside the exact workspace.

### D9 — Non-interactive sandboxed execution

Use the installed Codex non-interactive `exec` mode with provider-owned sandbox settings equivalent to workspace-write and no approval escalation.

Provider MUST NOT use or expose dangerous bypass/unrestricted settings.

At capability self-check time, run a harmless fixture proving:

```text
write exact fixture workspace -> succeeds
write sibling protected/canonical-like root -> denied
process exits -> no persistent child
```

No readiness advertisement without the physical negative proof.

### D10 — Result contract

Use Codex structured output support when compatible with the installed CLI, or normalize bounded final output into the same provider result.

Required semantic result:

```yaml
execution:
  provider: direct
  adapter: codex
  task_id:
  run_id:
  attempt_id:
  slice_id:
  exit_disposition:
workspace:
  isolated: true
  canonical_checkout_mutated: false
transport:
  canonical_pr:
  canonical_branch:
  actual_branch:
  expected_remote_sha:
  local_head:
  remote_head_readback:
  consistent:
verification:
  summary:
receipt:
  valid:
```

The bridge does not approve Acceptance or completion.

### D11 — Post-run validation

After Codex exits:

1. inspect actual workspace branch/head;
2. verify no replacement branch is being returned as canonical;
3. query canonical remote branch;
4. require direct-adapter transport consistency;
5. return a receipt only after readback.

If Codex changed only local state and did not persist the canonical branch, result is incomplete/failed rather than a completion claim.

No uncertain run is automatically replayed.

### D12 — Existing security composition and builtin effect inventory

Existing PR-010 firewall semantics continue to govern SentinelX's registered mutation surfaces.

The effective builtin `local_api` provider map MUST be single-source for both dispatch and firewall effect projection. `handlers/__init__.py` must not construct a model-reachable builtin provider set that is absent from `canonical_repository_mutation_firewall_feature(..., builtin_local_api_providers=...)`.

Every builtin provider must expose deterministic `repository_effect(action)` semantics understood by `operation_registry._builtin_effect`. Unknown/missing metadata is intentionally fail-closed.

The existing `devforge_runtime` provider and the new `devforge_direct_codex` provider must both participate. No new parallel operation inventory is introduced.

Because Codex is an external Development Host process, this Task additionally relies on exact workspace isolation and physical sandbox verification to prevent canonical checkout writes by the Codex child itself.

PR-011 scoped verification and PR-013/PR-014 Host Runtime capabilities are not duplicated.

## 2. Implementation slices

Formal Slice Set is compiled only after Plan Review approval.

### S01 — Provider contract, policy and readiness

Objective: establish `devforge_direct_codex` as a bounded builtin provider without executing development mutations.

Expected surfaces:

- new focused direct-Codex provider/runner module;
- policy schema/config example;
- local-api provider wiring;
- capability/readiness projection;
- tests.

Required verification:

- provider absent when disabled;
- closed action schema;
- no executable/argv/prompt/cwd/env fields;
- active-user and Codex package identity discovery;
- fixed Node + codex.js resolution;
- generic `exec` remains disabled where policy disables it;
- one exact builtin provider map drives both `local_api` dispatch and canonical firewall effect projection;
- `devforge_runtime` actions expose deterministic effect metadata and preserve existing scoped-mutation semantics;
- `devforge_direct_codex.execute_task` is process mutation and is not effective/ready until its required containment is proven;
- unknown/missing builtin effect metadata makes provider-wide readiness fail closed;
- regression fixture proves a future process-mutating builtin cannot be silently omitted from effective-surface inventory;
- legacy `script_run`/devforge_runtime behavior otherwise remains unchanged.

### S02 — Workspace/transport bootstrap + bounded Codex execution

Objective: create the isolated direct-host execution workspace, preserve exact github-pr transport, and invoke Codex non-interactively.

Expected surfaces:

- direct-Codex workspace placement;
- fixed user-scoped Git bootstrap;
- deterministic handoff compiler;
- user-scoped Codex process runner;
- bounded process/result lifecycle;
- security tests.

Required verification:

- no canonical checkout worktree metadata mutation;
- exact remote head CAS-style admission before start;
- exact task branch checkout;
- physical workspace-write positive proof;
- physical protected-sibling write denial;
- no shell shim execution boundary;
- no credential/environment leakage;
- timeout/process-tree closure;
- no provider fallback.

### S03 — Direct adapter receipt + live self-host recovery proof

Objective: prove the delivered bridge satisfies DevForge direct/Codex invocation for a real Task without changing the project binding.

Implementation-side verification:

- structured direct/Codex receipt validation;
- actual/canonical PR and branch match;
- remote readback;
- exact Task/Run/Attempt/Slice echo;
- malformed/transport-drift result negatives.

Acceptance owns live Agent activation/restart and the final physical proof.

The acceptance proof SHOULD use the completed bridge to run one bounded direct/Codex task/fixture and then demonstrate that PR-013 can pass the previously failing provider-admission boundary without changing its Task/Plan/Slice or project binding.

## 3. Bootstrap execution boundary

This Task is self-hosting: the persistent project binding requires `direct/codex`, while the missing bridge prevents the current ChatGPT/DevForge path from invoking Codex.

The Plan freezes exactly one bootstrap target: `direct:codebuddy`.

This is not a project rebinding. It is eligible only as a Task-scoped override governed by `system/task-scoped-bootstrap-execution-override-contract.md`.

After Plan R2 is Approved and its Slice Set is compiled, bootstrap authority can be requested only through:

```text
#开发引导执行 PR-015-direct-codex-development-host-invocation-bridge-v1 direct:codebuddy
```

The command must re-read current DevForge Runtime, Task, Approved Plan R2, Slice Set, PR #15 transport and current CodeBuddy Host availability before persisting an override.

Required target binding:

```yaml
target:
  provider: direct
  adapter: codebuddy
scope:
  stages: [implementation]
  max_slice_completions_per_execute: 1
  replacement_branch: forbidden
  replacement_pr: forbidden
  fallback: forbidden
  requirement_change: forbidden
  plan_change: forbidden
  gate_change: forbidden
  acceptance_authority: forbidden
  permission_expansion: forbidden
  write_scope_expansion: forbidden
```

If `direct:codebuddy` is no longer registered/available or cannot preserve the exact PR #15 branch/write boundary, the bootstrap command fails closed. It must not substitute Host Runtime, Harness, Cursor, Codex shell execution, generic Git or another adapter.

The project registry remains `provider: direct / adapter: codex` byte-for-byte unchanged.

During implementation, CodeBuddy is the bootstrap Development Host only. The product being implemented remains the bounded SentinelX bridge to the direct Codex Development Host.

S03 must perform exact-candidate direct-Codex bridge verification before all slices can be treated as complete; successful CodeBuddy implementation alone is not proof that the self-host objective was recovered.

## 4. Acceptance boundary

`#开发验收 PR-015-direct-codex-development-host-invocation-bridge-v1` owns:

1. exact implementation candidate verification;
2. live Windows Agent activation if separately admitted by current acceptance rules;
3. `local_api.list/describe` readback of the direct-Codex provider;
4. physical active-user Codex invocation;
5. workspace isolation negative proof;
6. credential non-disclosure checks;
7. canonical checkout `main + clean` readback;
8. exact PR/branch transport receipt;
9. PR-013 provider-admission recovery proof.

Acceptance MUST NOT use a production Hub modification, generic exec, operator_unrestricted, allowlist widening or provider rebinding.

## 5. Plan invariants

1. For the delivered bridge, Codex remains the Development Host and SentinelX is the bounded invocation transport; the temporary implementation bootstrap may use only the exact Task-scoped `direct:codebuddy` override.
2. Project binding remains `direct/codex`.
3. Hub remains immutable.
4. No generic run-as-user API.
5. No arbitrary command/shell/argv/cwd/env/prompt surface.
6. Canonical repository remains `main + clean`.
7. Direct-host workspace semantics do not masquerade as PR-013/PR-014 Host Runtime authority.
8. One `#开发执行` still completes at most one Slice.
9. No Receipt, No Completion Claim.
