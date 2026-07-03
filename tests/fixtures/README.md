# Shared Fixtures

## Purpose

Shared pytest fixtures, factories, and test doubles reused across unit, integration, performance, regression, and golden tests.

## Scope

Testing philosophy and conventions for `tests/fixtures/`. No implementation code lives here — only tests, fixtures, or test-scoped data as applicable.

## Responsibilities

- Fixtures are domain-aware but implementation-free until packages exist to fix them against.
- Prefer fixture composition over duplication across test suites.

## Contents

- `plugins/` — real, independently-buildable fixture plugin packages (one well-behaved, one deliberately broken) used to prove the Registry Framework's discovery and isolation guarantees end-to-end. See [`plugins/README.md`](plugins/README.md).
- `connectors/` — small, synthetic CSV fixtures (golden, malformed, and local-timezone variants) used to exercise `CSVConnector` and the full connector-to-event pipeline. See [`connectors/README.md`](connectors/README.md).

## Dependencies

`pytest` (see `pyproject.toml`).

## Future Work

Populate alongside implementation, per ROADMAP.md phasing and CONTRIBUTING.md's test-first rule.

## References

- Reference Implementation Blueprint v1.0
- Developer & Cookbook Guide — Part II
