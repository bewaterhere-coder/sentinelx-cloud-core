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
  source_max_total_bytes: 2147483648
  source_max_files: 200000
  dependency_max_total_bytes: 4294967296
  dependency_max_files: 200000
  max_single_file_bytes: 1073741824
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

They invoke exactly provider-resolved `node.exe` plus provider-resolved `node_modules/npm/bin/npm-cli.js`.

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

Resolution produces immutable `VerificationAdmission` containing source identity, source manifest digest, toolchain manifest/digest, dependency capsule digest, expected lock digest, resource limits and offline mode.

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

## 8. Audit Binding

Use existing `MutationAuditJournal`; do not create a second verification journal.

Seal source repository/revision/manifest, toolchain digest, launcher digest, capsule digest, expected package-lock digest, network mode and limits digest into START evidence. Receipt projection exposes logical identities/digests only, never raw Host paths, credentials or package contents.

## 9. Pre-SPAWN Workspace Materialization — F1/F2

After durable START and exact sandbox workspace activation, but **before any root process is spawned**:

1. broker materializes source snapshot into `<exact-workspace>\source`;
2. broker re-hashes the complete source copy and proves it equals sealed source manifest digest;
3. broker requires `source\package-lock.json` and verifies its SHA-256;
4. broker materializes dependency capsule into `<exact-workspace>\.sentinelx-verification\npm-cache`;
5. broker re-hashes the cache against capsule manifest;
6. broker writes deterministic launcher shims and verifies their digest;
7. provider revalidates toolchain final paths + manifest digest a second time;
8. only then may `sandbox.spawn(...)` create the suspended root PowerShell/Python process.

`package-lock.json` may not be absent at SPAWN. No script may materialize or choose the package-under-test after process start. Any copy/hash/bounds failure removes partial reserved material and fails before SPAWN. Post-run source/lock checks remain tamper detection before successful receipt.

## 10. Environment Composition

For `node_npm_v1`:

- cwd remains beneath `<exact-workspace>\source`;
- prepend workspace-local provider-generated shim directory to PATH;
- do not use Host toolchain root as PATH launcher discovery;
- set workspace-local npm cache/temp/log/home/profile locations;
- force npm offline mode;
- remove proxy/registry and npm/Git/SSH/GitHub credential variables;
- reject overrides of reserved verification keys;
- reject `NODE_OPTIONS` external injection.

Existing non-profiled scoped execution remains unchanged.

## 11. Node/npm Execution Semantics

Reuse existing `python3` / `powershell` / `pwsh` root execution. Do not add Node as a generic interpreter.

Example:

```powershell
npm ci --offline
npm run typecheck
npm test
npm run check
```

Logical `npm` resolves only to the sealed workspace shim. Before successful projection, source/lock integrity, verification identities and terminal Scope closure are revalidated.

## 12. Readiness / Capability

Keep base `host_mutation_sandbox_v1` readiness independent. Add a separate Node/npm verification feature.

Readiness verifies config, toolchain manifest, final paths, read/execute-not-write ACL, sealed launcher execution, AppContainer Job containment, credential isolation and terminal ACL cleanup.

Readiness is preflight only. Every request independently revalidates source/capsule/toolchain integrity. Toolchain replacement after cached readiness therefore fails request admission.

## 13. `devforge_runtime` Integration Dependency

Core implementation remains independent of PR-007.

Only after exact PR-007/equivalent admission exists in repository ancestry may `handlers/devforge_runtime.py` be modified.

Extend `execute_scoped` with a bounded verification object containing only logical profile/source/capsule ids and integrity values. No Host paths, duplicate executor or Hub change.

If PR-007 remains unmerged when core slices finish, stop at an external dependency checkpoint before this integration slice.

## 14. PR-010 Overlap Reconciliation

At every implementation entry, re-read `main` and PR-010. If merged, consume its canonical inventory/firewall primitive. Verification stores never become canonical-repository write authority, profiled execution remains `process_mutation` through the scoped path, and no unmerged PR-010 code is copied.

## 15. Implementation Sequence

### Step A — policy + pure contracts

Implement profile parsing, resource limits, source/dependency manifests, toolchain manifest and request/admission schemas. Exit requires legacy config compatibility and fail-closed pure negative cases.

### Step B — audit + sandbox + pre-SPAWN materialization

Implement START sealing, exact source/cache/shim materialization, mandatory pre-SPAWN source/lock verification, read/execute-only toolchain ACL, second toolchain revalidation, bounded copy/cleanup and transient ACL cleanup.

### Step C — scoped execution + real Node/npm verification

Implement sealed launcher use, offline npm execution, post-run integrity projection, network/credential controls and physical Windows fixtures.

### Step D — readiness/capability/docs

Add separate Node/npm readiness and docs without changing base readiness.

### Step E — dependency-gated `devforge_runtime` integration

After exact PR-007/equivalent admission, project the bounded verification object through existing local_api and existing scoped executor.

### Step F — downstream AC12 proof

Under separate ChatGPTControlShell PR-015 authority:

1. resolve exact current PR-015 head SHA;
2. construct/read back source snapshot containing exact `mcp/` bytes from that head and bound to repo/PR/head/subpath;
3. admit matching dependency capsule from exact `mcp/package-lock.json` digest;
4. resume PR-015 S01 without replaying implementation;
5. materialize source/cache into fresh exact workspace and verify lock before SPAWN;
6. run real `npm run typecheck` and `npm run check` offline;
7. receipt identifies PR head, source manifest, lock, toolchain, capsule and audit/scope identity;
8. PR-015 remains sole authority for Slice completion.

## 16. Test Matrix

Required tests cover:

- profile/limit parsing and hard-ceiling rejection;
- toolchain manifest digest stability and tamper after readiness;
- source repository/revision/manifest mismatch;
- wrong lockfile before SPAWN;
- source/capsule bytes/file-count/per-file/path bounds;
- reparse/unexpected-file rejection;
- launcher substitution/PATH shadowing;
- reserved env and credential/proxy stripping;
- exact-workspace-only source/cache materialization;
- partial copy cleanup;
- offline cache miss;
- toolchain write denial;
- Job descendant containment;
- timeout/nonzero/activation cleanup;
- physical Windows node/npm versions, offline npm ci/scripts, no network, canonical path negative probes, and residual ACL absence;
- existing policy/scoped-script/readiness/sandbox/incident/full CI regressions.

## 17. Risks and Controls

| Risk | Control |
|---|---|
| Verification checks wrong source | source snapshot bound to exact transport head + pre-SPAWN manifest/lock verification |
| Script chooses source after start | broker materialization before SPAWN + post-run tamper check |
| Receipt hashes different npm launcher | full toolchain manifest + provider-generated sealed shim |
| Toolchain changes after readiness | pre-START and pre-SPAWN request-time revalidation |
| Capsule resource exhaustion | fixed defaults + hard ceilings + bounded copy + cleanup |
| Toolchain ACL grants write | read/execute ACL + physical negative test + closure readback |
| Source/capsule smuggles Host path | logical ids + provider roots + normalized manifests + final-path containment |
| npm silently networks | offline env + proxy/registry sanitization + no-network physical test |
| Credential leak | reserved/deny environment + isolated workspace profiles |
| Job escape | existing no-breakaway Job + descendant regression |
| Audit loses identity | source/toolchain/capsule/lock/limits sealed into START |
| Base runtime regresses | separate verification readiness |
| PR-007 copied silently | dependency-gated Step E |
| PR-010 weakened | fresh implementation-entry reconciliation |

## 18. Explicitly Rejected Alternatives

Rejected: canonical checkout mount/read from AppContainer; source creation after SPAWN; lockfile absence before SPAWN; Host PATH npm launcher; global toolchain ACL widening; Node/npm generic allowlist expansion; network fallback; broker credential inheritance; caller Host paths; npm outside AppContainer; second executor/audit/scope authority; `operator_unrestricted`; Hub mutation; silent copy of unmerged PR-007/PR-010 code.

## 19. Round-1 Finding Closure

### F1
Closed by exact SourceUnderTestSnapshot identity, broker pre-SPAWN source materialization, mandatory pre-SPAWN lock verification, exact PR-015 head binding and post-run tamper checks.

### F2
Closed by deterministic complete toolchain manifest, provider-generated sealed launchers, request-time pre-START + pre-SPAWN revalidation, explicit safe defaults/hard ceilings, bounded copy/cleanup and negative tests.

## 20. Review Questions for Revision 2

Reviewer must re-evaluate the whole Plan, especially whether the source snapshot remains verification-only rather than replacing generic workspace materialization, whether toolchain digest/launcher identity cannot diverge, whether TOCTOU is sufficiently closed, whether resource limits are safe/testable, and whether PR-007/PR-010 dependency boundaries remain fail-closed.

No Requirement semantic change is introduced. Plan approval remains reviewer-owned.