# Benchmark Report — Simulation (v1.8.0)

**Date:** 2026-07-08
**Package:** `mineproductivity.simulation` (software v1.8.0)
**Scenarios:** [`benchmark/scenarios/simulation/`](../../scenarios/simulation/)
**Environment:** Windows 11 (AMD64), CPython 3.12.10, `mineproductivity` editable-installed. Single process, no other load control — reference numbers for order-of-magnitude regression tracking, not a controlled lab measurement.

Both scenarios are standalone scripts (the `mineproductivity.benchmark` harness package is not yet implemented — see `benchmark/README.md`); re-run them with:

```bash
python benchmark/scenarios/simulation/run_repository_latency.py
python benchmark/scenarios/simulation/seed_cache_effectiveness.py
```

## 1. `SimulationRunRepository.get()`/`list()` latency

Populations span "one big experiment" (10³ runs) through "a month of experiments, never pruned" (10⁵). `get()` figures are means over 10,000 calls; `list()` over 5.

| runs | get (µs) | list all (ms) | list by_scope (ms) | scope matches |
|---:|---:|---:|---:|---:|
| 1,000 | 0.08 | 0.01 | 0.29 | 500 |
| 10,000 | 0.07 | 0.16 | 2.64 | 5,000 |
| 100,000 | 0.08 | 2.87 | 30.20 | 50,000 |

**Reading:** `get()` — the hot per-trial path — is flat (~0.08 µs) across a 100× population spread, the O(1) bound design spec §36 requires. `list()` is linear by `core.BaseRepository`'s own contract — the discovery path (§22), not the trial hot path.

## 2. `SimulationStateCache` effectiveness across repeated trials

A 200-trial Monte Carlo experiment anchored to a historical `AsOf` over a 10,000-event history; the trial model itself is negligible, isolating the seeding cost. Uncached, every trial pays a full `EventStore.replay()`; cached, the first trial seeds and the rest hit the `(scenario_code, as_of)` key.

| mode | total (s) | per trial (ms) |
|---|---:|---:|
| uncached | 1.67 | 8.34 |
| cached | 0.02 | 0.10 |

**Reading:** hit-rate 199/200 (99.5%); wall-time saved 1.65 s (**98.8%**). One replay, cached, rather than one replay per trial — exactly the §26/§36 posture, quantified. The uncached bound grows linearly with history length (the reference store's replay is a linear scan, as recorded in the Digital Twin report); the cached bound does not.

## Regression guidance

Re-run both scenarios before each release touching `simulation`; investigate if `get()` exceeds ~1 µs at any population, or the cached experiment stops being at least ~10× faster than the uncached one at equal scale on comparable hardware.
