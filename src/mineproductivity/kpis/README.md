# mineproductivity.kpis

## Purpose

`mineproductivity.kpis` is the metric backbone of MineProductivity — the platform's most important package. It makes every performance indicator a discoverable, versioned, self-describing object ("KPI-as-object") rather than a formula buried in a script or a spreadsheet cell, guaranteeing the platform's central promise: two engineers, two sites, or two AI agents each computing "availability" get the same number from the same events.

This package implements the [KPI Engine Design Specification](../../../docs/architecture/05_KPI_Engine_Design_Specification.md) exactly. Where this README and that specification disagree, the specification governs.

## Scope

**What belongs here:**

- `KPIMetadata` — the complete, governed 29-field mandatory schema (Developer & Cookbook Guide Part III, KPI Standard Library) every registered KPI carries.
- `BaseKPI`, `CompositeKPI` — the two KPI base classes: a leaf reads raw event rows (`_compute`), a composite reads other KPIs' already-computed results (`_combine`). Never conflated.
- Nine category base classes (`ProductionKPI`, `UtilizationKPI`, `MaintenanceKPI`, `HaulageKPI`, `DelayKPI`, `EnergyKPI`, `QualityKPI`, `CostKPI`, `SafetyKPI`), one per controlled namespace family, contributing only a namespace-conformance check.
- `KPIEngine` — orchestration only: resolves a KPI's dependency graph, assembles exactly the rows each node needs, executes leaves before composites, caches, and returns a traceable `KPIResult`. Holds zero metric-specific logic (AD-KP-01).
- `DependencyGraph`, `aggregation.combine_results`, `Window`/`RollingWindow`/`CumulativeWindow`, `ResultCache`.
- Four pluggable `ExecutionBackend`s (`PandasBackend` default, `NumPyBackend`, `PolarsBackend`, `DuckDBBackend`) — the same `_compute` runs unchanged regardless of which one is active (backend parity).
- The 12-KPI Standard Library reference implementation, one flagship per category plus the `UTIL.OEE` composite worked example.
- `parse_identifier`/`KPIIdentifier` (the `NAMESPACE.Name[.Specialization]` naming standard), `specialize()` (KPI inheritance, e.g. `PROD.TPH.Ore`), `KPIValidator`, `CertificationFixture`/`run_certification_fixture`.

**What must never belong here:**

- Event definitions — owned by `events`; `kpis` reads canonical events via an injected `EventStore`, never redefines their shape.
- Ontology entity definitions — owned by `ontology`; `kpis` reads `Shift` for window resolution, never defines domain entities.
- **Any dependency on `connectors`, `analytics`, `optimization`, `simulation`, `decision`, `digital_twin`, or `agents`** — the single most load-bearing rule in the governing specification (§7).
- Metric-specific branches inside `engine.py` — a new KPI is added entirely in `standard_library/`, never by editing the engine.

## Architecture

```
core → ontology → events → registry → kpis
```

`kpis` sits after `events`, `ontology`, and `registry` in the dependency stack — it is intelligence built on top of the durable event log, resolving ontology reference data (shifts) for window bounds and using `registry` as its own KPI catalogue's specialization mechanism.

The engine's own internal flow, end to end:

```
KPIEngine.execute(code, window, scope)
   |
   v
DependencyGraph.topological_order(code)      -- dependencies before dependents (raises
   |                                             KPICircularDependencyError if cyclic)
   v
for each step in order:
   |
   +-- CompositeKPI?  -> combine(already-computed dependency KPIResults)
   |
   +-- leaf KPI?      -> rows_for(kpi, window, scope)
                            |  EventQuery scoped to kpi.meta.required_events + window/scope
                            |  EventStore.query() -> envelopes -> flatten -> ExecutionBackend
                            |  .assemble() -> .to_rows()  (mechanical backend-parity proof)
                            v
                         ResultCache.get_or_compute(code, window, scope, fingerprint, ...)
                            |
                            v
                         BaseKPI.compute(rows)  -- missing-column precheck, then _compute()
   |
   v
KPIResult  (value | None, unit, n, warnings, scope)
```

`KPIEngine.summary()` is the batched equivalent: it computes the transitive closure of every requested code's dependencies once, then scans the event store once per distinct `required_events` set shared across them — not once per KPI.

See the [design specification's §10](../../../docs/architecture/05_KPI_Engine_Design_Specification.md) for the full object model and canonical semantics.

## Package Structure

```
kpis/
├── __init__.py            # public API surface (__all__); registers the 12-KPI standard library
├── _registry.py             # REGISTRY, register() (internal, avoids a circular import)
├── metadata.py                 # KPIMetadata, Aggregation, Direction, DigitalMaturity
├── naming.py                     # KPIIdentifier, parse_identifier, CONTROLLED_NAMESPACES
├── lifecycle.py                    # KPIStatus (Proposed -> Active -> Deprecated -> Retired)
├── base_kpi.py                       # BaseKPI (compute() orchestration, _compute() abstract)
├── composite.py                        # CompositeKPI (combine(), _combine() abstract)
├── inheritance.py                        # specialize() (PROD.TPH.Ore-style specialization)
├── result.py                               # KPIResult (to_frame/plot/pareto)
├── engine.py                                 # KPIEngine (orchestration only, AD-KP-01)
├── dependency_graph.py                         # DependencyGraph (topological_order, detect_cycle)
├── aggregation.py                                # combine_results (RATIO-never-averaged rule)
├── windowing.py                                    # Window, RollingWindow, CumulativeWindow
├── caching.py                                        # ResultCache
├── validation.py                                       # KPIValidator (canonical time-model check)
├── certification.py                                      # CertificationFixture, run_certification_fixture
├── exceptions.py                                           # the kpis exception hierarchy
├── categories/                                               # nine namespace-family base classes
│   ├── _common.py                                              # enforce_namespace (shared)
│   └── production_kpi.py, utilization_kpi.py, maintenance_kpi.py, haulage_kpi.py,
│       delay_kpi.py, energy_kpi.py, quality_kpi.py, cost_kpi.py, safety_kpi.py
├── backends/                                                   # pluggable ExecutionBackend strategies
│   ├── base_backend.py                                           # ExecutionBackend ABC
│   ├── pandas_backend.py                                           # PandasBackend (default)
│   ├── numpy_backend.py, polars_backend.py, duckdb_backend.py
├── standard_library/                                           # the 12-KPI reference implementation
│   └── production.py, utilization.py, maintenance.py, haulage.py, delay.py,
│       energy.py, quality.py, cost.py, safety.py
└── README.md                                                   # this file
```

## Dependency Rules

```
core → ontology → events → registry → kpis
```

- **`kpis` depends on:** `core`, `ontology`, `events`, `registry`.
- **`kpis` is depended on by:** future `analytics`, `decision`, `digital_twin` packages — never the reverse.
- **Forbidden (the single most load-bearing rule in this document):** `kpis` MUST NOT import `connectors`, `analytics`, `optimization`, `simulation`, `decision`, `digital_twin`, or `agents`. This is mechanically checked by `tests/unit/kpis/test_public_api.py::TestNoForbiddenDependencies`, including a dedicated `test_never_imports_connectors_specifically` check.

## Public API

```python
from mineproductivity.kpis import (
    REGISTRY, register,
    BaseKPI, CompositeKPI,
    ProductionKPI, UtilizationKPI, MaintenanceKPI, HaulageKPI, DelayKPI,
    EnergyKPI, QualityKPI, CostKPI, SafetyKPI,
    KPIMetadata, Aggregation, Direction, DigitalMaturity, KPIStatus,
    KPIIdentifier, parse_identifier,
    KPIResult,
    KPIEngine, DependencyGraph,
    ResultCache,
    Window, RollingWindow, CumulativeWindow,
    KPIValidationError, KPINotFoundError, KPICircularDependencyError,
    KPIAggregationError, KPIVersionConflictError,
)
```

Every flagship in the 12-KPI Standard Library (`TonnesPerHour`, `PhysicalAvailability`, `OverallEquipmentEffectiveness`, ...) is registered into `REGISTRY` automatically at import time (`"PROD.TPH" in REGISTRY` is `True` with no setup) — but, matching the design specification's own §8 list, is deliberately **not** re-exported at the top level. Look them up by code via `REGISTRY.get("PROD.TPH")`, or import the concrete class directly from `mineproductivity.kpis.standard_library.production`. `ExecutionBackend` and its four implementations live under `mineproductivity.kpis.backends`; `KPIValidator`/`CertificationFixture` under `mineproductivity.kpis.validation`/`.certification` (design spec §9 — internal-API-documented, not top-level-exported, symbols).

## Extension Guide

**Adding a new KPI.** Subclass the matching category base, declare `meta`, implement `_compute`, decorate with `@register`:

```python
from typing import ClassVar
from mineproductivity.kpis import register
from mineproductivity.kpis.categories.maintenance_kpi import MaintenanceKPI
from mineproductivity.kpis.metadata import Aggregation, Direction, DigitalMaturity, KPIMetadata

@register
class MeanTimeBetweenFailures(MaintenanceKPI):
    meta: ClassVar[KPIMetadata] = KPIMetadata(
        code="MAINT.MTBF", name="Mean Time Between Failures", official_name="Mean Time Between Failures",
        business_purpose="...", operational_question="...", business_meaning="...",
        formula="sum(operating_h) / count(failures)", unit="h",
        dimensions=("Shift", "Equipment"), required_events=("MAINTENANCE",),
        aggregation=Aggregation.AVERAGE, direction=Direction.HIGHER_IS_BETTER,
        min_maturity=DigitalMaturity.L2_FMS, leading_or_lagging="lagging",
        operational_or_strategic="operational",
    )

    def _required_columns(self) -> tuple[str, ...]:
        return ("duration_h",)

    def _compute(self, rows):
        ...
```

A malformed `code`, an already-registered code, or a completed dependency cycle each raise immediately at class-definition/registration time — never deferred to first `KPIEngine.execute()` call.

**Adding a KPI specialization** (e.g. `PROD.TPH.Ore`), reusing a parent's `_compute` with a material filter:

```python
from mineproductivity.kpis.inheritance import specialize
from mineproductivity.kpis.standard_library.production import TonnesPerHour

ore_tph = specialize(TonnesPerHour, code="PROD.TPH.Ore", material_filter="ore")
```

**Switching the active `ExecutionBackend`** (process-level, e.g. to `DuckDBBackend` for a fleet-scale batch job):

```python
from mineproductivity.kpis.backends import DuckDBBackend, set_active_backend

set_active_backend(DuckDBBackend())
```

## Examples

Runnable, narrated scripts live in [`examples/kpis/`](../../../examples/kpis/README.md); a beginner-tier walkthrough lives in [`notebooks/beginner/01_first_kpi_lookup.ipynb`](../../../notebooks/beginner/01_first_kpi_lookup.ipynb).

| Script | Demonstrates |
|---|---|
| `01_simple_execution.py` | `PROD.TPH` end to end: resolve, scan, compute, inspect provenance, export to a DataFrame. |
| `02_composite_oee.py` | `UTIL.OEE`'s dependency graph resolved automatically; `None` propagation when a dependency has no data. |
| `03_batch_summary.py` | Nine KPIs across every category, computed in a single `summary()` call. |
| `04_discovery.py` | `REGISTRY` introspection: list, filter by namespace, filter composite-vs-leaf, fully describe a KPI. |

## Design Rationale

- **Why is `KPIMetadata.code` a required positional field, not defaulted?** A KPI with no identifier is a specification gap, not a valid partial object — mirrors `core.BaseMetadata.name`'s own required-positional-field contract.
- **Why does `enforce_namespace` accept more than one namespace?** The design specification itself describes some categories as spanning several controlled namespaces (`EnergyKPI` covers `ENERGY`/`CARBON`/`WATER`; `QualityKPI` covers `QUAL`/`GRADE`; `SafetyKPI` covers `SAFE`/`AUTO`); a single-namespace check would have made those categories unimplementable as specified.
- **Why does `DelayKPI` use only the `DISP` namespace, not `DELAY`?** Design spec §10.4's prose describes "DELAY/DISP," but §20's controlled namespace list — the one `parse_identifier`/`enforce_namespace` actually validate against — contains only `DISP`. The controlled list governs identifier validation; the prose description does not. See `categories/delay_kpi.py`'s module docstring for the full resolution.
- **Why is `ExecutionBackend.assemble()` `(rows, columns) -> table` instead of the design spec's illustrative `(query, columns) -> table`?** Store-querying is an `events`-specific concern already owned by `KPIEngine` (which holds the `EventStore`); duplicating query execution once per backend implementation would violate DRY and blur backend responsibility. Backends stay focused on tabular manipulation — assembly, grouping, pandas export — their own specialty.
- **Why does `KPIValidator`'s canonical time-model check skip `CompositeKPI` subclasses?** A composite's own formula composes other KPI *codes'* results (e.g. `UTIL.OEE`'s `UTIL.PA * UTIL.UA * UTIL.Performance`), not raw hour fields directly — each dependency is independently validated when it is itself registered. Checking a composite's formula string for `scheduled_h`/`available_h`/`operating_h`/`calendar_h` substrings would be a false negative for every legitimate composite, `UTIL.OEE` included.
- **Why does `UTIL.OEE` multiply only three factors (PA × UA × Performance), not the classic four-factor Availability × Performance × Quality?** No dedicated grade/reject-rate event stream is part of this milestone's canonical `events` catalogue yet; this is documented in `OverallEquipmentEffectiveness`'s own docstring as a valid three-factor formulation, with `QUAL.OreProportion` offered as a standalone, grade-adjacent ratio computed from what *is* available today.
- **Why does `COST.FuelPerTonne` declare `dependencies=("PROD.TPH",)` yet never read `PROD.TPH`'s computed value?** A non-composite KPI receives only raw rows from `BaseKPI.compute` — never a dependency's already-computed `KPIResult` (only `CompositeKPI.combine` does). The declared dependency documents the Standard Library's own thematic/DAG grouping (ensuring `PROD.TPH` is computed and cache-warmed alongside it), while `_compute` still re-derives its own ratio directly from the union of `CONSUMPTION`/`CYCLE` rows.
- **Why does `KPIEngine.rows_for` round-trip every row through the active `ExecutionBackend`'s `assemble()`/`to_rows()` even for a single-KPI request?** This is the mechanical proof of backend parity (design spec §29): swapping the active backend never changes the row *data* a `_compute` implementation sees, only how it was vectorized in transit.
- **Why is `ResultCache`'s key `(code, window, scope, fingerprint)` rather than a time-based TTL?** `fingerprint` (the matching envelope count) is a cheap, correct proxy for "has anything relevant changed" — the cache key naturally changes the moment a new matching event lands, giving the design spec §22 "invalidated automatically, never silently stale" guarantee without a new versioning API on the locked `EventStore` contract.

## Anti-Patterns

- ❌ **Averaging per-shift `RATIO`-aggregation results** instead of re-deriving from the union of raw rows (design spec §10.8, §19, §29) — the single most-cited mistake across the entire Standard Library. `aggregation.combine_results` raises `KPIAggregationError` structurally rather than merely discouraging this by convention.
- ❌ **A `UtilizationKPI` denominator outside the canonical ladder** (`calendar_h ⊇ scheduled_h ⊇ available_h ⊇ operating_h`). `KPIValidator` rejects this at registration time for every leaf `UtilizationKPI`.
- ❌ **A composite KPI fabricating a zero when a dependency has no value.** `CompositeKPI.combine()` propagates `None` with a warning the moment any declared dependency's value is `None`, before `_combine()` is ever called.
- ❌ **Editing `engine.py` to add a metric-specific branch.** A new KPI is always added entirely in `standard_library/` (or a plugin package); the engine's own zero-metric-logic invariant is mechanically checked by `tests/unit/kpis/test_public_api.py::TestEngineHoldsNoMetricLogic`.
- ❌ **Re-registering an existing `Active` code with different semantics.** `register()` raises `KPIVersionConflictError` — a genuine new meaning requires a MAJOR version bump under review, never silent re-registration.
- ❌ **Catching `Exception` instead of the `kpis` exception hierarchy** when handling a KPI failure. Every exception this package raises derives from `core.MineProductivityError`, `core.ValidationError`, `core.NotFoundError`, or `registry.RegistrationError` specifically so callers do not need a broad `except Exception`.

## Testing & Quality

- `tests/unit/kpis/` mirrors `src/mineproductivity/kpis/` 1:1 — **100% line coverage**.
- Backend parity tests (`tests/unit/kpis/backends/test_backend_parity.py`): identical `KPIResult.value` across all four `ExecutionBackend`s for every implemented leaf KPI, and identical `group_and_aggregate` output.
- The exact Cookbook Part I Ch. 6 ratio-correctness worked numbers (A-shift 1,300 t/h over 12h + B-shift 1,100 t/h over 6h → combined 1,233.3 t/h, not the naive 1,200 average) are proven at both the row level (`test_engine.py::TestRatioNeverAveraged`) and the aggregation-refusal level (`test_aggregation.py`).
- `tests/integration/test_kpi_pipeline.py` — the full CSV → canonical events → `EventStore` → `KPIEngine` pipeline, no stage bypassed, against the golden dataset in `tests/fixtures/kpis/`.
- `mypy --strict` and `ruff` are clean on `src/mineproductivity/kpis/` and `examples/kpis/`.

## Contents

See [Package Structure](#package-structure) above for the full file layout.

## Dependencies

**Depends on:** `core`, `ontology`, `events`, `registry`. Optionally, `numpy`/`pandas`/`polars`/`duckdb` (the `analytics` extra) for the non-default `ExecutionBackend`s — `pandas` alone is required for the default `PandasBackend` and `KPIResult.to_frame()`.

**Depended on by:** nothing yet in this milestone; future `analytics`, `decision`, and `digital_twin` packages will consume `kpis` for their own computations.

## Future Work

- A fourth, Quality-factor OEE variant once a grade/reject-rate event stream joins the canonical `events` catalogue.
- `KPIEngineConfiguration`/`ResultCacheConfiguration` as `core.BaseConfiguration` subclasses, once the cross-cutting `config` package exists.
- Database-backed `EventStore` implementations exercised against the same `KPIEngine.rows_for` contract, once `connectors` grows a database/historian adapter.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
- [`docs/architecture/05_KPI_Engine_Design_Specification.md`](../../../docs/architecture/05_KPI_Engine_Design_Specification.md)
- [`docs/design/05_KPI_Implementation_Checklist.md`](../../../docs/design/05_KPI_Implementation_Checklist.md)
- Developer & Cookbook Guide Part I, Chapter 4 ("The Query Layer") and Chapter 6 ("Your First KPI")
- Developer & Cookbook Guide Part III, the KPI Standard Library (29-field template, Canonical Semantics, KPI Naming Standard)
