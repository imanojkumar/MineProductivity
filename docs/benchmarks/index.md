# Benchmarks

Recorded, reproducible benchmark reports for the packages whose implementation checklists require them. Each report is a standalone measurement you can re-run yourself; the scenario scripts live under [`benchmark/scenarios/`](https://github.com/imanojkumar/MineProductivity/tree/main/benchmark/scenarios).

!!! info "What these measure — and what they don't"
    These are **reference numbers for order-of-magnitude regression tracking**, not controlled lab measurements. Two recurring results hold across every package:

    - **Repository `get()` is O(1)** — flat at ~0.08–0.11 µs across 10³–10⁵ populations, exactly as the design specifications require.
    - **Throughput scenarios report honest sequential-vs-parallel numbers.** For the trivial in-process fixtures, thread parallelism is GIL-bound and adds no speedup; real speedup materializes only when a concrete plugin backend (a native solver, an LLM call, a charting library) releases the GIL. The benchmarks prove *contention-free correctness*, not speedup.

## Reports by package

- [Decision](decision.md) — `RuleEngine` throughput, `DecisionAuditTrail` latency.
- [Digital Twin](digital_twin.md) — `TwinRepository` latency, cold-start replay cost.
- [Simulation](simulation.md) — `SimulationRunRepository` latency, `SimulationStateCache` effectiveness.
- [Optimization](optimization.md) — `OptimizationRunRepository` latency, sweep re-solve throughput.
- [AI Agents](agents.md) — `TaskRepository` latency, task-dispatch throughput.
- [Visualization](visualization.md) — `DashboardRepository` latency, multi-widget render throughput.
