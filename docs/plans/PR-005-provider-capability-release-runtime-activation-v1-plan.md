# PR-005 — SentinelX Provider Capability Release & Runtime Activation V1 — Plan

## Status

```yaml
task_id: PR-005-provider-capability-release-runtime-activation-v1
plan_revision: 1
status: approved
base_revision: 732a8dbf292a798af55edbc0abbb2f2070a5a6f9
requirement: docs/requirements/PR-005-provider-capability-release-runtime-activation-v1.md
plan_review: docs/reviews/PR-005-provider-capability-release-runtime-activation-v1-plan-review-r1.md
execution_slice_set: docs/execution/PR-005-provider-capability-release-runtime-activation-v1-execution-slice-set.yaml
transport:
  type: github-pr
  pr_number: 5
  branch: task/provider-capability-release-runtime-activation-v1
```

## Current-State Findings

1. Canonical `main` already contains the SX-HMSA provider implementation and fail-closed runtime readiness probe.
2. `src/sentinelx_core/__init__.py` reports `AGENT_VERSION` from installed package metadata, so the runtime version can naturally follow wheel metadata rather than a machine constant.
3. `pyproject.toml` still contains the static package version `0.21.1`, while a currently connected host may run another version. Static source metadata is therefore not reliable release authority.
4. The fork currently has no GitHub Releases and no release workflow/tooling of its own.
5. The Windows update playbook currently installs from `git+https://...@main`, which is useful for source updates but is not an exact immutable release artifact.
6. SX-HMSA runtime activation is already correctly fail-closed: `capabilities` calls `probe_mutation_runtime`, which requires explicit valid `mutation_execution` policy and real Windows AppContainer/ACL/Job/audit/scope readiness before advertising the two capabilities.

## Architecture Decision

Use a **tag-derived package version + host-local release executor** as the canonical V1 release path.

The release boundary is:

```text
canonical source commit C
        ↓
release input/tag vX.Y.Z
        ↓
validate tag/version/HEAD relation
        ↓
build wheel from exact tagged source
        ↓
verify wheel metadata + install smoke + sha256
        ↓
write release manifest bound to C + vX.Y.Z + artifact digests
        ↓
optional publish adapter creates immutable GitHub Release/assets
        ↓
exact artifact can be installed/upgraded
        ↓
runtime policy + readiness probe decides capability availability
```

GitHub Actions may call the same executor later, but V1 release semantics must be executable locally and must not depend on CI availability.

## Planned Changes

### 1. Make package version release-derived

Change package version resolution from a permanently static `pyproject.toml` value to VCS/tag-derived build metadata.

Preferred mechanism:

- use Hatch/Hatch-VCS (or an equivalent build-time VCS version source) so tag `vX.Y.Z` resolves wheel version `X.Y.Z`;
- reject release builds where the requested/tag version and built wheel metadata disagree;
- preserve `AGENT_VERSION = importlib.metadata.version("sentinelx-cloud-core")` as runtime truth for the installed artifact;
- non-release development checkouts may resolve to a development version, but only an exact release tag is accepted by the release executor.

This removes the need to edit a fixed source version for every host or release.

### 2. Add one canonical host-local release executor

Add a repository-owned Python release tool, e.g. `tools/release.py`, with bounded commands such as:

```text
build   --version <X.Y.Z> [--ref <commit-or-tag>] [--output <dir>]
verify  --manifest <path>
publish --manifest <path> [--repository <owner/repo>] [--dry-run]
```

Exact CLI spelling may be adjusted during implementation, but the semantics are fixed:

- resolve repository root dynamically;
- require a clean release source tree or build from an isolated temporary checkout/archive;
- resolve exact source commit and tag;
- build into an output directory supplied/discovered at runtime;
- verify wheel filename/version and installed `AGENT_VERSION` in an isolated environment;
- compute SHA-256 for every publishable artifact;
- emit a machine-readable release manifest containing version, tag, source commit, artifact names/digests, build timestamp/tool version, and verification result;
- publish through GitHub using caller credentials/tooling without storing credentials in the repository;
- refuse overwrite/conflicting same-version publication unless the existing release is proven identical;
- support `--dry-run`/build-only operation for acceptance and air-gapped validation.

No hostname, host ID, venv path, installation path, workspace path, or release number may be embedded in this tool.

### 3. Produce an exact installable release asset

Build at minimum a wheel. If practical within the existing dependency model, also produce a small wheel bundle archive containing the agent wheel plus the pinned protocol dependency and any metadata required for offline/exact installation.

The manifest is authoritative for integrity/provenance; release asset naming is deterministic from version and platform-independent package identity.

Do not require PyPI.

### 4. Define exact-version install/upgrade consumption

Update Windows/operator documentation and the existing `update_sentinelx_code` playbook so two explicit modes are distinguished:

- **release mode (canonical for normal upgrade):** install an exact versioned wheel/bundle/release asset;
- **source mode (compatibility/development):** reinstall from an explicit source ref; `@main` may remain as an opt-in development path but is not proof of a versioned release.

Installation location is discovered from the running environment or supplied by the operator/installer. Documentation examples may show conventional paths, but code and release authority must not depend on them.

Publishing a release must never auto-upgrade a connected host.

### 5. Preserve and expose readiness-gated activation

Do not replace SX-HMSA readiness with a package-version gate.

Verify and, only where needed, tighten the existing flow:

```text
installed package contains provider code
        ↓
load host mutation_execution policy
        ↓
probe_mutation_runtime
        ↓
real prerequisite pass?
  ├─ no  -> capability available=false + reason/checks
  └─ yes -> advertise host_mutation_sandbox_v1
            + pre_execution_audit_lineage_v1
```

Activation inputs remain host configuration/runtime state. Example config may document portable discovery/selection rules, but must not bake in the current machine's paths.

### 6. Add release and activation verification

Add focused tests covering:

- tag/version -> package metadata agreement;
- source commit -> manifest provenance;
- deterministic artifact hashing;
- conflict/idempotency behavior for publish planning;
- isolated wheel install -> `AGENT_VERSION` read-back;
- no `@main` dependency in exact-release install path;
- static guard against fixed host/path/version authority in release tooling;
- mutation capability stays unavailable when policy/readiness fails;
- successful Windows readiness continues to advertise both features;
- Linux/macOS remain unavailable for the scoped mutation feature;
- existing SX-HMSA security/regression tests remain green.

Network publication itself should be separated from deterministic build/verify tests; publish can be adapter-tested with a fake/fixture and later proven with a real release receipt when explicitly authorized.

## Expected Files / Entry Points

Likely change surface:

```text
pyproject.toml
tools/release.py                      # new canonical local release executor
tests/test_release.py                 # build/version/manifest/publish-plan tests
tests/test_release_install.py         # isolated wheel install/version smoke
src/sentinelx_core/__init__.py        # expected to remain metadata-based; touch only if required
src/sentinelx_core/handlers/basic.py  # only if activation evidence shape needs tightening
src/sentinelx_core/mutation_readiness.py # preserve behavior; only targeted fixes if tests expose drift
config.example.windows.yaml
README.md
.github/workflows/release.yml          # optional thin adapter only; not semantic authority
```

Implementation must minimize the actual diff; files listed above are candidates, not mandatory edits.

## Validation Strategy

### Release build validation

1. Create an isolated release fixture at a synthetic tag/version.
2. Build the wheel through the canonical release executor.
3. Inspect wheel metadata and assert version agreement.
4. Install wheel into an isolated venv and assert `sentinelx_core.AGENT_VERSION` equals the release version.
5. Verify manifest source revision and SHA-256 against built bytes.
6. Verify a mismatched version/tag/ref fails closed.
7. Verify repeated identical release planning is idempotent and conflicting artifact identity is rejected.

### Runtime activation validation

1. Run existing mutation readiness/capabilities regression tests with policy absent/disabled: unavailable.
2. Run Windows readiness fixture with valid dynamic temp roots: both capabilities available.
3. Force one readiness prerequisite failure: both remain unavailable with reason/check evidence.
4. Confirm tests use dynamically allocated temporary roots and do not rely on the developer machine.

### Regression validation

Run the full relevant test suite, with special emphasis on:

```text
test_capabilities_*
test_mutation_*
test_scoped_script_execution.py
test_windows_mutation_sandbox.py
test_incident_20260927_d_root_recursive_delete.py
```

Platform-inapplicable security tests must be explicitly classified; skipped tests are not proof of Windows sandbox acceptance.

## Risks and Mitigations

### Risk 1 — VCS-derived version breaks source archives

**Mitigation:** release executor builds only from an exact VCS/tag context and verifies wheel metadata before publication. Document source-build limitations explicitly.

### Risk 2 — Release tooling accidentally becomes GitHub/CI-only

**Mitigation:** keep build/verify/publish semantics in a host-local Python tool. Any GitHub Actions workflow is only a thin adapter invoking the same tool.

### Risk 3 — Publishing is mistaken for deployment

**Mitigation:** manifest/receipt vocabulary separates `built`, `published`, `installed`, and `runtime_ready`; no host mutation occurs in publish.

### Risk 4 — New package version logic accidentally advertises capabilities

**Mitigation:** capability advertisement remains exclusively based on `probe_mutation_runtime`; add regression proving package version alone is insufficient.

### Risk 5 — Offline bundle scope expands the task

**Mitigation:** wheel is the mandatory V1 artifact. Bundle support is included only if it can reuse existing dependency packaging without changing installer architecture; otherwise document it as follow-up without blocking the core release path.

## Requirement Traceability

| Requirement | Plan coverage | Acceptance evidence |
|---|---|---|
| R1 | Steps 1–2 | version/ref/manifest + installed version read-back |
| R2 | Steps 2–3 | build + hash + manifest verification |
| R3 | Step 4 | exact artifact install fixture; no `@main` dependency |
| R4 | Step 5 | disabled/failure/success readiness capability tests |
| R5 | Steps 2,4,5 | static/dynamic no-hardcode checks |
| R6 | Steps 2,4,6 | distinct build/publish/install/readiness receipts/state |

## Plan Review Gate

Plan Review r1 is **Approved** for plan revision 1. Implementation is authorized only through the compiled Execution Slice Set; real release publication remains a separately authorized external side effect.
