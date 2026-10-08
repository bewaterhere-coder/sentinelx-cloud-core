# PR-026 — Scoped PowerShell AppContainer Initialization Recovery V1 — Plan Review R2

## Review State

~~~yaml
task_id: PR-026-scoped-powershell-appcontainer-initialization-recovery-v1
review_target: plan
requirement_revision: 1
requirement_blob_sha: 6a0a6319fe0a82dd21812dafd07bdb4a99f25a3c
plan_revision: 2
plan_blob_sha: d3640c624f2890b54d7266b059aa4a0fd73a96d7
reviewed_task_head: d2db1d20b41d33b4a80ba9a01b9e181e9f6c1801
result: Approved
approved_scope: S02_session0_discrimination_diagnostic_only
owner_authorization_gate: [service_overlay, service_restart, production_probe]
runtime:
  devforge_version: "2.103.0"
  devforge_revision: ebc25425160790950bd4d4500186652d3bf52416
repository_reality:
  canonical_main: 2e5c69a112323867ee01783521554c43ebd731be
  canonical_pr: 26
  canonical_branch: task/scoped-powershell-appcontainer-initialization-recovery-v1
next_gate: implementation
next_expected_actor: implementer
~~~

## Decision

**Approved — S02 diagnostic scope only. No compatibility repair authority.**

## Review findings

1. **S02 Session-0 comparison design is sound.** S01's receipt (commit
   `c4a4028`) established the discriminator: interpreter-image/CLR init is
   disconfirmed in an interactive AppContainer session; the untested delta
   is the Session-0/LocalSystem service context. Plan R2 targets exactly
   that delta with one production probe through the original admitted
   request path. No mock, no fallback, no retry farming.

2. **Diagnostic scope only.** The plan explicitly defers any compatibility
   repair: the raw exit code, exact workspace/lineage identity and
   permission/audit evidence must exist first, and a repair still requires
   a further evidence-proven plan revision plus its own review. R2 grants
   no repair authority.

3. **S01 evidence is immutable and not replayed.** S01 artifacts are
   referenced read-only as the comparator baseline; R2 contains no S01
   execution replay.

4. **Owner Authorization Gate (binding condition).** The three
   state-changing service operations — (a) overlay of the two patched
   blobs into the installed service venv, (b) `SentinelX` service restart,
   (c) the production probe invocation — are each gated behind a separate,
   explicit Owner authorization to be granted at execution time. Approval
   of this plan does NOT authorize any of them. Without that authorization
   the slice records `BlockedByAuthorization`.

5. **Rollback / snapshot / restoration verified in design.** S02-A(1)
   mandates byte-hashes and file snapshots of the exact files to be
   overlayed, S02-A(6) mandates rollback-by-default with byte read-back of
   the restored installed state (retained only on explicit contrary
   instruction), and any restoration failure is an immediate `Degraded`
   report. The probe journal read-back is read-only.

6. **Audit integrity.** Evidence flows through the existing durable
   mutation-audit journal (OPERATION_STARTED/SPAWNED/FINISH with the S01
   raw-status field), so the probe produces the same evidence class as the
   original failure, making the A/B comparator valid.

7. **Boundary compliance.** R2 adds no ACL/protected-root authority, no
   credential change, no new execution surface, no PR-018 replay, and no
   canonical-main mutation.

## Required execution evidence (S02 receipt)

- before/after blob hashes of the overlayed files and exact restoration
  read-back (or the owner's explicit contrary instruction);
- the Session-0 raw child exit status (decimal + `0x%08X`) from the patched
  FINISH event, or the explicit negative readback with the precise blocker;
- spawn/containment/audit/terminalization identity for the probe operation;
- Session-0 vs interactive A/B comparator table and updated matrix;
- canonical checkout `main + clean` read-back.

Canonical next command after this review:

~~~text
#开发执行 PR-026-scoped-powershell-appcontainer-initialization-recovery-v1
~~~

The implementer may execute only the read-only S02-A(1) preparation without
the Owner Authorization Gate; overlay, restart and probe each require the
owner's separate explicit authorization.
