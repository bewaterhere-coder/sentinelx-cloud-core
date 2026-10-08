# SX-HMSA-001 — Acceptance Review R2

## Decision

```yaml
task_id: SX-HMSA-001
result: Approved
canonical_transport: github-pr
pr_number: 3
evaluated_product_head: 3f44a59e26bb0f15c80264ca4ef6d7302c95e3e1
prior_acceptance: docs/reviews/SX-HMSA-001-host-mutation-sandbox-pre-execution-audit-lineage-provider-v1-acceptance-r1.md
next_stage: accepted
```

**SX-HMSA-001 Acceptance: Approved.**

The fixing implementation closes all three blocking findings from Acceptance R1 on the canonical Task transport. No blocking implementation-quality, requirement, regression, scope, evidence, requirement-change, or transport finding remains.

Acceptance approval transitions the Task to **Accepted**. It does not merge PR #3 and does not constitute Completion Verification.

## Runtime / Transport Consistency

PASS.

- DevForge Runtime: `bewaterhere-coder/DevForge main@3cba70b07350c98008ae5f084c5f67dc78931477`.
- Acceptance Contract: `contracts/development/acceptance-contract.md` v1.5.
- Canonical repository: `bewaterhere-coder/sentinelx-cloud-core`.
- Canonical PR: #3.
- Canonical branch: `task/sx-host-mutation-sandbox-pre-execution-audit-lineage-provider-v1`.
- Evaluated fixing head: `3f44a59e26bb0f15c80264ca4ef6d7302c95e3e1`.
- Fix execution stayed on the same branch / same PR. No replacement Task, branch, worktree, PR, or unauthorized transport migration was used.
- PR review-thread read-back found no unresolved inline review threads.

No `TransportDrift` exists.

## Requirement Change Guard

PASS.

The Requirement semantics did not materially change after Plan approval. Changes to the Requirement artifact since approved Plan head are lifecycle metadata plus escaped Windows path rendering; the Goal, security boundary, failure semantics, incident regression, and Acceptance Criteria remain unchanged.

## Acceptance R1 Findings Closure

### A1 — START audit evidence / AC8 — Resolved

`OPERATION_STARTED` now durably seals, before workspace materialization/spawn:

- authoritative request and semantic lineage binding;
- scope, workspace, protected-inventory, policy, repository and semantic identity digests;
- process intent: interpreter, argv, executable final-path intent and cwd intent;
- provider-derived Host/AppContainer requested identity;
- retained forensic script hash/artifact evidence.

The scoped handler computes process intent with `materialize=false`, commits START, and only then activates/materializes the admitted workspace and runner artifacts. Payload fields do not become scope authority.

Fresh tests directly assert the START authority/process/sandbox fields and prove an injected durable START failure leaves the execution workspace unmaterialized and no process spawned.

### A2 — SPAWN audit evidence / AC9 — Resolved

The Windows provider creates the process suspended, binds it to the no-breakaway Job, then performs pre-resume read-back for:

- PID and PPID;
- final executable path;
- final cwd path identity;
- process user/AppContainer token identity;
- Job containment identity and breakaway state.

`PROCESS_SPAWNED` is durably appended before `resume_suspended`. If the SPAWN audit write fails, the suspended process/Job is terminated and resume is not called.

Fresh unit and real Windows integration tests prove durable SPAWN precedes the first untrusted instruction and that the recorded evidence contains the required identity/containment fields.

### A3 — FINISH terminal closure / AC10, AC12, AC13 — Resolved

Normal success, timeout and runtime-unavailable paths now terminalize scope authority before FINISH. `OPERATION_FINISHED` requires closure evidence proving:

- scope state is `terminal` for the exact scope/generation;
- scope/protected-inventory digests match START authority;
- Job handle is closed and active process count is zero;
- no active Job/process bindings remain;
- sandbox write authority is absent;
- process tree is quiescent;
- terminalization timestamp/read-back exists.

An injected terminalization/closure-read-back failure returns external failure and deliberately leaves START/SPAWN without a fabricated FINISH. Crash semantics likewise permit START without false successful FINISH.

## Acceptance Criteria Traceability

1. **Capability truthfulness — PASS.** Real Windows runtime self-check gates both provider capabilities; fresh incident matrix exercises capability readiness.
2. **Host-owned scope lifecycle — PASS.** Retained S02 evidence proves provider-owned provisioning/revalidation/terminalization and caller-minted rejection.
3. **Admission + START before materialization — PASS.** Fresh START durability regression plus scoped execution ordering.
4. **Exact-workspace write — PASS.** Fresh real Windows scoped execution/sandbox matrix.
5. **Out-of-scope write/delete denied — PASS.** Fresh canonical incident regression and Windows sandbox tests.
6. **Child/detached containment — PASS.** Fresh Job/process-tree and canonical incident regression.
7. **Durable START before spawn — PASS.** Fresh failure injection proves no spawn on START durability failure.
8. **Complete START evidence — PASS.** A1 closure evidence above.
9. **Complete SPAWN evidence — PASS.** A2 closure evidence above.
10. **Terminal FINISH/read-back + crash semantics — PASS.** A3 closure evidence above.
11. **Forensic evidence survives cleanup — PASS.** Fresh mutation-audit tests.
12. **Exact scope/generation terminalization before success — PASS.** Fresh scoped execution and closure tests.
13. **Terminalization/read-back failure blocks success — PASS.** Fresh injected failure regression.
14. **No unrestricted fallback — PASS.** Fresh scoped execution policy/no-fallback tests; retained compatibility evidence remains valid.
15. **Git credentials remain separate — PASS.** Scoped environment regression confirms credential-like authority is rejected; authenticated Git remains outside sandbox authority.
16. **Canonical incident regression — PASS.** Fresh disposable-fixture destructive-escape matrix preserves all protected sentinels.
17. **Relevant regression behavior — PASS.** Fresh directly affected security matrix passes; prior S01-S06 unaffected receipts remain retained. The standalone verifier still lacks the async pytest plugin for unrelated async-suite execution; this is verifier-environment evidence, not an observed product regression.
18. **Documentation/config semantics — PASS.** Retained S06 documentation/config evidence remains applicable; fixing did not change those semantics.

## Fresh Acceptance Verification

Evaluated from clean canonical worktree at product head `3f44a59e26bb0f15c80264ca4ef6d7302c95e3e1` on the Windows Host:

```text
pytest
  tests/test_mutation_audit.py
  tests/test_windows_mutation_sandbox.py
  tests/test_scoped_script_execution.py
  tests/test_incident_20260927_d_root_recursive_delete.py
  tests/test_policy.py

49 passed, 1 skipped
```

The single skip is explicitly classified: `pwsh` is not installed on this Host. Windows PowerShell/Python scoped behavior remains covered, and unsupported/runtime-unavailable paths fail closed rather than falling back.

Additional checks:

- Python `compileall` on touched runtime/tests — PASS.
- `git diff --check` for fixing commit — PASS.
- Worktree before Acceptance metadata — clean, `ahead=0`, `behind=0`.

The earlier inability to run unrelated async pytest cases in the standalone `C:\Python314` verifier remains attributable to missing `pytest-asyncio`; no failing product assertion from those cases was observed. This is not used as positive proof, and the acceptance decision relies on fresh directly relevant Windows/security tests plus retained unaffected slice evidence.

## Concrete Security Invariants

- No durable START -> no workspace materialization/spawn: PASS.
- No durable SPAWN -> no first untrusted instruction: PASS.
- Scoped process can mutate admitted workspace but not protected fixtures: PASS.
- Child/detached process cannot escape Job/AppContainer boundary: PASS.
- No verified terminal authority/process closure -> no successful FINISH or external success: PASS.
- Crash/interruption may leave START without fabricated FINISH: PASS.
- `operator_unrestricted` is not a scoped-mutation fallback: PASS.

Visual Fidelity: **Not Applicable**.
Direct pointer/touch/navigation interaction requirements: **Not Applicable**.

## Acceptance Result

```text
Acceptance Approved: true
Implementation Complete: true
Completion Verified: false
Current Gate: Accepted
```

Canonical next action:

`#开发完成 SX-HMSA-001`

**No Completion Claim.**
