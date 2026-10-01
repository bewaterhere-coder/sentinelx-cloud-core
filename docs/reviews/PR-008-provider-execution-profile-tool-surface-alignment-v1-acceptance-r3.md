# PR-008 — Provider Execution Profile Tool Surface Alignment V1 — Acceptance Review R3

## Decision

```yaml
task_id: PR-008-provider-execution-profile-tool-surface-alignment-v1
result: Blocked
finding_class: external_blocker
blocker_codes:
  - HubToolProjectionRequired
  - ProviderScopeAdmissionRequired
canonical_transport: github-pr
pr_number: 8
evaluated_product_head: 3c6245bffd45bf0fa8b7db4fc47d002e8cfeed9c
live_candidate_commit: 0badec02738af83c7e93101a72c18311858abf30
live_agent_version: 0.24.1.dev21+g0badec027
next_stage: acceptance
next_expected_actor: dependency_owner
```

## Summary

Acceptance R3 clears the two R2 blockers that were under Host/operator control:

- R10 known-build activation is now satisfied by the live exact candidate `0badec02738af83c7e93101a72c18311858abf30`, which contains both canonical `main` at `f7e878f3497582547e5d52cd33b060cae18d2e84` and PR-008 exact head `3c6245bffd45bf0fa8b7db4fc47d002e8cfeed9c` as merge parents.
- R12 direct Python denial is restored. `python` is absent from `allowed_commands`, and a live `sentinel_exec("python --version")` returns `command_not_allowed`.

The live Agent now advertises `host_runtime.script_run_execution_profile_v1` with `profile_argument=execution_profile`, `supported_profiles=[scoped_mutation]`, the required mutation/lineage/repository input contract, and verified Windows scoped-mutation readiness.

However, the actual ChatGPT-visible `sentinel_script_run` tool schema still exposes none of the required profiled input fields: `execution_profile`, `mutation`, `lineage`, or `repository`. A harmless unprofiled probe still returns `execution_profile_required`. Because the live Agent is now a known build carrying PR-008, this is no longer pre-activation ambiguity. The external Hub/MCP projection dependency is therefore definitively classified as `HubToolProjectionRequired`.

PR-007 also remains `plan_review_rejected`, so provider-owned scope admission is unavailable. R9 and the final R11 scoped marker proof remain blocked independently of the Hub projection issue.

No R3 finding is a local PR-008 implementation defect. The Task remains at the Acceptance gate and does not enter fixing.

## Live evidence

### F1 — Known PR-008-capable Agent is active

**Classification:** resolved external dependency / R10 PASS

The Acceptance Host reports:

```text
version = 0.24.1.dev21+g0badec027
```

The `g0badec027` provenance corresponds to candidate commit:

```text
0badec02738af83c7e93101a72c18311858abf30
```

That candidate was constructed without merging PR #8 and has two parents:

```text
f7e878f3497582547e5d52cd33b060cae18d2e84  # canonical main containing PR-005
3c6245bffd45bf0fa8b7db4fc47d002e8cfeed9c  # PR-008 exact head
```

The live Agent advertises:

```text
host_runtime.script_run_execution_profile_v1.available = true
feature = script_run_execution_profile_v1
operation = script_run
profile_argument = execution_profile
supported_profiles = [scoped_mutation]
```

Its `scoped_mutation` profile readiness is `available=true`, `verified=true`, platform `windows_appcontainer_v1`.

### F2 — Hub/MCP model-facing projection is definitively missing

**Classification:** external_blocker

**Blocker code:** `HubToolProjectionRequired`

The current ChatGPT-visible `sentinel_script_run` schema still accepts only the legacy script-run fields and does not expose:

```text
execution_profile
mutation
lineage
repository
```

A live harmless probe through that visible surface returns:

```text
error = execution_profile_required
required_argument = execution_profile
feature = script_run_execution_profile_v1
supported_profiles = [scoped_mutation]
```

The Agent-side advertised contract and readiness are now live on a known PR-008-capable build, so the remaining mismatch is outside this repository's Host Agent implementation boundary. R7 truth-boundary behavior is satisfied by explicitly reporting this external dependency; R8 remains blocked until the Hub/MCP tool projection carries the required fields.

No wrapper fallback, direct `exec python`, allowlist expansion, caller-minted scope authority, or `operator_unrestricted` fallback is authorized.

### F3 — Direct Python boundary is restored

**Classification:** resolved protected boundary / R12 PASS

Current capabilities do not list `python` in `allowed_commands`. Live proof:

```text
sentinel_exec("python --version")
→ command_not_allowed
```

The Host still reports verified `host_mutation_sandbox_v1` and `pre_execution_audit_lineage_v1`; structured Git remains available. Thus restoring the direct-command boundary did not disable the intended sandbox/audit capabilities.

### F4 — Provider-owned scope admission remains unavailable

**Classification:** external_blocker

**Blocker code:** `ProviderScopeAdmissionRequired`

PR-007 remains `plan_review_rejected` and implementation is not authorized. The two outstanding plan findings remain:

1. durable `allowed_operation_classes` must be consumed as an execution-time admission check by `script_run scoped_mutation`, not merely persisted;
2. scope control must reconcile with the existing `MutationScopeStore.read_scope(scope_id)` seam and preserve exact generation + repository + semantic binding without duplicating readback authority.

Therefore R9 remains blocked and R11 cannot yet perform the provider-issued-scope marker execution and terminal scope/audit readback.

## Requirement traceability

| Requirement | R3 result | Evidence / reason |
|---|---|---|
| R1–R6 | PASS | Repository implementation plus live Agent advertisement/diagnostic evidence |
| R7 | PASS | Missing Hub projection is explicitly classified as `HubToolProjectionRequired`; no false completion claim |
| R8 | BLOCKED | Client-visible `sentinel_script_run` still lacks `execution_profile`, `mutation`, `lineage`, `repository` |
| R9 | BLOCKED | PR-007 remains plan-review rejected; provider-owned scope admission unavailable |
| R10 | PASS | Exact candidate `0badec027...` containing PR-008 head is live on `Cherie_li` |
| R11 | NOT REACHED | Requires R8 + R9 to supply both model-facing profile fields and provider-issued scope authority |
| R12 | PASS | Direct `sentinel_exec python --version` returns `command_not_allowed` |
| R13–R14 | PASS | Mixed-fleet/payload-envelope design unchanged; no protocol churn required |

## Ordered unblockers

1. Implement/activate Hub/MCP projection of the advertised PR-008 `script_run` fields: `execution_profile`, `mutation`, `lineage`, `repository`, preserving target-Agent capability gating and without synthesizing authority.
2. Repair/review/implement PR-007 (or equivalent verified provider-owned scope admission), including execution-time `allowed_operation_classes` enforcement and exact existing-store binding.
3. Run the harmless scoped marker proof through the model-facing `sentinel_script_run` surface using provider-issued scope authority, then read back audit evidence and terminal scope closure.
4. Reconfirm direct Python denial and all Host sandbox/readiness evidence in the same final Acceptance environment.

## Acceptance result

```text
PR-008 Acceptance R3: Blocked
Strongest finding: external_blocker
Blockers: HubToolProjectionRequired, ProviderScopeAdmissionRequired
R10: PASS
R12: PASS
Task stage remains: acceptance
```
