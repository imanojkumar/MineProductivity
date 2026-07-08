# Benchmark Report — Digital Twin (v1.7.0)

**Date:** 2026-07-08
**Package:** `mineproductivity.digital_twin` (software v1.7.0)
**Scenarios:** [`benchmark/scenarios/digital_twin/`](../../scenarios/digital_twin/)
**Environment:** Windows 11 (AMD64), CPython 3.12.10, `mineproductivity` editable-installed. Single process, single thread, no other load control — these are reference numbers for order-of-magnitude regression tracking, not a controlled lab measurement.

Both scenarios are standalone scripts (the `mineproductivity.benchmark` harness package is not yet implemented — see `benchmark/README.md`); re-run them with:

```bash
python benchmark/scenarios/digital_twin/repository_latency.py
python benchmark/scenarios/digital_twin/cold_start_replay.py
```

## 1. `TwinRepository.get()`/`list()` latency

Populations span "a large site" (10³ twins) through "an enterprise-wide, multi-site deployment, never pruned" (10⁵). `get()` figures are means over 10,000 calls; `list()` over 5.

| twins | get (µs) | list all (ms) | list by_scope (ms) | scope matches |
|---:|---:|---:|---:|---:|
| 1,000 | 0.07 | 0.01 | 0.78 | 500 |
| 10,000 | 0.09 | 0.12 | 8.97 | 5,000 |
| 100,000 | 0.08 | 2.33 | 99.81 | 50,000 |

**Reading:** `get()` — the hot per-synchronization path — is flat (~0.08 µs) across a 100× population spread, the O(1) bound design spec §33 requires of the reference implementation and expects any production backend to preserve. `list()` (with or without a specification) is linear by `core.BaseRepository`'s own contract — the discovery path (§18), not the sync hot path; at the enterprise scale a scope-filtered listing costs ~100 ms, acceptable for the interactive/reporting use it serves.

## 2. Cold-start reconstruction cost vs. event-history length

Two paths per history length (§15, §33): **full replay** (`EventStore.replay` from genesis, folding every relevant envelope through `_apply`) and **snapshot-seeded catch-up** (restore from a `TwinSnapshot` at the 90% point, fold only the 10% tail via a bounded `EventStore.query(since_utc=...)`).

| events | full replay (ms) | snapshot-seeded (ms) | speedup |
|---:|---:|---:|---:|
| 1,000 | 0.97 | 0.53 | 1.8× |
| 10,000 | 8.42 | 4.89 | 1.7× |
| 50,000 | 51.59 | 36.03 | 1.4× |

**Reading:** full-replay cost is linear in history length, exactly as §33 states (~1 µs/event through the whole replay+fold path). Snapshot seeding cuts the *fold* work by 90%, but the observed speedup is a modest 1.4–1.8× because the reference `_InMemoryEventStore`'s `query()`/`replay()` both scan the full log linearly and implement no `EventSnapshot` acceleration of their own — `digital_twin` deliberately inherits whatever replay acceleration the `EventStore` implementation provides (§33), which for the in-memory reference is none. A production `EventStore` with time-indexed queries or `EventSnapshot`-accelerated replay would turn the seeded path's cost into ~10% of the full path; the twin-level mechanics for exploiting it (`TwinSnapshot` restore + bounded tail fold) are proven correct here (both paths converge on the identical `TwinState`, asserted on every run).

## Regression guidance

Re-run both scenarios before each release touching `digital_twin`; investigate if `get()` exceeds ~1 µs at any population, full-replay cost exceeds ~5 µs/event, or the snapshot-seeded path stops converging with full replay (a correctness failure, not a performance one).
