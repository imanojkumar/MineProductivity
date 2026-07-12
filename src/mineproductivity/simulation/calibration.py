"""``CalibrationModel``: interface-only extension point (design spec
§16) -- no concrete implementation ships in this package, by explicit
design.

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``digital_twin.TwinSnapshot`` is reused directly as the ground-truth
input shape (spec 08 §13) -- the same reuse of Digital Twin's
historical-capture concept ``Scenario.initial_state`` already makes
(design spec §9), applied here to calibration's need for "what
actually happened." Parameter fitting itself is an
optimization-adjacent technique this package's charter excludes (§3.1,
§4); a future ``optimization`` package is named as this interface's
most plausible first concrete implementer (§37, ADR-0009).

``CalibrationModel`` is deliberately **not** a ``SimulationModel``
subclass (design spec §8): calibration (fitting a model's parameters
against historical ground truth) is a conceptually distinct operation
from running a model forward, and forcing it under the same root would
blur that distinction the same way conflating
``decision.RankingStrategy`` with ``decision.ActionPrioritizer`` would
have (spec 07 §16, §20).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any

from mineproductivity.digital_twin import TwinSnapshot

from mineproductivity.simulation.abstractions import SimulationContext

__all__ = ["CalibrationModel"]


class CalibrationModel(ABC):
    """The contract a future calibration plugin implements: fit a
    registered ``SimulationModel``'s parameters against historical
    ground truth. THIS MODULE SHIPS NO CONCRETE SUBCLASS (design spec
    §16, §35's interface-purity proof)."""

    @abstractmethod
    def _calibrate(
        self,
        model_code: str,
        ground_truth: Sequence[TwinSnapshot],
        *,
        context: SimulationContext,
    ) -> Mapping[str, Any]:
        """Fit the registered model named by ``model_code`` against
        ``ground_truth``, returning the fitted parameter mapping a
        ``Scenario.parameters`` field can then carry -- no default
        implementation exists or is intended here (design spec §16)."""
