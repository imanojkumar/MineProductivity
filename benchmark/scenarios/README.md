# Benchmark — scenarios

## Purpose

Benchmark scenario definitions — inputs, configuration, and success criteria for each benchmark run.

## Scope

Benchmark data/definitions only. No harness implementation code.

## Responsibilities

- House scenarios for the MineProductivity benchmark suite.

## Contents

- `decision/` — standalone Decision Intelligence scenarios (`rule_engine_throughput.py`, `audit_trail_latency.py`); harness-free by design until `mineproductivity.benchmark` exists.

## Dependencies

`src/mineproductivity/benchmark/` (once implemented).

## Future Work

Populate as benchmarked subsystems are implemented.

## References

- Learning & Benchmark Suite v1.0
