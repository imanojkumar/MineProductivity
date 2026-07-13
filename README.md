# MineProductivity &nbsp;&nbsp;&nbsp; [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21172767.svg)](https://doi.org/10.5281/zenodo.21172767)


**MineProductivity is an enterprise-grade, ontology-driven Python framework for mining productivity intelligence, KPI standardization, Digital Twins, simulation, optimization, AI decision support, and operational analytics.**

[![CI](https://github.com/imanojkumar/MineProductivity/actions/workflows/ci.yml/badge.svg)](https://github.com/imanojkumar/MineProductivity/actions/workflows/ci.yml)
[![Quality](https://github.com/imanojkumar/MineProductivity/actions/workflows/quality.yml/badge.svg)](https://github.com/imanojkumar/MineProductivity/actions/workflows/quality.yml)
[![CodeQL](https://github.com/imanojkumar/MineProductivity/actions/workflows/codeql.yml/badge.svg)](https://github.com/imanojkumar/MineProductivity/actions/workflows/codeql.yml)
[![GitHub release](https://img.shields.io/github/v/release/imanojkumar/MineProductivity)](https://github.com/imanojkumar/MineProductivity/releases)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](pyproject.toml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-stable-brightgreen.svg)](ROADMAP.md)



> **Status: Architecture complete and locked — certified `v2.0.0`.** All
> eleven domain packages of the locked architecture —
> `core → ontology → events → kpis → analytics → decision → digital_twin
> → simulation → optimization → agents → visualization` — plus the three
> cross-cutting infrastructure packages (`registry`, `plugins`,
> `connectors`) are implemented, tested (2,986 passing tests, `mypy
> --strict` clean across 314 source files), documented, and released. The
> public APIs are stable by contract as of `v2.0.0`. New value now ships as
> plugins and applications, not as changes to the locked packages. Every
> directory in this tree mirrors an approved section of the Master
> Architecture Handbook and the Reference Implementation Blueprint.

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


## Current Development Phase

> Architecture maturity: ██████████ 100%

> Implementation maturity: ██████████ 100%

> Foundation (core → kpis) ████████████████████████████ 100%

> Analytics Engine ████████████████████████████ 100%

> Decision Intelligence ████████████████████████████ 100%

> Digital Twin ████████████████████████████ 100%

> Simulation ████████████████████████████ 100%

> Optimization ████████████████████████████ 100%

> AI Agents ████████████████████████████ 100%

> Visualization ████████████████████████████ 100%

> Certification (v2.0.0) ████████████████████████████ 100% (certified)




## Repository Structure

```
MineProductivity/
├── docs/                    # Architecture, blueprint, developer guide, learning suite
├── src/mineproductivity/    # The installable Python package (24 subsystems)
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

## Architecture Progress

| Package | Architecture | Implementation |
|----------|--------------|----------------|
| Core | ✅ | ✅ |
| Events | ✅ | ✅ |
| Ontology | ✅ | ✅ |
| Registry | ✅ | ✅ |
| Plugins | ✅ | ✅ |
| Connectors | ✅ | ✅ |
| KPI Engine | ✅ | ✅ |
| Analytics | ✅ | ✅ |
| Decision Intelligence | ✅ | ✅ |
| Digital Twin | ✅ | ✅ |
| Simulation | ✅ | ✅ |
| Optimization | ✅ | ✅ |
| AI Agents | ✅ | ✅ |
| Visualization | ✅ | ✅ |

> **Legend.** Architecture: ✅ locked design spec + checklist + ADR. Implementation: ✅ implemented, tested, and released as a versioned milestone. Every package in the locked architecture is implemented and released; the platform is certified at **v2.0.0** (see [`docs/certification/2.0-certification.md`](docs/certification/2.0-certification.md)). A future conformance-suite package (Phase 7 `certification`) remains a documented placeholder — see [ROADMAP.md](ROADMAP.md) and [`docs/adr/ADR-0013-Placeholder-Package-Rationalization.md`](docs/adr/ADR-0013-Placeholder-Package-Rationalization.md).


## Architecture Roadmap


| Foundation |
|----------|
| ✅ Core |
| ✅ Events |
| ✅ Ontology |
| ✅ Registry |
| ✅ Plugins |
| ✅ Connectors |
| ✅ KPI Engine |


| Intelligence |
|----------|
| ✅ Analytics |
| ✅ Decision Intelligence |
| ✅ Digital Twin |
| ✅ Simulation |
| ✅ Optimization |
| ✅ AI Agents |
| ✅ Visualization |


| Post-v2.0 (optional, plugin/application layer) |
|----------|
| ⏳ Conformance-suite package (Phase 7 `certification`) |
| ⏳ CLI application (`cli`) |


## Architectural Layering & Dependency Direction

MineProductivity enforces a strict, inward-pointing dependency direction. Lower
layers must never import from higher layers. For every implemented package,
this is mechanically enforced, not just documented: each package's own
`tests/unit/<package>/test_public_api.py::TestNoForbiddenDependencies` AST
-walks every submodule and fails the build on a forbidden cross-layer import
(see each package's own README, e.g.
[`src/mineproductivity/kpis/README.md`](src/mineproductivity/kpis/README.md#dependency-rules)'s
"Dependency Rules" section). The layering itself:

```
                     ┌───────────────────┐
                     │   visualization   │
                     ├───────────────────┤
                     │       agents      │
                     ├───────────────────┤
                     │    optimization   │
                     ├───────────────────┤
                     │     simulation    │
                     ├───────────────────┤
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
   (core has no dependencies on any other MineProductivity package;
   visualization is the final package — nothing depends on it)
```

Cross-cutting packages (`config`, `io`, `utils`, `exceptions`, `registry`,
`plugins`, `validation`, `cli`) may be depended upon by any layer, but must
never depend on `kpis`, `analytics`, `decision`, `digital_twin`, `simulation`,
`optimization`, `agents`, `visualization`, or `connectors`.

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

**Current Stable Release: v2.0.0**

Enterprise Certification — architecture complete and locked, public APIs stable by contract
Production Ready

**Completed milestones:**

| Version | Milestone | Status |
|---------|-----------|--------|
| v0.2.0 | Core Framework | ✅ Implemented |
| v0.3.0 | Event Framework | ✅ Implemented |
| v0.4.0 | Ontology Framework | ✅ Implemented |
| v0.5.0 | Registry & Plugin Framework | ✅ Implemented |
| v0.6.0 | Connector Framework | ✅ Implemented |
| v0.7.0 | KPI Engine | ✅ Implemented |
| v0.8.0 | Analytics Engine Architecture | ✅ Architecture Complete |
| v0.9.0 | Decision Intelligence Architecture | ✅ Architecture Complete |
| v1.0.0 | Digital Twin Architecture | ✅ Architecture Complete |
| v1.1.0 | Simulation Architecture | ✅ Architecture Complete |
| v1.2.0 | Optimization Architecture | ✅ Architecture Complete |
| v1.3.0 | AI Agents Architecture | ✅ Architecture Complete |
| v1.4.0 | Visualization Architecture | ✅ Architecture Complete |
| v1.5.0 | Analytics Engine Implementation | ✅ Implemented |
| v1.6.0 | Decision Intelligence Implementation | ✅ Implemented |
| v1.7.0 | Digital Twin Implementation | ✅ Implemented |
| v1.8.0 | Simulation Implementation | ✅ Implemented |
| v1.9.0 | Optimization Implementation | ✅ Implemented |
| v1.10.0 | AI Agents Implementation | ✅ Implemented |
| v1.11.0 | Visualization Implementation | ✅ Implemented |
| v2.0.0 | Enterprise Certification — architecture complete & locked | ✅ Certified |

## What's New in v2.0.0

`v2.0.0` is the **enterprise certification milestone: a stability declaration with zero breaking changes.** Every package in the locked architecture (`core → … → visualization`, plus `registry`/`plugins`/`connectors`) is implemented, released, documented, and exercised by examples and benchmarks. The public APIs are now **stable by contract** — they will not change incompatibly without a further MAJOR bump.

**Highlights:**

- The full architecture is complete and locked; `optimization` (v1.9.0), `agents` (v1.10.0), and `visualization` (v1.11.0) completed the chain, and v2.0.0 certifies it
- Public APIs stable by contract; new value ships as plugins (solver adapters, reasoning backends, renderers, connector adapters) and applications, never as changes to the locked packages
- Repository is fully **tool-neutral**; durable engineering rules live in [`docs/governance/ENGINEERING_RULES.md`](docs/governance/ENGINEERING_RULES.md)
- Repository-wide certification record in [`docs/certification/2.0-certification.md`](docs/certification/2.0-certification.md)

**Engineering Quality**

- 2,986 automated tests
- 99–100% coverage across the domain packages
- Cross-platform CI
- Automated GitHub Releases
- Strict typing (mypy `--strict`, 314 files clean)
- Ruff formatting and linting; 0 broken documentation links

See: 
 - [CHANGELOG.md](CHANGELOG.md) and 
 - [ROADMAP.md](ROADMAP.md)

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

### Next Steps

Installed and verified - now go **use** it:

| I want to... | Start here |
|---|---|
| See the whole platform in one script | [`examples/quickstart/01_five_minute_tour.py`](examples/quickstart/01_five_minute_tour.py) - one truck, one shift, one KPI, ~50 lines. |
| Follow a guided, cell-by-cell walkthrough | [`notebooks/beginner/01_first_kpi_lookup.ipynb`](notebooks/beginner/01_first_kpi_lookup.ipynb) (`pip install "mineproductivity[notebooks,analytics] @ git+..."` first). |
| Compute my first KPI | [`examples/kpis/01_simple_execution.py`](examples/kpis/01_simple_execution.py), then [`02_composite_oee.py`](examples/kpis/02_composite_oee.py), [`03_batch_summary.py`](examples/kpis/03_batch_summary.py), [`04_discovery.py`](examples/kpis/04_discovery.py). |
| Model equipment, fleets, and shifts | [`examples/ontology/01_equipment_modelling.py`](examples/ontology/01_equipment_modelling.py). |
| Ingest data from a real source | [`examples/connectors/01_csv_ingestion.py`](examples/connectors/01_csv_ingestion.py), [`02_rest_with_retry.py`](examples/connectors/02_rest_with_retry.py). |
| Record my first event | [`examples/events/01_first_event.py`](examples/events/01_first_event.py). |
| Understand how KPIs/connectors get discovered as plugins | [`examples/registry/01_register_and_discover.py`](examples/registry/01_register_and_discover.py) - the register → discover → lookup mechanism every domain package (and every third-party plugin) shares. |
| Read the full API of a specific package | that package's own `README.md`, e.g. [`src/mineproductivity/kpis/README.md`](src/mineproductivity/kpis/README.md). |

Every example above is a plain, runnable `.py` file with no test framework involved - `python examples/quickstart/01_five_minute_tour.py` and read along. [`examples/README.md`](examples/README.md) indexes all of them; [`notebooks/README.md`](notebooks/README.md) indexes the notebooks.

> **Looking for the Developer & Cookbook Guide?** It's one of the six locked
> SSOT documents this repository implements (see
> [Documentation](#documentation-single-source-of-truth) below) and is not
> yet transcribed into `docs/developer_guide/` in browsable form - that
> directory is still a placeholder. Until it is, the examples and package
> READMEs above are the actual, maintained, up-to-date documentation.

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

> Kumar, M. (2026). *MineProductivity*. Zenodo.
> https://doi.org/10.5281/zenodo.21172767

The DOI above is the **Concept DOI**, which always resolves to the latest published release.

For version-specific citations, see the Releases page or Zenodo.

See [`CITATION.cff`](CITATION.cff) for machine-readable citation metadata.


