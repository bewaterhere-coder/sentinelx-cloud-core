# PR-008 — Provider Execution Profile Tool Surface Alignment V1 — Acceptance Review R1

## Decision

```yaml
task_id: PR-008-provider-execution-profile-tool-surface-alignment-v1
result: Blocked
finding_class: external_blocker
canonical_transport: github-pr
pr_number: 8
evaluated_product_head: 26696e0151d782dd3ac69112233329c9d4e71044
next_stage: acceptance
next_expected_actor: dependency_owner
next_action: "#开发执行 PR-005-provider-capability-release-runtime-activation-v1"
```

## Summary

PR-008's repository-owned implementation is not rejected for a local code defect. S01 and S02 are durably complete, and the focused contract verification remains `18 passed in 0.31s`.

End-to-end Acceptance is blocked by external/runtime dependencies that must be resolved before the production probe can lawfully continue. No Acceptance-to-fixing transition is authorized because there is no `repair_local` finding.

## Transport and implementation consistency

PASS.

- Canonical transport remains PR #8 on `task/provider-execution-profile-tool-surface-alignment-v1`.
- Evaluated head is `26696e0151d782dd3ac69112233329c9d4e71044`.
- S01 implementation/verification and S02 public contract/checkpoint are present on the canonical branch.
- No alternate implementation transport was used for this Acceptance.

## Live Acceptance evidence

### A1 — Known deployed Agent build containing PR-008 is not established

**Classification:** `external_blocker`

The currently connected Windows Host `Cherie_li` reports Agent version `0.21.1`.

Its live `capabilities(detail=full)` result does not advertise either:

```text
script_run_execution_profile_v1
host_runtime.script_run_execution_profile_v1
```

The Host does advertise the pre-existing SX-HMSA readiness features:

```text
host_mutation_sandbox_v1
pre_execution_audit_lineage_v1
```

with verified Windows readiness, proving the Host is connected and the older sandbox provider is active, but not that PR-008 is installed.

The same capability response reports a newer public SentinelX Agent version is available, but version availability is not evidence that the current PR-008 head is contained in that build.

PR #5 (`PR-005-provider-capability-release-runtime-activation-v1`) remains open with an approved Plan and pending implementation slices. It owns the exact build/install/runtime-activation semantics required by PR-008 Requirement R10.

**Acceptance consequence:** stop before treating any current model-facing schema behavior as a definitive PR-008 Hub projection result.

### A2 — Current model-facing `sentinel_script_run` schema still lacks the profiled authority surface

**Classification:** `external_blocker` observation, not yet a post-activation Hub verdict

The actual ChatGPT-visible `sentinel_script_run` schema in this Acceptance session exposes the legacy arguments (`content`, `interpreter`, `args`, `cwd`, `timeout`, `sudo`, `cleanup`, `filename`, `env`, `background`, notification fields, `host_id`, `opaque_ref`) and does not expose:

```text
execution_profile
mutation
lineage
repository
```

This proves that the currently selected model-facing surface cannot express PR-008's scoped request contract.

However, because A1 failed first and the connected Agent does not advertise `script_run_execution_profile_v1`, this observation is not sufficient to conclude that a capability-aware Hub would still fail projection after a known PR-008 build connects.

After A1 is resolved, Acceptance must re-inspect the live schema. If the four required semantic fields are still absent or insufficient, the canonical classification is:

```text
HubToolProjectionRequired
```

No wrapper, direct `exec`, allowlist expansion, or `operator_unrestricted` fallback is authorized.

### A3 — Provider-owned scope admission is not yet available for the live scoped proof

**Classification:** `external_blocker`

PR #7 (`PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1`) remains at `plan_review_rejected` and is not implementation-authorized.

Therefore its rejected draft lifecycle API cannot be used as Acceptance authority, and PR-008 cannot lawfully fabricate a `scope_id`, generation, workspace, or equivalent provider authority to perform the harmless scoped marker execution required by R9/R11.

This blocker is downstream of A1 for the ordered production probe, but it will still need resolution before end-to-end Acceptance can become Approved.

## Requirement traceability at this Acceptance window

| Requirement | Result | Evidence / reason |
|---|---|---|
| R1–R6 | PASS at repository scope | S01 implementation + focused 18-test contract verification |
| R7–R8 | BLOCKED | current schema lacks required fields, but capable-Agent projection cannot be judged until A1 is resolved |
| R9 | BLOCKED | PR #7 remains plan-review rejected; no verified provider-owned scope admission path |
| R10 | BLOCKED | connected Agent is 0.21.1 and does not advertise PR-008 feature token; PR #5 implementation remains pending |
| R11 | NOT REACHED | harmless scoped execution requires R8–R10 prerequisites |
| R12 | NOT USED AS PR-008 PROOF | current old build cannot prove the boundary for a deployed PR-008 build |
| R13–R14 | PASS at repository scope | mixed-fleet/wire-envelope behavior documented and covered by S01/S02 evidence |

## Acceptance result

```text
PR-008 Acceptance: Blocked
Reason: external_acceptance_blocker
```

The Task remains at the `acceptance` gate. It does not enter `fixing`, because no current finding is classified `repair_local`.

The first ordered unblocker is runtime activation / known-build evidence owned by PR #5. After that dependency is implemented and a known PR-008-capable Agent is connected, rerun PR-008 Acceptance from the beginning. The live Hub schema must then be re-inspected before any scoped execution attempt.
