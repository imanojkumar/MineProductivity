"""``WencoConnector`` -- shape only. Named in the Cookbook as the
entry-point worked example (``wenco = "mineproductivity_wenco.connector:WencoConnector"``).
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import ClassVar

from mineproductivity.connectors.auth import AuthProvider
from mineproductivity.connectors.base import FMSConnector, IngestionMode
from mineproductivity.connectors.normalization import ReasonCodeMap
from mineproductivity.events import CycleEvent, DelayEvent
from mineproductivity.ontology import DelayCategory

__all__ = ["WENCO_REASON_CODE_MAP", "WencoConnector"]

#: Illustrative only -- see :data:`~mineproductivity.connectors.oem.minestar_shape.MINESTAR_REASON_CODE_MAP`'s
#: docstring for the same caveat, applied to Wenco.
WENCO_REASON_CODE_MAP = ReasonCodeMap(
    vendor_name="wenco",
    mapping={
        "BREAKDOWN": (DelayCategory.EQUIPMENT, "breakdown"),
        "STANDBY_NO_OP": (DelayCategory.STANDBY, "no operator available"),
        "FUEL": (DelayCategory.OPERATIONAL, "refuelling"),
    },
)


class WencoConnector(FMSConnector):
    """Shape only -- a real implementation lives in an independent
    plugin package with its own Wenco SDK dependency. This class
    documents the expected shape and constructor signature a conformant
    Wenco plugin should mirror; it is **not registered by default and
    has no working method bodies** -- both ``get_cycle_data`` and
    ``get_delay_data`` raise ``NotImplementedError``.
    """

    name: ClassVar[str] = "wenco"
    vendor_name: ClassVar[str] = "wenco"
    supported_modes: ClassVar[tuple[IngestionMode, ...]] = (
        IngestionMode.BATCH,
        IngestionMode.INCREMENTAL,
    )

    def __init__(self, host: str, auth: AuthProvider) -> None:
        self._host = host
        self._auth = auth

    def get_cycle_data(self, since: datetime, until: datetime) -> Iterable[CycleEvent]:
        raise NotImplementedError(
            "WencoConnector is a documentation-only shape. Implement a real "
            "Wenco integration as an independent plugin package (e.g. "
            "mineproductivity-wenco), never inside mineproductivity.connectors."
        )

    def get_delay_data(self, since: datetime, until: datetime) -> Iterable[DelayEvent]:
        raise NotImplementedError(
            "WencoConnector is a documentation-only shape. Implement a real "
            "Wenco integration as an independent plugin package (e.g. "
            "mineproductivity-wenco), never inside mineproductivity.connectors."
        )
