"""``DispatchConnector`` (Modular Mining's DISPATCH) -- shape only."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import ClassVar

from mineproductivity.connectors.auth import AuthProvider
from mineproductivity.connectors.base import FMSConnector, IngestionMode
from mineproductivity.connectors.normalization import ReasonCodeMap
from mineproductivity.events import CycleEvent, DelayEvent
from mineproductivity.ontology import DelayCategory

__all__ = ["DISPATCH_REASON_CODE_MAP", "DispatchConnector"]

#: Illustrative only -- see :data:`~mineproductivity.connectors.oem.minestar_shape.MINESTAR_REASON_CODE_MAP`'s
#: docstring for the same caveat, applied to DISPATCH.
DISPATCH_REASON_CODE_MAP = ReasonCodeMap(
    vendor_name="dispatch",
    mapping={
        "EQ_DOWN": (DelayCategory.EQUIPMENT, "equipment down"),
        "SHIFT_CHG": (DelayCategory.SCHEDULED, "shift change"),
        "BLAST": (DelayCategory.PROCESS, "blast clearance"),
    },
)


class DispatchConnector(FMSConnector):
    """Shape only -- a real implementation lives in an independent
    plugin package with its own DISPATCH SDK dependency. This class
    documents the expected shape and constructor signature a conformant
    DISPATCH plugin should mirror; it is **not registered by default and
    has no working method bodies** -- both ``get_cycle_data`` and
    ``get_delay_data`` raise ``NotImplementedError``.
    """

    name: ClassVar[str] = "dispatch"
    vendor_name: ClassVar[str] = "dispatch"
    supported_modes: ClassVar[tuple[IngestionMode, ...]] = (
        IngestionMode.BATCH,
        IngestionMode.INCREMENTAL,
    )

    def __init__(self, host: str, auth: AuthProvider) -> None:
        self._host = host
        self._auth = auth

    def get_cycle_data(self, since: datetime, until: datetime) -> Iterable[CycleEvent]:
        raise NotImplementedError(
            "DispatchConnector is a documentation-only shape. Implement a real "
            "DISPATCH integration as an independent plugin package, never inside "
            "mineproductivity.connectors."
        )

    def get_delay_data(self, since: datetime, until: datetime) -> Iterable[DelayEvent]:
        raise NotImplementedError(
            "DispatchConnector is a documentation-only shape. Implement a real "
            "DISPATCH integration as an independent plugin package, never inside "
            "mineproductivity.connectors."
        )
