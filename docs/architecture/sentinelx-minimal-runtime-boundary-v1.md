# SentinelX Minimal Runtime Boundary V1

Status: Architecture Decision — Frozen by PR-021 S02

Task: `PR-021-minimal-runtime-complexity-reduction-boundary-v1`

Requirement: Revision 1

Plan: Revision 1

Evidence baseline:

~~~text
sentinelx-cloud-core main:
1028030b33f0ea792a884491a431fffe566f6aa5

PR-021 S01 evidence:
docs/execution/PR-021-minimal-runtime-complexity-reduction-boundary-v1-s01-attempt-001-receipt.yaml

DevForge runtime at S02 admission:
v2.100.0
3d0880d271bd2e1e3955c81eb09344faf5cd6f69

DevForge slicing contract:
system/incremental-plan-execution-slicing-checkpoint-contract.md
v1.1
~~~

## 1. Context

SentinelX started as a secure local capability bridge but has accumulated responsibilities from several development lineages:

- structured host-local capability projection;
- command/script execution;
- scoped mutation authority;
- AppContainer/ACL/Job containment;
- mutation audit and canonical repository protection;
- verification runtime;
- DevForge runtime projection;
- execution-workspace placement/materialization;
- Direct Codex discovery, ACL handoff, workspace lifecycle, transport bootstrap, persistence, publication and receipt normalization;
- background job execution and completion replay;
- proposed durable long-running operation lifecycle.

The current pressure point is not merely timeout length.

The architectural issue is ownership.

A short Hub/local_api interaction is being asked to own the lifecycle of development work whose duration and internal loop are not naturally bounded by that interaction.

That creates a recurring expansion pattern:

~~~text
long task exceeds interaction window
→ extend timeout or detach work
→ add durable operation identity
→ add lifecycle persistence
→ add restart/reconnect recovery
→ add outcome reconciliation
→ add provider-specific execution bridges
→ add workspace/bootstrap dependencies
→ add more orchestration state
~~~

The resulting SentinelX is no longer a thin secure local bridge.

## 2. Decision

SentinelX V1 is defined as:

> A secure, bounded, short-duration local capability bridge between ChatGPT/DevForge and the Host.

SentinelX owns **security, projection, bounded local execution and verifiable read-back**.

SentinelX does **not** own the lifecycle of long-running development Agents.

Long-running or duration-uncertain development work is executed outside the Hub request lifecycle through a guided / semi-interactive local CLI handoff.

The boundary is:

~~~text
ChatGPT / DevForge
      │
      ├─ read / analyze
      │
      ├─ bounded short local operation
      │       ↓
      │    SentinelX
      │
      │    security + projection
      │    short execution + read-back
      │
      └─ long / uncertain development operation
              ↓
           guided CLI
              ↓
        CodeBuddy / Codex / build / test
              ↓
       commit / receipt / evidence
              ↓
         ChatGPT / DevForge
~~~

This decision intentionally reduces **orchestration complexity** without reducing **security complexity**.

## 3. Minimal Runtime responsibilities

SentinelX remains responsible for the following classes.

### 3.1 Structured local capability projection

SentinelX retains:

- MCP Tool Projection;
- `local_api` list / describe / call;
- closed schemas;
- bounded response projection;
- provider readiness;
- effect classification;
- structured error/read-back results.

Projection is a core bridge responsibility.

### 3.2 Read operations

SentinelX may expose bounded read operations against Host-local capabilities and files when allowed by policy.

Read operations should prefer structured APIs over shell parsing when such APIs exist.

### 3.3 Bounded file mutation

SentinelX may perform small, explicit, bounded file writes when:

- exact mutation scope is known;
- write roots are authorized;
- canonical repository protections remain active;
- the operation has no long-running Agent loop;
- completion can be verified synchronously within the bounded interaction.

### 3.4 Short command execution

SentinelX may run short commands when:

- command authority is explicit;
- scope and output are bounded;
- no large or recursively expanding workload is implied;
- no Agent lifecycle is embedded;
- verification/read-back is available.

### 3.5 Short verification

SentinelX may run narrow verification such as:

- focused unit/static checks;
- deterministic schema/config validation;
- short smoke checks;
- bounded read-back checks.

The verification subsystem remains valid where it supplies bounded, fail-closed verification.

A long test suite does not become a SentinelX responsibility merely because the verification machinery can technically execute it.

### 3.6 Mutation security

SentinelX continues to own the security substrate required for authorized Host mutation:

- Host Mutation Scope;
- durable scope identity and lifecycle;
- fail-closed mutation audit;
- AppContainer / ACL / Job containment;
- exact write-authority confinement;
- canonical repository mutation firewall;
- operation/effect registration;
- caller path/authority restrictions;
- residual authority cleanup/terminalization.

These are not simplification targets.

### 3.7 Receipt and read-back verification

SentinelX continues to provide or participate in verifiable evidence for operations it actually performs.

Core rule remains:

> No Receipt, No Completion Claim.

For work executed outside SentinelX, SentinelX may validate bounded returned evidence, but it does not retroactively become owner of the external process lifecycle.

## 4. Explicit non-responsibilities

The minimal SentinelX runtime does not own:

- CodeBuddy Agent lifecycle;
- Codex Agent lifecycle;
- multi-turn Agent execution loops;
- long build orchestration;
- long test-suite orchestration;
- large refactor execution lifecycle;
- generic development job scheduling;
- durable long-running development-operation state machines;
- reconnect/resume semantics created solely to keep a development Agent alive behind a Hub request;
- DevForge Slice progression;
- Plan/Requirement/Gate semantics;
- development task scheduling;
- automatic timeout extension as a routing strategy.

These responsibilities belong to DevForge, the local guided CLI execution plane, or a separately justified product capability.

## 5. Hub window semantics

The Hub/local_api request window is a **bounded control and interaction window**.

It is not a product promise that every valid development operation must fit inside one request.

The architecture therefore forbids this reasoning:

~~~text
operation takes longer than Hub window
→ Hub window must be increased
~~~

The correct question is:

~~~text
Is this operation a SentinelX-owned bounded local capability?
~~~

If no, the operation leaves the Hub lifecycle.

No precise seconds threshold grants execution authority.

Time estimates are advisory because task duration is often nondeterministic.

The resolver uses **operation class and boundedness**, not a fragile wall-clock prediction.

## 6. Execution Mode Resolution

The execution mode resolver follows this order.

### Mode 0 — Read / analysis path

Use repository/API/read-only access without Host mutation when the requested result can be obtained without local execution.

Examples:

- source inspection;
- GitHub artifact inspection;
- Plan/Requirement review;
- status/read-back;
- architecture analysis.

### Mode 1 — SentinelX direct-short

Use SentinelX direct execution only when all are true:

1. authority and target scope are explicit;
2. the operation is bounded in work scope;
3. output is bounded;
4. no CodeBuddy/Codex/Agent loop is required;
5. no large build, broad test suite or large refactor is required;
6. verification is narrow and bounded;
7. the operation can return a trustworthy result/read-back through the short interaction path;
8. security admission succeeds.

Typical examples:

- bounded file edit;
- small config/schema update;
- short command;
- focused unit/static verification;
- exact file/read-back check.

### Mode 2 — Guided CLI

Use guided CLI when any of the following is true:

- CodeBuddy is required;
- Codex is required;
- an Agent loop is required;
- large build;
- long test suite;
- large refactor;
- broad dependency installation;
- workload size is not predictably bounded;
- the operation can legitimately continue after the Hub request ends;
- the process needs sustained user-local terminal/session ownership.

Guided CLI is the default for development Agents even if a particular invocation might occasionally finish quickly.

A future requirement may prove a specific bounded Agent action belongs in direct-short, but that is an exception requiring explicit evidence.

### Mode 3 — Independent non-development async capability

An existing or future non-development feature may independently justify background execution.

Such a feature is evaluated on its own product requirement.

It must not inherit long-development automation requirements by default.

Existing generic background jobs are therefore not removed by this decision.

## 7. Guided CLI handoff contract

A guided CLI handoff must be complete enough that the local execution does not rely on chat memory.

Minimum semantic shape:

~~~yaml
repository:
task_id:
transport:
  type:
  pr:
  branch:
stage:
requirement:
  ref:
  revision:
  digest_or_blob:
plan:
  ref:
  revision:
  digest_or_blob:
current_slice:
  ref:
  id:
allowed_mutation_scope:
forbidden_actions:
verification:
expected_return_evidence:
  - commit_or_patch_identity
  - changed_file_manifest
  - test_or_verification_result
  - provider_or_cli_receipt_when_available
  - canonical_transport_readback
~~~

The handoff must also carry any applicable:

- canonical branch/PR identity;
- run/attempt/slice identity;
- no-replacement-branch rule;
- no-canonical-main-mutation rule;
- permission/credential expansion prohibition;
- exact verification commands or outcomes required.

The user executes the CLI locally.

After execution, ChatGPT/DevForge consumes returned durable evidence and resumes workflow evaluation.

A guided handoff is not evidence of execution.

Only returned/read-back evidence can support a completion claim.

## 8. Security invariants

The simplification must preserve all of the following.

### S1 — Canonical repository safety

Canonical repositories remain protected from unintended mutation.

A development execution path may not use simplification as justification to mutate canonical `main` or bypass isolated execution requirements.

### S2 — Explicit mutation authority

Host mutation requires explicit scope.

Caller-selected arbitrary write roots remain forbidden where provider-owned placement is required.

### S3 — Fail-closed audit

Security-critical mutation audit remains durable and fail-closed.

No process/materialization side effect may be treated as safely executed when the required audit lineage was not durably recorded.

### S4 — Sandbox confinement

Where an untrusted or development mutation process requires confinement, AppContainer/ACL/Job or the applicable canonical sandbox remains authoritative.

No simplification may silently downgrade to unrestricted subprocess execution.

### S5 — Operation/effect truth

Operation classification must remain authoritative enough for repository firewall/readiness decisions.

Removing orchestration code must not create unclassified mutation paths.

### S6 — Receipt/read-back

Externally meaningful completion remains evidence-driven.

Provider self-report, chat history or “Agent says done” is insufficient.

### S7 — No authority transfer through CLI text

A guided CLI handoff carries instructions and identity, not new authority.

It cannot widen:

- project binding;
- credentials;
- filesystem scope;
- canonical branch authority;
- destructive-operation authority;
- release authority.

## 9. Q1 Decision — Execution workspace materialization

Question:

> Is execution workspace materialization security substrate or orchestration substrate?

Decision:

**Split the concept.**

### Keep the security requirement

Safe bounded mutations may still require provider-owned isolated workspace placement/materialization.

Therefore the architecture keeps the invariant:

> Mutating development execution must not fall back to the canonical source checkout merely because the long-Agent runtime is removed.

The PR-014 S01 evidence is important because its branch implementation explicitly reuses existing `MutationScopeStore` and `WindowsMutationSandbox` and stops before repository materialization.

That indicates a potentially reusable security substrate:

- provider-owned workspace placement;
- protected-root separation;
- mutation scope binding;
- sandbox-root binding;
- no caller path authority.

### Do not keep long-Agent materialization as a goal by itself

PR-014's current S02 lineage is tied to:

- direct CodeBuddy bootstrap;
- execution workspace materialization for development Host execution;
- Direct Development Host invocation projection.

Those requirements are not automatically part of the minimal runtime.

Architecture disposition:

~~~text
workspace isolation / placement needed for short safe mutation
→ retain as minimal security substrate

workspace/bootstrap machinery needed only to run long CodeBuddy/Codex through SentinelX
→ HOLD / later deprecate or reshape
~~~

PR-014 must therefore be reshaped rather than blindly completed unchanged.

S03 owns the final component-level disposition.

## 10. Q2 Decision — PR-020 Durable Async Runtime

Question:

> Does PR-020 have independent non-development product value sufficient to justify a generic durable long-operation runtime now?

Decision:

**No current evidence proves that requirement. PR-020 is HOLD under the minimal-runtime architecture.**

The S01 evidence shows:

- generic background execution already exists;
- `jobs.py` supports detached Agent-side background operations;
- `pending_results.py` preserves completed answers across reconnect;
- `pending_results.py` explicitly does not preserve running-job truth across Agent restart;
- PR-020 was directly motivated by a development operation continuing beyond the synchronous request lifetime.

PR-020 offers real benefits:

- durable operation identity;
- caller handle;
- lifecycle persistence;
- restart reconciliation;
- status/receipt read-back;
- end-to-end automation.

However, adopting it as the response to long development tasks makes SentinelX own additional state machines:

- durable operation admission;
- duplicate identity resolution;
- lifecycle persistence;
- restart recovery;
- outcome-unknown reconciliation;
- retention/tombstones;
- provider adaptation;
- replay prevention;
- security composition with every long provider.

The selected product boundary removes the main development driver by moving long development execution to guided CLI.

Therefore:

1. PR-020 must not continue unchanged as a DevForge/Codex timeout solution.
2. Existing background jobs/pending-result delivery remain intact.
3. If a future non-development product requirement proves that running-job durability across Agent restart is independently necessary, create a separate requirement and evaluate the smallest async runtime for that use case.
4. That future requirement must not automatically re-import development Agent lifecycle ownership.

This is a HOLD decision, not source deletion authority.

## 11. Q3 Decision — Direct Codex after guided CLI

Question:

> What remains of Direct Codex after the Agent lifecycle moves outside SentinelX?

Decision:

**Direct Codex execution is not a core SentinelX responsibility. Freeze new dependency and plan retirement/splitting after guided CLI is established.**

Current main evidence shows a full Codex-specific subsystem:

- `handlers/direct_codex.py`;
- ACL handoff;
- CLI discovery;
- handoff compiler;
- workspace derivation;
- transport bootstrap;
- persistence/publication;
- result/receipt normalization.

The provider includes a real Codex sandbox probe with a 300-second timeout.

That is direct evidence that the subsystem is an Agent execution plane rather than a minimal short local bridge.

Post-boundary ownership is:

~~~text
Codex process lifecycle
→ local CLI / user-owned execution plane

DevForge Task / Plan / Slice semantics
→ DevForge

Host security for short SentinelX mutations
→ SentinelX

returned commit/receipt/read-back validation
→ DevForge + bounded SentinelX/repository verification as applicable
~~~

Not every Direct Codex module must be deleted.

The following semantics may remain useful if decoupled from Codex:

- canonical transport identity validation;
- returned receipt normalization;
- commit/read-back verification;
- deterministic handoff field compilation.

S03 must distinguish reusable generic evidence/security logic from Codex-specific lifecycle code.

No source is removed by PR-021.

## 12. Q4 Decision — Incremental execution slicing

Question:

> How does `incremental_execution.slice_v1` interact with the minimal runtime?

Decision:

**Slicing remains a DevForge workflow/execution concept and Harness consumer contract. It does not grant SentinelX long-running execution ownership.**

Canonical evidence distinguishes:

- DevForge Core slicing: already merged in `bewaterhere-coder/DevForge#3`;
- current Core contract: Incremental Plan Execution Slicing & Checkpoint Contract v1.1;
- Harness consumer work: `bewaterhere-coder/devforge-harness#229`.

The semantic rule is:

~~~text
Slice
!= short operation
!= one Hub request
~~~

A Slice is a durable DevForge decomposition unit.

For each Slice:

~~~text
DevForge selects exact dependency-ready Slice
↓
execution mode resolver evaluates actual operation
├─ bounded short operation
│    → SentinelX direct-short
└─ long / Agent / uncertain operation
     → guided CLI
↓
receipt / checkpoint
↓
DevForge updates Slice state
~~~

SentinelX may carry/echo `slice_id`, `run_id` and `attempt_id` as evidence identity.

SentinelX does not own:

- Slice selection;
- dependency progression;
- automatic next-Slice scheduling;
- long Slice process lifetime;
- Plan drift semantics.

Those remain DevForge/Harness responsibilities.

## 13. PR-019 stabilization relation

PR-019 currently treats Direct Codex behavior as part of stabilization evidence.

The minimal-runtime decision does not automatically invalidate PR-019.

However, a baseline that permanently requires a long-Agent Direct Codex bridge would conflict with this architecture.

Therefore a successor task must reconcile the stabilization baseline so that:

- security-critical short runtime capability remains baseline-critical;
- Direct Codex long-Agent lifecycle is not required merely to declare SentinelX stable;
- any evidence already gathered by PR-019 remains historical evidence rather than being erased.

PR-021 does not modify PR-019.

## 14. Existing background jobs

Generic background jobs are not deprecated by this ADR.

They have an existing product shape independent of Direct Codex.

Architecture rule:

> Background capability is evaluated by its owning product requirement, not by whether it runs longer than the Hub request.

The minimal-runtime boundary only forbids using generic background execution as an automatic escape hatch for DevForge long-Agent execution.

## 15. Verification boundary

Verification routing follows the same mode resolver.

### Direct-short verification

Suitable when:

- exact target is small;
- toolchain is already available;
- test set is narrow;
- expected output is bounded;
- no broad build/dependency resolution is required.

### Guided CLI verification

Required when:

- full project build;
- Unity build/editor verification;
- broad integration suite;
- dependency install/update;
- long platform test;
- unpredictable compilation;
- sustained log/process ownership is expected.

The system should classify by workload shape/capability rather than invent a strict “N seconds” policy.

## 16. Consequences

### Positive

The architecture removes the need for SentinelX to become a universal development job runtime.

Expected reductions include fewer requirements for:

- long-Agent lifecycle ownership;
- provider-specific process orchestration;
- Hub timeout extension;
- durable long-development operation state;
- reconnect/resume semantics around Agent execution;
- CodeBuddy/Codex-specific workspace bootstrapping in the Host bridge;
- development scheduling inside SentinelX.

The security boundary remains strong.

### Trade-off

Some long development actions require explicit local CLI execution by the user.

This is accepted because the local terminal is naturally capable of owning long process lifetime without forcing SentinelX to become a scheduler.

The handoff contract preserves deterministic Task/Plan/Slice identity and required verification.

### Automation impact

This architecture does not maximize zero-touch automation.

It optimizes for:

- lower system complexity;
- deterministic ownership;
- recoverability through durable repository evidence;
- security boundary clarity;
- less circular bootstrap dependency.

Future automation may be added at the CLI/DevForge layer without moving long-process ownership back into SentinelX.

## 17. Strongest counterargument

The strongest alternative is PR-020's Durable Async model:

~~~text
Hub admits long operation
→ durable operation handle returned quickly
→ Agent continues
→ lifecycle persisted
→ reconnect/status/receipt read back later
~~~

This can deliver superior end-to-end automation.

It is technically coherent.

The reason it is not selected for development execution is architectural ownership cost.

For SentinelX to make that model canonical, it must reliably own state and recovery semantics across every long development provider.

That is materially larger than SentinelX's core value as a secure local capability bridge.

Guided CLI reuses a process-lifetime owner that already exists — the user's local terminal/CLI environment — while DevForge continues to own development semantics and SentinelX continues to own bounded security-sensitive Host operations.

If future evidence shows the manual CLI boundary creates larger operational cost than the async state machine, this ADR may be superseded by a new reviewed Requirement.

It must not be silently eroded by incremental timeout/orchestration additions.

## 18. Requirement traceability

| Rule | Architecture resolution |
| --- | --- |
| R1 | Hub is explicitly a bounded control/interaction window; timeout extension is not a routing mode. |
| R2 | Read, bounded write, short command/verification, mutation security, projection and receipt/read-back remain SentinelX responsibilities. |
| R3 | CodeBuddy/Codex/large/uncertain development work routes to guided CLI with a frozen handoff contract. |
| R4 | Direct-short remains available for genuinely bounded work. |
| R5 | Security invariants are preserved; orchestration complexity is the reduction target. |
| R6 | Decision is grounded in S01 current-main/active-task evidence. |
| R7 | Workspace materialization is split into security substrate versus long-Agent orchestration; PR-014 must be reshaped. |
| R8 | PR-020 is HOLD unchanged; future independent non-development async requirement may be evaluated separately. |
| R9 | Slicing stays with DevForge/Harness and does not imply SentinelX lifecycle ownership. |
| R10 | Direct CodeBuddy/Codex Agent lifecycle is outside SentinelX core. |
| R11 | Existing generic background jobs remain and are independently evaluated. |
| R12 | ADR grants no source deletion/provider disablement/Hub/project-binding mutation authority. |
| R13 | This ADR freezes sequencing constraints; S04 owns exactly one final successor implementation order. |

## 19. Successor sequencing constraints

S04 will freeze exactly one primary successor order.

That final order must obey these constraints:

1. stop expanding architecture-conflicting long-Agent orchestration before adding replacement complexity;
2. establish guided CLI routing/handoff before removing working Direct Codex paths;
3. prove the direct-short SentinelX path still supports ordinary bounded operations;
4. reshape or retire long-Agent-specific bridges only after replacement evidence exists;
5. preserve security substrates throughout;
6. perform source deletion only in separate explicit DevForge tasks;
7. reconcile project binding and stabilization baseline through explicit successor tasks, never as an implicit side effect of PR-021.

This section constrains S04 but does not itself execute or finalize the successor plan.

## 20. Non-authority

This ADR does not authorize:

- deleting Direct Codex source;
- disabling Direct Codex provider;
- closing PR-014;
- closing PR-019;
- closing PR-020;
- changing `sentinelx-cloud-core` DevForge project binding;
- implementing guided CLI;
- modifying DevForge Runtime;
- increasing/decreasing production Hub timeout;
- changing production Agent installation;
- modifying Host permissions;
- merging PR-021;
- releasing/deploying SentinelX.

Those actions require explicit successor DevForge tasks.

## 21. Architecture verdict

~~~yaml
sentinelx_role: secure_bounded_short_duration_local_capability_bridge

development_execution_modes:
  direct_short:
    owner: SentinelX
    purpose: bounded authorized local operations
  guided_cli:
    owner: local_cli_execution_plane
    purpose: long_or_uncertain_development_execution

security_complexity:
  disposition: preserve

long_agent_orchestration:
  disposition: remove_from_sentinelx_core_responsibility

pr014:
  architecture_disposition: reshape
  keep_concept: short_mutation_workspace_isolation_security_substrate
  hold_concept: long_agent_workspace_bootstrap_orchestration

pr020:
  architecture_disposition: HOLD
  unchanged_implementation_authorized: false
  future_reentry: separate_independent_non_development_requirement_only

direct_codex:
  architecture_disposition: deprecate_as_core_responsibility_after_guided_cli
  immediate_source_deletion: false

incremental_execution_slice_v1:
  owner: DevForge_and_Harness
  sentinelx_long_lifecycle_ownership: false

generic_background_jobs:
  architecture_disposition: retain_pending_independent_capability_review

source_deletion_authority: false
project_binding_change_authority: false
active_related_pr_mutation_authority: false
~~~
