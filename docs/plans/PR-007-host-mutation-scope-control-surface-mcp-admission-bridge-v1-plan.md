# PR-007 — Host Mutation Scope Control Surface & MCP Admission Bridge V1 — Plan

## Plan State

```yaml
task_id: PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1
requirement_revision: 2
stage: fixing
plan_status: approved
implementation_authorized: true
plan_revision: 4
requirement: docs/requirements/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1.md
requirement_change_invalidation: docs/reviews/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-requirement-r2-invalidation.md
prior_plan_review: docs/reviews/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-plan-review-r3.md
current_plan_review: docs/reviews/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-plan-review-r4.md
current_acceptance_review: docs/reviews/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-acceptance-r2.md
execution_slice_set: docs/execution/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-r4-slices.yaml
transport: github-pr
pr_number: 7
task_branch: task/host-mutation-scope-control-surface-mcp-admission-bridge-v1
base_branch: main
planning_baseline_main: f7e878f3497582547e5d52cd33b060cae18d2e84
```

## Objective

Complete PR-007 without modifying or depending on modification of the closed-source production Hub.

Target composition:

```text
ChatGPT sentinel_local_api
→ existing Hub local_api transport (immutable external boundary)
→ Agent local_api handler
→ built-in devforge_runtime endpoint
→ existing provider-owned mutation scope lifecycle
→ existing scoped script executor
→ existing AppContainer + audit + Job containment
→ terminal scope readback
```

Plan Revision 4 preserves the Revision-3 architecture and remediates only Plan Review R3 findings F1-F3. It preserves verified provider/security work from S01-S04 and does not replay those completed side effects.

## Current Verified Reality

Planning baseline remains canonical `main@f7e878f3497582547e5d52cd33b060cae18d2e84` plus the existing PR-007 branch implementation.

Verified facts:

- PR-007 already contains the bounded `mutation_scope` lifecycle handler over `MutationScopeStore`.
- existing scope admission includes exact generation, repository, semantic lineage and provider-owned operation-class checks.
- existing scoped execution is implemented by `make_profiled_script_run_handler(...)` / `_run_scoped(...)`; it owns AppContainer, audit, materialization, spawn and terminalization semantics.
- `local_api` is already a first-class Agent operation implemented by `src/sentinelx_core/handlers/local_api.py` and `src/sentinelx_core/local_api.py`.
- current registry registers `local_api` only when `policy.local_apis` is non-empty.
- current configured `local_api` endpoints are operator-named external HTTP/JSON-RPC targets.
- current registry applies `policy.disabled_ops` after handlers are assembled, making a disabled top-level operation both unadvertised and unreachable.
- current scoped execution can return `workdir` and `script_path` when called with `cleanup=false`; that debugging response must not become part of the new model-facing built-in contract.
- the current ChatGPT model surface exposes `sentinel_local_api`; a live call reached the connected Agent and returned Agent-level `unsupported_op`, proving the Hub already transports this operation without any new Hub schema.
- production Hub source/deployment is outside repository/user control and is not an implementation target for this Plan.

## Retained Verified Prerequisites

The following completed Revision-2 evidence remains applicable and MUST NOT be replayed:

```text
S01 — authority admission + exact bound readback
S02 — mutation_scope lifecycle handler + provider-owned purpose mapping
S03 — registry/capability/operator contract projection for mutation_scope
S04 — existing scoped execution composition + Windows security regressions
```

Their checkpoints remain historical evidence. Revision 4 consumes their resulting implementation state but creates no new current Slice identity for them. The old S05 generic-Hub `/op mutation_scope` objective remains superseded.

## Authoritative Decisions

### D1 — Hub is immutable external infrastructure

No implementation Slice may require source/config/deployment changes to `mcp.sentinelx.app`.

The only Hub assumption used by PR-007 is the already observed, model-facing `sentinel_local_api` envelope. Acceptance must re-read this live surface; repository code cannot claim Hub availability by itself.

### D2 — Extend `local_api` with a built-in endpoint provider, not a fake socket profile

Add an Agent-owned built-in endpoint namespace alongside existing host-configured external endpoints.

Canonical built-in endpoint name:

```text
devforge_runtime
```

Do not encode it as a fabricated Unix socket/stdio `LocalApiEndpoint` and do not require operators to point YAML at the Agent itself.

Preferred structure:

```text
local_api handler
├─ configured external endpoint provider (existing)
└─ built-in endpoint provider registry (new, bounded)
    └─ devforge_runtime
```

The built-in provider owns list/describe/call metadata and action dispatch only. Provider authority remains in the existing mutation-scope/scoped-execution modules.

### D3 — Existing mutation policy is the Host opt-in boundary

The built-in `devforge_runtime` endpoint is eligible only when the Host has explicitly configured/enabled scoped mutation under the existing `mutation_execution` policy.

Rules:

- shipping a new Agent version alone MUST NOT grant mutation authority;
- a Host without configured/enabled scoped mutation must not expose usable `devforge_runtime` mutation actions;
- readiness failures remain action-level fail-closed diagnostics rather than triggers for fallback;
- existing configured external `local_apis` retain their prior behavior and authority model;
- the registry may expose `local_api` when either at least one configured external endpoint exists or an eligible non-colliding built-in endpoint exists; it must not expose `local_api` when neither exists.

### D4 — Make `local_api` context-aware without changing external endpoint semantics

The built-in execution path needs authoritative transport `RequestContext`; therefore the `local_api` handler becomes context-aware.

For configured external endpoints:

- context is not forwarded to the external service unless an existing declared contract already does so;
- request templates, compatibility checks, projection and allowlists remain unchanged;
- no payload value may overwrite transport request ID, opaque ref, receive time or actual outer operation.

For built-in `devforge_runtime`, the same immutable outer `RequestContext` is passed to the canonical internal execution function.

### D5 — Reuse one canonical scope-lifecycle service seam

Do not duplicate lifecycle parser/store logic already implemented in `handlers/mutation_scope.py`.

Both:

```text
Agent op=mutation_scope
and
local_api endpoint=devforge_runtime lifecycle actions
```

must compose one canonical provider-owned lifecycle service/helper.

The direct `mutation_scope` handler may keep its transport-op assertion as an adapter guard; the shared lifecycle service accepts validated action input and delegates to the same `MutationScopeStore` authority.

The shared service remains responsible for purpose mapping, strict repository/lineage/scope parsing, provider-only operation-class mapping, bounded response projection, and provision/revalidate/inspect/terminalize. No second scope ledger or independent lifecycle semantics are allowed.

### D6 — `execute_scoped` composes the existing profiled script handler

`devforge_runtime.execute_scoped` does not implement process execution.

It validates a bounded action payload, rejects authority/profile override fields, constructs the existing scoped-script payload with the internal constant:

```text
execution_profile = scoped_mutation
cleanup = true
```

and calls the existing profiled script execution path with the exact current `RequestContext`.

Allowed caller execution inputs are limited to:

```text
content
interpreter
args
cwd
env
timeout
scope_ref
repository
lineage
```

Caller `cleanup` is not accepted in V1. Caller `cleanup=false` or any cleanup override is rejected as `invalid_payload` before invoking the scoped executor.

Forbidden fields include caller-selected:

```text
execution_profile
cleanup
workspace/workspace_root/workspace_id authority
authorized write roots/protected roots
operation classes
sandbox identity
operator_unrestricted
legacy compatibility selector
```

The existing scoped path remains the single owner of revalidation, audit START, evidence materialization, AppContainer activation, spawn, finish and terminalization.

The built-in adapter MUST project the inner result onto an explicit allowlist. V1 may return only bounded execution/receipt fields such as:

```text
ok
interpreter
returncode
timed_out when present
output bounded by existing response limits
execution_profile = scoped_mutation
audit_operation_id
mutation_scope_ref
terminal_state
```

It MUST discard `workdir`, `script_path`, exact workspace paths, command/argv paths when they reveal provider-private placement, provider-private roots, and any unrecognized future inner-handler field. This is a positive response allowlist, not a denylist.

### D7 — Built-in endpoint schema is self-describing and policy-filtered

`operation=list` includes `devforge_runtime` only when the built-in endpoint is eligible, not shadowed by a configured external name collision, and has at least one policy-admitted action.

`operation=describe endpoint=devforge_runtime` returns:

```text
provider_kind = builtin
contract_id = devforge_runtime
contract_revision = 1
bounded action metadata
machine-readable nested parameter schemas
```

Action metadata MUST be computed from the same Host policy used by direct `call` admission. An action disabled by policy is not advertised.

Required conceptual actions are:

```text
provision_scope
revalidate_scope
inspect_scope
terminalize_scope
execute_scoped
```

subject to D11 transitive disable rules.

### D8 — Lifecycle actions map to existing semantics, not new authority

Conceptual calls:

```yaml
operation: call
endpoint: devforge_runtime
action: provision_scope
params:
  purpose: scoped_script
  repository: {...}
  lineage: {...}
```

```yaml
operation: call
endpoint: devforge_runtime
action: execute_scoped
params:
  scope_ref: {scope_id: ..., generation: 1}
  repository: {...}
  lineage: {...}
  interpreter: python3 | powershell | pwsh
  content: ...
  args: []
  cwd: .
```

```yaml
operation: call
endpoint: devforge_runtime
action: inspect_scope
params:
  scope_ref: {scope_id: ..., generation: 1}
  repository: {...}
  lineage: {...}
```

The lifecycle calls reuse the canonical lifecycle service. `execute_scoped` reuses the canonical scoped executor.

### D9 — No PR-008 / PR-009 execution dependency

PR-007 Revision 4 does not wait for dedicated `sentinel_script_run` model schema expansion, Hub dynamic projection, or Hub source/deployment binding.

PR-008 and PR-009 may continue independently. Shared-code drift must still be reconciled if it changes the local implementation seam, but their workflow state does not block PR-007 by itself.

### D10 — Live acceptance uses the actual model-visible `sentinel_local_api`

After implementation and known-build activation, acceptance runs:

```text
1. sentinel_local_api list
2. sentinel_local_api describe(devforge_runtime)
3. verify provider_kind=builtin + contract_revision=1
4. provision_scope
5. execute_scoped harmless deterministic marker
6. inspect_scope
7. verify terminal state + exact repository/lineage binding
8. negative mismatch and disabled-action checks
9. reconfirm direct Python exec remains denied when not allowlisted
```

No `/op mutation_scope` call is required for acceptance.

### D11 — `disabled_ops` applies transitively to built-in actions

Plan Review R3 F1 is closed by making action admission derive from the existing `policy.disabled_ops`; no new deny-list authority is introduced.

Rules:

1. `disabled_ops` containing `local_api` removes the entire outer `local_api` operation through the existing registry removal path.
2. `disabled_ops` containing `mutation_scope` makes all lifecycle actions unavailable through `devforge_runtime`:
   - `provision_scope`
   - `revalidate_scope`
   - `inspect_scope`
   - `terminalize_scope`
3. `disabled_ops` containing `script_run` makes `execute_scoped` unavailable through `devforge_runtime`.
4. `list`/`describe` filter actions using the same derived admission function used by `call`.
5. `call` independently checks admission and fails closed even when the caller never called `describe` or cached stale metadata.
6. If policy filtering leaves no built-in action, the built-in endpoint is not listed. Configured external endpoints remain independently governed by their existing profiles.

This preserves the current semantic that disabling an operation removes all routes to that operation's authority.

### D12 — Built-in/external name collision is fail-closed for the built-in

Plan Review R3 F3 is closed by preserving configured external endpoint meaning.

For endpoint name `devforge_runtime`:

- an operator-configured external `policy.local_apis["devforge_runtime"]` retains its exact existing meaning and is never reinterpreted, replaced, merged, or shadowed by the built-in provider;
- on that Host the built-in `devforge_runtime` provider is unavailable because the name is occupied;
- `list`, `describe`, and `call` resolve the same external provider deterministically;
- the Agent emits a stable non-secret diagnostic for the built-in collision in capabilities/help or local diagnostics, without changing the external endpoint response shape;
- the built-in provider is accepted in live PR-007 evidence only when `describe` proves `provider_kind=builtin`, `contract_id=devforge_runtime`, and `contract_revision=1`.

No automatic renaming or namespace migration is introduced in V1.

### D13 — Model-facing execution response is explicitly bounded

Plan Review R3 F2 is closed by two independent controls:

1. caller cleanup override is rejected and the inner scoped execution is always invoked with `cleanup=true`;
2. the adapter projects the returned result through the positive allowlist in D6.

Tests must include a synthetic inner result containing `workdir`, `script_path`, unexpected future path fields and unrelated extra fields and prove none escape the built-in response.

## Error / Security Semantics

Reuse existing provider classifications where applicable. Adapter-level classifications remain minimal and machine-readable, including equivalents of:

```text
endpoint_not_configured / endpoint_not_available
builtin_endpoint_name_conflict
operation_disabled
unknown_action
invalid_payload
HostMutationSandboxUnavailable
HostMutationScopeConflict
HostMutationScopeNotCurrent
HostMutationScopeBindingMismatch
HostMutationScopeOperationNotAllowed
HostMutationScopeTerminalizationFailed
```

No failure path authorizes shell, `exec`, direct Python, `operator_unrestricted`, legacy unrestricted compatibility, caller workspace placement, provider substitution, or response-path leakage.

## Approved Implementation Slices — compiled after Plan Review R4

Current Execution Slice Set:

`docs/execution/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-r4-slices.yaml`

### S06 — Built-in `devforge_runtime` endpoint + lifecycle composition

Primary surfaces:

```text
src/sentinelx_core/handlers/local_api.py
src/sentinelx_core/local_api.py and/or a small built-in endpoint abstraction
src/sentinelx_core/handlers/mutation_scope.py
src/sentinelx_core/handlers/__init__.py
new focused devforge_runtime provider module if useful
focused local_api registry/list/describe/call tests
```

Outcomes:

- introduce built-in endpoint provider support without changing external endpoint behavior;
- `local_api` becomes context-aware for built-in calls;
- endpoint eligibility is bound to existing mutation policy opt-in;
- lifecycle actions reuse one canonical mutation-scope service;
- transitive `disabled_ops` admission is shared by `describe` and `call`;
- external endpoint name collision preserves the external endpoint and makes the builtin unavailable;
- built-in metadata proves provider kind/contract revision;
- configured external local APIs remain behavior compatible;
- Hosts with neither external endpoints nor eligible built-ins still omit `local_api`.

Required tests:

1. no mutation policy + no external endpoints -> `local_api` unregistered;
2. external endpoints only -> prior behavior unchanged;
3. eligible mutation policy -> builtin listed with `provider_kind=builtin`, `contract_revision=1`;
4. `disabled_ops=[local_api]` -> outer operation absent/unreachable;
5. `disabled_ops=[mutation_scope]` -> lifecycle actions absent from describe and direct calls rejected;
6. `disabled_ops=[script_run]` -> `execute_scoped` absent from describe and direct call rejected;
7. mixed disable cases remain deterministic and do not affect unrelated configured external endpoints;
8. configured external endpoint named `devforge_runtime` remains external and builtin is unavailable with stable collision diagnostic;
9. list/describe/call resolve the same provider under collision;
10. lifecycle provision/revalidate/inspect/terminalize preserve exact binding/error semantics;
11. caller authority fields are rejected;
12. terminal inspect remains non-reactivating.

### S07 — `execute_scoped` adapter + bounded projection + no-fallback regressions

Primary surfaces:

```text
built-in devforge_runtime provider/handler
src/sentinelx_core/handlers/scoped_script.py (reuse/refactor only if needed)
request-context plumbing
focused integration/security tests
```

Outcomes:

- adapter injects fixed `scoped_mutation` and `cleanup=true` and reuses the existing profiled handler;
- caller cleanup override is rejected;
- exact outer `RequestContext` is preserved;
- scope/repository/semantic revalidation remains before material mutation;
- AppContainer/audit/Job/terminalization remains unchanged;
- positive response projection prevents exact provider path/debug-field leakage;
- no duplicate process runner/sandbox/audit/store exists;
- failure never falls back to shell/exec/Python allowlist/operator-unrestricted/legacy compatibility.

Required tests:

1. valid provider scope -> harmless scoped execution succeeds;
2. mismatched repository/lineage/generation -> denied before material mutation;
3. caller `execution_profile` rejected;
4. caller `cleanup` or `cleanup=false` rejected;
5. caller workspace/operation-class authority rejected;
6. synthetic inner `workdir`/`script_path`/future path/debug fields are stripped by positive projection;
7. audit START precedes materialization/spawn;
8. success/failure/timeout terminalization remains authoritative;
9. `disabled_ops=[script_run]` prevents invocation even if direct built-in call is attempted;
10. current SX-HMSA destructive-escape incident regression remains green.

### S08 — Known-build activation + real `sentinel_local_api` end-to-end evidence

Controlled sequence:

```text
1. build/activate an exact PR-007 candidate on the connected Windows Host using the existing release/development activation contract;
2. read Agent version/capabilities and prove exact candidate is active;
3. call model-facing sentinel_local_api list and confirm eligible devforge_runtime is present;
4. describe endpoint and prove provider_kind=builtin + contract_revision=1 + policy-filtered actions;
5. provision provider scope for exact repository + task/run/attempt[/slice];
6. execute one harmless deterministic marker via devforge_runtime.execute_scoped;
7. verify model-facing response contains no exact provider workspace/script path;
8. inspect exact scope and prove terminal/non-active state;
9. attempt mismatched repository/lineage and require fail-closed result;
10. exercise one live policy-disabled action condition where safely available, or use exact known-build policy/readback evidence plus focused regression if changing live policy would be a separate authority boundary;
11. reconfirm direct `python --version` through ordinary exec remains `command_not_allowed` when not allowlisted;
12. run/read back affected security regression evidence.
```

S08 completion requires a real receipt from the existing Hub interface and exact Host/Agent readback. Repository tests alone cannot satisfy A7.

## Verification Matrix

| Case | Expected |
|---|---|
| no eligible endpoint on Host | local_api absent or bounded unavailable; no mutation authority |
| configured external local_api endpoint | unchanged existing behavior |
| external endpoint named devforge_runtime | remains external; builtin unavailable; no shadowing |
| eligible builtin devforge_runtime | describe proves builtin identity/revision and only admitted actions |
| disabled local_api | outer operation unadvertised/unreachable |
| disabled mutation_scope | lifecycle actions unadvertised and direct call denied |
| disabled script_run | execute_scoped unadvertised and direct call denied |
| provision scoped_script | provider-issued current scope |
| duplicate same Attempt | same current authority |
| caller workspace/operation class/profile/cleanup | rejected |
| valid execute_scoped | existing scoped executor succeeds with cleanup fixed true |
| inner debug/path fields | stripped from model-facing response |
| mismatched repository/lineage/generation | denied before material mutation |
| execution failure/timeout | terminalized; no unrestricted retry |
| terminal inspect | terminal evidence; no reactivation |
| direct Python exec not allowlisted | command_not_allowed |
| model-facing sentinel_local_api E2E | provision -> scoped execute -> terminal inspect PASS |
| Hub has no new mutation_scope projection | irrelevant to current acceptance |

## Regression Requirements

At minimum retain/execute affected checks for:

- mutation-scope uniqueness and durable authority;
- operation-class immutable digest participation;
- exact placement/repository/semantic binding;
- audit START/SPAWN/FINISH ordering;
- Windows AppContainer ACL/Job containment;
- scoped script execution;
- configured `local_api` behavior and compatibility checks;
- transitive `disabled_ops` behavior;
- built-in/external endpoint collision behavior;
- bounded model-facing response projection;
- capability/help truthfulness;
- `INCIDENT-20260927-D-ROOT-RECURSIVE-DELETE` protection;
- direct Python allowlist denial;
- no fixed host/path/version/credential identity.

## Requirement Traceability

| Requirement | Plan |
|---|---|
| R1-R5 | retained S01/S02 authority + D5/S06 shared lifecycle composition |
| R6-R7 | D11 + S06/S07 transitive admission and no-fallback tests |
| R8 | D6/D13 + S07 existing scoped executor composition and bounded result |
| R9-R10 | D2/D3/D7/D11/D12 + S06 built-in endpoint admission/identity |
| R11 | D1 + S08 immutable Hub proof |
| R12 | D6/D13 + S07 bounded positive response projection |
| R13 | D11/D12 + S06 mixed/configured endpoint/disable regressions |
| R14 | static review across S06/S07 |
| R15 | D9 + Acceptance dependency check |

## R3 Finding Closure Mapping

| R3 finding | Revision 4 remediation |
|---|---|
| F1 `disabled_ops` bypass | D11 defines transitive policy-derived action admission; S06/S07 test describe + direct call paths. |
| F2 cleanup/path leakage | D6/D13 fix cleanup internally to true, reject caller override, and apply a positive model-facing response allowlist. |
| F3 endpoint-name collision | D12 preserves configured external meaning, makes builtin unavailable on collision, and requires builtin identity/revision metadata. |

## Plan Review Questions

Reviewer verified:

1. D11 preserves existing `disabled_ops` as the single policy truth without a second deny list.
2. Direct built-in calls cannot bypass the same policy filtering used by describe/list.
3. D6/D13 use a positive result projection that remains safe if the inner scoped handler adds fields later.
4. Collision behavior preserves an operator-configured external `devforge_runtime` rather than shadowing or reinterpreting it.
5. `provider_kind=builtin + contract_revision=1` lets Acceptance prove provider identity unambiguously.
6. `execute_scoped` still composes the exact existing scoped execution path and RequestContext.
7. S08 proves the real model-facing boundary without requiring Hub modification.

## Current Disposition

```text
Requirement Revision 2: Ready
Plan Revision 4: Approved
Plan Approved: true
Execution Slice Set: docs/execution/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-r4-slices.yaml
Implementation Authorized: true
Current Gate: implementation
Next Actor: implementer
```

No implementation or acceptance claim is made by this Plan.
