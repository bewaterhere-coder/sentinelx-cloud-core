# `devforge_runtime.execute_scoped` execution-profile contract

`devforge_runtime.execute_scoped` requires callers to select the bounded execution profile explicitly:

```json
{"execution_profile":"scoped_mutation"}
```

The field is required. `local_api.describe` advertises it in both the required parameter projection and the action schema, and `scoped_mutation` is the only supported value.

Requests that omit the field, send `null`, a non-string value, `read_only`, `operator_unrestricted`, or any unknown profile are rejected before the existing profiled script executor is invoked. The Agent does not synthesize a compatibility default for older callers.

The validated caller value is propagated to the existing `profiled_script_handler`; this interface does not create a second executor or grant caller authority over cleanup, workspace identity, mutation scope ownership, repository lineage, audit lineage, firewall behavior, or unrestricted execution.

A successful downstream result must report the same `scoped_mutation` profile. A different or missing downstream profile is treated as a scoped-execution failure.

This is an intentional breaking interface change for callers that previously omitted `execution_profile`. Live installation/restart and end-to-end deployed-Agent verification are separate activation/acceptance concerns, not part of this schema contract.
