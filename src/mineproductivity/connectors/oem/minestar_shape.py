"""``MineStarConnector`` -- shape only. See module-level warning below."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import ClassVar

from mineproductivity.connectors.auth import AuthProvider
from mineproductivity.connectors.base import FMSConnector, IngestionMode
from mineproductivity.connectors.normalization import ReasonCodeMap
from mineproductivity.events import CycleEvent, DelayEvent
from mineproductivity.ontology import DelayCategory

__all__ = ["MINESTAR_REASON_CODE_MAP", "MineStarConnector"]

#: Illustrative only -- a handful of example MineStar delay-reason codes,
#: not an exhaustive or vendor-verified mapping. A real MineStar plugin
#: package owns and maintains its own complete, vendor-verified
#: :class:`~mineproductivity.connectors.normalization.ReasonCodeMap`.
MINESTAR_REASON_CODE_MAP = ReasonCodeMap(
    vendor_name="minestar",
    mapping={
        "MECH_FAIL": (DelayCategory.EQUIPMENT, "mechanical failure"),
        "OP_BREAK": (DelayCategory.OPERATIONAL, "operator break"),
        "WEATHER": (DelayCategory.EXTERNAL, "weather stand-down"),
    },
)


class MineStarConnector(FMSConnector):
    """Shape only -- a real implementation lives in an independent
    plugin package with its own MineStar SDK dependency, per Cookbook
    Part I, Ch. 7's "conceptual outline." This class exists in this
    package only as documentation of the expected shape and constructor
    signature a conformant MineStar plugin should mirror; it is **not
    registered by default and has no working method bodies** -- both
    ``get_cycle_data`` and ``get_delay_data`` raise ``NotImplementedError``.
    """

    name: ClassVar[str] = "minestar"
    vendor_name: ClassVar[str] = "minestar"
    supported_modes: ClassVar[tuple[IngestionMode, ...]] = (
        IngestionMode.BATCH,
        IngestionMode.INCREMENTAL,
    )

    def __init__(self, host: str, auth: AuthProvider) -> None:
        self._host = host
        self._auth = auth

    def get_cycle_data(self, since: datetime, until: datetime) -> Iterable[CycleEvent]:
        raise NotImplementedError(
            "MineStarConnector is a documentation-only shape. Implement a real "
            "MineStar integration as an independent plugin package (e.g. "
            "mineproductivity-minestar), never inside mineproductivity.connectors."
        )

    def get_delay_data(self, since: datetime, until: datetime) -> Iterable[DelayEvent]:
        raise NotImplementedError(
            "MineStarConnector is a documentation-only shape. Implement a real "
            "MineStar integration as an independent plugin package (e.g. "
            "mineproductivity-minestar), never inside mineproductivity.connectors."
        )
