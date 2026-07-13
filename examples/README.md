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
- [`digital_twin/`](digital_twin/README.md) — cold-start + live twin synchronization, category/scope discovery, snapshot serialization, plugin twin type (4 scripts).
- [`simulation/`](simulation/README.md) — snapshot-seeded Monte Carlo experiment, scenario comparison, sensitivity sweep, plugin simulation model (4 scripts).
- [`optimization/`](optimization/README.md) — MIP fleet allocation seeded from a twin snapshot, plan comparison, sensitivity sweep, candidate-scenario search over `simulation`, plugin solver adapter (5 scripts).
- [`agents/`](agents/README.md) — single agent task, policy-gated approval, multi-agent workflow, planning agent composing `simulation`/`optimization`, plugin agent + tool (5 scripts).
- [`visualization/`](visualization/README.md) — single widget render, multi-source dashboard, exported report, simulation-playback view, plugin visualization + renderer (5 scripts).

Placeholders:

- `production/` (end-to-end production-composition patterns), `ai/` (superseded by `agents/`).

## Dependencies

`mineproductivity`, editable-installed from this repository (`pip install -e .`); `mineproductivity[analytics]` additionally for the `kpis/`, `decision/`, `simulation/`, `optimization/`, and `agents/` examples.

## Future Work

Author `production/` end-to-end composition examples; the `ai/` placeholder is superseded by `agents/` and is slated for removal.

## References

- Developer & Cookbook Guide — Part I
- Developer & Cookbook Guide — Part II
