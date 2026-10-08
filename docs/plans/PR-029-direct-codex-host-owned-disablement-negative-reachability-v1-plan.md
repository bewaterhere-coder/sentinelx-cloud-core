# PR-029 — Direct Codex Host-owned Disablement — Plan R2

```yaml
task_id: PR-029-direct-codex-host-owned-disablement-negative-reachability-v1
project_id: sentinelx-cloud-core
repository: bewaterhere-coder/sentinelx-cloud-core
requirement_revision: 1
requirement_blob_sha: 385129f8668002a8786023ecb43bb6a4122b78f3
plan_revision: 2
plan_status: proposed_for_separate_review
plan_approved: false
implementation_authorized: false
approved_execution_slice_count: 0
proposed_current_plan_slices: [S01]
allowed_current_plan_effects: read_only_evidence_and_task_scoped_docs
host_policy_mutation_authorized: false
service_reload_authorized: false
local_api_call_authorized: false
codex_execution_authorized: false
product_code_mutation_authorized: false
canonical_main_mutation_authorized: false
transport:
  type: github-pr
  pr_number: 29
  branch: task/direct-codex-host-owned-disablement-negative-reachability-v1
  base: main
canonical_main_at_remediation: 2e5c69a112323867ee01783521554c43ebd731be
devforge_main_at_remediation: 047df4f1c45ce9099ec112017063751243c78d7b
supersedes_plan_r1_blob: 17c3846423bc40b9e836f8713e5ffa2f20a55376
rejected_review_r1_blob: 4e0663bc1288487699d2eb590e427f7eb78acf89
```

## 1. Scope and approval boundary

Requirement R1 AC01–AC08 and PR #14 Owner Decision remain unchanged. The Owner selected Host-owned fail-closed denial of SentinelX-managed Direct Codex; the Owner **has not authorized a particular Host file edit, restart or negative invocation**. PR-021 Minimal Runtime and the canonical mutation/audit/protected-root boundaries continue to apply.

**This R2 proposes exactly one S01 read-only preflight/decision Slice.** It does not include executable S02 policy modification, S03 invocation, S04 runtime regression or any product-code delta. A later revision of the **same PR #29** may propose them only after S01 owner/Host evidence is persisted, an Owner disposition resolves consumer conflict, and a fresh Plan Review authorizes exact effects. Merely completing S01 is not approval for these later operations.

The current `main` already has a policy admission gate: `DirectCodexPolicy.enabled`, builtin `available_actions/describe/call` admission, `local_api` registry and effective-surface Firewall. The actual Host still projects `devforge_direct_codex.execute_task` and Firewall reports `local_api:direct_codex_containment_unproven`. Therefore source defaults are not proof that the live endpoint is disabled.

## 2. S01 — Single bounded read-only dependency / policy / route investigation

**Objective:** determine exactly which Host policy and development consumers must be reconciled, and whether a future independently reviewed, safe Host-owned policy operation and negative test are even feasible. S01 never performs that operation.

### S01 permitted reads (only where current effective policy permits)

1. **GitHub facts:** retrieve exact SentinelX `main` SHA and existing source/test blobs (`policy.py`, `handlers/direct_codex.py`, `handlers/__init__.py`, `handlers/local_api.py`, canonical Firewall and relevant tests), current PR #29 and original PR #14 identity/receipts, current PR #19 Requirement/Gate/test obligation, PR-021 Capability Disposition Matrix, and DevForge `main` registry project execution binding. Recheck all SHAs at completion.
2. **Structured live Host:** use `sentinel_capabilities(detail=full)`, `sentinel_local_api(operation=list)`, and `sentinel_local_api(operation=describe)` for the Direct Codex and `devforge_runtime` endpoints, plus supported structured read-only service status if authorized. Never invoke `operation=call`, even with empty `params`.
3. **Effective policy identity:** identify the currently active Host and policy source/config location **through Host-owned read-only projection**. The previously observed config locator `C:\ProgramData\SentinelX\config.yaml` is an evidence hint, not caller write authority. Read only narrowly scoped, permission-admitted fields relevant to `direct_codex.enabled`, `local_apis` name/action/protocol/transport/aliases, `disabled_ops`, and active policy load generation/fingerprint. If no redacted read/attested digest exists, record `PolicyEffectiveStateUnverified` rather than leaking config (tokens/credentials) or using generic shell.
4. **Safety/telemetry feasibility:** discover through read-only capability projection whether a future authorized Host owner can obtain an exact mutation mechanism, preconditioned CAS/policy parse/reload/readback, no-concurrent-editor protection, audit events including short-lived process creation, and workspace/repository-before/after identity. Identify real available tools/sources; mark inaccessible channels `Unverified`. Do **not** run telemetry setup or process probes.
5. **Consumer dependency matrix:** inspect real DevForge `sentinelx-cloud-core` `provider: direct/adapter: codex` binding (registry blob `08f50a36cbb90d5a08856d7dce2adf65248a7584` at R1) and PR-019 `implementation/S01` and its Direct Codex tests, plus guided CodeBuddy/Codex CLI availability and Harness bootstrap expectations **from already existing receipts/docs**. Never assume an unrelated CLI or Harness has taken over. Owner choice of "disable" is not an implicit execution-binding or baseline migration.
6. **Disposition matrix:** produce an immutable owner decision packet that distinguishes `ConsumerGateClearWithVerifiedMigrationReceipt`, `ExplicitOwnerAuthorizedHoldOrRetirement`, or `DecisionRequired/Blocked` and separately records `HostWriteTransportVerified`, `SafeNegativeProbeVerifiable` or `Unverified/Blocked`. Lack of proof blocks all future mutation.

### S01 strictly forbidden effects

- Any Host config file/write/permission/ACL/policy/allowlist or service reload/restart, scoped execution, provisioning/terminalization, process launch, local CLI, executable tests, filesystem/workspace/repository mutation, CI trigger, credentials or protected root access expansion.
- `sentinel_local_api(operation=call)` to **any** endpoint for a negative Direct Codex probe; empty `params={}` is not automatically safe because external `local_apis` entries shadow builtin routing.
- Direct Codex `execute_task`, full materializer, PR #14 source/history replay, PR #19 mutation, DevForge binding migration, new task/PR, canonical `main` write, rebase/cherry-pick/force push.
- Treating `list` omission, readiness=false, `invalid_payload`, a source default or a service-state report as physical "unreachable" proof.

### Required S01 outputs and fail-closed decisions

| Gating evidence | Must identify | If missing |
| --- | --- | --- |
| G1 consumer admission | current DevForge binding, PR-019/stabilization test dependence, Harness and guided CLI replacement evidence; explicit Owner hold/retirement or independently accepted migration receipt | `ConsumerDependencyOwnerGateUnresolved` |
| G2 loaded Host policy | actual Host identifier, source and policy load generation/digest, redacted `direct_codex.enabled`, effective `local_apis` entries and aliases | `PolicyEffectiveStateUnverified` |
| G3 route closure feasibility | builtin/external same-name routing precedence and all action aliases; prospectively safe call-denial path | `ExternalAliasOrNegativeProbeUnproven` |
| G4 Host mutation transport | exact owner-controlled write/reload mechanism, config CAS/parse, audit/permission authority, no concurrent editor, release/rollback constraints | `HostMutationTransportUnproven` |
| G5 zero-side-effect evidence | evidence channels for child **creation** (not just live PID), workspace/Git changes, local audit and service reload readback | `NoSpawnOrWorkspaceProofUnavailable` |
| G6 intact security | Sandbox/Audit, MutationScope/Job/AppContainer/ACL, canonical Firewall reason and protected `D:\coco` source root | `SecurityReadinessOrCoverageUnverified` |
| G7 transport/receipt | exact original PR #29 and current `main`, bounded S01 Run/Attempt/Checkpoint and remote readback, PR #14 unmodified | `TransportOrReceiptBlocked` |

S01 shall output `OwnerPreflightReadyForSeparatePlanReview` **only when all read-only gating evidence is available**; this is not a Host-action approval. Otherwise output `DecisionRequired/Blocked` with exact missing evidence and one Owner action. The S01 receipt must distinguish observed live state from proposed later validation; do not mark Firewall PASS, Direct Codex disabled or PR #19 resolved without physical evidence.

### S01 checkpoint and termination

A single bounded read-only command execution produces a task-scoped S01 evidence note, security/dependency decision, Run/Attempt record, Slice Completion Receipt (for read-only work only), and checkpoint on this original PR #29 branch, followed by remote SHA readback. Only if Plan Review R2 approves this exact Plan and compiles a Plan-R2-bound **S01-only Slice Set** is S01 executable. No background work, automatic next-Slice start or Host mutation.

If the active Host policy cannot be safely inspected by admitted read-only tools, S01 must stop, checkpoint `Blocked`, and ask for a narrowly reviewed owner-provided attested policy readback. Do not use `sentinel_exec`, a new scope, or a downloaded script as a workaround.

## 3. Future implementation stages are unadmitted, not current Slices

**FUTURE PROPOSAL ONLY (no S02/S03/S04 in current Plan's executable Slice Set):**

- **Host policy change:** separately revised Plan with exact source/target Host identity, Host-owner permission and surface, verified `direct_codex.enabled=false` path, no external alias, config digest CAS, owner-owned controlled reload, effective policy readback, audit, and a degraded state that **never restores uncontained opt-in**.
- **Negative reachability:** separately reviewed safely fenced, non-executable probe only after proof of no external shadow/alias and exact effective policy generation; hard stop on any unexpected `ok`/`invalid_payload`/scope drift. Preserve process-creation audit covering ephemeral children, no-workspace/Git/credential effects; no executable Task payload and no retry.
- **Focused regression:** independently prove genuine Firewall effective-surface readiness plus continuing Sandbox/Audit and `devforge_runtime` availability; report other independent Firewall blockers instead of claiming PASS. Check prerequisite consumer migration/hold receipts.
- **Acceptance/closure:** only against the original Requirement R1 AC01–AC08 after separate reviewed Plan/Slices and exact Host receipts. S01-only completion is **never** full Requirement acceptance.

Do not pre-approve or schedule these stages from this R2.

## 4. R1 findings closure in R2 plan

| R1 finding | R2 Plan remediation | Status for read-only S01 Plan Review |
| --- | --- | --- |
| R1-F01 | G1 consumer matrix and explicit Owner dependency gate before Host mutation; DevForge registry, PR-019 and Harness unchanged | Addressed in plan; actual Owner migration/retirement remains pending |
| R1-F02 | S01-only Plan; G2/G4 exact policy/Host mutation mechanism as read-only evidence; future Host edit requires new Plan Review | Addressed; Host mutation not admitted |
| R1-F03 | G3 route inventory; no `call` in S01; future probe only after independent no-alias proof and separate Plan Review | Addressed; real denial not yet proven |
| R1-F04 | G5 process creation and audit availability, explicit safe degraded non-reenable/rollback design, fail-closed on unavailable channels | Addressed; future telemetry and rollback not yet approved |

Requirement semantics are unchanged; each AC remains a future Acceptance requirement. Current S01 contributes prerequisites only, not proof of completed AC01–AC08.

## 5. Constraints and independent Review gate

PR-021 Minimal Runtime frozen decision and §13(9) separate disablement Task rule apply. PR #14 remains `acceptance/DecisionRequired`, PR #19 remains independently owned, MRS-01 HOLD and MRS-02 not admitted. Current DevForge `direct/codex` project binding is a live dependency, **not** migration authority.

The reviewer must verify that S01 is entirely read-only, has adequate external alias/consumer decision coverage, only requests policy data through admitted redacted channels, and can produce a credible negative decision even when Host tools are unavailable.

**Plan R2 is merely proposed; `plan_approved=false`.** After successful remediation readback, the Task must return to `plan_review` and the canonical next command is `#开发评审 PR-029-direct-codex-host-owned-disablement-negative-reachability-v1`. Plan remediation cannot approve itself, compile a Slice Set, perform Host operations, or advance to implementation.
