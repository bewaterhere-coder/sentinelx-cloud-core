# PR-012-execute-scoped-explicit-execution-profile-v1 — Plan R1

Requirement: docs/requirements/PR-012-execute-scoped-explicit-execution-profile-v1.md, revision 1.
Status: Pending Plan Review. No implementation authorization.

## Approach
Extend the existing execute_scoped schema and adapter; preserve the single profiled executor. No Hub-side change is assumed: local_api already returns the Agent-owned schema, but integration evidence must confirm it.

## Steps
1. Add execution_profile to allowed/required fields, action schema properties and required list; verify describe parameter generation uses the same contract.
2. Validate the value is the exact supported string before scope/executor dispatch. Use stable existing validation error conventions, with clear missing/unsupported diagnostics.
3. Pass params["execution_profile"] into the existing payload after validation; preserve cleanup, bindings, disabled policy, downstream profile verification and bounded result projection.
4. Update affected tests to supply explicit profile. Add missing/null/non-string/unsupported rejection cases with zero executor invocations, describe consistency and full local_api-to-adapter propagation coverage.
5. Document the required-field compatibility change and live activation acceptance procedure. Run focused devforge_runtime/local_api/profile tests followed by applicable repository CI.
6. At acceptance, use an approved deployment/activation path to install the exact accepted candidate; read describe, execute a harmless provider-scoped marker and read audit/terminal scope evidence. If the path is unavailable, report live acceptance blocked rather than completion.

## Proposed slices
S01: schema, adapter, integration tests and documentation (one tightly coupled change).
S02: live activation verification and evidence, after code verification and authorized activation.
The formal execution Slice Set is compiled after Plan approval.

## Write scope
src/sentinelx_core/handlers/devforge_runtime.py; directly relevant existing tests; README or focused execute_scoped contract documentation. Expand only for proven existing routing defects preserving Requirement.

## Risks
- Required field intentionally breaks old omitted-profile calls; update fixtures/docs, never default silently.
- PR-011 may touch shared runtime files; revalidate task HEAD and assess overlap before execution, preserve independent transport.
- Production Hub changes are out of scope. If evidence shows Hub filters params, return a scope decision rather than modify another repository.
- Current Host tool projection lacks the field needed to bootstrap mutation through itself. Planning artifacts use repository API; implementation must separately resolve an admitted execution path, without wrappers or canonical checkout mutation.

## Verification
Meaningful behavioral checks: zero downstream calls for invalid profiles; exact profile reaches existing executor; describe and actual validation agree; disabled operations and foreign/stale scope remain denied; unexpected downstream profile is rejected. Record exact commit/test results. Live marker/audit evidence remains distinct from mocks.

## Foundation and applicability
UI/visual fidelity: NotApplicable.
No unrelated foundation document required. Live profile-compatible execution is an operational admission dependency, not a reason to rewrite this Plan.
No implementation, acceptance, deployment or merge is claimed.
