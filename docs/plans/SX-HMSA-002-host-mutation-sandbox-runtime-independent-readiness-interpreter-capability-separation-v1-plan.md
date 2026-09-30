# SX-HMSA-002 — Implementation Plan

## Plan State

```yaml
task_id: SX-HMSA-002
stage: plan_review
requirement: docs/requirements/SX-HMSA-002-host-mutation-sandbox-runtime-independent-readiness-interpreter-capability-separation-v1.md
transport:
  type: github-pr
  pr_number: null
  branch: task/sx-hmsa-002-runtime-independent-readiness-interpreter-capability-separation-v1
  base_branch: main
plan_status: pending_review
plan_revision: 1
execution_state: not_started
acceptance_approved: false
completion_verified: false
next_expected_actor: reviewer
```

## Objective

Decouple SentinelX Host mutation **security readiness** from individual scoped interpreter **runtime readiness**.

After this plan:

- `host_mutation_sandbox_v1` proves provider-owned scope, durable audit, AppContainer exact ACL, no-breakaway Job containment, OS-baseline in-sandbox write/read-back, terminalization and residual-authority closure;
- `pre_execution_audit_lineage_v1` stays bound to that security-plane proof;
- `python3`, `powershell`, and `pwsh` are verified independently and reported through `scoped_mutation_interpreters_v1`;
- a Python loader failure such as `0xC0000135` makes Python unavailable without falsifying a valid Host sandbox;
- scoped execution admits only the exact verified executable for the requested logical interpreter and never falls back to unrestricted execution.

## Authoritative V1 Decisions

These decisions are fixed for implementation and must not be deferred to an execution slice.

1. **Sandbox readiness and interpreter readiness are separate state machines.** A sandbox probe may not use Python/PowerShell/pwsh as the selectable runtime being proven.
2. **Windows V1 security probe uses one provider-controlled OS-baseline executable.** Use `%SystemRoot%\\System32\\cmd.exe` with a fixed, provider-generated argv solely to prove in-sandbox workspace write/read-back. Caller input cannot alter this executable or command.
3. **The security probe still exercises the complete security lifecycle.** Durable START, suspended AppContainer spawn, no-breakaway Job bind, durable SPAWN-before-resume, marker read-back, process-tree quiescence, scope terminalization and residual-authority closure remain mandatory.
4. **Interpreter availability is proven by execution, not discovery.** File existence, `PATH`, `sys.executable` and `sys._base_executable` can only generate bounded provider candidates.
5. **Verified executable identity is authoritative for scoped execution.** A logical interpreter request binds to the exact final path/runtime identity that passed verification. Path drift between verification and execution fails closed.
6. **Interpreter failure is local to that interpreter.** No automatic fallback to another interpreter and no fallback to `operator_unrestricted`, legacy unrestricted execution or service identity.
7. **Current DevForge consumer contracts are not modified.** This task changes SentinelX provider truthfulness and admission behavior only.
8. **Release/runtime activation remains separate.** `PR-005-provider-capability-release-runtime-activation-v1` can publish/install this behavior later but does not own its semantics.
9. **The live `0xC0000135` defect becomes a regression fixture.** Diagnostics must retain the child exit code instead of collapsing to a secondary missing-marker error.

## Current Code Anchors

Primary current seams on canonical `main`:

```text
src/sentinelx_core/mutation_readiness.py
src/sentinelx_core/windows_mutation_sandbox.py
src/sentinelx_core/winspawn.py
src/sentinelx_core/handlers/basic.py
src/sentinelx_core/handlers/scoped_script.py
src/sentinelx_core/handlers/script.py
src/sentinelx_core/policy.py
```

Primary test seams:

```text
tests/test_windows_mutation_sandbox.py
tests/test_scoped_script_execution.py
tests/test_mutation_audit.py
tests/test_incident_20260927_d_root_recursive_delete.py
tests/test_capabilities_policy_evidence.py
```

Add focused tests/modules only where they reduce coupling. Do not duplicate scope, audit, AppContainer or Job authority in a second implementation.

## Design

### 1. Split readiness result models

Refactor the current readiness layer into two explicit result types, equivalent to:

```python
@dataclass(frozen=True)
class MutationSandboxReadiness:
    available: bool
    reason: str
    checks: dict[str, bool]

@dataclass(frozen=True)
class ScopedInterpreterReadiness:
    logical_name: str
    available: bool
    verified: bool
    reason: str
    runtime_identity: str | None
    executable_final_path: str | None
```

A small aggregate may hold the interpreter matrix, but its cache and success criteria must remain separate from `MutationSandboxReadiness`.

Security readiness cache key includes the mutation policy and security-placement state only.

Interpreter cache keys additionally include:

```text
logical interpreter name
resolved executable final path/runtime identity
runtime-read policy digest
security readiness identity/generation
```

A change to interpreter path/runtime identity invalidates only the affected interpreter proof plus any execution binding derived from it.

### 2. Security-plane probe

Replace the Python marker probe in `mutation_readiness.py` with a fixed Windows OS-baseline probe.

Provider constructs the executable from `SystemRoot` and resolves it to its final path before START:

```text
%SystemRoot%\System32\cmd.exe
```

Use a fixed provider-generated operation whose only material effect is creating a known marker under the exact activation workspace, e.g. conceptually:

```text
cmd.exe /d /q /c <fixed marker write>
```

Implementation requirements:

- no caller text is interpolated;
- the marker target is provider-derived from `activation.workspace`;
- final executable path and cwd are sealed in START intent;
- process is created suspended and Job-bound by the existing `WindowsMutationSandbox.spawn()` path;
- SPAWN is durable before resume;
- raw process exit status is captured before process handle release;
- non-zero exit is reported directly;
- marker is read back only after zero exit;
- terminalization executes even on probe failure where safe/possible;
- any inability to prove cleanup is a blocking residual-authority failure.

The existing scope/audit/sandbox implementation remains authoritative; do not create a parallel shortcut probe that bypasses those layers.

### 3. Preserve process exit evidence

The readiness defect exposed that `ManagedMutationProcess.wait()` releases the underlying process before callers can inspect the exit code.

Repair this through an explicit supported API rather than private-field use. Prefer one of:

```python
wait_result = process.wait_result(timeout_seconds)
# -> completed, exit_code, containment snapshot
```

or an equivalent contract that atomically captures exit/containment evidence before releasing handles.

Requirements:

- no readiness path reaches into `process._process`;
- exit code is represented as unsigned Windows process status where applicable;
- `0xC0000135` remains observable;
- the existing scoped-script result path preserves its current output/return-code behavior;
- process/Job handles are still closed exactly once.

### 4. Interpreter resolver and verifier

Introduce a provider-owned resolver/verifier seam, preferably a focused module such as:

```text
src/sentinelx_core/mutation_interpreters.py
```

Supported logical names remain:

```text
python3
powershell
pwsh
```

#### Python candidate resolution

Generate a bounded candidate list from provider/Host state. Candidates may include:

- `sys._base_executable` when present;
- `sys.executable`;
- bounded Host discovery such as `python3`/`python` when already supported by policy.

Rules:

- deduplicate by resolved final executable path;
- do not assume the service venv launcher is preferred;
- do not assume the base interpreter is usable;
- candidate must satisfy Host-owned runtime read/execute policy before verification;
- first candidate that passes a real sandbox verification becomes the verified binding;
- retain failure evidence for rejected candidates without exposing credential material.

#### Windows PowerShell

Resolve the Windows-baseline executable from a provider-controlled SystemRoot-derived path rather than caller PATH where possible:

```text
%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe
```

Still verify it inside the sandbox before reporting available.

#### PowerShell Core

`pwsh` is optional. Bounded provider discovery may use PATH/configured runtime state, but executable presence alone is not availability.

### 5. Interpreter verification scope

Interpreter verification must run through the same security sandbox implementation after security readiness is established.

Each verifier uses fixed provider-owned content with no caller script, sufficient to prove:

```text
executable loads
fixed code executes
workspace write/read-back succeeds
process exits normally
scope terminalizes
no residual authority remains
```

A verifier failure changes only that interpreter's capability entry unless it reveals a security-plane invariant failure. If it reveals scope/ACL/Job/audit/terminalization corruption, invalidate/fail the security readiness as well.

### 6. Capability advertisement

Update `handlers/basic.py` capability construction so it exposes:

```yaml
execution_features:
  host_mutation_sandbox_v1: <security readiness feature>
  pre_execution_audit_lineage_v1:
    <security readiness feature>
    bound_to: host_mutation_sandbox_v1
  scoped_mutation_interpreters_v1:
    available: <any interpreter verified>
    interpreters:
      python3: ...
      powershell: ...
      pwsh: ...
```

Do not hide interpreter failure reasons behind the sandbox `reason` field.

The capability endpoint must remain bounded: no script bodies, credentials or unrestricted environment dumps.

### 7. Scoped script admission

Refactor `_runner_argv()` / scoped execution admission in `handlers/scoped_script.py` so logical interpreter selection consumes the verified provider binding.

Required flow:

```text
logical interpreter requested
→ security readiness required
→ current interpreter verification/binding required
→ exact verified executable sealed into process intent
→ normal durable START / activation / suspended spawn / SPAWN / resume
```

Rules:

- Python execution does not independently pick `sys.executable` after verification;
- PowerShell/pwsh execution does not independently rerun unbounded `shutil.which()` after verification;
- final executable path is revalidated at execution admission;
- mismatch returns `HostMutationInterpreterBindingMismatch` before unverified execution;
- unavailable returns `HostMutationInterpreterUnavailable`;
- verifier failure returns/records `HostMutationInterpreterVerificationFailed` where appropriate;
- no profile downgrade or interpreter fallback.

## Incremental Execution Slices

The approved plan should compile into the following durable slice order.

### S01 — Readiness model separation and process-exit evidence

**Objective:** Separate security/interpreter readiness data models and expose a supported process wait/exit evidence contract.

Scope:

```text
src/sentinelx_core/mutation_readiness.py
src/sentinelx_core/windows_mutation_sandbox.py
src/sentinelx_core/winspawn.py
tests/test_windows_mutation_sandbox.py
```

Verification:

- security readiness result has no interpreter success dependency;
- process wait captures non-zero exit code before handle release;
- `0xC0000135` remains formatted/observable;
- no private `_process` access is required by readiness;
- handle/Job cleanup remains exactly-once and fail-closed.

Checkpoint required: yes.

### S02 — Windows OS-baseline sandbox probe

**Objective:** Replace Python-based sandbox self-check with the fixed provider-controlled Windows baseline probe.

Scope:

```text
src/sentinelx_core/mutation_readiness.py
src/sentinelx_core/windows_mutation_sandbox.py
src/sentinelx_core/mutation_audit.py
tests/test_windows_mutation_sandbox.py
tests/test_mutation_audit.py
```

Verification:

- sandbox probe never invokes selectable `python3`, `powershell`, or `pwsh`;
- fixed executable/argv/cwd are provider-derived and sealed before spawn;
- durable START precedes spawn;
- SPAWN precedes resume;
- marker write/read-back occurs only in exact workspace;
- non-zero native-probe exit blocks sandbox availability with exact exit evidence;
- terminal non-active and residual-authority absence are required for success.

Checkpoint required: yes.

### S03 — Interpreter verification, capability matrix and scoped admission

**Objective:** Independently verify Python/PowerShell/pwsh and bind scoped execution to exact verified runtime identity.

Scope:

```text
src/sentinelx_core/mutation_interpreters.py  # new if used
src/sentinelx_core/handlers/basic.py
src/sentinelx_core/handlers/scoped_script.py
src/sentinelx_core/policy.py
tests/test_scoped_script_execution.py
tests/test_capabilities_policy_evidence.py
```

Verification:

- three logical interpreter entries vary independently;
- Python `0xC0000135` fixture marks only Python unavailable;
- verified PowerShell may remain available;
- interpreter verification uses real sandbox execution/read-back;
- scoped execution uses the exact verified executable path;
- executable drift fails before unverified process admission;
- no fallback to another interpreter or unrestricted profile.

Checkpoint required: yes.

### S04 — Regression, documentation and release-consumption boundary

**Objective:** Lock the live defect regression and document the provider semantics without coupling this task to release execution.

Scope:

```text
tests/
README.md
SECURITY.md
THREAT_MODEL.md
config.example.windows.yaml
CHANGELOG.md
```

Verification:

- `SX-HMSA-002-R1-INTERPRETER-FAILURE-DOES-NOT-FALSIFY-SANDBOX` passes;
- existing `INCIDENT-20260927-D-ROOT-RECURSIVE-DELETE` regression remains passing;
- relevant SX-HMSA-001 Windows tests remain passing;
- docs distinguish security-plane capability from interpreter-plane availability;
- operator guidance does not recommend disabling sandbox/fail-closed behavior to make Python work;
- no host/version/install/workspace/interpreter path is hard-coded as product authority;
- `PR-005-provider-capability-release-runtime-activation-v1` can consume a later merged revision without semantic dependency in the opposite direction.

Checkpoint required: yes.

## Test Matrix

Minimum acceptance matrix:

| Security probe | Python | PowerShell | Expected sandbox | Expected interpreter matrix |
|---|---|---|---|---|
| PASS | PASS | PASS | available | python=true, powershell=true |
| PASS | `0xC0000135` | PASS | available | python=false, powershell=true |
| PASS | PASS | unavailable | available | python=true, powershell=false |
| PASS | fail | fail | available | aggregate interpreters=false |
| FAIL | PASS candidate exists | PASS candidate exists | unavailable | scoped execution blocked |
| audit START fail | any | any | unavailable | no process spawned |
| Job/ACL/terminalization fail | any | any | unavailable | no successful capability proof |

`pwsh` adds the same independent permutations where installed.

## Acceptance Evidence Required

Acceptance must include:

1. plan-revision-bound execution slice receipts;
2. targeted unit/integration test output;
3. real Windows evidence for the security-plane OS-baseline probe;
4. real or deterministic fixture evidence that `0xC0000135` is retained and only invalidates Python;
5. capability read-back showing security and interpreter states separately;
6. destructive escape regression evidence;
7. no-fallback regression evidence;
8. final source diff proving no DevForge consumer contract mutation in this task.

CI is useful evidence but is not the semantic completion authority. If repository CI is unavailable for billing/infrastructure reasons, acceptance may use equivalent reproducible Host test evidence with explicit classification.

## Risks and Controls

### Risk — `cmd.exe` becomes a hidden general shell fallback

Control: the OS-baseline probe is an internal fixed executable + fixed argv path only. It is not exposed as caller script execution and is never selected as a fallback interpreter.

### Risk — interpreter verifier weakens sandbox by broadening runtime ACLs

Control: runtime read roots remain Host-owned policy. Verifier may consume them but cannot add caller-selected roots or widen write authority.

### Risk — stale verification is reused after runtime replacement

Control: cache identity includes resolved final executable/runtime identity and relevant policy digest; admission performs final-path revalidation.

### Risk — sandbox reports available but no usable interpreter exists

Control: `scoped_mutation_interpreters_v1.available = false` is explicit. Scoped `script_run` fails with `HostMutationInterpreterUnavailable`; the sandbox remains truthfully available as a security primitive.

### Risk — security failure is mislabeled as interpreter failure

Control: scope/audit/AppContainer/Job/terminalization violations remain security-plane failures and invalidate sandbox readiness, even when encountered during interpreter verification.

## Non-Goals

- Solving every Python DLL/AppContainer compatibility issue.
- Automatically installing runtimes or Visual C++ redistributables.
- Replacing AppContainer + exact ACL + Job containment.
- Adding Linux/macOS scoped mutation support.
- Changing DevForge consumer contracts.
- Completing the separate provider release/runtime-activation task.
