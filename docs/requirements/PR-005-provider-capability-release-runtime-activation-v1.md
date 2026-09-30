# PR-005 — SentinelX Provider Capability Release & Runtime Activation V1

## State

```yaml
project_id: sentinelx-cloud-core
task_id: PR-005-provider-capability-release-runtime-activation-v1
title: SentinelX Provider Capability Release & Runtime Activation V1
development:
  stage: implementation
  gates:
    requirement_ready: true
    plan_approved: true
    acceptance_approved: false
    completion_verified: false
  next_expected_actor: implementer
transport:
  type: github-pr
  pr_number: 5
  branch: task/provider-capability-release-runtime-activation-v1
  base_branch: main
artifacts:
  plan: docs/plans/PR-005-provider-capability-release-runtime-activation-v1-plan.md
  approved_plan_blob: 74f60053c9e5dd4702b28e6db4d600606b33d051
  plan_review: docs/reviews/PR-005-provider-capability-release-runtime-activation-v1-plan-review-r1.md
  execution_slice_set: docs/execution/PR-005-provider-capability-release-runtime-activation-v1-execution-slice-set.yaml
related_tasks:
  - SX-HMSA-001
```

## Problem

`SX-HMSA-001` implemented `host_mutation_sandbox_v1` and `pre_execution_audit_lineage_v1`, but the canonical fork still has no versioned release artifact path of its own and `pyproject.toml` still reports `0.21.1`. A running agent can therefore remain on an older installed build after the provider code is merged.

The missing boundary is generic release + runtime activation, not another host-specific deployment patch.

## Goal

Make an exact canonical SentinelX revision publishable as an installable, versioned release without embedding a specific host, version number, install directory, mutation workspace, protected-root inventory, Python path, or machine identity in product code.

After installation, capability advertisement remains determined by the host's actual `mutation_execution` policy and real readiness probe. Publication never proves that any particular host upgraded or became runtime-ready.

## Required Behavior

### R1 — Versioned canonical release input

- Release version/ref is invocation/tag input, not host-specific source truth.
- Produced artifact reports the resolved release version through normal SentinelX package/runtime metadata.
- Release provenance binds the artifact to one exact canonical source revision.
- Same-version repeat is idempotent or rejects a conflicting artifact; it never silently replaces different bytes.

### R2 — Installable release artifact

- Produce at least one installable agent artifact plus integrity evidence.
- GitHub Release + wheel and/or wheel bundle is sufficient for V1; PyPI is not required.
- CI may invoke the path, but GitHub Actions/CI is not a semantic prerequisite: a host-local/manual release executor must be sufficient.

### R3 — Generic exact-version install/upgrade

- Windows can consume an exact released artifact/version rather than depending on `@main` as the only upgrade source.
- Installation/venv/service locations are discovered or supplied at execution time; no fixed hostname, `C:\ProgramData\SentinelX`, `D:\coco`, venv, or workspace path is canonical authority.
- Publishing a release does not silently mutate or upgrade a connected host.

### R4 — Readiness-gated runtime activation

Installing a capability-bearing release makes the provider implementation available, but availability remains fail-closed and runtime-derived:

- package version alone never enables `host_mutation_sandbox_v1` or `pre_execution_audit_lineage_v1`;
- missing/disabled policy, invalid roots, missing Windows sandbox prerequisites, audit/ACL/Job failure, or readiness-probe failure keeps both unavailable with diagnostic evidence;
- a host with valid host-resolved policy and passing readiness may advertise both capabilities;
- `pre_execution_audit_lineage_v1` remains bound to the same readiness boundary as `host_mutation_sandbox_v1`;
- Linux/macOS remain unavailable for scoped mutation in V1.

### R5 — No hard-coded deployment identity

Release/activation authority must not depend on a fixed host ID/hostname, release version, installation directory, mutation workspace root, protected-root inventory, Python executable, or virtualenv path. Portable defaults may exist only when overrideable/discoverable; host-specific roots remain host runtime/configuration state.

### R6 — Observable lifecycle boundaries

Evidence must distinguish:

```text
source_implemented
release_artifact_built
release_published
release_installed_on_host
runtime_capability_ready
```

Merged source is not released; released is not installed; installed is not runtime-ready.

## Compatibility / Non-Goals

- Preserve existing read-only/structured SentinelX behavior and SX-HMSA fail-closed readiness semantics.
- Source-based updating may remain as a compatibility/development path, but normal release documentation must support immutable exact artifacts.
- No automatic background updates.
- No `operator_unrestricted` fallback for scoped mutation.
- Do not hard-code or auto-enroll `Cherie_li` or any other host.
- Do not force all hosts to upgrade on publish.
- Do not enable scoped mutation by default without explicit valid policy.
- Do not add Linux/macOS scoped-mutation enforcement in V1.
- Do not require PyPI or CI.
- Do not redesign the accepted SX-HMSA sandbox/audit model.

## Requirement Readiness Evidence

```yaml
depth: deep
behavior_examples:
  - id: R1-example
    sequence: "Maintainer selects version V and canonical commit C -> release emits artifact A -> A reports V and release provenance binds A to C."
  - id: R3-example
    sequence: "Windows operator selects released version V -> upgrader installs the exact artifact -> runtime no longer depends on moving @main for that installation."
  - id: R4-example
    sequence: "Installed release contains SX-HMSA code, but mutation policy is disabled -> both capabilities remain unavailable; valid host-resolved policy plus successful readiness makes them available."
invariants:
  - release_version_is_input_not_machine_constant
  - release_artifact_is_bound_to_exact_source_revision
  - release_state_and_host_install_state_are_distinct
  - runtime_readiness_remains_capability_authority
  - no_host_or_workspace_identity_is_hardcoded
  - operator_unrestricted_is_never_scoped_mutation_fallback
  - no_ci_dependency_for_release_semantics
assumptions:
  - statement: "GitHub Release plus wheel/wheel-bundle is sufficient as the first canonical distribution channel."
    validation: "Build, integrity-check, and install an exact artifact without using @main."
  - statement: "Existing SX-HMSA runtime readiness remains activation authority rather than a version gate."
    validation: "Capability tests cover disabled policy, failed readiness, and successful Windows readiness."
material_questions: []
disconfirming_cases:
  - "A published artifact cannot be installed without resolving moving main."
  - "Changing release version requires editing host-specific source/path constants."
  - "Installed package advertises scoped mutation while readiness is unavailable or failing."
  - "Release success is represented as proof that a specific host upgraded."
challenge_completed: true
```

## Acceptance Criteria

- **A1 / R1:** explicit version/ref + canonical commit produce artifacts whose package/runtime version and provenance match, without host-specific source edits.
- **A2 / R2:** clean environment builds an installable artifact and verifies checksums/integrity without CI.
- **A3 / R2,R3:** Windows-compatible clean fixture installs/upgrades from the exact artifact/bundle without fetching `@main` as package source.
- **A4 / R4:** installed release with scoped mutation disabled/unconfigured reports both mutation features unavailable with reason/check evidence.
- **A5 / R4:** valid Windows host-resolved policy + real readiness can advertise both features; failing prerequisites stay fail-closed.
- **A6 / R5:** tests/static verification prove release/activation authority contains no fixed host ID/hostname, version, install path, or mutation workspace path.
- **A7 / R6:** release evidence separates build/publish/install/readiness states.
- **A8:** relevant SX-HMSA security/regression tests remain passing, including readiness advertisement behavior.
- **A9:** documentation defines versioned release, exact-artifact install/upgrade, activation/readiness semantics, and any retained source-update compatibility path.

## Regression Surface

- package version resolution (`pyproject.toml`, `AGENT_VERSION`, build metadata);
- release packaging/GitHub Release asset shape;
- Windows update/install documentation;
- `capabilities` execution feature reporting;
- `mutation_execution` policy and readiness probing;
- source-based update playbook;
- security boundary preventing false capability advertisement.
