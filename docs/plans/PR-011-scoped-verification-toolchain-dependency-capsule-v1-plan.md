# PR-011 — Scoped Verification Toolchain & Dependency Capsule V1 — Plan

## Plan State

```yaml
plan_revision: 2
task_id: PR-011-scoped-verification-toolchain-dependency-capsule-v1
requirement_revision: 1
status: proposed
review_state: pending
implementation_authorized: false
remediates:
  - PR011-R1-F1-source-under-test-materialization-pre-toolchain-binding
  - PR011-R1-F2-toolchain-capsule-integrity-resource-bounds
transport:
  type: github-pr
  pr_number: 11
  branch: task/scoped-verification-toolchain-dependency-capsule-v1
  base_branch: main
repository_baseline: f7e878f3497582547e5d52cd33b060cae18d2e84
```

## 1. Planning Decision

Implement V1 as a **provider-owned verification admission layer composed into the existing scoped executor**, not as a new command runner and not as a generic AppContainer mount/network feature.

Revision 2 separates four independently integrity-bound concepts:

```text
VerificationProfile
  = provider policy describing trusted Node/npm toolchain and stores

SourceUnderTestSnapshot
  = immutable provider-owned source snapshot bound to exact repository/revision identity

DependencyCapsule
  = immutable provider-owned offline npm dependency payload bound to package-lock digest

VerificationAdmission
  = one operation's resolved profile + source snapshot + dependency capsule + lockfile expectation
```

Only `VerificationAdmission` may reach sandbox/execution code. Caller-provided Host paths never do.

The existing Scope, `MutationAuditJournal`, Windows AppContainer, Job containment, exact-workspace ACL and terminalization remain authoritative.

## 2. Repository Reality / Entry Points

Current `main` implementation seams:

- `src/sentinelx_core/policy.py`
  - `MutationExecutionPolicy`
  - provider-owned canonical path parsing
  - existing `runtime_read_roots`
- `src/sentinelx_core/handlers/scoped_script.py`
  - `_scoped_environment`
  - `_run_scoped`
  - one canonical profiled script execution path
- `src/sentinelx_core/windows_mutation_sandbox.py`
  - exact workspace materialization
  - AppContainer profile/ACL activation
  - `_grant_runtime_read` / `_remove_runtime_read`
  - suspended spawn + Job containment
- `src/sentinelx_core/mutation_audit.py`
  - durable START → SPAWN → FINISH lifecycle
- `src/sentinelx_core/mutation_readiness.py`
  - base scoped-runtime physical self-check
- `src/sentinelx_core/handlers/basic.py`
  - execution-feature capability projection
- `config.example.windows.yaml`
- existing scoped-script / sandbox / audit / activation tests.

Integration seam that is **not on main**:

- PR-007 `src/sentinelx_core/handlers/devforge_runtime.py`
  - builtin `devforge_runtime.execute_scoped`
  - dynamic `params_schema` through generic `sentinel_local_api`
  - adapter onto the existing profiled script handler.

PR-007 is currently Accepted but unmerged. No Plan step may import that file from an unmerged branch as if it were baseline reality.

PR-010 remains unmerged and owns canonical-repository mutation-firewall semantics. Fresh overlap reconciliation is required at implementation entry.

## 3. Configuration Model

Extend `MutationExecutionPolicy` with optional verification profiles. Existing hosts with no mapping remain unchanged.

```yaml
mutation_execution:
  scoped_mutation_enabled: true
  workspace_root: D:\coco\DevForge-workspaces
  protected_roots:
    - D:\coco\repos

  verification_profiles:
    node_npm:
      kind: node_npm_v1
      toolchain_root: C:\Program Files\nodejs
      node_relative: node.exe
      npm_cli_relative: node_modules\npm\bin\npm-cli.js
      source_snapshot_root: D:\coco\sentinelx-verification-sources
      dependency_capsule_root: D:\coco\sentinelx-verification-capsules\node-npm
      capsule_manifest_revision: 1
      limits:
        source_max_total_bytes: 536870912
        source_max_files: 50000
        dependency_max_total_bytes: 1073741824
        dependency_max_files: 50000
        max_single_file_bytes: 268435456
        max_relative_path_chars: 512
```

V1 safe defaults are the values above. Operator configuration may lower them or raise them only to hard ceilings:

```yaml
hard_ceiling:
  source_max_total_bytes: 2147483648       # 2 GiB
  source_max_files: 200000
  dependency_max_total_bytes: 4294967296   # 4 GiB
  dependency_max_files: 200000
  max_single_file_bytes: 1073741824        # 1 GiB
  max_relative_path_chars: 1024
```

Rules:

1. profile key is caller-visible; Host roots are not;
2. all roots are operator policy and canonicalized at config load;
3. relative executable members are traversal-free and resolve inside `toolchain_root`;
4. toolchain/source/dependency roots must not overlap `workspace_root`, `protected_roots`, provider state/evidence roots, or Host canonical repository inventory when available;
5. verification roots are not converted into generic caller-selected `runtime_read_roots`;
6. no profile is inferred from PATH;
7. configured limits above hard ceilings are rejected at policy load;
8. profile parsing is additive and legacy hosts remain compatible.

Use a dedicated module such as `src/sentinelx_core/verification_profile.py` for policy-independent verification contracts and admission logic.

## 4. Immutable Source-Under-Test Snapshot Contract — F1

V1 introduces a provider-owned immutable `SourceUnderTestSnapshot` used only for verification input. It is not a replacement for DevForge's generic execution-workspace materialization contract.

Provider store shape:

```text
<source_snapshot_root>/<logical-source-id>/
  source-snapshot.json
  payload/
    ... exact source-under-test bytes ...
```

Manifest V1 includes at least:

```json
{
  "schema_version": 1,
  "kind": "verification_source_snapshot",
  "source_id": "...",
  "repository": {"vcs":"git","authority":"github.com","path":"owner/repo"},
  "transport": {"type":"github-pr","pr_number":15,"head_sha":"<40-hex>"},
  "source_subpath": "mcp",
  "source_manifest_digest": "<sha256>",
  "package_lock_sha256": "<sha256>",
  "files": [
    {"path":"package.json","size":123,"sha256":"..."},
    {"path":"package-lock.json","size":456,"sha256":"..."}
  ]
}
```

Security/determinism rules:

- source id is a logical identifier, never a Host path;
- repository identity + exact transport revision/head SHA are mandatory for Git-backed source;
- `source_subpath` is repository-relative semantic metadata, not a Host path;
- file paths are normalized relative paths; absolute/traversal/reparse entries are rejected;
- file entries are sorted before canonical digest computation;
- `source_manifest_digest` is SHA-256 of canonical source identity + file-entry data;
- every file size/hash is verified from the immutable store before admission;
- unexpected files and reparse points fail closed;
- source limits from Section 3 are enforced before and during copy;
- source snapshot preparation is an explicit provider/operator/transport build step outside scoped execution; scoped verification never fetches source from network and never reads the canonical checkout from inside AppContainer.

A utility such as `tools/build-verification-source-snapshot.py` may construct the snapshot from an already authorized transport/workspace. It is not model-facing execution authority.

## 5. Node/npm Dependency Capsule Contract

Use an immutable directory capsule:

```text
<dependency_capsule_root>/<capsule-id>/
  verification-capsule.json
  npm-cache/
    ... npm cache payload ...
```

Manifest V1 includes:

```json
{
  "schema_version": 1,
  "kind": "node_npm_dependency_capsule",
  "capsule_id": "...",
  "package_lock_sha256": "...",
  "payload_digest": "...",
  "files": [
    {"path":"npm-cache/...","size":123,"sha256":"..."}
  ]
}
```

Rules:

- normalized relative paths only;
- every file size/hash verified before materialization;
- `payload_digest` is over canonical file-entry data, not timestamps;
- provider resolves logical capsule id beneath configured root and verifies final containment;
- reparse points/symlinks/unexpected files fail closed;
- package-lock SHA-256 is mandatory;
- dependency limits from Section 3 are enforced during manifest admission and streaming copy;
- limit breach returns a stable verification-environment error and any partial workspace copy is removed before proceeding;
- missing package data never enables network fallback.

`tools/build-node-npm-verification-capsule.py` may prepare capsules outside scoped execution.

## 6. Deterministic Toolchain Integrity Contract — F2

The Node/npm profile has one deterministic **ToolchainManifest V1** generated from the provider-resolved readable toolchain root.

Because the AppContainer receives read authority to the admitted toolchain tree, the digest covers every regular file that can influence execution under that root, not only `node.exe` and `npm-cli.js`.

Canonical digest input:

```json
{
  "contract_revision": 1,
  "kind": "node_npm_v1",
  "node_relative": "node.exe",
  "npm_cli_relative": "node_modules/npm/bin/npm-cli.js",
  "files": [
    {"path":"<normalized-relative>","size":123,"sha256":"..."}
  ]
}
```

Rules:

- file entries are sorted by normalized relative path;
- absolute/traversal/reparse entries are rejected;
- unexpected files relative to the sealed manifest fail revalidation;
- `toolchain_digest = sha256(canonical_json(manifest))`;
- request admission recomputes/validates final paths, sizes, hashes and digest before durable START;
- after sandbox activation and before SPAWN, the exact selected toolchain manifest/digest is revalidated again to close the readiness-cache/TOCTOU gap;
- cached capability readiness is never request-time integrity authority.

### Authoritative launcher

V1 MUST NOT execute Host `npm.cmd`, `npm.ps1`, or another PATH-discovered launcher.

The provider creates deterministic workspace-local launch shims under:

```text
<exact-workspace>\.sentinelx-verification\bin
```

They invoke exactly:

```text
provider-resolved node.exe
+ provider-resolved node_modules/npm/bin/npm-cli.js
```

The shim bytes/digest are derived from the sealed `VerificationAdmission` and are included in verification START evidence. The verification environment prepends only this shim directory for logical `npm`/`node` convenience; execution identity remains the sealed Node/npm components. Launcher substitution or PATH shadowing is rejected/neutralized.

## 7. Verification Request / Admission Shape

Internal canonical scoped-handler payload:

```yaml
verification:
  profile: node_npm
  source_id: <logical-id>
  source_manifest_sha256: <64-hex>
  source_revision: <exact-head-sha-or-equivalent>
  capsule_id: <logical-id>
  package_lock_sha256: <64-hex>
```

Additional Host path/network/executable/cache fields are rejected.

Resolution produces immutable `VerificationAdmission` containing:

- profile id + contract revision;
- exact source repository/transport revision identity;
- source manifest digest + admitted file inventory;
- provider-resolved toolchain manifest/digest and exact node/npm CLI identities;
- dependency capsule revision/payload digest;
- expected package-lock digest;
- configured resource limits;
- offline/network mode = `none`;
- exact workspace-local source/cache/shim destinations.

Admission order before START:

```text
resolve policy profile
→ verify source snapshot identity/manifest/bounds
→ verify dependency capsule identity/manifest/bounds
→ verify source lock digest == dependency lock digest == request lock digest
→ recompute/verify toolchain manifest + digest
→ construct immutable VerificationAdmission
→ durable audit START
```

Caller fields are never consulted again for Host path authority.

## 8. Audit Binding

Use the existing `MutationAuditJournal`; do not create a second verification journal.

Seal a bounded verification intent into START evidence:

```yaml
verification_intent:
  profile_id: node_npm
  profile_revision: 1
  source_repository_digest: <sha256>
  source_revision: <exact revision>
  source_manifest_digest: <sha256>
  toolchain_kind: node_npm_v1
  toolchain_digest: <sha256>
  launcher_digest: <sha256>
  capsule_id: <id>
  capsule_revision: 1
  capsule_payload_digest: <sha256>
  expected_package_lock_sha256: <sha256>
  network_mode: none
  resource_limits_digest: <sha256>
```

The object participates in the existing START evidence digest. Receipt projection exposes logical identities/digests, never raw Host paths, credentials or package contents.

## 9. Pre-SPAWN Workspace Materialization — F1/F2

After durable START and exact sandbox workspace activation, but **before any root process is spawned**:

1. broker materializes the admitted source snapshot payload into:
   ```text
   <exact-workspace>\source
   ```
2. broker re-hashes the complete workspace source copy and proves it equals sealed `source_manifest_digest`;
3. broker requires `<exact-workspace>\source\package-lock.json` to exist and verifies its SHA-256 equals the sealed expected digest;
4. broker materializes the admitted dependency capsule into:
   ```text
   <exact-workspace>\.sentinelx-verification\npm-cache
   ```
5. broker re-hashes materialized cache against the capsule manifest;
6. broker writes deterministic launcher shims into the reserved verification bin and verifies their digest;
7. provider revalidates toolchain final paths + manifest digest a second time;
8. only after all checks pass may `sandbox.spawn(...)` create the suspended root PowerShell/Python process.

Consequences:

- `package-lock.json` may **not** be absent at SPAWN for a profiled Node/npm verification;
- no script is allowed to materialize or choose the package-under-test after process start;
- the AppContainer never reads the immutable source/capsule stores directly;
- every mutable copy is confined to exact workspace;
- any copy/hash/bounds failure removes partial reserved material and fails before SPAWN;
- a post-run source/lock digest check remains mandatory tamper detection before successful receipt.

This directly closes Round-1 F1.

## 10. Environment Composition

Create a verification-specific overlay on the existing sanitized scoped environment.

For `node_npm_v1`:

- set `cwd` for verification scripts beneath `<exact-workspace>\source` only;
- prepend the workspace-local provider-generated shim directory to PATH;
- do not add Host toolchain root to PATH as a launcher-discovery mechanism;
- set `NPM_CONFIG_CACHE` to workspace-local admitted cache;
- force `NPM_CONFIG_OFFLINE=true`;
- disable npm audit/fund/update-notifier network-adjacent behavior;
- set temp/log/home/profile locations inside exact workspace;
- remove inherited proxy/registry overrides and credential-bearing npm/Git/SSH/GitHub variables;
- reject caller `env` attempts to override reserved verification keys;
- reject `NODE_OPTIONS` values that could inject external code.

At minimum reserve/filter:

```text
PATH
HTTP_PROXY / HTTPS_PROXY / ALL_PROXY / NO_PROXY
npm_config_proxy / npm_config_https_proxy
npm_config_registry
NPM_CONFIG_CACHE
NPM_CONFIG_OFFLINE
NODE_OPTIONS
NPM_TOKEN / NODE_AUTH_TOKEN
GITHUB_TOKEN / GH_TOKEN
GIT_ASKPASS / SSH_AUTH_SOCK
USERPROFILE / HOME / APPDATA / LOCALAPPDATA
```

Existing non-profiled scoped execution remains unchanged.

## 11. Node/npm Execution Semantics

Do **not** add `node` as a generic scoped interpreter.

Reuse existing `python3` / `powershell` / `pwsh` root execution. The provider-generated shims expose the sealed Node/npm toolchain to descendants while preserving the one existing executor and Job containment.

Example verification script:

```powershell
npm ci --offline
npm run typecheck
npm test
npm run check
```

The logical `npm` resolves only to the workspace-local sealed shim, which invokes the exact hashed Node + npm CLI. Missing cache content fails offline.

Before successful result projection:

- source manifest is re-hashed or source mutation policy is checked according to the sealed source contract;
- package-lock SHA-256 is rechecked;
- toolchain/capsule/source identities in the result must match START evidence;
- terminal Scope closure remains required.

## 12. Readiness / Capability

Keep base `host_mutation_sandbox_v1` readiness independent.

Add a separate feature such as:

```text
host_runtime.scoped_verification_node_npm_v1
```

Readiness verifies physically:

- profile configuration resolves;
- toolchain manifest/digest can be computed;
- Node/npm final paths are valid;
- AppContainer receives read/execute but not write to toolchain root;
- provider-generated launcher invokes sealed Node/npm components;
- `node --version` / `npm --version` run in exact workspace + existing Job;
- no broker credentials/user profile are inherited;
- terminalization removes transient ACL authority.

Readiness remains a capability preflight only. Every verification request independently revalidates selected source/capsule/toolchain integrity as defined above. Toolchain replacement after readiness therefore fails request admission even if readiness was cached.

## 13. `devforge_runtime` Integration Dependency

Core implementation remains independent of PR-007.

Only after exact PR-007/equivalent admission exists in repository ancestry may `handlers/devforge_runtime.py` be modified.

Extend `execute_scoped` schema with only:

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

The adapter passes this bounded object to the existing scoped handler. No Host paths, duplicate executor or Hub change.

If PR-007 remains unmerged when core slices finish, stop at an external dependency checkpoint before this integration slice.

## 14. PR-010 Overlap Reconciliation

At every implementation entry:

1. re-read `main` and PR-010 state;
2. if PR-010 merged, consume its canonical repository inventory/firewall primitive rather than duplicate it;
3. toolchain/source/capsule stores must never become canonical-repository write authority;
4. profiled execution remains `process_mutation` routed through the physically constrained scoped path;
5. no PR-010 implementation is copied from an unmerged branch.

## 15. Implementation Sequence

### Step A — policy + pure contracts

Expected files:

- `src/sentinelx_core/policy.py`
- new `src/sentinelx_core/verification_profile.py`
- `config.example.windows.yaml`
- pure tests.

Implements:

- profile parsing + limits/hard ceilings;
- SourceUnderTestSnapshot manifest/digest/bounds;
- DependencyCapsule manifest/digest/bounds;
- ToolchainManifest deterministic digest contract;
- request/admission schemas.

Exit evidence:

- legacy config unchanged;
- path/bounds/manifest/launcher substitution cases fail closed;
- no AppContainer mutation yet.

### Step B — audit + sandbox + pre-SPAWN materialization

Expected files:

- `src/sentinelx_core/mutation_audit.py`
- `src/sentinelx_core/windows_mutation_sandbox.py`
- verification helpers/tests.

Implements:

- verification intent sealed at START;
- exact source/cache/shim broker materialization after START and before SPAWN;
- mandatory pre-SPAWN source manifest + lockfile verification;
- read/execute-only toolchain ACL;
- second request-time toolchain integrity check;
- bounded streaming copy and partial-copy cleanup;
- transient ACL cleanup.

Exit evidence:

- wrong source head/manifest/lockfile fails before SPAWN;
- toolchain tamper after readiness fails before SPAWN;
- oversized/file-count capsule fails without residual partial copy;
- existing sandbox tests remain passing.

### Step C — scoped execution + real Node/npm verification

Expected files:

- `src/sentinelx_core/handlers/scoped_script.py`
- optional snapshot/capsule builder utilities
- scoped integration/Windows fixtures.

Exit evidence:

- real sealed Node/npm toolchain executes through workspace-local shim;
- matching source + lockfile + dependency capsule completes offline npm checks;
- source mutation / launcher substitution / cache miss / credential override / network attempts fail closed;
- npm descendants remain in existing Job;
- post-run lockfile/source integrity verified before success projection.

### Step D — readiness/capability/docs

Expected files:

- readiness module(s)
- `src/sentinelx_core/handlers/basic.py`
- README/config docs
- activation/readiness tests.

Exit evidence:

- base sandbox readiness unaffected;
- separate Node/npm readiness is physically gated;
- cached readiness is proven non-authoritative for request-time toolchain integrity.

### Step E — dependency-gated `devforge_runtime` integration

Precondition: exact PR-007/equivalent is admitted into repository ancestry or explicitly reconciled after merge.

Exit evidence:

- local_api `describe` exposes bounded verification object;
- `execute_scoped` uses source/profile/capsule identities and existing executor;
- Host-path fields rejected;
- no Hub modification.

### Step F — downstream AC12 proof

Requires separate authority from ChatGPTControlShell PR-015.

Procedure:

1. resolve exact current PR-015 head SHA from its canonical transport;
2. construct/read back a verification source snapshot containing the exact `mcp/` package bytes from that head, with manifest bound to repository `bewaterhere-coder/ChatGPTControlShell`, PR #15, head SHA and source subpath `mcp`;
3. build/admit the matching dependency capsule from that exact `mcp/package-lock.json` digest;
4. invoke PR-015's separately authorized S01 continuation without replaying implementation side effects;
5. provider materializes source/cache into fresh exact workspace and verifies lockfile before SPAWN;
6. execute real `npm run typecheck` and `npm run check` offline;
7. receipt identifies PR-015 head SHA + source manifest digest + lockfile digest + toolchain digest + capsule digest + audit/scope identity;
8. PR-015 remains sole authority to issue its Slice completion receipt.

PR-011 Acceptance may consume that receipt as AC12 evidence but cannot synthesize or mutate PR-015 state.

## 16. Test Matrix

### Pure/unit

- profile absent/valid/malformed;
- configured limits and hard-ceiling rejection;
- toolchain member traversal/final-path rejection;
- ToolchainManifest canonical digest stability;
- source snapshot repository/revision/manifest digest validation;
- wrong source head/revision and manifest mismatch;
- dependency capsule containment/tamper/lock mismatch;
- source/capsule bytes, file-count, per-file and path-length bounds;
- symlink/reparse/unexpected-file rejection;
- launcher shim deterministic digest;
- reserved environment rejection and credential/proxy stripping.

### Scoped integration

- existing unprofiled Python/PowerShell unchanged;
- source copied only into exact workspace;
- package-lock verified before first SPAWN;
- node/npm success through provider shim;
- Host `npm.cmd`/`npm.ps1` substitution cannot affect execution;
- wrong source/capsule/lockfile fails before SPAWN;
- post-readiness toolchain replacement fails request-time revalidation;
- oversized capsule/file-count exhaustion fails closed;
- partial source/cache copy cleanup on failure;
- missing cache remains offline and fails;
- toolchain write denied;
- capsule/source immutable stores not AppContainer-writable;
- descendants remain Job-contained;
- timeout/nonzero/activation failure removes transient ACL/scope authority.

### Physical Windows

- sealed `node --version` / `npm --version` in AppContainer;
- offline fixture `npm ci` + scripts;
- DNS/HTTP probe remains unavailable;
- canonical/protected roots inaccessible/non-mutable;
- exact source manifest/head appears in receipt;
- residual toolchain ACL absent after terminalization.

### Regression

- mutation policy tests;
- scoped-script tests;
- mutation readiness tests;
- Windows mutation sandbox tests;
- incident regression suite;
- full CI and macOS compatibility where applicable.

## 17. Risks and Controls

| Risk | Control |
|---|---|
| Verification checks wrong source | immutable SourceUnderTestSnapshot bound to exact transport head + pre-SPAWN manifest/lock verification |
| Script creates/replaces source after start | source materialized by broker before SPAWN; post-run integrity check before success |
| Toolchain receipt hashes different launcher | complete toolchain manifest + provider-generated sealed launcher shim; no Host PATH npm launcher |
| Toolchain changes after cached readiness | request-time pre-START and pre-SPAWN manifest revalidation |
| Capsule resource exhaustion | fixed defaults + hard ceilings + streaming bounds + partial-copy cleanup |
| Toolchain ACL grants write | dedicated read/execute ACL + negative physical test + closure readback |
| Capsule/source smuggles Host path | logical ids + provider roots + normalized manifest + final-path containment |
| npm silently networks | offline env + proxy/registry sanitization + no-network physical test |
| Credential leak | environment deny/reserved set + isolated workspace profiles |
| Job descendant escape | existing no-breakaway Job + lifecycle descendant regression |
| Audit loses verification identity | source/toolchain/capsule/lock/limits sealed into START evidence |
| Base runtime becomes unavailable | independent verification readiness feature |
| PR-007 copied silently | dependency-gated Step E |
| PR-010 weakened | fresh implementation-entry reconciliation |

## 18. Explicitly Rejected Alternatives

Rejected:

- reading/mounting canonical checkout from AppContainer;
- source materialization by the verification script after SPAWN;
- allowing `package-lock.json` to be absent before profiled SPAWN;
- using Host PATH `npm.cmd`/`npm.ps1` as authoritative launcher;
- globally widening toolchain ACL;
- adding Node/npm to generic command allowlists;
- Internet/DNS fallback for npm;
- inheriting broker credentials;
- caller-supplied toolchain/source/cache/capsule Host paths;
- running npm outside scoped AppContainer;
- second executor/audit/scope authority;
- `operator_unrestricted` fallback;
- Hub modification;
- copying unmerged PR-007/PR-010 implementation into this branch.

## 19. Round-1 Finding Closure

### F1 — source-under-test materialization / pre-toolchain binding

Closed in Plan Revision 2 by Sections 4, 7, 8, 9, 15 Step B/C, 15 Step F and Test Matrix:

- exact repository/PR head/source manifest identity is sealed;
- source is broker-materialized before SPAWN;
- package-lock must exist and match before first process;
- downstream PR-015 proof is explicitly bound to exact PR head + `mcp/` bytes;
- post-run checks are tamper detection, not a substitute for pre-SPAWN truth.

### F2 — toolchain/capsule integrity / resource bounds

Closed in Plan Revision 2 by Sections 3, 5, 6, 9, 12 and Test Matrix:

- deterministic complete toolchain manifest/digest;
- exact Node + npm CLI execution through provider-generated launcher shims;
- request-time pre-START and pre-SPAWN integrity revalidation independent of readiness cache;
- concrete safe defaults + hard resource ceilings;
- bounded streaming copy + partial-copy cleanup and required negative tests.

## 20. Review Questions for Revision 2

Reviewer must re-evaluate the whole Plan, with particular attention to:

1. whether SourceUnderTestSnapshot is sufficiently narrow to preserve the Requirement's rule not to replace generic DevForge execution-workspace materialization semantics;
2. whether full readable-toolchain manifest + sealed workspace launcher prevents hash/launcher divergence;
3. whether pre-START + pre-SPAWN revalidation sufficiently closes cached-readiness/TOCTOU integrity risk;
4. whether the resource defaults/hard ceilings are safe and testable;
5. whether PR-007 remains correctly slice-local and PR-010 reconciliation remains fail-closed.

No Requirement semantic change is introduced by Revision 2. Plan approval remains reviewer-owned.