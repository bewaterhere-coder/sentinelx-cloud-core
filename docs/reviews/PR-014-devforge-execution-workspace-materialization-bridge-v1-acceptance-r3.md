# PR-014 — Acceptance R3 (Requirement R8 / Plan R14)

Decision: **DecisionRequired** — S07A's read-only evidence is verified, but full Requirement R8 security/transport closure and product acceptance are **not** established. The current Task remains at `acceptance`; no `accepted`, `fixing`, merge or release transition.

## Exact lineage

- Task: `PR-014-devforge-execution-workspace-materialization-bridge-v1`; original PR #14 / `task/devforge-execution-workspace-materialization-bridge-v1`.
- Canonical `main@2e5c69a112323867ee01783521554c43ebd731be`, PR branch at pre-review `f64a04cc7b7a6b29a7a6cb76438399246031fbd7`.
- Requirement R8, current Task blob `ceebd677409ff10c08801b7ff6c1339e71b7a6b4`.
- Plan R14 blob `d860b40805dd0cc0c96670fd84e7e4fea6deb487`, review R14 `14267d1c718ef9eed71372199caa5eab996328d7`.
- S07A Slice Set `c9a0589e8ac89023a77f967b55290bd6cb060b14` (`completed`), Completion Receipt `7fd755c276826b830133c982d71635fcf35e059a`, Run Finalization `226b20f6c3d14b3b280e2d964e40184ed7232b2c`.
- Current DevForge main `ebc25425160790950bd4d4500186652d3bf52416`; Acceptance Contract v1.5 and Artifact-State Transition Resolver v1.1.

## Verification matrix

| Criterion | Result | Basis |
|---|---|---|
| Canonical Task/PR and R14 Plan identity | PASS | exact GitHub refs, unchanged original PR #14 |
| Approved S07A bounded read-only investigation | PASS | decision `docs/execution/PR-014-devforge-execution-workspace-materialization-bridge-v1-s07a-decision-20261008.md`, Run/Attempt/Ledger/Finalization and Completion Receipt |
| Historical S01–S06A preservation and no replay | PASS for S07A scope | current Slice Set and docs-only commit path |
| Current-main source ownership evidence | PASS | current source/test file blobs grounded by GitHub main |
| Sandbox/AppContainer/Audit readiness | PASS | live Windows Host `0.24.1.dev791+g5d9286b22`, sandbox and audit both verified |
| Canonical Firewall / Direct Codex | **FAIL / Unverified** | firewall `verified=false`, `local_api:direct_codex_containment_unproven`; projected `execute_task` cannot serve as a physical or negative-reachability proof |
| No-loss original PR #14 product transport | **TransportBlocked** | `main` vs PR #14 diverged, at acceptance comparison ahead 173 / behind 717; PR nonmergeable. No reviewed no-loss normalization |
| Independent execution root | **Not Admitted** | only `D:\coco` legacy root is evidenced; no demonstrated bounded short-mutation consumer requiring new root |
| Required physical Firewall and negative reachability proof (Requirement R8 A/D) | **NOT SATISFIED** | cannot treat missing physical test as PASS; `execute_task` was not invoked |
| Product implementation / physical integration tests | **NOT APPLICABLE to evidence-only R14, NOT PROVED for Requirement R8** | no product code, CI, Host config, policy or deployment mutation authorized or executed |
| Merge / Task completion | **NOT ELIGIBLE** | original PR nonmergeable, owner security and transport gates unresolved |

## Decision

Plan R14 intentionally permits a negative `DecisionRequired/Blocked` outcome from its *evidence-only* S07A. That outcome is a valid, verified **investigation deliverable** but not positive satisfaction of R8's security closure requirements. Acceptance v1.5 requires full requirement satisfaction before `Approved`. The remaining decision is material/owner-held rather than an authorized in-plan code fix.

This Acceptance therefore returns **DecisionRequired**, not `Approved` and not an automatically executable `Rejected -> fixing` transition. No Acceptance gate transition is applied.

### Required Owner decisions / prerequisites

1. Select an independently authorized Direct Codex disposition under PR-021: enforce truly unreachable mutating action through fail-closed Host policy with a real negative reachability check, **or** prove physical AppContainer/Job/ACL/audit/canonical firewall containment. Neither was proved here; do not pick by guess.
2. If product changes remain necessary, establish no-loss existing PR #14 transport against exact current-main source paths and blob identities with abort-on-drift and remote readback. No rebase/cherry-pick/force-push or another PR is authorized.
3. Admit a separate short-mutation execution root only after proving an actual bounded consumer need; keep `D:\coco` protected.

## Guarded state

```yaml
acceptance_decision: DecisionRequired
stage: acceptance
acceptance_approved: false
completion_verified: false
formal_review_round: R3
readonly_slice_delivery: verified
material_owner_decision_pending: true
physical_firewall: FAIL
product_transport: TransportBlocked
product_mutation_authorized: false
host_mutation_authorized: false
historical_replay_authorized: false
mrs01: HOLD
mrs02_admitted: false
```

Recommended owner action: resolve the narrow Direct Codex authority boundary as a **Requirement/Plan owner decision**, on existing PR #14, before authorizing a separate product repair or another Acceptance. Do not issue `#开发完成`, `#开发执行` for stale implementation, or blindly rerun acceptance.
