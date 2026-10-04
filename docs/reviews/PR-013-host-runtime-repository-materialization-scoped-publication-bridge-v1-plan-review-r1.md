# PR-013 — Host Runtime Repository Materialization & Scoped Publication Bridge V1 — Plan Review R1

## Review State

```yaml
task_id: PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1
review_target: plan
requirement_revision: 1
requirement_blob_sha: 277713a48ba863c4cf0805304d90eefde12e3807
plan_revision: 1
plan_blob_sha: 7d46ff42a8eed971e0a5d284065420c6d17ab088
reviewed_task_head: 3b503c28e282e032455f02a191898abfb0f7c31f
result: Rejected
finding_classification: plan_local
runtime:
  devforge_version: v2.40.0
  devforge_revision: 1dc76ed0bcc1a70a2c5a860cd7a99aedd5d7820a
  project_development_workflow: "2.1"
  review_contract: "1.3"
repository_reality:
  canonical_main: dbf4bfc9ebcdbde2374d41e6825b613d46aa87f2
  pr_011: open_implementation_s03_pending
  pr_012: open_acceptance_blocked_not_merged
next_gate: plan_review_rejected
next_expected_actor: planner
```

## Scope Reviewed

- Canonical Requirement Revision 1.
- Canonical Plan Revision 1.
- Current `sentinelx-cloud-core/main@dbf4bfc9ebcdbde2374d41e6825b613d46aa87f2`.
- Current `MutationScopeStore` authority/lifecycle implementation.
- Current Agent-owned `devforge_runtime` local API contract.
- Current Windows user-scoped Git primitive.
- PR-011 and PR-012 current task states and overlap.
- DevForge `main@1dc76ed0bcc1a70a2c5a860cd7a99aedd5d7820a` / v2.40.0 Review Contract v1.3.

## Decision

**Rejected / Changes Requested.**

The architecture direction is valid: provider-owned source acquisition, exact scope-bound materialization, reuse of the existing AppContainer executor, fixed-semantics publication, CAS readback, and preservation of the canonical repository firewall all match Requirement Revision 1.

However, Plan R1 leaves four implementation-shaping authority assumptions unresolved. Each can materially change security behavior or Acceptance, so Implementation Ready cannot be granted yet.

## Blocking Finding F1 — Repository transaction has no concrete scope-admission contract

### Evidence

Current `devforge_runtime.provision_scope` admits only `purpose=scoped_script`. Current scope authority seals `allowed_operation_classes` into the durable scope record, and a retry of the same Attempt requesting a different operation-class set is rejected as a conflict.

Plan R1 says repository-transaction scopes will be “explicitly admitted” and later authorize materialize/execute/publish, but it does not define how that authority is minted through the model-facing contract.

Without an explicit admission design, implementation would be forced either to retrofit new authority onto an existing `scoped_script` scope or to invent an unreviewed provisioning path. Both violate the provider-owned authority boundary.

### Required remediation

Plan R2 must freeze one concrete admission shape before implementation, for example either:

1. extend `provision_scope` with a closed provider-owned `purpose=repository_transaction_v1` whose purpose maps internally to a fixed operation-class set; or
2. add a dedicated bounded `provision_repository_transaction` action that mints the existing Host-owned scope with the fixed required operation classes.

The Plan must specify:

- the exact purpose/action schema exposed by `local_api.describe`;
- the fixed operation classes minted by the provider;
- which operation class gates materialization, repository-scoped execution and publication;
- that callers cannot supply or enlarge the operation-class set;
- retry/idempotency behavior for the same Attempt;
- backward compatibility for `purpose=scoped_script`.

## Blocking Finding F2 — Materialization execution identity is not frozen

### Evidence

Requirement R3/R6 and the DevForge execution-workspace materialization contract require source hydration to be the first admitted scoped filesystem mutation after scope revalidation and durable START evidence.

Plan D3 says a provider-controlled materializer writes only to the exact scoped workspace, but it does not state which OS identity actually performs those writes. A LocalSystem/service-side direct copy into the workspace would become a second unrestricted filesystem mutation surface; a caller script is forbidden; granting broad canonical/source access to AppContainer is also forbidden.

S02 mentions a narrow snapshot read grant, but does not freeze the materializer spawn/identity/grant/cleanup sequence.

### Required remediation

Plan R2 must specify the materialization mechanism as an OS-enforced scoped operation, including:

- provider-generated materializer executable/module identity;
- exact AppContainer/sandbox identity or equivalent provider-owned restricted token used for workspace writes;
- durable START before materializer spawn;
- read-only access from that identity to only the immutable admitted source snapshot/capsule;
- write access only to the sealed exact workspace;
- explicit denial of canonical checkout and provider authority-store access;
- bounded process/Job tracking and no surviving child process;
- snapshot-read ACL/grant removal and readback after materialization;
- failure cleanup/terminalization semantics;
- a physical Windows test proving the service/broker cannot silently substitute a direct unrestricted copy.

## Blocking Finding F3 — Publication content handoff and credential boundary are underspecified

### Evidence

Plan R1 correctly keeps user Git credentials out of AppContainer and proposes a user-scoped publication broker. But it does not define how the credential-bearing interactive-user Git process obtains the exact post-execution workspace content.

The scoped workspace is Host-owned and sandbox-constrained. Assuming the interactive user can directly read/write it may require ACL broadening that is not currently authorized. Running credential-bearing Git inside AppContainer is forbidden. Running ordinary Git directly in the scoped workspace also complicates the no-hook/no-filter/no-signing requirement.

This is a material feasibility/security assumption, not an implementation detail.

### Required remediation

Plan R2 must freeze a publication-content handoff that does not broaden workspace authority. A preferred shape is:

```text
scoped execution closes
→ provider verifies no live Job/process authority
→ provider freezes the exact workspace delta/tree into an immutable transaction-owned publication capsule/tree object
→ publication content digest + produced-tree intent persist durably
→ user-scoped Git broker consumes only the frozen provider-owned publication object/staging repository
→ fixed plumbing creates the one commit
→ expected-remote-SHA CAS push
→ remote readback
```

An equivalent design is acceptable, but the Plan must explicitly prove:

- interactive-user credential context never gains reusable scoped-workspace write authority;
- publication content cannot change between validation and commit creation;
- repository hooks/filters/aliases/signing helpers are not executed;
- publication staging/cache paths remain provider-owned, not caller-controlled;
- produced commit identity is persisted before remote write;
- uncertain push resumes by readback first without regenerating a commit.

## Blocking Finding F4 — Acceptance/activation and downstream Task authority are mixed into an implementation Slice

### Evidence

Proposed S04 is named an implementation Slice but includes:

- install/activate the accepted Agent candidate;
- restart/verify the live Agent;
- physical end-to-end acceptance;
- resume the downstream `ChatGPTControlShell` PR #13 S01 under a separate `#开发执行` authority.

These operations are not ordinary implementation mutation for this SentinelX Task. The downstream command is owned by another Task and cannot be executed merely because a SentinelX implementation Slice is current. The Plan itself also states this Task cannot mutate the downstream Task without that Task's own command authority.

Keeping these operations in the formal execution Slice Set would blur `#开发执行` and `#开发验收` boundaries and risk an authority transfer that DevForge forbids.

### Required remediation

Plan R2 must separate implementation from Acceptance:

- Implementation slices may build the repository transaction capability, regression coverage, fixture harness and candidate-local/CI verification.
- Exact Agent installation/restart, live physical capability proof, remote fixture publication against the activated accepted candidate, and AC13 downstream unblock proof belong to `#开发验收` unless a separately registered deployment capability explicitly owns them.
- The downstream ChatGPTControlShell resume must remain a separately issued canonical command on that Task. SentinelX Acceptance may consume the resulting receipt/readback as cross-repository evidence but may not synthesize or inherit that command authority.

If a Windows physical fixture must run before Acceptance to validate implementation feasibility, the Plan must distinguish that isolated test environment from live Agent activation and downstream Task mutation.

## Related-Task Assessment

### PR-011

PR-011 remains open in implementation with S03 pending. Its source/dependency capsule mechanics are complementary. PR-013 must not copy PR-011 unmerged implementation or redefine verification-profile/toolchain semantics.

### PR-012

PR-012 remains open and is currently Acceptance-blocked; it is not merged into `main`. Its explicit `execution_profile` implementation therefore cannot be assumed as canonical baseline. PR-013 must re-read `main` and PR-012 state at each overlapping implementation entry and keep its own `devforge_runtime` changes isolated until canonical reality changes.

### PR-010

PR-010 is canonical baseline on `main`; firewall semantics remain mandatory and must stay regression-covered.

## Requirement Traceability Assessment

- R1/R2/R4/R5/R8/R9/R11/R12/R13/R14: Plan direction is adequate in substance.
- R3/R6: blocked by F2 until materializer execution identity and scope enforcement are concrete.
- R7/R10: blocked by F1 until repository transaction scope admission/operation classes are concrete.
- R8/R9/R10: additionally blocked by F3 until publication content handoff and credential isolation are implementation-shaped.
- AC12/AC13 verification placement: blocked by F4 until implementation-vs-Acceptance authority is separated.

No Requirement semantic change is required. All four findings are `plan_local`.

## Gate Result

```text
Plan Review: Rejected
Current Gate: plan_review_rejected
Implementation Authorized: false
Execution Slice Set: not compiled
Requirement Revision: 1 unchanged
Plan Revision Reviewed: 1
```

No product implementation, Agent activation, service restart, publication, or downstream Task execution is authorized by this review.

Canonical next action:

```text
#开发计划修复 PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1
```
