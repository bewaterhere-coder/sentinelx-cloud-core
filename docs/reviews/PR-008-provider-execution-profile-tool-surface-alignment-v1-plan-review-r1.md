# PR-008 — Plan Review R1

## Review State

```yaml
task_id: PR-008-provider-execution-profile-tool-surface-alignment-v1
transport: github-pr
pull_request: 8
reviewed_head: 30fab805295ebf53111d96d33bb30a3709fdbf3d
plan_ref: docs/plans/PR-008-provider-execution-profile-tool-surface-alignment-v1-plan.md
plan_blob: a97db1e3b7e9b0d5696790babd4790b503e4b20f
plan_revision: 1
decision: Approved
blocking_findings: []
next_stage: implementation
next_expected_actor: implementer
execution_slice_set: docs/execution/PR-008-provider-execution-profile-tool-surface-alignment-v1-slices.yaml
```

## Verdict

**Approved.**

The Plan is implementation-ready for the Agent-owned portion of the task. It correctly treats production Hub/MCP schema projection as an external Acceptance dependency rather than pretending Agent source changes can directly mutate the closed-source Hub.

## Review Basis

The review checked solution direction, scope control, technical feasibility, risk handling, requirement traceability, implementation-shaping assumptions, and whether verification observes the real model-facing behavior rather than an Agent-only proxy.

### Findings

1. **Agent/Hub ownership boundary — correct.** Agent feature advertisement, capability metadata, diagnostics and scoped-input contract evidence are owned by this repository; production `sentinel_script_run` JSON Schema projection is not.
2. **Wire protocol reuse — correct.** `RequestMessage.payload` already carries arbitrary operation mappings, so `execution_profile`, `mutation`, `lineage` and `repository` do not require a new top-level protocol field merely for transport.
3. **Complete scoped input surface — correct.** The Plan does not stop at `execution_profile`; it requires all authority-bearing inputs consumed by the existing scoped handler and rejects partial Hub projection at Acceptance.
4. **Authority and sandbox reuse — correct.** Existing profiled script execution remains canonical; the Plan does not introduce a second scope store, workspace authority, audit path or sandbox.
5. **No-fallback boundary — correct.** Python allowlist expansion, shell/PowerShell wrappers, `operator_unrestricted` fallback and caller-selected workspace mutation remain forbidden.
6. **Mixed-fleet strategy — acceptable.** A versioned hello feature token is additive compatibility evidence. It does not by itself grant readiness or mutation authority.
7. **Dependency separation — correct.** PR-007 owns provider scope admission; PR-005 owns release/runtime activation; PR-008 does not duplicate either.
8. **Behavioral verification — sufficient.** Source/unit PASS is explicitly insufficient for end-to-end completion. Acceptance requires the actual ChatGPT/MCP schema, provider-issued scope, harmless scoped Python execution, terminal scope read-back, and continued denial of direct `exec python`.

## Requirement / Plan Traceability

- R1/R13 → D1 versioned feature token and mixed-fleet tests.
- R2/R3 → D2 bounded machine-readable tool contract with readiness separated from field support.
- R4 → D4 plus reuse of the existing profiled handler.
- R5 → D3 stable fail-closed diagnostic metadata.
- R6/R12 → D6/D8 no-fallback tests and direct-Python denial proof.
- R7/R8 → D7 live production Hub/MCP schema Gate.
- R9 → D8 dependency on provider-issued scope from PR-007 or equivalent verified path.
- R10 → D7/D8 dependency on known-build runtime activation through PR-005 or equivalent.
- R11 → D8 harmless model-facing scoped execution and terminal closure proof.
- R14 → Planning Decision and D1/D2 reuse the existing payload envelope.

## Residual Risks — Non-blocking for Implementation

- The closed-source Hub may ignore the new feature advertisement and continue exposing the old static tool schema. If so, Acceptance must stop with `HubToolProjectionRequired`; Agent implementation is not end-to-end completion.
- PR-007 is currently not a verified scope-admission dependency. Its final accepted payload shape must be re-read before freezing PR-008's advertised scoped field contract.
- PR-005 or an equivalent verified activation path is required before production evidence can be trusted.

These risks have explicit validation/stop conditions and do not require a new Agent-side design decision before implementation.

## Implementation-Ready Closure

Approval is coupled to the durable Execution Slice Set for Plan revision 1. Manual `#开发执行` remains one-slice-per-invocation. D7/D8 production proof belongs to Acceptance and must not be claimed by implementation-only evidence.
