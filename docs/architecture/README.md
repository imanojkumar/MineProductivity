# Architecture Documentation

## Purpose

Companion documentation for the Master Architecture Handbook v1.0 — the locked SSOT describing MineProductivity's overall system architecture, layering, and design principles.

## Scope

Architectural rationale, layering diagrams, dependency rules, and cross-cutting design decisions (Clean Architecture, DDD, event-sourcing, ontology-first modeling). Does not include package-level implementation detail — that belongs in each package's own `README.md` under `src/mineproductivity/`.

## Responsibilities

- Explain the inward-pointing dependency direction between `core`, `ontology`, `events`, `kpis`, `analytics`, `decision`, and `digital_twin`.
- Document forbidden import patterns and architectural boundaries.
- Serve as the entry point for new contributors to understand system shape before reading code.

## Contents

- Placeholder for architecture overview, layering diagrams, and Architecture Decision Records (ADRs) to be added as implementation proceeds.

## Dependencies

None (documentation only).

## Future Work

Add ADRs as significant architectural decisions are made during implementation. Add rendered layering and sequence diagrams under `docs/images/`.

## References

- Master Architecture Handbook v1.0
