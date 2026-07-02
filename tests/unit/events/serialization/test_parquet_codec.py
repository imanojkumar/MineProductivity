"""Tests for mineproductivity.events.serialization.parquet_codec.

Skipped automatically when the optional ``pyarrow`` dependency is not
installed (see ``events/README.md``).
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("pyarrow")

from mineproductivity.events.serialization.parquet_codec import ParquetEventCodec  # noqa: E402


class TestSingleEnvelopeRoundTrip:
    def test_serialize_deserialize_round_trips(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        codec = ParquetEventCodec()
        envelope = cycle_envelope_factory()
        data = codec.serialize(envelope)
        restored = codec.deserialize(data)
        assert restored == envelope

    def test_serialize_returns_bytes(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        codec = ParquetEventCodec()
        data = codec.serialize(cycle_envelope_factory())
        assert isinstance(data["parquet_bytes"], bytes)
        assert len(data["parquet_bytes"]) > 0


class TestPartitionedStorage:
    def test_write_and_read_partitioned(  # type: ignore[no-untyped-def]
        self, tmp_path: Path, cycle_envelope_factory, cycle_event_factory
    ) -> None:
        codec = ParquetEventCodec()
        envelopes = [
            cycle_envelope_factory(payload=cycle_event_factory(equipment_id=f"HT-{i}"))
            for i in range(4)
        ]
        written = codec.write_partitioned(envelopes, tmp_path)
        assert len(written) >= 1
        for path in written:
            assert path.exists()

        read_back = codec.read_partitioned(tmp_path)
        assert len(read_back) == 4
        assert {e.event_id.value for e in read_back} == {e.event_id.value for e in envelopes}

    def test_partitions_by_site_from_metadata_attributes(  # type: ignore[no-untyped-def]
        self, tmp_path: Path, cycle_event_factory
    ) -> None:
        from mineproductivity.events.envelope import EventEnvelope, EventMetadata
        from mineproductivity.events.identifier import EventID
        from mineproductivity.events.versioning import EventVersion
        from datetime import datetime, timezone

        now = datetime(2026, 6, 25, 6, tzinfo=timezone.utc)
        codec = ParquetEventCodec()
        envelope = EventEnvelope(
            event_id=EventID.generate(),
            version=EventVersion(),
            payload=cycle_event_factory(),
            event_time_utc=now,
            processing_time_utc=now,
            ingestion_time_utc=now,
            metadata=EventMetadata(name="e", attributes={"site": "bingham-west"}),
        )
        codec.write_partitioned([envelope], tmp_path)
        assert (tmp_path / "site=bingham-west").exists()

    def test_defaults_to_unknown_site_when_absent(  # type: ignore[no-untyped-def]
        self, tmp_path: Path, cycle_envelope_factory
    ) -> None:
        codec = ParquetEventCodec()
        codec.write_partitioned([cycle_envelope_factory()], tmp_path)
        assert (tmp_path / "site=unknown").exists()

    def test_read_partitioned_empty_directory_returns_empty(self, tmp_path: Path) -> None:
        codec = ParquetEventCodec()
        assert codec.read_partitioned(tmp_path) == ()


class TestErrors:
    def test_deserialize_wrong_row_count_raises(  # type: ignore[no-untyped-def]
        self, cycle_envelope_factory, cycle_event_factory
    ) -> None:
        from mineproductivity.core import SerializationError
        from mineproductivity.events.serialization.arrow_codec import ArrowEventCodec
        import io
        import pyarrow.parquet as pq

        arrow_codec = ArrowEventCodec()
        table = arrow_codec.serialize_batch([cycle_envelope_factory(), cycle_envelope_factory()])
        buffer = io.BytesIO()
        pq.write_table(table, buffer)

        codec = ParquetEventCodec()
        with pytest.raises(SerializationError):
            codec.deserialize({"parquet_bytes": buffer.getvalue()})
