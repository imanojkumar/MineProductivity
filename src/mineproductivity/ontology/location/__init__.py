"""Location ontology: mine structure, surface and underground."""

from __future__ import annotations

from mineproductivity.ontology.location.mine import Mine
from mineproductivity.ontology.location.pit import Bench, Pit
from mineproductivity.ontology.location.route import Route, Zone
from mineproductivity.ontology.location.underground import Drive, Level, Stope

__all__ = ["Bench", "Drive", "Level", "Mine", "Pit", "Route", "Stope", "Zone"]
