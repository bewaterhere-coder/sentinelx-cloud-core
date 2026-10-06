# PR-016 Scoped Verification Node/npm TypeScript AppContainer Drive-Root Compatibility V1 — Plan

## Status

```yaml
task_id: PR-016-scoped-verification-node-npm-typescript-appcontainer-drive-root-compatibility-v1
plan_revision: 1
plan_status: ready_for_review
implementation_authority: false
requirement_ref: docs/requirements/PR-016-scoped-verification-node-npm-typescript-appcontainer-drive-root-compatibility-v1.md
transport:
  type: github-pr
  pr_number: 16
  branch: task/scoped-verification-node-npm-typescript-appcontainer-drive-root-compatibility-v1
  base: main
```

## Plan Objective

Repair the Windows AppContainer path-resolution boundary exposed by real TypeScript execution without broadening SentinelX's security model.

The implementation should make the smallest provider-owned ACL/runtime change that allows Node/npm to resolve the exact verification workspace lineage, including the drive anchor only when required, while preserving denial of unrelated volume content.

## Technical Decision

Treat this as an **ancestor path-resolution authority** problem inside the existing Windows mutation sandbox, not as a workspace-placement problem.

Do not move the execution workspace into `D:\coco`. Do not add a new executor or generic read root.

The preferred design is to evolve the existing transient workspace-ancestor authorization so it can represent and track the exact minimal access mask required for Windows path canonicalization:

```text
exact workspace: existing exact scoped authority
        ↑
provider-derived ancestor chain
        ↑
drive anchor: minimum non-inheriting metadata/traverse authority only
```

The exact mask is not considered frozen until focused real-Windows probes prove it. Start from the current `FILE_TRAVERSE` model and test whether drive-root `FILE_READ_ATTRIBUTES` is additionally required for Node `fs.realpathSync/lstat`.

## Planned Changes

### 1. Focused reproduction and mask proof

Add a real-Windows regression fixture that reproduces the current failure with an exact scoped workspace on a non-system drive when available, or an equivalent isolated drive-root fixture.

The probe must distinguish:

- traversal to the exact workspace;
- metadata/lstat on the drive root;
- directory enumeration;
- arbitrary sibling file read;
- write authority.

Use this to freeze the minimum ACL mask rather than granting broader `RX` as a shortcut.

### 2. Ancestor authorization primitive

Refactor the current workspace ancestor helper in `src/sentinelx_core/windows_mutation_sandbox.py` so the provider can include the filesystem anchor when required.

Requirements:

- paths are derived only from the canonical exact workspace;
- no caller path input;
- non-inheriting ACEs only;
- minimum mask only;
- exact AppContainer SID only;
- final-path/reparse checks retained;
- every granted ancestor is tracked for cleanup.

If different masks are needed for intermediate ancestors versus drive anchor, represent that explicitly instead of flattening to a broad shared permission.

### 3. Cleanup/read-back closure

Extend activation failure and terminalization cleanup so the exact drive-root/ancestor grants are revoked in reverse order.

Add explicit residual-authority assertions/read-back sufficient to fail closed if the AppContainer SID remains on an ancestor that this scope modified.

Do not remove unrelated pre-existing ACL entries.

### 4. Verification readiness strengthening

Extend `verification_readiness.py` and its real Windows self-check to exercise the actual path-resolution prerequisite needed by Node/npm package-local execution.

The readiness probe should be smaller than a full project build but stronger than `node --version` / `npm --version`; it must catch the class of failure that produced `EPERM lstat D:\\`.

### 5. Real TypeScript fixture

Add a bounded provider-owned fixture with:

- lockfile-bound offline dependency capsule;
- TypeScript dependency;
- `typecheck: tsc --noEmit`;
- a minimal TypeScript source and tsconfig.

Run through the existing profiled scoped execution path. Prove:

```text
npm ci --offline → pass
npm run typecheck → pass
```

No Internet access may be enabled.

### 6. Negative security regressions

Extend Windows sandbox tests to prove that drive-root compatibility does not permit:

- volume-root directory listing beyond what the minimum metadata operation inherently exposes;
- reading an unrelated sibling sentinel file;
- reading a protected/canonical repository sentinel;
- writing outside the exact workspace.

Also preserve existing Job/no-breakaway and exact workspace ACL tests.

### 7. Downstream integration replay

After the SentinelX candidate passes its own acceptance suite and is activated on the current Host, re-run ChatGPTControlShell PR-015 S01's exact profiled verification.

Expected downstream result:

```text
npm ci --offline → pass
npm run typecheck → pass
npm run check → pass
```

This is integration evidence, not a replacement for SentinelX's own reproducible acceptance fixture.

## Expected Files

Primary candidate files:

```text
src/sentinelx_core/windows_mutation_sandbox.py
src/sentinelx_core/verification_readiness.py
tests/test_windows_mutation_sandbox.py
tests/test_verification_readiness.py
tests/test_verification_scoped_execution.py
```

A small dedicated regression test file may be added if it keeps the drive-root compatibility proof isolated and readable.

## Verification Strategy

Run focused checks first:

```text
python -m pytest -q tests/test_windows_mutation_sandbox.py
python -m pytest -q tests/test_verification_readiness.py
python -m pytest -q tests/test_verification_scoped_execution.py
```

Then run the repository's affected scoped-verification regression set and real Windows physical proof.

Required evidence must include:

- the frozen minimal ACL mask;
- successful real `tsc --noEmit`;
- negative sibling/protected-root access;
- terminal cleanup read-back;
- no-network proof;
- readiness projection before/after semantics.

## Slice Proposal

Plan Review may compile the canonical Slice Set. Recommended decomposition:

```text
S01 — reproduce + minimal drive-root path-resolution primitive + security tests
S02 — readiness self-check + real TypeScript offline verification fixture
S03 — regression closure + current-Host activation/downstream PR-015 replay evidence
```

No Slice is authorized until Plan Review approves the Plan and the canonical Execution Slice Set is persisted.

## Risks

### RSK-1 — accidental volume-read widening

Mitigation: non-inheriting ACE, minimum mask proof, explicit root enumeration/sibling-read negatives, exact SID cleanup.

### RSK-2 — ACL cleanup damages unrelated entries

Mitigation: merge/revoke only the exact AppContainer SID ACE created for the scope; read back surrounding DACL state in tests.

### RSK-3 — readiness remains weaker than production behavior

Mitigation: readiness must execute the same path-resolution class used by package-local Node children rather than version-only probes.

### RSK-4 — overfitting to ChatGPTControlShell

Mitigation: independent minimal TypeScript fixture is mandatory; downstream PR-015 is secondary integration proof.

## Plan Review Questions

1. Is drive-root/ancestor ACL evolution the smallest correct boundary, or can Node path resolution be satisfied without any root ACE while still preserving normal `npm run typecheck` semantics?
2. Is the proposed mask proven minimal and non-inheriting?
3. Do negative tests prove `D:\coco` and unrelated sibling content remain inaccessible?
4. Does terminalization prove exact SID authority removal from every modified ancestor?
5. Is readiness strengthened enough that the current false-positive `verified=true` state cannot recur?
6. Does the plan remain within the existing PR-011 executor/scope/audit architecture?
