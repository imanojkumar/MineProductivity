# Benchmark Report — Optimization (v1.9.0)

**Date:** 2026-07-12
**Package:** `mineproductivity.optimization` (software v1.9.0)
**Scenarios:** [`benchmark/scenarios/optimization/`](../../scenarios/optimization/)
**Environment:** Windows 11 (AMD64), CPython 3.12.10, `mineproductivity` editable-installed. Single process, no other load control — reference numbers for order-of-magnitude regression tracking, not a controlled lab measurement.

Both scenarios are standalone scripts (the `mineproductivity.benchmark` harness package is not yet implemented — see `benchmark/README.md`); re-run them with:

```bash
python benchmark/scenarios/optimization/run_repository_latency.py
python benchmark/scenarios/optimization/sweep_resolve_throughput.py
```

## 1. `OptimizationRunRepository.get()`/`list()` latency

Populations span "one big sweep" (10³ runs) through "a month of sweeps, never pruned" (10⁵). `get()` figures are means over 10,000 calls; `list()` over 5.

| runs | get (µs) | list all (ms) | list by_scope (ms) | scope matches |
|---:|---:|---:|---:|---:|
| 1,000 | 0.08 | 0.01 | 0.27 | 500 |
| 10,000 | 0.08 | 0.14 | 3.13 | 5,000 |
| 100,000 | 0.10 | 3.62 | 33.29 | 50,000 |

**Reading:** `get()` — the hot per-re-solve path — is flat (~0.08–0.10 µs) across a 100× population spread, the O(1) bound design spec §36 requires. `list()` is linear by `core.BaseRepository`'s own contract — the discovery path (§22), not the re-solve hot path. Identical shape to the Simulation and Digital Twin repository benchmarks, as expected: all three are the same `core.InMemoryRepository` reference under a `type`-alias repository.

## 2. Sweep re-solve throughput (sequential vs. parallel)

The same N re-solves of a trivial, fast example-local MIP, run sequentially through `SensitivityAnalyzer.sweep()` and concurrently through an 8-worker `ThreadPoolExecutor` over independent run ids. The model is deliberately negligible, isolating executor dispatch + repository remove/add persistence overhead.

| re-solves | sequential (ms) | seq re-solves/s | parallel (ms) | par re-solves/s |
|---:|---:|---:|---:|---:|
| 50 | 1.82 | 27,509 | 4.35 | 11,485 |
| 200 | 5.96 | 33,530 | 7.82 | 25,573 |
| 1,000 | 27.05 | 36,966 | 32.31 | 30,954 |

**Reading:** sequential throughput is ~27k–37k re-solves/s and scales linearly with sweep size — the executor's per-re-solve cost is flat. The threaded path is **not** faster here, and that is the honest, expected result: with a pure-Python, sub-microsecond "solver," every re-solve holds the GIL for essentially its whole duration, so thread parallelism only adds pool overhead. The benchmark's real point is **correctness, not speedup**: independent `OptimizationRun`s (distinct ids) carry no shared mutable state and complete without contention or error under concurrent dispatch (design spec §32, §33). Wall-clock speedup from this parallelism materializes only when the concrete solver adapter releases the GIL — a native solver library (OR-Tools, CBC, …) doing real work off the interpreter, exactly the §17 adapter boundary this package keeps out of its own code.

## Regression guidance

Re-run both scenarios before each release touching `optimization`; investigate if `get()` exceeds ~1 µs at any population, or if sequential re-solve throughput drops below ~10k re-solves/s for the trivial model on comparable hardware (a sign the executor's dispatch/persistence path regressed).
