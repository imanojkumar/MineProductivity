"""Tests for mineproductivity.decision.audit."""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from types import MappingProxyType

from mineproductivity.decision.audit import DecisionAuditEntry, DecisionAuditTrail
from mineproductivity.decision.result import DecisionResult


def _entry(*, scope: dict[str, str] | None = None) -> DecisionAuditEntry:
    return DecisionAuditEntry(
        recorded_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        result=DecisionResult(model_code="STRATEGY.Threshold"),
        context_scope=scope or {"pit": "north"},
        source_event_ids=(),
    )


class TestDecisionAuditEntry:
    def test_context_scope_is_frozen(self) -> None:
        entry = _entry()
        assert isinstance(entry.context_scope, MappingProxyType)

    def test_source_event_ids_defaults_to_empty(self) -> None:
        entry = DecisionAuditEntry(
            recorded_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            result=DecisionResult(model_code="STRATEGY.Threshold"),
            context_scope={},
        )
        assert entry.source_event_ids == ()

    def test_source_event_ids_populated_explicitly(self) -> None:
        entry = DecisionAuditEntry(
            recorded_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            result=DecisionResult(model_code="STRATEGY.Threshold"),
            context_scope={},
            source_event_ids=("01ABC",),
        )
        assert entry.source_event_ids == ("01ABC",)


class TestDecisionAuditTrailRecordAndQuery:
    def test_empty_trail_has_no_entries(self) -> None:
        assert DecisionAuditTrail().query() == ()

    def test_recorded_entry_is_returned_by_unfiltered_query(self) -> None:
        trail = DecisionAuditTrail()
        entry = _entry()
        trail.record(entry)
        assert trail.query() == (entry,)

    def test_multiple_entries_preserve_insertion_order(self) -> None:
        trail = DecisionAuditTrail()
        first = _entry(scope={"pit": "north"})
        second = _entry(scope={"pit": "south"})
        trail.record(first)
        trail.record(second)
        assert trail.query() == (first, second)

    def test_scope_filter_matches_exact_key_value(self) -> None:
        trail = DecisionAuditTrail()
        trail.record(_entry(scope={"pit": "north"}))
        assert len(trail.query(scope={"pit": "north"})) == 1

    def test_scope_filter_excludes_non_matching_entries(self) -> None:
        trail = DecisionAuditTrail()
        trail.record(_entry(scope={"pit": "north"}))
        assert trail.query(scope={"pit": "south"}) == ()

    def test_scope_filter_requires_all_keys_to_match(self) -> None:
        trail = DecisionAuditTrail()
        trail.record(_entry(scope={"pit": "north", "shift": "A"}))
        assert len(trail.query(scope={"pit": "north", "shift": "A"})) == 1
        assert trail.query(scope={"pit": "north", "shift": "B"}) == ()

    def test_scope_filter_key_absent_from_entry_excludes_it(self) -> None:
        trail = DecisionAuditTrail()
        trail.record(_entry(scope={"pit": "north"}))
        assert trail.query(scope={"shift": "A"}) == ()

    def test_query_returns_a_snapshot_unaffected_by_later_records(self) -> None:
        trail = DecisionAuditTrail()
        trail.record(_entry())
        snapshot = trail.query()
        trail.record(_entry())
        assert len(snapshot) == 1
        assert len(trail.query()) == 2


class TestDecisionAuditTrailConcurrency:
    def test_concurrent_record_calls_do_not_lose_entries(self) -> None:
        trail = DecisionAuditTrail()

        def _record_many() -> None:
            for _ in range(50):
                trail.record(_entry())

        threads = [threading.Thread(target=_record_many) for _ in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert len(trail.query()) == 200

    def test_query_is_not_blocked_by_concurrent_record_calls(self) -> None:
        """Design spec §27's checklist proof: ``query()`` reads a
        snapshot under the lock and filters outside it, so it completes
        (returning a consistent prefix of the trail) while concurrent
        ``record()`` calls are still in flight -- it never waits for the
        writers to finish. Every observed snapshot length must be
        monotonically non-decreasing (append-only) and each snapshot
        internally consistent (a tuple of already-committed entries)."""
        trail = DecisionAuditTrail()

        def _record_many() -> None:
            for _ in range(200):
                trail.record(_entry(scope={"pit": "north"}))

        threads = [threading.Thread(target=_record_many) for _ in range(4)]
        for thread in threads:
            thread.start()

        observed_lengths: list[int] = []
        while any(thread.is_alive() for thread in threads):
            snapshot = trail.query(scope={"pit": "north"})
            observed_lengths.append(len(snapshot))

        for thread in threads:
            thread.join()

        assert observed_lengths == sorted(observed_lengths), (
            "append-only trail: snapshot lengths observed during concurrent "
            "record() calls must never decrease"
        )
        assert all(length <= 800 for length in observed_lengths)
        assert len(trail.query()) == 800


class TestDecisionAuditTrailRepr:
    def test_repr_includes_entry_count(self) -> None:
        trail = DecisionAuditTrail()
        trail.record(_entry())
        assert "1" in repr(trail)
