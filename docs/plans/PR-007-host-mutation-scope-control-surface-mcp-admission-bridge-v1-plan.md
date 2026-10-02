# PR-007 — Host Mutation Scope Control Surface & MCP Admission Bridge V1 — Plan

## Plan State

```yaml
task_id: PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1
requirement_revision: 2
stage: plan_review_rejected
plan_status: rejected
implementation_authorized: false
plan_revision: 3
requirement: docs/requirements/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1.md
requirement_change_invalidation: docs/reviews/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-requirement-r2-invalidation.md
prior_plan_review: docs/reviews/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-plan-review-r2.md
current_plan_review: docs/reviews/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-plan-review-r3.md
execution_slice_set: null
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

Plan Revision 3 replaces only the invalidated Hub-projection portion of Revision 2. It preserves verified provider/security work from S01-S04 and does not replay those completed side effects.

## Current Verified Reality

Planning baseline is canonical `main@f7e878f3497582547e5d52cd33b060cae18d2e84` plus the existing PR-007 branch implementation.

Verified facts:

- PR-007 already contains the bounded `mutation_scope` lifecycle handler over `MutationScopeStore`.
- existing scope admission includes exact generation, repository, semantic lineage and provider-owned operation-class checks.
- existing scoped execution is implemented by `make_profiled_script_run_handler(...)` / `_run_scoped(...)`; it owns AppContainer, audit, materialization, spawn and terminalization semantics.
- `local_api` is already a first-class Agent operation implemented by `src/sentinelx_core/handlers/local_api.py` and `src/sentinelx_core/local_api.py`.
- current registry registers `local_api` only when `policy.local_apis` is non-empty.
- current `local_api` implementation treats configured endpoints as external HTTP/JSON-RPC targets; there is no built-in Agent endpoint provider today.
- the current ChatGPT model surface exposes `sentinel_local_api`; a live call reached the connected Agent and returned Agent-level `unsupported_op`, proving the Hub already transports this operation without any new Hub schema.
- the prior live failure for `mutation_scope` proved only that the Hub does not dynamically route arbitrary newly registered Agent operations.
- production Hub source/deployment is outside repository/user control and is not an implementation target for this Plan.

## Retained Verified Prerequisites

The following completed Revision-2 evidence remains applicable and MUST NOT be replayed:

```text
S01 — authority admission + exact bound readback
S02 — mutation_scope lifecycle handler + provider-owned purpose mapping
S03 — registry/capability/operator contract projection for mutation_scope
S04 — existing scoped execution composition + Windows security regressions
```

Their checkpoints remain historical evidence. Plan Revision 3 consumes their resulting implementation state but creates no new current Slice identity for them.

The old S05 generic-Hub `/op mutation_scope` objective is superseded and is not a current executable Slice.

## Authoritative Decisions

### D1 — Hub is immutable external infrastructure

No implementation Slice may require source/config/deployment changes to `mcp.sentinelx.app`.

The only Hub assumption used by PR-007 is the already observed, model-facing `sentinel_local_api` envelope. Acceptance must re-read this live surface; repository code cannot claim Hub availability by itself.

### D2 — Extend `local_api` with a built-in endpoint provider, not a fake socket profile

Add an Agent-owned built-in endpoint namespace alongside existing host-configured external endpoints.

Canonical built-in endpoint:

```text
devforge_runtime
```

The implementation SHOULD keep the existing external HTTP/JSON-RPC endpoint machinery generic. Do not encode `devforge_runtime` as a fabricated Unix socket/stdio `LocalApiEndpoint` and do not require operators to point YAML at the Agent itself.

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
- existing configured external `local_apis` retain their prior behavior and authority model.

The registry may expose `local_api` when either an eligible built-in endpoint exists or configured external endpoints exist. It must not expose `local_api` on a Host with neither.

### D4 — Make `local_api` context-aware without changing external endpoint semantics

The built-in execution path needs authoritative transport `RequestContext` for audit lineage. Therefore the `local_api` handler should become context-aware and receive the current request context from the executor.

For existing external endpoints:

- context is not forwarded to the external service unless an existing declared contract already does so;
- request templates, compatibility checks, projection and allowlists remain unchanged;
- no payload value may overwrite transport request ID, opaque ref, receive time or actual outer operation.

For built-in `devforge_runtime`, the same immutable outer `RequestContext` is passed to the canonical internal execution function.

### D5 — Reuse one canonical scope-lifecycle service seam

Do not duplicate the lifecycle parser/store logic already implemented in `handlers/mutation_scope.py`.

Refactor only as needed so both:

```text
Agent op=mutation_scope
and
local_api endpoint=devforge_runtime lifecycle actions
```

compose one canonical provider-owned lifecycle service/helper.

The direct `mutation_scope` handler may keep its transport-op assertion as an adapter-level guard, while the shared lifecycle service accepts validated action input and delegates to the same `MutationScopeStore` authority.

The shared service remains responsible for:

```text
purpose=scoped_script mapping
strict repository parser
strict lineage parser
strict scope_ref parser
provider-only operation-class mapping
bounded response projection
provision/revalidate/inspect/terminalize
```

No second scope ledger or independent lifecycle semantics are allowed.

### D6 — `execute_scoped` composes the existing profiled script handler

`devforge_runtime.execute_scoped` does not implement process execution.

It validates a bounded action payload, rejects authority/profile override fields, constructs the existing scoped-script payload with the internal constant:

```text
execution_profile = scoped_mutation
```

and calls the existing profiled script execution path with the exact current `RequestContext`.

Allowed caller execution inputs may include only the existing bounded scoped-script data needed to run code inside provider authority, such as:

```text
content
interpreter
args
cwd
env
timeout
cleanup
scope_ref
repository
lineage
```

Forbidden fields include caller-selected:

```text
execution_profile
workspace/workspace_root/workspace_id authority
authorized write roots/protected roots
operation classes
sandbox identity
operator_unrestricted
legacy compatibility selector
```

The existing scoped path remains the single owner of revalidation, audit START, evidence materialization, AppContainer activation, spawn, finish and terminalization.

### D7 — Built-in endpoint schema must be self-describing through existing `local_api describe`

`operation=list` must include `devforge_runtime` only when it is eligible on the exact Host.

`operation=describe endpoint=devforge_runtime` must provide bounded action metadata and machine-readable nested parameter schemas sufficient for callers to construct requests without guessing.

Required actions:

```text
provision_scope
revalidate_scope
inspect_scope
terminalize_scope
execute_scoped
```

The schema is Agent-owned and versionable inside the endpoint metadata. It does not require the Hub to add fields because `sentinel_local_api.params` is already a generic structured object.

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

PR-007 Revision 3 must not wait for:

```text
sentinel_script_run model-facing schema expansion
Hub dynamic projection
Hub source/deployment binding
```

PR-008 and PR-009 may continue independently. Drift in shared Agent code must still be reconciled if it actually changes the canonical local implementation seam, but their workflow state does not block PR-007 by itself.

### D10 — Live acceptance is through the actual model-visible `sentinel_local_api`

After implementation and known-build activation, acceptance must run the real sequence through the same model-facing tool available to ChatGPT:

```text
1. sentinel_local_api list
2. sentinel_local_api describe(devforge_runtime)
3. provision_scope
4. execute_scoped harmless deterministic marker
5. inspect_scope
6. verify terminal state + exact repository/lineage binding
7. negative mismatch checks
8. reconfirm direct Python exec remains denied when not allowlisted
```

No `/op mutation_scope` call is required for acceptance.

## Error / Security Semantics

Reuse existing stable provider classifications wherever applicable. New adapter-level classifications should be minimal and machine-readable, for example:

```text
endpoint_not_configured / endpoint_not_available
unknown_action
invalid_payload
HostMutationSandboxUnavailable
HostMutationScopeConflict
HostMutationScopeNotCurrent
HostMutationScopeBindingMismatch
HostMutationScopeOperationNotAllowed
HostMutationScopeTerminalizationFailed
```

No failure path authorizes shell, `exec`, direct Python, `operator_unrestricted`, legacy unrestricted compatibility, caller workspace placement, or provider substitution.

## Planned Implementation Slices — Compile only after Plan approval

No current Execution Slice Set exists while Plan Revision 3 is under review.

### S06 — Built-in `devforge_runtime` endpoint + lifecycle composition

Primary surfaces:

```text
src/sentinelx_core/handlers/local_api.py
src/sentinelx_core/local_api.py and/or a small built-in endpoint abstraction
src/sentinelx_core/handlers/mutation_scope.py
src/sentinelx_core/handlers/__init__.py
new focused devforge_runtime handler/provider module if useful
tests for local_api registry/list/describe/call + lifecycle mapping
```

Outcomes:

- introduce built-in endpoint provider support without changing external endpoint behavior;
- `local_api` becomes context-aware for built-in calls;
- endpoint eligibility is bound to existing mutation policy opt-in;
- list/describe exposes bounded `devforge_runtime` metadata/schema;
- lifecycle actions reuse one canonical existing mutation-scope service;
- configured external local APIs remain byte/behavior compatible;
- Hosts with neither external endpoints nor eligible built-ins still omit `local_api`.

Required tests include:

1. no mutation policy + no external local APIs -> `local_api` unregistered;
2. configured external local APIs only -> prior behavior unchanged;
3. eligible mutation policy -> `local_api` registered and `devforge_runtime` listed;
4. describe returns only bounded actions/params;
5. provision/revalidate/inspect/terminalize preserve existing exact binding/error semantics;
6. caller authority fields are rejected;
7. terminal inspect remains non-reactivating.

### S07 — `execute_scoped` adapter + no-fallback regressions

Primary surfaces:

```text
built-in devforge_runtime provider/handler
src/sentinelx_core/handlers/scoped_script.py (reuse/refactor only if needed)
request-context plumbing
focused integration/security tests
```

Outcomes:

- `execute_scoped` injects fixed internal `scoped_mutation` profile and reuses the existing profiled script handler/path;
- exact outer `RequestContext` is preserved;
- scope/repository/semantic revalidation still occurs before material mutation;
- AppContainer/audit/Job/terminalization path remains unchanged;
- no duplicate process runner/sandbox/audit/store exists;
- forbidden profile/workspace/operation-class authority is rejected;
- failure never falls back to shell/exec/Python allowlist/operator-unrestricted/legacy compatibility.

Required focused tests include:

1. valid provider scope -> deterministic harmless scoped execution succeeds;
2. mismatched repository/lineage/generation -> denied before material mutation;
3. caller-supplied execution_profile -> rejected;
4. caller workspace/operation-class authority -> rejected;
5. audit START precedes materialization/spawn;
6. success/failure/timeout terminalization remains authoritative;
7. current SX-HMSA destructive-escape incident regression remains green.

### S08 — Known-build activation + real `sentinel_local_api` end-to-end evidence

Controlled sequence:

```text
1. build/activate an exact PR-007 candidate on the connected Windows Host using the existing release/development activation contract;
2. read Agent version/capabilities and prove exact candidate is active;
3. call model-facing sentinel_local_api list and confirm devforge_runtime is present;
4. describe endpoint and persist bounded schema evidence;
5. provision provider scope for exact repository + task/run/attempt[/slice];
6. execute one harmless deterministic marker via devforge_runtime.execute_scoped;
7. inspect exact scope and prove terminal/non-active state;
8. attempt mismatched repository/lineage and require fail-closed result;
9. reconfirm direct `python --version` through ordinary exec remains `command_not_allowed` when not allowlisted;
10. run/read back affected security regression evidence.
```

S08 completion requires a real receipt from the existing Hub interface and exact Host/Agent readback. Repository tests alone cannot satisfy A7.

## Verification Matrix

| Case | Expected |
|---|---|
| no eligible endpoint on Host | local_api absent or bounded unavailable; no mutation authority |
| configured external local_api endpoint | unchanged existing behavior |
| eligible devforge_runtime | list/describe exposes only bounded actions |
| provision scoped_script | provider-issued current scope |
| duplicate same Attempt | same current authority |
| caller workspace/operation class/profile | rejected |
| valid execute_scoped | existing scoped executor succeeds |
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
- `local_api` configured endpoint behavior and compatibility checks;
- Agent registry `disabled_ops` behavior;
- capability/help truthfulness;
- `INCIDENT-20260927-D-ROOT-RECURSIVE-DELETE` protection;
- direct Python allowlist denial;
- no fixed host/path/version/credential identity.

## Requirement Traceability

| Requirement | Plan |
|---|---|
| R1-R5 | retained S01/S02 authority + S06 shared lifecycle composition |
| R6-R7 | S06/S07 fail-closed admission and no-fallback tests |
| R8 | S07 existing scoped executor composition |
| R9-R10 | S06 built-in endpoint provider + policy-bound registration |
| R11 | D1 + S08 immutable Hub proof |
| R12 | S06/S07 bounded response projection |
| R13 | S06 mixed/configured endpoint regressions |
| R14 | static review across S06/S07 |
| R15 | D9 + Acceptance dependency check |

## Plan Review Questions

Reviewer must specifically challenge:

1. Does adding a built-in endpoint under `local_api` violate the existing host-declared endpoint security promise, or does binding it to explicit `mutation_execution` opt-in preserve operator authority?
2. Is the lifecycle logic genuinely shared with current `mutation_scope`, rather than duplicated?
3. Does `execute_scoped` truly compose the existing scoped execution path with the same `RequestContext`, or accidentally become a second executor?
4. Are external configured local APIs behaviorally unchanged?
5. Can `sentinel_local_api.params` carry all nested fields needed without requiring any Hub schema change?
6. Does the live acceptance path prove the actual model-facing boundary rather than only Agent-local unit behavior?

## Plan Review R3 Result

Plan Review R3 rejected Revision 3 with plan-local remediation only. Canonical findings are in:

`docs/reviews/PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1-plan-review-r3.md`

Required corrections are limited to:

1. preserve `disabled_ops` transitively across built-in lifecycle and execute actions;
2. bound `execute_scoped` cleanup/response so exact provider workspace/script paths are not exposed;
3. define deterministic built-in/external endpoint collision handling and built-in identity metadata.

## Current Disposition

```text
Requirement Revision 2: Ready
Plan Revision 3: Rejected
Plan Approved: false
Execution Slice Set: not compiled
Implementation Authorized: false
Current Gate: plan_review_rejected
Next Actor: planner
```

No implementation or acceptance claim is made by this Plan.
