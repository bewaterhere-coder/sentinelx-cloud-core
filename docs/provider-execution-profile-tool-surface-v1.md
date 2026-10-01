# Provider Execution Profile Tool Surface V1

## Status and ownership

This document freezes the Agent-owned contract introduced by
`PR-008-provider-execution-profile-tool-surface-alignment-v1`.

Ownership is intentionally split:

- `sentinelx-cloud-core` owns Agent payload semantics, capability advertisement,
  Host policy/readiness, scoped execution, and fail-closed diagnostics.
- `mcp.sentinelx.app` owns the closed-source Hub/MCP model-facing tool projection.
- Agent advertisement is therefore necessary but is not evidence that a ChatGPT
  or other MCP client can already send the fields described here.

The stable Agent feature token is:

```text
script_run_execution_profile_v1
```

Full capabilities expose the corresponding feature under:

```text
host_runtime.script_run_execution_profile_v1
```

The token means that the Agent understands the profiled `script_run` payload
contract. It does not grant mutation authority and does not prove that the
required sandbox is ready on the current Host.

## Model-facing input contract

A compatible model-facing `sentinel_script_run` projection must be able to
carry the following top-level semantics for `scoped_mutation`:

```text
execution_profile
mutation
lineage
repository
```

The existing Agent handler requires these concrete authority/binding fields:

```text
execution_profile = scoped_mutation
mutation.scope_ref.scope_id
mutation.scope_ref.generation
lineage.project_id
lineage.task_id
lineage.run_id
lineage.attempt_id
lineage.slice_id?          # optional
repository.vcs
repository.authority
repository.path
```

Equivalent serialized shapes are allowed only when they preserve the same
semantics. A Hub must not synthesize, guess, or caller-mint mutation scope,
repository identity, or lineage.

Conceptual request shape:

```yaml
execution_profile: scoped_mutation
interpreter: python3
content: "print('SENTINELX_PROFILED_SCRIPT_OK')"
mutation:
  scope_ref:
    scope_id: <provider-issued opaque id>
    generation: <positive integer>
lineage:
  project_id: <project>
  task_id: <task>
  run_id: <run>
  attempt_id: <attempt>
  slice_id: <optional slice>
repository:
  vcs: git
  authority: github.com
  path: owner/repository
```

This example is a shape contract only. It does not authorize a caller to invent
`scope_id`, `generation`, workspace placement, protected roots, operation
classes, sandbox identity, or any other provider-owned authority.

## Field support is not readiness

The Agent reports profile field support separately from current Host readiness.
For `scoped_mutation`, execution remains admitted only when all existing Host
mutation readiness and scope-validation checks pass.

In particular:

```text
feature advertised
!= profile admitted now
!= model-facing schema projected
!= provider scope issued
!= successful end-to-end execution
```

`operator_unrestricted` is not a safe fallback. It is reported only when the
existing Host policy explicitly opts in, and profile mismatch never authorizes
switching to it.

Likewise, this contract does not add Python to `allowed_commands` and does not
authorize `sentinel_exec` to run Python. Direct command execution remains under
the existing command allowlist.

## Mixed-fleet behavior

Older Agents that do not advertise `script_run_execution_profile_v1` remain
valid fleet members. A Hub must bind projected profiled fields to the selected
Agent's capabilities, not infer fleet-wide support from another connected Host.

A Hub that ignores the feature token may continue to operate older surfaces,
but such a Hub has not satisfied the profiled tool-surface acceptance gate.

No wire-protocol version change is required merely to transport these fields:
the existing request payload envelope already carries operation payload
mappings.

## Scope-admission dependency

As of 2026-10-01, PR #7,
`PR-007-host-mutation-scope-control-surface-mcp-admission-bridge-v1`, remains at
`plan_review_rejected`; it does not provide an approved or implemented external
scope lifecycle contract for PR-008 to freeze.

Therefore PR-008 freezes only the authority shape already consumed by the
existing canonical scoped handler. It does not freeze PR #7's rejected draft
API names, actions, or response projection.

End-to-end Acceptance must obtain scope authority from a verified provider-owned
admission path. Until PR #7, or an equivalent bounded provider-owned control
surface, is approved, implemented, and verified, the live scoped execution
proof remains blocked at scope acquisition.

## Runtime-activation dependency

PR #5, `PR-005-provider-capability-release-runtime-activation-v1`, owns generic
provider release/install/runtime activation. Source changes in PR-008 do not
prove that a connected production Agent is running a build containing this
contract.

Acceptance must identify a known deployed Agent build before interpreting live
Hub/MCP behavior as evidence for or against PR-008.

## Production Acceptance probe

Acceptance is deliberately fail-closed and proceeds in this order:

1. **Known build** — identify a connected Agent build that contains PR-008 via
   PR #5 or equivalent verified runtime-activation evidence.
2. **Agent advertisement** — verify the selected Agent advertises
   `script_run_execution_profile_v1` and full capabilities expose
   `host_runtime.script_run_execution_profile_v1` with the required-input
   contract.
3. **Model-facing schema inspection** — inspect the actual client-visible
   `sentinel_script_run` schema. It must expose semantically sufficient forms of
   `execution_profile`, `mutation`, `lineage`, and `repository`.
4. **Projection gate** — if any required field is absent or cannot carry the
   existing handler contract, stop with:

   ```text
   HubToolProjectionRequired
   ```

   Do not use a wrapper, direct `exec`, allowlist expansion, or unrestricted
   profile as a workaround.
5. **Provider-issued scope** — obtain a scope from an approved provider-owned
   admission path. Caller-minted IDs or workspaces are invalid evidence.
6. **Harmless scoped call** — invoke the model-facing profiled script path with
   the exact provider scope, repository identity, and semantic lineage. The
   script should emit a deterministic marker only, for example:

   ```python
   print("SENTINELX_PROFILED_SCRIPT_OK")
   ```

7. **Execution and closure evidence** — verify success output, scoped execution
   evidence, and terminal/non-active scope closure. Do not infer closure merely
   from a returned process code.
8. **No-escalation proof** — separately verify direct `sentinel_exec` of Python
   remains `command_not_allowed` when Python is not allowlisted.

Only completion of all applicable steps may support an end-to-end alignment
claim.

## Failure classification

The following boundaries are intentionally distinct:

- `execution_profile_required` — configured Host mutation execution received an
  unprofiled script request; Agent diagnostics name the required argument and
  supported profiles.
- `HubToolProjectionRequired` — Agent supports the profile contract but the live
  model-facing schema cannot express it.
- provider-scope dependency blocked — the model-facing schema can express the
  fields, but no verified provider-owned scope admission path is available.
- runtime-activation dependency blocked — source contains the contract but the
  live Agent build is not proven to contain it.
- Host mutation readiness/sandbox failures — the payload is expressible, but the
  current Host cannot lawfully admit or execute the requested profile.

None of these classifications authorizes fallback to unrestricted execution.

## S02 regression evidence

PR-008 focused contract verification completed on 2026-10-01 with:

```text
18 passed in 0.31s
```

The focused set covered:

- handshake/feature advertisement without misclassifying the token as a
  top-level wire-protocol field;
- machine-readable full-capabilities contract;
- Host-policy-gated `operator_unrestricted` advertisement;
- bounded `execution_profile_required` diagnostics;
- rejection of unknown profiles.

A broader Windows scoped-script run in the same development window reached:

```text
21 passed, 1 skipped, 3 failed
```

The three failures were all environmental ACL failures while the test fixture
attempted `icacls /grant` against `C:\Python314` from a non-elevated interactive
user. They were not failures in PR-008's capability or profile-diagnostic code.
PR-008 therefore isolated its contract tests from the pre-existing Windows
AppContainer integration suite rather than weakening ACL policy or requesting
administrator authority merely to satisfy this Slice.

These repository-level results do not replace the production Acceptance probe
above.
