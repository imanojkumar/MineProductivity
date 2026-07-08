"""The eleven twin category base classes (design spec §9) -- the domain
model. Each contributes a namespace/category-check convention over
``Twin`` and no behavior beyond it, identical in spirit to ``kpis``'
nine category base classes (spec 05 §10.4: "each category base
contributes no behavior beyond documentation and a namespace convention
check... all real behavior lives in ``BaseKPI``").

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
The namespace-conformance mechanism mirrors
``kpis.categories._common.enforce_namespace`` exactly (an
``__init_subclass__`` hook checking ``meta.code``'s namespace prefix at
class-definition/import time, skipping abstract intermediates that
declare no ``meta`` of their own) -- reimplemented here as one small
module-private helper rather than imported, because ``kpis``' helper is
typed against ``type[BaseKPI]``/``KPIValidationError`` specifically and
raising a KPI exception from a digital-twin class definition would
misattribute the failure ("shape fits, coupling doesn't," the same
recorded reasoning as ``TwinStateCache`` vs. ``kpis.ResultCache``,
design spec §22). The check here additionally asserts ``meta.category``
is the base's own ``TwinCategory`` member, since -- unlike KPI metadata
-- ``TwinMetadata`` carries an explicit ``category`` field that must
agree with the base class the type subclasses (§26).
"""

from __future__ import annotations

from abc import ABC

from mineproductivity.digital_twin.abstractions import Twin
from mineproductivity.digital_twin.exceptions import TwinValidationError
from mineproductivity.digital_twin.metadata import TwinCategory

__all__ = [
    "ConveyorTwin",
    "EquipmentTwin",
    "FleetTwin",
    "GeologicalTwin",
    "HaulageTwin",
    "MineTwin",
    "PlantTwin",
    "ProcessingPlantTwin",
    "ProductionTwin",
    "StockpileTwin",
    "VentilationTwin",
]


def _enforce_category(cls: type[Twin], namespace: str, category: TwinCategory) -> None:
    """Raise if ``cls`` declares its own ``meta`` whose ``code`` does
    not fall in ``namespace`` or whose ``category`` is not ``category``
    -- runs from each category base's ``__init_subclass__``, so a
    violation fails at class-definition (import) time, not first use.
    Abstract intermediates that do not yet declare their own ``meta``
    are skipped -- the check only applies once a class actually claims
    a code."""
    if "meta" not in cls.__dict__:
        return
    code = cls.meta.code
    if not (code == namespace or code.startswith(f"{namespace}.")):
        raise TwinValidationError(
            f"{cls.__name__}.meta.code {code!r} must fall in the {namespace!r} namespace"
        )
    if cls.meta.category is not category:
        raise TwinValidationError(
            f"{cls.__name__}.meta.category must be {category!r}, got {cls.meta.category!r}"
        )


class MineTwin(Twin, ABC):
    """A whole-mine virtual counterpart -- aggregates state across every
    other twin category scoped to the same mine."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        _enforce_category(cls, "MINE", TwinCategory.MINE)


class EquipmentTwin(Twin, ABC):
    """A single piece of equipment -- scope typically names one
    ``ontology.RigidHaulTruck``/``HydraulicShovel``/etc. instance."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        _enforce_category(cls, "EQUIPMENT", TwinCategory.EQUIPMENT)


class PlantTwin(Twin, ABC):
    """A processing/beneficiation plant as a whole, distinct from
    ``ProcessingPlantTwin``'s narrower processing-circuit framing."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        _enforce_category(cls, "PLANT", TwinCategory.PLANT)


class ConveyorTwin(Twin, ABC):
    """A conveyor system -- scope names an ``ontology.Conveyor``
    instance."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        _enforce_category(cls, "CONVEYOR", TwinCategory.CONVEYOR)


class HaulageTwin(Twin, ABC):
    """The haulage system (routes, cycle state) distinct from any one
    ``EquipmentTwin`` -- an aggregate view over a haul fleet's
    operation."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        _enforce_category(cls, "HAULAGE", TwinCategory.HAULAGE)


class FleetTwin(Twin, ABC):
    """A fleet as a whole -- scope names an ``ontology.Fleet``
    instance."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        _enforce_category(cls, "FLEET", TwinCategory.FLEET)


class ProcessingPlantTwin(Twin, ABC):
    """A specific processing circuit's live state (throughput, recovery
    inputs) -- narrower than ``PlantTwin``'s whole-plant framing."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        _enforce_category(cls, "PROCESSING_PLANT", TwinCategory.PROCESSING_PLANT)


class GeologicalTwin(Twin, ABC):
    """The geological/orebody model's currently-understood state."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        _enforce_category(cls, "GEOLOGICAL", TwinCategory.GEOLOGICAL)


class VentilationTwin(Twin, ABC):
    """A ventilation system's live state (airflow, gas readings)."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        _enforce_category(cls, "VENTILATION", TwinCategory.VENTILATION)


class StockpileTwin(Twin, ABC):
    """A stockpile's current volume/grade/quality state."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        _enforce_category(cls, "STOCKPILE", TwinCategory.STOCKPILE)


class ProductionTwin(Twin, ABC):
    """A production system's aggregate live state, distinct from any
    one ``EquipmentTwin``/``ConveyorTwin`` feeding it."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        _enforce_category(cls, "PRODUCTION", TwinCategory.PRODUCTION)
