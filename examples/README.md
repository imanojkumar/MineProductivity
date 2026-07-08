# Examples

## Purpose

Runnable, minimal usage examples of MineProductivity, ranging from quickstart snippets to production-grade patterns.

## Scope

Example scripts/projects and their documentation. Does not include the underlying package implementation or exhaustive tutorials (see `notebooks/`).

## Responsibilities

- Demonstrate the smallest possible working usage of each subsystem once implemented.
- Demonstrate production-grade composition patterns (config, logging, error handling).

## Contents

Implemented, runnable today — **new here? Start with `quickstart/`:**

- [`quickstart/`](quickstart/README.md) — the five-minute tour: one truck, one shift, one KPI, in ~50 lines (1 script).
- [`core/`](core/README.md) — entities, value objects, repositories, factories/builders, validation, serialization, `Result`/`Maybe` (6 scripts).
- [`events/`](events/README.md) — first event, replay, correction (3 scripts).
- [`ontology/`](ontology/README.md) — equipment modelling, structural modelling, validation (3 scripts).
- [`registry/`](registry/README.md) — register/discover, version compatibility (2 scripts; also covers `plugins`).
- [`connectors/`](connectors/README.md) — CSV ingestion, REST with retry/auth-refresh (2 scripts).
- [`kpis/`](kpis/README.md) — simple execution, composite `UTIL.OEE`, batch summary, `REGISTRY` discovery (4 scripts).
- [`decision/`](decision/README.md) — audited pipeline over real KPI/trend evidence, action prioritization/planning, real-time session, plugin strategy (4 scripts).

Placeholders, pending their corresponding subsystem's implementation:

- `production/`, `visualization/`, `ai/`, `digital_twin/`.

## Dependencies

`mineproductivity`, editable-installed from this repository (`pip install -e .`); `mineproductivity[analytics]` additionally for the `kpis/` and `decision/` examples.

## Future Work

Author `production/`, `visualization/`, `ai/`, and `digital_twin/` examples as their corresponding subsystems are implemented.

## References

- Developer & Cookbook Guide — Part I
- Developer & Cookbook Guide — Part II
