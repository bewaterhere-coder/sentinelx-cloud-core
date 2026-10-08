# PR-029 / S01 — Read-only Preflight Evidence, 2026-10-08

**Disposition: DecisionRequired / Blocked.** This artifact records observations only. It is not a Host configuration or security closure Receipt, and the S01 Slice remains pending until required owner/Host readback evidence is available. No `local_api.call`, SentinelX Host mutation, generic shell, scoped execution, Codex CLI/process, file edit, test or service restart was issued as part of this Slice.

## Canonical lineage

- Repository: `bewaterhere-coder/sentinelx-cloud-core`; main SHA `2e5c69a112323867ee01783521554c43ebd731be`.
- PR #29 branch `task/direct-codex-host-owned-disablement-negative-reachability-v1` at preflight HEAD `b41a7511a5411684d7f4459d06ea1e47274abe19` (open Draft).
- Requirement R1 Task SHA `032dd871e080bf5e4bd683451348fb907939dcfa`; Approved Plan R2 SHA `300b1adc237dd4220d866ecdeb4047880d203874`; Approved review SHA `17d16ceabb9f6dd1a5fdfbdd461632577669ad81`; pending S01 Slice Set SHA `539b385615c1d2c2bb29c0bdd7af60bce45e6f53`; transition Receipt SHA `be3b2b7d09924070c14dc4d5afea0fc937dce1af`.
- DevForge main `047df4f1c45ce9099ec112017063751243c78d7b`. PR #14 head `412509bd7d2db4484ea8b4916984f79eb5052e7e`; Owner Decision `5c9e060e7842d7c197ddc256de2e7fcfd8343c11`. PR #19 head `f13dfe874f5de20c843e0c8cba4eb7e8af5731b7`; current Task blob `1017f9f54cd34d7868d5c0438eadac6e076f16df`.

## G1 — active development consumers (BLOCKED)

1. DevForge project registry `system/development-project-registry.yaml` blob `08f50a36cbb90d5a08856d7dce2adf65248a7584` on current DevForge main still binds `sentinelx-cloud-core` to `provider: direct`, `adapter: codex`. No accepted migration or fail-closed holding disposition was read back.
2. Original PR #19 remains open Draft with Task stage `implementation`, current S01, tests including `tests/test_direct_codex_provider.py`, `tests/test_direct_codex_execution.py` and its Requirement includes physical provider readiness / end-to-end Direct Codex evidence. No Owner-authorized baseline retirement was read back.
3. Frozen PR-021 capability matrix blob `05b6906614715e14450a2fd03e0699200e016074` explicitly marks the Direct Codex lifecycle DEPRECATE but requires controlled downstream transition, separately reviewed provider disablement and dependency/readback proof. It notes Harness direct:codex bootstrap coupling as HOLD. ADR blob `36e0290de039336a8e4ce8561c22c731f12e9602` allows Guided CLI as a future external execution plane, not a migrated current binding.
4. DevForge CodeBuddy adapter blob `d1e0547ef212a0e45da59b5129d61ee1804cf722` and Codex adapter blob `a659274bbcb2c0657ecccafaf4a5d47c67ade6db` document alternatives; documentation alone is not an installed/accepted replacement or a verified migration Receipt.

**G1 result: `ConsumerDependencyOwnerGateUnresolved`.** Owner must authorize a specific fail-closed hold/retirement of affected Direct Codex consumers or read back a separately accepted guided CLI replacement/migration, without altering the DevForge registry or PR #19 under this Slice.

## G2 — effective Host-owned policy (BLOCKED)

- Structured SentinelX capabilities: host `Cherie_li` (label `windows`, Windows 11 AMD64), agent version `0.24.1.dev791+g5d9286b22`.
- Active config locator from structured `locations.config.path`: `C:\ProgramData\SentinelX\config.yaml`. The file is on the Host allowlisted read paths, **but an unredacted YAML fetch could expose credentials**. S01 did not read its contents because no proven policy-admitted, field-redacted structured projection / effective generation digest was available.
- Capability response `disabled_ops: [exec]` does not specify `direct_codex.enabled`; source defaults `enabled=false` do not establish loaded effective policy.
- Source `src/sentinelx_core/policy.py` blob `d476bad339a7560871d77f2746e3685d9a578348` defines disabled admission `direct_codex_disabled`. Runtime's actual Direct Codex action remains projected with one action, indicating builtin admission. Exact loaded policy identity/version and secure redacted Direct Codex flag are **not** proven.

**G2 result: `PolicyEffectiveStateUnverified`.** Requires an independently Host-owner-attested, secret-free selected-field policy/effective generation readback and integrity identity; do not dump full YAML.

## G3 — effective routes and alias / safe negative-probe admission (BLOCKED)

- Real `sentinel_local_api(operation=list)` returned `devforge_direct_codex`: `protocol=builtin`, `provider_kind=builtin`, `action_count=1`, and `devforge_runtime`: `protocol=builtin`, `action_count=5`. No configured external endpoint appeared in that **current advertised** local_api list.
- Real `describe(devforge_direct_codex)` returned `ok=true` and advertised `execute_task`. Its readiness `available=false, verified=false`, reason `direct_codex_containment_unproven`. These fields do not prove route refusal.
- Real `describe(devforge_runtime)` returned five bounded provider actions (`provision_scope, revalidate_scope, inspect_scope, terminalize_scope, execute_scoped`). No action was called.
- Source dispatcher `handlers/local_api.py` blob `5fab057318c11e7dd378cbb1daf89d677505a856` maps a configured external `policy.local_apis[name]` ahead of the builtin. Provider `handlers/direct_codex.py` blob `9fb4765bed432bf06a83fb50167e721a751c1ace` verifies builtin admission before payload validation. The live builtin is **not currently disabled** by effective policy.
- No verified loaded policy alias inventory or safe same-generation negative test disposition was available. A `call` with `params={}` is expressly forbidden by Plan R2; `invalid_payload` would not prove non-reachability.

**G3 result: `ExternalAliasOrNegativeProbeUnproven`.** The observed two builtin endpoints do not prove complete no-alias coverage or denial. No negative test executed.

## G4 — Host-owned mutation transport and rollback (BLOCKED)

- Structured `sentinel_service_status(service=sentinelx)` returned `Running` and `is_active=true`. The agent lists service actions `status, restart, is-active`; a read attempt for `is_enabled` was denied with `service_action_not_allowed`, safely left unchanged.
- The Host exposes policy-controlled file operations and service restart in its capabilities; this is **not** permission to edit active config or restart the service under S01. An exact Host-owned policy-edit transport, config parse/CAS digest, no-concurrent-editor/lease, safe non-reenabling rollback, service generation binding and independently approved owner authority remain unverified.
- No `sentinel_edit`, restart/reload, PowerShell, script, new scope, sandbox change, default binding migration or caller-selected path operation was issued.

**G4 result: `HostMutationTransportUnproven`.**

## G5 — zero-execution proof channels (BLOCKED)

- Baseline Windows Sandbox/Audit self-check advertises suspended spawn audit before resume, Job no breakaway and durable flush verified; these are readiness checks, **not this S01's Direct Codex process-creation/non-mutation evidence**.
- No policy-admitted exact process-creation event ledger, short-lived child capture receipt, pre/post workspace/Git content snapshot, credential-access audit or valid negative-call evidence has been read back.
- S01 itself requested no process spawn or Host mutation; that action log is not a physical `zero Codex processes spawned` proof.

**G5 result: `NoSpawnOrWorkspaceProofUnavailable`.**

## G6 — security substrate (PARTIAL, remains HOLD)

- `host_mutation_sandbox_v1.verified=true`, `pre_execution_audit_lineage_v1.verified=true` on live Host.
- `canonical_repository_mutation_firewall_v1.verified=false`, `effective_surface_ready=false`, reason `local_api:direct_codex_containment_unproven`.
- `development_host.direct_codex_v1.verified=false` for the same unproven containment.
- Structured `locations.devforge_workspace_root.path`: `D:\coco`; this remains protected. No ACL/protected-root edit performed.
- Firewall remains fail closed. No `PASS` claimed or forced.

**G6 result: `SecurityReadinessOrCoverageUnverified` (Firewall FAIL; Sandbox/Audit PASS).**

## G7 — task transport and no-replay (PASS at preflight; publishing requires final readback)

- Original PR #29 and Approved Plan R2/Task/Slice Set identities matched exactly at admission. SentinelX canonical main remained `2e5c69a112323867ee01783521554c43ebd731be`, DevForge main `047df4f1c45ce9099ec112017063751243c78d7b`.
- No external Host-side mutation, other Task/PR branch write, PR #14 replay, PR #19 rewrite, PR #20 activation, repo/DevForge binding change, or canonical main modification was requested.
- Evidence-only files and Run/Attempt/Checkpoint are persisted to the **same PR #29** and must be independently read back after commit. Until then, no persistence claim.

## S01 decision and strict continuation guard

```yaml
run_disposition: BLOCKED
slice_state: pending
owner_preflight_ready_for_separate_plan_review: false
owner_security_disposition: DecisionRequired/Blocked
consumer_dependency_gate: ConsumerDependencyOwnerGateUnresolved
effective_policy_gate: PolicyEffectiveStateUnverified
external_route_and_probe_gate: ExternalAliasOrNegativeProbeUnproven
host_mutation_transport_gate: HostMutationTransportUnproven
process_creation_proof_gate: NoSpawnOrWorkspaceProofUnavailable
canonical_firewall: FAIL
negative_call_performed: false
host_mutation_performed: false
S01_completion_receipt_generated: false
S02_S03_S04_authorized: false
mrs01: HOLD
```

**Single recommended Owner action:** Supply a narrow, independently authorized **Host policy + affected-consumer attestation packet** bound to this exact Host and DevForge `main`: secret-free effective `direct_codex.enabled`, all configured Direct Codex aliases, policy generation/digest, consumer migration-or-explicit-HOLD disposition, and availability of safe mutation/negative-probe/process-create audit mechanisms. This action requests evidence/decision only; it grants no new Host mutation or negative-call authority. Then re-read the current PR #29 S01 checkpoint before any further work.
