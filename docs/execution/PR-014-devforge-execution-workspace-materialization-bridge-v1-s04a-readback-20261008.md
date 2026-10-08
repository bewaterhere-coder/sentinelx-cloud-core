# PR-014 — S04A Source and Host Readback (2026-10-08)

## Scope and identity
Requirement R5, Approved Plan R10, S04A read-only. Existing PR #14 only. Main SHA `cd42e371f18056327c1d8b744f8956a76bc11541`; existing branch 125 commits ahead, 598 behind, merge base `e7064c9bf4fcd15bdb6f5a2678414210c01d1c00`. Canonical main lacks historical source files `src/sentinelx_core/policy.py`, `mutation_scope.py`, `handlers/devforge_runtime.py` and `pyproject.toml` per S03A; authoritative current-main product source tree remains unproven.

## Live Host structured readback
- Host: `Cherie_li`, operational Windows, installed agent `0.24.1.dev260+g45dc99d15`, current Host capability FULL readback.
- Local API `devforge_runtime` builtin contract revision 2 exposes `provision_scope`, `revalidate_scope`, `inspect_scope`, `terminalize_scope`, `execute_scoped`, `materialize_workspace`. These are API projections, not proof that writes work.
- Effective locations: `devforge_workspace_root: D:\coco` and `config: C:\ProgramData\SentinelX\config.yaml`. Dedicated `locations.devforge_execution_workspace_root` **absent** in readback; no validated safe independently bound DevForge execution root.
- Effective full capability self-check: `host_mutation_sandbox_v1`: `available=false, verified=false`; `pre_execution_audit_lineage_v1`: `available=false, verified=false`. Both explain `HostMutationScopeCorrupt: invalid scope record: MutationScopeRecord.__init__() got an unexpected keyword argument 'runtime_read_authority_roots'`.
- `canonical_repository_mutation_firewall_v1`: `available=true, verified=true`, inventory/effective surface ready.
- File-ops policy grants `D:\coco` rw generally, but this must NOT be treated as authorization to bypass protected-root/scope/audit controls.
- Installed package provenance is identified by version/candidate prefix only; no proof this version maps to present GitHub main. The S02 candidate prefix corresponds to `45dc99d`, but code equality/source ownership are not inferred.
- `execute_scoped` closed short-mutation API is present; no actual allowed consumer or verified successful safe invocation is established. Do not call it with broken sandbox/audit readiness.

## Decision matrix
| Question | Verdict |
|---|---|
| Canonical source ownership | Unverified / Blocked |
| Real bounded execute_scoped API | Yes, projected only |
| Sandbox + audit readiness | FAIL, durable MutationScope additive-field incompatibility |
| Independent safe DevForge root | Unproven, dedicated location absent |
| Need for new product implementation | Cannot adjudicate safely |
| Safe legacy materialization / old branch promotion | Forbidden |

```yaml
outcome: DecisionRequired/Blocked
primary_reason: RuntimeSecurityReadinessFailureAndCanonicalSourceUnresolved
blocking_facts:
  - HostMutationScopeCorruptRuntimeReadAuthorityRoots
  - MissingIndependentDevForgeExecutionRootBinding
  - CanonicalMainImplementationSurfaceMismatch
product_mutation_authorized: false
host_mutation_authorized: false
canonical_main_mutation_authorized: false
long_agent_lifecycle_authorized: false
```

## Required next disposition
A separate reviewed root-cause/security repair path must first reestablish current canonical product source ownership and installed-runtime provenance; repair durable MutationScope schema reader **without deleting state or widening authority**, admit separate Host-owned execution root outside `D:\coco`, and re-prove sandbox/audit/firewall controls. No product writes under S04A, no rebase or restore, no historical S01/S02 replay. R5 product completion is NOT claimed.
