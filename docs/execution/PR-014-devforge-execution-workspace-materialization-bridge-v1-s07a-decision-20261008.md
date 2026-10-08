# PR-014 S07A — Read-only Security and Transport Decision

Task: `PR-014-devforge-execution-workspace-materialization-bridge-v1`
Command: `#开发执行 PR-014-devforge-execution-workspace-materialization-bridge-v1`
Requirement R8; Plan R14 (blob `d860b40805dd0cc0c96670fd84e7e4fea6deb487`).
Execution Slice Set: `003844b90006542dd00da18162faf51b4b79be6d`.
Canonical main: `2e5c69a112323867ee01783521554c43ebd731be`.
Original PR #14 head at admission: `8c7d1875d81df4a670909614030dae02c309961a`.

## G1 — Source and transport

GitHub readback confirms main owns:
- `src/sentinelx_core/handlers/devforge_runtime.py` @ `41373dce1784b112af71b2b680b2d07e8182aa2e`
- `src/sentinelx_core/handlers/direct_codex.py` @ `9fb4765bed432bf06a83fb50167e721a751c1ace`
- `src/sentinelx_core/canonical_repository_firewall.py` @ `9698bd1199b092edffcb15c69157c27150f78cea`
- `tests/test_canonical_repository_firewall_readiness.py` @ `6d8335538143ae328b077ff334b3da9cc8d5cc52`

Comparison at admission: PR #14 branch diverged from main (164 commits ahead, 717 behind); PR is not mergeable. Historic branch materializer and handler blobs are not the current-main product baseline. **TransportBlocked** for product changes: no currently proven same-PR lossless, CAS-verified normalization. Any later proposal must preserve every untouched current-main blob, original task/receipts and original PR identity, with preflight and post-write compare; abort on ref drift. No transport rewrite was attempted.

## G2 — Host reachability

Connected Windows Host: `0.24.1.dev791+g5d9286b22`.
Structured readback: `host_mutation_sandbox_v1.verified=true`, `pre_execution_audit_lineage_v1.verified=true`.
`canonical_repository_mutation_firewall_v1.verified=false`, reason `local_api:direct_codex_containment_unproven`.
`development_host.direct_codex_v1.verified=false`, reason `direct_codex_containment_unproven`.
Local API registers `devforge_direct_codex` with `execute_task` projected. Its describe-readiness is unavailable/unverified. Registration or readiness=false alone does not demonstrate negative action reachability or physical containment. No action invocation was attempted. **DecisionRequired/Blocked** for security authority; no owner-selected disablement or containment proof is established.

## G3 — Placement

Host effective locations report legacy `devforge_workspace_root`; no admitted independent `devforge_execution_workspace_root`. The registered `devforge_runtime` rev 1 has bounded scope lifecycle and `execute_scoped`, not `materialize_workspace`. A separate execution-root product need is not demonstrated by a real bounded consumer. Disposition: `NoAdditionalProductDeltaNeededForPlacement` for the current evidence, without prejudging future independently authorized needs.

## G4 — Result and restrictions

```yaml
slice: S07A
observation_result: read_only_evidence_collected
owner_decision: DecisionRequired/Blocked
transport: TransportBlocked
firewall: FAIL
direct_codex_containment: unverified
sandbox: PASS
audit: PASS
independent_execution_root: unverified
product_mutation_authorized: false
host_mutation_authorized: false
mrs01: HOLD
mrs02_admitted: false
```

This is a negative **owner admission** outcome, not proof of a successful security repair, a completed execution Slice, an acceptance decision or permission to resume old product implementation. No source/test/CI/Host mutation or historical Slice replay was performed. The S07A Run/Receipt and Task state must be independently persisted and reread before claiming Slice completion.
