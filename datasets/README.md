# Datasets

## Purpose

Top-level storage for all data assets used by MineProductivity: canonical reference data, generated artifacts, golden expected outputs, benchmark inputs, edge-case fixtures, synthetic data, and raw/processed staging areas.

## Scope

Actual data files and their documentation. Does not include dataset loading code (see `src/mineproductivity/datasets/`) or test-scoped micro-datasets (see `tests/datasets/`).

## Responsibilities

- Provide a single, well-organized location for all non-code data assets.
- Keep canonical/golden data clearly separated from generated/synthetic data.

## Contents

- `canonical/` — authoritative reference datasets.
- `generated/` — artifacts produced by running the (future) pipeline; not hand-authored.
- `golden/` — golden expected-output datasets for regression/golden testing.
- `benchmark/` — datasets feeding `benchmark/` scenarios.
- `edge_cases/` — deliberately unusual/boundary-condition data.
- `synthetic/` — programmatically generated, non-real-world data.
- `raw/` — unprocessed source data staging area.
- `processed/` — cleaned/transformed data derived from `raw/`.

## Dependencies

None directly; consumed by `src/mineproductivity/datasets/`, `tests/`, `benchmark/`, and `certification/` once implemented.

## Future Work

Populate each subdirectory as datasets are sourced/generated per ROADMAP.md phasing.

## References

- Reference Implementation Blueprint v1.0
- Learning & Benchmark Suite v1.0
