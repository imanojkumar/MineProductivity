"""OEM adapter shapes -- documentation-only mapping/constructor contracts
for MineStar, DISPATCH, Wenco, Modular Mining, and Hexagon. No working
vendor SDK code exists here or is implied by this subpackage; a real OEM
plugin lives entirely outside this repository, as its own installable
package (design spec §6, AD-CN-03).
"""

from __future__ import annotations

from mineproductivity.connectors.oem.dispatch_shape import (
    DISPATCH_REASON_CODE_MAP,
    DispatchConnector,
)
from mineproductivity.connectors.oem.hexagon_shape import HEXAGON_REASON_CODE_MAP, HexagonConnector
from mineproductivity.connectors.oem.minestar_shape import (
    MINESTAR_REASON_CODE_MAP,
    MineStarConnector,
)
from mineproductivity.connectors.oem.modular_shape import MODULAR_REASON_CODE_MAP, ModularConnector
from mineproductivity.connectors.oem.wenco_shape import WENCO_REASON_CODE_MAP, WencoConnector

__all__ = [
    "DISPATCH_REASON_CODE_MAP",
    "HEXAGON_REASON_CODE_MAP",
    "MINESTAR_REASON_CODE_MAP",
    "MODULAR_REASON_CODE_MAP",
    "WENCO_REASON_CODE_MAP",
    "DispatchConnector",
    "HexagonConnector",
    "MineStarConnector",
    "ModularConnector",
    "WencoConnector",
]
