# MineProductivity

**A metadata-first, ontology-driven, event-sourced platform for mining productivity
intelligence - KPI computation, digital twins, decision support, and AI agents,
built on a clean, plugin-first Python architecture.**

[![DOI](https://zenodo.org/badge/1286272754.svg)](https://doi.org/10.5281/zenodo.21172767)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](pyproject.toml)
[![Status](https://img.shields.io/badge/status-pre--alpha-orange.svg)](ROADMAP.md)
[![Version](https://img.shields.io/badge/version-0.7.2-lightgrey.svg)](CHANGELOG.md)

> **Status: Incremental Implementation.** `core` (framework primitives), `events`
> (the Event Sourcing model), `ontology` (the typed domain vocabulary),
> `registry`/`plugins` (the plugin-first discovery-and-lifecycle backbone),
> `connectors` (the vendor-neutral ingestion boundary), and `kpis` (the
> metadata-first, self-describing KPI Engine) are implemented, tested
> (100% line coverage), and documented. Every other package remains a
> structural placeholder, built incrementally guided by the locked
> architecture documents described below. Every directory in this tree mirrors
> an approved section of the Master Architecture Handbook and the Reference
> Implementation Blueprint.

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

**Version 0.7.2.** The architecture is versioned v1.0 (locked,
documentation-complete). The software is versioned independently, starting at
`0.1.0`, and will only reach `1.0.0` once the reference implementation
satisfies the Reference Implementation Blueprint and passes the Certification
suite. Implemented so far: `core` (v0.2.0), `events` (v0.3.0), `ontology`
(v0.4.0), `registry`/`plugins` (v0.5.0), `connectors` (v0.6.0), `kpis`
(v0.7.0); v0.7.1 and v0.7.2 are packaging- and documentation-validation
patch releases (no new functionality). See [CHANGELOG.md](CHANGELOG.md) and
[ROADMAP.md](ROADMAP.md).

## Getting Started

### Installing

MineProductivity requires Python 3.12+. It is not yet published to PyPI; install
directly from GitHub or from a local checkout.

```bash
# From GitHub (latest main)
pip install git+https://github.com/imanojkumar/MineProductivity.git

# From a local checkout
git clone https://github.com/imanojkumar/MineProductivity.git
cd MineProductivity
pip install .
```

The base install has zero third-party dependencies and gives you `core`, `events`,
`ontology`, `registry`, `plugins`, `connectors`, and `kpis`. Optional dependency
groups add capability only where you need it:

| Extra | Adds | Needed for |
|---|---|---|
| `events` | `pyarrow` | Parquet/Arrow event codecs |
| `connectors` | `openpyxl`, `tzdata` (Windows) | `ExcelConnector`, local-timezone normalization |
| `analytics` | `numpy`, `pandas`, `polars`, `duckdb` | KPI Engine execution backends, `KPIResult.to_frame()` |
| `notebooks` | `jupyter`, `ipykernel` | Running the notebooks in `notebooks/` |
| `dev` | everything above, plus `pytest`, `ruff`, `mypy`, `pre-commit` | Contributing |

```bash
pip install "mineproductivity[analytics] @ git+https://github.com/imanojkumar/MineProductivity.git"
```

Verify the install:

```python
import mineproductivity
print(mineproductivity.__version__)

from mineproductivity.kpis import REGISTRY
tph = REGISTRY.get("PROD.TPH")().compute([{"payload_t": 220.0, "operating_h": 12.0}])
print(tph.value, tph.unit)  # 18.33... t/h
```

### Contributing

To set up a development environment for contributing:

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

If you use MineProductivity in research or industrial projects, please cite:

Kumar, M. (2026).

MineProductivity (Version v0.7.0).

Zenodo.

https://doi.org/10.5281/zenodo.21172768

See [CITATION.cff](CITATION.cff).
