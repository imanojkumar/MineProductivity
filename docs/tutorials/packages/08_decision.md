# Package Tutorial 8 — Decision (Deep)

!!! abstract "Milestone 2 · Package Tutorials · Tutorial 8 of 13"
    Deep, full-surface tutorial for `mineproductivity.decision` — turning a measured
    drift into an **explained, audited recommendation** driven by a versioned
    policy. Authored to **Package Tutorial Template v1.0** under the
    [Package Tutorial Implementation Standard](../../learning/PACKAGE_TUTORIAL_IMPLEMENTATION_STANDARD.md).

## Objective

Master the working surface of `mineproductivity.decision`: the `DecisionModel`
contract and `DecisionContext`, the versioned `Policy` with `Rule`s and
`Threshold`s, the composed `DecisionPipeline` and its stages, ranking and action
planning, the `DecisionAuditTrail`, real-time sessions, and — the payoffs — a
**plugin `DecisionStrategy`** and the interface-only `RootCauseAnalyzer`/`WhatIfEngine`.

All 49 public symbols (`mineproductivity.decision.__all__`) are accounted for under
the **coverage convention** (§5): **22 [deep]** / **27 [ref]**. Public APIs only.

## Prerequisites

- Package Tutorials [1 — Core](01_core.md), [6 — KPIs](06_kpis.md),
  [7 — Analytics](07_analytics.md): decision consumes KPI and analytics evidence (§3).
- [Fundamentals L08 — Decision](../fundamentals/08_decision.md): the intro —
  versioned policies, rules vs thresholds, the refusal to guess root cause.

This tutorial **builds on** L08.

## Running the examples

Every code block below is executed and its output pasted verbatim. Four scripts
(the analytics extra provides the KPI/analytics evidence engines):

```bash
pip install -e ".[analytics]"
python examples/decision/01_pipeline_over_evidence.py   # ...and 02, 03, 04
```

---

## 1. Why this package exists

Analytics tells you the fleet is drifting; something has to decide **what to do,
say why, and be defensible six months later in an incident review.** That is
`decision`. It consumes governed evidence (a `KPIResult`, a `TrendResult`), applies
a **versioned `Policy`**, and emits a `Recommendation` carrying its triggered rules,
the evidence, and an `Explanation` — then records the whole run in an append-only
`DecisionAuditTrail`.

Its disciplines: a decision is driven by a **governed object, not an `if` in a cron
script**; an unexplained recommendation is worthless, so explanation is a
first-class pipeline stage; and the platform **refuses to guess *why*** — root-cause
and what-if analysis ship as interface-only contracts (ADR-0007), because a
fabricated cause is worse than none.

## 2. Architectural role

`decision` sits above `analytics`, below the actioning layers:

```
… kpis ─► analytics ─► decision ─► digital_twin ─► … ─► visualization
```

It reads the *characterisations* analytics produced and the *measurements* kpis
governed, and turns them into ranked, audited, explained action — re-deriving
neither.

## 3. Integration with adjacent layers

**`kpis` (T6) & `analytics` (T7) — the evidence:** a `DecisionContext` bundles
`KPIResult`s and analytics results (a `TrendResult`); a `Rule` is a predicate *over
that evidence*, and a `Threshold` confirms a breach's magnitude. Decision **consumes**
governed evidence and re-derives nothing.

**`events` (T3):** a `RealTimeDecisionSession` subscribes to the `EventBus`,
re-deciding a scope as events land, and the audit trail traces each run back to its
source event id.

**`registry` (T4):** `REGISTRY` is a `registry.Registry` of decision models;
`@register` adds one, and a strategy pack is discovered by entry point (§13).

**`core` (T1):** a `Rule` *is* a `core.PredicateSpecification`; results are
`core.BaseValueObject`s; `decide()` and the runners return governed results.

**Upward:** the actioning/UX layers consume `Recommendation`/`Alert` — this package
produces the explained, ranked call to act.

## 4. Package structure

| Group | Module(s) | Public symbols |
|---|---|---|
| The model contract | `abstractions` | `DecisionModel`, `DecisionContext` |
| Metadata & registry | `metadata`, `_registry` | `DecisionMetadata`, `DecisionCategory`, `REGISTRY`, `register` |
| Policy & rules | `policy`, `rules`, `thresholds` | `Policy`, `DecisionStatus`, `Rule`, `RuleEngine`, `RuleEngineStage`, `Threshold`, `ThresholdBreach` |
| Strategy | `strategy` | `DecisionStrategy`, `ThresholdDecisionStrategy` |
| Pipeline | `pipeline`, `explanation` | `DecisionPipeline`, `PipelineStage`, `ModelStage`, `ExplanationStage`, `ExplanationBuilder`, `Explanation` |
| Results | `result` | `DecisionResult`, `Recommendation`, `RankedRecommendation`, `ActionPlan`, `RootCauseResult`, `WhatIfResult` |
| Ranking & scoring | `ranking`, `scoring` | `RankingStrategy`, `WeightedScoreRanking`, `DecisionScore`, `DecisionScorer`, `ConfidenceScore`, `ConfidenceScorer` |
| Action | `prioritization`, `planning`, `alerting` | `ActionPrioritizer`, `ActionPriority`, `ActionPlanner`, `Alert`, `AlertGenerator` |
| Runners | `batch`, `realtime` | `BatchDecisionRunner`, `RealTimeDecisionSession` |
| Audit | `audit` | `DecisionAuditTrail`, `DecisionAuditEntry` |
| Interface-only (ADR-0007) | `root_cause`, `what_if` | `RootCauseAnalyzer`, `WhatIfEngine` |
| Exceptions | `exceptions` | `DecisionModelNotFoundError`, `DecisionValidationError`, `DecisionVersionConflictError`, `NoApplicablePolicyError`, `PolicyConflictError` |

## 5. Public APIs

All 49 exports under the **coverage convention**:

**The spine — [deep]**
: `DecisionModel`, `DecisionContext`, `DecisionMetadata`, `DecisionCategory`,
  `DecisionResult`, `Policy`, `Rule`, `RuleEngineStage`, `Threshold`,
  `ThresholdBreach`, `DecisionStrategy`, `DecisionPipeline`, `ModelStage`,
  `ExplanationStage`, `Explanation`, `Recommendation`, `RankedRecommendation`,
  `RankingStrategy`, `WeightedScoreRanking`, `DecisionAuditTrail`, `RootCauseAnalyzer`,
  `WhatIfEngine`

**Everything else — [ref]** — see the table.

### Reference coverage

| Group | Symbols (`[ref]`) | What / when |
|---|---|---|
| Policy & rules | `DecisionStatus`, `RuleEngine`, `ThresholdDecisionStrategy` | The policy lifecycle status; the rule-evaluation engine; the built-in threshold strategy. |
| Pipeline & explanation | `PipelineStage`, `ExplanationBuilder` | The stage base class; the builder that assembles an `Explanation`'s premises. |
| Results | `RootCauseResult`, `WhatIfResult`, `REGISTRY`, `register` | Result types for the interface-only engines; the decision-model registry + decorator. |
| Scoring | `DecisionScore`, `DecisionScorer`, `ConfidenceScore`, `ConfidenceScorer` | Severity/confidence scoring behind a ranked recommendation. |
| Action | `ActionPrioritizer`, `ActionPriority`, `ActionPlan`, `ActionPlanner`, `Alert`, `AlertGenerator` | Urgency/impact/effort prioritization; dependency-ordered action plans; alert generation. |
| Runners & audit | `BatchDecisionRunner`, `RealTimeDecisionSession`, `DecisionAuditEntry` | Batch and live-session orchestration; one append-only audit record. |
| Exceptions | `DecisionModelNotFoundError`, `DecisionValidationError`, `DecisionVersionConflictError`, `NoApplicablePolicyError`, `PolicyConflictError` | Unknown model, invalid metadata, duplicate code, no matching policy, conflicting policies. All derive from `core.MineProductivityError`. |

## 6. Conceptual model

Five ideas explain the package.

**A. A decision model is metadata + one pure function.** `DecisionModel` declares
`meta: DecisionMetadata` and implements `_decide(context) -> DecisionResult` — the
same as-object shape as `kpis.BaseKPI` and `analytics.AnalyticsModel`.

**B. A `Policy` is governed, not an `if`.** It is versioned (`v1.0.0`), names its
`Rule`s (each a `core.PredicateSpecification` over the evidence) and `Threshold`s,
and a change of meaning is a version bump under review.

**C. Rules and thresholds do different jobs.** A `Rule` answers a boolean (*did it
fire?*); a `Threshold` answers a magnitude (*by how much?* → a `ThresholdBreach`).
You need both: one triggers the workflow, the other sizes the problem.

**D. Explanation is a pipeline stage, not an afterthought.** `DecisionPipeline`
composes `RuleEngineStage` → `ModelStage` → `ExplanationStage` → ranking; the
`ExplanationStage` attaches premises so a recommendation can be argued with — which
is what makes it trustworthy.

**E. The platform refuses to guess *why*.** `RootCauseAnalyzer` and `WhatIfEngine`
ship **zero** implementations (ADR-0007). The platform will tell you the fleet is
under target and declining; it will not invent a causal claim. Encode your site's
causal model in a plugin — the contract is waiting.

## 7. Real mining examples

The walkthroughs decide over real evidence: a low-fleet-availability policy over
`UTIL.OEE` and its trend, ranking and planning three competing recommendations, a
live throughput session over the event bus, and a site-pack strategy plugin.

## 8. Step-by-step walkthroughs

### 8.1 An audited pipeline over governed evidence

A `DecisionContext` carries `UTIL.OEE` (from the real `KPIEngine`) and its trend
(from the real analytics runner). A versioned `Policy`'s `Rule`s evaluate the
evidence; `Threshold`s confirm the magnitude; the `DecisionPipeline` composes
rule-evaluation, recommendation, explanation, and ranking; and the
`DecisionAuditTrail` records the run. Running
[`01_pipeline_over_evidence.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/decision/01_pipeline_over_evidence.py):

```text
--- 1. Evidence: UTIL.OEE for the shift, from the real KPIEngine ---
UTIL.OEE = 0.8305 (n=4)

--- 2. Evidence: its week-long trend, from the real BatchAnalyticsRunner ---
TREND.Linear: direction='decreasing' slope=-1.579e-07

--- 3. A versioned, governed fleet-availability Policy ---
policy='AVAIL.LowFleetAvailability' v1.0.0 rules=['oee_below_target', 'oee_trend_declining']

--- 4. Rule-evaluate + recommend, via one audited DecisionPipeline run ---
triggered: ('oee_below_target', 'oee_trend_declining')
summary:   Policy 'AVAIL.LowFleetAvailability' triggered by rule(s): oee_below_target, oee_trend_declining
evidence:  ('UTIL.OEE', 'TREND.Linear')

--- 5. The declarative Thresholds independently confirm the breaches ---
value < 0.85 (observed 0.8305)
trend.slope < 0.0 (observed -0.0000)

--- 6. Explain + rank, composed as pipeline stages ---
rank=1 score=0.755
components: {'severity': 0.75, 'policy_weight': 0.4, 'confidence': 1.0}
premise: Rule 'oee_below_target' triggered under policy 'AVAIL.LowFleetAvailability'
premise: Rule 'oee_trend_declining' triggered under policy 'AVAIL.LowFleetAvailability'
premise: UTIL.OEE = 0.8305
premise: TREND.Linear observed

--- 7. The audit trail recorded the operationally-actionable run ---
1 entry, recorded_at=2026-07-19T12:07:39+00:00
```

The `Recommendation` is not a bare alert: it names the rules, the evidence, the
threshold magnitudes, and a ranked `score` with its components — everything an
incident review needs.

### 8.2 Ranking, prioritization, and dependency-ordered planning

Given several `Recommendation`s, a `RankingStrategy` (`WeightedScoreRanking`) orders
them by score; an `ActionPrioritizer` weighs urgency/impact/effort under capacity;
and an `ActionPlanner` produces a dependency-respecting execution order — failing
loudly on a cycle. Running
[`02_action_planning.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/decision/02_action_planning.py):

```text
--- 2. Ranking: which recommendation is best (spec 07 sec. 16) ---
rank 1: MAINT.OverdueService (score 0.840)
rank 2: AVAIL.LowFleetAvailability (score 0.755)
rank 3: PROD.QueueBuildUp (score 0.590)

--- 3. Prioritization: urgency/impact/effort under capacity (spec 07 sec. 20) ---
MAINT.OverdueService: urgency=1.0 impact=0.840 effort=4.0 -> priority_score=0.210
AVAIL.LowFleetAvailability: urgency=0.75 impact=0.755 effort=2.0 -> priority_score=0.283
PROD.QueueBuildUp: urgency=0.5 impact=0.590 effort=0.5 -> priority_score=0.590

--- 4. Planning: dependency-respecting execution order (spec 07 sec. 21) ---
1. MAINT.OverdueService: Schedule overdue haul-truck service
2. PROD.QueueBuildUp: Rebalance truck assignments at the north crusher
3. AVAIL.LowFleetAvailability: Investigate declining fleet availability

--- 5. A cyclic dependency fails loudly, never silently re-ordered ---
is_err: True -> ActionPlanner.plan detected a cyclic action dependency
```

Note ranking and prioritization disagree: the highest-*scoring* item is not the
best-*priority* one once effort and capacity are weighed — which is exactly why both
exist.

### 8.3 Real-time decisions over the event bus

A `RealTimeDecisionSession` subscribes to the `EventBus`; each event refreshes and
re-decides its scope, `latest()` serves a scope's result without re-running, and
**real-time and batch produce the identical decision** from the same context — every
actionable run audited and traceable to its source event. Running
[`03_realtime_session.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/decision/03_realtime_session.py):

```text
--- 4. latest() serves each scope's result without re-running the pipeline ---
HT-214: no action (no rule triggered, tph at/above target)
HT-215: RECOMMEND -> Policy 'PROD.LowTruckThroughput' triggered by rule(s): tph_below_target

--- 5. Real-time/batch parity: the same context, decided the same way ---
batch:     ('tph_below_target',) "Policy 'PROD.LowTruckThroughput' triggered by rule(s): tph_below_target"
real-time: ('tph_below_target',) "Policy 'PROD.LowTruckThroughput' triggered by rule(s): tph_below_target"

--- 7. Cancelled: later events no longer update the session ---
HT-216 after cancel: None
```

## 9. Repository example reuse

The four `decision` scripts were each executed (exit `0`), output above.

| Script | Public API it exercises | Walkthrough |
|---|---|---|
| [`01_pipeline_over_evidence.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/decision/01_pipeline_over_evidence.py) | `Policy`, `Rule`, `Threshold`, `ThresholdBreach`, `DecisionPipeline`, `RuleEngineStage`, `ModelStage`, `ExplanationStage`, `Recommendation`, `Explanation`, `DecisionAuditTrail` | §8.1 |
| [`02_action_planning.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/decision/02_action_planning.py) | `RankingStrategy`, `WeightedScoreRanking`, `RankedRecommendation`, `ActionPrioritizer`, `ActionPlanner`, `ActionPlan`, `ActionPriority` | §8.2 |
| [`03_realtime_session.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/decision/03_realtime_session.py) | `RealTimeDecisionSession`, `BatchDecisionRunner`, `DecisionAuditEntry` | §8.3 |
| [`04_plugin_strategy.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/decision/04_plugin_strategy.py) | `DecisionStrategy`, `DecisionModel`, `DecisionCategory`, `REGISTRY`, `register` | §13 |

## 10. Common mistakes

| Mistake | What happens | Do this instead |
|---|---|---|
| Business rules as inline `if`s | No version, no audit, no explanation | A governed `Policy` |
| Re-deriving the KPI inside a rule | A second definition of the metric | Read `context` evidence (`KPIResult`/`TrendResult`) |
| Rules without thresholds | "It breached" — but nobody knows by how much | Attach a `Threshold` (→ `ThresholdBreach`) |
| Skipping the `ExplanationStage` | Alert fatigue; the recommendation is ignored | Always explain — premises make it arguable |
| Expecting a built-in root-cause engine | `RootCauseAnalyzer` has zero implementations | Write a site-specific plugin (ADR-0007) |
| Not auditing an actionable run | Unreconstructable six months later | `DecisionAuditTrail` |
| Silently reordering a cyclic action plan | Masks a real dependency contradiction | `ActionPlanner` fails loudly on a cycle |

## 11. Best practices

- **Version your policies** — the target *will* change; know what was in force when.
- **Name rules for what they mean** (`oee_below_target`) — the name lands in the audit trail.
- **Always attach thresholds** — magnitude drives triage.
- **Always run the `ExplanationStage`** — an unexplained recommendation is ignored.
- **Consume evidence; never re-derive it.**
- **Audit every operationally-actionable run.**

## 12. Performance considerations

- **The pipeline is a composed sequence of stages** — each stage is O(rules) or
  O(recommendations); nothing rescans the event store (evidence is passed in).
- **`RealTimeDecisionSession.latest()` serves a cached result** per scope — a read,
  not a re-run of the pipeline.
- **Real-time/batch parity** means one code path decides both, so there is one thing
  to optimise and trust.
- **Ranking/prioritization are O(n log n)/O(n)** in the number of recommendations.

## 13. Extension points — a `DecisionStrategy` plugin (and the two refusals)

`decision`'s extension point is a **custom `DecisionStrategy`**: subclass it (a
`DecisionModel`), declare `DecisionMetadata`, implement `_decide(context)`, and
register — most often shipped as a plugin discovered by entry point. The reused
[`04_plugin_strategy.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/decision/04_plugin_strategy.py)
discovers a site-pack strategy through the exact `EntryPointDiscovery` path a
pip-installed plugin uses:

```text
--- 1. The built-in strategies are already registered ---
before discovery: ['RANKING.WeightedScore', 'STRATEGY.Threshold']

--- 2. A site pack declares its strategy via a pyproject.toml entry-point ---
discover() -> is_ok: True, loaded entry-points: ('sitepack',)
registered after discovery: ['RANKING.WeightedScore', 'STRATEGY.SitePackEscalation', 'STRATEGY.Threshold']

--- 3. The discovered strategy is a first-class DecisionModel ---
class=SitePackEscalationStrategy category=DecisionCategory.STRATEGY

--- 4. ...and runs through the same decide() orchestration as any built-in ---
model_code='STRATEGY.SitePackEscalation' warnings=('site-pack demo strategy: escalate to supervisor',)
```

**The two interface-only refusals (ADR-0007).** `RootCauseAnalyzer` (produces a
`RootCauseResult`) and `WhatIfEngine` (produces a `WhatIfResult`) are contracts with
**zero** implementations. The platform will tell you FL-NORTH is under target and
declining; it will **not** tell you *why* (deepening pit? failing swing motor? wet
roads?) or *what if* you add three trucks — because those answers depend on your
site's causal model, and **a fabricated cause is worse than none**. You implement
these as plugins exactly like a `DecisionStrategy`; the contract is waiting.

!!! note "One extension idiom, three surfaces"
    `DecisionStrategy`, `RootCauseAnalyzer`, and `WhatIfEngine` are all
    `DecisionModel`s — "declare metadata, implement `_decide`, register." The first
    has built-ins to compose with; the other two ship nothing on purpose.

## 14. Exercises

1. **Change the target.** Lower a policy's threshold and re-run; which rules fire now,
   and why must the threshold be versioned *with* the policy?
2. **Add a third rule.** Fire only when `r_squared > 0.9` — escalate a *convincing*
   decline, not a noisy one. Why is this a better alerting policy than direction alone?
3. **Rank vs prioritize.** Build three recommendations where the top-ranked is not the
   top-priority; explain what effort/capacity changed the order.
4. **Read the audit.** Print a full `DecisionAuditEntry` including `recorded_at`. What
   can an incident review reconstruct — and what can it not?
5. **Sketch the refusal.** Outline a `RootCauseAnalyzer` for your site. What data would
   it need that this framework does not have? Does that change your view of ADR-0007?

## 15. Reference solutions

??? success "Solution 1 — Change the target"
    Lowering the `Threshold.limit` narrows what counts as a breach, so a shift that
    triggered before may now pass. The limit is stored *on the policy*, so an auditor
    can ask "which limit was in force in June?" — a bare `if tph < X` has no answer.

??? success "Solution 2 — Add a third rule"
    ```python
    "oee_decline_convincing": PredicateSpecification(
        lambda ctx: any(isinstance(r, TrendResult) and r.r_squared > 0.9
                        for r in ctx.analytics_results)
    )
    ```
    Direction alone fires on noise; gating on `r_squared > 0.9` escalates only a decline
    a straight line explains well — far fewer false alarms by shift three.

??? success "Solution 3 — Rank vs prioritize"
    `WeightedScoreRanking` orders by severity×confidence; `ActionPrioritizer` divides
    impact by effort under capacity. A high-severity item needing 4 units of effort can
    fall below a medium item costing 0.5 — ranking says "worst", prioritization says
    "do first".

??? success "Solution 4 — Read the audit"
    A `DecisionAuditEntry` reconstructs which policy *version* fired, on what evidence,
    with what thresholds, and when (`recorded_at`) — and (real-time) the source event
    id. It cannot tell you the *cause*; that is the ADR-0007 refusal.

??? success "Solution 5 — Sketch the refusal"
    A real `RootCauseAnalyzer` needs site-specific causal data the framework does not
    hold (haul-distance growth, component health, weather). Implement `_decide` to
    return a `RootCauseResult` from *your* model — and register it as a plugin. The
    refusal is precisely what keeps the framework from inventing a cause it cannot know.

## 16. Further reading

- **[`decision` package guide](../../packages/decision.md)** — the capability-tour view.
- **[`decision` API reference](../../api-reference/decision.md)** — every symbol, from source.
- **[Decision Intelligence Design Specification](../../architecture/07_Decision_Intelligence_Design_Specification.md)** · **[ADR-0007](../../adr/ADR-0007-Decision-Intelligence.md)** — the pipeline stages, ranking/prioritization, the root-cause/what-if refusal.
- **[Fundamentals L08 — Decision](../fundamentals/08_decision.md)** · Package Tutorials [6 — KPIs](06_kpis.md) · [7 — Analytics](07_analytics.md).

---

**Next package tutorial:** Digital Twin (deep) — live state that is always a
projection of the event log.
*(Not yet written — Tutorial 9 of 13.)*
