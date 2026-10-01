# PR-008 — SentinelX Provider Execution Profile Tool Surface Alignment V1 — Plan

## State

```yaml
task_id: PR-008-provider-execution-profile-tool-surface-alignment-v1
stage: implementation
requirement: docs/requirements/PR-008-provider-execution-profile-tool-surface-alignment-v1.md
transport: github-pr
pr_number: 8
task_branch: task/provider-execution-profile-tool-surface-alignment-v1
plan_status: approved
plan_revision: 1
plan_review: docs/reviews/PR-008-provider-execution-profile-tool-surface-alignment-v1-plan-review-r1.md
execution_slice_set: docs/execution/PR-008-provider-execution-profile-tool-surface-alignment-v1-slices.yaml
implementation_authorized: true
acceptance_approved: false
completion_verified: false
```

## Planning Decision

The defect is split into two boundaries:

```text
A. Agent contract advertisement / diagnostics       ← owned here
B. Production Hub/MCP model-facing schema projection ← external closed-source dependency
```

V1 implements A completely and makes B an explicit live Acceptance Gate. It must not hide B by weakening Host policy or by using an alternate shell path.

The Host handler already consumes profiled payloads, and the wire protocol already carries arbitrary operation payload mappings. Therefore this plan does not redesign the scoped executor and does not propose a wire-protocol breaking change.

## Design

### D1 — Stable handshake feature token

Add a protocol feature token to the Agent hello capability list:

```text
script_run_execution_profile_v1
```

Implementation seam:

```text
src/sentinelx_core/executor.py
  Executor.PROTOCOL_FEATURES
```

Semantics:

- the Agent understands profiled `script_run` payload fields;
- the token is compatibility evidence only;
- it does not mean `scoped_mutation` is currently ready/admitted;
- older Agents omit it and remain valid.

The token must be covered by unit tests that assert it is present in `capability_names()` without altering unrelated operation names.

### D2 — Machine-readable execution-profile tool contract

Extend full `capabilities` output with a provider-neutral-ish Agent feature block under `execution_features`, using a stable key equivalent to:

```text
host_runtime.script_run_execution_profile_v1
```

The block must describe:

```text
operation = script_run
profile_argument = execution_profile
profile requirement semantics
supported profile values
scoped_mutation required payload fields
current Host policy/readiness status separately from field support
```

For `operator_unrestricted`, advertise support only when existing Host policy explicitly enables it. Never advertise it as a DevForge-safe profile.

The metadata must remain bounded and static enough for a Hub/adapter to consume. It must not include live mutation scope IDs, exact workspace paths, protected-root inventories, credentials, or secrets.

Primary seam:

```text
src/sentinelx_core/handlers/basic.py
```

Tests:

```text
tests/test_*capabilities*.py or a focused new test module
```

### D3 — Diagnostic contract for missing profile

When `mutation_execution` is configured and no profile is supplied, keep the existing stable error code:

```text
execution_profile_required
```

Add bounded details equivalent to:

```yaml
required_argument: execution_profile
feature: script_run_execution_profile_v1
supported_profiles:
  - scoped_mutation
```

If `operator_unrestricted` is policy-enabled it may appear as supported by the Host, but the error must not recommend it as a fallback.

Primary seam:

```text
src/sentinelx_core/handlers/scoped_script.py
```

Tests must prove the error remains fail-closed and carries no live scope/workspace authority.

### D4 — Explicit scoped input contract coverage

Add tests/documentation freezing the existing required scoped payload structure:

```text
execution_profile
mutation.scope_ref.scope_id
mutation.scope_ref.generation
lineage.project_id
task_id
run_id
attempt_id
slice_id?
repository.vcs
authority
path
```

This plan does not redesign `_authority()`; it freezes the model-facing contract needed to call it lawfully.

A future Hub schema that exposes `execution_profile` but omits `mutation`, `lineage`, or `repository` must still fail Acceptance.

### D5 — Public contract documentation

Update `README.md` and/or a focused provider contract document to explain:

- `script_run_execution_profile_v1` advertisement;
- profile field vs Host readiness distinction;
- required scoped payload shape;
- Hub/MCP projection boundary;
- mixed-fleet behavior;
- no unrestricted fallback;
- direct `exec` allowlist remains independent.

Do not claim production Hub support merely because Agent code is ready.

### D6 — Regression suite

Add focused tests covering at least:

1. `capability_names()` advertises `script_run_execution_profile_v1`.
2. full capabilities includes the machine-readable tool contract.
3. `scoped_mutation` appears only as a contractually understood profile and current usability remains readiness/policy-gated.
4. `operator_unrestricted` is not advertised as enabled unless Host policy opts in.
5. configured `mutation_execution` + missing profile returns `execution_profile_required` with bounded diagnostic details.
6. unknown profile remains rejected.
7. existing legacy unprofiled behavior remains unchanged when `mutation_execution` is absent.
8. scoped profile still requires `mutation`, `lineage`, and `repository` authority inputs.
9. no test or implementation adds Python to `allowed_commands`.
10. unrelated `exec`, Git, file, service, upload, help and capability operation registration remains unchanged.

Prefer extending existing scoped-script/capability test modules where that keeps the contract localized.

### D7 — External Hub/MCP Acceptance probe

After Agent implementation is released/activated on a known Host, inspect the actual model-facing tool schema from ChatGPT/MCP.

PASS requires `sentinel_script_run` to expose a semantically sufficient surface for:

```text
execution_profile
mutation
lineage
repository
```

If any required field is absent:

```text
status = Blocked
reason = HubToolProjectionRequired
```

This is not repaired inside the Agent by wrapper execution, allowlist expansion, or unrestricted fallback.

Because the Hub is closed-source, external evidence may be a live tool-schema readback / tool invocation result rather than a repository diff.

### D8 — End-to-end harmless scoped execution

Full Acceptance after D7 additionally requires an admitted provider-issued mutation scope. Use `PR-007` or an equivalent verified scope-control path; do not manually fabricate scope/workspace authority.

Sequence:

```text
obtain provider-issued scope
→ invoke model-facing sentinel_script_run
   execution_profile=scoped_mutation
   harmless Python marker
   exact scope + lineage + repository
→ verify returncode=0 / deterministic marker
→ verify audit evidence and terminal scope closure
```

Then separately call direct `sentinel_exec` with Python while Python remains absent from `allowed_commands` and verify:

```text
command_not_allowed
```

This is the decisive proof that the safe script path was restored without weakening the direct command boundary.

## Files Expected to Change

Primary implementation scope:

```text
src/sentinelx_core/executor.py
src/sentinelx_core/handlers/basic.py
src/sentinelx_core/handlers/scoped_script.py
README.md and/or focused contract documentation
tests/test_scoped_script_execution.py
focused capability/handshake test file(s) if needed
```

Possible only if evidence requires it:

```text
CHANGELOG.md
pyproject.toml version metadata under release-owned work only
```

Explicitly out of scope:

```text
closed-source Hub code
mutation scope storage redesign
AppContainer sandbox redesign
Python allowlist mutation
operator_unrestricted default enablement
new generic shell execution path
```

## Dependency Handling

### PR-007

`PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1` currently owns provider scope lifecycle admission. PR-008 must not duplicate it.

PR-008 implementation can complete its Agent contract advertisement/tests independently, but D8 live scoped execution is blocked until a verified provider-owned scope admission path exists.

Before implementation, re-read PR-007 current state. If PR-007 changes the scope payload shape, PR-008 must reconcile its advertised contract with the accepted PR-007 shape rather than freezing stale fields.

### PR-005

`PR-005-provider-capability-release-runtime-activation-v1` owns generic release/install/runtime activation semantics. PR-008 does not duplicate deployment machinery.

Live D7/D8 evidence requires a known deployed build containing PR-008 through PR-005 or an equivalent verified activation path.

### Closed-source Hub

The Hub owns MCP schema projection. No source mutation is possible in this repository.

If the Agent advertises the feature correctly but production Hub still projects the old schema, PR-008 remains externally blocked at Acceptance. That state is preferable to a false completion claim.

## Verification Strategy

### Local/unit verification

Run the repository's focused Python tests for:

```text
handshake/capability advertisement
capabilities execution feature projection
profile parsing and missing-profile diagnostics
scoped script authority validation
legacy script compatibility
```

Then run the broad test suite available on the implementation host. Any platform-specific pre-existing collection limitation must be recorded exactly and cannot be silently treated as PASS.

### Contract verification

Check that:

```text
Host understands execution_profile
Hub-facing feature is advertised
capabilities expose the exact input contract
readiness remains independent
no fallback path was added
```

### Live verification

Required before Acceptance Approved:

```text
known Agent build active
actual ChatGPT/MCP tool schema read back
required profiled fields visible
provider-issued scope available
harmless scoped Python invocation succeeds
scope terminalization proven
direct exec Python remains denied
```

## Risks and Controls

### Risk A — Feature advertisement is mistaken for runtime readiness

Control: expose field support and current mutation readiness as distinct evidence.

### Risk B — Hub exposes only `execution_profile` but not authority fields

Control: D7 requires the complete semantically sufficient profiled surface, not one field.

### Risk C — Mixed-fleet Hub sends new fields to old Agents

Control: versioned hello feature token; Hub must gate new projection/routing on capable targets.

### Risk D — Team bypasses the external blocker using wrappers

Control: requirement and tests explicitly prohibit exec/shell/PowerShell wrappers, allowlist expansion and unrestricted fallback.

### Risk E — PR-007 changes authority shape

Control: implementation starts with dependency readback and reconciles advertised field contract to the accepted provider scope seam.

### Risk F — Source PASS is confused with production repair

Control: end-to-end Acceptance is impossible without live model-facing schema evidence and known runtime activation.

## Plan Review Checklist

Reviewer must answer:

1. Is the Agent/Hub ownership boundary correct?
2. Is a new wire-protocol field unnecessary because operation payload is already open?
3. Does the feature token safely support mixed fleet?
4. Does capabilities metadata describe field support without granting authority?
5. Does the plan include all fields needed by existing `_authority()` rather than only `execution_profile`?
6. Are PR-007 and PR-005 dependencies non-duplicative?
7. Is the no-fallback boundary preserved?
8. Is live Hub/MCP schema evidence mandatory before end-to-end completion?
9. Is direct `exec python` explicitly kept denied?

Approval authorizes implementation only after all blocking findings are resolved.
