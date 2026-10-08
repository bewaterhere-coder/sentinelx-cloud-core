# PR-029 — Plan R1 Rejection Remediation (Plan R2)

```yaml
task_id: PR-029-direct-codex-host-owned-disablement-negative-reachability-v1
source_command: "#开发计划修复 PR-029-direct-codex-host-owned-disablement-negative-reachability-v1"
owner_stage_before: plan_review_rejected
owner_stage_after: plan_review
reviewed_plan_before_revision: 1
reviewed_plan_before_blob: 17c3846423bc40b9e836f8713e5ffa2f20a55376
rejected_review_ref: docs/reviews/PR-029-direct-codex-host-owned-disablement-negative-reachability-v1-plan-review-r1.md
rejected_review_blob: 4e0663bc1288487699d2eb590e427f7eb78acf89
revised_plan_revision: 2
revised_plan_blob: 300b1adc237dd4220d866ecdeb4047880d203874
task_blob_before: 385129f8668002a8786023ecb43bb6a4122b78f3
task_blob_after: 983c9ccba0b94e2f21088f3e6b9763289f9ccc82
plan_approval: false
implementation_authorized: false
host_mutation_authorized: false
negative_call_authorized: false
current_plan_executable_slice_set_compiled: false
```

## Applied corrections

| R1 finding | Remediation in Plan R2 | Truth boundary |
| --- | --- | --- |
| R1-F01: active consumer dependency | Added mandatory G1 consumer matrix: DevForge `direct/codex` binding; PR-019 stabilization testing; Harness; guided CLI evidence, plus explicit migrated/Owner HOLD/DecisionRequired states before Host change | Owner choice selected, but consumer retirement/migration **not** resolved |
| R1-F02: abstract Host mutation authority | Current Plan reduced to **exactly one proposed S01 read-only** investigation; G2/G4 identify real owner-controlled policy write/reload, effective digest/CAS/rollback channels or block | No Host config write, reload or mutation admitted |
| R1-F03: unsafe negative invocation | S01 expressly forbids `local_api.call`; G3 captures builtin/external alias precedence and needed same-policy-generation safety proof | No invocation, `invalid_payload` cannot prove denied |
| R1-F04: rollback / telemetry coverage | G5 demands actual process-creation audit (including short-lived children), workspace/Git and service telemetry; future recovery may never restore unsafe enabled state | Missing channels become `DecisionRequired/Blocked` |

### Deliberately deferred work

The prior R1 S02 (live config mutation), S03 (real negative invocation), S04 (focused regression) are **not included in the R2 executable plan**. A later Plan Revision on original PR #29 needs an independent Plan Review, Owner consumer disposition and exact physical security evidence. R2 approval, if obtained, can authorize only bounded read-only S01 and task-owned documentation/receipts.

### Identity, authority and readback

- Repository `bewaterhere-coder/sentinelx-cloud-core`; original PR #29 and branch `task/direct-codex-host-owned-disablement-negative-reachability-v1`.
- Canonical `main@2e5c69a112323867ee01783521554c43ebd731be`; DevForge `main@047df4f1c45ce9099ec112017063751243c78d7b`.
- Requirement R1 remains unchanged **semantically**, with acceptance criteria AC01–AC08 intact; no upstream Requirement change and no Task reallocation.
- Owner-selected Host-owned Direct Codex disablement and PR-021 Minimal Runtime constraints preserved; PR #14 and PR #19 untouched; MRS-01 HOLD.
- Plan remediation has no approval authority. **Next:** `#开发评审 PR-029-direct-codex-host-owned-disablement-negative-reachability-v1` to independently approve/reject current exact Plan R2 and decide whether to compile an S01-only Slice Set.
