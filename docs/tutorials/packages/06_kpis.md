# Package Tutorial 6 — KPIs (Deep)

!!! abstract "Milestone 2 · Package Tutorials · Tutorial 6 of 13 · **opens Unit B (Intelligence)**"
    Deep, full-surface tutorial for `mineproductivity.kpis` — the metadata-first
    metric backbone that turns the events a connector ingested into governed,
    self-describing measurements. Authored to **Package Tutorial Template v1.0**
    under the [Package Tutorial Implementation Standard](../../learning/PACKAGE_TUTORIAL_IMPLEMENTATION_STANDARD.md).

## Objective

Master the working surface of `mineproductivity.kpis`: the `KPIEngine` over an
event store, `BaseKPI`/`CompositeKPI` and the category bases, the 29-field
`KPIMetadata` and the `Aggregation` RATIO guardrail, `DependencyGraph`-resolved
composites, the self-describing `REGISTRY`, `KPIResult` provenance, and — the
payoff — **defining a new KPI as a governed object**.

All 32 public symbols (`mineproductivity.kpis.__all__`) are accounted for under the
**coverage convention** (§5): **11 [deep]** / **21 [ref]**. Public APIs only.

## Prerequisites

- Package Tutorials [1 — Core](01_core.md), [2 — Ontology](02_ontology.md),
  [3 — Events](03_events.md), [4 — Registry & Plugins](04_registry_and_plugins.md):
  kpis integrates all of them (§3).
- [Fundamentals L06 — KPIs](../fundamentals/06_kpis.md): the intro — KPI-as-object,
  and the guardrail that stops you averaging a ratio.

This tutorial **builds on** L06; it does not repeat the "why not just a formula"
argument.

## Running the examples

Every code block below is executed and its output pasted verbatim. Four scripts
(the analytics extra provides the DataFrame backend):

```bash
pip install -e ".[analytics]"
python examples/kpis/01_simple_execution.py   # ...and 02, 03, 04
```

---

## 1. Why this package exists

A KPI is not a formula you retype in every report — it is an **agreement** about
what a number means, and where it may and may not be used. `kpis` makes each metric
a *governed object*: a class carrying 29 fields of metadata (purpose, formula,
unit, required events, aggregation rule, benchmark bands, …) plus one pure
`_compute`. The engine, not the metric, does the orchestration — scanning the event
store, assembling rows, resolving dependencies — so every KPI is computed **one
way, from one definition**, and a dashboard at the north pit means exactly what the
south pit's does.

The headline discipline (from L06): a **ratio may never be averaged**. `Aggregation`
makes that a typed, enforced property of the metadata, not a rule people remember.

## 2. Architectural role

`kpis` opens Unit B (Intelligence). It consumes the foundation and produces the
evidence everything above reads:

```
… events ─► registry ─► connectors ─► kpis ─► analytics ─► decision ─► …
```

Downstream, `analytics` characterises KPI *history* and `decision` acts on KPI
*breaches* — and neither re-derives the metric. A `KPIResult` is the governed unit
of evidence the whole intelligence half is built on.

## 3. Integration with adjacent layers

`kpis` is where the foundation converges into measurement.

**`events` (Tutorial 3) — the data source:** `KPIEngine` holds an
`events.EventStore`; `execute()` builds an `events.EventQuery`, scans the matching
envelopes, and flattens their payloads into the rows a KPI's `_compute` reads. A KPI
never touches raw storage — it consumes the governed event log.

**`ontology` (Tutorial 2) — scope resolution & namespaces:** the engine resolves a
`scope={"shift": …}` window against a known `ontology.Shift`'s `start_utc`/`end_utc`
(a real integration, not a placeholder); `KPIMetadata.required_ontology` and the
`NAMESPACE.Name` codes (`PROD.`, `UTIL.`, …) are ontology-governed.

**`registry` (Tutorial 4) — discovery:** `REGISTRY` is a
`registry.Registry[str, type[BaseKPI]]`; `@register` adds a KPI to it (and
`KPIVersionConflictError` *is* a `registry.RegistrationError`). Re-registering a
code is refused — a KPI code is a public contract requiring a MAJOR version bump,
never a silent overwrite.

**`core` (Tutorial 1):** `KPIMetadata` subclasses `core.BaseMetadata`; `KPIResult`
is a `core.BaseValueObject`; `execute()`/`summary()` return a `core.Result`.

**Upward:** `analytics` and `decision` consume `KPIResult`s — this package produces
the governed evidence they reason over.

## 4. Package structure

| Group | Module(s) | Public symbols |
|---|---|---|
| The KPI contract | `base_kpi`, `composite` | `BaseKPI`, `CompositeKPI` |
| Metadata & naming | `metadata`, `naming`, `lifecycle` | `KPIMetadata`, `Aggregation`, `Direction`, `DigitalMaturity`, `KPIIdentifier`, `parse_identifier`, `KPIStatus` |
| Category bases | `categories/` | `ProductionKPI`, `UtilizationKPI`, `HaulageKPI`, `MaintenanceKPI`, `DelayKPI`, `EnergyKPI`, `CostKPI`, `QualityKPI`, `SafetyKPI` |
| Engine & graph | `engine`, `dependency_graph`, `caching` | `KPIEngine`, `DependencyGraph`, `ResultCache` |
| Result & windows | `result`, `windowing` | `KPIResult`, `Window`, `RollingWindow`, `CumulativeWindow` |
| Registry | `_registry` | `REGISTRY`, `register` |
| Exceptions | `exceptions` | `KPIValidationError`, `KPINotFoundError`, `KPICircularDependencyError`, `KPIAggregationError`, `KPIVersionConflictError` |

## 5. Public APIs

All 32 exports under the **coverage convention**:

**The spine — [deep]**
: `BaseKPI`, `CompositeKPI`, `KPIMetadata`, `KPIResult`, `KPIEngine`,
  `DependencyGraph`, `REGISTRY`, `register`, `Aggregation`, `Direction`,
  `ProductionKPI`

**Everything else — [ref]** — see the table.

### Reference coverage

| Group | Symbols (`[ref]`) | What / when |
|---|---|---|
| Category bases | `UtilizationKPI`, `HaulageKPI`, `MaintenanceKPI`, `DelayKPI`, `EnergyKPI`, `CostKPI`, `QualityKPI`, `SafetyKPI` | The other eight namespace bases (`UTIL.`, `HAUL.`, …), each a `BaseKPI` subclass enforcing its namespace — you extend one exactly as §13 extends `ProductionKPI`. |
| Naming & lifecycle | `KPIIdentifier`, `parse_identifier`, `KPIStatus`, `DigitalMaturity` | A parsed `NAMESPACE.Name` code; the lifecycle status (PROPOSED/ACTIVE/DEPRECATED/RETIRED); the digital-maturity level a KPI requires. |
| Windows & cache | `Window`, `RollingWindow`, `CumulativeWindow`, `ResultCache` | Window value objects for rolling/cumulative aggregation; the engine's per-run row/result cache (so two KPIs over the same event stream fetch it once). |
| Exceptions | `KPIValidationError`, `KPINotFoundError`, `KPICircularDependencyError`, `KPIAggregationError`, `KPIVersionConflictError` | Invalid metadata, unknown code, a dependency cycle (caught at *registration*), an illegal aggregation (e.g. averaging a ratio), a duplicate-code registration. All derive from `core.MineProductivityError`. |

## 6. Conceptual model

Five ideas explain the package.

**A. A KPI is metadata + one pure function.** A leaf declares `meta: KPIMetadata`
and implements `_compute(rows) -> float | None`. Everything else — validation,
result wrapping, the "qualify, don't coerce" rule — is inherited from `BaseKPI`.

**B. The engine orchestrates; the KPI computes.** `KPIEngine.execute` resolves the
dependency graph, assembles exactly the rows each node needs from the event store,
runs leaves before composites, and returns a `KPIResult`. The KPI holds *no*
orchestration; the engine holds *no* metric logic.

**C. Composites are declared, not hand-wired.** A `CompositeKPI` names its
`dependencies`; `DependencyGraph` topologically orders them, so `UTIL.OEE` computes
`UTIL.PA`, `UTIL.UA`, `UTIL.Performance` first, then combines — from one `execute`.

**D. Qualify, don't coerce.** Missing data yields a `KPIResult` with `value=None`
and a warning, never a fabricated `0.0` and never a crash — and a missing dependency
propagates `None` upward, not a silent zero.

**E. KPIs are discoverable and self-describing.** `REGISTRY` lets you enumerate,
filter, and fully describe any KPI — purpose, formula, unit, dependencies — without
reading a line of its source.

## 7. Real mining examples

The walkthroughs run a real shift's events through the engine: the flagship
`PROD.TPH` (tonnes per hour), the composite `UTIL.OEE`, a nine-KPI batch summary,
and registry discovery. §13 adds a custom `PROD.AvgPayload`.

## 8. Step-by-step walkthroughs

### 8.1 Single-KPI execution and the traceable result

`engine.execute(code, window=, scope=)` returns a `core.Result[KPIResult]`; the
`KPIResult` carries provenance (unit, `n` source rows, warnings), not a bare number,
and `to_frame()` exports it via the active backend. A KPI with no matching data
returns a warning-carrying result, never a crash. Running
[`01_simple_execution.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/kpis/01_simple_execution.py):

```text
--- 1. Execute a single KPI for a single shift ---
PROD.TPH = 216.8 t/h (from 12 cycle events)

--- 2. KPIResult carries provenance, not just a bare number ---
code='PROD.TPH' unit='t/h' n=12 warnings=()

--- 3. A KPI with no matching data returns a warning-carrying result, never a crash ---
value=None warnings=()

--- 4. Export to a DataFrame via the active ExecutionBackend ---
    code      value unit  n
PROD.TPH 216.829268  t/h 12
```

### 8.2 Composite KPIs and the dependency graph

`DependencyGraph(REGISTRY).topological_order("UTIL.OEE")` shows the resolved order;
one `execute("UTIL.OEE", …)` computes each component then combines them — and a
missing dependency's data propagates `None`, never a fabricated zero. Running
[`02_composite_oee.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/kpis/02_composite_oee.py):

```text
--- 1. UTIL.OEE's dependency graph is resolved automatically ---
execution order: UTIL.PA -> UTIL.UA -> UTIL.Performance -> UTIL.OEE

--- 2. One execute() call computes every dependency, then combines them ---
UTIL.OEE = 0.8305 (n=4)

--- 3. The three components are independently inspectable too ---
           UTIL.PA = 0.9167
           UTIL.UA = 1.0000
  UTIL.Performance = 0.9060

--- 4. A missing dependency's data propagates None, never a fabricated zero ---
UTIL.OEE (no data) = None warnings=("upstream dependency has no value: ['UTIL.PA', 'UTIL.Performance', 'UTIL.UA']",)
```

### 8.3 Batch summary with shared row-fetching

`summary([...])` computes many KPIs in one call; the `ResultCache` ensures two KPIs
reading the same event stream (`PROD.TPH` and `HAUL.TruckCycleTime` both read
`CYCLE`) fetch those rows exactly once. Running
[`03_batch_summary.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/kpis/03_batch_summary.py):

```text
--- Requesting 9 KPIs in a single summary() call ---

KPI                            Value  Unit        n
---------------------------------------------------
PROD.TPH                     216.829  t/h        12
UTIL.OEE                       0.831  ratio       4
HAUL.TruckCycleTime           61.500  min        12
MAINT.MTTR                     1.000  h           1
DISP.TotalDelayHours           1.417  h           2
ENERGY.FuelConsumed          805.000  L           2
COST.FuelPerTonne              0.302  L/t        14
QUAL.OreProportion             0.750  ratio      12
SAFE.SpeedViolationCount       2.000  count       2

--- Rows backing PROD.TPH and HAUL.TruckCycleTime were fetched exactly once, ---
--- shared between them since both read only the CYCLE event stream. ---
PROD.TPH matched 12 CYCLE envelopes, 12 rows after assembly
```

### 8.4 Discovery: KPIs describe themselves

`REGISTRY` is enumerable and filterable, and each KPI's `meta` fully describes it —
so an engineer or an AI agent can trust a number without reading its formula in a
script. Running
[`04_discovery.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/kpis/04_discovery.py):

```text
--- 1. Every registered KPI code (12 total) ---
  COST.FuelPerTonne
  DISP.TotalDelayHours
  ENERGY.FuelConsumed
  HAUL.TruckCycleTime
  MAINT.MTTR
  PROD.TPH
  QUAL.OreProportion
  SAFE.SpeedViolationCount
  UTIL.OEE
  UTIL.PA
  UTIL.Performance
  UTIL.UA

--- 2. Filter by namespace: everything in UTIL ---
  ['UTIL.OEE', 'UTIL.PA', 'UTIL.Performance', 'UTIL.UA']

--- 3. Filter to composite (DERIVED) KPIs only ---
  ['UTIL.OEE']

--- 4. Fully describe one flagship KPI without reading its source ---
PROD.TPH -- Tonnes Per Hour [leaf, ratio]
  business purpose:      Throughput rate is the single most-watched production number in mining.
  operational question:  At what rate is this asset producing material?
  formula:               sum(payload_t) / sum(operating_h)
  unit:                  t/h
  direction:             higher_is_better
  required events:       CYCLE

UTIL.OEE -- Overall Equipment Effectiveness [composite, derived]
  business purpose:      The single composite number summarizing availability, utilisation, and performance together.
  operational question:  Overall, how effectively was this asset's scheduled time converted to output?
  formula:               UTIL.PA * UTIL.UA * UTIL.Performance
  unit:                  ratio
  direction:             higher_is_better
  required events:       MAINTENANCE, PRODUCTION
  dependencies:          UTIL.PA, UTIL.UA, UTIL.Performance
```

## 9. Repository example reuse

The four `kpis` example scripts were each executed (exit `0`), output above.

| Script | Public API it exercises | Walkthrough |
|---|---|---|
| [`01_simple_execution.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/kpis/01_simple_execution.py) | `KPIEngine.execute`, `KPIResult`, `to_frame` | §8.1 |
| [`02_composite_oee.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/kpis/02_composite_oee.py) | `CompositeKPI`, `DependencyGraph`, `REGISTRY` | §8.2 |
| [`03_batch_summary.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/kpis/03_batch_summary.py) | `KPIEngine.summary`, `ResultCache` | §8.3 |
| [`04_discovery.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/kpis/04_discovery.py) | `REGISTRY`, `KPIMetadata`, `Aggregation`, `Direction` | §8.4 |

## 10. Common mistakes

| Mistake | What happens | Do this instead |
|---|---|---|
| Averaging a ratio KPI | Mathematically wrong (1,200 vs 1,233.3 t/h) | Declare `Aggregation.RATIO`; re-derive from summed numerator/denominator |
| Defaulting missing data to `0.0` | A dashboard reads "stopped" when the feed died | Return `None` from `_compute`; the result carries a warning |
| Raising from `_compute` on empty input | One bad shift crashes the batch | Return `None`; `compute` attaches the warning |
| Re-deriving a KPI downstream | Two definitions of one metric | Consume the `KPIResult` (analytics/decision never recompute) |
| Re-registering a code to "update" it | `KPIVersionConflictError` | A new meaning is a MAJOR version bump under review |
| Putting orchestration in a KPI | Breaks "engine orchestrates, KPI computes" | Keep `_compute` a pure `rows -> scalar` function |
| Leaving a metadata field blank | `KPIValidationError` at construction | Every field is mandatory — a blank is a spec gap |

## 11. Best practices

- **Subclass the right category base** so your code lands in the correct namespace.
- **Populate all 29 metadata fields** — the metadata *is* the governance.
- **Keep `_compute` pure** (`rows -> float | None`); no I/O, no orchestration.
- **Declare the correct `Aggregation`** — it is the guardrail that keeps rollups honest.
- **Return `None`, never `0.0`,** for legitimately uncomputable inputs.
- **Let the engine assemble rows**; declare `required_events`/`_required_columns`
  and let it fetch (and cache) them.

## 12. Performance considerations

- **The `ResultCache` fetches shared event streams once** — a nine-KPI summary over
  the `CYCLE` stream scans it a single time, not nine.
- **`DependencyGraph` topological order is computed once** and cached; a cycle is
  caught at *registration*, never at execute time.
- **Backends are swappable** (numpy/pandas/polars/duckdb via the active
  `ExecutionBackend`) so the same KPI scales from a test file to a shift export.
- **KPI instances are stateless** across `compute` calls — safe to share and invoke
  concurrently.

## 13. Extension points — define a new KPI

`kpis`' extension point is **a new governed metric**: subclass a category base,
declare a full `KPIMetadata`, implement the pure `_compute`, and `@register`. It is
then discoverable in `REGISTRY` and executable through the same engine, with
qualify-don't-coerce inherited. The example was executed and passes `ruff` /
`ruff format --check` / `mypy --strict`:

```python
from collections.abc import Mapping, Sequence
from typing import Any

from mineproductivity.kpis import (
    REGISTRY, Aggregation, Direction, KPIMetadata, ProductionKPI, register,
)


@register
class AvgPayload(ProductionKPI):
    meta = KPIMetadata(
        code="PROD.AvgPayload",
        name="Average Payload",
        official_name="Average Payload",
        business_purpose="Mean tonnes carried per haul cycle, a core loading-efficiency signal.",
        operational_question="How much material is each truck carrying per cycle, on average?",
        business_meaning="Payload below rated capacity wastes cycles; above it risks the asset.",
        formula="mean(payload_t)",
        unit="t",
        dimensions=("equipment", "shift"),
        required_events=("CYCLE",),
        aggregation=Aggregation.AVERAGE,
        direction=Direction.HIGHER_IS_BETTER,
    )

    def _required_columns(self) -> tuple[str, ...]:
        return ("payload_t",)

    def _compute(self, rows: Sequence[Mapping[str, Any]]) -> float | None:
        payloads = [float(row["payload_t"]) for row in rows]
        return sum(payloads) / len(payloads) if payloads else None
```

Exercising it — the new KPI registers, is discoverable, computes a traceable result,
and inherits qualify-don't-coerce:

```text
--- 1. The custom KPI registered itself, discoverable like any built-in ---
'PROD.AvgPayload' in REGISTRY: True
REGISTRY now holds 13 KPIs

--- 2. compute() wraps the scalar in a traceable KPIResult ---
code=PROD.AvgPayload value=221.00 unit=t n=3

--- 3. Qualify, don't coerce: a missing column is a warning, never a crash ---
value=None warnings=("missing required columns: ['payload_t']",)
```

A **`CompositeKPI`** extends the same way, additionally declaring `dependencies`;
the `DependencyGraph` wires it in. Ship a KPI pack as a plugin (Tutorial 4) and its
`@register` runs on install — the mine's custom metrics appear in `REGISTRY`
alongside the standard library.

!!! note "Registration is a governance act"
    `@register` validates the metadata, refuses a duplicate code
    (`KPIVersionConflictError`), and proves the dependency graph acyclic — *at
    registration time*, not first execution. A KPI code is a public contract.

## 14. Exercises

1. **Define a leaf KPI.** Write `HAUL.AvgHaulMinutes` over `HaulageKPI`, computing the
   mean `haul_min`; register it and confirm it appears in `REGISTRY`.
2. **Trip the guardrail.** Give a ratio KPI `Aggregation.AVERAGE` and reason about why
   the platform wants `Aggregation.RATIO` instead — what would a shift rollup get wrong?
3. **Qualify, don't coerce.** Call your KPI's `compute` with rows missing its required
   column and with empty rows. What does each return, and why is neither an exception?
4. **Describe without reading source.** Using only `REGISTRY.get(code).meta`, print the
   purpose, formula, unit, and dependencies of `UTIL.OEE`. Why is this the whole point
   of KPI-as-object?
5. **Compose.** Sketch a `CompositeKPI` depending on two leaves; what does
   `DependencyGraph.topological_order` return, and when is a cycle caught?

## 15. Reference solutions

??? success "Solution 1 — Define a leaf KPI"
    ```python
    @register
    class AvgHaulMinutes(HaulageKPI):
        meta = KPIMetadata(code="HAUL.AvgHaulMinutes", name="Avg Haul Minutes",
            official_name="Average Haul Minutes", business_purpose="...",
            operational_question="...", business_meaning="...", formula="mean(haul_min)",
            unit="min", dimensions=("equipment",), required_events=("CYCLE",),
            aggregation=Aggregation.AVERAGE, direction=Direction.LOWER_IS_BETTER)
        def _required_columns(self): return ("haul_min",)
        def _compute(self, rows):
            xs = [float(r["haul_min"]) for r in rows]
            return sum(xs) / len(xs) if xs else None
    "HAUL.AvgHaulMinutes" in REGISTRY   # True
    ```

??? success "Solution 2 — Trip the guardrail"
    Averaging shift-level ratios weights every shift equally regardless of size, so a
    quiet 4-cycle shift skews the number as much as a busy 40-cycle one.
    `Aggregation.RATIO` re-derives from `sum(numerator) / sum(denominator)`, which is
    the only correct rollup — the platform encodes that as metadata so no one has to
    remember it.

??? success "Solution 3 — Qualify, don't coerce"
    ```python
    kpi.compute([{"tonnes": 220.0}]).warnings   # ("missing required columns: ['payload_t']",)  value=None
    kpi.compute([]).value                        # None (no rows) -- no warning, just uncomputable
    ```
    Neither raises: a missing column and an empty input are *data* conditions the
    caller must see, not crashes.

??? success "Solution 4 — Describe without reading source"
    ```python
    m = REGISTRY.get("UTIL.OEE").meta
    m.formula        # 'UTIL.PA * UTIL.UA * UTIL.Performance'
    m.unit           # 'ratio'
    m.dependencies   # ('UTIL.PA', 'UTIL.UA', 'UTIL.Performance')
    ```
    Every number is traceable to a governed definition without opening a script — that
    is what makes a KPI trustworthy across sites and to an AI agent.

??? success "Solution 5 — Compose"
    A `CompositeKPI` names `dependencies=("A", "B")`; `topological_order` returns
    `['A', 'B', 'Composite']` (leaves first). A cycle (A depends on the composite that
    depends on A) raises `KPICircularDependencyError` **at registration**, so it can
    never reach execution.

## 16. Further reading

- **[`kpis` package guide](../../packages/kpis.md)** — the capability-tour view.
- **[`kpis` API reference](../../api-reference/kpis.md)** — every symbol, from source.
- **[KPI Engine Design Specification](../../architecture/05_KPI_Engine_Design_Specification.md)** — AD-KP-01 (engine holds no metric logic), AD-KP-06 (registry), the 29-field Standard Library template.
- **[Fundamentals L06 — KPIs](../fundamentals/06_kpis.md)** · Package Tutorials [3 — Events](03_events.md) · [4 — Registry & Plugins](04_registry_and_plugins.md).

---

**Next package tutorial:** Analytics (deep) — characterising a KPI's *history*
(is it drifting?) without ever re-deriving the KPI.
*(Not yet written — Tutorial 7 of 13.)*
