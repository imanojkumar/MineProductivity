"""``HexagonConnector`` -- shape only."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import ClassVar

from mineproductivity.connectors.auth import AuthProvider
from mineproductivity.connectors.base import FMSConnector, IngestionMode
from mineproductivity.connectors.normalization import ReasonCodeMap
from mineproductivity.events import CycleEvent, DelayEvent
from mineproductivity.ontology import DelayCategory

__all__ = ["HEXAGON_REASON_CODE_MAP", "HexagonConnector"]

#: Illustrative only -- see :data:`~mineproductivity.connectors.oem.minestar_shape.MINESTAR_REASON_CODE_MAP`'s
#: docstring for the same caveat, applied to Hexagon.
HEXAGON_REASON_CODE_MAP = ReasonCodeMap(
    vendor_name="hexagon",
    mapping={
        "PLANNED_MAINT": (DelayCategory.SCHEDULED, "planned maintenance"),
        "GPS_LOSS": (DelayCategory.EQUIPMENT, "positioning system fault"),
        "WX_HOLD": (DelayCategory.EXTERNAL, "weather hold"),
    },
)


class HexagonConnector(FMSConnector):
    """Shape only -- a real implementation lives in an independent
    plugin package with its own Hexagon SDK dependency. This class
    documents the expected shape and constructor signature a conformant
    Hexagon plugin should mirror; it is **not registered by default and
    has no working method bodies** -- both ``get_cycle_data`` and
    ``get_delay_data`` raise ``NotImplementedError``.
    """

    name: ClassVar[str] = "hexagon"
    vendor_name: ClassVar[str] = "hexagon"
    supported_modes: ClassVar[tuple[IngestionMode, ...]] = (
        IngestionMode.BATCH,
        IngestionMode.INCREMENTAL,
    )

    def __init__(self, host: str, auth: AuthProvider) -> None:
        self._host = host
        self._auth = auth

    def get_cycle_data(self, since: datetime, until: datetime) -> Iterable[CycleEvent]:
        raise NotImplementedError(
            "HexagonConnector is a documentation-only shape. Implement a real "
            "Hexagon integration as an independent plugin package, never inside "
            "mineproductivity.connectors."
        )

    def get_delay_data(self, since: datetime, until: datetime) -> Iterable[DelayEvent]:
        raise NotImplementedError(
            "HexagonConnector is a documentation-only shape. Implement a real "
            "Hexagon integration as an independent plugin package, never inside "
            "mineproductivity.connectors."
        )
