---
task_id: PR-026-scoped-powershell-appcontainer-initialization-recovery-v1
title: SentinelX Scoped PowerShell AppContainer Initialization Recovery V1 — Plan R1
plan_revision: 1
plan_state: proposed
requirement_revision: 1
project_id: sentinelx-cloud-core
repository: bewaterhere-coder/sentinelx-cloud-core
transport:
  type: github-pr
  pr_number: 26
  branch: task/scoped-powershell-appcontainer-initialization-recovery-v1
  base_branch: main
review:
  status: pending
  next_command: "#开发评审 PR-026-scoped-powershell-appcontainer-initialization-recovery-v1"
implementation_authorized: false
---

# Plan R1 — Diagnose Before Compatibility Mutation

## 1. Baseline and authority

- Exact initial remote base: `main@8d2bafba87b529fb458faaa7fbdce39fe225361f`; check latest `main` SHA at each real execution gate.
- Installed Host: `0.24.1.dev791+g5d9286b22`, actual code revision `5d9286b22`; four key source blobs equal to remote `main` at initial admission.
- Frozen boundary: `docs/architecture/sentinelx-minimal-runtime-boundary-v1.md` from completed PR-021.
- PR-018/PR-017/PR-011 are regression/security references, **not** permission to replay Unity or extend generic Session-0 grants.
- Host sandbox self-check PASS is a base-infrastructure observation, not a scoped-PowerShell PASS.
- Existing `execute_scoped` failure text is weaker than raw process evidence. The current `result_path.exists()` failure branch lacks raw exit-code retention.
- Current Host exposes `devforge_runtime` scoped actions but denies unprofiled `sentinel_script_run` with `execution_profile_required`. This is an intended security limit. No unrestricted host execution is admitted.

## 2. Change-control decision

**R1 authorizes diagnostic collection and (only if indispensable) strictly fail-closed exit/status observability repair.** It does **not** approve a speculative PowerShell compatibility workaround. A compatibility fix requires S01 diagnosis evidence, precise target/authority change inventory, and a **Plan Revision + Plan Review** gate before product mutation.

DevForge one-execute/one-slice semantics apply. Completed diagnostic slices are immutable evidence; never replay them to work around a later gate.

## 3. Evidence acquisition sequence

1. Read latest `main`, PR #26, exact installed agent revision and DevForge Task/Plan.
2. Read original failure lineage through existing audit/evidence store (when authorized), including exact `scope_ref`, lineage, START/SPAWN/FINISH, Job/PID, terminalization and preserved raw child exit status, if any. Read relevant Windows crash/security event IDs, process image path/bitness, policy and ACL facts through authorized **read-only** projection. Redact identities/secret environment values.
3. Check whether `GetExitCodeProcess` already produces original exit status. In `winspawn.py` `AppContainerJobProcess.exit_code` is available; inspect `ManagedMutationProcess` access patterns, process lifetime and existing audit serialization before planning any code write.
4. If raw status unavailable, add **only** a fail-closed startup-failure diagnostic field to scoped error/finish evidence, sampled **before** scope terminalization closes process handles. Preserve timeout/normal-exit branches and child result marker semantics. Format unsigned DWORD and `0x%08X` without replacing the code with -1 or falsely asserting a script-level return code. No additional AppContainer rights.
5. Run a harmless real Windows scoped PowerShell probe with exact accepted noncanonical mutation workspace/lineage. Record raw code, whether runner reached script, Windows events and audit closure even on failure. Do not use shell/script fallback outside AppContainer as a substitute for a scoped PASS.
6. Correlate fault classes with discriminators:
   - Runtime/image: `powershell.exe` path/resolution, executable alias, version/bitness, base runtime; test exact binary and `pwsh` separately only when installed/admitted.
   - Session-0: compare observed WinSta/desktop ACE/read access against the already-introduced **exact minimum** generic capability; negative control if authorization already correct.
   - ACL: trace only denied specific file/registry/runtime object against AppContainer SID; reject broad-directory permissions.
   - Profile: workspace HOME/USERPROFILE/APPDATA/LOCALAPPDATA, initialized directories, startup side effects; `-NoProfile` disables scripts but not all CLR/runtime initialization.
   - Dependency/CLR: original NTSTATUS, fault module/event and missing runtime image; discriminate `0xC0000142` vs `0xC0000135` vs `0xC0000022` or others **only if actually observed**.
   - Lifecycle: SPAWN success, suspended->resumed, Job/no-breakaway, timeout and audit ordering; never equate CreateProcess success with runtime initialization success.
7. Persist evidence-only fault matrix, strongest disconfirmation and exact minimal target surface. If no definitive root cause, stop `BlockedByEvidence`; no workaround.

## 4. Proposed Slice / Gate structure

### S01 — Live evidence and fail-closed initialization diagnostics

**Scope:** read-only inspection, real Host evidence extraction, and conditional minimal diagnostic-observability patch. The patch may touch:
- `src/sentinelx_core/handlers/scoped_script.py`
- `src/sentinelx_core/windows_mutation_sandbox.py` (only if a read-only process exit accessor is necessary)
- `src/sentinelx_core/mutation_audit.py` (only if current audit contract needs a backwards-compatible optional raw exit field)
- focused regression tests under `tests/`, specifically startup-failure/terminalization/audit tests;
- Task-owned run/checkpoint/receipt under `docs/execution/`, `docs/checkpoints/`, `docs/reviews/`.

Forbidden: config modifications, `D:\coco` root ACL changes, PR-018 files, `scripts/Win32` privilege adjustments, direct Codex, Task transport changes, or new generalized execution surfaces.

**S01 completion receipt:** exact installed/build/branch revision; raw process code and hex or explicit negative readback evidence; runner marker presence; AppContainer+Job identity; audit operation ID; classification matrix; terminal state/readback; source diff and tests. A diagnostic-only change is not a claim of PowerShell recovery.

### S02 — Evidence-authorized minimal compatibility repair (separate Plan review required)

S02 **is not currently admitted for execution**. After S01, amend Plan R2 with:
- evidence-proven fault class and rejected alternatives;
- exact target lines and *least-authority* delta;
- failure/success A/B comparator design;
- test matrix and policy drift/ACL cleanup impacts.

Run `#开发评审` on R2 and freeze its Slice Set before running any S02 code mutation. If S01 reveals infrastructure/config prerequisite outside this Task's grant, record Blocked and do not force an in-task workaround.

### S03 — Real Windows Host acceptance and security regression

After S02 approval and verified implementation:
- `provision_scope` PASS for exact eligible workspace, repository, lineage;
- `execute_scoped(powershell)` executes `Write-Output 'SCOPED_PS_OK'`;
- `returncode==0`, output exact marker and `terminal_state` verified;
- enforce expected no-escape control, no-breakaway Job and AppContainer SID evidence;
- audit `START -> SPAWN -> FINISH`, scope terminalization, zero active process and ACL closure;
- canonical repo `main + clean`, unchanged `D:\coco` protected_root;
- unit tests for missing runner marker/timeout/native failure + PR-011/017/018 relevant regressions;
- model-facing actual `devforge_runtime` call, not local mock.

S03 also requires an approved R2 Slice Set before execution and does not confer acceptance on itself.

## 5. Plan Review focus / Decision Gate

The reviewer must assess:
1. Can the original process exit status be recovered without product mutation? If not, is S01 optional diagnostics instrumentation strictly least privilege and durable?
2. Are requirements specific enough to preserve a strict nonfallback, nonexpanding permission boundary?
3. Do S02 and S03 remain blocked until a root-cause-driven Plan revision passes review?
4. Does current main/host source parity, Task identity and PR #26 branch evidence hold?
5. Is a real Windows Host/receipt path available for later acceptance?

**Expected review outcome:** approve or reject **S01 diagnostic Plan R1 only**. No compatibility authority by inference.

## 6. Stop conditions

Stop and report `Blocked` or `Degraded` if original Windows evidence is inaccessible, installed candidate differs materially from reviewed source, exact workspace is not admitted, audit terminalization cannot be proven, process token/Job evidence is missing, or the only apparent fix is privileged shell fallback or protected-root ACL expansion.

No claim of functional completion before real Windows exit-0, containment, terminalization, audit and canonical clean readback receipts.
