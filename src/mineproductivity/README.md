# mineproductivity (package root)

## Purpose

The single installable Python package containing every MineProductivity subsystem, organized as independently documented sub-packages with an enforced, inward-pointing dependency direction.

## Scope

The `src/` layout root for the `mineproductivity` distribution. Contains 24 subsystem packages plus the package-level `__init__.py` exposing `__version__`. Does not contain tests (see `tests/`), datasets (see `datasets/`), or documentation (see `docs/`).

## Responsibilities

- Expose the package version and top-level public API surface (currently empty).
- House all subsystem sub-packages listed below, each independently documented.

## Contents

- `core/`, `events/`, `ontology/`, `kpis/`, `datasets/`, `connectors/`, `analytics/`, `optimization/`, `simulation/`, `digital_twin/`, `decision/`, `agents/`, `visualization/`, `benchmark/`, `certification/`, `config/`, `io/`, `utils/`, `typing/`, `cli/`, `exceptions/`, `registry/`, `plugins/`, `validation/`

## Dependencies

No third-party runtime dependencies are declared yet (see pyproject.toml). Internal dependency direction between sub-packages is documented in the root README.md.

## Future Work

Implement each sub-package per the phasing in ROADMAP.md, always starting with tests and metadata before behavior.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
