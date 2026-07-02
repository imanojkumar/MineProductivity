"""``ArrowEventCodec``: converts :class:`EventEnvelope` instances to and from Apache Arrow."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

from mineproductivity.core import BaseSerializer, SerializationError

from mineproductivity.events.envelope import EventEnvelope
from mineproductivity.events.serialization.json_codec import JSONEventCodec

if TYPE_CHECKING:
    import pyarrow as pa

__all__ = ["ArrowEventCodec"]


def _import_pyarrow() -> Any:
    try:
        import pyarrow as pa
    except ImportError as exc:  # pragma: no cover - exercised only without the extra installed
        raise SerializationError(
            "ArrowEventCodec requires the optional 'pyarrow' dependency. "
            'Install it with: pip install "mineproductivity[events]"'
        ) from exc
    return pa


class ArrowEventCodec(BaseSerializer[EventEnvelope[Any]]):
    """Converts :class:`~mineproductivity.events.envelope.EventEnvelope`
    instances to and from `Apache Arrow <https://arrow.apache.org/>`_
    in-memory columnar batches -- zero-copy interchange with vectorized
    engines (Polars/DuckDB/pandas) that a future ``kpis`` package will
    execute over.

    ``pyarrow`` is an optional dependency (the ``events`` extra); it is
    imported lazily, only when a method on this class actually runs, so
    ``import mineproductivity.events`` never requires it.

    Implements :class:`~mineproductivity.core.serialization.BaseSerializer`'s
    single-envelope contract (each envelope becomes/comes from a one-row
    Arrow table) plus batch-oriented :meth:`serialize_batch`/
    :meth:`deserialize_batch` methods, which are where Arrow's columnar
    efficiency actually matters: one :class:`RecordBatch` per event type,
    per the Event Framework design specification's guidance.
    """

    def __init__(self) -> None:
        self._json_codec = JSONEventCodec()

    def serialize(self, obj: EventEnvelope[Any]) -> Mapping[str, Any]:
        pa = _import_pyarrow()
        table = self._batch_to_table(pa, [obj])
        return {"table": table}

    def deserialize(self, data: Mapping[str, Any]) -> EventEnvelope[Any]:
        envelopes = self.deserialize_batch(data["table"])
        if len(envelopes) != 1:
            raise SerializationError(f"expected exactly one row, got {len(envelopes)}")
        return envelopes[0]

    def serialize_batch(self, envelopes: Sequence[EventEnvelope[Any]]) -> "pa.Table":
        """Convert many envelopes of (expectedly) the same event type
        into one Arrow ``Table`` -- the efficient, intended usage."""
        pa = _import_pyarrow()
        return self._batch_to_table(pa, envelopes)

    def deserialize_batch(self, table: "pa.Table") -> Sequence[EventEnvelope[Any]]:
        """Reconstruct envelopes from an Arrow ``Table`` produced by :meth:`serialize_batch`."""
        rows = table.to_pylist()
        for row in rows:
            row["metadata"] = dict(row["metadata"])
            row["metadata"]["attributes"] = json.loads(row["metadata"]["attributes"])
        return tuple(self._json_codec.deserialize(row) for row in rows)

    def _batch_to_table(self, pa: Any, envelopes: Sequence[EventEnvelope[Any]]) -> "pa.Table":
        rows = [self._json_codec.serialize(envelope) for envelope in envelopes]
        if not rows:
            return pa.table({})
        # metadata.attributes is an open-ended mapping; when every row's
        # attributes happen to be empty, Arrow infers a zero-child struct
        # type that Parquet cannot physically write ("Cannot write struct
        # type with no child field"). Encoding it as a JSON string column
        # sidesteps that Arrow/Parquet limitation entirely.
        for row in rows:
            row["metadata"] = dict(row["metadata"])
            row["metadata"]["attributes"] = json.dumps(row["metadata"]["attributes"])
        columns = {key: [row[key] for row in rows] for key in rows[0]}
        return pa.table(columns)
