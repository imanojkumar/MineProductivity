# Benchmark Report — Visualization (v1.11.0)

**Date:** 2026-07-12
**Package:** `mineproductivity.visualization` (software v1.11.0)
**Scenarios:** [`benchmark/scenarios/visualization/`](../../scenarios/visualization/)
**Environment:** Windows 11 (AMD64), CPython 3.12.10, `mineproductivity` editable-installed. Single process, no other load control — reference numbers for order-of-magnitude regression tracking, not a controlled lab measurement.

Both scenarios are standalone scripts (the `mineproductivity.benchmark` harness package is not yet implemented — see `benchmark/README.md`); re-run them with:

```bash
python benchmark/scenarios/visualization/dashboard_repository_latency.py
python benchmark/scenarios/visualization/render_parallel_throughput.py
```

## 1. `DashboardRepository.get()`/`list()` latency

Populations span "a team" (10³ dashboards) through "a whole enterprise, never pruned" (10⁵). `get()` figures are means over 10,000 calls; `list()` over 5.

| boards | get (µs) | list all (ms) | list by_owner (ms) | owner matches |
|---:|---:|---:|---:|---:|
| 1,000 | 0.11 | 0.02 | 0.15 | 500 |
| 10,000 | 0.10 | 0.10 | 1.20 | 5,000 |
| 100,000 | 0.11 | 1.54 | 19.56 | 50,000 |

**Reading:** `get()` — the hot open-a-dashboard path — is flat (~0.10 µs) across a 100× population spread, the O(1) bound design spec §29 requires. `list()` is linear by `core.BaseRepository`'s own contract — the discovery path (§27), not the open hot path. Identical shape to every other package's repository benchmark, as expected under the shared `core.InMemoryRepository` reference.

## 2. Multi-widget render throughput (sequential vs. parallel)

The same N widgets rendered through `RenderingPipeline.render` (visualization dispatch → `PresentationModel` → renderer dispatch → `RenderedOutput`). The example-local view and renderer are trivial, isolating pipeline dispatch overhead from a real charting backend's cost. Parallel runs over an 8-worker `ThreadPoolExecutor`.

| widgets | sequential (ms) | seq renders/s | parallel (ms) | par renders/s |
|---:|---:|---:|---:|---:|
| 50 | 0.21 | 234,852 | 2.78 | 17,996 |
| 200 | 0.98 | 203,707 | 6.44 | 31,069 |
| 1,000 | 4.04 | 247,739 | 19.19 | 52,099 |

**Reading:** sequential render throughput is ~200k–248k renders/s — the pipeline is a pure two-hop dispatch with no persistence, so it is the fastest hot path in the platform. The threaded path is slower here for the familiar reason: with a sub-microsecond pure-Python view and renderer, every render holds the GIL, so thread parallelism only adds pool overhead. The benchmark's point is **correctness under concurrency, not speedup**: `Visualization`/`Renderer` instances are stateless and share no mutable state across calls (design spec §29), so a dashboard's widgets render independently without contention. Wall-clock speedup materializes only when the concrete renderer releases the GIL (a native charting/rasterization library) — exactly the backend boundary this package keeps out of its own code (§3.1, §4).

## Regression guidance

Re-run both scenarios before each release touching `visualization`; investigate if `get()` exceeds ~1 µs at any population, or if sequential render throughput drops below ~50k renders/s for the trivial view/renderer on comparable hardware (a sign the two-hop dispatch path regressed).
