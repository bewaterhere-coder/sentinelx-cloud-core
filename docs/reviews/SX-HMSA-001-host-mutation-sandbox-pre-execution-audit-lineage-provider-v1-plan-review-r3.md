# SX-HMSA-001 — Plan Review r3

## Review State

```yaml
task_id: SX-HMSA-001
transport: github-pr
pull_request: 3
reviewed_head: e0acae46662ee9792eafd91a30b25db8d7488919
plan_ref: docs/plans/SX-HMSA-001-host-mutation-sandbox-pre-execution-audit-lineage-provider-v1-plan.md
plan_blob: 4445407a46dce415b5b81b39e49202a011879048
plan_revision: 3
decision: Approved
blocking_findings: []
next_stage: implementation
next_expected_actor: implementer
execution_slice_set: docs/execution/SX-HMSA-001-execution-slice-set.yaml
```

## Verdict

**Approved.**

The revised plan is implementation-ready. The two previous rejection rounds are materially closed and no new Plan Review blocker remains.

## Review Basis

The review checked the current plan against the DevForge Plan Review contract: solution direction, scope control, technical feasibility, risk handling, implementation-shaping assumptions, requirement traceability, and whether verification observes the required security behavior rather than a proxy.

### Closed prior P0 findings

1. **Provider-owned placement authority — closed.** The plan now defines Host-owned `mutation_execution.workspace_root` policy, deterministic repository + Run/Attempt[/Slice] placement, placement generation/policy digest, protected inventory and fail-closed drift detection. Caller paths and broad `file_ops` roots are explicitly non-authoritative.
2. **Windows sandbox primitive/bootstrap — closed.** Windows V1 is fixed to AppContainer + exact workspace ACL + Job Object containment, with trusted broker workspace creation only after durable START, suspended process creation, Job assignment before resume, no breakaway and no unrestricted fallback.
3. **Authoritative request identity — closed.** `RequestContext` is derived from `RequestMessage`, keeping transport `request_id` / `opaque_ref` distinct from semantic lineage and preserving the binding across background work and audit events.
4. **Legacy unrestricted migration ambiguity — closed.** Historical unprofiled execution is isolated as `legacy_unrestricted_compat`; explicit `operator_unrestricted` requires policy opt-in and never satisfies the new DevForge capabilities.
5. **Mutation-scope uniqueness/concurrency — closed.** A provider-owned unique lease key, reverse workspace index, atomic/idempotent provisioning, no-reactivation rule, one-SID/one-lease binding and terminal residual-authority checks close the second-round P0.

## Residual Implementation Risks — Non-blocking

- **AppContainer runtime compatibility:** Python/PowerShell and required immutable runtime roots must actually execute under the chosen AppContainer boundary. The plan explicitly requires runtime self-check plus real Windows integration evidence; provider unavailability is an allowed fail-closed outcome.
- **Durability semantics:** START/evidence/scope stores must prove platform-appropriate durable flush behavior under injected failures. The plan requires this before capability advertisement and spawn.
- **OS-bound terminalization:** No competing lease, Job/process or residual ACL write authority may remain. The plan includes authoritative read-back and negative regressions.

These are implementation/verification risks with explicit validation methods; they do not require a new design decision before implementation.

## Requirement / Plan Traceability

The plan directly covers the requirement's material boundaries:

- Host-owned scope authority and lifecycle → placement resolver + unique lease lifecycle;
- durable pre-spawn audit → mutation audit journal + retained forensic script evidence;
- Windows OS confinement → AppContainer + exact ACL + suspended Job containment;
- caller/credential/fallback boundaries → execution profiles + no fallback + separate authenticated Git broker;
- incident regression → disposable `INCIDENT-20260927-D-ROOT-RECURSIVE-DELETE` attack matrix;
- capability truthfulness → runtime prerequisite self-check and conditional advertisement.

## Implementation-Ready Closure

Approval is coupled to the durable Execution Slice Set for exact plan revision 3. Implementation must consume that Slice Set and complete at most one slice per explicit `#开发执行` invocation.

No provider implementation code is part of this review transition.
