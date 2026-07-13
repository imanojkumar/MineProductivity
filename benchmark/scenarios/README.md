# Benchmark — scenarios

## Purpose

Benchmark scenario definitions — inputs, configuration, and success criteria for each benchmark run.

## Scope

Benchmark data/definitions only. No harness implementation code.

## Responsibilities

- House scenarios for the MineProductivity benchmark suite.

## Contents

- `decision/` — standalone Decision Intelligence scenarios (`rule_engine_throughput.py`, `audit_trail_latency.py`); harness-free by design until `mineproductivity.benchmark` exists.
- `digital_twin/` — standalone Digital Twin scenarios (`repository_latency.py`, `cold_start_replay.py`); same harness-free posture.
- `simulation/` — standalone Simulation scenarios (`run_repository_latency.py`, `seed_cache_effectiveness.py`); same harness-free posture.
- `optimization/` — standalone Optimization scenarios (`run_repository_latency.py`, `sweep_resolve_throughput.py`); same harness-free posture.
- `agents/` — standalone AI Agents scenarios (`task_repository_latency.py`, `workflow_parallel_throughput.py`); same harness-free posture.
- `visualization/` — standalone Visualization scenarios (`dashboard_repository_latency.py`, `render_parallel_throughput.py`); same harness-free posture.

## Dependencies

`src/mineproductivity/benchmark/` (once implemented).

## Future Work

Populate as benchmarked subsystems are implemented.

## References

- Learning & Benchmark Suite v1.0
