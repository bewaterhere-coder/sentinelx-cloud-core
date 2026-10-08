# Scoped Verification Toolchain & Dependency Capsule V1 — Provisional Bootstrap

```yaml
schema_version: 1
kind: devforge_provisional_task_bootstrap
project_id: sentinelx-cloud-core
repository: bewaterhere-coder/sentinelx-cloud-core
source_command: "#开发 Scoped Verification Toolchain & Dependency Capsule V1"
semantic_slug: scoped-verification-toolchain-dependency-capsule-v1
provisional_branch: task/scoped-verification-toolchain-dependency-capsule-v1
base_branch: main
base_sha: f7e878f3497582547e5d52cd33b060cae18d2e84
transport_identity_seed:
  type: github-pr
  pr_number: 11
canonical_task_id: PR-011-scoped-verification-toolchain-dependency-capsule-v1
identity_frozen: true
created_at: 2026-10-03T02:38:00+08:00
```

## Intent

Create a provider-owned scoped verification environment for Windows AppContainer execution so an admitted development Scope can use a policy-selected Node/npm toolchain and an integrity-bound offline dependency source without exposing the canonical repository, arbitrary host paths, credentials, or unrestricted network access.

This Task is motivated by the blocked ChatGPTControlShell PR-015 S01 verification window, but it owns only `sentinelx-cloud-core` provider capability. It does not mutate or redefine that downstream Task.

## Repository reality at allocation

- canonical `main` is `f7e878f3497582547e5d52cd33b060cae18d2e84` and was read back as clean on the connected Host;
- existing `MutationExecutionPolicy` already owns `workspace_root`, `protected_roots`, `runtime_read_roots` and fail-closed scoped mutation admission;
- existing Windows sandbox grants the AppContainer exact-workspace write authority and bounded `runtime_read_roots` read authority;
- the current `devforge_runtime` builtin action surface exists only on unmerged PR-007, not on `main`, so it is an explicit integration dependency rather than repository-main reality;
- production `mcp.sentinelx.app` is treated as an immutable external transport boundary.

## Allocation result

GitHub created Draft PR #11 for the provisional branch. Under the DevForge GitHub-PR transport contract, PR number `11` is the stable transport identity seed and the canonical Task ID is frozen as:

`PR-011-scoped-verification-toolchain-dependency-capsule-v1`

Canonical Requirement and Plan are persisted separately. This bootstrap grants no implementation authority.