# PR-007 — Host Mutation Scope Control Surface & MCP Admission Bridge V1 — Acceptance R1

## Decision

```yaml
task_id: PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1
acceptance_revision: 1
result: Rejected
finding_classification: external_blocker
external_blocker: HubGenericOpProjectionRequired
canonical_transport: github-pr
pr_number: 7
canonical_branch: task/host-mutation-scope-control-surface-mcp-admission-bridge-v1
evaluated_head: fc760a033b991072405fc2a19bdb31f5d39ab8c9
next_stage: fixing
fixing_disposition: blocked_external_dependency_no_local_code_churn
acceptance_approved: false
completion_verified: false
```

**PR-007 Acceptance: Rejected.**

Repository-local implementation quality and the provider-owned security boundary are substantially verified, but the Task cannot enter `accepted` because Acceptance Criterion A7 is not satisfied: the live generic Hub `/op` projection still does not expose or route `mutation_scope` end to end.

This is an external Hub projection blocker, not a repository-local implementation defect. No unrestricted fallback, caller-minted scope authority, dedicated-Hub-tool claim, or local workaround is authorized by this finding.

## Runtime / Transport Consistency

PASS.

- DevForge Runtime: `bewaterhere-coder/DevForge main@9e0ec1aae06690840d8946d39460e7cb28ef36d1`, version `2.31.0`.
- Acceptance Contract: `contracts/development/acceptance-contract.md` v1.5.
- Canonical repository: `bewaterhere-coder/sentinelx-cloud-core`.
- Canonical PR: #7.
- Canonical branch: `task/host-mutation-scope-control-surface-mcp-admission-bridge-v1`.
- Evaluated Task head: `fc760a033b991072405fc2a19bdb31f5d39ab8c9`.
- S01-S05 evidence is stored on the same canonical Task transport.
- No alternate branch/PR is accepted as implementation transport and no transport migration is authorized.

No `TransportDrift` is identified.

## Requirement / Scope Guard

PASS.

The approved Requirement explicitly requires live generic Hub `/op` proof for A7 and separately requires truthful external-dependency recording for A8 when that relay cannot carry the lifecycle operation or scoped payload. The approved Plan likewise states that Hub inability to route the operation is an external dependency and is not a reason to weaken Host authority.

Accordingly, repository-local completion of S05 is not equivalent to Acceptance approval. S05's completion rule permits a precise external blocker so implementation can reach the Acceptance gate; it does not waive A7.

## Positive Evidence Retained

### A1 / R1,R9 — PASS

The Agent operation `mutation_scope` is registered and dispatchable through the normal registry; `ops_supported` derives registry truth; disabled-op behavior removes advertisement/reachability. S03 focused verification passed 7/7 tests.

### A2 / R2,R4 — PASS

Provider-owned provisioning/idempotency semantics are covered by the S01/S02 implementation and focused verification. S02 lifecycle handler verification passed 15 tests and retained the existing `MutationScopeStore` as the sole authority.

### A3 / R2,R3 — PASS

Caller-selected path/operation-class authority is rejected; repository and semantic lineage binding remain exact; operation-class admission occurs before material mutation. S01 focused admission tests passed and no duplicate authority/readback path was detected.

### A4 / R3,R6 — PASS

Current Host readiness is live and verified for Windows AppContainer/ACL/Job/audit/scope enforcement. Exact binding/revalidation remains fail closed.

### A5 / R5 — PASS

Terminal/non-current bound readback is non-reactivating. S04 security verification confirms terminal scope remains inspectable without reactivation.

### A6 / R7,R8 — PASS

S04 exercised the existing `script_run` scoped-mutation path with provider-issued authority. The Windows security matrix passed 13 tests with 1 explicit skip, including audit ordering, AppContainer/Job containment, terminalization and the `INCIDENT-20260927-D-ROOT-RECURSIVE-DELETE` protection. No unrestricted fallback was introduced.

### A8 / R11 — PASS

The implementation and evidence do not claim end-to-end MCP admission. The live failure is explicitly classified as `HubGenericOpProjectionRequired`, with the repository boundary preserved.

### A9 — PASS

Fresh S04 security evidence keeps scope uniqueness, AppContainer containment, START-before-spawn, terminal closure and the canonical destructive-escape incident protection green.

### A10 / R9,R11,R12 — PASS

Registry/help/documentation truthfully distinguish operation discoverability from scoped-mutation readiness and do not claim a dedicated Hub MCP tool. Bounded diagnostic evidence is preserved without exposing unrestricted filesystem authority or secrets.

### A11 / R13 — PASS

Legacy/public operations remain compatible; unknown/disabled registry operations fail closed as `unsupported_op`. The ordinary model-facing `sentinel_script_run` projection remains an independent PR-008/Hub boundary rather than being silently widened by PR-007.

### A12 — PASS for repository-local implementation evidence

Affected focused tests and compile/diff checks are durable across S01-S04. The current Task head contains the S05 completion checkpoint and no later product mutation after that checkpoint. GitHub currently reports no commit-status/check-run evidence for this head, so CI is not used as positive evidence.

### A13 / R14 — PASS

The accepted provider authority model does not make a fixed host ID, hostname, workspace path, install path, release version, credential or machine-specific identity canonical authority.

## Blocking Finding

### F1 — A7 / R10 — Live generic Hub `/op` admission is not proven

The exact live candidate is active as Agent `0.24.1.dev58+g21b2cb154`. Fresh Host capability readback shows:

- `mutation_scope` is present in Agent `ops_supported`;
- `host_mutation_sandbox_v1` is available and verified;
- `pre_execution_audit_lineage_v1` is available and verified;
- `script_run_execution_profile_v1` advertises `scoped_mutation` readiness as available and verified.

However, a fresh short-lived Hub REST contract obtained during this Acceptance still lists the generic `/op` catalog without `mutation_scope`. This independently reconfirms the S05 live evidence where `/op capabilities` succeeded but `/op mutation_scope/provision` returned HTTP 500 before the Agent handler created durable scope authority.

Therefore the required live sequence is not proven:

```text
generic Hub /op
-> mutation_scope provision
-> provider-issued scope
-> scoped script_run
-> terminal readback
```

Classification: `external_blocker` / `HubGenericOpProjectionRequired`.

This finding is not `repair_local`. Editing PR-007 to bypass the Hub, widen an allowlist, mint caller authority, use `operator_unrestricted`, or add a duplicate executor would violate the approved Requirement and security boundary.

## Acceptance Result

```text
Acceptance Approved: false
Completion Verified: false
Result: Rejected
Blocking Finding: HubGenericOpProjectionRequired
Finding Class: external_blocker
```

The Task must not be merged or marked done from this state.

Canonical recovery condition: the Hub generic `/op` catalog/dispatcher must expose and route the Agent-registered `mutation_scope` operation (or an explicitly approved equivalent admission path), after which the full A7 live sequence must be re-run against the same exact repository/lineage authority and Acceptance repeated.

No Completion Claim.
