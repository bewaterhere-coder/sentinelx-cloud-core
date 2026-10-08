# Scoped PowerShell AppContainer Initialization Recovery V1 — Provisional Transport

Status: provisional; no canonical Task ID until GitHub Draft PR is created.

Repository: bewaterhere-coder/sentinelx-cloud-core
Base: main@8d2bafba87b529fb458faaa7fbdce39fe225361f
Source architecture: PR-021 Minimal Runtime Boundary (done).
Provisional slug: scoped-powershell-appcontainer-initialization-recovery-v1

## Observed failure

`devforge_runtime.provision_scope` passes, while `devforge_runtime.execute_scoped` with `execution_profile=scoped_mutation` and `interpreter=powershell` raises `HostMutationSandboxUnavailable` and reports `powershell could not initialize inside the required AppContainer`.

Current `scoped_script.py` checks for missing `returncode.txt` and loses the raw child process exit code in this failure branch. This observation does NOT establish DLL, Session-0, ACL, PowerShell runtime or profile root cause.

## Safety boundary

Diagnostic-first only. No code mutation before approved plan. Keep AppContainer, no-breakaway Job, MutationScope, canonical firewall, durable audit and closure; no unrestricted fallback or `D:\coco` protected-root permission expansion. No PR-018 Unity repair replay.

## Next step

Obtain PR identity, persist evidence-gated Requirement, review/plan, and diagnose raw Windows child status under a real Windows Host before admitting any compatibility fix.
