# AI Agents — Implementation Checklist

**Package:** `mineproductivity.agents`
**Governing specification:** [`docs/architecture/11_AI_Agents_Design_Specification.md`](../architecture/11_AI_Agents_Design_Specification.md)
**Architecture Decision Record:** [`docs/adr/ADR-0011-AI-Agents.md`](../adr/ADR-0011-AI-Agents.md)
**Status:** Implemented and released (software v1.10.0, 2026-07-12).

All items below are satisfied: the complete design spec §6 module list is implemented, the unit suite passes with ≥95% coverage (99% including branches), the five `examples/agents/` scripts and both `benchmark/reports/agents/` reports exist and are `mypy --strict`/`ruff`-clean, and the §35 acceptance proofs each run as dedicated tests. `TaskExecutor.resume()` is an added public method resolving the spec's Approved/Rejected approval transitions, disclosed in the module docstring. No architectural changes were made relative to the locked v1.3.0 design.

Binding, **locked** implementation contract for `agents` — the sixth package built on top of the Foundation Layer, sitting directly above the now-locked `optimization`, and the enterprise operational-intelligence (orchestration) layer for the entire platform. Nothing described here may be implemented before this checklist and its governing specification exist in reviewed form, and nothing may be implemented that is not represented by an item on this list. Complete in order; every box must be checked or explicitly deferred with a linked issue and Chief Software Architect sign-off before merge.

## Pre-Implementation Gate

- [x] Design specification (`11_AI_Agents_Design_Specification.md`) read in full by the implementer, including every cross-reference to specs 01–10.
- [x] ADR-0011 read in full; the rationale for `agents` existing as a separate package above `optimization` (and for the interface-only treatment of `Agent`, `Tool`, and `AgentMemory`) is understood, not merely accepted.
- [x] `core`, `events`, `ontology`, `registry`, `plugins`, `connectors`, `kpis`, `analytics`, `decision`, `digital_twin`, `simulation`, `optimization` available and importable, exactly as released; no lower package file is modified as a side effect of this work.
- [x] Confirmed: `agents` will not import `visualization` under any circumstance — it does not exist yet (design spec §5, §37).
- [x] Confirmed: no lower package (`core` through `optimization`) will be modified to import or otherwise reference `agents` (design spec §5).
- [x] Confirmed: no concrete LLM provider SDK (OpenAI, Anthropic, Gemini, Llama, or any local-model runtime) is added as a dependency of this package — reasoning backends are out of scope (design spec §4's non-responsibilities, §35's no-provider-coupling proof).

## Package Structure

- [x] `src/mineproductivity/agents/` created matching design spec §6 exactly: `abstractions.py`, `metadata.py`, `capability.py`, `policy.py`, `task.py`, `state.py`, `memory.py`, `conversation.py`, `approval.py`, `tool.py`, `communication.py`, `goal.py`, `workflow.py`, `executor.py`, `result.py`, `audit.py`, `discovery.py`, `persistence.py`, `_registry.py`, `exceptions.py`, `__init__.py`, `README.md`.
- [x] `agents/README.md` written following the `core/README.md` template.
- [x] Confirmed `memory.py` (`AgentMemory`) and `tool.py` (`Tool`) each contain zero concrete, non-test subclasses (mechanical grep/AST check — design spec §14, §17, §35's interface-purity proof).
- [x] Confirmed no module under `src/mineproductivity/agents/` performs direct KPI, statistical, decision, twin-state, simulation-projection, or solved-plan computation of its own — every such value arrives via the corresponding lower package's public API (design spec §3.2, §35's no-fact-recomputation proof).
- [x] Confirmed no module under `src/mineproductivity/agents/` imports, or contains a string reference to, `openai`, `anthropic`, `google.generativeai`, or any other LLM provider SDK (design spec §35's no-provider-coupling proof).

## Public API

- [x] `agents/__init__.py` exports exactly the symbol list in design spec §7, alphabetized `__all__`.
- [x] `test_public_api.py` mirrors `tests/unit/core/test_public_api.py` and every existing package's own copy of it.
- [x] `TestNoForbiddenDependencies` AST-walks every `agents` submodule for a forbidden import (`visualization`) — mirrors every existing package's own copy of this test (design spec §5).
- [x] A second, reverse-direction test asserts no file under `src/mineproductivity/{core,ontology,events,registry,plugins,connectors,kpis,analytics,decision,digital_twin,simulation,optimization}/` imports `mineproductivity.agents` (design spec §5) — the `optimization`-package precedent for this test extended one layer up.

## Agent Abstractions (§8)

- [x] `Agent` (§8) — `meta: ClassVar[AgentMetadata]`; one shared abstract method `_act(task, *, context) -> AgentResult`, mirroring `decision.DecisionModel`'s shared-`_decide` posture, not `simulation`'s/`optimization`'s no-shared-method posture.
- [x] `AgentContext` (§8) — `kpi_results`, `analytics_results`, `decision_results`, `twin_snapshot`, `simulation_results`, `optimization_results`, each defaulting to an empty sequence or `None`; caller-assembles pattern only, no session-assembles variant.
- [x] Confirmed `Agent` subclasses (of every category) are stateless — no instance attribute is mutated by any `_act` implementation; all statefulness lives in `Task` (§11, §29, §32).

## Agent Capabilities and Permissions (§9)

- [x] `Permission` (§9) — frozen `core.BaseValueObject`; `capability: str`, `scope: Mapping[str, str]` (default empty).
- [x] `AgentCapabilitySet` (§9) — frozen `core.BaseValueObject`; `agent_code: str`, `permissions: tuple[Permission, ...]`.
- [x] Confirmed an `AgentCapabilitySet` is always an explicit, authored, and governed artifact — never inferred from an `Agent` subclass's own code at runtime.

## Policy Engine (§10)

- [x] `PolicyStatus` enum (§10) — exactly `Proposed`/`Active`/`Superseded`/`Retired`.
- [x] `AgentPolicy` (§10) — frozen `core.BaseValueObject`; `code`, `version` (default `"1.0.0"`), `status`, `rule`, `requires_approval` (default `False`), `denies` (default `False`).
- [x] `PolicyEngine.evaluate(task, *, capabilities, policies) -> Result[None]` (§10) implemented; confirmed to return exactly one of three outcomes — proceed, route to `AWAITING_APPROVAL`, or raise/return `PermissionDeniedError` — never a fourth.
- [x] Confirmed `PolicyEngine` never parses or evaluates `AgentPolicy.rule` as executable code — `rule` is a solver-independent string interpreted only by a concrete evaluation strategy.
- [x] Confirmed an `Active` `AgentPolicy` is never edited in place anywhere in the codebase — a changed policy is published as a new version, with the prior version transitioned to `Superseded` (§10, §26, §34's recorded anti-pattern).
- [x] `PolicyConflictError` raised for a materially-different re-registration under an existing, `Active` policy code without a version bump (§10, §26).
- [x] Confirmed `AgentPolicy` is documented as a deliberate non-reuse of `decision.Policy` — the shapes look similar but the concerns (authorization guardrail vs. business-recommendation threshold) are distinct (§10, §34's recorded anti-pattern against conflating them).

## Task Model and Agent Lifecycle (§11)

- [x] `TaskStatus` enum (§11) — exactly `Scheduled`/`Running`/`AwaitingApproval`/`Paused`/`Completed`/`Failed`.
- [x] `Task` (§11) — subclasses `core.BaseEntity[str]` directly; `goal_code`, `agent_code`, `state: TaskState`, `status: TaskStatus`; `with_state()` non-overridden, produces a new instance via `dataclasses.replace`, never mutates `self`.
- [x] `TaskState` (§11) — frozen `core.BaseValueObject`; open `attributes: Mapping[str, Any]` carries model-specific/delegation-chain data; `validate()` rejects empty `attributes`.
- [x] Identity/equality proven: `Task.__eq__`/`__hash__` inherited unchanged from `BaseEntity` (identity-based on `id`, ignoring `state`/`status`); no override anywhere in the package.
- [x] Lifecycle transitions proven to match design spec §11's state diagram exactly; `Completed` and `Failed` proven terminal (no transition out of either).

## Task Execution and Failure Recovery (§12)

- [x] `TaskExecutor` (§12) — evaluates `PolicyEngine`, dispatches to the registered `Agent`'s `_act`, gates on approval, retries on recoverable failure, persists resulting state via a `remove`-then-`add` pair against `TaskRepository`, appends to `AgentAuditTrail`.
- [x] `TaskExecutor`'s dispatch, approval-gate, and persistence sequence tested against design spec §12's sequence diagram exactly, including the approval-required, denied, and cleared branches.
- [x] Confirmed `retry_policy` (defaulting to `connectors.RetryPolicy`'s own defaults, spec 04 §10) governs only retrying the same `Agent`'s `_act` call after a transient failure — never silently reassigns a `Task` to a different agent.
- [x] Confirmed a `Task` whose retries are exhausted transitions to `Failed`, never retries indefinitely.

## Workflow Engine and Goal Decomposition (§13)

- [x] `Goal` (§13) — frozen `core.BaseValueObject`; `description`, `success_criteria` (default empty mapping).
- [x] `WorkflowEngine` (§13) — `decompose(goal, *, context) -> Sequence[Task]`; `run(goal, *, context) -> Sequence[AgentResult]`; composes `TaskExecutor` per individual `Task` rather than duplicating its dispatch/persistence/audit logic.
- [x] A scripted hypothesis-exploration task is proven to compose `simulation.ExperimentRunner.run_trials` directly (§13), without this package reimplementing simulation logic.
- [x] A scripted candidate-plan-search task is proven to compose `optimization.OptimizationExecutor`/`optimization.PlanComparator` directly (§13), without this package reimplementing optimization logic.

## Memory Model (§14)

- [x] `AgentMemory` (§14) — `remember(task_id, key, value, *, context) -> None` and `recall(task_id, key, *, context) -> Any | None` abstract; zero concrete subclasses shipped.
- [x] Confirmed a `recall()` miss returns `None` and is never treated as an error anywhere in the package's own code.
- [x] Confirmed `AgentMemory` is documented as a deliberate non-reuse of `kpis.ResultCache`/`digital_twin.TwinStateCache`/`simulation.SimulationStateCache` — memory is semantically meaningful to an agent's reasoning, never a silently-evictable performance optimization.

## Conversation Context (§15)

- [x] `ConversationTurn` (§15) — frozen `core.BaseValueObject`; `speaker` (open string), `content`, `occurred_at`.
- [x] `ConversationContext` (§15) — frozen `core.BaseValueObject`; `task_id`, `turns: tuple[ConversationTurn, ...]` (default empty); a new turn produces a new instance, never mutates `turns` in place.

## Human Approval Workflows (§16)

- [x] `ApprovalStatus` enum (§16) — exactly `Pending`/`Approved`/`Rejected`.
- [x] `ApprovalRequest` (§16) — frozen `core.BaseValueObject`; `task_id`, `requested_action`, `status` (default `Pending`), `approver` (default `None`), `resolved_at` (default `None`).
- [x] Confirmed an `ApprovalRequest` resolving to `Approved` transitions its `Task` from `AwaitingApproval` back to `Running`; a resolution to `Rejected` transitions it directly to `Failed`, carrying the rejection as an `AgentResult` warning.
- [x] Confirmed `TaskExecutor` never resolves an `ApprovalRequest` itself — resolution is exclusively a caller (human-supervisor-facing) action.

## Tool Invocation (§17)

- [x] `ToolMetadata` (§17) — `code`, `description`, `version` (default `"1.0.0"`).
- [x] `Tool` (§17) — `meta: ClassVar[ToolMetadata]`; `invoke(*, arguments, context) -> Mapping[str, Any]` abstract; zero concrete subclasses shipped.
- [x] `ToolInvocation` (§17) — frozen `core.BaseValueObject`; `tool_code`, `arguments`, `result`, `invoked_at`.
- [x] Confirmed this package never invokes a `Tool` on an `Agent`'s behalf — a concrete `Agent` implementation looks up and invokes a needed `Tool` itself and carries the resulting `ToolInvocation` on its own `AgentResult`.

## Inter-Agent Communication and Delegation (§18)

- [x] `AgentMessage` (§18) — frozen `core.BaseValueObject`; `from_agent_code`, `to_agent_code`, `task_id`, `content` (open mapping), `sent_at`; published via `events.EventBus` directly, no new message bus defined.
- [x] `DelegationRequest` (§18) — frozen `core.BaseValueObject`; `task_id`, `from_agent_code`, `to_agent_code`, `reason`.
- [x] Confirmed delegation is expressed as an ordinary `AgentMessage` whose `content` carries a `DelegationRequest` — no separate delegation-transport mechanism exists.
- [x] Confirmed the delegation chain (which agent handed a task to which) is carried in `Task.state.attributes` as an open-mapping entry — no new typed field added to `Task` for this purpose.

## Multi-Agent Collaboration (§19)

- [x] A scripted integration test reproduces design spec §19's worked example shape (a `ShiftSupervisor`-category task coordinating a `Fleet`-category and a `Maintenance`-category task via `WorkflowEngine.decompose`/`run`), each producing its own audited `AgentResult`.
- [x] Confirmed no concrete category behavior (which evidence a `FleetAgent` weighs, etc.) is hard-coded into `WorkflowEngine` or `TaskExecutor` — category-specific reasoning lives exclusively in the registered `Agent` subclass.

## Agent Outputs (§20)

- [x] `AgentResult` (§20) — frozen `core.BaseValueObject`; `task_id` (default `""`), `computed_at`, `warnings` (default empty tuple), `output` (open mapping, default empty), `explanation: Explanation | None` (reuses `decision.Explanation` directly — no second justification type), `tool_invocations: tuple[ToolInvocation, ...]` (default empty).
- [x] Confirmed `TaskState` is **not** an `AgentResult` subclass (it represents the task's condition itself, not the outcome of an orchestration call about it).

## Explainability and Audit Trails (§21)

- [x] `AgentAuditEntry` (§21) — frozen `core.BaseValueObject`; `recorded_at`, `result: AgentResult`, `agent_code`, `scope`.
- [x] `AgentAuditTrail.record()`/`query(*, scope=None)` (§21) implemented; `record()` proven to serialize concurrent appends internally; `query()` proven never to block on a concurrent `record()`.
- [x] Confirmed every `AgentResult`'s `explanation` and every `ToolInvocation` it carries are preserved verbatim in the recorded `AgentAuditEntry` — never summarized.

## Agent Registry and Tool Registry (§22)

- [x] `agents._registry.REGISTRY`/`register` (§22) — `Registry[str, type[Agent]]`, raising `AgentValidationError` for an empty code and `AgentVersionConflictError` for a materially-different re-registration under an existing code.
- [x] `agents._registry.TOOLS`/`register_tool` (§22) — `Registry[str, type[Tool]]`, identical error semantics, specialized for `Tool`.
- [x] `EntryPointSpec(group="mineproductivity.agents", target_registry="agents")` and `EntryPointSpec(group="mineproductivity.agents.tools", target_registry="agents.tools")` discovery wired via `registry.EntryPointDiscovery` (§31).
- [x] Confirmed `REGISTRY` and `TOOLS` are never merged into one — an `Agent` type and a `Tool` type remain orthogonal registrable concepts throughout the codebase.

## Agent Discovery (§23)

- [x] `by_category()`/`by_scope()` (§23) — plain `core.PredicateSpecification` factories; composed with `TaskRepository.list()`; confirmed to return an empty sequence (never raise) for a filter matching nothing.
- [x] Confirmed the three-way distinction (`REGISTRY`/`TOOLS` = which types are known; `TaskRepository` = which task instances currently exist; `discovery.py` = query facade over the instance store) is never conflated anywhere in the codebase.

## Serialization and Persistence (§24, §25)

- [x] Every `TaskState`/`Permission`/`AgentCapabilitySet`/`AgentPolicy`/`ConversationTurn`/`ConversationContext`/`ApprovalRequest`/`ToolMetadata`/`ToolInvocation`/`AgentMessage`/`DelegationRequest`/`Goal`/`AgentResult`/`AgentAuditEntry` and `Task` itself confirmed to serialize via `core.serialization` (`DataclassSerializer`/`to_dict`) with no bespoke per-type serializer.
- [x] `TaskRepository` implemented as `type TaskRepository = BaseRepository[Task, str]` — a type alias, **not** a new ABC or subclass.
- [x] Reference implementation uses `core.InMemoryRepository[Task, str]()` directly, with zero new persistence code.
- [x] Test suite for `TaskRepository` behavior written against the `core.BaseRepository[Task, str]` contract alone, never against `InMemoryRepository`-specific internals (§35's repository-substitutability proof).

## Versioning (§26)

- [x] `AgentMetadata.version`/`ToolMetadata.version` (a registered type's own SemVer) and `AgentPolicy.version` (a governed guardrail artifact's own SemVer) confirmed to vary independently — no code path derives one from another.
- [x] `AgentVersionConflictError` raised at registration time for a materially-different re-registration under an existing `AgentMetadata`/`ToolMetadata` code; `PolicyConflictError` raised at publication time for the equivalent `AgentPolicy` case — both never deferred.

## Caching (§27)

- [x] Confirmed no dedicated cache module exists anywhere in the package (§27's documented, deliberate non-need; §34's recorded anti-pattern against introducing one "for consistency").
- [x] Confirmed `AgentContext` assembly happens once, at construction, never re-fetched per-retry or per-delegation (§36).
- [x] Confirmed `AgentMemory` (§14) is never treated as a substitute for a cache — its absence-of-caching rationale is documented distinctly from its own semantics.

## Validation (§28)

- [x] `AgentMetadata.validate()`/`ToolMetadata.validate()` — non-empty `code`, category matches the closed `AgentCategory` namespace where applicable.
- [x] `Task.validate()` — non-empty `goal_code` and `agent_code`.
- [x] `TaskState.validate()` — non-empty `attributes`.
- [x] `AgentPolicy.validate()` — non-empty `code` and `rule`.
- [x] `PolicyEngine.evaluate()`'s three-outcome contract mechanically proven to never return a fourth outcome.

## Metadata (§29)

- [x] `AgentCategory` enum (§29) — exactly `Production`/`Dispatch`/`Fleet`/`Maintenance`/`DrillAndBlast`/`ShiftSupervisor`/`Esg`/`Safety`/`ExecutiveAdvisor`/`Planning`; a closed enum, adding a member is a governance-reviewed change.
- [x] `AgentMetadata` (§29) — `code`, `category`, `description`, `version` (default `"1.0.0"`); `validate()` rejects an empty `code`.
- [x] Confirmed `AgentMetadata.code` names an agent **type** and is never confused with a `Task.id` anywhere in the codebase.

## Error Handling (§30)

- [x] Full exception hierarchy (design spec §6 `exceptions.py`): `AgentValidationError`, `TaskNotFoundError`, `AgentExecutionError`, `AgentVersionConflictError`, `PolicyConflictError`, `PermissionDeniedError` — each subclassing the matching `core` or `registry` exception (`AgentVersionConflictError`/`PolicyConflictError` subclass `registry.RegistrationError`; the rest subclass a `core` exception).
- [x] Confirmed no `Agent._act` implementation raises for a legitimately incomplete or ambiguous task — returns an `AgentResult` carrying a warning instead (§30's "qualify, don't coerce" central rule).
- [x] Confirmed `PermissionDeniedError` is the one case in this package where a policy outcome is a hard-stop exception rather than a warning — never a silently-persisted `AgentResult`.

## Extension Points & Plugin Integration (§31)

- [x] Entry-point groups `mineproductivity.agents` and `mineproductivity.agents.tools` documented and wired exactly per §31.
- [x] A scripted integration test exercises a fixture "sitepack" plugin (registered via entry points, mirroring `examples/registry/01_register_and_discover.py`'s pattern) that subclasses `Agent`, proving the platform-side dispatch and registration path works end to end.
- [x] A second fixture plugin subclasses `Tool` and is proven discoverable via `TOOLS` independently of the `Agent` fixture.

## Thread Safety & Concurrency (§32)

- [x] `Agent` instances (of every category) confirmed stateless and safe to share/read across threads with no locking.
- [x] `Task` instances confirmed immutable and safe to share/read across threads with no locking.
- [x] `TaskRepository`'s per-id write serialization contract documented and tested against any production-grade implementation candidate; confirmed the bare `core.InMemoryRepository` reference implementation provides **no** locking of its own — any concurrent-write test against it must add external synchronization itself.
- [x] `AgentAuditTrail.record()` proven to serialize concurrent appends internally; no lost entry under concurrent load.
- [x] `agents.REGISTRY`/`agents.TOOLS` each confirmed read-only and thread-safe after startup discovery, inheriting `Registry`'s own contract.
- [x] Independent `Task`s (different `id`s) proven to execute fully in parallel without contention.

## Security (§33)

- [x] Confirmed every `Agent._act`-proposed action is evaluated by `PolicyEngine`/`TaskExecutor` before any effect — never executed directly against a `Tool` or downstream system.
- [x] Confirmed a concrete `Tool` implementation validates its own `arguments` independently — never assumes an `Agent`'s `AgentCapabilitySet` already constrains argument-level safety.
- [x] Confirmed `AgentMemory` is scoped per `task_id` in every reference usage — no global-sharing code path exists.
- [x] Confirmed no new cryptographic, network, or credential-handling surface is introduced by this package.

## Tests

- [x] `tests/unit/agents/` mirrors `src/mineproductivity/agents/` 1:1.
- [x] Coverage ≥95%.
- [x] Unit tests per concrete agent category — at least one flagship agent per `AgentCategory`, each against a scripted task with a known expected `AgentResult` (§35).
- [x] Identity/equality tests, policy-gate tests, approval-lifecycle tests, failure-recovery tests, delegation tests, `simulation.ExperimentRunner`/`optimization.OptimizationExecutor` composition tests, interface-only ABC contract tests, registry/discovery isolation tests, and concurrency stress tests as enumerated in design spec §35.
- [x] The six package acceptance proofs in design spec §35 (no-fact-recomputation, immutability, interface-purity, no-architectural-drift, no-provider-coupling, policy-enforcement) each independently verified and recorded in the PR description.

## Documentation

- [x] `agents/README.md` complete.
- [x] Every registered `Agent`/`Tool` type's docstring restates its `AgentMetadata.description`/`ToolMetadata.description` for source-level readability.

## Examples

- [x] `examples/agents/01_single_agent_task.py` — a single `Agent` category executing one `Task` end-to-end via `TaskExecutor`.
- [x] `examples/agents/02_policy_gated_approval.py` — a scripted `AgentPolicy` requiring approval, driving a `Task` through `AwaitingApproval` to `Completed` via a resolved `ApprovalRequest`.
- [x] `examples/agents/03_multi_agent_workflow.py` — the design spec §19 worked example (`ShiftSupervisor`/`Fleet`/`Maintenance` coordination via `WorkflowEngine`), end-to-end.
- [x] `examples/agents/04_hypothesis_and_plan_search.py` — a task composing `simulation.ExperimentRunner` and a task composing `optimization.OptimizationExecutor`, each via `WorkflowEngine` (§13).
- [x] `examples/agents/05_plugin_agent_and_tool.py` — a third-party-style `Agent` and `Tool` subclass registered via entry points, mirroring `examples/registry/01_register_and_discover.py`'s pattern.
- [x] All examples pass `mypy --strict` + `ruff`.

## Benchmarks

- [x] `TaskRepository.get()`/`list()` latency at representative task-population scale, recorded in `benchmark/reports/agents/`.
- [x] A `WorkflowEngine`-decomposed multi-task workflow's parallel-execution throughput at representative sub-task counts, recorded.

## Certification

- [x] Design spec §35's six package acceptance proofs pass and are recorded in the PR description (duplicated here from Tests for merge-gate visibility).

## Type Hints, Mypy, Ruff, Coverage

- [x] 100% type-hinted; `mypy --strict` clean.
- [x] `ruff check` and `ruff format --check` clean.
- [x] Coverage report attached; ≥95%.

## Release

- [x] `CHANGELOG.md` updated.
- [x] Root README dependency diagram cross-checked — confirm no forbidden import (`visualization`) was introduced, and confirm no lower package gained a new `agents` import.
- [x] Version bump proposed and reviewed.
- [x] Design spec §35's acceptance proofs re-verified as final merge gate.

---

*Derived from [`11_AI_Agents_Design_Specification.md`](../architecture/11_AI_Agents_Design_Specification.md). Keep in sync with the governing specification and with [`ADR-0011-AI-Agents.md`](../adr/ADR-0011-AI-Agents.md).*
