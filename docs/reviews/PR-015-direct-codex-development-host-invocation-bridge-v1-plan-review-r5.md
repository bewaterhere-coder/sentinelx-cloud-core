# PR-015 — Direct Codex Development Host Invocation Bridge V1 — Plan Review R5

## Review State

```yaml
task_id: PR-015-direct-codex-development-host-invocation-bridge-v1
review_target: plan
requirement_revision: 2
requirement_blob_sha: c21ee726db19afa51b27003a381f739c81ddcfc3
plan_revision: 5
plan_blob_sha: c45a373e4f7a62ae11fceba89316dd8cf6353969
reviewed_task_head: 81e90e0c25f636c402a6e83566be4c662c4c498f
result: Rejected
finding_classification: plan_local
runtime:
  devforge_version: 2.82.0
  devforge_revision: 748004cc3ec3932e5c4106e0d62ff06b19c5f883
  review_contract: "1.3"
repository_reality:
  canonical_main: 018b78ca20984176d53fbe90039dc795a7f2742f
  canonical_pr: 15
  canonical_branch: task/direct-codex-development-host-invocation-bridge-v1
  project_provider: direct
  project_adapter: codex
next_gate: plan_review_rejected
next_expected_actor: planner
```

## Decision

**Rejected.**

Plan R5 successfully closes the R4 Windows canonical-blob problem at persistence time. The candidate-side design now correctly separates safe Git builtin clean normalization from external/custom process-filter authority.

One remaining P0 implementation-shaping gap exists earlier in the lifecycle: **physical checkout materialization is not yet governed by the same normalization/filter authority boundary**.

No Requirement Revision 3 is needed.

## F1 — Checkout materialization can execute or depend on attribute/filter authority before persistence checks

Current PR-015 transport implementation obtains the independent checkout through fixed active-user Git calls equivalent to:

```text
git clone --no-checkout ...
git checkout --force -B <branch> <expected_sha>
```

The checkout call is routed through `run_user_scoped_git` under the active user's normal Git environment. It does not currently establish the R5 local-candidate config/attribute clamp before worktree materialization.

Plan R5 captures `core.autocrlf/core.eol/core.safecrlf` **after** exact checkout and rejects custom `filter` attributes only during later candidate persistence.

That is too late for two reasons.

### Security

A versioned `.gitattributes`, global/system attributes source, or equivalent attribute authority can bind a path to a custom smudge/process filter. If matching filter-driver configuration is visible to the active-user Git process, checkout can execute that external process **before Codex starts and before the R5 persistence precheck**.

The persistence broker must not claim "external filter/process authority is forbidden" while the same direct-Codex lifecycle allows such authority during checkout.

### Canonicalization consistency

Even when no external process executes, checkout may be materialized under one set of global/system attributes/config while persistence later disables those sources and replays only the R5 safe scalar config.

If checkout bytes were produced using attribute semantics that persistence does not replay, the clean conversion is not guaranteed to be the inverse of checkout conversion. The Windows CRLF issue can therefore reappear through attribute provenance rather than `core.autocrlf` alone.

Fresh repository evidence confirms the current code does not yet provide this pre-checkout clamp:

- `direct_codex_transport.bootstrap_execution_checkout` calls fixed `run_user_scoped_git(..., "checkout", "--force", "-B", ...)`;
- `user_git` provides noninteractive guards but does not make checkout use the R5 candidate-local config/attribute isolation contract.

On the current host the directly inspected user/system `.gitattributes` files are empty, so this is not evidence of an active incident. It is a Plan-level authority/correctness gap in the bounded Windows provider contract.

## Required Plan R6 correction

Plan R6 must make **checkout materialization and later candidate clean conversion share one provider-owned normalization/attribute authority contract**.

At minimum:

1. after clone/fetch has obtained the exact commit but **before any checkout/worktree materialization**, read the allowlisted safe scalar normalization config required by the active user's checkout semantics;
2. freeze and persist/read-back that snapshot before checkout;
3. inspect the expected commit's versioned attribute rules sufficiently to detect any custom/external `filter` assignment that could affect checkout, and fail closed before materialization;
4. exclude/neutralize system/global attribute sources for checkout, or prove them empty/unsupported and bind that proof into the snapshot;
5. require `.git/info/attributes` to be absent/empty before checkout;
6. run checkout with provider-clamped local Git configuration:
   - replay only the frozen safe normalization scalars;
   - no external filter-driver configuration;
   - no hooks/signing/fsmonitor/editor/pager/prompt execution authority;
   - no arbitrary user/repository config;
7. use the **same frozen normalization/attribute authority snapshot** later for provider temporary-index clean conversion;
8. any snapshot/attribute drift between checkout and persistence fails closed;
9. focused tests must prove a repository `.gitattributes` custom filter cannot execute during checkout, not merely during staging;
10. focused tests must prove checkout-induced CRLF expansion under the frozen snapshot re-canonicalizes to the parent LF blob during persistence.

A conservative V1 may reject repositories/paths requiring custom filter drivers entirely. It does not need to support external filters.

## Accepted Plan R5 direction

The following remain accepted and should be preserved in R6:

- provider-owned deterministic commit-on-publish;
- Codex remains Development Host;
- one new S04 delta only; S01-S03 remain retained evidence;
- Codex-owned index remains untrusted;
- provider-owned temporary candidate index;
- safe builtin text/eol/binary/ident/working-tree-encoding clean semantics;
- raw Windows worktree bytes are not canonical blob authority;
- custom external filters are forbidden;
- recovery journal and frozen commit-SHA inputs;
- bit-identical same-attempt candidate reconstruction;
- `publish_intent` before first push;
- uncertain publication => readback only, no automatic re-push;
- ordinary fast-forward publication;
- no force/force-with-lease;
- no replacement branch/PR;
- no canonical checkout mutation;
- no generic Git/shell surface;
- no permission/credential expansion;
- prior CodeBuddy override remains expired.

## Gate Result

```text
Plan Review R5: Rejected
Requirement Revision: 2 / Ready
Plan Revision: 5 / Rejected
Plan Approved: false
Implementation Authorized: false
Formal Plan R5 Slice Set: not compiled
Current Gate: plan_review_rejected
Next Actor: planner
```

No product implementation, new bootstrap override, live Agent mutation or transport mutation is authorized by this review.

## Required Plan R6 delta

Freeze one shared **pre-checkout + persistence canonicalization authority snapshot** and ensure custom/external filters cannot execute at checkout or persistence time.

No other architecture change is requested.
