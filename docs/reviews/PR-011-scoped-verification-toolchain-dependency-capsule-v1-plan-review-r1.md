# PR-011 — Scoped Verification Toolchain & Dependency Capsule V1 — Plan Review R1

## Review State

```yaml
task_id: PR-011-scoped-verification-toolchain-dependency-capsule-v1
review_target: plan
requirement_revision: 1
requirement_blob_sha: c3058b742d77313256b4c40236b9bee3cb64e4a0
plan_revision: 1
plan_blob_sha: 0ecca078bfaf01131c293c1d7b16e6f28ba60cd8
reviewed_task_head: 2668a9ae26f028fb19f7921b8164b177530da02c
result: Rejected
finding_classification: plan_local
runtime:
  devforge_version: v2.34.0
  devforge_revision: e0fe219252b160ec35d7349bb1dc27c16227229a
  project_development_workflow: "2.1"
  review_contract: "1.3"
next_gate: plan_review_rejected
next_expected_actor: planner
```

## Scope Reviewed

- Canonical Requirement Revision 1.
- Canonical Plan Revision 1.
- `sentinelx-cloud-core/main@f7e878f3497582547e5d52cd33b060cae18d2e84` repository reality.
- PR-007 current state: accepted but unmerged; `devforge_runtime` remains outside `main`.
- PR-010 current state: implementation, S01-S03 completed and S04 pending; canonical-repository firewall work remains unmerged.
- DevForge `main@e0fe219252b160ec35d7349bb1dc27c16227229a` / v2.34.0 and Review Contract v1.3.

## Decision

**Rejected / Changes Requested.**

The architecture direction is sound: keep the existing Scope/AppContainer/Job/audit executor, add provider-owned logical verification profiles, use immutable offline dependency capsules, keep network/credentials/canonical checkouts outside the sandbox, and gate `devforge_runtime` integration on exact PR-007/equivalent admission.

Plan Revision 1 nevertheless has two implementation-shaping gaps that can make a successful verification receipt cease to mean "the intended repository revision was actually checked". Both are Plan-local and can be remediated without changing the Requirement goal.

## Blocking Finding F1 — Source-under-test materialization and pre-toolchain identity binding are missing

### Evidence

The Plan defines dependency materialization only:

```text
admitted dependency capsule
→ <exact-workspace>/.sentinelx-verification/npm-cache
```

It does not define how the actual package under test (`package.json`, `package-lock.json`, TypeScript sources, tests, tsconfig, etc.) is materialized into the exact execution workspace.

This is material for the downstream proof. A fresh provider-owned Scope is not the canonical repository, and the current PR-007 `devforge_runtime.execute_scoped` contract carries script content/cwd/env plus scope/repository/lineage; it does not provide a source-tree/materialization parameter or authority. The Plan also explicitly preserves the rule that the AppContainer cannot read the canonical checkout and cannot fetch source from the network.

Plan Section 9 currently permits `package-lock.json` to be absent before the root process SPAWN and to be checked only after the verification script has materialized/prepared the package workspace. That is too late for a dependency-backed truth claim: the script can spawn Node/npm descendants before the provider has proven that the package-under-test lockfile matches the capsule/expected digest.

Therefore a successful process exit could prove that *some script-created workspace* passed, without proving that the exact current Task/PR source revision passed.

### Required remediation

Revise the Plan to define one bounded source-under-test admission path before any profiled Node/npm child is allowed to execute. The plan may reuse an admitted DevForge execution-workspace materialization capability or define an equivalent provider-owned, integrity-bound source snapshot seam, but it must not mount/read the canonical checkout from the AppContainer or grant arbitrary caller-selected Host paths/network authority.

The revised Plan must freeze at least:

1. the source identity bound to verification (repository identity + exact transport/commit/head identity or equivalent immutable source digest);
2. how source bytes are materialized into the exact workspace and how their manifest/digest is read back;
3. that `package-lock.json` is present and SHA-256 verified **before the first Node/npm/toolchain process or descendant can execute**;
4. that source materialization cannot write outside the exact workspace and cannot smuggle Host paths/credentials;
5. the downstream PR-015 procedure that binds the disposable verification workspace to the exact PR-015 head and `mcp/` package bytes without replaying PR-015 implementation side effects.

A post-run lockfile check may remain as tamper detection, but it cannot substitute for the pre-toolchain binding.

Required tests must include wrong source-head/source-manifest, wrong lockfile, source mutation before toolchain execution, and proof that the receipt identifies the admitted source revision/digest.

## Blocking Finding F2 — Toolchain/capsule request-time integrity and bounded materialization are under-specified

### Evidence

The Requirement requires machine-readable toolchain provenance/integrity evidence and bounded capsule materialization. Plan Revision 1 names `toolchain_digest` / `toolchain provenance digest` but does not freeze what bytes/metadata participate in that digest or how request-time execution proves the resolved Node/npm files still match it.

The proposed profile verifies `node.exe` and `npm-cli.js`, while execution examples invoke `npm` through `PATH`. The Plan does not freeze whether `npm.cmd`/`npm.ps1`, a provider-generated shim, or `node <npm-cli.js>` is authoritative. That leaves room for the receipt to hash one set of files while execution resolves another.

The risk section also says to "bound capsule size/file count" but defines no admission-time limits/defaults/policy fields. A provider-owned capsule can therefore be integrity-valid yet still cause unbounded copy/disk/time consumption before verification fails.

Finally, Node/npm readiness is cached for the Agent lifetime in the existing readiness model. The Plan requires a real readiness probe but does not explicitly require request-time integrity revalidation of the selected toolchain/capsule after that cached probe. A toolchain changed after readiness could otherwise remain advertised until restart.

### Required remediation

Revise the Plan to freeze:

1. a deterministic `toolchain_digest` algorithm over the exact executable/CLI components that can participate in execution, including normalized relative identities and hashes plus the profile contract revision;
2. one authoritative npm launch mechanism (for example provider-resolved `node.exe + npm-cli.js` or a provider-generated workspace-local shim) so execution cannot resolve an unhashed Host launcher via PATH;
3. request-time final-path/hash revalidation of the selected toolchain and capsule before START/SPAWN, independent of cached capability readiness;
4. explicit capsule bounds (maximum total payload bytes, file count, per-file size/path length as appropriate) enforced before/materially during copy with a stable fail-closed error;
5. negative tests for post-readiness toolchain replacement/tamper, launcher substitution, oversized capsule/file-count exhaustion, and partial-copy cleanup.

The exact numeric defaults may be configurable provider policy, but V1 must define safe defaults and hard upper bounds rather than leaving them implementation-defined.

## Related-Task Assessment

### PR-007

PR-007 is now **accepted but unmerged**. This improves feasibility but does not change repository ancestry. Plan Revision 1 correctly keeps core profile/capsule work independent and forbids silently copying unmerged `devforge_runtime` code. Step E remains dependency-gated and is not itself a rejection reason.

### PR-010

PR-010 remains in implementation with S04 pending and has not merged. Its current S03 direction treats `scoped_mutation` as the physically constrained process path and leaves unproven process classes fail-closed. That is compatible with PR-011's direction. Fresh overlap reconciliation at each implementation entry remains required. No current PR-010 fact justifies weakening canonical-repository protection.

## Reviewer Notes — Non-blocking

### N1 — Existing audit journal is sufficient in principle

A separate durable verification journal is not required if the revised Plan seals source identity + verification admission into the existing START evidence digest and returns bounded verification evidence from the same operation lineage.

### N2 — Offline dependency capsule direction is valid

An immutable npm-cache capsule copied into exact-workspace mutable cache is a valid V1 direction, provided F1/F2 preconditions are satisfied and no network fallback exists.

### N3 — PR-007 dependency terminology

The Requirement's foundation block uses `current_task_p0_dependencies` for PR-007 while the development-start receipt treats it as an integration-only dependency. The intent is clear from R7/Plan Step E: it blocks `devforge_runtime` integration/AC9, not the independent core slices. The revised Plan should keep this slice-local dependency explicit so Implementation Ready does not falsely claim Step E is currently executable.

### N4 — Cross-repository AC12 remains separately authorized

PR-011 cannot inherit authority to mutate or complete ChatGPTControlShell PR-015. The downstream proof may consume a separately authorized PR-015 execution receipt; PR-011 Acceptance must not synthesize that receipt.

## Requirement Traceability Assessment

- R1/R2/R5/R6/R7/R9: overall design direction is feasible and scope-controlled.
- R3/R4/R8: F2 blocks approval because the integrity/boundedness contract is not yet sufficiently implementation-shaped.
- R10 / AC12: F1 blocks approval because the Plan currently lacks a truthful source-under-test projection into the isolated workspace.
- AC3/AC4/AC5/AC6/AC7/AC8/AC9/AC10/AC11: direction is testable once F1/F2 are repaired.

## Gate Result

```text
Plan Review: Rejected
Current Gate: plan_review_rejected
Implementation Authorized: false
Execution Slice Set: not compiled
```

No product implementation, Host policy, Agent installation, or downstream Task mutation is authorized by this review.

Canonical next action:

```text
#开发计划修复 PR-011-scoped-verification-toolchain-dependency-capsule-v1
```
