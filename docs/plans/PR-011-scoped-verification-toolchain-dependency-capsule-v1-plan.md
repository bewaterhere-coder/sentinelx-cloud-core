# PR-011 — Scoped Verification Toolchain & Dependency Capsule V1 — Plan

## Plan State

```yaml
plan_revision: 3
task_id: PR-011-scoped-verification-toolchain-dependency-capsule-v1
requirement_revision: 1
status: approved
review_state: approved
implementation_authorized: true
approved_review_ref: docs/reviews/PR-011-scoped-verification-toolchain-dependency-capsule-v1-plan-review-r3.md
execution_slice_set_ref: docs/execution/PR-011-scoped-verification-toolchain-dependency-capsule-v1-slices.yaml
remediates:
  - PR011-R1-F1-source-under-test-materialization-pre-toolchain-binding
  - PR011-R1-F2-toolchain-capsule-integrity-resource-bounds
  - PR011-R2-F3-stale-main-baseline-pr007-merged-dependency-reconciliation
transport:
  type: github-pr
  pr_number: 11
  branch: task/scoped-verification-toolchain-dependency-capsule-v1
  base_branch: main
repository_baseline: df9252fd4305eed361d8dc84e04da90222cd622e
ancestry_refresh_commit: 90121415ea0680c776bf4075f6bfd6c3f077836d
prior_plan:
  revision: 2
  ref: docs/plans/PR-011-scoped-verification-toolchain-dependency-capsule-v1-plan-r2.md
  blob_sha: c30d771ea5167db92f549bcb8e55589a7550dafd
```

## 1. Revision 3 Decision

Revision 3 preserves the security and verification design from Revision 2 and changes only the repository-reality assumptions invalidated by subsequent merges.

The complete Revision 2 design is durably frozen at the `prior_plan` blob above and is incorporated by reference for all sections not explicitly replaced by this Revision 3 artifact. If a statement in Revision 2 conflicts with this artifact, Revision 3 controls.

The implementation remains a **provider-owned verification admission layer composed into the existing scoped executor**. It must not introduce a second executor, second scope authority, second audit journal, generic network access, arbitrary Host-path authority, or Hub modification.

The four integrity-bound concepts remain unchanged:

```text
VerificationProfile
  = provider policy for a trusted Node/npm verification environment

SourceUnderTestSnapshot
  = immutable provider-owned source snapshot bound to exact repository/revision identity

DependencyCapsule
  = immutable provider-owned offline npm dependency payload bound to package-lock digest

VerificationAdmission
  = one operation's sealed profile + source + dependency + lockfile identity
```

Round-1 F1/F2 mechanisms from Revision 2 remain normative:

- exact source identity and source manifest binding;
- broker materialization before process spawn;
- mandatory pre-SPAWN `package-lock.json` verification;
- complete deterministic toolchain manifest/digest;
- provider-generated workspace-local Node/npm launcher shims;
- pre-START and pre-SPAWN request-time toolchain revalidation;
- bounded source/dependency materialization with hard ceilings and cleanup;
- offline/no-network verification;
- credential/proxy/user-profile stripping;
- post-run source/lock integrity readback before success projection.

## 2. Current Repository Reality — F3 Replacement

Canonical remote `main` for this Plan revision is:

```text
df9252fd4305eed361d8dc84e04da90222cd622e
```

This main already contains completed PR-007 through merge commit:

```text
26fe28bd5e2317d31e09d2055b191447c3f7ed37
```

Therefore the following are now **canonical main seams**, not external/unmerged dependencies:

- `src/sentinelx_core/handlers/devforge_runtime.py`;
- builtin `devforge_runtime` provider lifecycle;
- `devforge_runtime.execute_scoped` dynamic schema exposure through generic `sentinel_local_api`;
- `make_devforge_execute_scoped_adapter(...)` composition into the existing profiled script handler;
- provider-owned MutationScopeStore lifecycle used by the builtin endpoint.

Current `devforge_runtime.execute_scoped` main contract accepts:

```text
scope_ref
repository
lineage
interpreter
content
args?
cwd?
env?
timeout?
```

and adapts those fields to the existing `scoped_mutation` script path. Revision 3 extends this canonical seam; it does not recreate it.

### Branch ancestry reconciliation

Before Revision 3 was written, the same PR-011 task branch was refreshed from current main by explicit two-parent merge commit:

```text
90121415ea0680c776bf4075f6bfd6c3f077836d
```

Read-back comparison against `main@df9252fd...` produced:

```yaml
status: ahead
ahead_by: 28
behind_by: 0
merge_base: df9252fd4305eed361d8dc84e04da90222cd622e
```

No replacement Task, branch, or PR was created. The ancestry refresh preserved the existing PR-011 orchestration artifacts and incorporated canonical PR-007 product/runtime code.

### PR-010 current relationship

PR-010 Canonical Repository Mutation Firewall V1 is now **Accepted but not yet integrated** at the time of Revision 3 planning. It remains an implementation-entry reconciliation dependency, not a code-copy dependency.

At every implementation entry:

1. re-read remote `main` and PR-010 state;
2. if PR-010 has merged, refresh PR-011 ancestry to the new canonical main before product mutation and consume its canonical firewall/inventory primitives;
3. if PR-010 is still unmerged, do not copy its implementation into PR-011;
4. verification toolchain/source/capsule stores must never become canonical-repository write authority;
5. profiled verification remains process mutation routed through the physically constrained scoped path.

## 3. Configuration and Integrity Contracts — Preserved from Revision 2

The Revision 2 configuration model remains normative, including provider-owned logical profiles and these V1 default limits:

```yaml
source_max_total_bytes: 536870912
source_max_files: 50000
dependency_max_total_bytes: 1073741824
dependency_max_files: 50000
max_single_file_bytes: 268435456
max_relative_path_chars: 512
```

Hard ceilings remain:

```yaml
source_max_total_bytes: 2147483648
dependency_max_total_bytes: 4294967296
source_max_files: 200000
dependency_max_files: 200000
max_single_file_bytes: 1073741824
max_relative_path_chars: 1024
```

Caller-visible requests contain logical identifiers and integrity expectations only. Caller-selected toolchain roots, executable paths, source-store paths, dependency-store paths, ACL targets, cache roots, and network endpoints remain rejected.

## 4. Source-Under-Test Contract — Preserved F1 Closure

The immutable `SourceUnderTestSnapshot` remains mandatory for profiled Node/npm verification.

It binds at least:

```text
repository identity
+ exact transport/revision identity
+ source subpath
+ canonical file manifest
+ source manifest digest
+ package-lock SHA-256
```

The broker, not the verification script, materializes admitted source into:

```text
<exact-workspace>\source
```

Before the first profiled process can SPAWN, the provider must prove:

```text
materialized source manifest == sealed source manifest
AND
source/package-lock.json exists
AND
sha256(source/package-lock.json) == sealed expected lock digest
AND
source lock digest == dependency capsule lock digest
```

A post-run source/lock check remains tamper detection only; it does not replace the pre-SPAWN truth binding.

## 5. Dependency Capsule Contract — Preserved F2 Closure

The immutable Node/npm dependency capsule remains provider-owned and offline. Manifest validation includes normalized paths, file sizes/hashes, payload digest, package-lock digest, reparse rejection, unexpected-file rejection, configured resource limits, and final-path containment.

Materialization target remains:

```text
<exact-workspace>\.sentinelx-verification\npm-cache
```

Missing package data, manifest mismatch, digest mismatch, oversized content, excessive file count, partial-copy failure, or tampering must fail closed. No network fallback is permitted.

## 6. Toolchain Integrity and Launcher Contract — Preserved F2 Closure

`ToolchainManifest V1` remains deterministic and covers every regular file under the admitted readable toolchain root that may influence execution.

Request-time integrity sequence remains:

```text
profile resolution
→ final-path validation
→ toolchain manifest/hash recomputation before START
→ durable START with sealed verification intent
→ sandbox activation/materialization
→ second toolchain manifest/hash verification before SPAWN
→ only then root process creation
```

Cached readiness is never request-time execution authority.

Host `npm.cmd`, `npm.ps1`, or PATH-discovered launchers are not authoritative. The provider creates deterministic workspace-local launcher shims that invoke exactly the sealed `node.exe + npm-cli.js` identity.

## 7. Audit and Evidence Contract

The existing `MutationAuditJournal` remains the only durable execution journal.

START evidence seals at least:

```yaml
profile_id: node_npm
profile_revision: 1
source_repository_digest: <sha256>
source_revision: <exact-revision>
source_manifest_digest: <sha256>
toolchain_kind: node_npm_v1
toolchain_digest: <sha256>
launcher_digest: <sha256>
capsule_id: <logical-id>
capsule_revision: 1
capsule_payload_digest: <sha256>
expected_package_lock_sha256: <sha256>
network_mode: none
resource_limits_digest: <sha256>
```

Successful result evidence must remain bounded and must expose logical identities/digests plus existing scope/audit identity and terminal state. It must not expose credentials, raw Host paths, package contents, or unrestricted environment data.

## 8. Environment and Execution Semantics

Existing scoped Python/PowerShell/Pwsh remain the root interpreters. Node/npm are available only as descendants under an admitted verification profile.

For `node_npm_v1`:

- working directory is confined beneath `<exact-workspace>\source` only;
- PATH uses the provider-generated workspace-local shim directory rather than Host launcher discovery;
- `NPM_CONFIG_CACHE` points to the workspace-local admitted cache;
- `NPM_CONFIG_OFFLINE=true` is mandatory;
- proxy/registry overrides and npm/Git/SSH/GitHub credentials are removed/rejected;
- temp/log/home/profile locations stay inside exact workspace;
- npm descendants stay inside the existing no-breakaway Job;
- direct canonical checkout access remains unavailable.

## 9. Readiness and Capability

Base `host_mutation_sandbox_v1` readiness remains independent.

Add a separate physical readiness feature such as:

```text
host_runtime.scoped_verification_node_npm_v1
```

It is true only after a real Windows/AppContainer self-check proves the configured profile is physically usable. Request-time source/capsule/toolchain integrity still runs independently for every operation.

## 10. Canonical `devforge_runtime` Integration — F3 Replacement

Because PR-007 is merged, this is no longer dependency-gated.

Modify canonical main seam `src/sentinelx_core/handlers/devforge_runtime.py` after the core verification contract exists.

Extend `execute_scoped` with one optional bounded object:

```yaml
verification:
  type: object
  required:
    - profile
    - source_id
    - source_manifest_sha256
    - source_revision
    - capsule_id
    - package_lock_sha256
  additionalProperties: false
```

Required adapter changes:

1. add `verification` to the exact `_EXECUTE_SCOPED_ALLOWED` set;
2. add the bounded schema to `_ACTION_SCHEMAS["execute_scoped"]`;
3. validate/copy only that object into the canonical scoped-handler payload;
4. do not permit Host-path, executable, cache, network, credential, or authority fields inside it;
5. keep `execution_profile="scoped_mutation"`, the existing scope/repository/lineage bindings, and the existing single executor;
6. project bounded verification evidence from the scoped-handler result without exposing raw Host paths or credentials;
7. keep transport as generic `sentinel_local_api`; no Hub schema/source/deployment change is required.

A `describe devforge_runtime` readback must expose the current verification selector directly from the Agent-owned schema.

## 11. Implementation Sequence

### Step A — policy + pure verification contracts

Implement provider profile parsing, resource limits/hard ceilings, SourceUnderTestSnapshot validation, DependencyCapsule validation, ToolchainManifest canonical digest, and VerificationAdmission request/admission schemas.

Expected seams include:

- `src/sentinelx_core/policy.py`
- new `src/sentinelx_core/verification_profile.py`
- `config.example.windows.yaml`
- pure tests.

### Step B — audit + sandbox + pre-SPAWN materialization

Compose verification intent into the existing audit START evidence and existing Windows sandbox.

Implement:

- exact source/cache/shim broker materialization after START and before SPAWN;
- source manifest + lockfile verification before SPAWN;
- read/execute-only toolchain ACL;
- second toolchain integrity check before SPAWN;
- bounded streaming copy and partial-copy cleanup;
- terminal ACL cleanup.

### Step C — scoped execution + real Node/npm verification

Extend the canonical scoped handler/environment so a profiled script can run real offline Node/npm through sealed workspace-local shims while preserving Job containment, credential stripping, exact-workspace semantics, and post-run integrity checks.

### Step D — readiness/capability/docs

Add separately gated Node/npm verification readiness, physical Windows self-checks, capability projection, configuration/operator documentation, and regression coverage.

### Step E — canonical `devforge_runtime` integration

This step is now an ordinary implementation step against canonical main, not an external dependency checkpoint.

Extend the merged PR-007 `devforge_runtime.execute_scoped` seam exactly as Section 10 specifies and validate live Agent-owned `describe` + `execute_scoped` readback.

### Step F — downstream AC12 proof

Requires separate ChatGPTControlShell PR-015 authority.

Procedure remains:

1. resolve exact current PR-015 head SHA;
2. build/read back a SourceUnderTestSnapshot for exact PR-015 `mcp/` bytes;
3. bind matching dependency capsule to that exact `mcp/package-lock.json` digest;
4. resume the separately authorized PR-015 S01 continuation without replaying implementation side effects;
5. run real offline `npm run typecheck` and `npm run check` through admitted scoped verification;
6. receipt must identify PR-015 head, source manifest, lockfile, toolchain, capsule, scope and audit identities;
7. PR-015 remains sole authority for its own Slice completion claim.

## 12. Required Test Matrix

### Pure/unit

- profile absent/valid/malformed;
- configured limits and hard-ceiling rejection;
- toolchain traversal/final-path rejection;
- ToolchainManifest deterministic digest;
- source repository/revision/manifest validation;
- wrong source head/revision/manifest;
- dependency capsule tamper/lock mismatch;
- size/file/path bounds;
- symlink/reparse/unexpected-file rejection;
- launcher shim deterministic identity;
- reserved environment and credential/proxy stripping.

### Scoped integration

- existing unprofiled Python/PowerShell/Pwsh remain unchanged;
- source copied only to exact workspace;
- lockfile verified before first SPAWN;
- Node/npm success through sealed shims;
- Host launcher substitution cannot affect execution;
- wrong source/capsule/lock fails before SPAWN;
- post-readiness toolchain replacement fails request-time validation;
- oversized capsule/source fails with partial-copy cleanup;
- missing cache remains offline and fails;
- toolchain write denied;
- descendants remain Job-contained;
- timeout/nonzero/activation failure closes transient authority.

### `devforge_runtime` integration

- `describe` exposes bounded verification schema from canonical Agent code;
- valid verification object is forwarded to canonical scoped handler;
- unknown/path/network/authority fields fail schema/admission;
- returned evidence is bounded;
- existing lifecycle actions and unprofiled `execute_scoped` remain regression-compatible.

### Physical Windows

- sealed `node --version` and `npm --version` inside AppContainer;
- offline fixture `npm ci` and package scripts;
- DNS/HTTP remains unavailable;
- canonical/protected roots remain inaccessible/non-mutable;
- source revision/manifest appears in evidence;
- transient toolchain ACL is absent after terminalization.

## 13. Requirement Traceability

| Requirement | Plan coverage |
|---|---|
| R1 provider-owned profiles | Steps A/D; Sections 3/9 |
| R2 read/execute toolchain only | Steps B/C; Sections 6/8 |
| R3 integrity-bound offline capsule | Steps A/B/C; Section 5 |
| R4 workspace-local materialization | Step B; Sections 4/5 |
| R5 no network widening | Steps C/D; Sections 5/8/12 |
| R6 one scoped executor | Steps B/C/E; Sections 1/10 |
| R7 `devforge_runtime` integration | Step E; Section 10 |
| R8 evidence/readiness | Steps B/D/E; Sections 7/9/10 |
| R9 migration safety | Steps A/C/D plus regression matrix |
| R10 downstream unblock | Step F |

## 14. Risks and Controls

| Risk | Control |
|---|---|
| verifies wrong source | exact immutable SourceUnderTestSnapshot + pre-SPAWN source/lock binding |
| toolchain receipt does not match executed launcher | complete ToolchainManifest + provider-generated sealed shims |
| cached readiness hides toolchain tamper | request-time pre-START + pre-SPAWN revalidation |
| capsule exhausts disk/time | admission/copy bounds + hard ceilings + partial cleanup |
| Host toolchain becomes writable | read/execute-only ACL + terminal removal + negative write test |
| dependency capsule smuggles Host authority | logical id + provider root + relative paths + manifest + containment |
| npm silently networks | no AppContainer network widening + offline config + missing-cache negative test |
| credentials leak | sanitized env + reserved-key rejection + isolated temp/home/profile |
| npm child escapes | existing Job containment + descendant regression test |
| base scoped execution regresses | optional profile + unprofiled regression matrix |
| PR-007 integration duplicated | extend canonical merged devforge_runtime only |
| PR-010 firewall weakened | fresh implementation-entry reconciliation + no unmerged code copy |
| downstream PR-015 is replayed | exact source snapshot + separate PR-015 authority + no side-effect replay |

## 15. Implementation Entry Gate

Implementation may proceed only after Plan Review approves Revision 3 and the exact Revision 3 Slice Set is persisted/read back.

Every Slice entry must then revalidate:

1. current remote `main` still matches or is reconciled into the task branch;
2. current PR-010 state and overlap;
3. Plan Revision 3 is still current and approved;
4. the Slice Set binds exact Plan Revision 3 / blob;
5. current Slice is dependency-ready;
6. required Host/runtime capability for that Slice is live;
7. no permission/network/credential/canonical-repository widening is required.

The physical Windows/Node/npm and live `devforge_runtime` slices may block on Host availability; they must not downgrade to mock-only completion evidence.

## 16. Approval Questions

Plan Review must answer:

1. Does the source snapshot + pre-SPAWN lock binding truthfully identify the source under test?
2. Does the toolchain manifest + sealed shim ensure the hashed toolchain is the executed toolchain?
3. Are source/capsule resource bounds and partial cleanup sufficient and testable?
4. Does Revision 3 correctly consume merged PR-007 without duplicating executor/scope authority?
5. Is PR-010 treated as an implementation-entry reconciliation boundary without importing unmerged code?
6. Can required offline/no-network/credential/Job/canonical-root behavior be observed with real Windows evidence?
7. Can AC12 be proven later without transferring ChatGPTControlShell authority into PR-011?

If approved, compile a new Slice Set bound exactly to Plan Revision 3. Do not reuse any older provisional Slice Set.
