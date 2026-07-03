"""``CSVConnector``: the reference implementation of the minimal
``FMSConnector`` contract.
"""

from __future__ import annotations

import csv
import logging
from collections.abc import Callable, Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import ClassVar, TypeVar

from mineproductivity.connectors.base import FMSConnector, IngestionMode
from mineproductivity.connectors.exceptions import MappingError, SourceUnavailableError
from mineproductivity.connectors.file._common import FileRowNormalizer, parse_source_datetime
from mineproductivity.connectors.health import ConnectorHealth, HealthStatus
from mineproductivity.connectors.normalization import Normalizer
from mineproductivity.events import CycleEvent, DelayEvent

__all__ = ["CSVConnector"]

_logger = logging.getLogger(__name__)
_TEvent = TypeVar("_TEvent")


class CSVConnector(FMSConnector):
    """Reads a haul-cycle (and, optionally, delay) CSV export -- the
    reference implementation of the minimal ``FMSConnector`` contract.
    See Cookbook Part I, Ch. 7 for the full worked version this class's
    shape is drawn from.

    Two source files, not one, because a real FMS export typically ships
    cycles and delays as separate homogeneous-schema files rather than
    interleaved rows of different shapes; ``delay_path`` is optional
    since some sources (like a cycle-only export) have no delay data.

    Expected columns -- cycles: ``event_time, equipment_id, queue_min,
    spot_min, load_min, haul_min, dump_min, return_min, payload_t``,
    plus optional ``route_id, operator_id, material_type``. Delays:
    ``event_time, equipment_id, delay_category, delay_reason,
    duration_min``, where ``delay_category`` is a
    :class:`~mineproductivity.ontology.DelayCategory` member name.

    Not thread-safe for concurrent calls against the same instance --
    each call re-opens and re-reads its source file independently;
    construct one instance per worker for concurrent ingestion (design
    spec §24).
    """

    name: ClassVar[str] = "csv"
    supported_modes: ClassVar[tuple[IngestionMode, ...]] = (IngestionMode.BATCH,)

    def __init__(
        self,
        path: str | Path,
        shift_id: str,
        *,
        delay_path: str | Path | None = None,
        source_timezone: str = "UTC",
        normalizer: Normalizer | None = None,
    ) -> None:
        self._path = Path(path)
        self._delay_path = Path(delay_path) if delay_path is not None else None
        self._shift_id = shift_id
        self._source_timezone = source_timezone
        self._normalizer: Normalizer = normalizer if normalizer is not None else FileRowNormalizer()
        self._last_successful_pull_utc: datetime | None = None
        self._last_status: HealthStatus = HealthStatus.UNKNOWN

    def get_cycle_data(self, since: datetime, until: datetime) -> Iterator[CycleEvent]:
        yield from self._read(self._path, since, until, self._normalizer.normalize_cycle)

    def get_delay_data(self, since: datetime, until: datetime) -> Iterator[DelayEvent]:
        if self._delay_path is None:
            return
        yield from self._read(self._delay_path, since, until, self._normalizer.normalize_delay)

    def _read(
        self,
        path: Path,
        since: datetime,
        until: datetime,
        normalize: Callable[[dict[str, str | None]], _TEvent],
    ) -> Iterator[_TEvent]:
        if not path.exists():
            self._last_status = HealthStatus.UNHEALTHY
            raise SourceUnavailableError(f"CSV source not found: {path}")
        try:
            with path.open(newline="", encoding="utf-8") as handle:
                self._last_status = HealthStatus.HEALTHY
                self._last_successful_pull_utc = datetime.now(tz=timezone.utc)
                reader = csv.DictReader(handle)
                for row in reader:
                    raw_time = row.get("event_time")
                    if not raw_time:
                        _logger.warning("row missing event_time, skipped: %r", row)
                        continue
                    try:
                        event_time = parse_source_datetime(
                            raw_time, source_timezone=self._source_timezone
                        )
                    except MappingError as exc:
                        _logger.warning("unparseable event_time, row skipped: %s", exc)
                        continue
                    if not (since <= event_time < until):
                        continue
                    raw = {**row, "shift_id": self._shift_id}
                    try:
                        yield normalize(raw)
                    except MappingError as exc:
                        _logger.warning("row failed to normalize and was skipped: %s", exc)
                        continue
        except OSError as exc:
            self._last_status = HealthStatus.UNHEALTHY
            raise SourceUnavailableError(f"failed to read {path}: {exc}") from exc

    def health_check(self) -> ConnectorHealth:
        return ConnectorHealth(
            status=self._last_status,
            last_successful_pull_utc=self._last_successful_pull_utc,
        )
