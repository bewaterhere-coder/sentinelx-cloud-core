# SentinelX execute_scoped Explicit Execution Profile Schema & End-to-End Propagation V1

Provisional requirement; canonical Task ID awaits GitHub-assigned PR number.

Expose required execution_profile=scoped_mutation in devforge_runtime.execute_scoped, validate before execution, propagate the caller value to the existing profiled executor, and verify model-facing describe/call behavior. Preserve provider-owned scope, audit, isolation and canonical firewall. No production Hub implementation, permission expansion or unrestricted fallback.
