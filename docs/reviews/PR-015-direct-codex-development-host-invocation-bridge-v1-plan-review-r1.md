# PR-015 — Direct Codex Development Host Invocation Bridge V1 — Plan Review R1

## Review State

```yaml
task_id: PR-015-direct-codex-development-host-invocation-bridge-v1
review_target: plan
requirement_revision: 1
requirement_blob_sha: 1bff9fc2f7c30f1ceb54bd36d2851f9b91f80b50
plan_revision: 1
plan_blob_sha: bf7eefc2bc5ebcf7bc4d45782bec3736b316eae1
reviewed_task_head: fef13d33b17d4787ed10ac58c15e0336797f70f8
result: Rejected
finding_classification: plan_local
runtime:
  devforge_version: 2.68.0
  devforge_revision: edfdaf33fc5e54964ea134b4b89ae408f52d7afd
  review_contract: "1.3"
  slicing_contract: "1.1"
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

Requirement Revision 1 remains Ready and the overall architecture direction is accepted. Plan R1 has two P0 implementation-shaping gaps that must be closed before Implementation Ready.

## F1 — Self-host bootstrap strategy is incomplete

Plan R1 correctly identifies that this Task repairs the invocation capability required by its own canonical direct/Codex provider.

It references the Task-Scoped Bootstrap Execution Override contract, but it does not identify a concrete implementation bootstrap path or the evidence required to prove that path is executable before the first implementation mutation.

Plan R2 must freeze:

1. the intended bootstrap execution target/path;
2. why that path is valid under current DevForge contracts;
3. exact Task/Plan/PR/write-scope preservation;
4. the live availability evidence required before mutation;
5. the fail-closed result when unavailable;
6. no automatic fallback.

The later bootstrap authorization remains owned by its explicit canonical command; Plan remediation must not create that authority.

## F2 — Provider-wide repository-effect/firewall composition is underspecified

The new builtin direct-Codex local-api action is a process-producing repository mutation path.

Plan R1 says existing canonical repository firewall semantics remain mandatory, but S01 does not explicitly require the new builtin action to participate in the effective local-api repository-effect inventory and provider-wide readiness calculation.

Plan R2 must require:

1. deterministic repository-effect metadata for every new builtin action;
2. fail-closed classification for uncovered/unknown actions;
3. composition of the direct-Codex builtin into local-api effect inventory/readiness;
4. regression coverage proving a newly added process-mutating builtin cannot be omitted from provider-wide firewall readiness;
5. preservation of existing devforge_runtime and canonical firewall behavior.

## Accepted Plan R1 direction

The following are not rejected and should be preserved:

- project binding remains direct/Codex;
- SentinelX is transport/policy enforcement, not the Development Host;
- production Hub remains unchanged;
- dedicated builtin local-api projection;
- closed structured invocation schema;
- fixed provider-owned executable resolution;
- provider-derived isolated workspace;
- canonical checkout remains protected;
- exact PR/branch/expected-head transport lock;
- physical Windows workspace isolation verification;
- no generic execution expansion;
- PR-013 and PR-014 remain separate Tasks.

## Gate Result

```text
Plan Review R1: Rejected
Requirement Revision: 1 / Ready
Plan Revision: 1 / Rejected
Plan Approved: false
Implementation Authorized: false
Execution Slice Set: not compiled
Current Gate: plan_review_rejected
Next Actor: planner
```

No product implementation is authorized or performed by this review.

## Required Plan R2 delta

1. freeze the concrete self-host bootstrap implementation strategy and its pre-mutation admission;
2. explicitly bind the new builtin process action into provider-wide repository-effect/firewall readiness and regression coverage.

No Requirement rewrite is requested.
