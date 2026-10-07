# PR-017 Large Runtime Root ACL Cleanup Timeout & Recovery V1 — Plan

## Status

```yaml
task_id: PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1
plan_revision: 1
plan_status: ready_for_review
implementation_authority: false
requirement_ref: docs/requirements/PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1.md
transport:
  type: github-pr
  pr_number: 17
  branch: task/large-runtime-root-acl-cleanup-timeout-recovery-v1
  base: main
```

## Plan Objective

Repair the fixed 20-second Windows runtime-root ACL boundary without weakening the AppContainer security model.

The implementation should make runtime ACL duration provider-owned and bounded, close the partial-grant ambiguity, preserve the existing revoked/terminal lifecycle, and prove the fix against a real large runtime root.

## Technical Decision

Treat this as a **runtime-root ACL lifecycle reliability** defect inside the existing `WindowsMutationSandbox`.

Do not redesign `execute_scoped`, scope identity, Job containment or AppContainer authority.

Preferred model:

```text
Host policy
  runtime_acl_timeout_seconds
          ↓
runtime root ACL grant/remove
          ↓
timeout translated to sandbox-domain failure
          ↓
partial grant compensation
          ↓
revoked until residual authority closure
          ↓
retryable terminalization
```

## Planned Changes

### 1. Policy surface

Update `src/sentinelx_core/policy.py`.

Add:

```python
runtime_acl_timeout_seconds: int = 20
```

Parse only from `mutation_execution`.

Validate a bounded integer range. Plan default:

```text
5 <= runtime_acl_timeout_seconds <= 600
```

No request-level override.

Update `config.example.windows.yaml` with the optional setting and explain that large immutable runtime roots may require a larger bounded value.

### 2. Policy identity / drift

Update `src/sentinelx_core/mutation_placement.py`.

Include the timeout in the mutation placement policy digest so future scope admission observes Host policy drift.

Do not prevent cleanup of already-issued scopes when policy changes; retain the existing stale-policy cleanup semantics in `terminalize_scope()`.

### 3. ACL runner timeout contract

Update `src/sentinelx_core/windows_mutation_sandbox.py`.

Refactor `_run_icacls()` so timeout is explicit at the runtime-root call site rather than hard-coded.

Preferred shape:

```python
_run_icacls(args, *, timeout_seconds=...)
```

Requirements:

- catch `subprocess.TimeoutExpired`;
- convert it to deterministic sandbox error;
- include operation/root/timeout context at the caller boundary;
- preserve current non-zero return-code handling;
- do not expose raw sensitive environment state.

Keep unrelated PR-011 verification toolchain ACL timeout semantics unchanged unless helper compatibility requires an explicit default.

### 4. Runtime grant compensation

Refactor `_grant_runtime_read()`.

Current risk:

```text
icacls grant starts
→ Windows partially propagates inheritable ACE
→ process times out
→ call raises before root is recorded in granted_runtime
→ rollback list may not include the attempted root
```

New behavior:

```text
attempt exact root grant
→ on any timeout/failure
→ attempt exact SID removal from same root
→ read back/return deterministic closure result
→ if cleanup ambiguous, fail closed as residual authority
```

The activation rollback path should not depend solely on "successfully appended roots" for the currently-attempted root.

Do not remove unrelated ACL entries.

### 5. Runtime cleanup recovery

Refactor `_remove_runtime_read()` only as needed to:

- use configured timeout;
- classify timeout/cleanup failure as residual-authority ambiguity;
- preserve exact SID removal semantics.

Do not mark scope terminal on cleanup failure.

Reuse the existing `MutationScopeStore.terminalize_scope()` retry behavior; do not add a new state.

### 6. Focused tests

Primary tests:

```text
tests/test_policy.py
tests/test_mutation_scope_admission.py or existing policy-digest coverage
tests/test_windows_mutation_sandbox.py
```

Add focused cases for:

1. default timeout;
2. valid configured timeout;
3. invalid low/high/non-integer timeout;
4. policy digest changes when timeout changes;
5. runtime grant receives configured timeout;
6. runtime cleanup receives configured timeout;
7. `TimeoutExpired` becomes deterministic sandbox error;
8. grant timeout invokes compensating removal on exact attempted root;
9. compensation failure preserves fail-closed residual-authority semantics;
10. cleanup timeout leaves scope revoked;
11. retry terminalization succeeds and reaches terminal;
12. successful closure removes exact AppContainer SID.

Use monkeypatch/fakes for deterministic timeout tests; do not make ordinary unit tests wait hundreds of seconds.

### 7. Real Windows physical proof

After focused tests pass, run a real Host proof.

Recommended Host config:

```yaml
mutation_execution:
  runtime_acl_timeout_seconds: 300
  runtime_read_roots:
    - C:\ProgramData\SentinelX\.venv
    - C:\Python314
    - C:\Windows\System32\WindowsPowerShell\v1.0
    - C:\Program Files\Unity\Hub\Editor\6000.6.4f1
```

Proof sequence:

```text
A. execute_scoped python3 marker
   → PASS
   → terminal

B. execute_scoped powershell marker
   → expected runtime result
   → cleanup terminal

C. execute_scoped python3
   → subprocess Unity.exe batch/version probe
   → Unity process initializes
   → cleanup completes
   → terminal

D. icacls/readback
   → exact test AppContainer SID absent from Unity runtime root
```

If Unity itself exposes a separate AppContainer compatibility blocker after ACL cleanup is fixed, record that as a distinct downstream limitation rather than broadening this Task.

### 8. Regression closure

Run at minimum:

```text
python -m pytest -q tests/test_policy.py
python -m pytest -q tests/test_mutation_scope_admission.py
python -m pytest -q tests/test_windows_mutation_sandbox.py
python -m pytest -q tests/test_scoped_script_execution.py
python -m pytest -q tests/test_verification_readiness.py
python -m pytest -q tests/test_verification_scoped_execution.py
```

Then run the repository's affected Windows mutation/security regression set.

## Expected Files

Primary:

```text
src/sentinelx_core/policy.py
src/sentinelx_core/mutation_placement.py
src/sentinelx_core/windows_mutation_sandbox.py
tests/test_policy.py
tests/test_windows_mutation_sandbox.py
config.example.windows.yaml
```

Possible only when existing test organization requires it:

```text
tests/test_mutation_scope_admission.py
tests/test_scoped_script_execution.py
```

No protocol schema change is expected.

## Slice Proposal

Plan Review should compile the canonical Slice Set. Recommended decomposition:

```text
S01 — policy + digest + runtime ACL timeout/error semantics + focused tests
S02 — partial-grant compensation + revoked/retry recovery regression closure
S03 — real Windows large-runtime-root proof + affected security regressions
```

No Slice is authorized until Plan Review approves this Plan and persists the canonical Execution Slice Set.

## Risks

### RSK-1 — timeout increase hides an unbounded operation

Mitigation: bounded Host policy, explicit maximum, exact operation scope, real timing evidence.

### RSK-2 — grant timeout leaves residual authority

Mitigation: compensate the currently-attempted root even when grant never returned success; fail closed if cleanup cannot be proven.

### RSK-3 — cleanup timeout incorrectly publishes terminal

Mitigation: preserve existing two-phase `revoked -> cleanup -> terminal`; add explicit timeout/retry regression.

### RSK-4 — policy change invalidates cleanup of old scope

Mitigation: include timeout in policy identity for future admission while preserving existing stale-policy terminal cleanup rule.

### RSK-5 — large Unity tree still exceeds configured bound

Mitigation: real timing evidence and bounded operator choice up to the approved maximum. If 600 seconds is insufficient, treat it as a separate design problem rather than removing the bound.

## Plan Review Questions

1. Is a provider-owned bounded timeout the smallest correct fix for large immutable runtime roots?
2. Should the V1 range remain 5–600 seconds?
3. Is timeout correctly part of the Host mutation policy digest?
4. Does partial-grant compensation close the current rollback ambiguity?
5. Is cleanup timeout correctly classified as residual-authority ambiguity?
6. Does the existing revoked/retry terminalization already satisfy recovery without a new state?
7. Are PR-011 verification-toolchain ACL semantics intentionally unchanged?
8. Does real Unity-root proof sufficiently exercise the original incident without making Unity a permanent SentinelX dependency?
