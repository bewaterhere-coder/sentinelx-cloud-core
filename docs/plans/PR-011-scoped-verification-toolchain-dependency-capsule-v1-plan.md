# PR-011 — Scoped Verification Toolchain & Dependency Capsule V1 — Plan

## Plan State

```yaml
plan_revision: 1
task_id: PR-011-scoped-verification-toolchain-dependency-capsule-v1
requirement_revision: 1
status: proposed
review_state: pending
implementation_authorized: false
transport:
  type: github-pr
  pr_number: 11
  branch: task/scoped-verification-toolchain-dependency-capsule-v1
  base_branch: main
repository_baseline: f7e878f3497582547e5d52cd33b060cae18d2e84
```

## 1. Planning Decision

Implement V1 as a **provider-owned verification admission layer composed into the existing scoped executor**, not as a new command runner and not as a generic AppContainer mount/network feature.

The implementation will separate three concepts:

```text
VerificationProfile
  = provider policy describing a trusted toolchain and capsule store

DependencyCapsule
  = immutable integrity-bound offline dependency payload

VerificationAdmission
  = one operation's resolved profile + capsule + lockfile expectation
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
  - operator policy documentation
- `tests/test_scoped_script_execution.py`
- `tests/test_windows_mutation_sandbox.py`
- `tests/test_mutation_audit.py`
- `tests/test_release_activation_boundary.py`

Integration seam that is **not on main**:

- PR-007 `src/sentinelx_core/handlers/devforge_runtime.py`
  - builtin `devforge_runtime.execute_scoped`
  - dynamic `params_schema` through generic `sentinel_local_api`
  - adapter onto the existing profiled script handler.

No plan step may import that file from an unmerged branch as if it were baseline reality.

## 3. Configuration Model

Extend `MutationExecutionPolicy` with an optional immutable mapping of verification profiles. Existing hosts with no mapping remain behaviorally unchanged.

Proposed operator shape:

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
      capsule_root: D:\coco\sentinelx-verification-capsules\node-npm
      capsule_manifest_revision: 1
```

Rules:

1. profile key is the only caller-visible selection identifier;
2. all paths are operator policy, canonicalized at config load;
3. `node_relative` / `npm_cli_relative` must be relative, traversal-free and resolve inside `toolchain_root`;
4. toolchain/capsule roots must not overlap `workspace_root`, `protected_roots`, provider state/evidence roots, or Host canonical repository inventory when that capability is present;
5. verification roots are not appended to generic caller-controlled `runtime_read_roots` semantics;
6. no profile is inferred from PATH or installed programs;
7. profile parsing is additive and fail-closed per profile without breaking hosts that do not configure V1.

Introduce a dedicated module such as:

```text
src/sentinelx_core/verification_profile.py
```

so policy parsing, profile resolution, capsule validation and evidence shapes do not expand `scoped_script.py` into a second policy engine.

## 4. Node/npm Dependency Capsule Contract

Use a directory capsule with a canonical JSON manifest at its root:

```text
<capsule_root>/<capsule-id>/
  verification-capsule.json
  npm-cache/
    ... npm cache payload ...
```

Manifest V1 carries at least:

```json
{
  "schema_version": 1,
  "kind": "node_npm_dependency_capsule",
  "capsule_id": "...",
  "package_lock_sha256": "...",
  "payload_digest": "...",
  "files": [
    {"path": "npm-cache/...", "size": 123, "sha256": "..."}
  ]
}
```

Determinism/security rules:

- paths are normalized relative paths; absolute/traversal/reparse entries are forbidden;
- files are sorted by normalized relative path before canonical digest computation;
- every file size/hash is verified before materialization;
- `payload_digest` is the SHA-256 of canonical manifest file-entry data, not directory timestamps;
- capsule id is metadata, never a filesystem path supplied by the caller;
- provider resolves `<capsule-id>` under configured `capsule_root` and verifies final path containment;
- reparse points/symlinks inside capsule payload fail closed;
- unexpected files fail closed unless the manifest contract explicitly permits them;
- package-lock SHA-256 is mandatory for Node/npm V1.

A helper such as:

```text
tools/build-node-npm-verification-capsule.py
```

may prepare a capsule outside scoped execution. It is an operator/build utility, not a model-facing execution primitive. Scoped verification itself never downloads missing packages.

## 5. Verification Request / Admission Shape

Internally add an optional bounded verification request to the canonical scoped handler payload:

```yaml
verification:
  profile: node_npm
  capsule_id: <logical-id>
  package_lock_sha256: <64-hex>
```

It must reject additional path/network/executable/cache fields.

Resolution produces an immutable internal `VerificationAdmission` containing:

- profile id + contract revision;
- canonical provider-resolved toolchain root;
- resolved node/npm executable/script identities;
- toolchain provenance digest;
- canonical provider-resolved capsule root/member;
- capsule revision + payload digest;
- expected package-lock digest;
- offline/network mode = `none`;
- exact workspace-local cache destination.

`VerificationAdmission` is constructed before durable audit START. Caller fields are never consulted again for path authority.

## 6. Audit Binding

Add an optional bounded verification intent/evidence object to the existing START evidence rather than inventing another audit journal.

Proposed shape:

```yaml
verification_intent:
  profile_id: node_npm
  profile_revision: 1
  toolchain_kind: node_npm_v1
  toolchain_digest: <sha256>
  capsule_id: <id>
  capsule_revision: 1
  capsule_payload_digest: <sha256>
  expected_package_lock_sha256: <sha256>
  network_mode: none
```

The verification intent participates in the existing START evidence digest. Therefore profile/capsule/lockfile identity cannot change between durable START and SPAWN without failing audit identity checks.

No credential, raw Host path or package content is placed in the user-visible receipt.

## 7. Sandbox Authority Composition

Do not make Node/npm globally readable merely because the host has a profile.

For one operation with an admitted profile:

1. durable START is committed with verification intent;
2. existing sandbox activation establishes exact-workspace write ACL;
3. sandbox grants the AppContainer **read/execute only** to provider-resolved toolchain roots for that exact activation;
4. immutable capsule remains broker-readable/provider-owned; AppContainer does not receive write authority to it;
5. broker verifies and copies only the admitted capsule payload into:

```text
<exact-workspace>\.sentinelx-verification\npm-cache
```

6. copy verification re-hashes the workspace-local materialization before SPAWN;
7. existing AppContainer process starts suspended, is bound to the existing no-breakaway Job, SPAWN is durably recorded, then process resumes;
8. terminalization removes per-AppContainer toolchain read ACL together with the existing runtime-read cleanup path.

The sandbox activation API should accept an internal verified admission/read-root set, not caller paths.

## 8. Environment Composition

Create a verification-specific environment overlay on top of existing credential stripping.

For `node_npm_v1`:

- prepend the provider-resolved Node toolchain to `PATH`;
- set `NPM_CONFIG_CACHE` to the workspace-local materialized cache;
- force `NPM_CONFIG_OFFLINE=true`;
- disable audit/fund/update-notifier network-adjacent behavior for verification;
- set npm temp/log locations inside the exact workspace;
- remove inherited proxy/registry override variables and credential-bearing npm variables;
- reject caller `env` attempts to override verification-reserved keys.

At minimum reserve/filter:

```text
PATH
HTTP_PROXY / HTTPS_PROXY / ALL_PROXY / NO_PROXY
npm_config_proxy / npm_config_https_proxy
npm_config_registry
NPM_CONFIG_CACHE
NPM_CONFIG_OFFLINE
NODE_OPTIONS when it would inject external code
```

Existing non-profiled scoped execution keeps its current environment behavior except for fixes independently required by security tests.

## 9. Lockfile Verification

The expected lockfile digest is mandatory for a dependency capsule.

Resolution validates capsule manifest ↔ expected digest before START.

For the project workspace:

- when `<cwd>/package-lock.json` exists before SPAWN, hash and compare before process execution;
- after a successful process, hash it again before any successful verification result is emitted;
- if it was absent before SPAWN, it must exist after the verification script has materialized/prepared the package workspace and must match the expected digest;
- mismatch changes the operation to failed verification; no successful profiled receipt is returned.

`cwd` remains workspace-relative under the existing path guard.

## 10. Node/npm Execution Semantics

Do **not** add `node` as a new generic scoped interpreter in V1.

Reuse existing `python3` / `powershell` / `pwsh` root execution. The admitted profile makes `node`/`npm` available to descendants through provider-owned environment/toolchain ACL.

This preserves one executor and existing Job descendant containment while still allowing scripts such as:

```powershell
npm ci --offline
npm run typecheck
npm test
npm run check
```

The package manager cannot switch online when cache content is missing.

## 11. Readiness / Capability

Keep base `host_mutation_sandbox_v1` readiness independent.

Add a separate feature, for example:

```text
host_runtime.scoped_verification_node_npm_v1
```

Readiness is true only when a real Windows probe verifies at least:

- profile config resolves;
- Node/npm files exist and final-path validation passes;
- AppContainer gets read/execute and cannot write toolchain root;
- `node --version` and `npm --version` run inside exact workspace + existing Job;
- no broker credentials/user profile are inherited;
- terminalization removes transient ACL authority.

The profile capability may report capsule-store availability, but it must not claim that every lockfile has a capsule. Per-capsule admission remains request-time fail-closed.

## 12. `devforge_runtime` Integration Dependency

PR-007 is not part of the baseline. Therefore implementation is split:

### Core implementation — independent of PR-007

May modify baseline files/modules for:

- policy/profile model;
- capsule validation/materialization;
- audit binding;
- sandbox/environment integration;
- scoped-handler internal verification payload;
- readiness/capability/tests/docs.

### Builtin action integration — dependency gated

Only after exact PR-007/equivalent admission exists in the task branch ancestry may the plan modify `handlers/devforge_runtime.py`.

Then extend `execute_scoped` schema with only:

```yaml
verification:
  type: object
  required: [profile, capsule_id, package_lock_sha256]
  additionalProperties: false
```

The adapter passes this bounded object to the canonical scoped handler. No duplicate executor and no Hub change.

If PR-007 is still unmerged when the core slices are ready, stop before this integration step with an external dependency checkpoint rather than copying unmerged code into the Task branch silently.

## 13. PR-010 Overlap Reconciliation

PR-010 may modify `policy.py`, handler registration/effect metadata and readiness/capability surfaces before PR-011 implementation lands.

At each implementation entry:

1. re-read `main` and PR-010 state;
2. if PR-010 has merged, reconcile against its canonical-repository inventory/firewall primitives;
3. profile toolchain/capsule roots must never be classified as canonical repository write authority;
4. profiled execution must remain a process mutation covered by the existing scoped sandbox/firewall path;
5. no PR-010 file is copied from an unmerged branch without explicit dependency admission.

Overlap drift is a planning/execution reconciliation issue, not permission to weaken either security contract.

## 14. Implementation Sequence

### Step A — policy + pure contracts

Files expected:

- `src/sentinelx_core/policy.py`
- new `src/sentinelx_core/verification_profile.py`
- `config.example.windows.yaml`
- pure tests for parsing, path containment, capsule manifest and digest logic.

Exit evidence:

- legacy config matrix unchanged;
- profile/path/capsule negative cases fail closed;
- no AppContainer mutation yet.

### Step B — audit + sandbox + workspace preparation

Files expected:

- `src/sentinelx_core/mutation_audit.py`
- `src/sentinelx_core/windows_mutation_sandbox.py`
- verification-profile module/helpers
- Windows sandbox/audit tests.

Exit evidence:

- verification intent sealed at START;
- toolchain read/execute but no write;
- capsule copied only inside exact workspace and hash-verified;
- transient ACL removed on terminalization/failure;
- existing sandbox tests unchanged/pass.

### Step C — scoped execution + Node/npm verification

Files expected:

- `src/sentinelx_core/handlers/scoped_script.py`
- optional capsule builder utility
- scoped execution tests/Windows fixtures.

Exit evidence:

- real Node/npm commands execute in AppContainer;
- matching fixture lockfile + capsule completes offline install/check;
- cache miss/tamper/mismatch/network/credential override cases fail closed;
- npm descendants remain in existing Job.

### Step D — readiness/capability/docs

Files expected:

- new or existing readiness module
- `src/sentinelx_core/handlers/basic.py`
- README/config documentation
- activation/readiness tests.

Exit evidence:

- base sandbox readiness unaffected;
- Node/npm profile capability is separately readiness-gated;
- real Windows self-check receipt exists.

### Step E — dependency-gated `devforge_runtime` integration

Precondition: exact PR-007/equivalent admitted into repository ancestry or explicitly reconciled after merge.

Files expected only when precondition holds:

- `src/sentinelx_core/handlers/devforge_runtime.py`
- `tests/test_devforge_runtime_local_api.py`

Exit evidence:

- local_api `describe` exposes bounded verification object;
- live `execute_scoped` uses profile/capsule and returns bounded evidence;
- caller Host-path fields are schema/admission rejected;
- no Hub source/schema/deployment change.

### Step F — downstream unblock verification

After accepted Agent build activation and profile/capsule provisioning:

- resume ChatGPTControlShell PR-015 S01 from its latest checkpoint;
- do not replay S01 implementation;
- execute real `mcp npm run typecheck` and `mcp npm run check` through admitted scoped verification;
- preserve PR-015 as authority for its own Slice completion receipt.

This cross-repository run is Acceptance evidence for PR-011 AC12, not a mutation authorization for PR-015 outside its explicit command.

## 15. Test Matrix

### Pure/unit

- verification profile absent / valid / malformed;
- absolute/traversal relative toolchain members rejected;
- root overlap matrix;
- capsule final-path containment;
- manifest canonicalization and digest stability;
- symlink/reparse/unexpected-file rejection;
- lockfile digest validation;
- reserved environment key rejection;
- credential/proxy stripping.

### Scoped integration

- existing unprofiled Python succeeds unchanged;
- existing unprofiled PowerShell succeeds unchanged;
- node profile success;
- npm profile success;
- wrong profile/capsule/lockfile fails;
- missing cache stays offline and fails rather than networking;
- toolchain write attempt denied;
- capsule write attempt denied/not exposed;
- exact-workspace cache write succeeds;
- descendant process stays Job-contained;
- timeout/nonzero/activation failure cleans transient ACL and scope authority.

### Physical Windows

- `node --version` from AppContainer;
- `npm --version` from AppContainer;
- offline fixture `npm ci`;
- fixture package scripts;
- DNS/HTTP probe remains unavailable;
- canonical/protected path read/write negative probe;
- residual AppContainer/toolchain ACL absent after terminalization.

### Regression

- existing mutation policy tests;
- existing scoped-script tests;
- mutation readiness tests;
- Windows mutation sandbox tests;
- incident regression suite;
- full CI and macOS compatibility where relevant.

## 16. Risks and Controls

| Risk | Control |
|---|---|
| Toolchain ACL grants unintended write | dedicated read/execute ACL helper + write-negative physical test + cleanup readback |
| Capsule payload is tampered | per-file SHA-256 + canonical payload digest + no reparse points |
| Lockfile/capsule drift | manifest binding + pre/post workspace lockfile digest checks |
| npm silently networks | explicit offline env + proxy/registry sanitization + physical no-network negative test |
| Caller smuggles Host path | logical profile/capsule ids only + `additionalProperties:false` + provider final-path resolution |
| Credential leak | extend environment sanitization and reserved-key admission |
| Job descendant escape | reuse existing no-breakaway Job; lifecycle-script descendant regression |
| Audit loses profile identity | seal verification intent into existing START evidence digest |
| Base scoped runtime becomes unavailable | separate Node/npm readiness feature; legacy profile absence is compatible |
| PR-007 branch copied silently | dependency-gated integration step and exact revision readback |
| PR-010 overlap weakens firewall | fresh overlap reconciliation at implementation entry |
| Huge capsule copy cost | V1 correctness first; bound capsule size/file count and measure copy; optimization is separate unless required by acceptance |

## 17. Non-Goals / Explicitly Rejected Alternatives

Rejected:

- exposing `C:\Program Files\nodejs` by globally widening generic AppContainer ACL;
- adding Node/npm to generic command allowlists;
- enabling Internet/DNS for npm install;
- inheriting the broker's npm/Git credentials;
- accepting caller-supplied toolchain/cache/capsule paths;
- running npm outside the scoped AppContainer as a verification shortcut;
- creating a second executor specifically for Node;
- using `operator_unrestricted` as a fallback;
- making production Hub changes;
- copying PR-007 implementation into PR-011 before dependency admission.

## 18. Plan Review Questions

Reviewer must explicitly decide:

1. Is sealing `VerificationAdmission` into existing mutation START evidence sufficient, or is a separate durable verification journal required? Default plan answer: existing journal + bounded result evidence is sufficient and avoids duplicate authority.
2. Is immutable npm-cache capsule + workspace-local copy a valid V1 dependency source? Default: yes; it preserves offline execution and exact-workspace mutation authority.
3. Does post-run lockfile digest verification cover the case where package files are materialized inside the verification script? Default: yes for receipt truth, while pre-run verification is additionally required whenever the lockfile already exists.
4. Can core implementation proceed before PR-007 merge? Default: yes; only Step E/AC9 and downstream AC12 are dependency-gated.
5. Does the design preserve PR-010 canonical firewall semantics? Reviewer must inspect latest PR-010/main overlap before approval.

No unresolved product decision remains; these are technical review questions with fail-closed defaults.