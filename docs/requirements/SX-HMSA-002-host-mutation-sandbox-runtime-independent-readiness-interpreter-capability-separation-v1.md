# SX-HMSA-002 — Host Mutation Sandbox Runtime-Independent Readiness & Interpreter Capability Separation V1

## State

```yaml
project_id: sentinelx-cloud-core
task_id: SX-HMSA-002
title: Host Mutation Sandbox Runtime-Independent Readiness & Interpreter Capability Separation V1
development:
  stage: plan_review
  gates:
    requirement_ready: true
    plan_approved: false
    acceptance_approved: false
    completion_verified: false
  next_expected_actor: reviewer
transport:
  type: github-pr
  pr_number: null
  branch: task/sx-hmsa-002-runtime-independent-readiness-interpreter-capability-separation-v1
  base_branch: main
artifacts:
  plan: docs/plans/SX-HMSA-002-host-mutation-sandbox-runtime-independent-readiness-interpreter-capability-separation-v1-plan.md
related_tasks:
  - SX-HMSA-001
  - PR-005-provider-capability-release-runtime-activation-v1
```

## Requirement Source

Follow-up to `SX-HMSA-001` after real Windows runtime activation of the merged provider implementation.

`SX-HMSA-001` successfully established the security-critical Host mutation boundary: provider-owned scope authority, durable pre-spawn audit, AppContainer exact-workspace ACLs, suspended Job-contained process creation, no-breakaway containment, and terminal residual-authority cleanup.

During live activation, however, capability readiness remained unavailable even after the security primitives themselves passed. The failure was isolated to the readiness probe's selected Python runtime.

Observed live evidence:

```text
host_mutation_sandbox_v1.available = false
pre_execution_audit_lineage_v1.available = false

checks.windows = true
checks.policy_enabled = true
checks.placement_store = true
checks.scope_store = true
checks.audit_durable_flush = true
checks.evidence_store = true
checks.appcontainer_acl = true
checks.job_no_breakaway = true
checks.suspended_spawn_audit_before_resume = true
checks.runtime_read_execute = false

readiness child exit = 0xC0000135  # STATUS_DLL_NOT_FOUND
```

The same failure reproduced after selecting the base Python executable rather than the service virtual-environment launcher. This proves that optional interpreter runtime health is currently conflated with the Host sandbox security boundary.

## Problem

Current `mutation_readiness.py` proves `host_mutation_sandbox_v1` by launching the agent's Python runtime inside the mutation AppContainer and asking that Python process to create `SELF_CHECK_OK`.

That design couples two different facts:

1. **Security-plane readiness** — whether SentinelX can enforce provider-owned scope, exact workspace authority, durable pre-execution audit, AppContainer containment, Job containment and terminal authority cleanup.
2. **Interpreter-plane readiness** — whether one particular Python/PowerShell/pwsh runtime can successfully load and execute inside that sandbox on the current Host.

A loader/runtime failure such as `STATUS_DLL_NOT_FOUND` currently makes the entire sandbox capability unavailable even when all security-plane checks pass.

This is too coarse. It prevents DevForge from using another verified scoped interpreter and makes a Python packaging/runtime problem indistinguishable from a broken security boundary.

## Goal

Separate Host mutation **security readiness** from scoped **interpreter readiness** while preserving fail-closed semantics.

The required invariant is:

> A Host sandbox capability proves only the Host-enforced mutation boundary. An interpreter capability proves only that an exact interpreter runtime can execute inside that already-proven boundary. Failure of one interpreter must never weaken the sandbox and must not falsify an otherwise verified sandbox.

## Required Capability Boundary

### Security-plane capabilities

The existing DevForge-required capabilities remain:

```text
host_mutation_sandbox_v1
pre_execution_audit_lineage_v1
```

`host_mutation_sandbox_v1.available = true` requires successful proof of:

- Windows V1 platform and required AppContainer/ACL/Job primitives;
- enabled valid Host mutation policy;
- provider-owned placement/scope stores;
- durable mutation evidence/audit START path;
- exact workspace AppContainer authority;
- suspended spawn + no-breakaway Job containment;
- an OS-baseline, provider-controlled in-sandbox workspace write/read-back probe that does **not** depend on a user-selectable Python/PowerShell/pwsh runtime;
- exact scope terminalization;
- non-active terminal read-back;
- no residual Job/process/AppContainer workspace authority.

`pre_execution_audit_lineage_v1` remains bound to the same security-plane readiness and must not become available when the durable audit boundary cannot be proven.

### Interpreter-plane capability

Expose a separate provider feature:

```text
scoped_mutation_interpreters_v1
```

Equivalent capability evidence:

```yaml
execution_features:
  scoped_mutation_interpreters_v1:
    available: true | false
    interpreters:
      python3:
        available: true | false
        verified: true | false
        reason: <stable diagnostic>
        runtime_identity: <provider-derived identity or null>
      powershell:
        available: true | false
        verified: true | false
        reason: <stable diagnostic>
        runtime_identity: <provider-derived identity or null>
      pwsh:
        available: true | false
        verified: true | false
        reason: <stable diagnostic>
        runtime_identity: <provider-derived identity or null>
```

Rules:

1. This feature is provider evidence; it does not redefine the DevForge consumer contracts in this task.
2. Each interpreter is verified independently inside the same security boundary.
3. One failing interpreter does not mark another interpreter unavailable.
4. One failing interpreter does not set `host_mutation_sandbox_v1.available = false` when the security-plane probe passes.
5. The aggregate `available` value means at least one scoped interpreter is verified; consumers must still use the selected interpreter's own entry.
6. Capability evidence must be derived from real Host execution/read-back, not executable presence alone.

## Runtime-Independent Windows Sandbox Probe

The sandbox self-check must not depend on the agent's Python installation, virtual environment, user-installed PowerShell Core, PATH resolution, or caller-selected interpreter.

For Windows V1, use a provider-controlled OS-baseline probe whose executable/argv are not caller supplied. A fixed `%SystemRoot%\\System32\\cmd.exe` probe is acceptable for V1 because it is part of the Windows baseline rather than one of the selectable scoped mutation runtimes.

The probe must:

1. use provider-derived exact workspace and scope authority;
2. persist durable `OPERATION_STARTED` before spawn;
3. create the process suspended;
4. bind it to the no-breakaway kill-on-close Job;
5. durably commit SPAWN evidence before resume;
6. perform a fixed write/read-back inside the exact workspace;
7. prove the process tree is quiescent;
8. terminalize the scope;
9. remove/revoke sandbox authority;
10. prove terminal non-active state and no residual authority.

Caller script text, caller executable path and arbitrary shell fragments are forbidden in this security-plane probe.

If the OS-baseline probe itself cannot execute or write inside the exact sandbox, the sandbox remains unavailable. There is no unrestricted fallback.

## Interpreter Discovery and Verification

Interpreter selection remains provider-owned.

A caller may request the logical interpreter name already supported by `script_run`:

```text
python3
powershell
pwsh
```

The caller must not gain authority to choose an arbitrary absolute executable path.

Provider resolution requirements:

1. resolve a bounded candidate set from Host-owned runtime/configuration state;
2. canonicalize each candidate to its final executable path before verification;
3. require the runtime's read/execute closure to be covered by Host-owned policy or Windows baseline authority;
4. execute a fixed provider-owned no-op/write-read-back verification inside an admitted sandbox scope;
5. record exact exit status and stable diagnostic evidence;
6. cache only against a key that includes current mutation policy, runtime identity/final path and relevant runtime-read policy;
7. invalidate/recompute on policy/runtime identity drift;
8. never reinterpret executable presence as verified runtime availability.

Python discovery must not assume that `sys.executable` is the correct sandbox runtime. `sys._base_executable`, the service venv launcher or any discovered Python candidate may be considered only as provider-derived candidates and must pass the actual in-sandbox verifier before becoming available.

## Scoped Mutation Admission

For `execution_profile = scoped_mutation`:

1. security-plane sandbox readiness must be verified;
2. the requested logical interpreter must have a current verified interpreter capability;
3. execution must bind to the exact verified executable identity used by the interpreter verifier;
4. executable identity drift between verification and START/spawn fails closed;
5. interpreter failure returns a named interpreter error and never falls back to another interpreter unless the caller explicitly requested that other logical interpreter in a new operation;
6. interpreter failure never falls back to `operator_unrestricted` or `legacy_unrestricted_compat`;
7. normal-user Git credentials remain outside the mutation sandbox.

## Diagnostics and Failure Semantics

Add stable equivalents for:

```text
HostMutationInterpreterUnavailable
HostMutationInterpreterVerificationFailed
HostMutationInterpreterBindingMismatch
```

Interpreter diagnostics must preserve useful loader/exit information when available, including unsigned 32-bit Windows process exit codes such as:

```text
0xC0000135
```

The readiness path must not discard the child exit code before constructing the failure reason.

Security-plane failures continue to use the existing Host mutation sandbox/audit failure classes and remain fail-closed.

## Capability Advertisement Semantics

Capability advertisement must make the boundary explicit.

Example expected state when Python fails with `0xC0000135` but the sandbox and PowerShell are valid:

```yaml
host_mutation_sandbox_v1:
  available: true
  verified: true

pre_execution_audit_lineage_v1:
  available: true
  verified: true

scoped_mutation_interpreters_v1:
  available: true
  interpreters:
    python3:
      available: false
      verified: false
      reason: "... exit_code=0xC0000135 ..."
    powershell:
      available: true
      verified: true
```

The provider must not claim that Python is available merely because the sandbox is available.

## Regression Requirements

Add a canonical regression for the live activation defect:

```text
SX-HMSA-002-R1-INTERPRETER-FAILURE-DOES-NOT-FALSIFY-SANDBOX
```

It must prove:

- security-plane native probe passes;
- Python verifier returns a deterministic simulated/fixture loader failure equivalent to `0xC0000135`;
- `host_mutation_sandbox_v1` remains available;
- `pre_execution_audit_lineage_v1` remains available;
- `python3` interpreter capability is unavailable with diagnostic evidence;
- another verified interpreter can remain independently available;
- attempting scoped Python execution fails before unverified Python execution is admitted;
- there is no unrestricted fallback.

Existing `INCIDENT-20260927-D-ROOT-RECURSIVE-DELETE` regression remains authoritative and must continue to pass.

## Acceptance Criteria

V1 is accepted only when evidence proves all of the following:

1. Sandbox readiness no longer invokes Python, PowerShell or pwsh as the selectable interpreter under test.
2. Windows sandbox readiness still performs a real in-sandbox write/read-back under AppContainer + exact ACL + no-breakaway Job containment.
3. Durable START precedes probe spawn and SPAWN evidence precedes resume.
4. Scope terminalization and residual-authority read-back remain mandatory before security readiness is successful.
5. `host_mutation_sandbox_v1` is available when the security-plane probe passes even if `python3` verification fails.
6. `pre_execution_audit_lineage_v1` remains bound to security-plane readiness, not to one interpreter runtime.
7. `scoped_mutation_interpreters_v1` reports independent verified state for `python3`, `powershell`, and `pwsh`.
8. Interpreter availability is based on actual sandbox execution/read-back, not file existence or PATH discovery alone.
9. A selected scoped interpreter binds execution to the exact verified executable identity; drift fails closed.
10. An unavailable interpreter returns a stable interpreter-specific failure and spawns no unverified scoped process.
11. `0xC0000135` or equivalent non-zero Windows exit evidence is preserved in diagnostics rather than collapsing to a missing-marker secondary error.
12. Interpreter failure never causes fallback to another interpreter, `operator_unrestricted`, legacy unrestricted execution, LocalSystem authority, or unsandboxed process creation.
13. Existing Host scope/audit/AppContainer/Job/terminalization tests remain passing.
14. Canonical destructive-escape regression remains passing with all protected sentinels unchanged.
15. Capability tests prove that sandbox security readiness and interpreter readiness can vary independently.
16. Documentation/config guidance explains the separation and how operators diagnose an unavailable interpreter without disabling the sandbox.
17. No DevForge consumer contract change is required to complete this provider task.
18. `PR-005-provider-capability-release-runtime-activation-v1` remains a separate release/activation concern; this task does not hard-code a release version, host, install path, workspace path or interpreter path.

## Non-Goals

- Weakening AppContainer, ACL, Job, scope, audit or terminalization requirements.
- Making Python 3.14 or any particular Python distribution universally AppContainer-compatible.
- Automatically installing missing DLLs/runtimes on a Host.
- Allowing caller-selected arbitrary executable paths.
- Adding unrestricted fallback when an interpreter fails.
- Changing DevForge consumer semantics in this task.
- Replacing the generic release/runtime-activation work tracked separately by `PR-005-provider-capability-release-runtime-activation-v1`.
