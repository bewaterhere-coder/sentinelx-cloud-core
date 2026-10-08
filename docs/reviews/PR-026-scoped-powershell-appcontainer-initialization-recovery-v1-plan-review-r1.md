# PR-026 — SentinelX Scoped PowerShell AppContainer Initialization Recovery V1 — Plan Review R1

## Review State

~~~yaml
task_id: PR-026-scoped-powershell-appcontainer-initialization-recovery-v1
review_target: plan
requirement_revision: 1
requirement_blob_sha: 2b50d5ea66e0d6719880c03180658556b21a31ca
plan_revision: 1
plan_blob_sha: e3288e6db607ba4365f3056719e41a17e34cc6b9
reviewed_task_head: 4fa5f4f481f226425719a8eb8a913ef89541f1ad
result: Approved
approved_scope: S01_diagnostic_only
held_scope: [S02, S03]
runtime:
  devforge_version: "2.103.0"
  devforge_revision: ebc25425160790950bd4d4500186652d3bf52416
  command_registry_source: system/command-registry.yaml@ebc25425160790950bd4d4500186652d3bf52416
repository_reality:
  canonical_main: 2e5c69a112323867ee01783521554c43ebd731be
  canonical_pr: 26
  canonical_branch: task/scoped-powershell-appcontainer-initialization-recovery-v1
next_gate: implementation
next_expected_actor: implementer
~~~

## Decision

**Approved — S01 diagnostic scope only. S02/S03 remain HOLD.**

Plan R1's diagnose-before-mutation structure is accepted:

1. S01 (read-only evidence acquisition plus, only if indispensable, strictly
   fail-closed exit/status observability repair) is technically feasible,
   bounded, reversible and independently verifiable on the real Windows Host.
2. No PowerShell compatibility workaround is approved. S02 requires a
   separate Plan Revision (R2) with evidence-proven fault class, exact target
   lines, least-authority delta and A/B comparator design, followed by a new
   `#开发评审` gate before any product mutation.
3. S03 real-Host acceptance stays blocked behind the approved R2 Slice Set.
4. Boundary preservation is mandatory: AppContainer, no-breakaway Job,
   MutationScope, canonical repository firewall, durable audit; no
   unrestricted PowerShell fallback; no `D:\coco` protected_root permission
   expansion; no PR-018 Unity repair replay.

## Host and Repository Reality Verification (at review time)

- Canonical remote `main`: `2e5c69a112323867ee01783521554c43ebd731be`
  (119 commits ahead of the stale local canonical checkout `cd42e37`; the
  local checkout remains `main + clean` and was not advanced).
- Installed Host: `0.24.1.dev791+g5d9286b22` (service `SentinelX`,
  `C:\ProgramData\SentinelX`). Blob-parity vs `main@2e5c69a1` for the five
  key sources — all **byte-identical (PASS)**:
  - `handlers/scoped_script.py` = `4580475ba9bd`
  - `winspawn.py` = `b13bc310a731`
  - `mutation_sandbox.py` = `9f419cf59781`
  - `mutation_scope.py` = `1a6dce6d066c`
  - `mutation_audit.py` = `f6bbbf15aeab`
- Execution workspace materialized as an independent clone:
  `pr026-s01-a1` on `task/scoped-powershell-appcontainer-initialization-recovery-v1`
  @ `4fa5f4f481f226425719a8eb8a913ef89541f1ad`, clean. Not a worktree of the
  canonical checkout; canonical checkout untouched.
- Existing audit-journal evidence (read-only) confirms the Plan R1 §1
  observation: failed scoped-PowerShell operations persist
  `error_code=HostMutationSandboxUnavailable` with **no returncode**, and
  spawn succeeds inside the AppContainer before the silent child exit.

## Runtime Refresh

Plan R1 was created against DevForge `2.103.0` semantics; at review time the
canonical DevForge `main` is:

~~~text
2.103.0 @ ebc25425160790950bd4d4500186652d3bf52416
~~~

The command registry used for dispatch was read from that exact revision
(single-revision control plane; no mixed-revision anchors).

## Review Outcome

- Plan R1: **Approved** for the S01 slice defined by
  `docs/execution/PR-026-scoped-powershell-appcontainer-initialization-recovery-v1-slices.yaml`.
- S01 completion must return raw process exit status (decimal DWORD and
  `0x%08X`), startup-stage classification, Windows event query results,
  AppContainer/Job/audit identity and terminalization evidence, or explicit
  negative readback where evidence is unavailable.
- If no definitive root cause is proven, S01 must stop `BlockedByEvidence`
  — no workaround, no compatibility fix.

Canonical next action:

~~~text
#开发执行 PR-026-scoped-powershell-appcontainer-initialization-recovery-v1
~~~
