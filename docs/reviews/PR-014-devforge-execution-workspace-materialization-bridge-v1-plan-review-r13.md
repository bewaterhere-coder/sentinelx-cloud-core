# PR-014 — Plan Review R13

Decision: **Rejected** (product implementation admission not established).

Review identity: Requirement R8; Plan R13 blob `63b9467a70992964ecdc360cad432604abb68766`; PR #14 existing branch `task/devforge-execution-workspace-materialization-bridge-v1`. Current GitHub main `5d9286b22f46ae8bdf6d983b6366da0da3f1323e`. Compared branch: 155 ahead, 600 behind, PR mergeable=false.

## Passing controls
- PR-021 minimal-runtime boundary and prohibition of long-agent/materialization lifecycle retained.
- Host Sandbox/Audit already PASS; no redundant MutationScope rewrite required.
- Firewall is fail-closed while `local_api:direct_codex_containment_unproven`.
- Protected `D:\coco` unchanged; historical S01-S06A not replayed.

## Blocking findings

**R13-F01 — Unadmitted transport / exact product source (P0).** Existing #14 branch is materially divergent and nonmergeable. The plan says "separately reviewed no-loss transport normalization" will be produced later, but specifies neither executable normalization method nor exact readback/abort evidence that would make S07 product edits safe. Plan approval cannot admit product mutation conditional on a separate undefined review; no destructive rebase/cherry-pick/force push allowed.

**R13-F02 — S07 decision and executable impact undefined (P0).** Disabling the projected Direct Codex endpoint versus proving physical containment materially changes product/Host scope and observed capability. R13 has alternatives, not a frozen minimal product delta with precise current-main blob ownership and negative reachability tests. Runtime surface may need to be held fail-closed pending a separate owner/policy decision. No product S07 can be authorized yet.

**R13-F03 — S08 conditional, unproven consumer (P1).** Placement implementation is contingent on demonstrating actual short-mutation need, Host-owned independently placed root and no protected-root overlap. These are admission inputs, not implementation conclusions. A conditional implementation slice cannot be approved now.

**R13-F04 — S09 depends on unadmitted product and Host changes (P1).** Physical integration and rollback cannot be authorized ahead of exact candidate, effective policy/deployment control and required Host approval.

## Mandatory minimum remediation

Keep Requirement R8 and original PR #14. Do not create a new Task, branch or PR. Replace R13's implementation slice proposal with **one read-only decision/admission slice**, which must:
1. Establish current main exact-source/file/test ownership and no-loss existing-PR transport mechanics, otherwise STOP `TransportBlocked`.
2. Compare Direct Codex effective reachability and fail-closed disablement vs physical containment; record the chosen owner-authorized path, otherwise `DecisionRequired/Blocked`.
3. Determine whether an independent execution root is required by a real bounded short-mutation consumer; omit implementation if absent.
4. Emit durable decision receipt; no product/Host/main mutations, no prior slice replay. Only a separate later reviewed exact product Plan can admit S07/S08/S09.

No new Slice Set compiled; no implementation authorization.

Next: `#开发计划修复 PR-014-devforge-execution-workspace-materialization-bridge-v1`.
