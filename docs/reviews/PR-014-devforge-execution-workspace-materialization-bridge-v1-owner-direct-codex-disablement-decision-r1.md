# PR-014 Owner Decision R1 — Direct Codex Host-owned fail-closed disablement

## Decision (2026-10-08)
**Selected: Host-owned policy disablement.** The Owner rejects further SentinelX Runtime expansion or physical containment development for the unproven `devforge_direct_codex` long-Agent provider. The selected scope is **all SentinelX-exposed Direct Codex invocation surfaces**, not removal of the user's independent local CLI.

Authority: user Owner decision resolving Acceptance R3's first material choice. Applies to original PR #14 `task/devforge-execution-workspace-materialization-bridge-v1`. Requirement R8 already admits either fail-closed disabling or verified physical containment; this is a choice within that existing boundary, **not approval of a Host mutation**.

## Grounded current-main implementation
- Source owner main: `2e5c69a112323867ee01783521554c43ebd731be`.
- `src/sentinelx_core/policy.py` defines `DirectCodexPolicy.enabled` default false and a `direct_codex_disabled` admission reason.
- `src/sentinelx_core/handlers/direct_codex.py` gates `available_actions()`, `describe()`, and `call()` through policy admission.
- `src/sentinelx_core/handlers/__init__.py` builds Host policy-bound provider registration and dispatch.
- `src/sentinelx_core/handlers/local_api.py` resolves configured external `local_apis` names ahead of builtin names. **An external same-name alias or separate action must not survive as a mutating route.**
- Windows example `config.example.windows.yaml` documents `direct_codex.enabled: false`.

Live pre-decision Windows agent `0.24.1.dev791+g5d9286b22` still lists `devforge_direct_codex.execute_task` and firewall reports `local_api:direct_codex_containment_unproven`. These observations prove **no disablement has been applied or validated yet**.

## Binding safety contract for the separate DevForge implementation Task

1. **Policy-owned:** change only the effective Host-owned Direct Codex admission policy, initially preferring `direct_codex.enabled: false`. Do not disable the entire `local_api` operation (needed by bounded `devforge_runtime`); do not edit Host protected roots, allowlists, MutationScope/Audit, network/proxy, user runtime binaries, or DevForge execution binding.
2. **No alternate route:** enumerate builtin, externally configured same-name `local_apis`, MCP projection, Host action dispatcher, and any alias to `execute_task`. Absence from capability advertisements is not sufficient. All actual mutating routes must be rejected **before** process spawn, workspace creation, credential access, or filesystem write.
3. **Negative-reachability proof:** after independently approved Host config deployment and controlled service reload, read effective policy identity/digest; inspect `sentinel_local_api(list)`, `describe`, and an authorized *safety-guarded negative call* to the exact `devforge_direct_codex.execute_task` route. A valid-shaped call without pre-execution safety guard is not allowed. Capture refusal reason, audit trail, zero Codex child processes / zero new workspace or repository changes; verify no same-name external endpoint was routed.
4. **Preserve existing defenses:** sandbox/AppContainer/ACL/Job, pre-execution Audit, protected `D:\coco`, MutationScope, short `devforge_runtime` operation, and other unrelated `local_api` actions remain unchanged. Prove Firewall `verified=true` through genuine effective-surface accounting; never force a readiness flag.
5. **Rollback:** independently authorized Host owner retains known-good config backup and restart/read-back plan; fail closed on unexpected policy parsing, alternate-route discovery, or inability to verify negative reachability. No unsafe enabled fallback.
6. **Proof/receipt:** exact GitHub main source and targeted tests; before/after Host policy fingerprint, service/runtime identity, structured negative call evidence, audit / process / workspace non-mutation evidence, sandbox/audit baseline, transport/rollback receipts. **No Receipt, No Completion Claim.**
7. **Transport:** original PR #14 history and S01–S07A evidence must not be replayed/rebased/cherry-picked/force-pushed. Current PR #14 remains nonmergeable. No product change can borrow PR #14's stale tree as current-main code.

## Ownership and next Gate
PR-021 Capability Disposition Matrix V1 §13 rule 9 requires **a separate DevForge Task for every provider disablement**, with exact dependency/readback proof. This Owner decision must remain attached to PR #14; **the actual Host config/policy change and real negative tests belong to that separate formally registered Task**. DevForge allocates its Task/PR identity; do not invent a Task number or start implementation before Plan Review.

Original PR #14 retains `acceptance / DecisionRequired` and `MRS-01 HOLD` until independent proof is delivered, reconciled and separately accepted. Owner **choice** resolved; security **outcome** remains unverified.
