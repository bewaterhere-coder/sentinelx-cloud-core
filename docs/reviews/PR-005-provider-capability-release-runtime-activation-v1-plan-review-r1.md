# PR-005 — Plan Review r1

## Review State

```yaml
task_id: PR-005-provider-capability-release-runtime-activation-v1
transport: github-pr
pull_request: 5
reviewed_head: e7b487111f48545e7a6080a3b5a88f0a47c3a691
plan_ref: docs/plans/PR-005-provider-capability-release-runtime-activation-v1-plan.md
plan_blob: 74f60053c9e5dd4702b28e6db4d600606b33d051
plan_revision: 1
decision: Approved
blocking_findings: []
next_stage: implementation
next_expected_actor: implementer
execution_slice_set: docs/execution/PR-005-provider-capability-release-runtime-activation-v1-execution-slice-set.yaml
```

## Verdict

**Approved.**

The plan is implementation-ready. It preserves the requirement boundary that release, host installation, and runtime capability readiness are separate lifecycle states, and it does not bind release semantics to one host, version, install path, workspace path, or CI environment.

## Review Basis

The review checked solution direction, scope control, technical feasibility, risk handling, requirement traceability, implementation-shaping assumptions, and whether verification observes the required release/runtime behavior rather than a proxy.

### Material findings

1. **Release truth is coherent.** Tag/version input is validated against an exact source revision and built package metadata, while installed `AGENT_VERSION` remains package-metadata derived. Static source version is explicitly removed as release authority.
2. **CI is not semantic authority.** The host-local release executor owns build/verify semantics; GitHub Actions is optional orchestration only.
3. **Exact artifact consumption is observable.** The plan requires wheel build, digest/provenance manifest, isolated install smoke, and an exact-artifact upgrade path distinct from the moving `@main` development path.
4. **SX-HMSA readiness remains authoritative.** Package version alone cannot advertise `host_mutation_sandbox_v1` or `pre_execution_audit_lineage_v1`; policy plus real readiness remains fail-closed authority.
5. **Publication is not deployment.** Real network publication is separated from deterministic build/verify acceptance and does not auto-upgrade a connected host.
6. **No hard-coded deployment identity.** Host identity, version, install location, venv, workspace roots and protected-root inventory remain runtime/operator inputs, not product constants.

## Residual Implementation Risks — Non-blocking

- VCS-derived versioning must be proven on the actual Hatch build path and fail closed for tag/version/ref mismatch.
- The direct protocol dependency is currently pinned to a Git tag; exact SentinelX release installation must not regress into a moving `@main` source dependency.
- Publish idempotency/conflict handling must compare immutable release identity and artifact digests rather than silently overwrite same-version bytes.
- Windows readiness success must be demonstrated with dynamic host-resolved roots; non-Windows or failed prerequisites must remain unavailable.

Each risk has an explicit verification path in the Plan and does not require an upstream requirement/design change.

## Requirement / Plan Traceability

- R1 → tag/version/source-revision validation + package metadata read-back + manifest provenance.
- R2 → local build/verify executor + wheel + SHA-256 manifest.
- R3 → exact artifact install/upgrade path with `@main` retained only as compatibility/development mode.
- R4 → readiness-gated capability tests covering disabled, failed and successful Windows cases.
- R5 → static/dynamic no-hardcode verification.
- R6 → distinct build, publish, install and runtime-ready evidence states.

## Implementation-Ready Closure

Approval is coupled to the durable Execution Slice Set for plan revision 1. One explicit `#开发执行` may complete at most one slice. Real publication of a release remains a separately authorized external side effect and is not implicitly granted by this Plan Review.
