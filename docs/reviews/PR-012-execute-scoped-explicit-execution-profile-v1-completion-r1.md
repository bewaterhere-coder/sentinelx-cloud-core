# PR-012 — execute_scoped Explicit Execution Profile Schema & End-to-End Propagation V1 — Completion R1

## Decision

```yaml
task_id: PR-012-execute-scoped-explicit-execution-profile-v1
requirement_revision: 1
plan_revision: 3
acceptance_revision: 1
completion_revision: 1
result: Completed
stage: done
completion_verified: true
next_expected_actor: none
```

PR-012 Completion R1 is verified.

The accepted implementation was finalized on the same Task lineage, merged through GitHub PR #12, and read back from canonical `main` at merge commit `29c724fdc6faed28018d60e61250d3f21b02c1b3`.

## Integration Evidence

- exact verified product candidate: `1e4012d7d6bfe4fa1bff70f364f3199d67626104`;
- finalization head: `76827d63cff599d4151aecca7ef60d72de481112`;
- base before merge: `dbf4bfc9ebcdbde2374d41e6825b613d46aa87f2`;
- merge commit: `29c724fdc6faed28018d60e61250d3f21b02c1b3`;
- canonical `main` readback: exact merge commit match;
- focused verification: `47 passed` on Python `3.12.13`;
- generic CI, macOS Agent, and PR-010 S01-S05 regression evidence: success;
- live AC6: exact candidate running as `0.24.1.dev175+g1e4012d7d`, live describe requires `execution_profile=scoped_mutation`, scoped marker succeeded, audit identity returned, and terminal scope readback succeeded;
- compare evidence proved no product-code change after the verified product candidate.

## Reconciliation

PR #12 was merged after all required pre-merge workflow finalization had been persisted. Terminal `done` metadata, the Integration Receipt, Completion R1, completed checkpoint, and reconciliation receipt are persisted to canonical `main` under same-Task post-merge reconciliation semantics. Implementation is not replayed and no replacement Development PR is created.

## Safety

- Hub unchanged;
- canonical local checkout not mutated;
- no permission or allowlist expansion;
- no `operator_unrestricted` or unrestricted fallback;
- no new Development Task or replacement PR created;
- completion claim is made only after merge and canonical-main readback.
