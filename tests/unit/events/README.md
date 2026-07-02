# Unit Tests — mineproductivity.events

## Purpose

Unit tests for `src/mineproductivity/events/`, mirroring its structure one-to-one, including its `canonical/` and `serialization/` subpackages.

## Scope

Isolated tests for `mineproductivity.events` only — no filesystem, network, or cross-package integration beyond the minimal `ontology.DelayCategory` contract. Cross-package pipeline behavior (connector → validate → append → query) belongs in `tests/integration/`.

## Responsibilities

- Cover every public symbol exported by `mineproductivity.events`.
- Exercise the event lifecycle (§11 of the design spec): structural validation, contextual validation/confidence scoring, envelope construction, append, publish, query, replay, snapshot.
- Prove the two normative properties the design specification calls out explicitly: **idempotency** (re-appending an identical `(EventID, EventVersion)` is a no-op) and **replay/snapshot equivalence**.
- Maintain >95% line coverage of `src/mineproductivity/events/`.

## Contents

- `test_exceptions.py` — the `events`-specific exception hierarchy.
- `test_identifier.py` — `EventID`, ULID generation/sortability.
- `test_versioning.py` — `EventVersion`.
- `test_base_event.py` — `BaseEvent` ABC contract.
- `test_schema.py` — `EventSchema`, JSON Schema export.
- `test_envelope.py` — `EventEnvelope`, `EventMetadata`, the three-timestamp invariant.
- `test_validation.py` — `EventValidator`, `ConfidenceScore`, `ValidationOutcome`, `score_confidence`.
- `test_replay.py` — `AsOf`, `ReplayHandle`.
- `test_snapshot.py` — `EventSnapshot`.
- `test_store.py` — `EventStore` ABC, `EventQuery`, `_InMemoryEventStore` (append, idempotency, versioning, query, replay, snapshot).
- `test_bus.py` — `EventBus` ABC, `Subscription`, `_InMemoryEventBus`.
- `test_public_api.py` — the `mineproductivity.events` package's exported surface and import structure.
- `canonical/` — one `test_*.py` per canonical event type.
- `serialization/` — one `test_*.py` per codec (JSON, Arrow, Parquet).

## Dependencies

`pytest` (see root `pyproject.toml`). Arrow/Parquet tests additionally require the `pyarrow` optional dependency (installed via the `dev` extra) and are skipped automatically if it is absent.

## Future Work

Extend as `events` gains new canonical event types or codecs; keep the 1:1 file mapping to `src/mineproductivity/events/`.

## References

- Reference Implementation Blueprint v1.0
- [`docs/architecture/01_Event_Framework_Design_Specification.md`](../../../docs/architecture/01_Event_Framework_Design_Specification.md)
- [`docs/design/01_Event_Implementation_Checklist.md`](../../../docs/design/01_Event_Implementation_Checklist.md)
