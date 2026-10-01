# PR-005 — SentinelX Provider Capability Release & Runtime Activation V1 — Acceptance R1

## Decision

**Approved**

```yaml
task_id: PR-005-provider-capability-release-runtime-activation-v1
acceptance_revision: 1
decision: Approved
accepted_head: 0c33d6c46fe92161e58a0b65786fb9f97da28dd9
requirement: docs/requirements/PR-005-provider-capability-release-runtime-activation-v1.md
plan: docs/plans/PR-005-provider-capability-release-runtime-activation-v1-plan.md
execution_slice_set: docs/execution/PR-005-provider-capability-release-runtime-activation-v1-execution-slice-set.yaml
```

## Scope / Authority

Acceptance evaluates the approved V1 requirement and deterministic implementation evidence. Real GitHub Release publication, connected-Host package installation, and service restart are explicitly separate external side effects and are not required by the approved Plan Review for this acceptance pass.

## Acceptance Criteria

### A1 / R1 — PASS

Explicit version/ref and exact source commit produce release artifacts whose wheel metadata and installed `AGENT_VERSION` match the requested version. Manifest provenance binds the artifact to the exact source revision and SHA-256 digest. Tag/version/ref mismatch fails closed.

Evidence: S01 completion receipt `github-pr-comment:5933950162`; commits `370c1e7`, `076c559`, `56ef6d8`; focused result `6 passed`.

### A2 / R2 — PASS

A clean isolated environment builds an installable wheel, verifies metadata/install smoke, and records integrity/provenance without depending on CI.

Evidence: S01 release executor and isolated build/install verification.

### A3 / R2,R3 — PASS

Windows-compatible isolated install consumes the exact manifest-bound wheel. The canonical release-mode install plan does not resolve moving `@main`; source mode is explicitly compatibility/development only.

Evidence: S01 isolated install; S02 exact-artifact planning verification; commit `dcf6abe`; receipt `github-pr-comment:5934287234`.

### A4 / R4 — PASS

Disabled/unconfigured mutation policy keeps both `host_mutation_sandbox_v1` and `pre_execution_audit_lineage_v1` unavailable with fail-closed reason/check evidence.

Evidence: S03 activation-boundary suite; receipt `github-pr-comment:5934602805`.

### A5 / R4 — PASS

Valid Windows host-resolved readiness can advertise both capabilities only after real AppContainer/ACL/Job/audit/scope checks pass. Missing prerequisites remain unavailable with diagnostics.

Evidence: real Windows incident/readiness probe `2 passed in 168.24s`; S03 focused activation tests.

### A6 / R5 — PASS

Release/activation authority has no fixed host ID/hostname, release version, installation directory, mutation workspace, protected-root inventory, Python executable, or virtualenv path. Static/focused verification also excludes fixed `C:\ProgramData`, `D:\coco`, host identity and `@main` from canonical release authority.

Evidence: S02 focused verification.

### A7 / R6 — PASS

Documentation and tests explicitly separate:

```text
source_implemented
release_artifact_built
release_published
release_installed_on_host
runtime_capability_ready
```

No later state is inferred from an earlier one.

Evidence: README lifecycle contract + S03 lifecycle assertion.

### A8 — PASS

Relevant SX-HMSA regressions remain green. Core suite result: `32 passed, 1 skipped`; real Windows incident/readiness tests: `2 passed`.

The skipped case is platform/runtime conditional and is not used as Windows readiness proof.

### A9 — PASS

Operator documentation defines versioned release creation, exact-artifact install/upgrade, release-vs-source update modes, activation/readiness semantics, and the retained source-update compatibility path.

## Non-blocking observations

- `PytestConfigWarning: Unknown config option: asyncio_mode` appeared in release-focused runs; it did not affect the release tests and is outside this task's acceptance boundary.
- Linux-style `upload_base` literal-path assertions fail when executed unchanged on Windows; they are unrelated to mutation readiness and were not counted as S03 acceptance evidence.
- Local PR workspace may contain editor `.bak` files / CRLF worktree noise. Canonical remote content is the acceptance authority; these local artifacts are not committed.

## External side effects not performed

- No GitHub Release was published.
- No connected Host was upgraded from the release artifact.
- No SentinelX service was restarted as part of PR-005 implementation/acceptance.

Those actions require their own explicit authorization/receipt and do not change this V1 implementation acceptance decision.

## Result

All A1–A9 criteria are satisfied. There are no `repair_local` findings and no acceptance blocker.

PR-005 may transition from `acceptance` to `accepted`.
