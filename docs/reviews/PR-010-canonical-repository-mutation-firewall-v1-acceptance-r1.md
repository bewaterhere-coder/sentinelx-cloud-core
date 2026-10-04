# PR-010 — SentinelX Provider Canonical Repository Mutation Firewall V1 — Acceptance R1

## Decision

```yaml
task_id: PR-010-canonical-repository-mutation-firewall-v1
requirement_revision: 2
plan_revision: 4
acceptance_revision: 1
result: Approved
canonical_transport: github-pr
pr_number: 10
canonical_branch: task/canonical-repository-mutation-firewall-v1
evaluated_head: ab7c09d9e7e320a3265030f1d27267d934465c48
current_stage: accepted
gate_transition: acceptance_to_accepted
acceptance_approved: true
completion_verified: false
```

**PR-010 Acceptance R1: Approved.**

Requirement Revision 2 is satisfied on the canonical PR transport. Approval enters the DevForge `accepted` boundary only. It does not perform merge/integration, release, production Host activation, or a `done` claim.

## Runtime / Transport Consistency

PASS.

- DevForge Runtime source of truth: `bewaterhere-coder/DevForge main@c6972894f187da7d41e384bfbc663a1ae06d1e35`.
- Acceptance Contract: `contracts/development/acceptance-contract.md` v1.5.
- Canonical repository: `bewaterhere-coder/sentinelx-cloud-core`.
- Canonical PR: #10.
- Canonical branch: `task/canonical-repository-mutation-firewall-v1`.
- Evaluated head: `ab7c09d9e7e320a3265030f1d27267d934465c48`.
- Canonical main at Acceptance: `df9252fd4305eed361d8dc84e04da90222cd622e`.
- No TransportDrift is present.

The evaluated head is one evidence-persistence commit ahead of verified S05 product head `c08e46dfce287213b7b3760a322c2a53eb6acdc6`. Exact compare shows only S05 completion/final-reconciliation checkpoints and Slice Set state changed; no product code changed after the verified product head.

GitHub currently reports PR #10 `mergeable=false` against the newer `main`. This is not represented as integration success. Per Acceptance Contract v1.5, integration belongs to `#开发完成`; completion finalization must reconcile current `main` and verify the resulting integration before any `done` claim.

## Requirement Change Guard

PASS.

- Requirement Revision 2 is current.
- Plan Revision 4 is approved/current.
- S01-S05 completion evidence is all Revision-2 / Plan-R4 evidence.
- The former Hub-projection requirement was superseded by Requirement Revision 2; Hub projection is explicitly non-blocking when Core-owned evidence exists.
- PR-007 is completed and merged; final reconciliation found no post-acceptance PR-007 product/capability/local_api/mutation-scope/executor seam change requiring replay.
- PR-008 remains unchanged at `f7594c468d764ad85c0dc508ad47f009c89793c1`.
- PR-009 remains independent/non-blocking.

No stale Requirement-1 Hub evidence is used to satisfy Acceptance.

## Fresh / Durable Verification

PASS.

### S05 exact product-head evidence

Verified product head: `c08e46dfce287213b7b3760a322c2a53eb6acdc6`.

- `pr010-s05-verification` run `37078293416`: success.
- `macos-agent` run `37078293526`: success.
- local Python validator: success.
- local YAML validator: success.
- `git diff --check`: success.

### Retained slice evidence

- S01 verified head `69dfdef75bc14ef2df445fa01ddd8d436868daa5`; Windows focused, CI, macOS all success.
- S02 verified head `a7978ff29c47e1831dfd835ae840d0ce91ce5987`; Windows focused, CI, macOS all success.
- S03 verified head `4c23087b50ba4e27a53fc884699377e4d5762e0d`; S03/S02/S01 focused regressions, CI and macOS all success.
- S04 verified head `f7a4731638de19513aa3f6247fa38d8b81d2f97d`; S04/S03/S02/S01 focused regressions, CI and macOS all success.

## Acceptance Matrix

- **A1 / R1 — PASS:** Host-authoritative canonical inventory is distinct from generic protected/workspace roots; traversal/symlink/ambiguity fail closed and broad parent `file_ops rw` does not remove canonical role.
- **A2 / R2 — PASS:** canonical inventory and existing consumers share `sentinelx_core.mutation_placement.RepositoryIdentity`; parallel policy normalization was removed; credentials are excluded, explicit ports preserved, `.git` normalized, invalid authority/traversal fail closed. Existing normal repository identity/digest compatibility is pinned; incompatible legacy schemed/credential-bearing bindings require reprovision rather than silent aliasing.
- **A3 / R3 — PASS:** one reusable Core canonical firewall/admission seam supplies stable allow/block/indeterminate behavior and is consumed before material mutation.
- **A4 / R4,R5 — PASS:** structured edit/file/upload/Git mutators are covered before backup/write/delete/patch/final materialization; incident regressions prove blocked canonical edit/delete creates no `.bak`/partial side effect and structured Git mutation blocks while read-only Git remains available.
- **A5 / R6 — PASS:** process-producing operations are accounted for by Core-owned effect/disposition semantics. Generic `exec`, legacy/unprofiled script paths and unknown/conflicting profiles cannot coexist with advertised readiness without proven physical coverage; `scoped_mutation` composes existing Host scope/sandbox/audit authority. Shell/path-string heuristics are not used as security proof.
- **A6 / R7,R8 — PASS:** dispatch and firewall coverage share the authoritative operation/effect registry. Unknown top-level operations, Git selectors, local_api endpoint/actions, required-but-unproven mutations, and readiness-probe failures remove capability readiness. Core hello/capability output uses the same readiness predicate. Windows may advertise only on complete proof; Linux/macOS remain unavailable without equivalent physical proof.
- **A7 / R9,R10 — PASS:** generic tools have no `canonical_sync` escape hatch; canonical read/list/search/status/diff remain usable; same-repository non-canonical execution workspace passage is exclusion evidence only and remains governed by existing scope/file/sandbox/audit authority.
- **A8 / R11 — PASS:** S05 freezes the Windows incident matrix including broad-parent-rw canonical writes, backup-producing edit/delete, structured Git patch, generic/child/background process cases, indeterminate classification, fake canonical_sync, read-only access, workspace behavior and mixed-operation unknown-effect readiness failures.
- **A9 — PASS:** affected security/regression workflows pass; no unrestricted fallback, permission/allowlist expansion, duplicate executor/store/sandbox/audit authority, canonical-checkout mutation, canonical-main mutation by PR-010 execution, or Hub modification was introduced.
- **A10 — PASS:** README/config/threat-model documentation describes Host inventory/readiness, fail-closed effective-surface accounting, Windows/platform availability, same-repository workspace distinction, repository-identity reuse semantics, Core-vs-scoped authority boundary, and the immutable third-party Hub transport boundary. No Hub implementation or deployment change is claimed.

## Integration Boundary

Acceptance approves the implementation evidence only. The current PR is not claimed integrated.

`main` advanced through completed PR-007 after much of PR-010 was developed. S05 final reconciliation verified that PR-007 post-acceptance movement changed finalization/integration artifacts only and that the product semantics already composed by PR-010 did not require replay. Nevertheless, GitHub's current mergeability result is false; `#开发完成` must perform current-main integration reconciliation, resolve any textual/branch conflict without losing either PR's semantics, rerun required verification on the integration candidate, and persist an Integration Receipt before completion can be verified.

## Acceptance Result

```text
Acceptance Approved: true
Completion Verified: false
Result: Approved
Gate Transition: acceptance -> accepted
Current Stage: accepted
```

Per Acceptance Contract v1.5, the canonical next action is:

`#开发完成 PR-010-canonical-repository-mutation-firewall-v1`
