# Decision Intelligence — Implementation Checklist

**Package:** `mineproductivity.decision`
**Governing specification:** [`docs/architecture/07_Decision_Intelligence_Design_Specification.md`](../architecture/07_Decision_Intelligence_Design_Specification.md)
**Architecture Decision Record:** [`docs/adr/ADR-0007-Decision-Intelligence.md`](../adr/ADR-0007-Decision-Intelligence.md)
**Status:** Not started

Binding, **locked** implementation contract for `decision` — the second package built on top of the Foundation Layer, sitting directly above the now-locked `analytics`. Nothing described here may be implemented before this checklist and its governing specification exist in reviewed form, and nothing may be implemented that is not represented by an item on this list. Complete in order; every box must be checked or explicitly deferred with a linked issue and Chief Software Architect sign-off before merge.

## Pre-Implementation Gate

- [ ] Design specification (`07_Decision_Intelligence_Design_Specification.md`) read in full by the implementer, including every cross-reference to specs 01–06.
- [ ] ADR-0007 read in full; the rationale for `decision` existing as a separate package above `analytics` (not folded into it, not merged with a future `optimization`/`decision` combination) is understood, not merely accepted.
- [ ] `core`, `events`, `ontology`, `registry`, `plugins`, `connectors`, `kpis`, `analytics` available and importable, exactly as released; no Foundation Layer or `analytics` file is modified as a side effect of this work.
- [ ] Confirmed: `decision` will not import `digital_twin`, `simulation`, `optimization`, `visualization`, or `agents` under any circumstance — none of those packages exist yet (design spec §5).
- [ ] Confirmed: no lower package (`core` through `analytics`) will be modified to import or otherwise reference `decision` (design spec §5, §3.5).

## Package Structure

- [ ] `src/mineproductivity/decision/` created matching design spec §6 exactly: `abstractions.py`, `metadata.py`, `result.py`, `pipeline.py`, `rules.py`, `policy.py`, `thresholds.py`, `strategy.py`, `recommendation.py`, `ranking.py`, `explanation.py`, `root_cause.py`, `what_if.py`, `prioritization.py`, `planning.py`, `alerting.py`, `scoring.py`, `realtime.py`, `batch.py`, `audit.py`, `_registry.py`, `exceptions.py`, `__init__.py`, `README.md`.
- [ ] `decision/README.md` written following the `core/README.md` template.
- [ ] Confirmed `pipeline.py` contains zero strategy-specific branches (mechanical grep/AST check — design spec §9).
- [ ] Confirmed `root_cause.py`/`what_if.py` contain zero concrete, non-test subclasses of `RootCauseAnalyzer`/`WhatIfEngine` (design spec §18, §19, §34's interface-purity proof).

## Public API

- [ ] `decision/__init__.py` exports exactly the symbol list in design spec §7, alphabetized `__all__`.
- [ ] `test_public_api.py` mirrors `tests/unit/core/test_public_api.py` and every existing package's own copy of it.
- [ ] `TestNoForbiddenDependencies` AST-walks every `decision` submodule for a forbidden import (`digital_twin`, `simulation`, `optimization`, `visualization`, `agents`) — mirrors every existing package's own copy of this test (design spec §5).
- [ ] A second, reverse-direction test asserts no file under `src/mineproductivity/{core,ontology,events,registry,plugins,connectors,kpis,analytics}/` imports `mineproductivity.decision` (design spec §5, §3.5) — the `analytics`-package precedent for this test (spec 06 checklist) extended one layer up.

## Abstractions & Registry (§8, §31, §32)

- [ ] `DecisionModel` (§8) — `decide()` non-overridable orchestration checking for at least one `KPIResult`/`AnalyticsResult` in context; `_decide()` abstract.
- [ ] `DecisionContext` (§8) — `kpi_results`, `analytics_results`, `scope`, optional `event_store`, optional `as_of`.
- [ ] `DecisionMetadata`/`DecisionCategory` (§30) — `code`, `category`, `description`, `version`; `validate()` rejects an empty `code`.
- [ ] `decision._registry.REGISTRY`/`register` (§32) — `Registry[str, type[DecisionModel]]`, raising `DecisionValidationError` for an empty code and `DecisionVersionConflictError` for a materially-different re-registration under an existing code.
- [ ] `EntryPointSpec(group="mineproductivity.decision", target_registry="decision")` discovery wired via `registry.EntryPointDiscovery` (§32).

## Decision Pipelines and Rule Engine (§9, §10, §11)

- [ ] `PipelineStage` (ABC) and `DecisionPipeline` (§9) — `run()` chains stages in order, rejects a pipeline whose final stage does not yield a `DecisionResult`.
- [ ] `ModelStage` (§9) — the concrete terminal stage wrapping one `DecisionModel`.
- [ ] `Rule` type alias over `core.BaseSpecification[DecisionContext]` (§10) — no bespoke rule DSL introduced anywhere.
- [ ] `RuleEngine.evaluate()` (§10) — isolates one malformed rule's failure from the rest, returns triggered rule names in stable (sorted) order.
- [ ] `RuleEngineStage` (§10) — the `PipelineStage` wrapper composing `RuleEngine` + a `Policy` into a `DecisionPipeline`.
- [ ] Confirmed no second rule-composition mechanism exists anywhere in the package beyond `core.BaseSpecification`'s `&`/`|`/`~` (§11, §34).

## Business Policies and Thresholds (§12, §13)

- [ ] `DecisionStatus` enum (§12) — exactly `Proposed`/`Active`/`Superseded`/`Retired`, mirroring `kpis.KPIStatus`.
- [ ] `Policy` (§12) — `code`, `version`, `status`, `rules`, `thresholds`, `strategy_code`; `validate()` rejects an empty `code` or zero rules.
- [ ] `PolicyConflictError` raised for a re-registration attempt that changes an `Active` policy's rules/thresholds without a version bump and a `Superseded` transition for the prior version (§12, §29).
- [ ] `Threshold` (§13) — `field`, `comparator` (exactly `<`/`<=`/`>`/`>=`/`==`/`!=`), `limit`; `validate()` rejects an empty `field`.
- [ ] `ThresholdBreach` (§28) — `threshold`, `observed_value`, `breached_at`.

## Decision Strategies, Recommendations, Ranking, Explanations (§14–§17)

- [ ] `DecisionStrategy` (ABC) / `ThresholdDecisionStrategy` (§14) — evaluates a `Policy`'s rules against a `DecisionContext`, produces `Recommendation`s for triggered, threshold-breaching rules.
- [ ] `Recommendation` (§15) — `policy_code`, `triggered_rules`, `summary`, `severity`, `evidence`, optional `explanation`; always traceable to specific `Policy`/`Rule` names and `KPIResult.code`/`AnalyticsResult.model_code` evidence.
- [ ] `RankingStrategy` (ABC) / `WeightedScoreRanking` (§16) — orders `Recommendation`s into `RankedRecommendation`s by `DecisionScore`.
- [ ] `ExplanationBuilder`/`ExplanationStage` (§17) — walks a `Recommendation`'s provenance into a structured `Explanation` (`premises`, `evidence_refs`); composes as a `DecisionPipeline` terminal stage.
- [ ] Confirmed ranking (§16) and prioritization (§20) remain distinct code paths, never collapsed into one score (§33).

## Interface-Only Modules (§18, §19)

- [ ] `RootCauseAnalyzer` (ABC) — `_analyze(symptom, context) -> RootCauseResult` signature only; zero concrete subclasses shipped.
- [ ] `WhatIfEngine` (ABC) — `_simulate(context, hypothesis, as_of) -> WhatIfResult` signature only, deliberately reusing `events.AsOf.scenario`; zero concrete subclasses shipped.
- [ ] `RootCauseResult`, `WhatIfResult` result types implemented per §18/§19 even though no producer of them ships in this release.

## Action Prioritization and Planning (§20, §21)

- [ ] `ActionPriority` (§20) — `urgency`, `impact`, `effort`, `priority_score` property; all three components retained alongside the aggregate.
- [ ] `ActionPrioritizer.prioritize()` (§20) — assigns `ActionPriority` to each `RankedRecommendation`.
- [ ] `ActionPlanner.plan()` (§21) — topological ordering of prioritized actions respecting an optional `dependencies` mapping; returns `Result.err` on a detected cycle rather than silently dropping it.
- [ ] Confirmed `ActionPlanner` implements its own narrow ordering and does **not** reuse `kpis.DependencyGraph` (§3.3, §21, §33 — the coupling-mismatch rule is the single most load-bearing design decision in this module).
- [ ] `ActionPlan` (§21) — `ordered_actions`, `priorities`.

## Alerting and Scoring (§22, §23, §24)

- [ ] `AlertGenerator.from_breach()`/`from_recommendation()` (§22) — produces `Alert` value objects only; confirmed no I/O/channel-delivery side effect exists anywhere in this class.
- [ ] `Alert` (§22) — `message`, `severity`, `scope`, optional `triggered_by`.
- [ ] `DecisionScorer.score()` (§23) — `DecisionScore` (`value`, `components`) as a function of severity, policy weight, and optional `ConfidenceScore`.
- [ ] `ConfidenceScorer.score()` (§24) — `ConfidenceScore` (`value`, `basis`) derived from `analytics.DataQualityScore` plus rule-evidence strength; confirmed fallback to `"rule_strength"` basis when no `DataQualityScore` is present in context, and that the `basis` field correctly records which path was taken.

## Real-Time and Batch Evaluation, Audit Trail (§25–§28)

- [ ] `RealTimeDecisionSession` (§25) — subscribes to `events.EventBus`, refreshes `KPIEngine`/`BatchAnalyticsRunner` outputs per relevant event, re-runs `DecisionPipeline`; `start()` returns the `events.Subscription` handle; `latest()` reads without re-running the pipeline.
- [ ] `BatchDecisionRunner` (§26) — thin, named wrapper over `DecisionPipeline.run()`.
- [ ] `DecisionAuditTrail`/`DecisionAuditEntry` (§27) — append-only; `record()`/`query()`; `source_event_ids` populated on a best-effort basis (§27's "what traceable means in practice" note) — an empty tuple is not an error.
- [ ] `DecisionAuditTrail` thread safety: concurrent `record()` calls proven safe under stress test (append-only lock or equivalent); `query()` proven non-blocking against a concurrent `record()`.
- [ ] Real-time/batch parity proven: `RealTimeDecisionSession.latest()` and a `BatchDecisionRunner` run over the same assembled context produce the same `DecisionResult` (§34).

## Result Models, Lifecycle, Metadata (§28–§30)

- [ ] `DecisionResult` base (`model_code`, `computed_at`, `warnings`) and every concrete subclass (`Recommendation`, `RankedRecommendation`, `ActionPlan`, `Alert`, `RootCauseResult`, `WhatIfResult`) implemented as frozen `core.BaseValueObject`s.
- [ ] `Explanation`, `DecisionScore`, `ConfidenceScore`, `ActionPriority`, `Threshold`, `ThresholdBreach` implemented as plain `BaseValueObject`s (not `DecisionResult` subclasses) per §28's explicit distinction.
- [ ] Every result type serializes via `core.serialization` (`DataclassSerializer`/`to_dict`) with no bespoke per-type serializer (§28).
- [ ] `Policy` lifecycle (§29): `Proposed → Active → Superseded → Retired`, version bump + `Superseded` transition enforced for any change to an `Active` policy's rules/thresholds.
- [ ] `DecisionMetadata.version` (§30) confirmed to version independently of any `Policy`'s own version.

## Thread Safety & Concurrency

- [ ] Every `DecisionModel` subclass confirmed stateless across `decide()` calls (no instance mutation) — test proves concurrent invocation of one shared instance is safe (§8).
- [ ] `decision.REGISTRY` confirmed read-only and thread-safe after startup discovery, inheriting `Registry`'s own contract (§8, spec 03 §24).
- [ ] `DecisionAuditTrail` confirmed **not** thread-safe on its own without its internal synchronization mechanism; stress-tested under concurrent `record()` calls (§27).

## Error Handling

- [ ] Full exception hierarchy (design spec §6 `exceptions.py`): `DecisionValidationError`, `NoApplicablePolicyError`, `DecisionModelNotFoundError`, `DecisionVersionConflictError`, `PolicyConflictError` — each subclassing the matching `core` exception.
- [ ] Confirmed `DecisionModel.decide()` never raises for a legitimately no-recommendation input — returns a `DecisionResult` with zero recommendations instead (§8, §33).
- [ ] `DecisionVersionConflictError`/`PolicyConflictError` proven to raise at *registration* time for a materially-different re-registration/re-publication, never deferred.
- [ ] `Policy` referencing a `strategy_code` for which no `DecisionModel` is registered proven to fail at activation time (`DecisionModelNotFoundError`), not silently at first evaluation (§12).

## Performance & Memory

- [ ] Confirmed `decision` performs no independent large-scale computation — rule evaluation profile dominated by already-small `DecisionContext` objects, not raw event/statistical volume (§35).
- [ ] `RealTimeDecisionSession` confirmed to delegate to `KPIEngine.execute()`/`BatchAnalyticsRunner` rather than re-fetching or re-aggregating raw data itself (§35).
- [ ] `DecisionAuditTrail.record()` confirmed O(1) per entry; `query()` confirmed to support scope-based filtering without a full linear scan at production audit-trail sizes (§35).
- [ ] `ActionPlanner.plan()` confirmed O(V+E) over the declared action-dependency graph (§35).
- [ ] `Policy` lookup confirmed registry-speed (in-memory), never a disk/network round-trip on the rule-evaluation hot path (§35).

## Tests

- [ ] `tests/unit/decision/` mirrors `src/mineproductivity/decision/` 1:1.
- [ ] Coverage ≥95%.
- [ ] Unit tests per concrete strategy (`ThresholdDecisionStrategy`, `WeightedScoreRanking`) against hand-authored `Policy`/`Threshold` fixtures with known expected outputs (§34).
- [ ] Rule composition tests reusing `core.specification`'s own test patterns (§34).
- [ ] Policy governance tests: `PolicyConflictError` raised for an unversioned `Active`-policy change (§34).
- [ ] Confidence-scoring correctness tests: with and without a `DataQualityScore` present, asserting the correct `basis` recorded (§34).
- [ ] Registry/discovery isolation tests mirroring `tests/integration/test_registry_plugin_discovery.py`'s healthy/broken fixture-plugin pattern, specialized for `DecisionModel` (§34).
- [ ] Interface-only ABC contract tests for `RootCauseAnalyzer`/`WhatIfEngine` (bare-ABC instantiation raises `TypeError`) — no algorithmic-correctness test exists for either (§34).
- [ ] Action-planning ordering tests: correct topological ordering and correct cycle rejection (§34).
- [ ] Real-time/batch parity tests (§34).
- [ ] The five package acceptance proofs in design spec §34 (no-fact-recomputation, rule-isolation, interface-purity, no-architectural-drift, audit-completeness) each independently verified and recorded in the PR description.

## Documentation

- [ ] `decision/README.md` complete.
- [ ] Every registered `DecisionModel`'s docstring restates its `DecisionMetadata.description` for source-level readability.

## Examples

- [ ] `examples/decision/01_pipeline_over_evidence.py` — the design spec §9 worked example (fleet-availability policy evaluated against `UTIL.OEE` + its trend), end-to-end.
- [ ] `examples/decision/02_action_planning.py` — `ActionPrioritizer` + `ActionPlanner` producing an `ActionPlan` with declared dependencies.
- [ ] `examples/decision/03_realtime_session.py` — `RealTimeDecisionSession` over an `EventBus`, producing a live `DecisionResult`.
- [ ] `examples/decision/04_plugin_strategy.py` — a third-party-style `DecisionStrategy` registered via entry points, mirroring `examples/registry/01_register_and_discover.py`'s pattern.
- [ ] All examples pass `mypy --strict` + `ruff`.

## Benchmarks

- [ ] `RuleEngine.evaluate()` throughput at representative policy/rule-count scale, recorded in `benchmark/reports/decision/`.
- [ ] `DecisionAuditTrail` append/query latency at representative audit-trail sizes.

## Certification

- [ ] Design spec §34's five package acceptance proofs pass and are recorded in the PR description (duplicated here from Tests for merge-gate visibility).

## Type Hints, Mypy, Ruff, Coverage

- [ ] 100% type-hinted; `mypy --strict` clean.
- [ ] `ruff check` and `ruff format --check` clean.
- [ ] Coverage report attached; ≥95%.

## Release

- [ ] `CHANGELOG.md` updated.
- [ ] Root README dependency diagram cross-checked — confirm no forbidden import (`digital_twin`, `simulation`, `optimization`, `visualization`, `agents`) was introduced, and confirm no lower package gained a new `decision` import.
- [ ] Version bump proposed and reviewed.
- [ ] Design spec §34's acceptance proofs re-verified as final merge gate.

---

*Derived from [`07_Decision_Intelligence_Design_Specification.md`](../architecture/07_Decision_Intelligence_Design_Specification.md). Keep in sync with the governing specification and with [`ADR-0007-Decision-Intelligence.md`](../adr/ADR-0007-Decision-Intelligence.md).*
