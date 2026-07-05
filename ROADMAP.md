# Roadmap

MineProductivity's overall architecture (Master Architecture Handbook v1.0) is
locked and documentation-complete. The software implementing it is versioned
independently via [Semantic Versioning](https://semver.org/); the current
software release is `1.1.0` (see [`CHANGELOG.md`](CHANGELOG.md) for the full
milestone history). This roadmap tracks implementation phases against the
Reference Implementation Blueprint v1.0 and reflects the repository's actual,
current state — not a plan for a future not-yet-executed sequence.

Each phase below is one of three states: **Implemented** (real code, tested,
merged), **Architecture Complete** (a locked Design Specification,
Implementation Checklist, and ADR exist; no production code yet), or **Not
Started** (neither exists yet).

## Phase 0 — Repository Skeleton

**Status: Complete.**

- Full directory structure for `src/`, `tests/`, `docs/`, `datasets/`,
  `notebooks/`, `examples/`, `benchmark/`, `certification/`, `scripts/`.
- Packaging, governance, and CI/CD placeholders.
- Zero business logic.

## Phase 1 — Foundation Layer

**Status: Partially implemented.**

- `core` — **Implemented.** Base entities, value objects, identifiers.
- `ontology` — **Implemented.** Domain vocabulary and schema definitions.
- `registry`, `plugins` — **Implemented.** Extension mechanisms.
- `exceptions`, `config`, `utils`, `io` — **Not started.** Cross-cutting
  primitives; each remains a structural placeholder. (`core` defines its own
  internal exception hierarchy directly and does not currently depend on the
  separate top-level `exceptions` package.)

## Phase 2 — Event & KPI Layer

**Status: Partially implemented.**

- `events` — **Implemented.** Event schema, event store, event bus,
  replay/time-travel.
- `kpis` — **Implemented.** KPI metadata model and the standard KPI library
  (per Developer & Cookbook Guide — Part III).
- `validation` — **Not started.** Schema and data-quality validation
  framework; remains a structural placeholder.

## Phase 3 — Data & Connectivity Layer

**Status: Partially implemented.**

- `connectors` — **Implemented.** Source-system integration interfaces and
  six reference connectors, plus five documentation-only OEM adapter shapes.
- `datasets` — **Not started.** Dataset abstractions and canonical/golden
  dataset loaders; remains a structural placeholder. (The implemented `kpis`
  package uses its own, separate `tests/fixtures/kpis` sample-dataset loader
  in the meantime.)

## Phase 4 — Analytical Layer

**Status: Architecture complete for `analytics` and `simulation`; not
started for `optimization`.**

- `analytics` — **Architecture complete** (v0.8.0 milestone). Statistical and
  analytical processing built on `kpis`/`events`; interface-only
  forecasting/anomaly/outlier-detection models. Design Specification exists
  only on the unmerged `feature/analytics-engine` branch (see
  `ADR-0006-Analytics-Engine.md`).
- `simulation` — **Architecture complete** (v1.1.0 milestone). Scenario
  management, `SimulationRun` execution, interface-only Monte Carlo/
  discrete-event/system-dynamics/calibration models, experiment
  orchestration, scenario comparison and sensitivity analysis (delegated to
  `analytics`). See
  [`docs/architecture/09_Simulation_Design_Specification.md`](docs/architecture/09_Simulation_Design_Specification.md).
- `optimization` — **Not started.** No architecture specification or ADR
  exists yet.

## Phase 5 — Decision & Twin Layer

**Status: Architecture complete for `decision` and `digital_twin`; not
started for `agents`.**

- `decision` — **Architecture complete** (v0.9.0 milestone). Decision-support
  and recommendation frameworks that translate `analytics`' statistical
  judgments into actionable, explained recommendations.
- `digital_twin` — **Architecture complete** (v1.0.0 milestone). Stateful
  twin representation and event-driven synchronization.
- `agents` — **Not started.** No architecture specification or ADR exists
  yet.

## Phase 6 — Experience Layer

**Status: Not started.**

- `visualization` — dashboards and visual reporting. No architecture
  specification exists yet.
- `cli` — command-line interface. No architecture specification exists yet.

## Phase 7 — Quality & Certification

**Status: Not started** (as packages; lightweight standalone substitutes
already exist under `scripts/quality/`).

- `benchmark` — conformance/reference benchmark scenarios and reporting as a
  package remain a structural placeholder; `scripts/quality/perf_smoke.py`
  already provides a lightweight, standalone performance smoke test used by
  CI in the meantime.
- `certification` — conformance test suite and reference output validation;
  remains a structural placeholder.
- A `1.0`-line software release milestone tagged specifically for
  "Reference Implementation Blueprint fully satisfied, certification suite
  passing" has not yet been reached — see Versioning Policy below for how
  this differs from the software's own SemVer track, which has already
  passed `1.0.0` for unrelated reasons.

## Versioning Policy

- **Architecture documents** are versioned independently and are already
  locked at `v1.0` (Master Architecture Handbook, Reference Implementation
  Blueprint).
- **Software** follows [Semantic Versioning](https://semver.org/), starting
  at `0.1.0`. The single authoritative source is
  [`src/mineproductivity/__init__.py`](src/mineproductivity/__init__.py)'s
  `__version__`; `pyproject.toml` reads it dynamically and nothing else
  should hardcode it (tests compare against installed package metadata
  instead — see `tests/unit/core/test_public_api.py`).
- In practice, this repository has bumped the software's MINOR version once
  per completed architecture milestone (`v0.7.0` KPI Engine through `v1.1.0`
  Simulation) — a deliberate, precedented convention distinct from waiting
  for a certification-gated `1.0` release. Under this convention, the
  software's SemVer track and the "Phase 7 certification-gated 1.0"
  milestone described above are two different concepts that happen to share
  the digit `1.0`: the software already carries a version number at or past
  `1.0.0`, while the certification-gated milestone Phase 7 describes has not
  been reached. A future decision may rename or otherwise reconcile this
  overlap; until then, treat "software version" (SemVer, `CHANGELOG.md`) and
  "Reference Implementation Blueprint completion" (this roadmap's phases) as
  two independently-tracked measures of progress, not one.
