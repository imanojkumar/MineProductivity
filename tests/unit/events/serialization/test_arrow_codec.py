"""Tests for mineproductivity.events.serialization.arrow_codec.

Skipped automatically when the optional ``pyarrow`` dependency is not
installed (see ``events/README.md``).
"""

from __future__ import annotations

import pytest

pytest.importorskip("pyarrow")

from mineproductivity.events.serialization.arrow_codec import ArrowEventCodec  # noqa: E402


class TestSingleEnvelopeRoundTrip:
    def test_serialize_deserialize_round_trips(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        codec = ArrowEventCodec()
        envelope = cycle_envelope_factory()
        data = codec.serialize(envelope)
        restored = codec.deserialize(data)
        assert restored == envelope

    def test_serialize_returns_a_table(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        import pyarrow as pa

        codec = ArrowEventCodec()
        data = codec.serialize(cycle_envelope_factory())
        assert isinstance(data["table"], pa.Table)
        assert data["table"].num_rows == 1


class TestBatchRoundTrip:
    def test_batch_of_same_type_round_trips(  # type: ignore[no-untyped-def]
        self, cycle_envelope_factory, cycle_event_factory
    ) -> None:
        codec = ArrowEventCodec()
        envelopes = [
            cycle_envelope_factory(payload=cycle_event_factory(equipment_id=f"HT-{i}"))
            for i in range(5)
        ]
        table = codec.serialize_batch(envelopes)
        assert table.num_rows == 5
        restored = codec.deserialize_batch(table)
        assert len(restored) == 5
        assert {e.event_id.value for e in restored} == {e.event_id.value for e in envelopes}

    def test_empty_batch_produces_empty_table(self) -> None:
        codec = ArrowEventCodec()
        table = codec.serialize_batch([])
        assert table.num_rows == 0

    def test_empty_attributes_do_not_break_batch_encoding(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        # Regression test: metadata.attributes defaulting to {} for every
        # row previously produced a zero-child Arrow struct type.
        codec = ArrowEventCodec()
        envelopes = [cycle_envelope_factory() for _ in range(3)]
        table = codec.serialize_batch(envelopes)
        restored = codec.deserialize_batch(table)
        assert all(e.metadata.attributes == {} for e in restored)


class TestErrors:
    def test_deserialize_wrong_row_count_raises(  # type: ignore[no-untyped-def]
        self, cycle_envelope_factory, cycle_event_factory
    ) -> None:
        from mineproductivity.core import SerializationError

        codec = ArrowEventCodec()
        table = codec.serialize_batch([cycle_envelope_factory(), cycle_envelope_factory()])
        with pytest.raises(SerializationError):
            codec.deserialize({"table": table})
