# PR-007 — Host Mutation Scope Control Surface & MCP Admission Bridge V1 — Acceptance R3

## Decision

```yaml
task_id: PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1
requirement_revision: 2
plan_revision: 4
acceptance_revision: 3
result: Approved
canonical_transport: github-pr
pr_number: 7
canonical_branch: task/host-mutation-scope-control-surface-mcp-admission-bridge-v1
evaluated_head: c053d01f0ff5e1b65ff5b43f4ce511508f317580
current_stage: accepted
gate_transition: acceptance_to_accepted
acceptance_approved: true
completion_verified: false
```

**PR-007 Acceptance R3: Approved.**

Requirement Revision 2 is satisfied on the canonical PR transport. Acceptance R2's only blocking finding, `A10DocumentationContractDrift`, was repaired and independently verified. No merge/integration or `done` claim is made by this Acceptance decision.

## Runtime / Transport Consistency

PASS.

- DevForge Runtime source of truth: `bewaterhere-coder/DevForge main@e0fe219252b160ec35d7349bb1dc27c16227229a`.
- Acceptance Contract: `contracts/development/acceptance-contract.md` v1.5.
- Canonical repository: `bewaterhere-coder/sentinelx-cloud-core`.
- Canonical PR: #7.
- Canonical branch: `task/host-mutation-scope-control-surface-mcp-admission-bridge-v1`.
- Evaluated head: `c053d01f0ff5e1b65ff5b43f4ce511508f317580`.
- Canonical main remains `f7e878f3497582547e5d52cd33b060cae18d2e84`.
- No TransportDrift is present.

## Requirement Change Guard

PASS.

Requirement Revision 2's invalidation remains authoritative: S01-S04 are retained prerequisites, Plan Revision 4 is approved/current, and S05/Acceptance R1 remain historical Revision-1 evidence. Acceptance R2 is retained as a truthful rejected review whose sole blocking finding was repaired by the canonical repair checkpoint and transition receipt.

## Fresh Verification

### Canonical PR-head CI

PASS.

Current PR head `c053d01f0ff5e1b65ff5b43f4ce511508f317580` has:

- `ci` run `37040751232`: success;
- `macos-agent` run `37040751337`: success.

### A10 focused repair verification

PASS.

Repair checkpoint proves:

- product fix commit `aa215d7c6affb0b44dd581dc2a6a63966d08cbe5`;
- focused verifier run `37040107791`: success;
- Ruff focused checks: success, excluding only pre-existing unrelated `UP017`;
- focused pytest: `18 passed`;
- temporary verifier was removed;
- final product-equivalent head `cd7569774ce2cc405304e3ea3216966439b5ac37` has zero file differences from the product fix commit;
- final repair CI/macOS runs passed.

### Live runtime freshness

PASS.

Acceptance-time readback shows:

- Agent version `0.24.1.dev70+gf11491fd4`, matching exact S08 product candidate `f11491fd48199f2dbe958f4dcd54caf1d39d9c5a`;
- `local_api` remains in `ops_supported`;
- `host_mutation_sandbox_v1` remains `available=true, verified=true`;
- `pre_execution_audit_lineage_v1` remains `available=true, verified=true`;
- `disabled_ops` remains empty;
- `sentinel_local_api list` still exposes only builtin `devforge_runtime` contract revision 1;
- `describe` still exposes exactly five bounded actions: `provision_scope`, `revalidate_scope`, `inspect_scope`, `terminalize_scope`, `execute_scoped`.

Comparison from live S08 candidate `f11491f...` to current PR head shows no changes to `devforge_runtime`, mutation scope lifecycle, scoped executor, sandbox, store, audit or Job execution code. Post-S08 product-code changes are limited to Help/operator guidance and focused tests; therefore the already terminal S08 side-effect evidence is reused and not replayed.

## Acceptance Matrix

- **A1 / R1 — PASS:** provider-owned `MutationScopeStore` remains the single lifecycle authority; no duplicate scope ledger exists.
- **A2 / R2,R4 — PASS:** bounded provider-issued scope/generation/workspace identity and same-Attempt idempotency remain covered by retained S06 evidence.
- **A3 / R2,R3 — PASS:** caller authority fields and repository/lineage/generation mismatches fail closed; S08 observed `HostMutationScopeBindingMismatch` live.
- **A4 / R3,R6 — PASS:** exact revalidation and runtime readiness remain fail closed; current sandbox/audit self-checks remain verified.
- **A5 / R5 — PASS:** S08 execution and exact inspect both proved terminal scope state; no reactivation path was observed or introduced later.
- **A6 / R7,R8 — PASS:** `execute_scoped` still composes the existing scoped script/AppContainer/audit/Job path with no duplicate executor or unrestricted fallback; no relevant execution code changed after S08.
- **A7 / R9,R10,R11 — PASS:** real model-facing S08 evidence proved `list -> describe -> provision_scope -> execute_scoped -> inspect_scope terminal`; Acceptance-time list/describe and readiness readback reconfirm the same exact live contract without replaying mutation.
- **A8 / R10,R13 — PASS:** older Agent evidence remains fail-closed and focused coverage preserves configured external `local_apis` plus deterministic name-collision behavior.
- **A9 — PASS:** retained scope/AppContainer/audit/terminal/security regression evidence remains valid; current head CI/macOS are green.
- **A10 / R11,R12 — PASS:** README/Help/operator guidance now reflects immutable Hub + `sentinel_local_api -> builtin devforge_runtime`, with applicability/collision tests and bounded non-secret evidence. Acceptance R2's sole blocker is closed.
- **A11 / R13 — PASS:** legacy/public operations remain compatible and capability remains Host-specific.
- **A12 — PASS:** canonical Task transport contains S06/S07 focused evidence, S08 live evidence, A10 focused verifier evidence, and fresh current-head CI/macOS success; S01-S04 were retained, not replayed.
- **A13 / R14 — PASS:** no fixed host/path/version/user/credential identity is part of the authority model; runtime identities remain evidence only.
- **A14 / R15 — PASS:** PR-008 and PR-009 remain non-blocking; PR-007 completes through the existing Hub `sentinel_local_api` envelope.

## Acceptance Result

```text
Acceptance Approved: true
Completion Verified: false
Result: Approved
Gate Transition: acceptance -> accepted
Current Stage: accepted
```

Per Acceptance Contract v1.5, Approval enters the `accepted` boundary only. Merge/integration and the final `done` claim remain gated by `#开发完成 PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1`.
