# mineproductivity.decision

## Purpose

Decision-support and recommendation frameworks that translate `analytics`' statistical judgments (trends, benchmarks, confidence intervals) into recommended, ranked, explained, actionable decisions — the platform's prescriptive layer, sitting directly above `analytics`' descriptive layer.

## Scope

**What belongs here:**
- Decision/recommendation interfaces and contracts.
- Decision provenance and explainability contracts.

**What must never belong here:**
- AI agent orchestration (see `agents`).
- Presentation/visualization logic (see `visualization`).

## Responsibilities

- Implements the `decision` subsystem as defined in the Reference Implementation Blueprint v1.0.
- **Phase 07.1 — Decision Intelligence Foundation** is implemented: every component required before concrete decision models can exist, per `docs/architecture/07_Decision_Intelligence_Design_Specification.md`. `DecisionModel` (ABC)/`DecisionContext` (§8) mirror `analytics.AnalyticsModel`/`AnalyticsContext` one layer up — `decide()` is the non-overridden orchestration wrapper checking a `DecisionContext` carries at least one `KPIResult`/`AnalyticsResult`, `_decide()` is the abstract method every concrete strategy implements. `DecisionMetadata`/`DecisionCategory` (§30) are the minimal registration schema, as light as `analytics.AnalyticsMetadata`. The full `DecisionResult` family (§28) is implemented: `Recommendation`, `RankedRecommendation`, `ActionPlan`, `Alert`, `RootCauseResult`, `WhatIfResult` (envelope subclasses) and `Explanation`, `DecisionScore`, `ConfidenceScore`, `ActionPriority`, `ThresholdBreach` (plain, supporting value objects) — every type serializes via `core.serialization` with no bespoke per-type serializer. `Threshold` (normally `thresholds.py`'s own later-phase module) is included ahead of schedule because `ThresholdBreach` cannot be correctly typed without it. `DecisionPipeline`/`PipelineStage`/`ModelStage` (§9) compose ordered stages over one `DecisionContext`, holding no strategy-specific branching, mirroring `analytics.AnalyticsPipeline` one layer down. `REGISTRY`/`register` (§32) specialize `registry.Registry` exactly as `analytics._registry`/`kpis._registry` do. The full exception hierarchy (§6) is implemented.
- **Phase 07.2 — Decision Rule Engine** is implemented: rule composition/evaluation, policy governance, and the default, concrete decision strategy. `Rule` (§10) is a `type` alias over `core.BaseSpecification[DecisionContext]`, reusing the same composition mechanism `events.EventFilter` already established — no bespoke rule language. `RuleEngine.evaluate()`/`RuleEngineStage` (§10) isolate one malformed rule's failure from the rest and attach triggered rule names to `DecisionContext.triggered_rules` — a necessary, minimal, disclosed extension of that Phase 07.1 class (`None` by default, meaning "not yet evaluated," deliberately distinct from `()`, "evaluated, nothing triggered" — collapsing the two was a real bug caught by this phase's own QA review and fixed before release). `DecisionStatus`/`Policy` (§12) are versioned, governed business artifacts, publishable via `policy.publish_policy` (an internal function — see `policy.py`'s own module docstring for why it is not re-exported, and for a disclosed, inherent limitation of its "changed rules" detection when reusing `core.PredicateSpecification`'s lambda-identity equality); `policy.policy_history` records every version a publish transitioned to `Superseded`; publishing a `Policy` as `Active` while its `strategy_code` names no registered `DecisionModel` raises `DecisionModelNotFoundError` at activation time, never silently at first evaluation (§12's own activation gate). `DecisionStrategy` (ABC)/`ThresholdDecisionStrategy` (§14) is the default, concrete, rule/threshold-driven strategy — self-registered into `REGISTRY` at import time exactly as `analytics.trend.LinearTrendModel` self-registers one layer down; its `check_thresholds()` method performs real threshold-breach evaluation, including dotted-path field resolution against `AnalyticsResult` evidence (§13).
- **Phase 07.3 — Decision Intelligence Analysis Layer** is implemented: the analytical capabilities operating on already-produced `Recommendation`/`DecisionResult` objects. `DecisionScorer`/`ConfidenceScorer` (§23, §24) compute the numeric weight backing ranking and the trust weight backing how strongly a recommendation should be acted on — the latter deriving from `analytics.DataQualityScore` when present in a `DecisionContext`'s evidence, never recomputing data quality itself; both reuse one shared `_rule_strength`/`_SEVERITY_WEIGHTS` foundation so ranking and prioritization never silently disagree on what "critical" numerically means. `RankingStrategy` (ABC)/`WeightedScoreRanking` (§16) order `Recommendation`s by `DecisionScore.value`, descending (stable-sort tie-break), self-registered into `REGISTRY`; its own `rank()` method is the primary, richly-tested batch-ranking capability, with `_decide()` a thin ABC-satisfying adapter returning the top-ranked item. `ExplanationBuilder`/`ExplanationStage` (§17) walk a `Recommendation`'s provenance into a structured, evidence-linked `Explanation`; `ExplanationStage` is a non-terminal pipeline stage (see its own module docstring for a disclosed spec-text inconsistency this resolves). `ActionPrioritizer` (§20) assigns each `RankedRecommendation` an `ActionPriority` (urgency from severity, impact from `DecisionScore.value`, effort from an optional caller-supplied estimate) — a distinct question from ranking. `RootCauseAnalyzer` (§18) is an interface-only ABC with zero concrete subclasses by design (ADR-0007), mirroring `analytics.ForecastingModel`'s own interface-only shape. `DecisionContext` gained a third field this phase, `recommendations` (alongside `triggered_rules` from 07.2), for the same "batch operation over a context-only method signature" reason.
- **Phase 07.4 — Decision Operational Services** is implemented, completing the package: `WhatIfEngine` (§19) is an interface-only ABC with zero concrete subclasses by design, the decision-layer counterpart to `RootCauseAnalyzer` — it deliberately reuses `events.AsOf`'s already-reserved `scenario` field rather than inventing a second scenario concept, so a future Digital Twin plugin implements `_simulate` against a hook that already exists. `ActionPlanner` (§21) sequences prioritized actions into an `ActionPlan`, respecting caller-supplied dependencies via its own narrow, self-contained topological ordering (a priority-queue-based Kahn's algorithm, `O((V+E) log V)`) rather than reusing `kpis.DependencyGraph`, which is tightly coupled to `Registry[str, type[BaseKPI]]`/`KPIMetadata.dependencies` — a shape that does not fit arbitrary action-to-action dependencies (§33's own anti-pattern entry); it fails loudly (`Result.err`) on both a cyclic dependency and a duplicate `policy_code` among the actions being planned (the latter caught by this phase's own QA review — silently keeping only one same-keyed action would silently drop the other from the plan). `AlertGenerator` (§22) produces an `Alert` from a `ThresholdBreach` or a high-severity `Recommendation` — a pure value-object factory with no channel-delivery side effects; since neither a `ThresholdBreach` nor a `Recommendation` carries a severity-for-a-breach or a scope value directly, `AlertGenerator` reuses `ThresholdDecisionStrategy`'s own precedent of a caller/policy-configured severity (`breach_severity`, rather than inventing a magnitude-to-severity heuristic) and an optional `scope` keyword mirroring `ActionPlanner.plan`'s own `dependencies` default-mapping convention. `RealTimeDecisionSession`/`BatchDecisionRunner` (§25, §26) are the two execution modes — the live, event-driven counterpart and the bounded, scheduled-report counterpart of running one `DecisionPipeline` — both composing `kpis.KPIEngine`/`analytics.BatchAnalyticsRunner` rather than recomputing anything themselves (§3.2), mirroring `analytics.StreamingAnalyticsSession`/`BatchAnalyticsRunner` one layer down; both accept an optional `audit_trail` beyond what §25/§26's own bare pseudocode constructors show, the smallest compatible way to honor §33's "never bypass `DecisionAuditTrail`" anti-pattern without breaking the spec's literal signature. `RealTimeDecisionSession` guards its per-scope `latest()` result against an out-of-order-delivery race (caught by this phase's own QA review: a handler's refresh work runs outside its lock, so two concurrent deliveries for the same scope could otherwise let an older envelope's slower handler overwrite a newer one's already-stored result) by keying its stored state on the envelope's own canonical `event_time_utc` rather than last-writer-wins. `DecisionAuditTrail`/`DecisionAuditEntry` (§27, §28) are the append-only accountability record every operationally-actionable `DecisionPipeline` run should feed — `record()` serializes concurrent appends via one lock, `query()` reads a snapshot and filters outside it, and every entry serializes via `core.serialization` with no bespoke handling, exactly like every other value object in this package. `recommendation.py` exists as the §6 module holding recommendation-generation logic with, per §6's own entry for it, no public classes, functions, or API of its own (the `Recommendation` *type* lives in `result.py`; `ThresholdDecisionStrategy`'s methods delegate construction to it, keeping exactly one summary-text/traceability format package-wide) — originally folded into `strategy.py` in Phase 07.2 and extracted into its own file during this phase's completion pass, so the package structure matches §6's twenty-two-module list exactly. **This completes every module design spec §6 enumerates — `decision` is now feature-complete per the Reference Implementation Blueprint, including the checklist's examples (`examples/decision/`, four scripts) and recorded benchmarks (`benchmark/reports/decision/`).**

## Contents

- `__init__.py` — public API surface (49 symbols, the full design spec §7 list).
- `abstractions.py` — `DecisionModel` (ABC), `DecisionContext`.
- `metadata.py` — `DecisionMetadata`, `DecisionCategory`.
- `result.py` — `DecisionResult` and every concrete result/value type implemented in Phase 07.1.
- `thresholds.py` — `Threshold` (included ahead of schedule; see its own module docstring).
- `pipeline.py` — `DecisionPipeline`, `PipelineStage` (ABC), `ModelStage`.
- `rules.py` — `Rule`, `RuleEngine`, `RuleEngineStage`.
- `policy.py` — `DecisionStatus`, `Policy`.
- `strategy.py` — `DecisionStrategy` (ABC), `ThresholdDecisionStrategy`.
- `recommendation.py` — recommendation-generation logic (no public API of its own, per design spec §6; `ThresholdDecisionStrategy` delegates here).
- `scoring.py` — `DecisionScorer`, `ConfidenceScorer`.
- `ranking.py` — `RankingStrategy` (ABC), `WeightedScoreRanking`.
- `explanation.py` — `ExplanationBuilder`, `ExplanationStage`.
- `prioritization.py` — `ActionPrioritizer`.
- `root_cause.py` — `RootCauseAnalyzer` (ABC, interface only — zero concrete subclasses).
- `what_if.py` — `WhatIfEngine` (ABC, interface only — zero concrete subclasses).
- `planning.py` — `ActionPlanner`.
- `alerting.py` — `AlertGenerator`.
- `realtime.py` — `RealTimeDecisionSession`.
- `batch.py` — `BatchDecisionRunner`.
- `audit.py` — `DecisionAuditTrail`, `DecisionAuditEntry`.
- `_registry.py` — `REGISTRY`, `register`.
- `exceptions.py` — the package's exception hierarchy.
- `README.md` — this file.

## Dependencies

**Depends on:** `core`, `events`, `registry`, `kpis`, `analytics` (currently exercised); `ontology`, `plugins`, `connectors` are permitted under the platform-wide layering rule but not yet exercised — `connectors` for the same reason as `analytics` (decision operates on already-computed `KPIResult`/`AnalyticsResult` objects, never a vendor-specific wire format), `ontology`/`plugins` because no concrete strategy needing entity-type scoping or explicit plugin-lifecycle wiring exists yet.

**Depended on by:** `digital_twin`, `simulation`, `optimization`, `visualization`, `agents`, `cli`

## Future Work

`decision` is feature-complete per the Reference Implementation Blueprint's design spec §6 module list. Future work is limited to: a concrete `RootCauseAnalyzer`/`WhatIfEngine` plugin (first-party or third-party, per §31.2 — deliberately never shipped inside this package itself, §33), new `Policy` authoring (a governed, no-code-change extension, §31.4), and whatever `digital_twin`/`simulation`/`optimization`/`agents`/`visualization` need from this package as those packages move from architecture-complete to implemented (§36).

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
