# PR-013 — Host Runtime Repository Materialization & Scoped Publication Bridge V1 — Plan Review R2

## Review State

```yaml
task_id: PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1
review_target: plan
requirement_revision: 1
requirement_blob_sha: 568d21c6d47fae821a84108cd05e3eca02191b91
plan_revision: 2
plan_blob_sha: e65fceea327df2820719d0feb74759e733955efb
reviewed_task_head: 32cd89bdc3430596409329c676e18d36dddffc1b
result: Approved
runtime:
  devforge_version: 2.41.0
  devforge_revision: 902a9d71b425753928c01904be1e9b2b60f0c3fe
  project_development_workflow: "2.1"
  review_contract: "1.3"
  slicing_contract: "1.1"
repository_reality:
  canonical_main: e7064c9bf4fcd15bdb6f5a2678414210c01d1c00
  pr012: done_merged_canonical
  pr011: open_implementation_s03_blocked
  local_canonical_checkout:
    branch: main
    head: e7064c9bf4fcd15bdb6f5a2678414210c01d1c00
    dirty: true
    observation: 24 unstaged files are line-ending-only LF→CRLF drift by read-only diff
next_gate: implementation
next_expected_actor: implementer
```

## Decision

**Approved.**

Plan Revision 2 closes all four Plan Review R1 blockers without changing Requirement Revision 1. It now provides an implementation-shaped authority model for repository transaction admission, source materialization, multi-operation scope lifecycle, publication content freezing, bounded user-scoped Git publication, retry/readback semantics, and the separation of Implementation from live Acceptance and downstream Task authority.

Approval authorizes compilation of the S01–S04 Execution Slice Set only. It does not authorize live Agent installation/restart, downstream ChatGPTControlShell execution, Hub changes, canonical-checkout mutation, generic Git/shell fallback, or any completion claim.

## R1 Finding Re-evaluation

### F1 — Repository transaction scope admission

**Closed.**

R2 freezes one concrete admission shape on the existing `provision_scope` action:

```text
purpose=repository_transaction_v1
→ provider-owned fixed operation classes:
  repository_materialize
  repository_execute
  repository_publish
```

The caller cannot supply or enlarge operation classes, Host paths, staging/cache identifiers, sandbox identity, Git argv, remote URLs, or credential controls. Exact source/publication ref+SHA are sealed into a durable repository-transaction record bound one-to-one with repository identity, semantic lineage, scope generation and workspace identity.

Same-Attempt retry semantics are explicit: exact sealed-input retries converge; authority-changing retries conflict; terminal/revoked/expired authority cannot be reactivated; a legacy `scoped_script` Attempt cannot be upgraded into a repository transaction.

This preserves the existing immutable scope authority model and legacy one-shot behavior.

### F2 — Materialization execution identity

**Closed.**

R2 explicitly forbids unrestricted LocalSystem/service-side copying of repository source bytes. Source hydration is a scoped OS-enforced operation:

```text
revalidate
→ durable START
→ scope-derived AppContainer + Job
→ temporary read-only grant to one immutable source snapshot
→ trusted provider materializer spawn
→ exact workspace-only writes
→ Job/process quiescence
→ snapshot ACL removal
→ zero-authority readback
→ exact tree digest
```

The materializer is provider code, not repository/caller code. Canonical checkout, mutation authority store, user profile and Git credential material receive no grant. Traversal/reparse/ADS/special-file/resource-limit cases are fail-closed.

The physical Windows verification requirement that rejects a direct unrestricted service-copy substitute is sufficient to keep this boundary testable rather than aspirational.

### F3 — Publication content handoff / credential boundary

**Closed.**

R2 now freezes post-execution content before entering user credential context:

```text
execution closes
→ zero live process/write authority readback
→ provider freezes exact source tree into immutable publication capsule
→ publication_content_digest persisted
→ provider-owned staging/object store
→ fixed Git plumbing under user-scoped credentials
→ produced_commit_sha persisted before push
→ non-force CAS push
→ exact remote readback
```

Credential-bearing Git never receives reusable scoped-workspace access. The broker consumes immutable provider-owned publication content, neutralizes hooks/filters/aliases/signing/editor/shell behavior, accepts no arbitrary Git argv, and does not expose credential material in state/receipts.

Uncertain publication is readback-first and reuses the same produced commit; third-value remote drift fails closed.

### F4 — Implementation / Acceptance / downstream authority boundary

**Closed.**

Implementation is limited to S01–S04 product code, fixture harnesses and candidate-local/CI/isolated Windows verification.

Live Agent installation/restart and accepted-candidate physical proof belong to `#开发验收`.

The downstream ChatGPTControlShell AC13 proof still requires its own separately issued canonical command:

```text
#开发执行 PR-013-manual-command-adoption-workflow-lineage-attachment-v1
```

SentinelX Acceptance may consume the downstream durable receipt as evidence but cannot synthesize, inherit or replay downstream Task authority.

## Requirement / Security Traceability

- R1/R2 + AC1–AC3: concrete purpose-discriminated scope admission and exact ref/SHA/lineage binding in S01.
- R3/R6 + AC2–AC5: AppContainer materializer, exact ACL/Job/process closure and source-tree readback in S02.
- R4/R13 + AC4/AC11: canonical firewall and no-fallback regressions across all affected slices.
- R5: broker-owned source acquisition with non-projected provider paths and credential isolation.
- R7/R10 + AC5/AC10: single canonical executor, repository operation closure, and legacy one-shot terminalization regressions in S03.
- R8/R9 + AC6–AC8: immutable publication handoff plus fixed-plumbing/no-hook/no-filter/no-signing/non-force CAS publication in S04.
- R10/R11 + AC9: durable produced-commit identity and readback-first idempotent retry.
- R12: dynamic `local_api.describe` projection stays on the Agent-owned `devforge_runtime` endpoint; Hub remains immutable.
- AC12: isolated Windows implementation fixture plus separate live Acceptance fixture.
- AC13: cross-repository receipt only after independently authorized downstream execution.

## Current Canonical Baseline

PR-012 is merged and completed; `execution_profile=scoped_mutation` is therefore canonical baseline and R2 correctly builds on it rather than treating it as an unmerged dependency.

PR-011 remains open and blocked in S03. Its current branch changes overlap future PR-013 surfaces including `windows_mutation_sandbox.py`, `mutation_audit.py` and `handlers/scoped_script.py`. This is not an approval blocker because R2 forbids importing unmerged PR-011 code and requires a fresh main/PR-011 overlap impact check at every slice admission. If PR-011 merges before an overlapping PR-013 slice, that slice must reconcile against the new canonical baseline before mutation.

## Host Canonical Checkout Admission Note

The current local canonical checkout is not clean: read-only diff shows 24 unstaged files whose changes are LF→CRLF line-ending normalization only. This does **not** invalidate Plan correctness and is not a Plan blocker.

It is, however, a hard Implementation-entry guard under the repository invariant:

```text
canonical checkout must be main + clean before first product mutation
```

`#开发执行` must therefore re-read the canonical checkout and stop before material mutation if it remains dirty. Plan approval does not authorize `restore`, `reset`, line-ending rewrite, or any other canonical-checkout mutation.

## Slice Compilation Guidance

Compile exactly four ordered implementation slices:

1. **S01 — Repository Transaction Admission + Durable State**
2. **S02 — Exact Source Snapshot + AppContainer Materializer**
3. **S03 — Repository-Scoped Execution Lifecycle + Publication Freeze**
4. **S04 — Fixed Git Publication Broker + Candidate Verification Harness**

Rules:

- one `#开发执行` completes at most one admitted slice;
- each slice revalidates current `main`, PR-013 transport head, approved-plan lineage, PR-011 state and local canonical `main + clean` before material mutation;
- completed slices are not replayed;
- material plan/Requirement drift fails closed;
- implementation uses Host-owned execution workspace only, never the canonical checkout;
- live Agent activation/restart and AC13 downstream execution are not implementation slices.

## Gate Result

```text
Plan Review R2: Approved
Requirement Revision: 1
Plan Revision: 2
Plan Approved: true
Execution Slice Set: required and compiled by this review transition
Next Gate: implementation
Next Slice: S01
Next Actor: implementer
```

No product implementation, live Agent activation, service restart, remote publication side effect, downstream Task execution or completion claim is performed by this review.