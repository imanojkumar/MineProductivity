"""``ModularConnector`` (Modular Mining) -- shape only."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import ClassVar

from mineproductivity.connectors.auth import AuthProvider
from mineproductivity.connectors.base import FMSConnector, IngestionMode
from mineproductivity.connectors.normalization import ReasonCodeMap
from mineproductivity.events import CycleEvent, DelayEvent
from mineproductivity.ontology import DelayCategory

__all__ = ["MODULAR_REASON_CODE_MAP", "ModularConnector"]

#: Illustrative only -- see :data:`~mineproductivity.connectors.oem.minestar_shape.MINESTAR_REASON_CODE_MAP`'s
#: docstring for the same caveat, applied to Modular Mining.
MODULAR_REASON_CODE_MAP = ReasonCodeMap(
    vendor_name="modular",
    mapping={
        "MAINT_UNPLANNED": (DelayCategory.EQUIPMENT, "unplanned maintenance"),
        "SURVEY": (DelayCategory.PROCESS, "survey/grade control hold"),
        "TRAFFIC": (DelayCategory.OPERATIONAL, "haul road congestion"),
    },
)


class ModularConnector(FMSConnector):
    """Shape only -- a real implementation lives in an independent
    plugin package with its own Modular Mining SDK dependency. This
    class documents the expected shape and constructor signature a
    conformant Modular Mining plugin should mirror; it is **not
    registered by default and has no working method bodies** -- both
    ``get_cycle_data`` and ``get_delay_data`` raise ``NotImplementedError``.
    """

    name: ClassVar[str] = "modular"
    vendor_name: ClassVar[str] = "modular"
    supported_modes: ClassVar[tuple[IngestionMode, ...]] = (
        IngestionMode.BATCH,
        IngestionMode.INCREMENTAL,
    )

    def __init__(self, host: str, auth: AuthProvider) -> None:
        self._host = host
        self._auth = auth

    def get_cycle_data(self, since: datetime, until: datetime) -> Iterable[CycleEvent]:
        raise NotImplementedError(
            "ModularConnector is a documentation-only shape. Implement a real "
            "Modular Mining integration as an independent plugin package, never "
            "inside mineproductivity.connectors."
        )

    def get_delay_data(self, since: datetime, until: datetime) -> Iterable[DelayEvent]:
        raise NotImplementedError(
            "ModularConnector is a documentation-only shape. Implement a real "
            "Modular Mining integration as an independent plugin package, never "
            "inside mineproductivity.connectors."
        )
