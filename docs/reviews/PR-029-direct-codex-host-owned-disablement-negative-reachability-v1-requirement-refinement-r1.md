# PR-029-direct-codex-host-owned-disablement-negative-reachability-v1 — Requirement Refinement & G1 Challenge R1

```yaml
task_id: PR-029-direct-codex-host-owned-disablement-negative-reachability-v1
review_target: Requirement_R1
stage: planning
decision: Ready_for_Plan_Review
main_at_intake: 2e5c69a112323867ee01783521554c43ebd731be
owner_source_pr: 14
owner_choice: HostOwnedFailClosedDisablement
provisional_branch: task/direct-codex-host-owned-disablement-negative-reachability-v1
allocated_pr: 29
ui_semantics: NotApplicable
readiness_depth: deep_security_sensitive
```

## Requirement challenge

The Owner has decided the disputed architecture choice: **disable SentinelX-hosted Direct Codex at the Host policy layer**. It does **not** authorize physical mutation. Potential ambiguity between "hidden from advertised list" and "truly unreachable" is resolved by AC02/03: both dispatch surface and a real fail-safe negative invocation must prove refusal.

### Verification/assumption matrix

| Concern | Chosen requirement rule | Disconfirming case |
| --- | --- | --- |
| Builtin policy | Effective `enabled=false` with current Host policy receipt | YAML changed but Host still uses old policy |
| External route shadow | All effective local_apis aliases covered | External `devforge_direct_codex` shadows builtin |
| Real denial | Guarded negative call returns policy/endpoint denial | Only `invalid_payload` observed |
| Zero spawn | Audit/process/workspace before-and-after evidence | Short-lived child process escaped late scan |
| Firewall | Actual effective-surface classifier PASS | Force-made-green status with missing route coverage |
| Collateral | `devforge_runtime` and short operations unaffected | Global `local_api` removed |
| Host authority | Independently approved config/reload/test receipt | Ad hoc privileged config edit in original canonical checkout |
| Source transport | Original PR #29 immutable identity, exact main blobs | PR #14 historical branch merged or replayed |

**Foundation/readiness:** PR-021/PR-027 already define the minimal-runtime boundary and Owner gate matrix. The latest live P0 missing evidence concerns Host policy state, alternate route and negative proof; this is deliberately an execution/Acceptance precondition, not an unresolved choice about desired behavior. Plan must fail closed if the Host safety case for a negative test cannot be proven.

**G1 result:** Ready, with all source constraints/risks preserved. Requirement Ready does not imply implementation authorization. No Host, user CLI, repository source or canonical main modification was made by refinement.
