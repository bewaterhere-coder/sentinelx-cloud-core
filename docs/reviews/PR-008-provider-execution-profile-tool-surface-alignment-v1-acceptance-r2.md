# PR-008 — Provider Execution Profile Tool Surface Alignment V1 — Acceptance Review R2

## Decision

```yaml
task_id: PR-008-provider-execution-profile-tool-surface-alignment-v1
result: Blocked
finding_class: protected_boundary
canonical_transport: github-pr
pr_number: 8
evaluated_product_head: 7a3da6ce9204535fa54624b0f33bf1f5a5feb73d
live_agent_version: 0.24.0
next_stage: acceptance
next_expected_actor: dependency_owner
```

## Summary

PR-005 is no longer an unresolved release/runtime infrastructure dependency. SentinelX v0.24.0 is published, installed, connected, and reports verified Windows mutation sandbox/audit readiness.

PR-008 still cannot be Acceptance Approved because the deployed v0.24.0 build does not contain PR-008, provider-owned scope admission remains unavailable, and the current Host configuration permits direct `exec python`, preventing the final no-escalation proof required by R12.

No finding is a local PR-008 implementation defect. The Task remains at the Acceptance gate and does not enter fixing.

## Live evidence

### F1 — PR-005 release/runtime path is resolved, but R10 known-build evidence is still absent

**Classification:** external_blocker

Live Host `Cherie_li` is connected and reports Agent `0.24.0`. The release was built from canonical `main` commit `f7e878f3497582547e5d52cd33b060cae18d2e84`.

PR-008 remains open on `task/provider-execution-profile-tool-surface-alignment-v1` at `7a3da6ce9204535fa54624b0f33bf1f5a5feb73d`; therefore v0.24.0 is not a build containing this Task.

The PR-008 implementation adds hello feature token `script_run_execution_profile_v1` and capabilities feature `host_runtime.script_run_execution_profile_v1`. The live v0.24.0 Agent advertises neither token. Thus R10 remains BLOCKED, now specifically on activation of a known PR-008-capable build rather than on missing release infrastructure.

### F2 — Current model-facing tool schema still cannot express the required profile contract

**Classification:** external_blocker observation; not yet final Hub verdict

The current ChatGPT-visible `sentinel_script_run` schema still lacks `execution_profile`, `mutation`, `lineage`, and `repository`. A live unprofiled probe returns `execution_profile_required`.

Because F1 is unresolved, this remains pre-activation evidence. After a known PR-008-capable Agent is active, Acceptance must read the schema again. If the required fields remain absent, classify the dependency as `HubToolProjectionRequired`.

No wrapper, direct `exec`, allowlist expansion, or `operator_unrestricted` fallback is authorized.

### F3 — Provider-owned scope admission is still unavailable

**Classification:** external_blocker

PR-007 remains `plan_review_rejected`, with implementation unauthorized. Its two blocking plan findings remain unresolved: execution-time consumption of `allowed_operation_classes`, and reconciliation with the existing `MutationScopeStore.read_scope(scope_id)` seam plus exact generation/repository/semantic binding.

Therefore R9 and the harmless R11 scoped execution proof remain blocked.

### F4 — Direct Python execution is currently open on the Acceptance Host

**Classification:** protected_boundary

Live capabilities list `python` in `allowed_commands`, and the read-only probe:

```text
sentinel_exec("python --version")
→ Python 3.14.7
→ returncode=0
```

This is not attributed to PR-008 source changes; PR-008 does not add Python to the allowlist. It is Host configuration drift relative to the intended Acceptance boundary.

R12 requires the final environment to prove the safe profiled script path without weakening direct command execution. The current Host cannot provide that proof while direct Python is allowlisted.

## Requirement traceability

| Requirement | R2 result | Evidence / reason |
|---|---|---|
| R1–R6 | PASS at repository scope | PR-008 S01/S02 implementation remains present; feature token and capabilities contract are in the PR diff |
| R7–R8 | BLOCKED | client schema still lacks required fields; definitive Hub verdict waits for a deployed PR-008-capable Agent |
| R9 | BLOCKED | PR-007 remains plan-review rejected |
| R10 | BLOCKED | v0.24.0 is active but does not contain PR-008 |
| R11 | NOT REACHED | requires R8–R10 plus provider-issued scope |
| R12 | BLOCKED / protected boundary | direct `exec python` currently succeeds on the live Host |
| R13–R14 | PASS at repository scope | mixed-fleet/payload-envelope design unchanged |

## Ordered unblockers

1. Restore the Acceptance Host direct-command boundary so Python is not generically allowlisted.
2. Activate an exact, known Agent build containing PR-008 using the now-working PR-005 release/runtime path or an equivalent verified candidate activation path.
3. Re-read the live model-facing `sentinel_script_run` schema; if required fields remain absent, persist `HubToolProjectionRequired`.
4. Repair/review/implement PR-007 (or equivalent verified provider-owned scope admission).
5. Run the harmless scoped marker proof plus terminal scope/audit readback and direct-exec denial proof.

## Acceptance result

```text
PR-008 Acceptance R2: Blocked
Strongest finding: protected_boundary
Task stage remains: acceptance
```
