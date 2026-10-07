# PR-017 Large Runtime Root ACL Cleanup Timeout & Recovery V1 — Plan

## Status

```yaml
task_id: PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1
plan_revision: 5
plan_status: completed
review_state: approved
implementation_authority: false
execution_state: all_slices_completed
acceptance_state: approved
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

**Revision 3 integration objective:** preserve the already-completed S01/S02 evidence, consume only the production subset of the separately verified PR-018 Unity/AppContainer compatibility candidate, and replay only PR-017 S03 / Requirement R8.3 on the combined canonical PR-017 candidate. No S01/S02 replay, PR-018 diagnostic seam import, or PR-018 documentation import is authorized.

## Technical Decision

Treat this as a **runtime-root ACL lifecycle reliability** defect inside the existing `WindowsMutationSandbox`.

Do not redesign `execute_scoped`, scope identity, Job containment or AppContainer authority.

### Revision 3 — PR-018 production-subset integration decision

Plan Review R2 rejected the exact-12-blob payload because two candidate blobs still contained PR-018/S01-only paired-diagnostic behavior. Revision 3 corrects only that integration boundary; Requirement Revision 1 and the S03 behavioral objective are unchanged.

The upstream evidence remains:

```text
PR-018 verified product candidate:
73a52013055a8b3bb70b319a0ed7b7ba832ae0c9

PR-018 exact live source proof:
86bc881265ee3fb2ab388170a16e627caf6d723e

PR-018 local acceptance:
AC1-AC17 and AC19 pass
AC18 waits on this PR-017 combined replay
```

PR-017 consumes PR-018 as an integration dependency, not as authority to import PR-018 task-specific diagnostics.

The canonical integration rule is now:

```text
current PR-017 canonical branch
+ frozen PR-018 production-subset manifest
→ combined PR-017 candidate
→ replay PR-017 S03 only
→ prove R8.3 + original PR-017 cleanup/containment requirements
```

### Production-subset manifest

Execution MUST use compare-and-swap semantics. Every `current_blob` below must still match before any product mutation. If any current blob drifts, execution stops for reconciliation.

```yaml
manifest_version: pr017-pr018-production-subset-v1
reviewed_pr017_head: 0c9ab574ce4d38818e4bb55a2d5f8deaf77f2bcb
upstream_candidate: 73a52013055a8b3bb70b319a0ed7b7ba832ae0c9

project:
  - path: config.example.windows.yaml
    current_blob: 4a2090833cb780c4c9ca85ad436d454ce617dbd9
    target_blob: a76b1772361517838b40de019bee1e9aa9fb9c85

  - path: src/sentinelx_core/handlers/basic.py
    current_blob: ef48f514e549b8ac25e5ab4be104845828c78895
    target_blob: 5a99296d9c80b164d344abf519f5627eae5f52fe

  - path: src/sentinelx_core/handlers/mutation_scope.py
    current_blob: 6c75e48fec5cd5b11bffc56e6ef84dec79b53392
    target_blob: af310b650151de168a9ff437140fbe0e1187cf6d

  - path: src/sentinelx_core/mutation_placement.py
    current_blob: 3aaa686c569dd07d8a2ecce0eb3aca5928758ddc
    target_blob: 6ee33bacee65dac566116a4252756e40e25c4662

  - path: src/sentinelx_core/mutation_readiness.py
    current_blob: f1bcbbc8b98a2ff97a776eacb45448516998e947
    target_blob: aa318aec6e25b2b0ce3d13feb9c46c6680852144

  - path: src/sentinelx_core/mutation_scope.py
    current_blob: cb5f87642a65f84859a0f60a7b46b7ad2bc3fcec
    target_blob: 1a6dce6d066c07569ea5676cd9a411105171a9f6

  - path: src/sentinelx_core/policy.py
    current_blob: f6a664f87b20e7f426de3e2bd47096d4d9935d80
    target_blob: 82cc82615f090f19777161125c1e2aff14e63806

  - path: src/sentinelx_core/windows_mutation_sandbox.py
    current_blob: dab8a33dccf842fdbd18ae6e46c11cd4e7b4bcc9
    target_blob: 1e662eba2dbc61825bc874e102a735e7a9d9a179
    target_kind: derived_production_subset

  - path: tests/test_mutation_scope_admission.py
    current_blob: a7d1ab1af121b8fe540841461d731a8691869d20
    target_blob: 4dd4db78a3c20487ae442ac312760dd6dbaa4b1e

  - path: tests/test_policy.py
    current_blob: 99ab9e269f6554225dcc358ceac59ccb66f75873
    target_blob: fd1d002d8426f58c71c0b5f66a343f00c786e943

  - path: tests/test_windows_mutation_sandbox.py
    current_blob: db8b0271d634322f6083fa34f9d9832960724c8e
    target_blob: 926900b91055707528a6cfdd5fb131d11abdfc89
    target_kind: derived_genericized_test
```

Exactly **11 files** are projected.

### Explicitly preserved file

```yaml
path: src/sentinelx_core/handlers/scoped_script.py
required_blob: 4580475ba9bd8ba5301b579ee11a584abbd75d4b
action: preserve_current_PR017_blob
reason: PR-018 candidate delta is entirely S01 paired-diagnostic behavior
```

Execution must assert this blob remains unchanged before and after integration.

### Deterministic derivation rules

The two derived blobs were precomputed during Plan remediation and are not left to implementation judgment.

#### windows_mutation_sandbox.py

Input:

```text
PR-018 candidate blob:
c5a9ae35b8324adffc31ce9ed6cbbf9ebe172bde
```

Mechanical transform:

1. Locate the unique line beginning exactly with:
   `    def enable_pr018_paired_session_read(`
2. Locate the next unique line beginning exactly with:
   `    def enable_verification_descendants(`
3. Delete the full contiguous text interval from the first marker up to, but not including, the second marker.
4. Make no other textual change.
5. The result MUST hash to:

```text
1e662eba2dbc61825bc874e102a735e7a9d9a179
```

The resulting blob contains no:

- `enable_pr018_paired_session_read`;
- `pr018_paired_session_absence`;
- `PR018_S01_PAIRED_DIAGNOSTIC`;
- `.pr018-s01-paired`.

This preserves the generic production Session-0 lifecycle while removing PR-018/S01-only diagnostic methods.

#### tests/test_windows_mutation_sandbox.py

Input:

```text
PR-018 candidate blob:
8218fa324a99ba48669a5427fdafaf714f43f25f
```

Mechanical transform:

```text
test_pr018_session_masks_are_exact_frozen_read_only_values
→
test_session_object_masks_are_exact_frozen_read_only_values
```

No test body changes are authorized.

The result MUST hash to:

```text
926900b91055707528a6cfdd5fb131d11abdfc89
```

### Excluded surfaces

The integration MUST NOT import:

```text
src/sentinelx_core/handlers/scoped_script.py from PR-018
enable_pr018_paired_session_read(...)
pr018_paired_session_absence(...)
PR018_S01_PAIRED_DIAGNOSTIC
.pr018-s01-paired
all PR-018 docs/**
.github/workflows/pr018-s02-verification.yml
PR-018 task/branch/PR state
```

The implementation host is not authorized to perform any additional production-subset inference beyond this manifest.

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

### 7. Combined-candidate S03 real Windows replay

S01 and S02 are historical completed slices under Plan R1 and MUST NOT be replayed.

After Plan R5 approval, S03 execution first materializes the frozen PR-018 production-subset payload onto the canonical PR-017 branch, verifies the resulting tree, and then performs the real Host replay.

Recommended Host config remains bounded and provider-owned:

```yaml
mutation_execution:
  runtime_acl_timeout_seconds: 300
  runtime_session_object_read_enabled: true  # temporary S03 proof only
  runtime_read_roots:
    - C:\ProgramData\SentinelX\.venv
    - C:\Python314
    - C:\Program Files\Unity\Hub\Editor\6000.6.4f1
```

The compatibility toggle is temporary proof configuration only. It must be restored to `false` after the replay and the Host must re-read healthy with no residual authority.

Replay sequence:

```text
A. combined-candidate admission
   → canonical PR-017 branch only
   → exact 12-file PR-018 payload read back
   → no PR-018 docs/workflow/task-state import

B. execute_scoped python3 marker
   → PASS
   → terminal

C. execute_scoped python3
   → subprocess exact Unity.exe -version
   → raw child status != 0xC0000142
   → deterministic output 6000.6.4f1
   → scope terminal

D. live security/cleanup readback
   → AppContainer=true
   → process is Job-contained / no-breakaway
   → Session 0 exact read-only masks only
   → exact Unity scope AppContainer SID absent from:
      - Unity runtime root
      - bound Window Station
      - bound Desktop
   → durable Session-0 cleanup binding cleared before terminal success

E. post-proof restore
   → runtime_session_object_read_enabled=false
   → temporary proof authority removed
   → host_mutation_sandbox_v1 verified
   → PR-011 Node/npm scoped verification verified
   → canonical mutation firewall verified
```

The existing PR-017 PowerShell evidence remains preserved from Plan R1. It is not replayed merely because Unity compatibility was supplied by PR-018; a new PowerShell run is required only if Plan Review identifies material overlap affecting that evidence.

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

Plan R5 authorizes no new local design beyond the frozen production-subset manifest. The only product/config/test files eligible for S03 integration are the 11 CAS-bound paths listed in the Revision 3 decision above; `src/sentinelx_core/handlers/scoped_script.py` is explicitly preserved and is not an integration target.

PR-017 Requirement/Plan/Slice/checkpoint/receipt artifacts may change only to record Plan R5 lineage and S03 evidence.

Explicitly excluded:

```text
all docs/** from PR-018
.github/workflows/pr018-s02-verification.yml
PR-018 branch / PR number / task-state mutation
PR-017 S01/S02 product or receipt replay
```

No protocol schema change is expected.

## Slice Proposal

Plan Review R5 must preserve S01 and S02 as completed historical slices with their existing receipts and compile only the revised S03 authority.

```text
S01 — PRESERVED COMPLETED; no replay
S02 — PRESERVED COMPLETED; no replay
S03 — frozen PR-018 production-subset integration on canonical PR-017 branch
      + combined-candidate real Windows R8.3 replay
      + exact cleanup/security readback
      + affected regression closure
```

No new S04 is introduced. One explicit `#开发执行 PR-017-large-runtime-root-acl-cleanup-timeout-recovery-v1` after Plan R5 approval may complete at most the revised S03.

No product mutation is authorized until Plan Review approves Plan R5 and recompiles the canonical Execution Slice Set.

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

### RSK-6 — cross-Task payload drift

Mitigation: freeze the exact PR-018 candidate and per-file blob identities; refuse branch-level merge or moving-head cherry-pick semantics.

### RSK-7 — replay accidentally invalidates S01/S02 evidence

Mitigation: preserve their canonical receipts and prohibit replay/mutation unless the 11-file production-subset integration materially changes an invariant they own. Plan Review must explicitly decide any such invalidation; implementation must not infer it.

### RSK-8 — PR-018 proof is mistaken for PR-017 S03 evidence

Mitigation: PR-018 proof is only dependency evidence. PR-017 must create its own combined-candidate S03 scope/audit/cleanup receipt on the canonical PR-017 transport.

## Plan Review Questions

1. Does the frozen 11-file production-subset manifest remove all PR-018/S01 diagnostic-only surfaces while preserving the generic compatibility behavior?
2. Are the two derived blobs mechanically reproducible and sufficiently immutable for execution authority?
3. Is preserving the PR-017 `scoped_script.py` blob and excluding the PR-018-only workflow correct for PR-017 S03?
4. Can S01/S02 receipts remain valid without replay because PR-017 current head has no product drift since the PR-018 stacked base?
5. Does the revised S03 prove both R8.3 and the original PR-017 runtime-root cleanup/terminal invariants?
6. Is temporary `runtime_session_object_read_enabled=true` acceptable only for S03 proof with mandatory default-off restoration?
7. Are PR-011/PR-012 regression and no-breakaway/canonical-firewall checks sufficient after combined-candidate activation?
8. Does Plan R5 avoid treating PR-018 isolated evidence as PR-017 S03 completion evidence?
