# PR-011 Acceptance R1 Fix Impact Analysis — Hosted CI / Real-Host Boundary

## Finding

Acceptance R1 rejected on `AC11RelevantWindowsCIRegression` because
`pr011-s04-verification` executed two tests whose contract is the configured
provider Host physical boundary, and those tests failed on the GitHub-hosted
Windows runner even though the mandatory SYSTEM Host proof passed.

## Classification

```yaml
finding: AC11RelevantWindowsCIRegression
classification: repair_local
requirement_revision_changed: false
plan_revision_changed: false
product_runtime_semantics_changed: false
security_boundary_changed: false
real_host_evidence_invalidated: false
```

## Evidence

The exact product candidate and the later evidence-only head both produced the
same hosted failure:

- exact product run `37462685310`: 2 failed, 53 passed;
- acceptance-head run `37465837618`: 2 failed, 53 passed.

The failing tests were:

- `test_real_windows_node_npm_readiness_is_physical_and_revokes_toolchain_acl`;
- `test_post_readiness_toolchain_tamper_fails_before_start`.

Both require the provider-owned physical Host readiness path. The accepted
Plan R6 and S04 workflow comment already distinguish GitHub-hosted regression
coverage from the mandatory configured Host proof.

The authoritative physical evidence remains:

- SYSTEM Host final S04 gate: 35 passed, 0 failed;
- focused post-readiness toolchain tamper gate: passed;
- S05 live readiness: verified;
- S05 live profiled `execute_scoped`: passed;
- S05 terminal scope readback: passed.

## Repair

The workflow is narrowed to its declared hosted-CI role:

1. run the three readiness tests that verify non-Host readiness semantics;
2. retain affected Windows sandbox/materialization/runtime/profile/scoped-script
   regression suites;
3. do not execute the two provider-Host physical readiness tests on
   `windows-latest`;
4. keep those two tests mandatory in the separate SYSTEM physical Host gate.

No test is deleted and no product behavior is weakened.

## Preserved Evidence

Because this repair changes only CI orchestration and does not modify runtime,
policy, sandbox, readiness, handler or test semantics, the existing real-Host
S04 and live S05 receipts remain valid.

A fresh successful `pr011-s04-verification` run on the repaired exact head is
required before the Task may re-enter Acceptance.
