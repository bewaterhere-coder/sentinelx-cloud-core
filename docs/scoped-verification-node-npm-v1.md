# Scoped Verification Node/npm V1

## Purpose

`host_runtime.scoped_verification_node_npm_v1` is a separately gated readiness signal for the provider-owned Node/npm verification environment. It neither replaces nor redefines `host_mutation_sandbox_v1`.

A Host with no Node/npm verification profile may still advertise the base scoped mutation sandbox as ready. The Node/npm feature remains unavailable until its own physical self-check passes.

## Operator configuration

Configure `mutation_execution.verification_profiles.<logical-id>` with provider-owned roots for:

- the immutable Node/npm toolchain;
- immutable source snapshots;
- immutable dependency capsules.

The source and capsule stores must already exist. Callers never provide Host paths, executable locations, cache roots, ACL targets, credentials, registry URLs, proxies, or network endpoints.

The example Windows configuration uses the logical profile `node_npm` and kind `node_npm_v1`.

## What readiness proves

The readiness probe first requires the base Windows AppContainer scoped runtime to be ready. It then validates the configured provider stores and computes the deterministic toolchain manifest.

The physical self-check reuses the same canonical profiled `script_run` executor used by real scoped verification. With a disposable provider-owned source/capsule fixture it proves all of the following inside a real Windows AppContainer:

1. `node --version` succeeds through the sealed workspace-local launcher;
2. `npm --version` succeeds through the sealed workspace-local launcher;
3. DNS is unavailable;
4. HTTP is unavailable;
5. provider-protected state is not readable;
6. the scope reaches terminal state;
7. transient toolchain AppContainer authority is revoked during terminalization.

The capability projection contains only bounded logical evidence: profile id, toolchain kind, toolchain digest, boolean checks, and a sanitized reason. It does not expose provider paths, credentials, package contents, or unrestricted environment data.

## Request-time integrity remains authoritative

Readiness is cached only as capability evidence. Every real verification request still independently loads and verifies its source snapshot, dependency capsule, package-lock digest, complete toolchain manifest, materialized source, launcher identity, and pre-SPAWN toolchain state.

After a successful readiness probe, its verified toolchain digest is additionally retained as a negative drift guard. If the configured toolchain changes afterward, the next request recomputes the manifest and fails admission before durable START rather than silently treating the replacement toolchain as the new trusted baseline.

Absence of cached readiness does not widen authority and does not substitute a cached digest for request-time validation.

## Interpreting an unavailable feature

`host_runtime.scoped_verification_node_npm_v1.available=false` can mean the profile is absent, a configured store is unavailable, the toolchain fails integrity validation, the base AppContainer runtime is unavailable, or the physical verification self-check failed.

Diagnostics are intentionally bounded. Inspect the operator-owned configuration and Agent logs locally when deeper path-specific diagnosis is required. Do not add caller-selected paths, network access, credential inheritance, `operator_unrestricted`, or a second executor to make readiness pass.

## Security invariants

- canonical repositories are never verification workspaces;
- AppContainer mutation authority remains confined to the exact execution workspace;
- the Host Node/npm toolchain receives transient read/execute authority only, never write authority;
- source/capsule stores remain provider-owned and are not made writable by the AppContainer;
- networking remains disabled; cache misses are verification failures, not a trigger for online fallback;
- Git, SSH, GitHub, npm credentials, proxy settings, and Host user-profile authority are not inherited;
- the existing Scope store, MutationAuditJournal, Windows sandbox, Job containment, and terminalization path remain the single authority chain.

## Physical verification

PR-011 S04 is not complete on mock-only evidence. The Windows verification workflow exercises the readiness and scoped-execution regressions on `windows-latest`, but GitHub Actions temp paths are not the Host-workspace acceptance receipt. Completion requires the same readiness probe to pass on the configured Windows Host under `D:\coco\workspaces`, with AppContainer/Job containment, no-network/protected-root checks, terminal cleanup readback, plus the relevant repository regressions.
