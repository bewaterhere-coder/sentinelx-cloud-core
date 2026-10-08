# PR-015 — Acceptance R1 Invalidation after Requirement Revision 2

## Disposition

```yaml
task_id: PR-015-direct-codex-development-host-invocation-bridge-v1
acceptance_revision: 1
prior_result: DecisionRequired
prior_finding_classification: upstream_material_decision
requirement_revision_before: 1
requirement_revision_after: 2
current_acceptance_authority: invalidated
historical_evidence_retained: true
reacceptance_required: true
```

Acceptance R1 remains authoritative historical evidence that the real installed Codex Development Host performs bounded workspace edits but does not create a Git commit, leaving the bridge unable to produce a persisted successful receipt under Requirement Revision 1 / Plan R2.

The current explicit `#开发` command resolves the material decision by selecting provider-owned deterministic commit-on-publish. That decision changes the Requirement and implementation scope, so Acceptance R1 MUST NOT be reused as the current Acceptance disposition.

## Retained evidence

The following observations remain valid inputs to Plan R3 and future Acceptance:

- real `@openai/codex` bounded execution works inside the isolated checkout;
- the real host leaves eligible implementation changes uncommitted;
- the bridge correctly reports `implementation_not_persisted` rather than fabricating success;
- exact identity/transport receipt validation and drift negatives are valid;
- Windows MIC containment and active-user execution evidence remain relevant.

## Invalidated acceptance claims

The following must be re-evaluated after Plan R3 implementation:

- AC8 persisted real-host direct/Codex success receipt;
- AC12 end-to-end recovery of the direct/Codex provider path for PR-013;
- deployed live-Agent provider availability/readiness;
- exact product-candidate activation and live transport readback.

No prior Acceptance result may approve, reject, or complete Requirement Revision 2 without a fresh `#开发验收`.

No completion claim.
