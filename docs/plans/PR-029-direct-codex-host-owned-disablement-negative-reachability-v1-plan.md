# PR-029-direct-codex-host-owned-disablement-negative-reachability-v1 — Plan R1

```yaml
task_id: PR-029-direct-codex-host-owned-disablement-negative-reachability-v1
project_id: sentinelx-cloud-core
repository: bewaterhere-coder/sentinelx-cloud-core
requirement_revision: 1
requirement_blob_sha: ddb1f2a1801d09da0723417eadc3f93fd76670f8
plan_revision: 1
plan_state: proposed_pending_independent_review
plan_approved: false
implementation_authorized: false
host_policy_mutation_authorized: false
safe_negative_probe_authorized: false
transport:
  type: github-pr
  pr_number: 29
  branch: task/direct-codex-host-owned-disablement-negative-reachability-v1
  base: main
canonical_main_at_planning: 2e5c69a112323867ee01783521554c43ebd731be
devforge_main_at_planning: 047df4f1c45ce9099ec112017063751243c78d7b
upstream_owner_choice: PR014_host_owned_fail_closed_disablement
```

## 1. Implementation boundary / primary approach

**Use the existing Host-owned policy, not a new SentinelX execution subsystem.** Existing `DirectCodexPolicy.enabled=false` already prevents the builtin provider's admitted `execute_task` action; the real challenge is proving the *effective* Host policy has loaded it and no external configured `local_apis` action shadows the builtin or exposes an alias. No product-code delta is planned by default. Existing independent local DevForge Guided CLI must not be disabled.

This plan deliberately **does not** invoke `devforge_direct_codex`, modify Host config, install binaries, restart any service, create an execution root or materialize a workspace on Plan creation/review. Host effects require a separately admitted Slice, owner privilege, explicit operator consent and transport/readback receipts.

### Current source ownership and tests

| Owner | Current main source | Verification |
| --- | --- | --- |
| Direct Codex policy | `src/sentinelx_core/policy.py` | `tests/test_direct_codex_provider.py` |
| Builtin gate | `src/sentinelx_core/handlers/direct_codex.py` | direct provider tests |
| Registration/dispatch | `src/sentinelx_core/handlers/__init__.py`, `handlers/local_api.py` | `tests/test_direct_codex_provider.py` |
| Canonical Firewall | `src/sentinelx_core/canonical_repository_firewall.py` and readiness projection | `tests/test_canonical_repository_firewall_readiness.py` |
| Example policy | `config.example.windows.yaml` | parse/config tests if a new case is required |

Any source or test change requires separate exact-main ownership confirmation and re-review of the narrow changed file list. No historical PR #14 code is imported.

## 2. Slice proposal (not compiled, not executable until Plan R1 approval)

### S01 — Effective Host policy and alternate-route read-only preflight
- **Allowed:** read exact main and approved Policy/Dispatch contracts, observe agent host/version, local_api `list`/`describe`, capabilities, service state, effective Host-owned config with owner-approved bounded reads; inspect configured `local_apis` for same-name or other Direct Codex aliases; derive a non-secret policy digest and an enforceable rollback/readback strategy.
- **No effects:** no `call`, config edit, service reload, token/credential inspection, bootstrap, workspace creation.
- **Outputs:** exact prior `direct_codex.enabled`, effective route inventory, scoped change plan, current Audit/Sandbox/Firewall baselines, redacted policy fingerprint, S02 Host authority readiness or explicit `DecisionRequired/Blocked` if route ownership unknown.
- **Checkpoint:** durable original PR #29 Run/Receipt and GitHub SHA readback; any unresolved alternative route blocks S02.

### S02 — Bounded Host-owned policy disablement (conditional)
- **Prerequisites:** S01 receipt verified; Plan Review approved; exact active Host + config location/digest verified; explicit Host-owner authority granted for *only* Direct Codex effective policy change and controlled service reload; backup/recovery evidence; no concurrent policy editor; owner-approved rollback that never accidentally re-enables an unsafe endpoint.
- **Change scope:** prefer minimal `direct_codex.enabled: false` in effective Host-owned config. Remove/deny an external same-name/alias route **only** after exact observed alias and separate review/consent for that scope; otherwise STOP. Do **not** disable `local_api` globally, modify `devforge_runtime`, `MutationScope`, sandbox, audit, protected roots, credentials, project routing, source or main. No caller-selected Host paths.
- **Verification:** config parse before activation, exact old/new policy hash, guarded reload, active service/version/new policy readback, bounded rollback decision if reload fails; no unapproved retry.
- **Checkpoint:** Host operation/audit receipt, exact policy readback, PR #29 documentation receipt. If authority lacks, S02 is BLOCKED, not simulated.

### S03 — Guarded real negative reachability
- **Preflight:** re-read S02 receipt and active Host policy; verify effective builtin-disabled and absence of external endpoint shadows/aliases, and inspect actual dispatch path semantics from exact current sources. **Never use a valid-shaped executable task payload.**
- **Test:** only after independently authorized safe-probe admission, issue one real `sentinel_local_api(operation=call,endpoint=devforge_direct_codex,action=execute_task,params={})` or stricter non-executable probe. Source implementation guarantees policy denial before payload validation when disabled; if instead `invalid_payload`, `ok=true`, or any unusual response occurs, STOP, report FAILURE (no retry with valid args), maintain Host fail-closed and Owner HOLD.
- **Security evidence:** expected `endpoint_not_available` / `endpoint_not_configured` / equivalent explicit policy refusal, audit event, before/after process-creation logs (short-lived children included), workspace dir existence/mtime inventory, no Git repo write and no credential access. Static `list` omission is NOT proof. If Host process/audit evidence is unavailable, return `VerificationBlocked`, not PASS.
- **Checkpoint:** exact denial code, timestamp and policy digest, no-child/no-workspace proof receipt, no side effects, GitHub readback.

### S04 — Minimal Runtime regression + formal completion evidence
- **Checks:** `host_mutation_sandbox_v1`, `pre_execution_audit_lineage_v1`, `canonical_repository_mutation_firewall_v1`, unrelated local_api `devforge_runtime` availability, known-safe short operations. Do not conceal remaining firewall blockers; verdict must distinguish Direct Codex coverage closed from total Firewall PASS if other classes remain.
- **Tests:** focused offline tests of `tests/test_direct_codex_provider.py`, `tests/test_canonical_repository_firewall_readiness.py` only when safe bounded runner admitted (else record not-run); read effective deployment and no-mutation receipts. Verify no Host project binding or legacy PR #14 changes.
- **Exit:** only if AC01–AC08 all verifiably satisfied, S01–S04 Run/Receipt/Checkpoint read back, can `#开发验收` evaluate full Requirement R1; no automated acceptance or merge.
- **Negative exit:** remain blocked if any shadow route/call/probe/Firewall/deployment/authority proof missing. Record deterministic `DecisionRequired/Blocked` instead of new generic Runtime or full materializer work.

## 3. Risk & attack-path matrix

| Risk | Fail-closed treatment |
| --- | --- |
| Same-name external `local_apis` shadows builtin | Preflight effective route map; never assume `enabled=false` closes external actions |
| Provider action hidden but dispatch still callable | Real guarded negative `call`, audit and dispatch source contract |
| Missing source claim / `invalid_payload` alone | Negative proof invalid; no executable retry |
| Child briefly spawned and exited | Process creation/audit event coverage, not only process list |
| Service not using edited config | Effective loaded policy/hash/reload/readback required |
| Global `local_api` accidentally disabled | Explicit regression requirement; `devforge_runtime` must stay available |
| Firewall status artificially green | Inspect real effect registry, not only capability flag |
| Privilege/Host MutationScope denial | Respect refusal; no sudo/generic script/scoped bypass |
| DevForge `direct/codex` binding still references provider | Preserve binding; report independent routing debt, no implicit migration |
| Repo PR #29/main drift | Task/PR SHA CAS, re-read main and affected blobs; no blind rebase/push |

## 4. Traceability

| Requirement | Verification |
| --- | --- |
| AC01 | S01 effective Host config read, S02 policy reload + hash |
| AC02 | S01 route map and S03 real dispatcher denial |
| AC03 | S03 safe non-executable call with explicit denial |
| AC04 | S03 child-process creation, workspace, Git and audit evidence |
| AC05 | S04 full Firewall status and Sandbox/Audit re-read |
| AC06 | S04 unrelated `local_api` / `devforge_runtime` and no-root-change proof |
| AC07 | S02 Host operation/audit/rollback receipt + S04 replay prevention |
| AC08 | GitHub PR #29 same identity, current main affected blobs and per-Slice readback |

## 5. Review Gate decision boundary

**Plan R1 is an unapproved proposal.** Reviewer must challenge:
1. whether every Host mutation has exact root/authority and rollback, and whether S02 should be further split under a short interaction budget;
2. whether S03's empty `params` remains provably no-execution in the actual deployed version, including external endpoint shadowing; deny admission until S01 proves this;
3. whether any Host read/telemetry required by S01/S03 is outside current allowed policy, and how to return BLOCKED rather than bypass;
4. whether S04 evidence can physically distinguish true Direct Codex closure from unrelated residual firewall readiness failures;
5. whether direct/codex DevForge project binding debt requires separate owner task before disablement, without broadening this Task.

A rejected review may only trigger Plan Remediation, not implementation. **No S01 execution until `#开发评审 PR-029-direct-codex-host-owned-disablement-negative-reachability-v1` approves the exact plan and compiles an exact Slice Set.**
