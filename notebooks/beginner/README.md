# Notebooks - beginner

## Purpose

Notebooks for first-time users with no prior MineProductivity knowledge - installation, core concepts, first KPI lookup (once implemented).

## Scope

Notebook files (.ipynb) and their direct supporting narrative. No package implementation code.

## Responsibilities

- House beginner-tier learning notebooks per the Learning & Benchmark Suite v1.0.

## Contents

- `01_first_kpi_lookup.ipynb` - loads the sample dataset shared with `examples/kpis/`, computes `PROD.TPH` via `KPIEngine`, inspects a `KPIResult`'s provenance, and discovers the rest of the Standard Library through `REGISTRY` - no source-code reading required.

## Dependencies

`mineproductivity[analytics]`, plus `jupyter`/`ipykernel` (install both via `mineproductivity[notebooks]`, or `mineproductivity[dev]` for the full development environment).

## Running

```bash
pip install -e ".[notebooks,analytics]"
jupyter notebook notebooks/beginner/01_first_kpi_lookup.ipynb
```

## Future Work

Author intermediate/advanced/expert/research-tier notebooks as their corresponding subsystems (`analytics`, `decision`, `digital_twin`) are implemented.

## References

- Learning & Benchmark Suite v1.0
