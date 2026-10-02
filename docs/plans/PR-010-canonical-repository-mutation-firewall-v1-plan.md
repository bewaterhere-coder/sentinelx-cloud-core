# PR-010 — SentinelX Provider Canonical Repository Mutation Firewall V1 — Plan

## Plan State

```yaml
task_id: PR-010-canonical-repository-mutation-firewall-v1
stage: plan_review
plan_status: proposed
plan_revision: 1
requirement: docs/requirements/PR-010-canonical-repository-mutation-firewall-v1.md
transport: github-pr
pr_number: 10
task_branch: task/canonical-repository-mutation-firewall-v1
base_branch: main
planning_baseline_main: f7e878f3497582547e5d52cd33b060cae18d2e84
implementation_authorized: false
execution_slice_set: null
acceptance_approved: false
completion_verified: false
```

This plan deliberately does **not** compile executable Slices before Plan Review. `#开发执行` remains unauthorized until the Plan is approved and a durable Execution Slice Set is materialized.

## Current Verified Reality

### Canonical repository

- project: `sentinelx-cloud-core`;
- canonical remote `main`: `f7e878f3497582547e5d52cd33b060cae18d2e84` at planning time;
- local canonical checkout is not an implementation target because it was observed dirty/out-of-date during task creation;
- all Task artifacts are created through the GitHub task branch transport.

### Existing security primitives to compose

1. `Policy.resolve_path(..., need_write=True)` canonicalizes paths and enforces `file_ops rw` for structured mutation.
2. `MutationExecutionPolicy` already owns `workspace_root`, `protected_roots`, `runtime_read_roots`, scoped-mutation enablement and related readiness inputs.
3. `edit` and destructive filesystem handlers already centralize path resolution before mutation.
4. structured Git `apply_patch` already uses the same `file_ops rw` substrate.
5. scoped mutation / audit / sandbox work exists from SX-HMSA and continues in PR-007/PR-008.

### Gap to close

The existing primitives do not form a provider-wide canonical-repository exclusion boundary:

```text
file_ops rw                    = operator write allowlist
protected_roots                = scoped-mutation protection input
canonical repository firewall = missing provider-wide deny role
```

`exec` and legacy `script_run` are especially important because arbitrary child processes cannot be proven safe by parsing path-looking substrings from command/script text.

## Design Decision

### D1 — Separate canonical inventory from generic protected roots

Add a Host-owned canonical repository inventory to mutation policy rather than reusing `protected_roots` as a second meaning.

Proposed portable shape (final field names may be normalized during implementation, semantics may not):

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

Properties:

- config is Host/operator authority, not caller payload authority;
- root is canonicalized at policy load;
- repository identity is normalized independently of transport URL/credentials;
- invalid/ambiguous entries make firewall readiness false;
- execution workspaces are separate roots and are not inferred canonical by repository identity alone;
- no DevForge-specific path or owner is compiled into SentinelX.

The existing `protected_roots` remains what it already means for sandbox/scoped-mutation policy.

### D2 — One reusable firewall module

Introduce one provider-owned module, tentatively:

```text
src/sentinelx_core/canonical_repository_firewall.py
```

Responsibilities:

```text
canonical inventory normalization/readiness
path intersection classification
write-target admission
generic-process disposition
structured diagnostic evidence
capability readiness summary
```

Handlers consume this module; handlers do not each invent canonical-role logic.

### D3 — Structured mutators get exact target admission

For operations with explicit target paths, enforcement occurs after normal path canonicalization but before backup, staging-finalization, patch application, permission change or child mutation.

Expected order:

```text
existing operation validation
→ canonicalize/resolve concrete target
→ canonical firewall admission
→ existing file_ops/scope/operation authority
→ first material side effect
```

When existing `file_ops` resolution is itself the canonicalization seam, the firewall may consume that already-resolved path rather than resolving twice.

### D4 — Generic process surfaces fail closed in V1

V1 will **not** claim that parsing shell/script content proves physical non-mutation.

When canonical firewall mode is enabled and the provider advertises `canonical_repository_mutation_firewall_v1`:

```text
generic/unprofiled exec capable of arbitrary filesystem mutation
legacy/unprofiled script_run
operator_unrestricted process fallback
```

must not remain an unrestricted path around canonical protection.

Preferred V1 disposition:

- process mutation requiring writes uses the existing profiled/scoped mutation path with sandbox/audit/scope authority;
- generic process execution that cannot be physically constrained against canonical roots is blocked under firewall-ready mode with a stable diagnostic;
- hosts that choose legacy generic process compatibility may keep it, but then firewall readiness/capability advertisement remains false.

This is an opt-in security boundary; default legacy hosts are not silently migrated into a stricter behavior merely by upgrading.

A future OS-enforced generic-process mode may restore broader `exec` compatibility, but it is not required to satisfy V1.

### D5 — Capability means complete coverage, not code presence

`canonical_repository_mutation_firewall_v1` is advertised only when all of the following hold:

```text
policy configured and enabled
canonical inventory valid/non-ambiguous
structured mutator coverage registered
process-surface disposition fail-closed
scoped process path has its own required readiness when used
no known model-facing repository mutator bypass exists
```

Feature presence and runtime readiness remain separate evidence.

## Implementation Slices After Plan Approval

### S01 — Canonical inventory + core admission seam

**Scope**

- extend policy parsing with canonical repository inventory and enablement;
- normalize repository identity without credentials;
- canonicalize roots and reject invalid/ambiguous overlap states;
- implement central classifier/admission module;
- expose deterministic readiness diagnostics without advertising capability yet.

**Primary files**

- `src/sentinelx_core/policy.py`;
- new `src/sentinelx_core/canonical_repository_firewall.py`;
- focused unit tests;
- configuration example fixture(s).

**Verification**

- traversal/symlink normalization;
- broad parent `file_ops rw` does not change canonical classification;
- canonical root vs same-repository execution workspace remains distinguishable;
- duplicate/conflicting inventory fails closed;
- caller payload cannot create/remove inventory authority.

**Stop condition**

Core classifier and readiness tests pass; no handler mutation behavior is changed yet.

### S02 — Structured mutation surface integration

**Scope**

Integrate the central admission seam into explicit-path mutators:

- edit + edit-upload completion;
- move/copy/delete/chmod/chown;
- structured Git `apply_patch`;
- upload/finalization paths where host files are materialized;
- any currently registered equivalent structured write primitive found by operation-registry audit.

**Security ordering**

Firewall block must occur before:

```text
backup creation
partial overwrite/delete
patch application
metadata mutation
final file materialization
```

**Verification**

- exact canonical root and descendants blocked;
- non-canonical `rw` path still follows existing behavior;
- no `.bak.*` artifact on blocked edit/delete;
- move/copy endpoint matrix correct;
- structured Git read operations unaffected.

### S03 — Process mutation fail-closed boundary

**Scope**

- inventory all model-facing process-producing operations (`exec`, script paths, background descendants, any equivalent operation registry entry);
- add a single process admission policy tied to firewall readiness;
- block legacy/unprofiled arbitrary mutation process paths when firewall-ready mode is enabled unless physical canonical exclusion is independently proven;
- preserve profiled/scoped mutation path and its existing sandbox/audit/scope requirements;
- ensure timeout/nonzero/background child paths do not escape the process boundary.

**Non-goal**

No shell/script text parser may be treated as the security proof.

**Verification**

- `git switch`, redirection, Python/PowerShell file write and spawned-child canonical writes cannot bypass;
- `operator_unrestricted` is not fallback;
- legacy compatibility remains available only with firewall capability unavailable;
- scoped execution in a valid execution workspace remains governed by existing sandbox/audit authority.

### S04 — Capability readiness + active-branch reconciliation

**Admission before touching overlap files**

Re-read exact latest PR-007 and PR-008 heads and changed files. Current planning-time overlaps include capability/scoped execution surfaces such as:

```text
client.py
handlers/basic.py
handlers/scoped_script.py
mutation scope code
```

Do not copy moving-branch state by memory.

**Scope**

- compose final readiness probe;
- advertise `canonical_repository_mutation_firewall_v1` only on complete provider-wide coverage;
- add bounded diagnostics/reason codes;
- integrate with current capability/hello projection without weakening PR-007/PR-008 semantics;
- update protocol-feature tests as required.

**Verification**

- one uncovered mutator => capability absent/unavailable;
- policy disabled => capability unavailable without breaking legacy host;
- valid Windows configuration + complete coverage => advertised;
- Linux/macOS remain unavailable unless equivalent physical enforcement is proven.

### S05 — Incident regression, security suite, docs

**Scope**

Freeze the real incident family and complete documentation.

Required regression matrix:

1. broad parent `rw` + canonical edit -> blocked;
2. canonical delete/edit -> blocked before backup;
3. canonical structured Git patch -> blocked;
4. generic process `git switch`/write -> blocked under firewall-ready mode;
5. indirect/background child canonical write -> blocked;
6. unknown inventory/target -> fail closed;
7. canonical read/list/search/status/diff -> allowed;
8. same-repository execution workspace scoped write -> allowed by firewall then evaluated by existing authorities;
9. fake `canonical_sync` claim on generic tool -> no bypass;
10. capability advertisement removed whenever one required enforcement component is unavailable.

Documentation:

- README / config examples;
- SECURITY / THREAT_MODEL where boundary semantics belong;
- distinction among `file_ops`, `protected_roots`, canonical repository firewall and scoped mutation sandbox;
- migration/compatibility behavior for generic process tools.

## Implementation-Ready Admission Gate

Plan approval requires reviewers to confirm all of the following:

### P0-A — Inventory authority is distinct and sufficient

The proposed Host-owned canonical inventory must be accepted as provider authority and must not overload `protected_roots` or caller-supplied repository paths.

### P0-B — Process-surface semantics are acceptable

Review must explicitly accept the V1 compatibility trade-off:

> A host cannot advertise provider-wide canonical firewall protection while also retaining an arbitrary unprofiled process mutation path that has no physical canonical exclusion.

The approved Plan may choose a stronger OS-enforced mechanism instead, but it may not weaken this invariant.

### P0-C — Active PR overlap strategy is exact-readback driven

PR-007/PR-008 moving branches do not block S01/S02 automatically, but overlapping capability/scoped-execution files may not be modified until exact dependency heads are re-read and a no-loss composition/rebase strategy is recorded.

### Admission result

```text
P0-A accepted
AND P0-B accepted
AND P0-C accepted
→ Plan Approved / Implementation Ready

otherwise
→ Plan Review Rejected or DecisionRequired
```

## Verification Strategy

### Unit/security tests

Add focused tests for:

- policy inventory parsing/normalization;
- canonical path classifier;
- each structured mutation operation;
- process admission modes;
- readiness/capability advertisement;
- platform support/fail-closed behavior.

### Regression suite

Run all affected existing suites, especially:

```text
file/edit/fsmutate tests
git operation tests
script/exec tests
mutation scope/sandbox/readiness tests
capability policy/protocol feature tests
SX-HMSA incident/security tests
```

### Windows evidence

Before Acceptance Approved, run the incident matrix on a Windows candidate build with a fixture containing:

```text
broad rw parent
canonical checkout root
same-repository non-canonical execution workspace
scoped mutation readiness where applicable
```

No production-host upgrade is implied by candidate verification.

## Acceptance Mapping

| Requirement | Plan evidence |
|---|---|
| R1 | S01 inventory + policy tests |
| R2 | S01 central admission module |
| R3 | S02 structured mutation matrix |
| R4 | S02 Git matrix |
| R5 | S03 process fail-closed boundary |
| R6 | S03 scoped/legacy/background tests |
| R7 | S04 readiness + advertisement tests |
| R8 | S02/S03 no generic canonical exception |
| R9 | S01 classifier + S03 scoped workspace evidence |
| R10 | S05 Windows incident regression matrix |

## Risks and Controls

### Risk — over-blocking normal SentinelX administration

Control: firewall mode is explicit/readiness-gated; legacy hosts do not automatically advertise the capability. V1 favors fail-closed correctness over pretending arbitrary process execution is physically isolated.

### Risk — duplicated meanings for `protected_roots`

Control: new canonical inventory has one purpose; existing sandbox protected roots keep their current semantics.

### Risk — moving PR-007/PR-008 implementation conflict

Control: S04 requires immutable head readback before overlapping file mutation; no moving branch is silently treated as canonical truth.

### Risk — capability advertised on partial coverage

Control: readiness is composed from registered operation coverage; a missing surface invalidates the provider-wide claim.

### Risk — blocked operation leaves side effects

Control: target admission precedes backups, staging finalization, process spawn and material mutation; tests assert absence of backup/partial artifacts.

## Plan Review Target

Review should focus on three questions rather than implementation style:

1. Does the Host-owned canonical inventory have enough authority and separation from generic `protected_roots`?
2. Is fail-closing arbitrary generic process mutation the correct V1 security trade-off until an OS-enforced generic process mode exists?
3. Does the coverage/readiness model make it impossible to advertise `canonical_repository_mutation_firewall_v1` while any model-facing repository mutator remains outside enforcement?
