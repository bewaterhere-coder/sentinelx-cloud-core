# PR-015 — Direct Codex Development Host Invocation Bridge V1 — Plan Review R4

## Review State

```yaml
task_id: PR-015-direct-codex-development-host-invocation-bridge-v1
review_target: plan
requirement_revision: 2
requirement_blob_sha: 195e0099bb6ea0d69133fffc2558248aceaa193e
plan_revision: 4
plan_blob_sha: cc351da6bd5746a171bdd14bdb34fa07e41c6336
reviewed_task_head: 681f786eab240f1fea352ecb895fedca09c2ebbf
result: Rejected
finding_classification: plan_local
runtime:
  devforge_version: 2.81.0
  devforge_revision: fb05202b03fb5e3d0147b9b30f43b49c2404b072
  review_contract: "1.3"
repository_reality:
  canonical_main: 018b78ca20984176d53fbe90039dc795a7f2742f
  canonical_pr: 15
  canonical_branch: task/direct-codex-development-host-invocation-bridge-v1
  project_provider: direct
  project_adapter: codex
next_gate: plan_review_rejected
next_expected_actor: planner
```

## Decision

**Rejected.**

Plan R4 successfully closes the two R3 findings:

- the Codex-owned checkout index is no longer candidate authority;
- deterministic candidate/recovery identity is now sufficiently frozen.

One remaining P0 implementation-shaping gap exists in the blob canonicalization boundary. No Requirement Revision 3 is needed.

## F1 — Raw no-filter worktree bytes can corrupt canonical Git content on Windows

Plan R4 intentionally uses:

```text
git hash-object -w --no-filters --stdin
```

to prevent repository-controlled clean/process filters from executing.

That closes an execution-authority risk, but it also bypasses Git's canonical clean conversion. On the real Windows PR-015 execution workspaces, checkout text files are physically CRLF while canonical Git blobs are LF.

Fresh review evidence:

```yaml
physical_windows_file:
  path: D:\coco\workspaces\bewaterhere-coder\sentinelx-cloud-core\pr015-s03-a1\src\sentinelx_core\policy.py
  sampled_bytes: 20000
  crlf_count: 497
  lf_count: 497
canonical_blob:
  repository: bewaterhere-coder/sentinelx-cloud-core
  ref: 018b78ca20984176d53fbe90039dc795a7f2742f
  path: src/sentinelx_core/policy.py
  blob_sha: 8ae469d1b8a72a2224e1cc6efdea63ba024bf4d7
  crlf_count: 0
  lf_count: 1277
repository_gitattributes: absent
```

Therefore raw no-filter hashing of a modified Windows worktree file can create a candidate blob whose line endings differ across the whole file even when Codex changed only a small semantic region.

That would violate the intended bounded eligible-delta semantics and can produce a large accidental implementation payload.

### Required Plan R5 correction

Plan R5 must preserve the provider-owned temporary index and external-execution firewall while separating:

```text
external filter/process authority
!=
safe canonical clean normalization
```

R5 must freeze a canonical blob-materialization policy with all of the following:

1. **Do not hash raw Windows worktree bytes directly as the canonical blob for ordinary tracked files merely because external filters are forbidden.**
2. Resolve the exact eligible path's Git attributes/config needed for clean conversion through fixed provider-owned Git operations.
3. Fail closed when a path requires an external/custom `filter` or other repository/user configured process driver that cannot be proven non-executing.
4. Permit only explicitly supported in-process/builtin canonical transforms such as Git text/eol normalization and supported `working-tree-encoding` conversion.
5. Candidate blob construction must run under provider-clamped configuration with no shell, external filter command, hook, signing, fsmonitor, editor, pager or terminal prompt execution.
6. The provider-owned temporary index remains seeded from `expected_remote_sha`; the Codex-owned index remains untrusted.
7. The provider must prove that an **unchanged canonical file whose Windows worktree copy contains only checkout-induced CRLF expansion re-materializes to the exact parent blob SHA**, not a new CRLF blob.
8. A file with a real Codex edit must produce canonicalized content preserving only the semantic edit rather than whole-file line-ending churn.
9. Binary files must not undergo text normalization.
10. Unsupported/custom attribute semantics fail closed rather than falling back to raw bytes silently.

The implementation may use a fixed Git builtin clean-conversion path (for example a provider-owned temporary index with controlled path-aware hashing/staging) only after custom external filter/process attributes are rejected and all execution-producing config surfaces are clamped. The exact command sequence is implementation-owned, but the Plan must make the canonicalization/security split explicit.

## Accepted Plan R4 direction

The following are approved direction and should remain unchanged in R5:

- provider-owned deterministic commit-on-publish;
- Codex remains Development Host; SentinelX remains bounded persistence/transport broker;
- S01-S03 remain retained verified prerequisites;
- one new S04 implementation delta only;
- Codex-owned checkout index is untrusted;
- provider-owned temporary index seeded from the exact admitted parent;
- candidate tree contains only provider-validated eligible delta;
- durable recovery journal outside the candidate set;
- all commit-SHA metadata frozen before candidate creation;
- bit-identical same-attempt candidate reconstruction;
- `publish_intent` before the first push;
- uncertain publish => readback only, no automatic second push;
- ordinary fast-forward publication;
- no force/force-with-lease;
- no replacement branch/PR;
- no canonical checkout mutation;
- no generic Git/shell surface;
- no permission/credential expansion;
- previous CodeBuddy override remains expired.

## Gate Result

```text
Plan Review R4: Rejected
Requirement Revision: 2 / Ready
Plan Revision: 4 / Rejected
Plan Approved: false
Implementation Authorized: false
Formal Plan R4 Slice Set: not compiled
Current Gate: plan_review_rejected
Next Actor: planner
```

No product implementation, bootstrap override, live Agent mutation or transport mutation is authorized by this review.

## Required Plan R5 delta

Add one explicit **canonical blob materialization boundary** that preserves Git's safe canonical text/encoding semantics while continuing to prohibit repository/user-controlled external process filters.

No other architecture change is requested.
