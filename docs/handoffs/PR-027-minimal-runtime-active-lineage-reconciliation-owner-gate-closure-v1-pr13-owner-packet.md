# MRS-01 / S03 — PR #13 Owner-Specific Decision & Handoff Packet

**Origin:** `PR-027-minimal-runtime-active-lineage-reconciliation-owner-gate-closure-v1`; source PR #27, branch `task/minimal-runtime-active-lineage-reconciliation-owner-gate-closure-v1`; latest canonical source ref `main@8d2bafba87b529fb458faaa7fbdce39fe225361f`.

## Owner #13 — RESHAPE / KEEP bounded security substrate

**Owner Task:** `PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1` · [PR #13](https://github.com/bewaterhere-coder/sentinelx-cloud-core/pull/13)

| Identity/Gate | 2026-10-08 fresh readback |
|---|---|
| Original branch / Head | `task/host-runtime-repository-materialization-scoped-publication-bridge-v1` @ `4a3f8e3504b65d1dc222ecb9421ffa16cd96c76d` |
| Requirement R1 / blob | `docs/requirements/PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1.md` @ `55317e8ce3fc850167a38928d448fbf76b3bc6b7` |
| Approved Plan R2 / blob | `docs/plans/PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1-plan.md` @ `e65fceea327df2820719d0feb74759e733955efb` |
| Current Task Gate | `implementation`; `plan_approved=true`; S03 pending |
| Transport | open/draft; `mergeable=false` at snapshot |
| Historical completed Slices | S01 checkpoint `d51e7ba385abcf5bf6ffa30329c9297af7191fc4`; S02 checkpoint `54e3113d3748e066598de7a986017dc73245e653`; S02 completion Receipt `3d7f108d909da74d98aa89db6f7f16b45f26502c` |

**Scope to KEEP:** minimal Host-owned short repository read/verify and bounded mutation/publication only for a verified consumer, exact admitted workspace/source identity, scoped CAS, audit/effects and independent readback. Containerized execution and credential/security controls must remain physically enforced. Reuse existing product contracts and completed Slices as immutable historical evidence; do not copy historical candidate bytes directly into current `main`.

**Scope to RESHAPE/forbid:** no SentinelX-owned full development checkout/bootstrap, long Agent orchestration, indefinite Direct Codex/CodeBuddy execution, arbitrary publication root, SSH credential leakage into AppContainer, or canonical protected-root expansion. Original S03 authorization derived from an older baseline is not independently sufficient for post-PR021 work. The Plan R2 introduction still says pending review, while Task/Review says approved; resolve stale prose through owner evidence, not an external Gate rewrite.

### Missing owner proofs / abort points

- Current `main` exact source and APIs vs. branch #13 historical candidate, with no-loss and safe transport into original PR (currently not mergeable).
- Requirement/Plan impact decision narrowing the original owner scope under PR-021; explicitly separate limited Host transaction security substrate from long development lifecycle.
- Approved **owner** Review/transition and updated Plan-bound Slice Set as required if semantics change; preserve S01/S02 Receipt lineage.
- Finite Windows Host sandbox/firewall/audit/scope verification and durable publication/readback evidence for the retained short operation.
- If transport unmergeable, security containment unproven, or owner approvals missing: **HOLD S03**; no implementation replay.

### 唯一 Owner 下一命令（建议，未执行）

```text
#开发 PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1 修订当前方案：基于当前 main 和 PR-021 Minimal Runtime，区分短时有界仓库事务安全能力与 DevForge/Guided CLI 负责的完整工作区及长 Agent 执行；保留 S01/S02 历史 Receipt；先完成原 PR #13 无损传输、当前源码和 Requirement/Plan 影响分析，禁止执行 S03 或产品 mutation，回到对应 DevForge 审查 Gate。
```

**期望返回：** 原 PR #13 上的 Requirement/Plan 影响证据、独立 Plan/Owner Decision Review、readback-verifiable Gate Transition Receipt、当前 Head/具体候选 source verification/transport receipt，且显式证明长 Agent scope 未重新引入。**当前：Owner exit Receipt 未建立，MRS01 保持 HOLD。**

## 共同权限与证据约束

本文件由 **PR #27 的 S03** 生成，只是移交给 Owner 的只读决策包；不是该 Owner 的 Requirement 修订、Plan Review、批准、实施或 Gate Transition Receipt。

- PR-021 Minimal Runtime ADR：`docs/architecture/sentinelx-minimal-runtime-boundary-v1.md` @ `36e0290de039336a8e4ce8561c22c731f12e9602`；Capability Disposition Matrix @ `05b6906614715e14450a2fd03e0699200e016074`。
- PR-023 Successor Roadmap（MRS-01）：`docs/architecture/sentinelx-minimal-runtime-successor-roadmap-v1.md` @ `8a281b60c1b8e9f5d665003a94f4f6b1d906de34`。
- 本次经批准的 Plan R1 @ `3d8b5b56e4235cdb22880ec01c45885e7fced8f6`；S02 矩阵 @ `7507dff0032f29a99387c25f648508c48a03b6e9`；S02 完成 Receipt @ `7d2c0844925e54daf0a9ca7250e4cc822c6d479d`。
- Owner 执行必须重新读取原 PR 的最新 Head、Task、Plan、审查和 Receipt；本文中的 SHA 是 **2026-10-08 S03 快照**，一旦漂移即停止按旧假设执行。
- 所有授权仍以 **Owner 原 Task、原 PR/branch、其自身独立 DevForge Gate** 为准。不得以本包修改 Owner；不得 force/rebase/close/merge、重放历史 Slice、绕过当前 Plan Review 或不经 Receipt 宣称完成。
- AppContainer、Job、MutationScope、canonical mutation firewall、审计与 effect/Receipt readback 一律保留。不得 unrestricted shell fallback、扩大 `D:\coco` protected_root 权限、借用 caller-selected host root、修改 DevForge registry 或其他 PR。
- 当前 `MRS01=HOLD`，`MRS02_admitted=false`；PR #27 产出交接文件不能改变它。
