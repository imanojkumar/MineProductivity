# Unit Tests — mineproductivity.decision

## Purpose

Unit tests for `src/mineproductivity/decision/`, mirroring its structure one-to-one.

## Scope

Isolated tests for `mineproductivity.decision` only. Cross-package behavior belongs in `tests/integration/`.

## Responsibilities

- Cover every public symbol exported by `mineproductivity.decision` once implemented.

## Contents

- `test_exceptions.py` — the exception hierarchy.
- `test_metadata.py` — `DecisionMetadata`, `DecisionCategory`.
- `test_thresholds.py` — `Threshold`.
- `test_result.py` — `DecisionResult` and every concrete result/value type, plus `core.serialization` round-trips.
- `test_abstractions.py` — `DecisionModel`, `DecisionContext` (including `triggered_rules`/`recommendations`), including a stateless-concurrency proof.
- `test_pipeline.py` — `PipelineStage`, `DecisionPipeline`, `ModelStage`.
- `test_rules.py` — `Rule` composition, `RuleEngine.evaluate()` (including the rule-isolation proof), `RuleEngineStage`.
- `test_policy.py` — `DecisionStatus`, `Policy`, `publish_policy`/`published_policy`/`policy_history` governance behavior.
- `test_strategy.py` — `DecisionStrategy`, `ThresholdDecisionStrategy` (recommendation generation, threshold-breach evaluation, comparator edge cases, pipeline integration).
- `test_scoring.py` — `DecisionScorer`, `ConfidenceScorer` (score boundaries, severity/confidence weighting, `DataQualityScore` derivation).
- `test_ranking.py` — `RankingStrategy`, `WeightedScoreRanking` (ranking correctness, ties, registry/pipeline integration).
- `test_explanation.py` — `ExplanationBuilder`, `ExplanationStage` (premise/evidence generation, non-terminal pipeline integration).
- `test_prioritization.py` — `ActionPrioritizer` (urgency/impact/effort assignment, edge cases).
- `test_root_cause.py` — `RootCauseAnalyzer` interface-purity proof (zero concrete subclasses, docstring-only abstract method body).
- `test_what_if.py` — `WhatIfEngine` interface-purity proof (zero concrete subclasses, docstring-only abstract method body), mirroring `test_root_cause.py`.
- `test_planning.py` — `ActionPlanner.plan` (priority-score-descending degenerate case, dependency ordering, diamond dependencies, cycle rejection, duplicate-`policy_code` rejection).
- `test_alerting.py` — `AlertGenerator.from_breach`/`from_recommendation` (default/custom severity, `scope` pass-through, `None` for sub-alertable severities).
- `test_realtime.py` — `RealTimeDecisionSession` (KPI/analytics refresh and re-decide on publish, partial/total KPI-refresh failure, pipeline-failure handling, scope derivation, out-of-order-delivery ordering guarantee, audit-trail wiring, subscription cancellation).
- `test_batch.py` — `BatchDecisionRunner` (delegation to `DecisionPipeline.run`, optional audit-trail wiring).
- `test_audit.py` — `DecisionAuditEntry`/`DecisionAuditTrail` (frozen `context_scope`, record/query, scope filtering, snapshot isolation, concurrent-record safety).
- `test__registry.py` — `REGISTRY`, `register`.
- `test_public_api.py` — `__all__` surface, forbidden/reverse dependency checks, circular-import checks.

Covers Phase 07.1 (Decision Intelligence Foundation), Phase 07.2 (Decision Rule Engine), Phase 07.3 (Decision Intelligence Analysis Layer), and Phase 07.4 (Decision Operational Services) — every module `src/mineproductivity/decision/README.md` lists is tested here.

## Dependencies

`pytest`.

## Future Work

`decision` is feature-complete; add tests for a concrete `RootCauseAnalyzer`/`WhatIfEngine` plugin only if one is ever added to this package (neither is expected to ship here, per §33's own anti-pattern entry).

## References

- Reference Implementation Blueprint v1.0
