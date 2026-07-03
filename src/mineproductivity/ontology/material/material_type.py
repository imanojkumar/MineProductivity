"""``MaterialType``: the three material classifications a mine moves."""

from __future__ import annotations

from enum import Enum

__all__ = ["MaterialType"]


class MaterialType(Enum):
    """Whether a given tonne of material is ore, waste, or a processed product."""

    ORE = "ore"
    WASTE = "waste"
    PRODUCT = "product"
