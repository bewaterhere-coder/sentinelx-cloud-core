# PR-014 Requirement R4 Change Impact — 2026-10-08

- Trigger: user explicitly directed PR-021 Minimal Runtime architecture reconciliation on the same Task/PR.
- Supersedes Requirement R3 materialization/handoff Goal and Plan R7 rejected review; R4 normative clause takes precedence over incompatible historical R1–R3 passages.
- Removed: long Agent/Direct CodeBuddy/Codex bootstrap, user-level Development Host lifecycle/ACL handoff, generic Git source capsule and full checkout materialization.
- Retained: shortest necessary synchronous short-mutation workspace isolation, independent Host-owned canonical source/execution placement, protected-root/canonical firewall, exact MutationScope, additive durable schema compatibility including runtime_read_authority_roots, audit START, AppContainer/ACL/Job confinement, readback and terminalization.
- Finding F1 PR021MinimalRuntimeDispositionNotConsumed: resolved at **Requirement scope**; subject to next Plan Review.
- Finding F2 CanonicalMainImplementationSurfaceMismatch: NOT yet resolved as product ownership; converted to explicit read-only S03A topology/consumer admission gate before any code mutation. Do not pretend historical branch is merge-ready.
- Historical S01/S02 evidence and candidate 45dc99d15a23c499b4c1500fab60ed5e76475aeb preserved with no replay/promotion.
- Replanned R8 on existing PR #14 and existing branch. No product, Host policy, main, or CI mutation.
- Next review: #开发评审 PR-014-devforge-execution-workspace-materialization-bridge-v1. Reviewer must reject if the topology gate is bypassed, and must not permit S03B until S03A is read back.
