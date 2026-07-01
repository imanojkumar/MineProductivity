# Roadmap

MineProductivity's architecture (v1.0) is locked and documentation-complete.
The software implementing it is versioned independently, starting from
`0.1.0`. This roadmap tracks implementation phases against the Reference
Implementation Blueprint v1.0.

## Phase 0 — Repository Skeleton (Current)

**Status: Complete.**

- Full directory structure for `src/`, `tests/`, `docs/`, `datasets/`,
  `notebooks/`, `examples/`, `benchmark/`, `certification/`, `scripts/`.
- Packaging, governance, and CI/CD placeholders.
- Zero business logic.

## Phase 1 — Foundation Layer

- `core`: base entities, value objects, identifiers.
- `ontology`: domain vocabulary and schema definitions.
- `exceptions`, `config`, `utils`, `io`: cross-cutting primitives.
- `registry`, `plugins`: extension mechanisms.

## Phase 2 — Event & KPI Layer

- `events`: event schema, event store interfaces.
- `kpis`: KPI metadata model and the standard KPI library (per Developer &
  Cookbook Guide — Part III).
- `validation`: schema and data-quality validation framework.

## Phase 3 — Data & Connectivity Layer

- `datasets`: dataset abstractions and canonical/golden dataset loaders.
- `connectors`: source-system integration interfaces and reference connectors.

## Phase 4 — Analytical Layer

- `analytics`: statistical and analytical processing built on `kpis`/`events`.
- `optimization`: optimization models and solvers.
- `simulation`: simulation engines.

## Phase 5 — Decision & Twin Layer

- `digital_twin`: state representation and twin synchronization.
- `decision`: decision-support and recommendation frameworks.
- `agents`: AI agent orchestration built atop the decision layer.

## Phase 6 — Experience Layer

- `visualization`: dashboards and visual reporting.
- `cli`: command-line interface.

## Phase 7 — Quality & Certification

- `benchmark`: implemented benchmark scenarios and reporting.
- `certification`: conformance test suite and reference output validation.
- 1.0.0 release candidate once the full Reference Implementation Blueprint
  is satisfied and the certification suite passes.

## Versioning Policy

- Architecture documents: versioned independently (`v1.0`, locked).
- Software: [Semantic Versioning](https://semver.org/), starting at `0.1.0`.
- `1.0.0` will not be tagged until the certification suite (Phase 7) passes
  in full.
