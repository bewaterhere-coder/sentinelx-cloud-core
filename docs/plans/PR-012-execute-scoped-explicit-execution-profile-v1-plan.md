# PR-012-execute-scoped-explicit-execution-profile-v1 — Plan R3

Requirement revision: 1 (unchanged).
Status: Approved; S01 implementation completed; Acceptance R1 approved; completion finalization in progress.
Supersedes R2. Withdraws the incorrect independent-Codex prerequisite; preserves tests, acceptance and Requirement.

## Corrected execution boundary
An independent Codex execution channel is NOT a prerequisite of this Requirement or Plan. R1/R2 F01 incorrectly elevated one implementation option into a mandatory requirement; that rationale is withdrawn.
Use SentinelX's existing restricted development path where currently admitted. The live devforge_runtime describe readback on 2026-10-05 still lacks execution_profile and rejects additional properties; the existing adapter hardcodes scoped_mutation internally. Scope lifecycle calls exist, but do not by themselves satisfy the explicit profile contract.
Current model-facing script_run also lacks the required profile/scope fields. No compatible current SentinelX process tool was observed for this mutation/test operation.
This is a live execution-interface limitation, not a design defect and not a reason to require Codex. Do not self-approve this Plan or use a missing-field call to bootstrap itself.
Minimal bootstrap, if no compatible restricted tool is available: an operator uses their existing approved local development workflow on exact PR-12 branch in an isolated execution workspace, applies the bounded S01 correction and runs its tests, then activates the exact verified build through their authorized installation workflow. No new agent/tool platform is required. If workspace admission is absent, stop before materialization.
After activation, current local_api.describe and harmless scoped execution/audit/terminal readback must prove the repaired interface.
No generic SentinelX script, source-checkout write, unrestricted execution, provider switch or permission expansion is authorized by this correction.

## Technical approach
Use src/sentinelx_core/handlers/devforge_runtime.py:
- _EXECUTE_SCOPED_ALLOWED and _EXECUTE_SCOPED_REQUIRED admit/require execution_profile.
- _ACTION_SCHEMAS["execute_scoped"] requires the field and allows only scoped_mutation.
- DevForgeRuntimeProvider.describe derives params directly from schema.required; test both projections together.
- make_devforge_execute_scoped_adapter rejects missing or invalid profiles before invoking profiled_script_handler and propagates the validated caller value.
Preserve existing cleanup, scope/repository/lineage, disabled policy and bounded result projection. Keep downstream unexpected-profile rejection.

## Single implementation slice
S01: schema, adapter, relevant tests and compatibility documentation.
Formal Slice Set is compiled only after Plan approval.
Remove former S02: installation/activation and live Acceptance are not implementation Slice completion.

## Concrete test entrypoints and traceability — F03
Existing tests/test_devforge_runtime_local_api.py contains:
- test_eligible_host_lists_bounded_builtin: extend schema/params assertions (B1/AC1).
- _execute_params: supply explicit profile in valid fixtures (B2).
- test_execute_scoped_adapter_injects_fixed_authority_and_projects_result: revise to verify validated caller profile propagation while retaining authority/result bounds (B2/B5, AC2/AC4).
- test_execute_scoped_adapter_rejects_caller_authority_overrides: retain forbidden authority fields, handle unsupported profile through explicit validation (B4/B6).
- test_disabled_script_run_filters_optional_execute_adapter and lifecycle/disabled tests: preserve no-execution policy semantics (B6/AC4).
Add local_api-handler -> builtin provider -> real adapter -> recording profiled handler integration for exact propagation (AC2).
Add missing/null/non-string/read_only/operator_unrestricted/unknown-string cases with zero executor calls (B3/B4/B7, AC3).
Add unexpected downstream profile rejection (B5).
Existing tests/test_local_api.py covers outer routing; run alongside the focused runtime tests (AC4/AC5).
Focused command on admitted test workspace: python -m pytest tests/test_devforge_runtime_local_api.py tests/test_local_api.py.
Inspect repository CI/pyproject before choosing broader checks; record exact candidate, environment and outcomes. Windows containment/live evidence cannot be replaced by portable mocks.

## Verifier-owned live Acceptance — F02
AC6 belongs to Acceptance, separately from code Slice completion:
1. Resolve exact candidate commit and its code-test evidence; do not install moving main.
2. Resolve installation/restart operator and explicit activation authority before changing service installation. Current development/plan command does not grant deployment authority.
3. Read previous running build and retain a reproducible recovery reference; any installation failure stops and follows the approved recovery procedure without deleting user data.
4. Activate through a verified installation interface, restart and read running version/candidate identity.
5. Through current ChatGPT local_api.describe read required execution_profile and exact supported value.
6. Provision/revalidate a provider-owned scope for the exact harmless verification identity; execute a deterministic marker with explicit scoped_mutation.
7. Read output, durable audit identity and terminal scope evidence. Invalid/missing profile must be denied before process spawn.
If activation authority/interface is absent, return Acceptance blocked. If Hub filters parameters, surface scope decision; no unapproved Hub repository modification.
No actual activation path or operator authority is claimed verified by this Plan.

## Write scope / compatibility / risks
Write scope: existing devforge_runtime adapter, tests/test_devforge_runtime_local_api.py, directly justified local_api regression tests, focused README/contract documentation.
Required-field change intentionally rejects old omitted-profile clients; no default or migration of authority.
Revalidate overlap with PR-011 without sharing transport. PR-008/009 remain related, independent work.
UI/visual fidelity: NotApplicable. Requirement unchanged; no permission expansion, firewall change, unrestricted mode, acceptance or merge.
