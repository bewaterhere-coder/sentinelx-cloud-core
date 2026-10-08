# SX-HMSA-001 — Acceptance Review R1

## Decision

```yaml
task_id: SX-HMSA-001
result: Rejected
canonical_transport: github-pr
pr_number: 3
evaluated_product_head: 1234b99ade8434f305915769fc8f7dc609a27895
checkpoint_head: 30fdad7b423a058233dc6517dbba1d8a65d918a0
next_stage: fixing
```

## Transport Consistency

PASS.

The implementation remains on canonical PR #3 and canonical branch
`task/sx-host-mutation-sandbox-pre-execution-audit-lineage-provider-v1`.
No alternate implementation transport or unresolved review thread was found.

## Evidence Retained From Completed Slices

S01-S06 all have durable completion receipts. The Windows destructive-escape regression,
scoped mutation containment, unique lease lifecycle, retained script evidence, and
capability-readiness tests provide substantial positive evidence for acceptance criteria
1-7 and 11-18, subject to the blocking findings below.

S06 verified the remote product tree with `compileall` PASS and the focused security matrix
at 25 passed / 1 explicitly classified skip. The incident test uses disposable fixture-owned
roots only; no destructive acceptance test targets real `D:\\`, `D:\\coco`, or a real project
checkout.

An additional whole-repository acceptance rerun from canonical checkpoint
`30fdad7b423a058233dc6517dbba1d8a65d918a0` could not collect because the standalone
`C:\\Python314` verifier environment does not contain the project's runtime dependencies
(`sentinelx_protocol`, etc.), and one pre-existing Unix-specific test references
`os.geteuid` on Windows. This is verifier-environment evidence, not a product regression,
and is not the rejection reason.

## Blocking Findings

### A1 — START audit evidence does not satisfy Acceptance Criterion 8

Requirement AC8 requires START to contain request identity, semantic lineage, scope
identity/digests, process intent, and durable script evidence.

Current `MutationAuditBinding.audit_dict()` / `MutationAuditJournal.begin()` persist the
request id/op/opaque ref, lineage, scope id/generation, workspace id, unique lease key,
binding digest, and script evidence. They do **not** persist equivalent evidence for the
required scope/protected-authority digests and process intent (interpreter, cwd, argv,
resolved executable), nor the requested host/sandbox identity evidence.

The current tests assert the reduced schema, so green S03 tests do not prove AC8.

Required correction: extend the sealed START evidence model and tests so the canonical
scoped execution path durably records the materially required scope digests and process
intent before workspace materialization/spawn, without making payload fields authoritative.

### A2 — SPAWN audit evidence does not satisfy Acceptance Criterion 9

Requirement AC9 requires PID/PPID, final executable/cwd identity, OS identity, and
containment identity.

Current `MutationAuditJournal.record_spawn()` persists PID, job binding, sandbox identity,
timestamp, operation id, and binding digest. It does **not** record PPID,
`executable_final_path`, `cwd_final_path`, or equivalent OS identity read-back.

Required correction: collect the authoritative post-create/pre-resume process read-back
while the root process is still suspended and write these fields durably before
`ResumeThread`. Audit-write failure must continue to terminate the suspended Job/process
and never resume it.

### A3 — FINISH audit evidence does not satisfy Acceptance Criterion 10

Requirement AC10 requires terminal outcome/process-tree/read-back evidence.

Current `MutationAuditJournal.finish()` persists only status, return code, error code,
timestamp, operation id, and binding digest. It does not persist process-tree closure or
containment/scope read-back evidence. The scoped handler also calls `audit.finish()` before
`terminalize_scope()` in the normal success/timeout path, so FINISH cannot contain the
required terminalization/read-back evidence as currently structured.

Required correction: define and persist authoritative FINISH closure evidence (including
process-tree/Job quiescence and the relevant scope/authority read-back), and add a regression
that proves a successful externally returned result cannot be produced when terminalization
or closure read-back fails. Preserve the requirement that a crash may leave START without a
fabricated successful FINISH.

## Non-blocking Observation

`src/sentinelx_core/handlers/basic.py` contains the text typo `not recommed`. It has no
security or behavioral effect and is not an acceptance blocker; it may be corrected while
addressing the blocking findings.

## Acceptance Result

```text
SX-HMSA-001 Acceptance: Rejected
```

The canonical fix loop remains on PR #3. No new task, branch, or PR is authorized by this
review.
