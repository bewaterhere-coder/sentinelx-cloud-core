# Provisional DevForge Intake — Direct Codex Host-owned Fail-Closed Disablement and Negative Reachability V1

> This is a **provisional creation artifact**, not a canonical Requirement, Task ID, execution approval, or product implementation. GitHub must allocate the PR number first. The canonical Task Markdown is created after that number is read back.

Project: `sentinelx-cloud-core`
Repository: `bewaterhere-coder/sentinelx-cloud-core`
Canonical main at intake: `2e5c69a112323867ee01783521554c43ebd731be`
Provisional branch: `task/direct-codex-host-owned-disablement-negative-reachability-v1`

Owner direction: fail-close every SentinelX-exposed `devforge_direct_codex.execute_task` path through Host-owned policy. Preserve independent local CodeBuddy/Codex CLI and short `devforge_runtime`; do not expand SentinelX long-Agent Runtime.

Upstream source:
- PR #14 Owner Decision: `docs/reviews/PR-014-devforge-execution-workspace-materialization-bridge-v1-owner-direct-codex-disablement-decision-r1.md` on the original PR #14 branch, commit `412509bd7d2db4484ea8b4916984f79eb5052e7e`.
- Frozen PR-021 Minimal Runtime architecture and capability disposition rule requiring a separate DevForge Task for provider disablement.

Security definition of done: effective Host config and runtime readback; enumerate builtin and external `local_apis` aliases; no `execute_task` reachable under real effective policy; safety-guarded negative invocation; no process/workspace/repository mutation; Canonical Firewall PASS genuinely re-evaluated; Sandbox/Audit retained; exact Host receipt. A list omission alone is insufficient.

**No Host mutation, product source change, PR #14 transport surgery, or implementation is authorized by this provisional intake.**
