# Benchmark — reports

## Purpose

Historical benchmark run reports, retained for trend tracking across releases.

## Scope

Benchmark data/definitions only. No harness implementation code.

## Responsibilities

- House reports for the MineProductivity benchmark suite.

## Contents

- `decision/` — Decision Intelligence benchmark reports (`RuleEngine.evaluate()` throughput, `DecisionAuditTrail` append/query latency), first recorded at software v1.6.0.
- `digital_twin/` — Digital Twin benchmark reports (`TwinRepository.get()`/`list()` latency, cold-start replay cost with/without snapshot seeding), first recorded at software v1.7.0.
- `simulation/` — Simulation benchmark reports (`SimulationRunRepository.get()`/`list()` latency, `SimulationStateCache` hit-rate/time saved across repeated trials), first recorded at software v1.8.0.

## Dependencies

`src/mineproductivity/benchmark/` (once implemented).

## Future Work

Populate as benchmarked subsystems are implemented.

## References

- Learning & Benchmark Suite v1.0
