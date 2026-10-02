# PR-010 — SentinelX Provider Canonical Repository Mutation Firewall V1 — Plan Revision 3

## Plan State

```yaml
task_id: PR-010-canonical-repository-mutation-firewall-v1
stage: plan_review
plan_status: ready_for_review
plan_revision: 3
requirement_revision: 2
requirement: docs/requirements/PR-010-canonical-repository-mutation-firewall-v1.md
requirement_change_impact: docs/reviews/PR-010-canonical-repository-mutation-firewall-v1-requirement-r2-invalidation.md
historical_plan_review:
  - docs/reviews/PR-010-canonical-repository-mutation-firewall-v1-plan-review-r1.md
  - docs/reviews/PR-010-canonical-repository-mutation-firewall-v1-plan-review-r2.md
historical_approval_checkpoint: docs/checkpoints/PR-010-canonical-repository-mutation-firewall-v1-plan-review-r2-approved-20261002.yaml
transport: github-pr
pr_number: 10
task_branch: task/canonical-repository-mutation-firewall-v1
base_branch: main
planning_baseline_main: f7e878f3497582547e5d52cd33b060cae18d2e84
implementation_authorized: false
execution_slice_set: docs/execution/PR-010-canonical-repository-mutation-firewall-v1-slices.yaml
acceptance_approved: false
completion_verified: false
```

Plan Revision 3 is required because Requirement Revision 2 materially changes the verification and Acceptance authority. Plan Revision 2 and its approval remain historical evidence but are not current implementation authority.

## Current Verified Reality

### Canonical repository and transport

- project: `sentinelx-cloud-core`;
- canonical remote `main`: `f7e878f3497582547e5d52cd33b060cae18d2e84` at replanning time;
- Task transport remains PR #10 on `task/canonical-repository-mutation-firewall-v1`;
- canonical `main` is not an implementation mutation target.

### Immutable external Hub boundary

`mcp.sentinelx.app` is a third-party closed-source transport boundary and is not modifiable by this project.

PR-010 therefore cannot require:

```text
Hub source changes
Hub MCP schema changes
Hub dynamic tool support
Hub execution_profile projection
Hub capability-field rendering
Hub deployment/activation
```

Those may be recorded as external integration limitations only. Core-owned security and verification must remain complete without them.

### Retained S01 implementation

Already-landed S01 code is preserved:

```text
src/sentinelx_core/policy.py
src/sentinelx_core/canonical_repository_firewall.py
tests/test_canonical_repository_firewall.py
```

Historical implementation head: `62b9fba588fac58161c909e8622278d791c07a92`.

The previous dynamic attempt was blocked by a model-facing tool lacking `execution_profile`; Requirement Revision 2 supersedes that as a PR-010 blocker.

The current Core-owned S01 blocker remains:

```text
sentinelx_core.mutation_placement.RepositoryIdentity
vs
sentinelx_core.policy._canonical_repository_identity
```

The second normalizer creates parallel semantics and strips explicit authority ports, so S01 must compose one shared provider identity primitive before it can complete.

### Existing security primitives to compose

1. `Policy.resolve_path(..., need_write=True)` canonicalizes paths and enforces `file_ops rw` for structured mutation.
2. `MutationExecutionPolicy` owns `workspace_root`, `protected_roots`, `runtime_read_roots`, scoped-mutation enablement and related readiness inputs.
3. `sentinelx_core.mutation_placement.RepositoryIdentity` already defines provider repository identity semantics.
4. edit/destructive filesystem handlers centralize path resolution before mutation.
5. structured Git `apply_patch` uses the structured write substrate.
6. scoped mutation / audit / sandbox paths remain provider-owned Core authority.
7. `handlers.build_registry()` is the runtime source of dispatchable operations; effective operation exposure must remain derived from that authoritative registration path.
8. SentinelX Core already owns hello/capability/protocol construction even when the third-party Hub later chooses what to render.

## Design Decisions

### D0 — Core-only security and verification authority

The canonical firewall is an Agent/Core boundary, not an MCP/Hub boundary.

Required shape:

```text
existing transport input
        ↓
SentinelX Agent operation dispatch
        ↓
Core operation-effect classification
        ↓
canonical repository firewall / process disposition
        ↓
existing operation-specific authority
        ↓
material side effect
```

Verification is performed through Core unit/integration/protocol evidence and required physical Windows regression evidence. Hub projection is never required to prove the security property.

### D1 — One repository identity semantic

Refactor S01 so canonical repository inventory consumes the existing `RepositoryIdentity` primitive directly or through one extracted shared normalizer used by both mutation placement and canonical inventory.

Constraints:

- no circular import from `policy.py` to `mutation_placement.py` may be introduced if it creates a dependency cycle;
- a small provider-neutral shared module is acceptable if both call sites use it;
- authority host/port semantics must be explicit and tested rather than silently truncated;
- credentials remain excluded;
- `.git` suffix/path normalization remains deterministic;
- traversal/invalid repository paths fail closed.

This repair is the first implementation work after Plan Review approval.

### D2 — Separate canonical inventory from generic protected roots

Keep canonical repository inventory as Host/operator authority under mutation policy rather than overloading `protected_roots`.

Portable shape remains equivalent to:

```yaml
mutation_execution:
  canonical_repository_firewall_enabled: true
  canonical_repositories:
    - root: <absolute host path>
      repository:
        vcs: git
        authority: github.com
        path: owner/repository
      canonical_branch: main
```

Invalid/ambiguous entries make readiness false. Execution workspaces remain separate roots and are not inferred canonical merely from matching repository identity.

### D3 — One reusable firewall module

`src/sentinelx_core/canonical_repository_firewall.py` remains the central provider-owned seam for:

- canonical inventory readiness;
- normalized path intersection classification;
- write-target admission;
- process-class disposition inputs;
- bounded diagnostics;
- capability readiness components.

Handlers do not invent per-operation canonical-role logic.

### D4 — Structured mutators get exact target admission

For explicit target paths:

```text
existing validation / canonical path resolution
→ canonical firewall admission
→ existing file_ops/scope/operation authorization
→ first material side effect
```

The block must precede backup creation, staging finalization, patch application, overwrite/delete, chmod/chown, or equivalent side effect.

### D5 — Generic process surfaces are Core fail-closed

PR-010 does not require the Hub to send `execution_profile` or expose a new tool.

Core operation registration and handler state determine whether a process-producing operation has a proven physical disposition.

When firewall-ready mode is enabled:

- constrained/scoped execution may continue only through existing verified scope/sandbox/audit authority;
- arbitrary unprofiled execution with no physical canonical exclusion is blocked, or makes readiness false;
- legacy compatibility may remain only while firewall capability is unavailable;
- shell/script/path string parsing is not accepted as physical proof;
- background descendants, timeout and nonzero paths remain inside the disposition;
- `operator_unrestricted` and allowlist expansion are forbidden fallbacks.

### D6 — Authoritative operation-effect registration is fail-closed

Extend or wrap the existing authoritative operation registration with metadata equivalent to:

```text
handler
exposure: model_facing | internal_only
repository_effect:
  read_only
  structured_mutation
  process_mutation
  non_repository_mutation
  unknown
firewall_coverage:
  required | not_applicable
```

Invariants:

1. dispatchability and `ops_supported` remain derived from the same authoritative registry;
2. missing/unknown effect on an effective model-facing operation makes firewall readiness false;
3. required-but-unproven coverage makes readiness false;
4. internal-only operations are explicit;
5. disabled operations are removed before final readiness computation;
6. mixed Git selectors are explicitly classified.

### D7 — PR-007/PR-008 overlap is exact-readback driven

Before any Slice mutates an overlapping Core seam, re-read exact current PR-007/PR-008 heads, changed-file sets, relevant contracts/artifacts, and current stage/disposition.

Known overlap family includes:

```text
src/sentinelx_core/client.py
src/sentinelx_core/handlers/__init__.py
src/sentinelx_core/handlers/basic.py
src/sentinelx_core/handlers/scoped_script.py
src/sentinelx_core/mutation_scope.py
src/sentinelx_core/executor.py
capability / hello / protocol-feature code
```

Material semantic conflict is a Decision Boundary before product mutation.

PR-009 is not a semantic blocking dependency. It is consulted only if an exact future changed-file readback demonstrates a direct code overlap requiring conflict reconciliation.

### D8 — Core Capability Readiness + Existing Transport Projection

S04 computes and verifies capability readiness entirely within SentinelX Core.

Required positive path:

```text
valid canonical inventory
+ complete effective operation-effect classification
+ structured mutator coverage
+ process physical disposition
+ no unrestricted bypass
→ Core readiness true
→ existing Core hello/capability/protocol structure contains canonical_repository_mutation_firewall_v1
```

Required negative paths remove/unavailable the capability.

Existing transport may relay that structure. Hub-native dynamic schema/tool generation or UI/model rendering is outside PR-010 and cannot block S04 or Acceptance.

## Verification Strategy

### Core-owned required verification

Use, in order of scope:

1. focused unit tests for the modified primitive/module;
2. focused handler/registry integration tests;
3. Core protocol/hello/capability construction/readback tests;
4. affected repository security/regression suite;
5. exact-head CI when available;
6. Windows physical process/incident evidence required by the contract.

A Core-owned verification channel that is genuinely unavailable may block a Slice if no equivalent required evidence can be produced.

### External non-blocking diagnostics

Do not gate PR-010 on:

- Hub `execution_profile` projection;
- Hub dynamic tool schema;
- Hub capability rendering;
- production Hub deployment/readback.

Record these separately if observed.

## Implementation Slices After Plan Approval

### S01 — Retained inventory implementation repair + Core revalidation

**State entering Plan Review:** implementation retained, incomplete, revalidation required.

**Scope after approval:**

- preserve existing canonical inventory/firewall implementation;
- eliminate the parallel repository identity normalizer by composing the existing `RepositoryIdentity` semantic through a safe shared seam;
- test authority/port, credential stripping, `.git`, traversal, invalid identity and same-repository-workspace cases;
- rerun focused S01 unit tests through a Core-owned verification channel;
- retain prior static evidence only as history, not as final completion proof.

**Stop condition:** one repository identity semantic is proven and focused Core-owned S01 verification passes. No handler mutation coverage is claimed yet.

### S02 — Authoritative operation-effect registry + structured mutation integration

**Entry:** exact PR-007/PR-008 overlap reconciliation before touching registry/overlap surfaces.

**Scope:**

- add fail-closed operation-effect metadata to the authoritative dispatch registration;
- integrate central admission into edit/edit-upload, fsmutate, move/copy/delete/chmod/chown, structured Git `apply_patch`, upload/finalization, and every equivalent currently effective structured mutator discovered from the registry;
- classify internal-only and read-only operations explicitly.

**Stop condition:** unknown/uncovered effective mutators make readiness false; all structured canonical writes block before any side effect; non-canonical paths retain existing behavior.

### S03 — Core process mutation fail-closed boundary

**Entry:** exact PR-007/PR-008 reconciliation before touching scoped-script/basic/client/mutation-scope/executor or equivalent process seams.

**Scope:**

- identify every effective process-producing operation from authoritative registration;
- enforce Core-owned process disposition independent of Hub parameter availability;
- preserve scoped/sandbox/audit authority without duplicating it;
- block or mark readiness unavailable for unconstrained process paths;
- freeze direct, redirection, Python/PowerShell, spawned-child/background mutation regressions.

**Stop condition:** no effective generic/child-process canonical mutation bypass exists while provider-wide readiness can be true.

### S04 — Core Capability Readiness + Existing Transport Projection

**Entry:** exact overlap reconciliation if capability/hello/protocol seams overlap moving PR-007/PR-008 state.

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

Plan Review must confirm:

### P0-A — Requirement Revision 2 lineage

Review is explicitly against Requirement Revision 2 and this Plan Revision 3; Plan R2 approval is not reused.

### P0-B — Repository identity reuse

S01 repair uses one provider repository identity semantic without introducing a circular dependency or second identity model.

### P0-C — Core process semantics

A host cannot advertise provider-wide firewall protection while retaining an effective arbitrary process mutation path with no physical canonical exclusion. Hub parameter availability is irrelevant to this invariant.

### P0-D — Coverage registration fail-closed

The authoritative dispatch/effective-exposure path is also the coverage accounting source; future unknown mutators remove readiness automatically.

### P0-E — Immutable Hub boundary

No Slice requires Hub source/schema/deployment/tool/capability rendering mutation or production Hub readback.

### P0-F — Exact dependency readback

PR-007/PR-008 overlaps are reconciled before first overlapping mutation. PR-009 is non-blocking unless a future exact file overlap requires code conflict handling only.

## Post-Review Transition

If Plan Revision 3 is approved, compile/authorize the Revision 3 Slice Set and resume at **S01 retained implementation repair + Core revalidation**.

Until then:

```yaml
implementation_authorized: false
current_gate: plan_review
```
