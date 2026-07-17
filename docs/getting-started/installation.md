# Installation

MineProductivity requires **Python 3.12+**. It is not yet published to PyPI; install directly from GitHub or a local checkout.

## From GitHub

```bash
pip install git+https://github.com/imanojkumar/MineProductivity.git
```

## From a local checkout

```bash
git clone https://github.com/imanojkumar/MineProductivity.git
cd MineProductivity
pip install .
```

The base install has **zero third-party dependencies** and gives you `core`, `events`, `ontology`, `registry`, `plugins`, `connectors`, and `kpis`, plus the pure-Python `analytics`, `decision`, `digital_twin`, `simulation`, `optimization`, `agents`, and `visualization` packages (they import with no extras; third-party libraries are needed only to *execute* certain backends).

## Optional dependency groups

| Extra | Adds | Needed for |
|---|---|---|
| `events` | `pyarrow` | Parquet/Arrow event codecs |
| `connectors` | `openpyxl`, `tzdata` (Windows) | `ExcelConnector`, local-timezone normalization |
| `analytics` | `numpy`, `pandas`, `polars`, `duckdb` | KPI Engine execution backends, `KPIResult.to_frame()` |
| `notebooks` | `jupyter`, `ipykernel` | Running the notebooks |
| `docs` | `mkdocs-material`, `mkdocstrings`, … | Building this documentation site |
| `dev` | everything above, plus `pytest`, `ruff`, `mypy`, `pre-commit` | Contributing |

```bash
pip install "mineproductivity[analytics] @ git+https://github.com/imanojkumar/MineProductivity.git"
```

## Verify the install

```python
import mineproductivity
print(mineproductivity.__version__)

from mineproductivity.kpis import REGISTRY

# One CAT 793F's shift: 40 cycles x 220 t at ~18 min (0.3 h) each.
cycles = [{"payload_t": 220.0, "operating_h": 0.3} for _ in range(40)]
tph = REGISTRY.get("PROD.TPH")().compute(cycles)
print(tph.value, tph.unit)  # 733.33... t/h
```

Next: the [Quick Start](quick-start.md) runs the whole platform end-to-end in about fifty lines.

New to the framework? The **[Learning Suite — Fundamentals](../tutorials/fundamentals/01_hello.md)** teaches it from first principles in ten lessons.
