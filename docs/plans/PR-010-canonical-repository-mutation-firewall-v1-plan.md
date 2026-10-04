# PR-010 — SentinelX Provider Canonical Repository Mutation Firewall V1 — Plan Revision 4

## Plan State

```yaml
task_id: PR-010-canonical-repository-mutation-firewall-v1
stage: done
plan_status: approved
plan_revision: 4
requirement_revision: 2
requirement: docs/requirements/PR-010-canonical-repository-mutation-firewall-v1.md
requirement_change_impact: docs/reviews/PR-010-canonical-repository-mutation-firewall-v1-requirement-r2-invalidation.md
prior_plan_review: docs/reviews/PR-010-canonical-repository-mutation-firewall-v1-plan-review-r3.md
plan_review: docs/reviews/PR-010-canonical-repository-mutation-firewall-v1-plan-review-r4.md
approval_checkpoint: docs/checkpoints/PR-010-canonical-repository-mutation-firewall-v1-plan-review-r4-approved-20261002.yaml
transport: github-pr
pr_number: 10
task_branch: task/canonical-repository-mutation-firewall-v1
base_branch: main
planning_baseline_main: f7e878f3497582547e5d52cd33b060cae18d2e84
implementation_authorized: true
execution_slice_set: docs/execution/PR-010-canonical-repository-mutation-firewall-v1-slices.yaml
acceptance_approved: true
completion_verified: true
finalization_status: integrated
finalization_ref: docs/reviews/PR-010-canonical-repository-mutation-firewall-v1-completion-finalization-r1.yaml
integration_receipt: docs/reviews/PR-010-canonical-repository-mutation-firewall-v1-integration-receipt-r1.yaml
completion_review: docs/reviews/PR-010-canonical-repository-mutation-firewall-v1-completion-r1.md
reconciliation_receipt: docs/reviews/PR-010-canonical-repository-mutation-firewall-v1-completion-reconciliation-r1.yaml
```

Plan Revision 4 repairs only the two plan-local findings from Plan Review R3. Requirement Revision 2, the Core-only security boundary, the immutable third-party Hub boundary, and the retained S01 implementation remain unchanged.

## R3 Remediation Summary

### F1 — Mixed `local_api` endpoint/action effects

Resolved in planning by generalizing authoritative operation-effect coverage from a flat op classification into an operation + bounded suboperation model.

For operations whose repository effect depends on a selector beneath the top-level op, coverage must be derived from the same Core-owned semantic source that admits the selector:

```text
git -> operation selector
local_api -> endpoint + action
future mixed op -> explicit bounded selector owned by Core
```

The invariant is fail-closed:

```text
effective model-facing operation
+ effective selected suboperation
+ missing/unknown repository effect
=> canonical_repository_mutation_firewall_v1 readiness = false
```

`local_api` is therefore never globally assumed read-only or non-repository merely because it uses a structured transport. Configured external endpoint/actions default to unknown for firewall readiness unless an explicit Core-understood effect declaration is present and valid. Built-in endpoint/actions use provider-owned metadata. PR-007 `devforge_runtime.execute_scoped` may compose existing scoped execution/sandbox/audit coverage; its lifecycle readback actions can be classified separately from its execution action.

### F2 — Existing `RepositoryIdentity` consumer compatibility

Resolved in planning by making shared-consumer regression evidence a hard S01 completion requirement. If S01 changes `RepositoryIdentity.canonical` or extracts a shared primitive, verification must cover the existing mutation-placement, mutation-scope/binding, scoped-script and relevant Windows sandbox consumers before S01 can complete.

A semantic incompatibility is a Decision Boundary: either preserve compatibility or persist an explicit migration/compatibility decision before proceeding. S01 cannot silently change existing scope/repository digests or binding semantics.

## Current Verified Reality

### Canonical repository and dependencies

- canonical `main`: `f7e878f3497582547e5d52cd33b060cae18d2e84` at review time;
- PR-010 transport remains PR #10;
- observed PR-007 head at Plan R4 review: `221c7b870e9305847a94b7d947a870dbe6aa28ab`, implementation;
- observed PR-008 head: `f7594c468d764ad85c0dc508ad47f009c89793c1`, Acceptance blocked;
- dependency SHAs are observations only and must be re-read at every overlapping Slice entry.

### Immutable external Hub boundary

`mcp.sentinelx.app` is a third-party closed-source transport boundary. PR-010 does not require or claim Hub source, schema, deployment, dynamic tool, `execution_profile`, capability rendering, or production Hub readback changes.

Required evidence is Core-owned:

```text
SentinelX Core unit evidence
+ Core integration evidence
+ Core protocol/hello/capability readback where applicable
+ Windows physical mutation regression evidence where required
```

### Retained S01 implementation

Retain without replay:

```text
src/sentinelx_core/policy.py
src/sentinelx_core/canonical_repository_firewall.py
tests/test_canonical_repository_firewall.py
```

Historical implementation head: `62b9fba588fac58161c909e8622278d791c07a92`.

The active S01 issue remains the parallel repository identity semantic between:

```text
sentinelx_core.mutation_placement.RepositoryIdentity
sentinelx_core.policy._canonical_repository_identity
```

The historical Hub `execution_profile_required` failure is non-blocking for PR-010.

### Current Core exposure facts relevant to F1

`handlers.build_registry()` is the dispatch and `ops_supported` source of truth. `local_api` is a conditional model-facing operation when eligible. Existing configured local APIs can invoke Host-local HTTP/JSON-RPC actions and may include a `run_as` relay path; PR-007 plans a built-in `devforge_runtime` endpoint under the same operation. Therefore `local_api` must participate in provider-wide repository-effect accounting at endpoint/action granularity.

## Design Decisions

### D0 — Core-only security and verification authority

The firewall is enforced beneath transport semantics inside SentinelX Core. Hub behavior is diagnostic only.

### D1 — One repository identity semantic with compatibility preservation

Canonical inventory consumes one provider repository identity semantic: either the existing `RepositoryIdentity` directly or a provider-neutral primitive extracted and used by all existing consumers.

Required semantic properties:

- stable `vcs + authority + path` canonicalization;
- credentials excluded;
- authority host/port behavior explicit and tested;
- deterministic `.git` normalization;
- traversal/invalid repository paths fail closed;
- no circular-import architecture that leaves duplicate logic behind.

Compatibility requirement:

- existing mutation-placement repository binding remains valid;
- mutation-scope repository/semantic binding and digests remain compatible unless explicitly migrated;
- scoped-script and Windows sandbox consumers retain expected repository identity behavior;
- any intentional digest/schema change requires explicit compatibility evidence and cannot be smuggled in as a firewall-only refactor.

### D2 — Canonical inventory is distinct Host authority

Canonical repositories remain distinct from generic `protected_roots`, `file_ops rw`, caller paths, cwd, environment values, branch names and model assertions. An execution workspace belonging to the same repository identity is not inferred canonical.

### D3 — One reusable provider firewall seam

`canonical_repository_firewall.py` remains the shared classifier/readiness seam. Handlers do not create per-operation canonical-role logic.

Required dispositions remain equivalent to:

```text
AllowedNonCanonicalTarget
CanonicalRepositoryMutationBlocked
HostCanonicalMutationFirewallIndeterminate
```

### D4 — Structured mutators admit exact targets before material side effects

For explicit path mutation:

```text
existing validation / canonical resolution
-> canonical firewall admission
-> existing operation-specific authority
-> first material side effect
```

Blocking occurs before backup, staging finalization, patch application, overwrite, delete, chmod/chown or equivalent mutation.

### D5 — Process surfaces are Core fail-closed

An effective arbitrary process mutation path with no physical canonical exclusion cannot coexist with advertised provider-wide firewall readiness. Core must block it, route it through already-proven physical scoped containment, or keep readiness false. Shell/script/path text parsing is not physical proof. No `operator_unrestricted`, legacy unrestricted fallback, command allowlist expansion or caller-minted authority is allowed.

### D6 — Authoritative operation-effect registration

The authoritative dispatch/effective-exposure model carries or derives metadata equivalent to:

```text
handler
exposure: model_facing | internal_only
repository_effect:
  read_only
  structured_mutation
  process_mutation
  non_repository_mutation
  mixed
  unknown
firewall_coverage:
  required | not_applicable
suboperation_classifier: optional Core-owned bounded classifier
```

Rules:

1. dispatchability and `ops_supported` remain derived from the same authoritative registration path;
2. unknown/missing repository effect on an effective model-facing op makes readiness false;
3. required-but-unproven coverage makes readiness false;
4. internal-only operations are explicit;
5. disabled operations are removed before effective-surface readiness computation;
6. `mixed` requires a fail-closed Core-owned suboperation classifier; absence/unknown selector effect makes readiness false.

No second hand-maintained firewall operation list is allowed.

### D6A — Generic mixed-operation subeffect model

Mixed operations must expose bounded, Core-owned suboperation effect semantics rather than rely on transport shape or caller assertion.

#### Structured Git

The Git operation selector is classified so read-only selectors remain usable and mutation selectors require firewall coverage.

#### `local_api`

The effective identity is:

```text
local_api / endpoint / action
```

Coverage rules:

- `list` and `describe` are read-only Core operations;
- `call` requires endpoint/action effect resolution;
- built-in endpoint/action effects come from provider-owned code/metadata;
- configured external endpoint/action effects are `unknown` by default;
- an operator may not make firewall readiness true merely by naming an action “read” or by generic configuration presence;
- if configuration later supports an explicit effect declaration, the declaration must be schema-bounded, validated by Core, default unknown on absence/invalid value, and cannot claim physical process containment it does not provide;
- external action classified read-only/non-repository may remain available without firewall enforcement only if its effect contract is explicit and valid;
- external structured/process mutation action must either have provable firewall coverage or make readiness false;
- `run_as`/relay process behavior is part of effect/coverage accounting, not ignored because the top-level op is structured;
- built-in `devforge_runtime.execute_scoped` may satisfy process mutation coverage by composing the existing scoped mutation/sandbox/audit path; lifecycle list/describe/inspect/readback actions are separately classifiable;
- an unknown configured or built-in action makes provider-wide readiness false while that action is effectively exposed.

PR-007 remains an exact-readback overlap dependency before PR-010 changes `local_api`, built-in endpoint metadata, registry or scoped-execution semantics.

### D7 — Exact overlap reconciliation

Before each Slice mutates an overlapping seam, re-read exact latest PR-007/PR-008 heads, changed files, relevant artifacts and stage/disposition. Known overlap includes registry, `local_api`, scoped-script, mutation-scope, executor, basic/client capability and protocol seams. Material semantic conflict stops before mutation and requires a no-loss composition decision.

PR-009 is independent/non-blocking unless exact future changed-file evidence shows a direct code conflict.

### D8 — Core capability readiness and existing transport output

Positive readiness requires:

```text
valid Host canonical inventory
+ one compatible repository identity semantic
+ complete effective op/suboperation classification
+ structured mutation coverage
+ process physical disposition
+ no unrestricted bypass
=> Core readiness true
=> existing Core hello/capability/protocol output contains canonical_repository_mutation_firewall_v1
```

Unknown `local_api` endpoint/action effect is therefore a negative readiness input just like an unknown top-level op or Git selector.

## Verification Strategy

### Required Core-owned evidence

1. focused unit tests for modified primitive/module;
2. shared `RepositoryIdentity` consumer compatibility tests in S01;
3. registry + mixed selector/endpoint integration tests;
4. handler integration tests;
5. Core protocol/hello/capability construction/readback tests;
6. affected security/regression suite;
7. exact-head CI when available;
8. Windows physical process/incident evidence required by the contract.

External Hub projection/rendering is never a required PR-010 receipt.

## Implementation Slices After Plan Approval

### S01 — Retained inventory repair + identity consumer revalidation

**State:** implementation retained; incomplete; no replay.

**Scope:**

- preserve retained canonical inventory/firewall code;
- replace the parallel policy normalizer with the existing/shared repository identity primitive;
- freeze credential, authority/port, `.git`, traversal, invalid identity and same-repository-workspace behavior;
- run focused firewall/inventory tests;
- run focused compatibility regressions for existing `RepositoryIdentity` consumers: mutation placement, mutation scope/binding, scoped-script repository binding and relevant Windows sandbox identity usage;
- detect stored digest/binding incompatibility explicitly rather than silently accepting drift.

**Decision boundary:** if the shared semantic repair changes existing valid scope/repository identity or persisted digest expectations, stop and persist a compatibility/migration decision before S01 completion.

**Stop condition:** one shared repository identity semantic is proven, focused firewall tests pass, existing consumer compatibility evidence passes, and no handler-wide mutation coverage is claimed yet.

### S02 — Authoritative op/suboperation effect registry + structured mutation integration

**Entry:** exact PR-007/PR-008 overlap reconciliation before registry, `local_api` or other overlapping mutation.

**Scope:**

- extend authoritative registration with fail-closed repository-effect/coverage semantics;
- support `mixed` operations with Core-owned suboperation classifiers;
- classify Git selectors;
- classify `local_api` list/describe and endpoint/action call effects;
- for configured external local APIs, make missing/invalid endpoint/action effect metadata resolve to unknown/readiness false;
- compose any current PR-007 built-in endpoint metadata without duplicating its authority;
- integrate central firewall into edit/edit-upload, fsmutate, move/copy/delete/chmod/chown, structured Git apply_patch, upload/finalization and equivalent effective structured mutators.

**Required verification:**

- unknown top-level op -> readiness false;
- unknown mixed selector -> readiness false;
- `local_api` configured action without effect contract -> readiness false;
- explicit read-only/non-repository action -> does not falsely require repository mutation enforcement;
- structured/process-mutation local action without proven coverage -> readiness false;
- disabled operation removal precedes readiness accounting;
- canonical explicit-path writes block before side effects;
- no `.bak` on blocked edit/delete;
- Git read selectors remain available.

**Stop condition:** authoritative op/suboperation accounting fails closed and structured mutator regressions pass without a parallel firewall list.

### S03 — Core process mutation fail-closed boundary

**Entry:** exact PR-007/PR-008 reconciliation before scoped-script, `local_api`, mutation-scope, executor or equivalent process seams.

**Scope:**

- identify every effective process-producing op/suboperation from authoritative metadata;
- enforce disposition independent of Hub parameter availability;
- compose existing scoped/sandbox/audit authority rather than duplicate it;
- account for `local_api` built-in scoped execution and any configured action whose implementation/relay is process-producing;
- block or make readiness unavailable for unconstrained process paths;
- freeze direct/redirection/Python/PowerShell/spawned-child/background regressions.

**Stop condition:** no effective generic, mixed-operation or child-process canonical mutation bypass can coexist with readiness true.

### S04 — Core Capability Readiness + Existing Transport Projection

**Entry:** exact overlap reconciliation if registry/local_api/capability/hello/protocol seams moved.

**Scope:**

- compose readiness from inventory + effective operation registry + structured coverage + process disposition;
- expose capability through existing SentinelX Core hello/capability/protocol structures;
- add bounded reason codes/diagnostics;
- preserve PR-007/PR-008 semantics;
- do not modify, require changes to, deploy, or validate production Hub rendering.

**Verification:**

- one unknown exposed op => Core capability unavailable;
- one uncovered mutator => unavailable;
- policy disabled => unavailable while legacy behavior remains;
- valid Windows complete-coverage fixture => Core capability present;
- Core protocol/hello readback confirms the field;
- missing Hub projection, if separately observed, is diagnostic only.

**Stop condition:** partial Core coverage cannot mechanically advertise the capability, and complete Core coverage is visible in existing Core-owned protocol output.

### S05 — Incident regression, affected security suite and documentation

**Scope:**

Freeze the real incident family and document the final operator/security boundary.

Required regression matrix:

1. broad parent `rw` + canonical edit -> blocked;
2. canonical delete/edit -> blocked before backup;
3. canonical structured Git patch -> blocked;
4. generic process switch/write -> blocked under firewall-ready mode;
5. indirect/background child canonical write -> blocked;
6. unknown inventory/target -> fail closed;
7. canonical read/list/search/status/diff -> allowed;
8. same-repository non-canonical execution workspace -> passes firewall then existing authorities decide;
9. fake `canonical_sync` claim -> no bypass;
10. unknown/unclassified operation -> readiness unavailable;
11. internal-only transport op -> not silently counted as model-facing evidence;
12. Hub projection omission -> documented external limitation only, no PR-010 failure.

Documentation covers inventory configuration, identity semantics, readiness/error behavior, platform support, `file_ops` vs `protected_roots` vs canonical firewall vs scoped sandbox, authoritative operation registration, process compatibility, and immutable Hub boundary.

**Stop condition:** Core/local implementation has durable required evidence and is ready for `#开发验收`; no merge, release, production Host activation, or Hub activation is implied.

## Implementation-Ready Admission Gate

Plan Review confirms:

### P0-A — Requirement R2 lineage
Review is against Requirement Revision 2 / Plan Revision 4; prior approvals are history only.

### P0-B — Repository identity reuse + compatibility
S01 has one semantic source and explicit existing-consumer compatibility verification/Decision Boundary.

### P0-C — Process fail-closed semantics
Arbitrary process mutation cannot coexist with readiness without physical exclusion; Hub arguments are irrelevant.

### P0-D — Authoritative fail-closed coverage
Dispatch/effective exposure and firewall accounting share one source; unknown top-level operations fail readiness.

### P0-E — Mixed-operation coverage
Git selectors and `local_api` endpoint/actions are classified through bounded Core-owned suboperation semantics; unknown nested effects fail readiness.

### P0-F — Immutable Hub boundary
No Slice requires Hub source/schema/deployment/tool/capability rendering or production Hub readback.

### P0-G — Exact dependency readback
PR-007/PR-008 are re-read before overlapping mutation; PR-009 remains non-blocking absent direct code conflict.

## Post-Review Transition

Plan Revision 4 is approved. The Revision 4 Slice Set is implementation authority and execution resumes at **S01 retained inventory repair + identity consumer revalidation**.

```yaml
implementation_authorized: true
current_gate: implementation
next_slice: S01
```
