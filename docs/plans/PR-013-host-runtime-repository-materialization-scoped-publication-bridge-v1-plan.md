# PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1 — Plan R2

Requirement: `docs/requirements/PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1.md`, revision 1 (unchanged).

Status: **Pending Plan Review**. No implementation authorization.

Supersedes Plan R1 and remediates Plan Review R1 findings F1–F4 without changing Requirement semantics.

## 0. Repository reality and remediation baseline

Planning/reconciliation baseline:

```yaml
sentinelx_main: e7064c9bf4fcd15bdb6f5a2678414210c01d1c00
pr013_task_branch_reconciled_with_main: true
pr013_reconciliation_commit: 855543abbaab79c1c2cef6c2a56642595f148b91
pr010_firewall: merged_canonical_baseline
pr011_verification_capsule: open_implementation_s03_pending
pr012_explicit_execution_profile: done_merged_canonical
pr012_merge_commit: 29c724fdc6faed28018d60e61250d3f21b02c1b3
devforge_runtime_baseline:
  execute_scoped_execution_profile_required: true
  execution_profile: scoped_mutation
```

The task branch was reconciled with current canonical `main` on the same PR/branch before R2 was written. The reconciliation retained only PR-013 Task artifacts on top of current product code; it did not add PR-013 product implementation.

PR-012 is now canonical baseline, not an external/unmerged dependency. R2 therefore builds on the merged explicit `execution_profile=scoped_mutation` contract.

PR-011 remains unmerged and complementary. PR-013 may reuse canonical concepts only after they reach `main`; it MUST NOT copy PR-011 unmerged code or redefine its verification-profile/toolchain semantics.

## 1. Planning objective

Implement one bounded provider-owned repository transaction path that composes the existing mutation scope, Windows AppContainer sandbox, canonical-repository firewall, audit lineage, explicit scoped execution profile, and user-scoped Git transport.

Target lifecycle:

```text
exact repository + Task/Run/Attempt[/Slice]
+ exact source ref/SHA
+ exact publication ref/expected remote SHA
        ↓
provision_scope(purpose=repository_transaction_v1)
        ↓
provider mints fixed operation classes
        ↓
provider-owned exact source snapshot
        ↓
scoped materializer under AppContainer/Job
        ↓
materialized
        ↓
execute_scoped(execution_profile=scoped_mutation)
        ↓
process authority fully quiesced
        ↓
immutable publication capsule/tree frozen by provider
        ↓
publication_pending
        ↓
fixed-plumbing user-scoped Git broker
        ↓
expected-remote-SHA CAS / non-force push
        ↓
remote readback
        ↓
published → terminal
```

The caller never supplies Host workspace/cache/mirror/staging paths, operation classes, Git argv, credential controls, or sandbox identity.

## 2. Plan Review R1 remediation summary

| Finding | R2 disposition |
| --- | --- |
| F1 repository transaction scope admission | Closed in plan: `purpose=repository_transaction_v1` is added to existing `provision_scope` and maps provider-side to a fixed operation-class set. |
| F2 materializer execution identity | Closed in plan: repository bytes are written only by a provider-generated materializer process running under the scope-derived Windows AppContainer/Job with a temporary read-only snapshot grant. |
| F3 publication content handoff | Closed in plan: after process quiescence, provider freezes the workspace source tree into an immutable publication capsule; credential-bearing Git consumes only provider-owned staging derived from that capsule, never the scoped workspace. |
| F4 implementation/Acceptance authority mixing | Closed in plan: live Agent activation, service restart, physical accepted-candidate proof and downstream ChatGPTControlShell resume are removed from implementation slices and placed in Acceptance; downstream resume still requires its own canonical command. |

## 3. Architecture decisions

### D1 — Concrete repository-transaction scope admission

R2 freezes the admission shape by extending the existing `devforge_runtime.provision_scope` action rather than adding a second scope minting primitive.

`local_api.describe` schema becomes purpose-discriminated:

```yaml
provision_scope:
  required: [purpose, repository, lineage]
  purpose:
    enum:
      - scoped_script
      - repository_transaction_v1
```

For `purpose=scoped_script`, current behavior remains unchanged and the provider mints exactly:

```text
scoped_script
```

For `purpose=repository_transaction_v1`, the request additionally requires a closed `repository_transaction` object:

```yaml
repository_transaction:
  source_ref: string
  expected_source_sha: full_commit_sha
  publication_ref: refs/heads/<task-branch>
  expected_remote_sha: full_commit_sha
```

No Host path, remote URL, Git argv, sandbox identity, cache identifier, staging path, operation class or credential field is accepted.

The provider independently validates repository identity and resolves the source/publication refs. The source ref MUST resolve to `expected_source_sha` before transaction creation. The publication ref MUST resolve to `expected_remote_sha` at admission. A branch-name-only match is insufficient.

The provider maps `repository_transaction_v1` to this fixed immutable operation-class set:

```text
repository_materialize
repository_execute
repository_publish
```

Callers cannot submit, remove, reorder or enlarge these classes.

The repository transaction record is durable provider state bound one-to-one to the minted scope and records:

```yaml
transaction_id
repository_identity_digest
project_id
task_id
run_id
attempt_id
slice_id
scope_id
scope_generation
workspace_id
source_ref
expected_source_sha
publication_ref
expected_remote_sha
state
materialization_evidence
execution_evidence
publication_evidence
```

Mutable transaction progress stays in the repository-transaction store; the existing immutable mutation-scope digest is not repurposed as a mutable transaction journal.

Same-Attempt retry behavior:

- the existing scope Attempt index remains authoritative;
- retrying `repository_transaction_v1` with exactly the same sealed transaction inputs returns/reconciles the existing current transaction;
- changing purpose, repository, lineage, ref/SHA, target ref, expected remote SHA or fixed authority on the same Attempt is a conflict;
- a terminal/revoked/expired scope cannot be reactivated;
- a previously provisioned `scoped_script` Attempt can never be upgraded into a repository transaction.

This closes F1 and preserves AC10 legacy one-shot semantics.

### D2 — Repository actions and operation gates

The existing `devforge_runtime` endpoint gains bounded actions:

```text
materialize_repository
inspect_repository_transaction
publish_checkpoint
```

`execute_scoped` remains the only model-facing process execution action.

Operation gates are provider-selected from transaction identity, never caller-selected:

```text
materialize_repository              → repository_materialize
execute_scoped on repository tx     → repository_execute
publish_checkpoint                  → repository_publish
legacy execute_scoped               → scoped_script
```

`execute_scoped` keeps the merged PR-012 schema requirement:

```json
{"execution_profile":"scoped_mutation"}
```

For a scope bound to a repository transaction, the provider resolves the transaction first, requires state `materialized`, then the same canonical scoped executor validates `repository_execute`. For a non-transaction legacy scope it continues to validate `scoped_script`.

No second generic executor is introduced.

### D3 — Broker-owned exact source acquisition

Source network/credential work occurs outside caller script semantics through a focused provider repository-source broker.

The broker:

1. resolves repository identity to provider-owned transport configuration/inventory; caller does not supply a URL;
2. independently probes `source_ref` and requires the exact `expected_source_sha`;
3. obtains exactly that Git object/tree using existing user-scoped Git credential context under fixed broker verbs/configuration;
4. exports an immutable source snapshot/capsule to a provider-owned store;
5. validates and persists a manifest containing relative path, type/mode, size and content digest plus the exact source commit;
6. marks the snapshot immutable for this transaction before any scoped workspace write begins.

The snapshot path is never returned as authority and is never caller-selectable.

Provider acquisition MUST NOT fetch, checkout, reset, commit or otherwise mutate the canonical checkout.

V1 supports regular files, directories and explicitly validated Git symlink entries. Unsupported special-file/device, submodule/gitlink or unsafe path semantics fail closed unless implementation demonstrates an equally bounded representation and adds focused tests without widening Requirement scope.

### D4 — Materialization runs as an OS-enforced scoped operation

This decision closes F2.

Repository source bytes MUST NOT be copied into the workspace by an unrestricted LocalSystem/service-side filesystem loop.

`materialize_repository` sequence is frozen as follows:

```text
revalidate scope + transaction + repository + lineage
→ require repository_materialize
→ persist materialization START
→ build existing Windows mutation sandbox for exact scope
→ derive/reserve the same scope-owned AppContainer identity
→ activate exact workspace authority
→ install temporary READ-ONLY grant for that AppContainer SID to exactly one immutable source snapshot
→ materialize provider-generated trusted materializer bootstrap into provider-reserved control area
→ spawn trusted materializer under the AppContainer + Job
→ materializer reads snapshot manifest/content and writes repository bytes only into exact workspace source tree
→ wait/terminate through bounded Job semantics
→ verify no surviving child/process
→ remove temporary snapshot read grant
→ clear sandbox write authority for this operation
→ read back grant removal + process quiescence + exact source tree digest
→ transaction state = materialized
```

The service may create only provider-generated control/bootstrap bytes required to start the sandbox after durable START. It MUST NOT write repository source bytes on behalf of the materializer.

The materializer is SentinelX provider code, not repository code and not caller-supplied code. Its executable/module identity is sealed in START/SPAWN evidence before process resume.

#### Exact filesystem authority

The materializer identity receives:

```text
READ   immutable transaction source snapshot only
WRITE  exact scope-owned workspace only
DENY/NO GRANT canonical checkout
DENY/NO GRANT mutation authority store
DENY/NO GRANT user profile / Git credential material
```

Before each entry write it validates:

- relative non-empty path;
- no `..`, absolute, drive-relative or UNC target;
- no ADS target syntax;
- no traversal through symlink/junction/reparse points;
- supported regular-file/directory/symlink semantics only;
- resource/file-count/size ceilings;
- target remains under the sealed source tree.

Partial materialization failure terminalizes/revokes the transaction and cannot become `materialized`.

A Windows physical regression test MUST prove successful materialization carries AppContainer SID + Job + START/SPAWN/FINISH evidence and MUST fail if a test implementation substitutes a direct unrestricted service copy without that evidence.

### D5 — Exact workspace layout and provider control namespace

Repository transactions reserve a provider-owned internal control namespace under the sealed exact workspace. The exact name is implementation-defined but fixed by provider policy and MUST be rejected if the admitted repository source already contains that reserved path.

Conceptually:

```text
<exact_workspace>/
  <repository_source_tree...>
  <provider_control_namespace>/   # provider-only runtime scripts/output, never publishable
```

`execute_scoped` defaults its repository-transaction `cwd` to the repository source tree. Caller `cwd` remains relative and cannot target/escape into the provider control namespace.

Runner scripts, stdout/stderr, return-code evidence and sandbox profile files are placed in the provider control namespace so publication never mistakes runtime artifacts for source changes.

### D6 — Multi-operation scope lifecycle without weakening legacy one-shot execution

Repository transaction state is:

```text
provisioned
→ materializing
→ materialized
→ executing
→ executed
→ publication_freezing
→ publication_pending
→ publishing
→ published
→ terminal
```

Failure substates may be persisted, but no failed/terminal state can be reactivated by caller input.

The mutation scope remains the unique Host authority envelope. To support multiple bounded operations, add an operation-closure primitive to the existing Windows sandbox composition that:

1. terminates/waits the operation Job/process tree;
2. releases durable Job/PID bindings;
3. removes operation-specific AppContainer ACL grants;
4. readbacks zero live process authority and zero sandbox write authority;
5. leaves the current repository-transaction scope nonterminal only when the transaction state machine explicitly requires a successor operation.

This operation closure is NOT a generic “keep sandbox open” switch and is not caller-selectable.

Materialization success closes all materializer process/ACL authority before `materialized`.

Repository execution success closes all execution process/ACL authority before publication freezing. Non-zero execution, timeout, containment failure, audit failure or cleanup failure forbids publication and terminalizes/revokes fail closed.

Legacy `scoped_script` does not use this multi-operation retention path and retains its current automatic terminalization exactly as on canonical `main`.

TTL/revocation/placement-generation drift remain authoritative at every operation boundary.

### D7 — Repository-scoped execution reuses the canonical executor

`execute_scoped` retains merged PR-012 explicit-profile semantics and routes through the existing profiled scoped execution implementation.

Repository-transaction differences are internal authority/lifecycle composition only:

- transaction must be `materialized`;
- required operation class is `repository_execute`;
- provider runtime artifacts live in the reserved control namespace;
- successful return code 0 performs operation closure instead of final scope terminalization;
- transaction advances to `executed`;
- any failure terminalizes/revokes and cannot publish.

No Git credential, canonical checkout ACL or source snapshot credential authority is inherited by the execution child.

### D8 — Freeze publication content before entering credential context

This closes F3.

After successful repository execution, publication content is frozen before any credential-bearing Git process is launched:

```text
execution process/job closes
→ readback zero process authority and zero sandbox write authority
→ revalidate scope + transaction + exact workspace
→ persist publication-freeze START
→ provider reads exact repository source tree under sealed transaction authority
→ validate paths/reparse/ADS/special-file policy again
→ construct immutable publication manifest/capsule/tree bytes
→ compute publication_content_digest
→ persist source SHA + publication tree intent + digest
→ transaction state = publication_pending
```

The provider service may READ the transaction workspace after process quiescence to freeze content; it does not give the interactive user or Git broker direct reusable workspace access and does not mutate the canonical checkout.

Once `publication_pending` is persisted, publication content for that transaction is immutable. Later workspace drift causes failure rather than silently changing the intended commit.

The publication capsule/staging location is provider-owned and not caller-visible as authority.

### D9 — Fixed-plumbing publication broker

The credential-bearing user-scoped Git broker consumes only the immutable publication capsule and a provider-owned ephemeral staging/object store. It never receives access to the scoped workspace.

The broker resolves remote transport from repository identity/provider inventory; caller cannot supply a remote URL.

V1 publication uses a fixed plumbing-oriented sequence equivalent to:

```text
probe publication_ref
require exact expected_remote_sha
obtain expected parent commit/object into provider staging
hash-object raw publication bytes without clean/smudge filters
construct tree with fixed validated modes
commit-tree with parent = expected_remote_sha
persist produced_commit_sha BEFORE push
re-probe publication_ref == expected_remote_sha
push non-force produced_commit_sha:publication_ref
read back publication_ref
require readback == produced_commit_sha
```

Hardening:

- no shell;
- no arbitrary Git argv;
- no checkout/add/porcelain commit path that would invoke repository filters;
- raw blob hashing does not use repository attributes/clean filters;
- `core.hooksPath` is forced to a provider-owned empty hooks directory for network push;
- no `-S`, signing helper, editor or interactive prompt;
- aliases cannot replace the fixed built-in verbs;
- repository-local config in the publication capsule is not execution authority;
- credential helper/SSH authority exists only in the user-scoped broker process and is never persisted into transaction state/output;
- author/committer identity is provider policy, not arbitrary repository config;
- commit message is bounded/sanitized Task checkpoint metadata;
- no force push in V1.

Because the produced commit has `expected_remote_sha` as its parent, a normal non-force push can only fast-forward from that parent. If the remote advances after the final probe, the push fails instead of overwriting the new head.

Temporary broker ACL/staging authority is removed after publication attempt and verified by readback.

### D10 — Publication CAS, persistence and retry semantics

Before remote write:

1. transaction must be `publication_pending`;
2. repository, lineage, scope generation and publication ref are revalidated;
3. remote ref must equal sealed `expected_remote_sha`;
4. immutable publication content digest must match persisted intent;
5. exact produced commit is created once;
6. `produced_commit_sha` is durably persisted before push.

Outcome rules:

```text
verified remote readback == produced commit
  → published; duplicate request returns existing evidence; no second push

push response lost / timeout
  → publication_uncertain; next invocation reads remote first

remote == produced commit
  → reconcile published without replay

remote == expected old SHA
  → bounded retry of the SAME produced commit may occur if current transaction authority remains valid

remote == any third SHA
  → conflict/drift; fail closed; no force, no regenerated commit
```

Never regenerate a different commit merely because push response/readback was lost.

### D11 — Audit and durable receipts

Materialization, execution, publication freeze and publication are correlated to one repository transaction and the same repository + Task/Run/Attempt/slice + scope generation.

Evidence records at minimum:

```yaml
repository_identity_digest
transaction_id
source_ref
verified_source_sha
scope_id
scope_generation
workspace_id
materialization_audit_operation_id
materializer_sandbox_identity
materializer_job_closure
materialized_tree_digest
execution_audit_operation_id
execution_closure
publication_content_digest
publication_ref
expected_remote_sha
produced_commit_sha
push_outcome
remote_readback_sha
canonical_checkout_mutated: false
generic_bypass_used: false
operator_unrestricted_used: false
terminal_scope_state
```

Receipts MUST omit source snapshot/staging Host paths, credential identifiers, raw credential-helper output and raw interactive-user environment data.

No verified receipt/readback means no completion claim.

### D12 — Related-task composition

#### PR-012

PR-012 is now `done` and merged. Its explicit `execution_profile=scoped_mutation` requirement is canonical baseline. PR-013 directly extends current `main` and MUST preserve PR-012 regressions.

#### PR-011

PR-011 remains open at implementation S03. Its verification toolchain/dependency capsule is complementary but unmerged. PR-013 does not import PR-011 task-branch code. At each implementation-slice admission, re-read current `main` and PR-011 status; if PR-011 later merges, perform a same-task overlap impact check before modifying overlapping sandbox/materialization surfaces.

#### PR-010

Canonical repository firewall remains mandatory baseline and all affected firewall readiness/effect-class regressions remain required.

## 4. Implementation slices

Formal Execution Slice Set is compiled only after this R2 passes Plan Review.

### S01 — Repository Transaction Admission + Durable State

Objective: implement concrete `repository_transaction_v1` admission and durable transaction identity/state without source hydration or publication side effects.

Expected surfaces:

- `src/sentinelx_core/handlers/devforge_runtime.py`;
- new focused `repository_transaction.py` store/model;
- `mutation_scope.py` only for fixed operation-class composition where necessary;
- Agent provider wiring/capability projection;
- focused tests/docs.

Required verification:

- `describe` shows purpose-discriminated path-free schema;
- provider maps repository purpose to exact fixed classes `repository_materialize`, `repository_execute`, `repository_publish`;
- caller operation-class/path/credential fields rejected;
- exact source/publication ref/SHA admission independently checked;
- same-Attempt exact retry idempotent;
- changed authority inputs conflict;
- stale/foreign/terminal scope rejected;
- legacy `scoped_script` provisioning unchanged;
- current merged PR-012 explicit execution-profile tests remain passing.

### S02 — Exact Source Snapshot + AppContainer Materializer

Objective: acquire exact source into immutable provider storage and hydrate repository bytes only through the scope-owned Windows AppContainer materializer.

Expected surfaces:

- provider source acquisition/snapshot module;
- repository materializer module;
- Windows sandbox/ACL operation-closure support;
- audit evidence;
- security/integration tests.

Required verification:

- remote ref resolves exact admitted SHA;
- canonical checkout unchanged;
- source snapshot location not caller-controlled;
- materializer START precedes workspace source write;
- repository bytes are written by AppContainer/Job materializer, not direct service copy;
- snapshot read grant is exact/read-only/transient and removed/read back;
- AppContainer has no canonical checkout, authority-store or credential access;
- traversal/reparse/ADS/special-file/resource-limit negatives fail closed;
- exact source tree digest/readback proves materialization;
- failed materialization terminalizes/revokes and cannot publish.

### S03 — Repository-Scoped Execution Lifecycle + Publication Freeze

Objective: reuse `execute_scoped` with `repository_execute`, safely quiesce process authority without prematurely terminalizing the transaction, and freeze exact post-execution publication content.

Expected surfaces:

- scoped execution lifecycle composition;
- Windows operation closure/quiescence;
- repository transaction state transitions;
- provider control namespace;
- immutable publication capsule/tree freezer;
- audit/receipt tests.

Required verification:

- `execute_scoped` still requires explicit `execution_profile=scoped_mutation`;
- transaction must be materialized;
- repository execution requires `repository_execute` internally;
- provider runtime artifacts cannot enter publication tree;
- success closes Job/PID/AppContainer write authority before freeze;
- nonzero/timeout/containment failure forbids publication and terminalizes/revokes;
- immutable publication digest persisted;
- content changes after freeze are detected/fail closed;
- legacy scoped-script successful/failed executions still auto-terminalize exactly as current main.

### S04 — Fixed Git Publication Broker + Candidate Verification Harness

Objective: publish one frozen checkpoint with fixed Git plumbing under user-scoped credentials and prove CAS/idempotency/security behavior in isolated fixture/CI environments.

Expected surfaces:

- focused publication broker module;
- narrow reusable primitives in `user_git.py` only where Git-specific;
- transaction publication state/evidence;
- fixture repository harness and Windows/CI tests;
- activation/operator documentation.

Required verification:

- credential-bearing Git never accesses scoped workspace;
- publication staging path provider-owned and transient;
- hooks/filters/aliases/signing/editor/shell execution prevented;
- produced commit persists before push;
- commit parent exactly expected remote SHA;
- non-force CAS/fast-forward push only;
- remote drift creates no overwrite;
- verified retry is no-op;
- uncertain push resumes readback-first and reuses same produced commit;
- credential material absent from state/log/receipt;
- full affected regression suite + isolated Windows fixture passes on exact candidate.

S04 does **not** install/restart the live SentinelX service and does **not** execute any downstream ChatGPTControlShell Task.

## 5. Acceptance boundary — not an implementation Slice

This section closes F4.

`#开发验收 PR-013-host-runtime-repository-materialization-scoped-publication-bridge-v1` owns the live proof after all implementation slices are complete.

Acceptance sequence:

1. verify exact implementation candidate and candidate-local/CI receipts;
2. activate/install that exact accepted candidate through the approved SentinelX operator/update path;
3. restart the live Agent only under Acceptance/operator authority;
4. read back running candidate identity;
5. verify capability readiness and `local_api.describe devforge_runtime` repository transaction schemas;
6. execute a dedicated benign physical fixture transaction on Windows: provision → exact materialize → scoped mutation → freeze → checkpoint → non-force CAS push → remote readback → terminalize;
7. run physical negative cases for wrong SHA, stale scope, remote drift, no-hook behavior and credential isolation;
8. verify canonical checkout remains unchanged/protected and terminal scope has no residual authority.

### AC13 downstream proof boundary

Acceptance cannot synthesize or inherit ChatGPTControlShell Task authority.

To satisfy AC13, SentinelX Acceptance may reach a waiting state that explicitly requires the operator/user to issue the downstream Task's own canonical command:

```text
#开发执行 PR-013-manual-command-adoption-workflow-lineage-attachment-v1
```

That command belongs to the ChatGPTControlShell Task and creates/resumes its own Attempt under its own DevForge authorization.

After that separately authorized execution produces durable evidence, SentinelX Acceptance may read the downstream receipt/readback as cross-repository proof that materialization reached the implementation/verification boundary without generic fallback. SentinelX Acceptance MUST NOT send the command itself as a side effect of this Task, mutate downstream Task artifacts, or claim AC13 without the downstream receipt.

## 6. Write scope

Expected product write scope after approval:

- `src/sentinelx_core/handlers/devforge_runtime.py`;
- new focused repository transaction/source snapshot/materializer/publication modules;
- `src/sentinelx_core/mutation_scope.py` only for explicit fixed operation-class/lifecycle support;
- `src/sentinelx_core/handlers/scoped_script.py` only to compose repository-transaction execution with the existing executor without duplicating it;
- `src/sentinelx_core/mutation_audit.py` only for bounded new evidence;
- `src/sentinelx_core/windows_mutation_sandbox.py` / sandbox composition for operation closure and narrow snapshot grant;
- `src/sentinelx_core/user_git.py` only for fixed Git-specific broker primitives;
- Agent capability/composition wiring;
- focused unit/integration/Windows/CI fixture tests;
- config example/operator documentation.

Forbidden:

- production `mcp.sentinelx.app` Hub changes;
- canonical checkout implementation writes;
- downstream ChatGPTControlShell source/Task mutation;
- generic shell/Git/copy wrapper;
- caller-selected Host paths;
- caller-selected operation classes;
- `operator_unrestricted`;
- allowlist widening as a workaround;
- broad AppContainer canonical/user-profile credential access;
- force push;
- importing unmerged PR-011 task code.

## 7. Security/correctness risk controls

1. **Authority inflation** — fixed purpose→operation-class mapping; same-Attempt mutation conflicts.
2. **Direct service materialization bypass** — source bytes require AppContainer materializer START/SPAWN evidence.
3. **Snapshot escape** — strict manifest/path/reparse/ADS/resource validation + exact read-only ACL.
4. **Long-lived process authority** — every materialize/execute operation closes Job/PID/ACL authority before next state.
5. **Legacy regression** — multi-operation retention applies only to repository transactions; ordinary scoped scripts still terminalize.
6. **Publication workspace ACL widening** — user-scoped Git consumes frozen provider capsule/staging only, never scoped workspace.
7. **Repository code execution during Git** — fixed plumbing/raw blob hashing + empty hooks path + no signing/shell/editor.
8. **TOCTOU publication content** — immutable frozen publication digest before credential process.
9. **Remote race** — produced commit parent=expected SHA + immediate re-probe + non-force push + readback.
10. **Duplicate external side effect** — persist produced SHA before push; uncertain result reconciles by readback first.
11. **Credential leakage** — credentials remain user-scoped broker-only; state/output redaction required.
12. **Parallel task drift** — re-read canonical main/PR-011 at every slice admission; PR-012 is already canonical baseline.

## 8. Requirement / Acceptance traceability

| Requirement / AC | Planned proof |
| --- | --- |
| R1/R2, AC1–AC3 | S01 closed admission schema, exact ref/SHA binding, lineage/scope conflict tests |
| R3/R6, AC2–AC5 | S02 AppContainer materializer + physical OS identity/ACL/Job evidence |
| R4/R13, AC4/AC11 | canonical firewall regressions + zero canonical mutation + no fallback tests |
| R5 | S02 broker-owned source acquisition + credential/snapshot path non-projection |
| R7/R10, AC5/AC10 | S03 single executor + repository operation closure + legacy auto-terminal regression |
| R8/R9, AC6–AC8 | S04 fixed-plumbing broker + no-hook/filter/signing + non-force CAS tests |
| R10/R11, AC9 | durable transaction/push evidence + readback-first retry/idempotency tests |
| R12 | S01/S04 dynamic `local_api.describe` and capability projection |
| AC12 | S04 isolated Windows fixture plus Acceptance live physical fixture |
| AC13 | Acceptance reads receipt from separately authorized downstream ChatGPTControlShell `#开发执行` |

## 9. Verification strategy

### Unit/contract

- purpose-discriminated provisioning schema;
- fixed operation-class mapping and same-Attempt conflict behavior;
- transaction state persistence/transition table;
- exact ref/SHA/transport binding;
- caller path/operation/credential field rejection;
- snapshot manifest/integrity/path validation;
- publication tree construction and content digest;
- fixed Git command construction;
- CAS/idempotency/uncertain-outcome reconciliation;
- output/credential redaction.

### Existing regressions

At minimum rerun affected suites covering:

- `test_devforge_runtime_local_api.py`;
- mutation scope admission/handler/store/registry;
- mutation audit;
- scoped script execution including merged PR-012 profile semantics;
- canonical repository firewall + structured firewall;
- Windows mutation sandbox;
- user-scoped Git + Git network failure classification;
- PR-011-compatible verification/runtime suites when/if their code is canonical at slice admission.

Run the applicable full repository test suite on the exact Task candidate before implementation completion.

### Isolated Windows implementation verification

Implementation may run physical Windows fixture tests in an isolated test environment/workspace to prove materializer identity, operation closure and publication broker feasibility. This is candidate verification only: it MUST NOT replace live Agent activation Acceptance, mutate production canonical checkouts, or invoke downstream Task commands.

### Live Acceptance

Live Agent installation/restart and accepted-candidate physical proof are Acceptance-owned as defined in section 5.

## 10. Completion boundary

Plan R2 does not authorize:

- product implementation;
- Execution Slice creation before review approval;
- live Agent installation/restart;
- service mutation;
- Hub mutation;
- downstream ChatGPTControlShell execution;
- merge/release/completion claims.

If Plan Review approves R2, DevForge may compile the formal Execution Slice Set from S01–S04 and transition to implementation. One `#开发执行` still completes at most one admitted slice according to the current DevForge runtime.
