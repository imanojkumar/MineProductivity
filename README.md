# MineProductivity

**A metadata-first, ontology-driven, event-sourced platform for mining productivity
intelligence - KPI computation, digital twins, decision support, and AI agents,
built on a clean, plugin-first Python architecture.**

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](pyproject.toml)
[![Status](https://img.shields.io/badge/status-skeleton%20%2F%20pre--alpha-orange.svg)](ROADMAP.md)
[![Version](https://img.shields.io/badge/version-0.1.0-lightgrey.svg)](CHANGELOG.md)

> **Status: Repository Skeleton.** This repository currently contains **no business
> logic**. It is the structural foundation onto which the MineProductivity reference
> implementation will be built incrementally, package by package, guided by the
> locked architecture documents described below. Every directory in this tree
> mirrors an approved section of the Master Architecture Handbook and the
> Reference Implementation Blueprint.

## What is MineProductivity?

MineProductivity is an open-source platform for modeling, measuring, and improving
productivity across mining operations. It is designed from first principles to be:

- **Ontology-first** - a shared, explicit domain vocabulary (assets, processes,
  events, KPIs) precedes any code that operates on it.
- **Event-first** - the system of record is an immutable event stream; all
  derived state (KPIs, digital twins, analytics) is a projection of events.
- **Metadata-first** - every KPI, dataset, and model ships with machine-readable
  metadata (units, provenance, validity, versioning) before it ships with logic.
- **Plugin-first** - connectors, KPIs, analytics, and agents are discovered and
  loaded through a registry/plugin system, not hard-wired into the core.
- **Domain-Driven Design** - package boundaries mirror bounded contexts in the
  mining productivity domain, not incidental technical layers.
- **Clean Architecture** - dependencies point inward, toward `core` and
  `ontology`; outer layers (connectors, agents, visualization) depend on inner
  layers, never the reverse.
- **SOLID** - every package has a single, clearly documented responsibility
  (see each package's `README.md`).
- **Test-first** - `tests/` mirrors `src/` before implementation exists, and
  every implementation PR is expected to arrive with tests.
- **Documentation-first** - the Master Architecture Handbook, Reference
  Implementation Blueprint, and Developer & Cookbook Guides are the Single
  Source of Truth (SSOT); code implements documentation, not the reverse.

## Repository Structure

```
MineProductivity/
├── docs/                    # Architecture, blueprint, developer guide, learning suite
├── src/mineproductivity/    # The installable Python package (22 subsystems)
├── tests/                   # Unit, integration, performance, regression, golden tests
├── datasets/                # Canonical, generated, golden, benchmark, synthetic data
├── notebooks/               # Beginner → research-grade learning notebooks
├── examples/                # Runnable usage examples, from quickstart to production
├── benchmark/               # Benchmark scenarios and reference outputs
├── certification/           # Conformance / certification test suite
├── scripts/                 # Bootstrap, development, release, and quality tooling
└── .github/                 # CI/CD workflow placeholders, templates, ownership
```

See [`docs/architecture/README.md`](docs/architecture/README.md) for the full
architectural rationale behind this layout.

## Architectural Layering & Dependency Direction

MineProductivity enforces a strict, inward-pointing dependency direction. Lower
layers must never import from higher layers. This is documented (not yet
mechanically enforced - see [Dependency Rules](docs/architecture/README.md#dependency-rules))
as follows:

```
                     ┌───────────────────┐
                     │   digital_twin    │
                     ├───────────────────┤
                     │     decision      │
                     ├───────────────────┤
                     │     analytics     │
                     ├───────────────────┤
                     │       kpis        │
                     ├───────────────────┤
                     │      events       │
                     ├───────────────────┤
                     │      ontology     │
                     ├───────────────────┤
                     │        core       │
                     └───────────────────┘
   (core has no dependencies on any other MineProductivity package)
```

Cross-cutting packages (`config`, `io`, `utils`, `exceptions`, `registry`,
`plugins`, `validation`, `cli`) may be depended upon by any layer, but must
never depend on `kpis`, `analytics`, `decision`, `digital_twin`, `agents`,
`connectors`, `optimization`, or `simulation`.

## Documentation (Single Source of Truth)

This repository is the implementation vessel for six locked documents:

1. **Master Architecture Handbook v1.0**
2. **Reference Implementation Blueprint v1.0**
3. **Developer & Cookbook Guide - Part I**
4. **Developer & Cookbook Guide - Part II**
5. **Developer & Cookbook Guide - Part III** (KPI Standard Library & Cookbook)
6. **Learning & Benchmark Suite v1.0**

These documents are not stored in this repository verbatim; `docs/` contains
structured, versioned notes and placeholders that mirror their sections. See
[`docs/README.md`](docs/README.md) for the documentation map.

## Engineering Philosophy

| Principle | What it means here |
|---|---|
| Clean Architecture | Dependencies point inward; `core`/`ontology` know nothing about `connectors`, `agents`, or `visualization`. |
| Domain-Driven Design | Package names are domain concepts (`kpis`, `digital_twin`, `decision`), not technical layers (`services`, `helpers`, `managers`). |
| SOLID | Each package has one reason to change; extension happens via `plugins`/`registry`, not by editing `core`. |
| Plugin-first | New KPIs, connectors, analytics, and agents are registered, not hard-coded. |
| Event-first | Events are the immutable source of truth; everything else is a derived, rebuildable projection. |
| Metadata-first | No KPI or dataset ships without units, provenance, and versioning metadata. |
| Ontology-first | Domain concepts are defined in `ontology` before any package is allowed to model them in code. |
| Test-first | `tests/` structure exists ahead of implementation; every package README defines its test philosophy. |
| Documentation-first | The locked SSOT documents govern structure; this README and every package README describe intent before code exists. |

## Project Status

**Version 0.1.0 - Skeleton.** The architecture is versioned v1.0 (locked,
documentation-complete). The software is versioned independently, starting at
`0.1.0`, and will only reach `1.0.0` once the reference implementation
satisfies the Reference Implementation Blueprint and passes the Certification
suite. See [ROADMAP.md](ROADMAP.md).

## Getting Started

There is no functionality to run yet. To set up a development environment for
contributing to the skeleton or a future implementation PR:

```bash
python -m venv .venv
source .venv/bin/activate      # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
pre-commit install
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow.

## License

Apache License 2.0 - see [LICENSE](LICENSE).

## Citation

See [CITATION.cff](CITATION.cff).
