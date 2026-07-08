"""The Decision registry -- a typed specialization of the generic
Registry Framework mechanism (design spec §32), identical in shape to
``analytics._registry``/``kpis._registry`` (design spec §32, spec 06
§33, spec 05 AD-KP-06).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``registry.Registry`` is reused verbatim as the storage/lookup
primitive -- no bespoke registration container is introduced (ADR-0007
explicitly reuses the same Registry Framework specialization mechanism
"identical" to every other extension point, §32). ``register()``'s
shape mirrors ``analytics._registry.register()``/``kpis._registry.register()``
field-for-field: an empty-code guard, then a single
``REGISTRY.register()`` call, translating a ``Result.err`` into a
raised, Decision-specific exception. No ``DependencyGraph``-equivalent
machinery is added here either, for the same reason ``analytics``
omitted it: ``DecisionMetadata`` (§30) has no ``dependencies`` field --
a ``DecisionModel`` never depends on another registered strategy.
"""

from __future__ import annotations

from mineproductivity.registry import Registry

from mineproductivity.decision.abstractions import DecisionModel
from mineproductivity.decision.exceptions import (
    DecisionValidationError,
    DecisionVersionConflictError,
)

__all__ = ["REGISTRY", "register"]

REGISTRY: Registry[str, type[DecisionModel]] = Registry(name="decision")


def register(cls: type[DecisionModel]) -> type[DecisionModel]:
    """Register ``cls`` into :data:`REGISTRY`, keyed by ``cls.meta.code``.

    Raises
    ------
    DecisionValidationError
        If ``cls.meta.code`` is empty. In practice ``DecisionMetadata.validate()``
        already rejects an empty ``code`` at construction time (§30), so
        this is a defensive, redundant check -- kept anyway for the same
        reason ``analytics.register``/``kpis.register`` keep their own
        equivalent check.
    DecisionVersionConflictError
        If ``cls.meta.code`` is already registered. ``Registry.register()``
        is add-only and rejects *any* re-registration under an existing
        key, identical item or not (design spec AD-RG-04) -- this
        function does not attempt to distinguish "identical metadata,
        harmless re-import" from "materially different, dangerous
        repointing," exactly mirroring ``analytics.register``'s own
        behavior.
    """
    if not cls.meta.code:
        raise DecisionValidationError(f"{cls.__name__}.meta.code must not be empty")

    result = REGISTRY.register(cls.meta.code, cls, metadata=cls.meta)
    if result.is_err:
        raise DecisionVersionConflictError(
            f"DecisionModel code {cls.meta.code!r} is already registered; changing what it "
            f"means requires a new code or a reviewed version bump, not re-registration"
        )

    return cls
