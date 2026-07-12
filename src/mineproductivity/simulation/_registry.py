"""The Simulation Registry -- a typed specialization of the generic
Registry Framework mechanism (design spec §21), identical in shape to
``digital_twin._registry``/``decision._registry``/``analytics._registry``
(spec 08 §17, spec 07 §32, spec 06 §33).

This registry answers "which simulation model **types** does this
installation know about" -- a type-level question, entirely distinct
from ``SimulationRunRepository`` (design spec §24, an instance-level
question: "which runs currently exist") and from ``discovery.py``
(§22, a query facade over that instance-level store). The three are
related but never conflated (§21).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``registry.Registry`` is reused verbatim as the storage/lookup
primitive -- no bespoke registration container is introduced;
``register()``'s shape mirrors ``digital_twin._registry.register()``
field-for-field.
"""

from __future__ import annotations

from mineproductivity.registry import Registry

from mineproductivity.simulation.abstractions import SimulationModel
from mineproductivity.simulation.exceptions import (
    SimulationValidationError,
    SimulationVersionConflictError,
)

__all__ = ["REGISTRY", "register"]

REGISTRY: Registry[str, type[SimulationModel]] = Registry(name="simulation")


def register(cls: type[SimulationModel]) -> type[SimulationModel]:
    """Register ``cls`` into :data:`REGISTRY`, keyed by ``cls.meta.code``.

    Raises
    ------
    SimulationValidationError
        If ``cls.meta.code`` is empty -- a defensive, redundant check
        (``SimulationMetadata.validate()`` already rejects it at
        construction time), kept for the same reason every sibling
        package's ``register`` keeps its own equivalent.
    SimulationVersionConflictError
        If ``cls.meta.code`` is already registered.
        ``Registry.register()`` is add-only and rejects *any*
        re-registration under an existing key, identical item or not
        (design spec AD-RG-04) -- raised at registration time, never
        deferred (§25).
    """
    if not cls.meta.code:
        raise SimulationValidationError(f"{cls.__name__}.meta.code must not be empty")

    result = REGISTRY.register(cls.meta.code, cls, metadata=cls.meta)
    if result.is_err:
        raise SimulationVersionConflictError(
            f"SimulationModel code {cls.meta.code!r} is already registered; changing what "
            f"it means requires a new code or a reviewed version bump, not re-registration"
        )

    return cls
