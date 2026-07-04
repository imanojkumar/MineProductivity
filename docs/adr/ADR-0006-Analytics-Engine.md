# ADR-0006: Analytics Engine as a Separate Package Above `kpis`

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-07-04 |
| **Deciders** | Chief Software Architect, MineProductivity |
| **Governs** | `mineproductivity.analytics` |
| **Related documents** | [`docs/architecture/06_Analytics_Engine_Design_Specification.md`](../architecture/06_Analytics_Engine_Design_Specification.md); [`docs/design/06_Analytics_Engine_Implementation_Checklist.md`](../design/06_Analytics_Engine_Implementation_Checklist.md); [`docs/architecture/05_KPI_Engine_Design_Specification.md`](../architecture/05_KPI_Engine_Design_Specification.md) §4, §7 |

## Context

MineProductivity's Foundation Layer — `core`, `events`, `ontology`, `registry`, `plugins`, `connectors`, `kpis` — is complete, tested (1,390 tests, 100% line coverage), and locked as of `kpis` v0.7.0. The KPI Engine spec itself already anticipated what comes next: its own §4 (Out of Scope) states that *"analytics, forecasting, benchmarking implementations"* are explicitly not `kpis`' responsibility, and its §7 (Dependency Direction) already lists `analytics` among the packages `kpis` is depended on by. `Registry`'s own docstring (`src/mineproductivity/registry/registry.py`) already names `AnalyticsRegistry` alongside `KPIRegistry`/`ConnectorRegistry` as an anticipated specialization. In other words, the platform's own locked documents already assume an `analytics` package will exist, directly above `kpis`, before this ADR was written — this decision formalizes and designs that already-assumed package, rather than introducing a new idea into the architecture.

The immediate question this ADR answers: given a `KPIResult` — a single, correct, versioned number — operational users repeatedly ask a second-order question the KPI Engine was never meant to answer: *is this trending, is this normal, how does it compare, how confident are we.* Somewhere in the platform, exactly one package needs to own turning a correct number into an operational judgment. This ADR decides where.

## Decision

Create `mineproductivity.analytics` as a new, independent package sitting directly above `kpis` and directly below the not-yet-designed `decision` package:

```
core → ontology → events → kpis → analytics → decision → digital_twin
```

`analytics` is permitted to import `core`, `events`, `ontology`, `registry`, `plugins`, `connectors`, and `kpis`; it introduces its own public API (`AnalyticsModel`, `AnalyticsPipeline`, `AggregationEngine`, `TimeSeries`, statistical primitives, `TrendModel`/`BaselineModel`/`BenchmarkModel` and their default concrete implementations, and interface-only `ForecastingModel`/`AnomalyDetector`/`OutlierDetector` contracts) without requiring any change to any Foundation Layer file, public API, or dependency rule. Its own registry (`analytics.REGISTRY`) is a direct specialization of `registry.Registry`, exactly as `kpis.REGISTRY` already is. Full design detail is in the governing specification linked above; this ADR records *why* the package exists and *why* it is shaped the way it is, not the object model itself.

## Why a Separate Package (Not Folded Into `kpis`)

1. **Distinct responsibility, distinct rate of change.** `kpis` answers "what is the value of this one metric, for this one scope, right now" — a question governed by audited business metadata (the 29-field `KPIMetadata` schema) that changes rarely and under heavy governance. `analytics` answers "what does a series of such values mean" — a question whose answer set (new trend algorithms, new benchmarking strategies, eventually new forecasting/anomaly-detection plugins) is expected to grow much faster and with much lighter governance. Folding the two into one package would force the slower-changing, heavily-governed KPI schema and the faster-changing analytics surface to release, version, and review together for no shared reason.
2. **`kpis`' own spec already drew this boundary.** Spec 05 §4 explicitly excludes analytics/forecasting/benchmarking from `kpis`' scope and §7 explicitly forbids `kpis` from importing anything above it in the stack. Keeping analytics inside `kpis` would have required either violating that already-locked out-of-scope boundary or silently ignoring it — both worse than creating the separate package the spec already assumed.
3. **Independent testability of a categorically different question.** `kpis`' correctness proofs are about formula/aggregation/dependency-graph correctness for one metric. `analytics`' correctness proofs (§35 of the design spec) are about statistical correctness over series and about *not* silently re-deriving KPI semantics incorrectly one layer up (the cross-group ratio-aggregation delegation rule, design spec §10). These are different enough test philosophies that co-locating them in one package's test suite would blur, not clarify, what each suite is actually proving.
4. **Consistent with every other layer boundary already drawn in this platform.** `connectors` is separate from `events` for exactly the same shape of reason (vendor-neutral ingestion vs. the event model itself); `registry`/`plugins` is separate from every domain package that specializes it. A platform that has consistently drawn a package boundary at every "distinct responsibility, distinct rate of change, distinct governance weight" seam would be inconsistent to suddenly stop doing so at the one seam (`kpis` → `analytics`) its own spec already named.

## Dependency Rationale

`analytics` is permitted to import the entire Foundation Layer (`core` through `kpis`), not merely `kpis` directly, for a specific reason: Analytics computations legitimately need `events.EventStore`/`EventBus` directly (for streaming and for raw-row distribution analysis that does not go through a KPI at all, design spec §12, §27), not merely `kpis.KPIResult` objects. Restricting `analytics` to *only* import `kpis` would have forced either (a) `kpis` to grow pass-through re-exports of `events`/`registry` types it does not otherwise need to expose, purely so `analytics` could reach them indirectly, or (b) `analytics` to duplicate event-querying logic `events` already provides. Both are worse than the direct, transitive-looking-but-architecturally-clean permission this ADR grants.

`connectors` is included in the permitted-import list for platform-wide layering consistency (every package above `events` may reach it), but this design deliberately does not exercise it — Analytics operates on already-ingested, already-validated data (`EventStore` rows, `KPIResult` objects), never on a vendor-specific wire format. This is recorded as a standing anti-pattern in the design spec (§34) rather than left ambiguous, precisely so a future contributor does not read "connectors is a permitted import" as an invitation to import it.

## Architectural Trade-offs

- **Trade-off accepted:** `analytics` reuses `kpis.Window`/`RollingWindow`/`CumulativeWindow`, `kpis.ExecutionBackend`, and `kpis.Aggregation` rather than defining its own parallel concepts (design spec §3.3, §11, §36). This couples `analytics`' own windowing/vectorization vocabulary to `kpis`' already-locked shapes — a genuine constraint, since `analytics` cannot unilaterally redesign windowing if it later finds `kpis.Window`'s shape limiting. This trade-off was accepted because the alternative (a second, subtly-different windowing concept) is a strictly worse failure mode: two similar-but-not-identical "rolling window" ideas in one platform is a standing source of subtle bugs and confused contributors, which this platform has consistently avoided at every other layer.
- **Trade-off accepted:** the cross-group `RATIO`-aggregation delegation rule (design spec §10) means `AggregationEngine.reduce_kpi_results` sometimes has to call back into `KPIEngine.execute()` rather than combining already-computed values directly — more expensive (a second engine invocation) than a naive combine, but the naive combine is provably wrong for exactly the same reason spec 05 §13.3 already proved it wrong one level down. Correctness was chosen over the cheaper, wrong path.
- **Trade-off accepted:** `AnalyticsMetadata` (design spec §31) is deliberately much lighter than `KPIMetadata` — this means an `AnalyticsModel` carries far less governance ceremony than a KPI, which is the right default for a computational strategy but does mean Analytics models do not get the same "this is a public, versioned business contract" treatment a KPI code gets. If a future need arises for Analytics models to carry that same weight (e.g. a regulator-facing benchmarking methodology), that would be a deliberate, separate future revision, not something this design silently under-provisions for today.

## Alternatives Considered

1. **Fold analytics capability directly into `kpis`** (e.g. `KPIResult.trend()`, `KPIResult.benchmark()` methods). Rejected — directly contradicts `kpis`' own already-locked out-of-scope boundary (spec 05 §4) and would make `kpis` responsible for a second, faster-changing surface with a different governance need (see "Why a Separate Package," above).
2. **Defer `analytics` entirely until `decision` needs it**, treating trend/benchmark/statistics logic as `decision`'s own internal implementation detail rather than a shared package. Rejected — `digital_twin`, `optimization`, `simulation`, and a future `agents` package (design spec §37) will all independently need the same statistical vocabulary (percentile, confidence interval, rolling window, trend slope); deferring this package would mean each of those future packages reimplements its own, likely mutually inconsistent, version of "what is a rolling average" — the exact failure mode "KPI-as-object" was invented to prevent one layer down, recurring one layer up if not addressed now.
3. **A single, larger "analytics + decision" package**, reasoning that trend/benchmark output only exists to feed decision logic anyway. Rejected — `digital_twin` and `optimization`/`simulation` (design spec §37) are also expected to consume Analytics' outputs without needing any decision-recommendation logic at all; bundling the two would force those packages to depend on decision-making code they do not need, violating the same "distinct responsibility, distinct rate of change" reasoning used above.
4. **Ship concrete forecasting/anomaly/outlier-detection algorithms now**, on the reasoning that an interface without any implementation is less immediately useful. Rejected — see "Alternatives Rejected" below; this was the most seriously considered and most explicitly rejected alternative.

## Alternatives Rejected

**Shipping at least one concrete `ForecastingModel`/`AnomalyDetector`/`OutlierDetector` implementation in this initial release** was the most seriously debated alternative, and is rejected for three compounding reasons:

1. **Scope creep into machine learning.** Even a "simple" forecasting or anomaly-detection algorithm is a modeling choice (which smoothing method, which threshold, which distributional assumption) — exactly the kind of decision this package's charter (design spec §3.1, §3.4) excludes. Shipping one now, "just as a starting point," would establish a precedent that quietly widens `analytics`' scope every time a new modeling technique seems reasonable to add.
2. **Premature commitment to an interface's shape via its first implementation.** An ABC designed alongside its first concrete implementation tends to be shaped by that implementation's convenience rather than by the general contract future, independent implementations will need. Shipping the interface alone, now, and deferring the first concrete implementation to a future, independently-reviewed and independently-versioned addition, keeps the contract honest.
3. **The three capabilities are exactly the ones most likely to need genuinely different algorithms per deployment.** A mine's fleet-level forecasting need (shift-level tonnage) and a corporate rollup's forecasting need (quarterly trend) are different enough problems that a single "reference" implementation shipped by this project would likely be wrong, or at best mediocre, for most real deployments — better to hand implementers a stable contract and let the ecosystem's plugin mechanism (design spec §33) do what it already does well for KPIs and connectors.

**A bespoke plugin/discovery mechanism specific to Analytics** (rather than reusing `registry.Registry`/`registry.EntryPointDiscovery`) was also considered and rejected outright — the entire point of the Registry Framework (spec 03) is that every domain package specializes the same mechanism; a bespoke Analytics-specific one would be pure, unjustified duplication with no compensating benefit.

## Long-Term Evolution

This package is expected to grow along two, and only two, axes without requiring a new ADR:

1. **New concrete strategies within existing categories** (new `TrendModel`/`BaselineModel`/`BenchmarkModel` subclasses) — this is ordinary, checklist-governed extension (design spec §32), not an architectural change.
2. **The first concrete `ForecastingModel`/`AnomalyDetector`/`OutlierDetector` implementations**, whenever they arrive (first-party or third-party) — these are expected to land as plugins against the already-stable ABCs this design defines, not as a revision to this specification.

A new ADR **would** be warranted if a future need arose to: change `analytics`' position in the dependency chain; permit `analytics` to be imported by a Foundation Layer package (which would indicate a design error somewhere, not a legitimate evolution); or introduce a second, competing extension mechanism alongside the Registry Framework specialization this design already commits to.

## Future Compatibility

Every public type this package introduces (§30 of the design spec, `AnalyticsResult` and its subclasses) is a plain, frozen `core.BaseValueObject`, serializable via the platform's existing `core.serialization` mechanism, with no `analytics`-internal state leaking into any type a future package would need to consume. This is a deliberate compatibility guarantee for the packages named in the design spec's Future Roadmap (§37) — `decision`, `digital_twin`, `optimization`, `simulation`, and a future `agents` package — none of which are designed by this ADR or by the governing specification, but all of which are expected to consume `analytics`' output types without requiring a breaking change to them. The `ForecastingModel`/`AnomalyDetector`/`OutlierDetector` interfaces (design spec §16, §18, §19) exist specifically so that whichever of those future packages first needs a concrete forecasting or anomaly-detection capability can implement against a contract that already exists, rather than this specification needing revision when that need arrives.

---

*This ADR governs the existence and shape of `mineproductivity.analytics` as a package. See [`06_Analytics_Engine_Design_Specification.md`](../architecture/06_Analytics_Engine_Design_Specification.md) for the full object model and [`06_Analytics_Engine_Implementation_Checklist.md`](../design/06_Analytics_Engine_Implementation_Checklist.md) for the locked implementation contract.*
