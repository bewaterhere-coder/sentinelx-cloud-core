# PR-010 — SentinelX Provider Canonical Repository Mutation Firewall V1 — Plan

## Plan State

```yaml
task_id: PR-010-canonical-repository-mutation-firewall-v1
stage: plan_review
plan_status: proposed
plan_revision: 2
requirement: docs/requirements/PR-010-canonical-repository-mutation-firewall-v1.md
prior_plan_review: docs/reviews/PR-010-canonical-repository-mutation-firewall-v1-plan-review-r1.md
transport: github-pr
pr_number: 10
task_branch: task/canonical-repository-mutation-firewall-v1
base_branch: main
planning_baseline_main: f7e878f3497582547e5d52cd33b060cae18d2e84
implementation_authorized: false
execution_slice_set: null
acceptance_approved: false
completion_verified: false
remediation_r2:
  addressed_findings:
    - ProviderWideCoverageRegistrationFailClosedMechanism
    - DependencyReadbackOrderingBeforeOverlapMutation
  requirement_semantics_changed: false
```

Plan Revision 2 remediates the two plan-local findings from Review R1. It does **not** self-approve, compile an Execution Slice Set, or authorize `#开发执行`.

## Current Verified Reality

### Canonical repository

- project: `sentinelx-cloud-core`;
- canonical remote `main`: `f7e878f3497582547e5d52cd33b060cae18d2e84` at remediation time;
- local canonical checkout is not an implementation target because it was observed dirty/out-of-date during task creation;
- Task artifacts remain on the existing GitHub PR transport.

### Active dependency heads at remediation time

These are observations, not durable implementation authority:

```yaml
pr_007:
  head: 4b8bfd897b2e614bdb30fa85bcc400ee01c2469b
  state: implementation
  note: moving branch; S05 verification remains active
pr_008:
  head: f7594c468d764ad85c0dc508ad47f009c89793c1
  state: acceptance
  note: external Hub projection blocker remains
```

Any later movement invalidates these observations for an overlapping implementation Slice and triggers fresh readback before mutation.

### Existing security primitives to compose

1. `Policy.resolve_path(..., need_write=True)` canonicalizes paths and enforces `file_ops rw` for structured mutation.
2. `MutationExecutionPolicy` already owns `workspace_root`, `protected_roots`, `runtime_read_roots`, scoped-mutation enablement and related readiness inputs.
3. `edit` and destructive filesystem handlers already centralize path resolution before mutation.
4. structured Git `apply_patch` already uses the same `file_ops rw` substrate.
5. scoped mutation / audit / sandbox work exists from SX-HMSA and continues in PR-007/PR-008.
6. `handlers.build_registry()` is the runtime source of truth for dispatchable operations, and `capabilities.ops_supported` is already derived from that registry rather than a separate hand-maintained list.

### Gap to close

The existing primitives do not form a provider-wide canonical-repository exclusion boundary:

```text
file_ops rw                    = operator write allowlist
protected_roots                = scoped-mutation protection input
canonical repository firewall = missing provider-wide deny role
```

`exec` and legacy `script_run` are especially important because arbitrary child processes cannot be proven safe by parsing path-looking substrings from command/script text.

A second gap identified by Review R1 is coverage accounting: an operation registry containing only `op -> handler` cannot prove that every future model-facing repository mutator is covered by the firewall.

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

### D5 — Authoritative operation-effect registration is fail-closed

Review R1 F1 is closed by making repository-effect classification part of the same authoritative operation registration path that defines dispatch and `ops_supported`.

The implementation must replace or wrap bare `op -> handler` registration with equivalent metadata carrying at least:

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

Exact Python type names are implementation detail; the invariants are not.

Rules:

1. Dispatchability and `ops_supported` continue to derive from the authoritative registry; no second hand-maintained operation list becomes canonical.
2. A model-facing operation with `repository_effect=unknown`, missing effect metadata, or required-but-unproven firewall coverage makes `canonical_repository_mutation_firewall_v1` readiness **false**.
3. A new model-facing operation therefore fails closed for provider-wide firewall advertisement until its repository effect is explicitly classified and, when required, its enforcement is registered/proven.
4. Internal-only transport operations are explicitly marked `internal_only`; they are not silently treated as model-facing and do not become an unreviewed capability bypass.
5. Read-only operations are explicitly distinguishable from mutation operations and need no mutation firewall handler merely to satisfy coverage accounting.
6. Mixed operations such as structured Git must classify the mutation selector(s) rather than allowing the presence of a read-only selector to exempt the whole operation.
7. `disabled_ops` removal is applied before final readiness computation so an unavailable operation is not counted as exposed; readiness evidence records the effective registry surface.

Required invariant:

```text
new model-facing op registered
AND repository effect missing/unknown
→ firewall readiness false
→ canonical_repository_mutation_firewall_v1 not advertised
```

This composes with the existing registry design instead of reintroducing the historical hand-maintained drift problem.

### D6 — Dependency reconciliation is an entry gate before first overlapping mutation

Review R1 F2 is closed by moving active-branch reconciliation out of S04 and making it a pre-mutation admission rule for every Slice.

Before any Slice mutates a file overlapping PR-007/PR-008 semantics, execution must re-read:

```text
exact latest dependency head
changed-file set
relevant immutable contract/artifact revision
current dependency stage/disposition
```

and persist a no-loss composition decision for the current Slice.

Current known overlap family includes:

```text
client.py
handlers/basic.py
handlers/scoped_script.py
mutation_scope.py / mutation-scope handlers
capability/protocol feature projection code
```

Rules:

- S01/S02 may proceed without dependency reconciliation only while their exact mutation set does not overlap a live dependency surface.
- S03 **must** run this gate before touching `scoped_script` or any equivalent profiled-execution seam.
- S04 runs the same gate again if dependency state has moved or its mutation set overlaps capability/projection files.
- A moving dependency branch is evidence, not authority; stale planning-time SHAs cannot authorize transplantation.
- A material semantic conflict stops at a Decision Boundary; no silent overwrite, branch-state copying, or lossy rebase is allowed.

## Implementation Slices After Plan Approval

### S01 — Canonical inventory + core admission seam

**Entry admission**

- compute intended changed-file set before mutation;
- if any intended file overlaps the current PR-007/PR-008 overlap family, execute D6 first; otherwise record `dependency_overlap=false` for the Slice.

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

### S02 — Authoritative operation-effect registry + structured mutation integration

**Entry admission**

Compute exact changed-file set and run D6 before the first overlapping mutation.

**Scope**

1. Extend the authoritative operation registry with D5 metadata and fail-closed coverage accounting.
2. Keep dispatch and `ops_supported` derived from this same registry.
3. Integrate the central admission seam into explicit-path mutators:
   - edit + edit-upload completion;
   - move/copy/delete/chmod/chown;
   - structured Git `apply_patch`;
   - upload/finalization paths where host files are materialized;
   - any currently registered equivalent structured write primitive discovered from the authoritative registry.
4. Explicitly classify internal-only transfer operations and read-only operations.

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

- newly registered model-facing op with missing/unknown effect metadata => firewall readiness false;
- required-but-uncovered mutator => firewall readiness false;
- internal-only op is distinguishable from model-facing exposure;
- disabled op is removed before effective-surface readiness computation;
- exact canonical root and descendants blocked;
- non-canonical `rw` path still follows existing behavior;
- no `.bak.*` artifact on blocked edit/delete;
- move/copy endpoint matrix correct;
- structured Git read operations unaffected.

### S03 — Process mutation fail-closed boundary

**Hard entry gate**

Before touching `handlers/scoped_script.py`, `handlers/basic.py`, `client.py`, mutation-scope code, or an equivalent overlap surface, execute D6 against the exact current PR-007/PR-008 heads. The planning-time heads are not sufficient.

**Scope**

- use authoritative D5 registration metadata to identify all exposed process-producing operations (`exec`, script paths, background descendants and equivalents);
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
- scoped execution in a valid execution workspace remains governed by existing sandbox/audit authority;
- unclassified process operation makes firewall readiness false.

### S04 — Capability readiness + projection composition

**Entry admission**

Run D6 again whenever PR-007/PR-008 state moved after the last recorded reconciliation or this Slice touches an overlapping capability/projection file.

**Scope**

- compose final readiness probe from Host inventory, D5 effective operation registry, structured coverage and process disposition;
- advertise `canonical_repository_mutation_firewall_v1` only on complete provider-wide coverage;
- add bounded diagnostics/reason codes;
- integrate with current capability/hello projection without weakening PR-007/PR-008 semantics;
- update protocol-feature tests as required.

**Verification**

- one exposed unknown/unclassified op => capability absent/unavailable;
- one required uncovered mutator => capability absent/unavailable;
- policy disabled => capability unavailable without breaking legacy host;
- valid Windows configuration + complete effective-surface coverage => advertised;
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
10. capability advertisement removed whenever one required enforcement component is unavailable;
11. newly registered model-facing op with unknown effect class -> capability unavailable;
12. internal-only transport op does not silently become model-facing coverage evidence.

Documentation:

- README / config examples;
- SECURITY / THREAT_MODEL where boundary semantics belong;
- distinction among `file_ops`, `protected_roots`, canonical repository firewall and scoped mutation sandbox;
- authoritative operation-effect registration and fail-closed extension rule;
- migration/compatibility behavior for generic process tools.

## Implementation-Ready Admission Gate

Plan approval requires reviewers to confirm all of the following:

### P0-A — Inventory authority is distinct and sufficient

The proposed Host-owned canonical inventory must be accepted as provider authority and must not overload `protected_roots` or caller-supplied repository paths.

### P0-B — Process-surface semantics are acceptable

Review must explicitly accept the V1 compatibility trade-off:

> A host cannot advertise provider-wide canonical firewall protection while also retaining an arbitrary unprofiled process mutation path that has no physical canonical exclusion.

The approved Plan may choose a stronger OS-enforced mechanism instead, but it may not weaken this invariant.

### P0-C — Active dependency overlap is exact-readback driven before mutation

No Slice may mutate an overlapping PR-007/PR-008 seam until D6 has re-read the exact current dependency heads/contracts and recorded a no-loss composition decision. This applies before S03, not only during S04.

### P0-D — Provider-wide coverage extension is fail-closed by construction

The authoritative operation registration path must carry enough effect/exposure metadata that:

```text
new model-facing op + missing/unknown repository effect
→ firewall readiness false
```

A separate best-effort firewall list is insufficient.

### Admission result

```text
P0-A accepted
AND P0-B accepted
AND P0-C accepted
AND P0-D accepted
→ Plan Approved / Implementation Ready

otherwise
→ Plan Review Rejected or DecisionRequired
```

## Verification Strategy

### Unit/security tests

Add focused tests for:

- policy inventory parsing/normalization;
- canonical path classifier;
- authoritative operation effect/exposure registration;
- unknown/unclassified-op fail-closed readiness;
- each structured mutation operation;
- process admission modes;
- readiness/capability advertisement;
- platform support/fail-closed behavior.

### Regression suite

Run all affected existing suites, especially:

```text
handler registry/capabilities tests
file/edit/fsmutate tests
git operation tests
script/exec tests
mutation scope/sandbox/readiness tests
capability policy/protocol feature tests
SX-HMSA incident/security tests
```

### Dependency-drift evidence

For every Slice touching an overlap seam, persist equivalent evidence:

```yaml
dependency_reconciliation:
  pr_007_head: <exact current sha>
  pr_008_head: <exact current sha>
  changed_files_read: true
  relevant_contracts_read: true
  intended_slice_files: [...]
  overlap: [...]
  composition_disposition: no_loss | decision_required
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
| R6 | S03 scoped/legacy/background tests + D6 composition gate |
| R7 | D5 + S02/S04 authoritative coverage readiness tests |
| R8 | S02/S03 no generic canonical exception |
| R9 | S01 classifier + S03 scoped workspace evidence |
| R10 | S05 Windows incident + extension-regression matrix |

## Review R1 Remediation Traceability

| Review finding | Revision 2 disposition |
|---|---|
| F1 — no fail-closed operation classification source of truth | Closed by D5, P0-D, S02 and S04: operation exposure/effect classification is part of the authoritative dispatch registry; unknown model-facing operations invalidate firewall readiness by default. |
| F2 — dependency readback scheduled after possible overlapping mutation | Closed by D6, P0-C and per-Slice entry gates: exact dependency readback happens before the first overlapping mutation, including before S03 touches scoped/capability seams. |

## Risks and Controls

### Risk — over-blocking normal SentinelX administration

Control: firewall mode is explicit/readiness-gated; legacy hosts do not automatically advertise the capability. V1 favors fail-closed correctness over pretending arbitrary process execution is physically isolated.

### Risk — duplicated meanings for `protected_roots`

Control: new canonical inventory has one purpose; existing sandbox protected roots keep their current semantics.

### Risk — moving PR-007/PR-008 implementation conflict

Control: D6 is a per-Slice pre-mutation gate. A live dependency change invalidates stale overlap evidence before product-code mutation, not after it.

### Risk — capability advertised on partial or future-unclassified coverage

Control: readiness derives from the authoritative effective operation registry. Missing/unknown effect metadata or required-but-uncovered mutation invalidates the provider-wide capability by default.

### Risk — blocked operation leaves side effects

Control: target admission precedes backups, staging finalization, process spawn and material mutation; tests assert absence of backup/partial artifacts.

## Plan Review Target

Review Revision 2 should verify four questions:

1. Does the Host-owned canonical inventory have enough authority and separation from generic `protected_roots`?
2. Is fail-closing arbitrary generic process mutation the correct V1 security trade-off until an OS-enforced generic process mode exists?
3. Does authoritative operation-effect registration make future model-facing mutators fail closed for firewall advertisement by default?
4. Does dependency reconciliation now occur before the first possible overlapping mutation rather than after it?
