"""Serialization codecs for :class:`~mineproductivity.events.envelope.EventEnvelope`.

Three format contracts, each implementing
:class:`~mineproductivity.core.serialization.BaseSerializer`: JSON (no
extra dependency), Arrow, and Parquet (both requiring the optional
``pyarrow`` dependency, imported lazily -- see each codec's own
docstring).
"""

from __future__ import annotations

from mineproductivity.events.serialization.arrow_codec import ArrowEventCodec
from mineproductivity.events.serialization.json_codec import JSONEventCodec
from mineproductivity.events.serialization.parquet_codec import ParquetEventCodec

__all__ = ["ArrowEventCodec", "JSONEventCodec", "ParquetEventCodec"]
