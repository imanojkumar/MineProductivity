"""The Twin Registry -- a typed specialization of the generic Registry
Framework mechanism (design spec §17), identical in shape to
``decision._registry``/``analytics._registry``/``kpis._registry``
(spec 07 §32, spec 06 §33, spec 05 AD-KP-06).

This registry answers "which twin **types** does this installation know
about" -- a type-level question, entirely distinct from
``TwinRepository`` (design spec §20, an instance-level question: "which
twin **instances** currently exist") and from ``discovery.py`` (§18, a
query facade over that instance-level store). The three are related but
never conflated.

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``registry.Registry`` is reused verbatim as the storage/lookup
primitive -- no bespoke registration container is introduced (ADR-0008
explicitly reuses the same Registry Framework specialization mechanism
"exactly as ``decision.REGISTRY``, ``analytics.REGISTRY``, and
``kpis.REGISTRY`` already are"). ``register()``'s shape mirrors
``decision._registry.register()`` field-for-field: an empty-code guard,
then a single ``REGISTRY.register()`` call, translating a
``Result.err`` into a raised, Twin-specific exception.
"""

from __future__ import annotations

from mineproductivity.registry import Registry

from mineproductivity.digital_twin.abstractions import Twin
from mineproductivity.digital_twin.exceptions import (
    TwinValidationError,
    TwinVersionConflictError,
)

__all__ = ["REGISTRY", "register"]

REGISTRY: Registry[str, type[Twin]] = Registry(name="digital_twin")


def register(cls: type[Twin]) -> type[Twin]:
    """Register ``cls`` into :data:`REGISTRY`, keyed by ``cls.meta.code``.

    Raises
    ------
    TwinValidationError
        If ``cls.meta.code`` is empty. In practice ``TwinMetadata.validate()``
        already rejects an empty ``code`` at construction time (design
        spec §26), so this is a defensive, redundant check -- kept
        anyway for the same reason ``decision.register``/
        ``analytics.register``/``kpis.register`` keep their own
        equivalent check.
    TwinVersionConflictError
        If ``cls.meta.code`` is already registered. ``Registry.register()``
        is add-only and rejects *any* re-registration under an existing
        key, identical item or not (design spec AD-RG-04) -- this
        function does not attempt to distinguish "identical metadata,
        harmless re-import" from "materially different, dangerous
        repointing," exactly mirroring ``decision.register``'s own
        behavior.
    """
    if not cls.meta.code:
        raise TwinValidationError(f"{cls.__name__}.meta.code must not be empty")

    result = REGISTRY.register(cls.meta.code, cls, metadata=cls.meta)
    if result.is_err:
        raise TwinVersionConflictError(
            f"Twin type code {cls.meta.code!r} is already registered; changing what it "
            f"means requires a new code or a reviewed version bump, not re-registration"
        )

    return cls
