<p align="center">
  <img src="docs/images/github_logo.png" width="300" alt="MineProductivity Logo">
</p>

<div align="center">

# MineProductivity

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21172767.svg)](https://doi.org/10.5281/zenodo.21172767)

**Enterprise-grade ontology-driven framework for mining productivity intelligence, KPI standardization, Digital Twins, simulation, optimization, AI decision support, and operational analytics.** 

[![PyPI](https://img.shields.io/pypi/v/mineproductivity?color=blue)](https://pypi.org/project/mineproductivity/)
[![Python](https://img.shields.io/pypi/pyversions/mineproductivity)](https://pypi.org/project/mineproductivity/)
[![Docs](https://img.shields.io/badge/docs-latest-blue)](https://imanojkumar.github.io/MineProductivity/)
[![Release](https://img.shields.io/github/v/release/imanojkumar/MineProductivity)](https://github.com/imanojkumar/MineProductivity/releases)
[![CI](https://github.com/imanojkumar/MineProductivity/actions/workflows/ci.yml/badge.svg)](https://github.com/imanojkumar/MineProductivity/actions/workflows/ci.yml)
[![CodeQL](https://github.com/imanojkumar/MineProductivity/actions/workflows/codeql.yml/badge.svg)](https://github.com/imanojkumar/MineProductivity/actions/workflows/codeql.yml)
[![License](https://img.shields.io/pypi/l/mineproductivity?color=blue)](LICENSE)


[**Documentation**](https://imanojkumar.github.io/MineProductivity/) · [**Quick Start**](#quick-start) · [Examples](examples/README.md) · [Architecture](https://imanojkumar.github.io/MineProductivity/architecture/README/) · [Changelog](CHANGELOG.md)

</div>

---

MineProductivity turns raw mine-site events into **governed KPIs, digital twins, simulations, optimized plans, and audited decisions** - through one coherent, plugin-first architecture. Every performance indicator is a discoverable, versioned, self-describing object rather than a formula buried in a script.

The base install has **zero third-party dependencies**; every heavy backend (numpy, pandas, pyarrow, …) is opt-in.

```bash
pip install mineproductivity
```

## Why MineProductivity?

- **🧭 Ontology-first** - a shared, explicit domain vocabulary (assets, processes, events, KPIs) precedes any code that operates on it.
- **⏳ Event-first** - the system of record is an immutable event stream; all derived state (KPIs, twins, analytics) is a rebuildable projection.
- **🏷️ Metadata-first** - every KPI, dataset, and model ships with machine-readable metadata (units, provenance, versioning) before it ships with logic.
- **🔌 Plugin-first** - connectors, KPIs, analytics, solvers, agents, and renderers are discovered through a registry, never hard-wired into the core.
- **🧱 Clean, layered architecture** - 14 packages whose inward-pointing dependency direction is *mechanically enforced* (both ways) by tests, not just documented.
- **✅ Enterprise quality** - **2,986 tests**, `mypy --strict` clean across **314 files**, **99% branch coverage**, and public APIs **stable by contract** as of `v2.0.0`.

## Who is this for?

> - Mining companies
> - Researchers
> - Universities
> - Consultants
> - Software developers

## Installation

```bash
pip install mineproductivity
```

Optional dependency groups add capability only where you need it:

| Extra | Adds | Needed for |
|---|---|---|
| `analytics` | `numpy`, `pandas`, `polars`, `duckdb` | KPI Engine execution backends, `KPIResult.to_frame()` |
| `events` | `pyarrow` | Parquet/Arrow event codecs |
| `connectors` | `openpyxl`, `tzdata` (Windows) | `ExcelConnector`, local-timezone normalization |
| `notebooks` | `jupyter`, `ipykernel` | Running the learning notebooks |
| `dev` | the above + `pytest`, `ruff`, `mypy`, `pre-commit` | Contributing |

```bash
pip install "mineproductivity[analytics]"
```

Requires **Python 3.12+**.

## Quick Start

Every KPI is a governed, discoverable object - look it up by its identifier and compute it:

```python
from mineproductivity.kpis import REGISTRY

# Tonnes per hour for one truck over one shift.
tph = REGISTRY.get("PROD.TPH")().compute([{"payload_t": 220.0, "operating_h": 12.0}])
print(tph.value, tph.unit)   # 18.33... t/h
```

Discover what the Standard Library ships:

```python
from mineproductivity.kpis import REGISTRY

print(len(REGISTRY), "KPIs available")
for code in sorted(REGISTRY):
    print(code)
```

Want the whole platform end-to-end - one truck, one shift, one KPI, in ~50 lines? Run the [five-minute tour](examples/quickstart/01_five_minute_tour.py), or read the [Quick Start guide](https://imanojkumar.github.io/MineProductivity/getting-started/quick-start/).

## The platform

Work flows up a strict, inward-pointing dependency chain - lower layers never import higher ones:

```
core → ontology → events → kpis → analytics → decision
     → digital_twin → simulation → optimization → agents → visualization
```

plus three cross-cutting infrastructure packages (`registry`, `plugins`, `connectors`) importable by any layer.

| Tier | Packages | What they do |
|---|---|---|
| **Foundation** | `core` · `ontology` · `events` · `kpis` | Primitives, the typed domain vocabulary, the event-sourced system of record, and the metadata-first KPI Engine. |
| **Intelligence** | `analytics` · `decision` · `digital_twin` · `simulation` · `optimization` · `agents` · `visualization` | Statistical characterization, prescriptive recommendations, stateful representation, projection, prescriptive search, autonomous orchestration, and presentation. |

The interface-only extension points (solver adapters, reasoning backends, renderers, forecasting models, …) ship **zero** concrete implementations by design — new value arrives as plugins, evaluated against the locked specifications. See the [package reference](https://imanojkumar.github.io/MineProductivity/packages/) for each package's public API and extension guide.

## Documentation

Full documentation is published at **[imanojkumar.github.io/MineProductivity](https://imanojkumar.github.io/MineProductivity/)**:

- [Getting Started](https://imanojkumar.github.io/MineProductivity/getting-started/installation/) - installation, quick start, next steps
- [Tutorials](https://imanojkumar.github.io/MineProductivity/tutorials/) - runnable, package-by-package walkthroughs
- [Packages](https://imanojkumar.github.io/MineProductivity/packages/) & [API Reference](https://imanojkumar.github.io/MineProductivity/api-reference/) - narrative guides and the docstring-generated symbol reference
- [Architecture Handbook](https://imanojkumar.github.io/MineProductivity/architecture/README/) & [ADRs](https://imanojkumar.github.io/MineProductivity/adr/) - the twelve locked design specifications and the decisions behind them
- [Benchmarks](https://imanojkumar.github.io/MineProductivity/benchmarks/) & [Certification](https://imanojkumar.github.io/MineProductivity/certification/2.0-certification/)

## Project status

**Stable - `v2.0.0`.** The architecture is complete and locked, and the public APIs are stable by contract: they will not change incompatibly without a further MAJOR release. New value ships as plugins and applications, not as changes to the locked packages. See the [certification record](docs/certification/2.0-certification.md) and the [CHANGELOG](CHANGELOG.md).

<details>
<summary>Milestone history</summary>

| Version | Milestone |
|---|---|
| v0.2.0 – v0.7.0 | Foundation Layer (`core`, `events`, `ontology`, `registry`/`plugins`, `connectors`, `kpis`) |
| v0.8.0 – v1.4.0 | Architecture milestones for the Intelligence tier (design specs + checklists + ADRs) |
| v1.5.0 | Analytics Engine implementation |
| v1.6.0 | Decision Intelligence implementation |
| v1.7.0 | Digital Twin implementation |
| v1.8.0 | Simulation implementation |
| v1.9.0 | Optimization implementation |
| v1.10.0 | AI Agents implementation |
| v1.11.0 | Visualization implementation |
| **v2.0.0** | **Enterprise certification — architecture complete & locked** |

A future conformance-suite package and a CLI application are tracked as optional, post-2.0 work in the [ROADMAP](ROADMAP.md).

</details>

## Contributing

Contributions are welcome. Set up a development environment:

```bash
git clone https://github.com/imanojkumar/MineProductivity.git
cd MineProductivity
pip install -e ".[dev]"
pre-commit install
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

Apache License 2.0 - see [LICENSE](LICENSE).

## Citation

If you use MineProductivity in research or industry, please cite it via the Zenodo **Concept DOI** (which always resolves to the latest release):

> Kumar, M. (2026). *MineProductivity*. Zenodo. https://doi.org/10.5281/zenodo.21172767

Machine-readable metadata is in [`CITATION.cff`](CITATION.cff).
