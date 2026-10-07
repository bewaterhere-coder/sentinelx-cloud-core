# PR-015 — Direct Codex Development Host Invocation Bridge V1 — Acceptance R5

## Decision

```yaml
task_id: PR-015-direct-codex-development-host-invocation-bridge-v1
requirement_revision: 2
plan_revision: 6
acceptance_revision: 5
result: Rejected
finding_classification: repair_local
canonical_transport: github-pr
pr_number: 15
canonical_branch: task/direct-codex-development-host-invocation-bridge-v1
evaluated_head_before_acceptance_artifacts: a974ffa3a84b79f1c09a7ec32fb2be6886d72633
verified_product_candidate: 02eb3de2ec9c137b3285398e555f1e037b574965
current_stage_before_transition: acceptance
target_stage: fixing
acceptance_approved: false
completion_verified: false
```

**PR-015 Acceptance R5: Rejected.**

The Host activation blocker is resolved: the exact PR-015 candidate is running as
`0.24.1.dev499+g02eb3de2e`, the explicit `direct_codex` Host policy is present,
and `local_api.list/describe` exposes the bounded `devforge_direct_codex`
provider/action with a closed schema.

Live readiness still reports `direct_codex_containment_unproven`. This is an
implementation-local lifecycle defect, not an external activation blocker.
The provider constructor initializes `_containment_proof = None`; the production
registry only creates the provider and projects `readiness()`; and
`execute_task` refuses execution while the proof is absent. The delivered
`prove_containment()` method has no production invocation path in the PR
candidate. Therefore the live provider cannot move from admitted-but-unproven
to verified-ready through the delivered product path.

## Acceptance Matrix

- **AC1 — PASS:** live `local_api.describe` exposes one bounded
  `devforge_direct_codex.execute_task` action with only repository, lineage,
  development and transport objects; no arbitrary executable/argv/shell/cwd/env/prompt.
- **AC2 — PASS:** the exact candidate fails closed while containment is unproven.
- **AC3 — PASS:** retained exact-candidate physical active-user Codex evidence.
- **AC4 — PASS:** canonical checkout read back `main + clean`, ahead/behind 0/0.
- **AC5 — PASS:** retained physical Windows MIC protected-sibling negative evidence.
- **AC6 — PASS:** retained transport-drift and exact-head negative evidence.
- **AC7 — PASS:** retained exact Requirement/Plan/Slice/transport lock evidence.
- **AC8 — PASS:** retained real fixture deterministic commit + ordinary FF push + remote readback + persisted receipt evidence.
- **AC9 — PASS:** retained fail-closed timeout/nonzero/malformed/local-only/transport-drift evidence.
- **AC10 — PASS:** retained focused/regression verification on the exact product candidate.
- **AC11 — PASS:** generic exec remains disabled; no operator_unrestricted, allowlist widening or Hub mutation.
- **AC12 — FAIL / REPAIR_LOCAL:** live end-to-end execution and PR-013 provider admission cannot occur because live containment readiness can never become verified through the delivered production lifecycle.

## Required Repair

Repair the current Plan R6 implementation without changing Requirement semantics,
Task identity, project binding or transport:

1. provide a provider-owned production lifecycle that actually executes and
   persists the physical containment proof before direct-Codex execution may be
   admitted;
2. do not expose a generic shell/path/prompt surface or caller-controlled
   containment operation;
3. keep readiness fail-closed until the proof is verified;
4. after repair, repeat live activation/readiness, one persisted direct/Codex
   execution, canonical `main + clean` readback and PR-013 provider-admission
   proof.

No new Requirement/architecture decision is required. The finding is bounded to
the implementation needed to make the already-approved containment contract
reachable in production.
