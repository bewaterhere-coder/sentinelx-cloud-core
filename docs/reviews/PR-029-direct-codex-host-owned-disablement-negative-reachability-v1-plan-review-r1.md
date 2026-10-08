# PR-029 — DevForge Plan Review R1

## Exact review identity

```yaml
task_id: PR-029-direct-codex-host-owned-disablement-negative-reachability-v1
project_id: sentinelx-cloud-core
source_command: "#开发评审 PR-029-direct-codex-host-owned-disablement-negative-reachability-v1"
review_target: Plan_R1
requirement_revision: 1
requirement_blob_sha: 0f7359ce1d71d59fd07f6a97af566aa7814927c4
plan_revision: 1
plan_blob_sha: 17c3846423bc40b9e836f8713e5ffa2f20a55376
reviewed_head: 5eba81ab1c6eb8e812b3f95ddc94e83e9cae8f8c
canonical_main_sha: 2e5c69a112323867ee01783521554c43ebd731be
devforge_main_sha: 047df4f1c45ce9099ec112017063751243c78d7b
repository: bewaterhere-coder/sentinelx-cloud-core
pr: 29
branch: task/direct-codex-host-owned-disablement-negative-reachability-v1
decision: Rejected
review_contract: DevForge_Review_Contract_v1.3
implementation_authorized: false
host_mutation_authorized: false
negative_call_authorized: false
```

## Conclusion

**Rejected — Plan-local remediation required before Plan Review can approve even a read-only Slice.** The Owner-selected **Host-owned, fail-closed Direct Codex disablement** direction is appropriate and preserves the PR-021 minimal-runtime boundary. This review rejects **execution admission**, not that Owner decision or Requirement R1.

The Plan proposes S01 read-only preflight plus S02 live policy edit/reload, S03 real `local_api.call`, and S04 regression. Host privileges, exact transport, operative routing dependencies, and the negative-test safety case have not yet been proven. A conditional phrase like "owner consent" is not sufficient to admit later execution under a currently unverified Host mutating surface.

## Passing controls

- New canonical Task identity and Draft PR #29 allocated by GitHub; no Task/PR #14 identity reassignment.
- Current main `2e5c69a112323867ee01783521554c43ebd731be` owns existing `DirectCodexPolicy.enabled=false` admission gate and `local_api` dispatcher. Zero product-code changes is an appropriate default.
- Requirement AC01–AC08 traceability exists, and forbidden generic `local_api` disabling, protected-root weakening, long-Agent Runtime expansion and historical source replay are explicitly excluded.
- Live Host `0.24.1.dev791+g5d9286b22` reports Sandbox/Audit verified, but Firewall FAIL `local_api:direct_codex_containment_unproven`; `sentinel_local_api(list)` still registers `devforge_direct_codex` with one builtin action. No physical disablement or negative test was performed.
- GitHub PR #29 is ahead of main by documentation-only commits; the source baseline is not obtained from the materially divergent PR #14.

## Blocking findings

### R1-F01 — Unresolved active development-consumer dependency (P0, plan_local + Owner gate)

DevForge `system/development-project-registry.yaml` current-main blob `08f50a36cbb90d5a08856d7dce2adf65248a7584` still binds `sentinelx-cloud-core` to `provider: direct / adapter: codex`. Original PR-019 remains in `implementation/S01` on an old candidate with tests explicitly including Direct Codex, and the PR-021 frozen Capability Disposition Matrix `05b6906614715e14450a2fd03e0699200e016074` says freeze/deprecate but retain operational use until guided CLI and baseline/binding migration has been admitted, with provider disablement on a separate Task.

Plan R1 simultaneously promises `direct_codex` Host disablement **and** forbids project-binding migration, while relegating those real consumers to "report routing debt". A live disablement can strand a current execution route and falsify PR-019's stabilization criteria. Owner's disablement choice is settled; its compatibility/transition preconditions are not.

**Minimum remediation:** add an explicit, reviewed **consumer-dependency owner gate before any Host mutation**. Inventory true PR-019/DevForge/Harness reliance; require a separately accepted guided CLI routing/migration receipt or an explicit Owner-authorized fail-closed retirement/holding disposition for affected callers. `direct/codex` does not automatically become supported elsewhere. The Plan must stop at read-only evidence if none is available; do not silently change the DevForge registry or PR-019.

### R1-F02 — Host mutation admission is still abstract (P0, plan_local)

S02 allows `C:\ProgramData\SentinelX\config.yaml` policy mutation and service reload after S01, yet its mechanism/Host-owner authority model, exact write-scope, active-policy parser/reload admission, policy digest binding, no-concurrent-edit lease and fail-closed restore/rollback are not defined concretely from supported Host capabilities. A Plan Review that approves executable S02 before its physical safety mechanism is established would be a speculative Host mutation admission, contrary to current Host Mutation Scope/Audit boundaries.

**Minimum remediation:** revise the **currently executable plan to one S01 read-only decision Slice**, whose output is exact Host config/owner evidence, approved policy-edit transport candidate, no-concurrency and fail-closed rollback strategy, or `DecisionRequired/Blocked`. Move S02+ real Host operations into **a separate subsequently reviewed revised Plan** only after the S01 receipt confirms the bound physical API/owner authority and dependency gate. Never use a shell/file-edit workaround merely because a documented Host operation is unavailable.

### R1-F03 — Negative reachability invocation lacks an independently frozen safety proof (P0, plan_local)

A remote-configured `local_apis.devforge_direct_codex` takes precedence over the builtin provider in `handlers/local_api.py`. An empty `params={}` `operation=call` can therefore dispatch to an **external** endpoint even while the builtin is disabled; it is not generically a "safe" call. The requirement rightly states `invalid_payload` is insufficient and no Codex child/workspace side effects may occur. R1's conditional S03 preflight lacks a frozen endpoint type/identity digest + no-alias proof + same-policy-generation pre-call admission that makes the probe safely non-executable for the actually loaded Host.

**Minimum remediation:** no `call` in approved S01. Require later S03 to be separately reviewed against S01's exact builtin/external route inventory and reloaded policy identity, with an explicit safe-denial mechanism, process-creation/audit proof and abort-on-drift/no-retry conditions. If external shadow/alternate mutating alias cannot be ruled out without attempting action, return `DecisionRequired/Blocked` and **do not send the probe**. `invalid_payload` never establishes negative reachability.

### R1-F04 — Owner-safe rollback and measurable absence evidence not executable yet (P1, plan_local)

Raw backup/restore of the original policy could **re-enable** the uncontained Direct Codex route. S02 does not specify a safe degraded state when reload fails, and S03's process absence requirement includes short-lived child processes; ordinary later process listing alone cannot prove it. Several audit/telemetry read paths are not currently proven Host-admitted.

**Minimum remediation:** S01 must record an exact fail-closed degraded/recovery state without restoring unsafe opt-in, plus exact read-only available process-creation, audit, workspace, git, and service/policy verification channels; mark unavailable observations explicitly BLOCKED. Subsequent Host operations require fresh Owner review/consent and real Receipt.

## Review matrix

```yaml
solution_direction: PASS
minimal_runtime_and_non_goals: PASS
requirement_traceability: PASS
task_transport_identity: PASS
technical_feasibility_for_full_plan: NOT_PROVEN
host_security_admission: FAIL_PENDING_EVIDENCE
negative_reachability_test_safety: FAIL_PENDING_EVIDENCE
owner_dependency_gate: FAIL_PENDING_EVIDENCE
risk_and_rollback: PARTIAL
plan_review_decision: Rejected
```

## Mandatory Plan R2 remediation

Preserve Requirement R1 AC01–AC08, original PR #29, original branch and Owner decision. Remediate **Plan only**:

1. Compile a proposal for **S01 read-only investigation/decision** with exact allowed GitHub/Host read operations; no Host config write, service reload, `local_api.call`, dev CLI execution, policy denial bypass or protected-root mutation.
2. Add an immutable S01 output matrix for DevForge project execution binding / PR-019 / guided CLI readiness and required Owner disposition. No implicit project migration.
3. Require S01 to surface Host policy effective config identity, exact route registry and any external shadow/alias; candidate Host-owned write/reload mechanism, audit/readback source and safe rollback/recovery, otherwise `DecisionRequired/Blocked`.
4. Defer S02–S04 to a **fresh independently reviewed implementation Plan revision**, with physical mutation authority, safe negative-call admission and measured non-execution evidence. Review R2 of S01 must not authorize S02/03 by implication.
5. Freeze fail-closed negative outcomes, all current security invariants, original PR #14 evidence, and `MRS-01 HOLD`.

No current Slice Set created; no tests executed or Host policy altered. `main` remains unchanged.

**Canonical next command:** `#开发计划修复 PR-029-direct-codex-host-owned-disablement-negative-reachability-v1`.
