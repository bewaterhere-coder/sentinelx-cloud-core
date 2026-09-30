# PR-005 — SentinelX Provider Capability Release & Runtime Activation V1

## State

```yaml
project_id: sentinelx-cloud-core
task_id: PR-005-provider-capability-release-runtime-activation-v1
title: SentinelX Provider Capability Release & Runtime Activation V1
development:
  stage: planning
  gates:
    requirement_ready: true
    plan_approved: false
    acceptance_approved: false
    completion_verified: false
  next_expected_actor: orchestration
transport:
  type: github-pr
  pr_number: 5
  branch: task/provider-capability-release-runtime-activation-v1
  base_branch: main
artifacts:
  plan: docs/plans/PR-005-provider-capability-release-runtime-activation-v1-plan.md
related_tasks:
  - SX-HMSA-001
```

## Problem

`SX-HMSA-001` implemented the provider-side security capabilities `host_mutation_sandbox_v1` and `pre_execution_audit_lineage_v1`, but the canonical SentinelX fork currently has no versioned release artifact path of its own and its package metadata still reports `0.21.1`. A running Windows agent can therefore remain on an older installed build even though the capability implementation is already merged.

The missing boundary is not another host-specific deployment patch. SentinelX needs a generic release and activation path so a capability-bearing canonical revision can be packaged, published, installed, and then truthfully activated according to the target host's runtime readiness.

## Goal

Provide a reusable SentinelX release boundary that can publish an exact canonical source revision as an installable versioned release without embedding a specific host, version number, installation path, workspace path, or machine identity in product code.

After a released build is installed, runtime capability advertisement must continue to be determined by the host's actual `mutation_execution` policy and readiness probe. Publication must not imply that a particular host has upgraded or that scoped mutation is ready.

## Required Behavior

### R1 — Versioned canonical release input

A release invocation accepts a release version/ref as input and binds the produced artifacts to one exact canonical source revision.

- The release version is supplied by the release invocation/tag/request; it is not hard-coded into host-specific logic.
- The artifact exposes the same resolved version through SentinelX runtime version reporting.
- Source revision and artifact identity are recoverable from release metadata/manifest or equivalent provenance.
- Re-running the same release input must either be idempotent or fail clearly on an existing conflicting release; it must not silently replace a different artifact.

### R2 — Installable release artifact

The release path produces at least one installable SentinelX agent artifact from the canonical repository, plus integrity evidence sufficient to verify what was built.

A GitHub Release with a Python wheel and/or wheel bundle is an acceptable V1 distribution channel. PyPI publication is not required.

The release path must be usable without GitHub Actions/CI being a semantic prerequisite. CI may validate the same path, but a host-local/manual release executor must be sufficient.

### R3 — Generic install/upgrade consumption

A Windows installation can consume an exact released artifact/version rather than requiring `@main` as the only upgrade source.

The mechanism must not assume a specific hostname, `C:\ProgramData\SentinelX`, `D:\coco`, a fixed virtualenv, or any other machine-specific path as canonical product truth. Existing installer/configured installation locations may be discovered or supplied at execution time.

The release mechanism must not silently mutate a host as part of package publication. Release availability and host upgrade state are separate facts.

### R4 — Readiness-gated runtime activation

Installing the capability-bearing release makes the provider implementation available, but capability advertisement remains fail-closed and runtime-derived.

For `host_mutation_sandbox_v1` and `pre_execution_audit_lineage_v1`:

- capability availability is computed from real runtime readiness, not the package version alone;
- missing/disabled `mutation_execution` policy, invalid roots, missing Windows sandbox prerequisites, audit failure, ACL/Job failure, or readiness-probe failure keep the capability unavailable with diagnostic evidence;
- a host with valid host-resolved policy and passing readiness advertises both capabilities;
- `pre_execution_audit_lineage_v1` remains bound to the same verified readiness boundary as `host_mutation_sandbox_v1`;
- Linux/macOS do not gain false scoped-mutation availability in V1.

### R5 — No hard-coded deployment identity

The implementation must not embed any of the following as release/activation authority:

- a specific SentinelX host ID or hostname;
- the current development machine;
- a fixed release version;
- a fixed installation directory;
- a fixed mutation workspace root;
- a fixed protected-root inventory;
- a fixed Python executable or virtualenv path.

Defaults may exist only when they are portable platform defaults and remain overrideable/discoverable. Host-specific roots and policy remain host configuration/runtime state.

### R6 — Release/activation observability

The system exposes enough evidence to distinguish these states:

```text
source_implemented
release_artifact_built
release_published
release_installed_on_host
runtime_capability_ready
```

No state may be inferred from a later state that has not been verified. In particular:

- merged source does not mean released;
- released does not mean installed on a host;
- installed does not mean readiness passed;
- package version does not authorize capability advertisement.

## Compatibility

- Preserve existing SentinelX read-only and structured operation behavior.
- Preserve the existing fail-closed mutation readiness probe introduced by `SX-HMSA-001`.
- Existing installs that continue to update from source may remain supported for compatibility, but the documented/canonical release path must support exact versioned artifacts.
- Do not introduce automatic background updates.
- Do not make `operator_unrestricted` a fallback for scoped mutation.

## Non-Goals

- Hard-coding or auto-enrolling the current `Cherie_li` host.
- Forcing every connected host to upgrade when a release is published.
- Making scoped mutation enabled by default on hosts lacking an explicit valid policy.
- Adding Linux/macOS scoped-mutation enforcement in V1.
- Replacing the SentinelX hub.
- Requiring PyPI as the release channel.
- Requiring GitHub Actions/CI for release completion.
- Redesigning the already accepted SX-HMSA-001 sandbox/audit semantics.

## Requirement Readiness Evidence

```yaml
depth: deep
behavior_examples:
  - id: R1-example
    sequence: "Maintainer selects version V and canonical commit C -> release build emits artifact A -> A reports V and provenance binds A to C."
  - id: R3-example
    sequence: "A Windows operator selects released version V -> installer/upgrader consumes the exact release artifact -> SentinelX restarts from that installed build without depending on @main."
  - id: R4-example
    sequence: "Installed release contains SX-HMSA provider code, but mutation policy is disabled -> capabilities reports both mutation features unavailable; enabling valid host-resolved policy and passing the readiness probe makes them available."
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
    validation: "Build, integrity-check, and install the artifact from an exact release fixture without using @main."
  - statement: "Existing SX-HMSA runtime readiness is the correct activation authority and should be reused rather than replaced by a version gate."
    validation: "Capability tests cover disabled policy, failed readiness, and successful Windows readiness paths."
material_questions: []
disconfirming_cases:
  - "A published artifact cannot be installed without resolving the moving main branch."
  - "Changing the release version requires editing a host-specific path or source constant outside the release input."
  - "An installed capability-bearing package advertises scoped mutation while the readiness probe is unavailable or failing."
  - "Release success is reported as proof that a particular host upgraded."
challenge_completed: true
```

## Acceptance Criteria

- **A1 / R1:** Given an explicit release version/ref and canonical source commit, the release build produces artifacts whose runtime package version and provenance match those inputs; no host-specific source edit is required.
- **A2 / R2:** A clean environment can build the versioned installable artifact and verify its checksum/integrity metadata without requiring CI.
- **A3 / R2,R3:** A clean Windows-compatible installation fixture can install/upgrade from the exact produced release artifact or bundle without fetching `@main` as the package source.
- **A4 / R4:** With the released package installed but scoped mutation disabled/unconfigured, runtime capability evidence remains unavailable and explains why.
- **A5 / R4:** With valid Windows host-resolved mutation policy and real readiness prerequisites, the runtime probe can advertise both `host_mutation_sandbox_v1` and `pre_execution_audit_lineage_v1`; failing prerequisites remain fail-closed.
- **A6 / R5:** Tests or static verification prove release/activation code contains no dependency on a fixed host ID/hostname, fixed version, fixed installation path, or fixed mutation workspace path.
- **A7 / R6:** Release evidence distinguishes build/publish state from host-install/runtime-readiness state and never treats one as proof of another.
- **A8:** Existing relevant SX-HMSA regression/security tests remain passing, including readiness advertisement behavior.
- **A9:** Documentation defines the versioned release path, exact-artifact install/upgrade path, activation/readiness semantics, and the continued optional `@main` compatibility path if retained.

## Regression Surface

- package version resolution (`pyproject.toml`, `AGENT_VERSION`, build metadata);
- release packaging and GitHub Release artifact shape;
- Windows install/update documentation and bundle consumption;
- `capabilities` execution feature reporting;
- `mutation_execution` policy parsing and readiness probing;
- existing source-based update playbook;
- security boundary preventing false capability advertisement.
