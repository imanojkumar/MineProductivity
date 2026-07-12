"""The Optimization Registry (design spec §21) -- a typed
specialization of ``registry.Registry``, identical in shape to every
sibling package's registry; the type-level question ("which model
types are known"), never conflated with ``OptimizationRunRepository``
(instance-level) or ``discovery.py`` (query facade).
"""

from __future__ import annotations

from mineproductivity.registry import Registry

from mineproductivity.optimization.abstractions import OptimizationModel
from mineproductivity.optimization.exceptions import (
    OptimizationValidationError,
    OptimizationVersionConflictError,
)

__all__ = ["REGISTRY", "register"]

REGISTRY: Registry[str, type[OptimizationModel]] = Registry(name="optimization")


def register(cls: type[OptimizationModel]) -> type[OptimizationModel]:
    """Register ``cls`` into :data:`REGISTRY`, keyed by
    ``cls.meta.code``.

    Raises
    ------
    OptimizationValidationError
        If ``cls.meta.code`` is empty (defensive, redundant guard --
        ``OptimizationMetadata.validate()`` already rejects it).
    OptimizationVersionConflictError
        If ``cls.meta.code`` is already registered -- add-only, raised
        at registration time, never deferred (design spec §25).
    """
    if not cls.meta.code:
        raise OptimizationValidationError(f"{cls.__name__}.meta.code must not be empty")

    result = REGISTRY.register(cls.meta.code, cls, metadata=cls.meta)
    if result.is_err:
        raise OptimizationVersionConflictError(
            f"OptimizationModel code {cls.meta.code!r} is already registered; changing "
            f"what it means requires a new code or a reviewed version bump, not "
            f"re-registration"
        )

    return cls
