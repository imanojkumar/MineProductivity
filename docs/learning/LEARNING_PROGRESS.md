# Learning Suite - Progress Tracker

> **Live execution state.** The stable plan is
> [`LEARNING_ROADMAP.md`](LEARNING_ROADMAP.md) (locked); this file is the
> authoritative record of *what is actually done*, verified against the
> repository. Update it at the end of every session.

**Last updated:** 2026-07-13
**Active milestone:** 1 - Fundamentals
**Overall:** Milestone 1 **RELEASE CANDIDATE (RC1)** - certified, corrected, and release-prepared · Milestones 2-6 not started

### Release Candidate (RC1) — release-preparation phase (docs only)

Five consolidated RC tasks executed; no lesson/tutorial/production change.

| Task | Scope | Files |
|---|---|---|
| **RC-01** Discoverability | Surface the Suite from every entry point | `README.md`, `docs/index.md`, `docs/getting-started/next-steps.md`, `examples/README.md` |
| **RC-02** Doc consistency | Align the `18.33` → `733.33` first-number contradiction | `README.md`, `docs/getting-started/installation.md`, `docs/getting-started/quick-start.md` |
| **RC-03** Internal docs | Exclude the engineering tracker from the published site | `mkdocs.yml` (`exclude_docs: learning/LEARNING_PROGRESS.md`) |
| **RC-04** Roadmap cross-ref | Link project `ROADMAP.md` ↔ Learning Suite | `ROADMAP.md` |
| **RC-05** Release comms | Changelog entry + release notes + nav | `CHANGELOG.md`, `docs/releases/LEARNING_SUITE_v1.0.md`, `mkdocs.yml` |

**RC validation:** `mkdocs build --strict` 0 warnings · `check_docs.py` 0 broken /
0 failed (README snippets re-executed, now emit 733.33) · funnel verified from
README/PyPI, docs home, Getting Started, Next Steps, examples index, and ROADMAP.
Lessons/tutorials/`src/` untouched. `LEARNING_ROADMAP.md` remains LOCKED.


Legend: ☑ done & validated (LOCKED) · ◐ in progress · ☐ not started

---

## Milestone 1 - Fundamentals

### Lessons (`examples/fundamentals/`)

| # | Lesson | Script | ruff | format | mypy --strict | executes | Status |
|---|---|---|:--:|:--:|:--:|:--:|---|
| 01 | Hello MineProductivity | `01_hello_mineproductivity/hello.py` | ☑ | ☑ | ☑ | ☑ | ☑ **LOCKED** |
| 02 | Entities | `02_entities/entities.py` | ☑ | ☑ | ☑ | ☑ | ☑ **LOCKED** |
| 03 | Value objects | `03_value_objects/value_objects.py` | ☑ | ☑ | ☑ | ☑ | ☑ **LOCKED** |
| 04 | Events | `04_events/events.py` | ☑ | ☑ | ☑ | ☑ | ☑ **LOCKED** |
| 05 | Ontology | `05_ontology/ontology.py` | ☑ | ☑ | ☑ | ☑ | ☑ **LOCKED** |
| 06 | KPIs | `06_kpis/kpis.py` | ☑ | ☑ | ☑ | ☑ | ☑ **LOCKED** |
| 07 | Analytics | `07_analytics/analytics.py` | ☑ | ☑ | ☑ | ☑ | ☑ **LOCKED** |
| 08 | Decision | `08_decision/decision.py` | ☑ | ☑ | ☑ | ☑ | ☑ **LOCKED** |
| 09 | Digital Twin | `09_digital_twin/digital_twin.py` | ☑ | ☑ | ☑ | ☑ | ☑ **LOCKED** |
| 10 | Visualization | `10_visualization/visualization.py` | ☑ | ☑ | ☑ | ☑ | ☑ **LOCKED** |

**10 / 10 lessons complete.** All LOCKED.

### Tutorials (`docs/tutorials/fundamentals/`)

| # | Tutorial | Status |
|---|---|---|
| 01 | `01_hello.md` | ☑ **LOCKED** |
| 02 | `02_entities.md` | ☑ **LOCKED** |
| 03 | `03_value_objects.md` | ☑ **LOCKED** |
| 04 | `04_events.md` | ☑ **LOCKED** |
| 05 | `05_ontology.md` | ☑ **LOCKED** |
| 06 | `06_kpis.md` | ☑ **LOCKED** |
| 07 | `07_analytics.md` | ☑ **LOCKED** |
| 08 | `08_decision.md` | ☑ **LOCKED** |
| 09 | `09_digital_twin.md` | ☑ **LOCKED** |
| 10 | `10_visualization.md` | ☑ **LOCKED** |

**10 / 10 tutorials complete.** All LOCKED.

### Milestone-level validation

| Task | Status |
|---|---|
| Navigation updated (`mkdocs.yml` + tutorial hub) | ☑ **DONE** |
| `mkdocs build --strict` (0 warnings) | ☑ **PASS** - 0 warnings |
| `check_docs.py` (0 broken links, 0 failed snippets) | ☑ **PASS** - 0 broken, 0 failed |
| Full `pytest` suite green (no regression) | ☑ **PASS** - 2,986 passed |
| `src/` unmodified | ☑ verified - production untouched |
| Examples verified (all execute, exit 0) | ☑ **10 / 10** |

---

## Verified API notes (carry forward)

Recorded so future sessions do not re-derive or re-guess. Each was read from the
implementation or an existing example, not recalled.

| Concept | Verified signature / fact | Source |
|---|---|---|
| `BaseEntity` subclass | must declare `@dataclass(frozen=True, slots=True, eq=False)` - `eq=False` is mandatory or dataclasses replaces identity equality | `examples/core/01_entity_and_value_object.py` |
| `Mine` | `Mine(id=, commodity_codes=("copper",), method="open_pit")` - **not** `commodity_code`/`country` | `examples/ontology/02_structural_modelling.py` |
| `Pit` / `Bench` | `Pit(id=, mine_id=, commodity=)` · `Bench(id=, pit_id=, elevation_m=)` | same |
| `Relationship` | `Relationship(source_id=, kind=RelationshipKind.BELONGS_TO, target_id=)` - **`BELONGS_TO`**, not `PART_OF` | same |
| `Shift` | `Shift(id=, mine_id=, pattern=, start_utc=, end_utc=, scheduled_h=)`; has `.contains(dt)` | same |
| KPI direct compute | `REGISTRY.get("PROD.TPH")().compute([{"payload_t": .., "operating_h": ..}])` → `KPIResult(value, unit, code, n, warnings)` | `README.md`, lesson 01 |
| `KPIEngine` wiring | `KPIEngine(store=, registry=REGISTRY, backend=PandasBackend(), cache=ResultCache(), shifts={id: Shift})`; `engine.execute(code, window="shift", scope={"shift": id})` → `Result` (`.is_ok`, `.unwrap()`) | `examples/kpis/_dataset.py` |
| Composite `UTIL.OEE` | needs the **engine** (resolves dependencies); not computable via bare `.compute(rows)` | `examples/kpis/02_composite_oee.py` |
| Event append | `EventEnvelope(event_id=EventID.generate(), version=EventVersion(), payload=, event_time_utc=, processing_time_utc=, ingestion_time_utc=, metadata=EventMetadata(name=, source_system=))`; `store.append(env).is_ok` | `examples/events/01_first_event.py` |
| Twin subclass | override `_apply(self, events, *, context) -> TwinState`; `meta: ClassVar[TwinMetadata]`; `twin.with_state(state, status=TwinStatus.SYNCHRONIZED)` | `examples/digital_twin/01_provision_and_sync.py` |
| Interface-only ABCs | `analytics.ForecastingModel` / `AnomalyDetector` / `OutlierDetector`, `decision.RootCauseAnalyzer`/`WhatIfEngine`, `visualization.Visualization`/`Renderer` ship **zero** concrete subclasses by design (ADR-0006/0007/0012). Lessons must subclass them locally, never expect a built-in. | ADRs; `src/mineproductivity/analytics/forecasting.py` |
| KPI metadata | `REGISTRY.get(code).meta` → `.code`, `.official_name`, `.aggregation` (enum), `.business_purpose`, `.operational_question`, `.formula`, `.unit`, `.direction` (enum), `.required_events`, `.dependencies` | `examples/kpis/04_discovery.py` |
| Leaf vs composite | `issubclass(REGISTRY.get(code), CompositeKPI)`; only `UTIL.OEE` is composite in the 12-KPI Standard Library | same |
| `DependencyGraph` | `DependencyGraph(REGISTRY).topological_order("UTIL.OEE")` → `['UTIL.PA','UTIL.UA','UTIL.Performance','UTIL.OEE']`. Works **without** an engine. | `examples/kpis/02_composite_oee.py` |
| `KPIResult` | `KPIResult(code, value: float\|None, unit, *, n=0, warnings=(), scope={})` | introspection |
| `Aggregation` | exported from `mineproductivity.kpis`; members: `ADDITIVE`, `RATIO`, `AVERAGE`, `WEIGHTED_AVERAGE`, `ROLLING`, `CUMULATIVE`, `DERIVED` | introspection |
| `combine_results` | **not** a top-level export - `from mineproductivity.kpis.aggregation import combine_results`. Signature: `combine_results(results: Sequence[KPIResult], aggregation: Aggregation, *, code: str, unit: str) -> KPIResult` | introspection |
| **RATIO guardrail** | `combine_results(..., Aggregation.RATIO, ...)` **raises `KPIAggregationError`** ("ratio KPIs cannot be combined by averaging already-computed results - re-derive from the union of raw rows instead"). It does *not* compute a weighted mean. Correct path: re-`compute()` over the union of raw rows. Canonical numbers: 1,300 t/h (12 h) + 1,100 t/h (6 h) → naive 1,200 **wrong**, re-derived **1,233.3** correct. | `src/mineproductivity/kpis/aggregation.py:46`; lesson 06 |
| `KPIAggregationError` | `from mineproductivity.kpis.exceptions import KPIAggregationError` | same |
| `TimeSeriesPoint` / `TimeSeries` | `TimeSeriesPoint(timestamp: datetime, value: float, *, scope={})` · `TimeSeries(points: tuple[TimeSeriesPoint, ...])` (positional tuple, not list) | introspection |
| `describe` | `describe(series: TimeSeries) -> StatisticalSummary`; fields: `model_code`, `computed_at`, `warnings`, `n`, `mean`, `std`, `minimum`, `maximum`, `percentiles` (dict keyed by int, e.g. `percentiles[50]`) | introspection |
| `AnalyticsContext` | `AnalyticsContext(*, event_store: EventStore, kpi_engine=None, backend=None)` — **`event_store` is required**; use `_InMemoryEventStore()` in lessons | introspection |
| `LinearTrendModel` | `meta.code == "TREND.Linear"`; call `._analyze(series, context=AnalyticsContext(...)) -> TrendResult`. (`analyze()` is the public wrapper returning `AnalyticsResult`.) | introspection |
| `TrendResult` | fields: `model_code`, `computed_at`, `warnings`, `slope`, `intercept`, `r_squared`, `direction`, `window`. `direction` is `Literal['increasing','decreasing','flat']` — a **plain string, not an enum** (no `TrendDirection` export exists). | introspection |
| **Trend slope units** | `slope` is **per SECOND** — `trend.py:67` fits `x = (timestamp - origin).total_seconds()`. Raw slope prints as `-0.00` and looks like "no trend". Multiply by `12*3600` for t/h-per-12h-shift. Verified: -0.000288/s = **-12.4 t/h per shift**, r²=0.974 over a 1300→1150 t/h decline. | `src/mineproductivity/analytics/trend.py:66-67`; lesson 07 |
| `Policy` (decision) | `Policy(code=, rules={name: Rule}, thresholds={name: Threshold}, strategy_code="STRATEGY.Threshold")`; has `.version` | `examples/decision/01_pipeline_over_evidence.py` |
| `Rule` | a `core.PredicateSpecification(lambda ctx: ...)` over a `DecisionContext` | same |
| `Threshold` | `Threshold(field=, comparator="<", limit=)`; `strategy.check_thresholds(ctx)` → breaches with `.threshold`, `.observed_value` | same |
| `DecisionContext` | `DecisionContext(kpi_results=, analytics_results=, scope=, recommendations=)` | same |
| Decision pipeline | `DecisionPipeline(stages=(RuleEngineStage(policy=), ModelStage(ThresholdDecisionStrategy(policy=, severity="high"))))`; run via `BatchDecisionRunner(pipeline=, audit_trail=DecisionAuditTrail()).run(ctx)` → `Result` → `.unwrap()` → `Recommendation` (`.triggered_rules`, `.summary`, `.evidence`, `.explanation`) | same |
| Explain + rank | `DecisionPipeline(stages=(ExplanationStage(), ModelStage(WeightedScoreRanking())))` → `RankedRecommendation` (`.rank`, `.score.value`, `.score.components`, `.recommendation.explanation.premises`) | same |
| `DecisionAuditTrail` | `.query(scope={...})` → entries with `.recorded_at` | same |
| `TimeSeries.from_kpi_results` | `TimeSeries.from_kpi_results(results, timestamps=[...])` — convenient alternative to building points manually | same |
| Twin category bases | `MineTwin`, `EquipmentTwin`, `PlantTwin`, `ConveyorTwin`, `HaulageTwin`, `FleetTwin`, `ProcessingPlantTwin`, `GeologicalTwin`, `VentilationTwin`, `StockpileTwin`, `ProductionTwin` (11); `TwinCategory` has the matching members | introspection |
| `TwinState` / `TwinSnapshot` | `TwinState(attributes, captured_at, schema_version="1.0.0")` · `TwinSnapshot(twin_id, state, status, as_of)` | introspection |
| `TwinContext` | `TwinContext(*, event_store, kpi_results=(), analytics_results=(), decision_results=(), as_of=None)` | introspection |
| `TwinSynchronizer` | `.synchronize(twin_id, events: Sequence[BaseEvent], *, context) -> SyncResult` (`.previous_status`, `.new_status`, `.events_applied`) | introspection |
| **`AsOf.utc` is optional** | typed `datetime \| None` — needs a narrowing `assert` before `.isoformat()` under `mypy --strict` | lesson 09 |
| `PredicateSpecification` typing | when bound to a bare variable, `mypy --strict` needs the type param: `x: PredicateSpecification[EventEnvelope[Any]] = PredicateSpecification(...)` | lesson 09 |
| Visualization (lesson 10) | `Visualization` subclass: `meta = VisualizationMetadata(code="KPI_CARD.X", category=VisualizationCategory.KPI_CARD, description=)`, `_render(widget, *, context) -> PresentationModel`. `Renderer` subclass: `meta = RendererMetadata(code=, description=)`, `render(model, *, context) -> RenderedOutput`. `RenderingPipeline(registry=REGISTRY, renderers=RENDERERS).render(widget, context=, renderer_code=)`. `Widget(code=, visualization_code=, binding={})`. | `examples/visualization/01_single_widget_render.py`; lesson 10 |

### APIs still to verify (next sessions)

- ~~`analytics` (lesson 07)~~ — **verified & locked**; see the analytics rows in the table above.
- ~~`decision` (lesson 08)~~ — **verified & locked**; see the decision rows above.
- ~~`digital_twin` (lesson 09)~~ — **verified & locked**; see the twin rows above.
- ~~`visualization` (lesson 10)~~ — **verified & locked**; see the visualization row above.

---

## Checkpoint

**Session ended:** context limit reached after completing **all ten lessons**
(a major milestone boundary: the entire implementation half of Milestone 1).
No work is half-finished; everything below is validated.

### Completed this session

- **Lesson 08 - Decision** authored, validated, **LOCKED**.
- **Lesson 09 - Digital Twin** authored, validated, **LOCKED**.
- **Lesson 10 - Visualization** authored, validated, **LOCKED**.
- **ALL 10 LESSONS NOW COMPLETE AND LOCKED.**
- Full sweep: `ruff` clean, `ruff format --check` clean (10 files),
  `mypy --strict` clean (10 files), **10/10 execute exit 0**.
- `src/` confirmed unmodified - no production code touched, no defect found.
- Verified-API table extended with the decision + digital_twin surfaces.

### Certification correction phase (Class A only)

Three Class A findings from the Master Certification Report were corrected.
Class B/C were explicitly **not** implemented (recorded as future work).

| ID | Finding | Correction applied | Lessons |
|---|---|---|---|
| **A1** | `CAT 793F` paired with `rated_capacity=363.0` — 363 t is the **797F**'s payload; a 793F is ~226 t. Verified against `examples/ontology/01`, which correctly pairs 797F ↔ 363.0. | Standardised on **793F @ 226 t**. Chosen over 797F @ 363 t because every lesson already uses 220 t loads — a well-loaded 793F (**97.3%**) but a badly under-loaded 797F (60.6%). Overload example 400 → 245 t (a plausible ~8% overload, not an absurd 77%). | 03, 05 |
| **A2** | One truck moving 220 t across a full 12 h shift = **18.33 t/h** — arithmetically right, operationally a broken truck, and the **first number a learner sees**. | Replaced with a realistic shift: **40 cycles × 220 t @ 0.3 h = 8,800 t over 12 h → 733.33 t/h (n=40)**. Preserves the educational objective and `n=40` now teaches provenance *better*. Identical figure in L06 also corrected. | 01, 06 |
| **A3** | Lessons taught **private** framework API: `LinearTrendModel()._analyze()`, `twin._apply()`, `ShiftKpiCard()._render()`. | Replaced with public contracts, each verified first: `.analyze()` + `isinstance` narrowing to `TrendResult`; `TwinSynchronizer.synchronize()` for cold start; a second registered renderer observing the model via `RenderingPipeline.render()`. Grep sweep confirms **zero** private framework calls remain. | 07, 08, 09, 10 |

**A3 design note (recorded, not a defect):** `Visualization` exposes **no public
method at all** — only `_render`. The only public path is
`RenderingPipeline.render()`, returning a `RenderedOutput`, not a
`PresentationModel`. There is no public way to fetch a model directly; the
pipeline *is* the contract. Class definitions overriding `_apply`/`_render`
remain in lessons 09/10 — that is the extension point you implement, which A3
explicitly permits.

**Post-correction validation:** ruff clean · `ruff format --check` 725 files ·
`mypy --strict` clean (314 src + 10 lessons) · **10/10 lessons exit 0** ·
`mkdocs build --strict` 0 warnings · `check_docs.py` 0 broken / 0 failed ·
**pytest 2,986 passed** · `src/` untouched.

**Tutorials updated for changed output:** 01 (§3/§4, code excerpt, stale 18.33
prose), 03 (§3/§5, explanation, common-mistakes), 05 (§1), 06 (§2), 07 (excerpt
→ public API), 09 (§2 cold-start), 10 (§4).

### Remaining recommendations (NOT implemented — future work)

**Class B (this milestone, when scheduled):** pytest test executing all 10
lessons (E2) · exercise solutions (D1) · surface Fundamentals on landing page +
Next Steps (U1) · exclude `LEARNING_PROGRESS.md` from the published site (U2/U3)
· name deferred packages in lesson 10 (D2) · automate expected-output
verification (E3).

**Class C (future milestone):** shared fixtures (E4) · time/difficulty markers
(D3) · lesson-length ramp (D4) · ROM pad scale (M4) · footer nav (U4).

**New finding (out of scope, recorded):** the root `README.md` and
`docs/getting-started/quick-start.md` still show the same operationally
implausible `220 t / 12 h → 18.33 t/h` example that A2 corrected in the Learning
Suite. Those are production docs outside this milestone; correcting them was not
authorised here.

### QA findings — tutorial phase

- **Lesson 04 defect found and FIXED (locked lesson revisited under the
  genuine-defect rule).** Its "time travel" section printed
  `as of 06:18 ... 875t` while the *previous* section already showed
  `875t across 4 cycles` — the same number twice. The AsOf query ran *before*
  the correction was appended, so the demo **failed to demonstrate its own
  claim**: a reader learned nothing about point-in-time replay. Execution was
  correct; the *pedagogy* was broken. Fixed by adding section 7, which re-runs
  the same AsOf query *after* the correction: `as of 06:18 = 875t (unchanged)`
  vs `as of now = 1103t across 5 cycles`. Re-validated: ruff/format/mypy clean,
  exit 0. This is exactly the class of defect that only surfaces when you write
  the tutorial and have to explain the output.

### QA findings — lesson phase

- **Lesson 09: two `mypy --strict` errors caught before locking.**
  (1) `PredicateSpecification` needed an explicit type parameter when bound to
  a bare variable: `only_our_trucks: PredicateSpecification[EventEnvelope[Any]]`.
  (2) `AsOf.utc` is `datetime | None`, so `.isoformat()` needed a narrowing
  assert. Both fixed; the strict gate did its job.
- **No production defects found.** Lessons 08-10 used the decision,
  digital_twin, and visualization APIs exactly as documented; every behaviour
  matched the specification. `src/` untouched.
- Earlier finding retained: **trend slope is per SECOND** (see the API table) -
  lesson 07 exited 0 while printing a meaningless `-0.00`. Exit 0 is not
  correctness.

### Exact next step

Implementation is **done**. The next block is **Tutorials 01-10** in
`docs/tutorials/fundamentals/` (`01_hello.md` … `10_visualization.md`).

Author them **in order, 2-3 per session**, each using the roadmap's fixed
eleven-section format (Title · Objective · Prerequisites · Concepts covered ·
Complete runnable example · Expected output · Explanation · Best practices ·
Common mistakes · Exercises · Suggested next lesson).

**Method for each tutorial:**

1. **Run the lesson first and paste its REAL output** into "Expected output".
   Never write expected output from memory - the roadmap forbids it, and
   lesson 07 proved output can be wrong even at exit 0.
2. **Embed the runnable example** by reference: link the script on GitHub
   (`https://github.com/imanojkumar/MineProductivity/blob/main/examples/fundamentals/<dir>/<file>.py`)
   and show the key excerpt inline. Do **not** duplicate the whole script -
   reuse policy.
3. **"Common mistakes" is where the QA findings pay off.** Mine the verified-API
   table above: `eq=False` on entities (02), `RelationshipKind.BELONGS_TO` not
   `PART_OF` (05), the RATIO guardrail (06), the per-second slope trap (07),
   `AsOf.utc` being optional (09), qualify-don't-coerce (10).
4. **Cross-link** per the roadmap: script, API Reference, Architecture Handbook
   section, and next lesson.
5. Mark each tutorial row ☑ above as it lands.

**Then, in order:**
- Navigation: add a `Fundamentals` section under Tutorials in `mkdocs.yml`;
  link it from `docs/tutorials/index.md`.
- `mkdocs build --strict` (must be 0 warnings - note the link-rewrite hook at
  `scripts/docs/link_rewrite_hook.py` handles links escaping `docs/`).
- `scripts/quality/check_docs.py` (0 broken links, 0 failed snippets).
- Full `pytest` (regression check only - no production code was touched).
- Then **Phases 2-7**: freeze, and run the four independent reviews
  (Engineering QA, Educational, Mining Domain, Documentation/UX), classifying
  every recommendation as (a) defect-before-certification, (b) enhancement for
  this milestone, or (c) future-milestone candidate. Finally the Master
  Certification Report.

### Known risks / lessons learned

- **APIs are not guessable.** Lesson 05 failed on invented
  `Mine(commodity_code=…)` / `RelationshipKind.PART_OF`. Lesson 06 wrongly
  assumed `combine_results(RATIO)` returns a weighted mean - it *raises*.
  Read the source or an existing example **before** writing, every time.
- **Exit 0 is not correctness.** Lesson 07 exited 0 while printing a
  meaningless slope. Always read the numbers and ask whether they can be true.
- **The framework is often stricter than expected** - and that strictness is
  usually the best teaching material in the lesson (RATIO guardrail, slope
  units, interface-only forecasting).
- Tutorials (0/10) are the largest remaining block. Each needs all eleven
  sections, and its "Expected output" must be pasted from a **real run**, not
  imagined.
