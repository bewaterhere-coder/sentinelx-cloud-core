# Provisional Requirement — SentinelX Provider Capability Release & Runtime Activation V1

This provisional artifact exists only to establish the independent GitHub PR transport required before the canonical PR-backed Task ID is allocated.

Intent:

- make SentinelX provider capability changes publishable through a versioned, reproducible release path;
- avoid hard-coded host identity, version number, installation path, or workspace path;
- preserve fail-closed runtime readiness for `host_mutation_sandbox_v1` and `pre_execution_audit_lineage_v1`;
- allow an installed release to activate those capabilities from host-resolved policy/configuration when prerequisites are satisfied;
- keep release completion separate from any one host's upgrade state.

The canonical Task Markdown and Plan will replace this provisional artifact after GitHub allocates the PR number.
