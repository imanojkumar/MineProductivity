"""``ParquetEventCodec``: converts :class:`EventEnvelope` instances to and from Apache Parquet."""

from __future__ import annotations

import io
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from mineproductivity.core import BaseSerializer, SerializationError

from mineproductivity.events.envelope import EventEnvelope
from mineproductivity.events.serialization.arrow_codec import ArrowEventCodec

__all__ = ["ParquetEventCodec"]


def _import_pyarrow_parquet() -> Any:
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:  # pragma: no cover - exercised only without the extra installed
        raise SerializationError(
            "ParquetEventCodec requires the optional 'pyarrow' dependency. "
            'Install it with: pip install "mineproductivity[events]"'
        ) from exc
    return pq


class ParquetEventCodec(BaseSerializer[EventEnvelope[Any]]):
    """Converts :class:`~mineproductivity.events.envelope.EventEnvelope`
    instances to and from `Apache Parquet <https://parquet.apache.org/>`_
    -- the at-rest, partitioned storage format for the event lake.

    ``pyarrow`` is an optional dependency (the ``events`` extra); it is
    imported lazily. The single-envelope :meth:`serialize`/
    :meth:`deserialize` methods round-trip through an in-memory Parquet
    byte buffer (satisfying :class:`~mineproductivity.core.serialization.BaseSerializer`'s
    contract); :meth:`write_partitioned` is the intended bulk-storage
    entry point, partitioning by ``(site, event_type_code,
    date(event_time_utc))`` as specified.
    """

    def __init__(self) -> None:
        self._arrow_codec = ArrowEventCodec()

    def serialize(self, obj: EventEnvelope[Any]) -> Mapping[str, Any]:
        pq = _import_pyarrow_parquet()
        table = self._arrow_codec.serialize_batch([obj])
        buffer = io.BytesIO()
        pq.write_table(table, buffer)
        return {"parquet_bytes": buffer.getvalue()}

    def deserialize(self, data: Mapping[str, Any]) -> EventEnvelope[Any]:
        pq = _import_pyarrow_parquet()
        buffer = io.BytesIO(data["parquet_bytes"])
        table = pq.read_table(buffer)
        envelopes = self._arrow_codec.deserialize_batch(table)
        if len(envelopes) != 1:
            raise SerializationError(f"expected exactly one row, got {len(envelopes)}")
        return envelopes[0]

    def write_partitioned(
        self, envelopes: Sequence[EventEnvelope[Any]], root: Path
    ) -> Sequence[Path]:
        """Write ``envelopes`` under ``root``, partitioned by
        ``(site, event_type_code, date)``. ``site`` is read from each
        envelope's ``metadata.attributes["site"]`` (default ``"unknown"``
        when absent, since no first-class ``site`` field exists yet ahead
        of the Ontology Framework's ``Mine`` entity). Returns the paths written."""
        pq = _import_pyarrow_parquet()
        groups: dict[tuple[str, str, str], list[EventEnvelope[Any]]] = {}
        for envelope in envelopes:
            site = str(envelope.metadata.attributes.get("site", "unknown"))
            key = (
                site,
                envelope.payload.event_type_code,
                envelope.event_time_utc.date().isoformat(),
            )
            groups.setdefault(key, []).append(envelope)

        written: list[Path] = []
        for (site, event_type_code, date_str), group in groups.items():
            partition_dir = (
                root / f"site={site}" / f"event_type={event_type_code}" / f"date={date_str}"
            )
            partition_dir.mkdir(parents=True, exist_ok=True)
            table = self._arrow_codec.serialize_batch(group)
            file_path = partition_dir / "part-0.parquet"
            pq.write_table(table, file_path)
            written.append(file_path)
        return written

    def read_partitioned(self, root: Path) -> Sequence[EventEnvelope[Any]]:
        """Read back every envelope written under ``root`` by :meth:`write_partitioned`."""
        pq = _import_pyarrow_parquet()
        envelopes: list[EventEnvelope[Any]] = []
        for file_path in sorted(root.rglob("*.parquet")):
            table = pq.read_table(file_path)
            envelopes.extend(self._arrow_codec.deserialize_batch(table))
        return tuple(envelopes)
