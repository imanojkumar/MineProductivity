"""The Analytics registry -- a typed specialization of the generic
Registry Framework mechanism (design spec §32-§33), identical in shape
to ``kpis._registry`` (spec 05 AD-KP-06).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``registry.Registry`` is reused verbatim as the storage/lookup
primitive -- no bespoke registration container is introduced (ADR-0006's
own "Alternatives Rejected" section explicitly rejects "a bespoke
plugin/discovery mechanism specific to Analytics" for exactly this
reason: "the entire point of the Registry Framework is that every
domain package specializes the same mechanism"). ``register()``'s shape
mirrors ``kpis._registry.register()`` field-for-field: an empty-code
guard, then a single ``REGISTRY.register()`` call, translating a
``Result.err`` into a raised, Analytics-specific exception. The one
piece of ``kpis._registry`` deliberately **not** mirrored is its
``DependencyGraph``/circular-dependency check: that machinery exists
because a KPI can declare `dependencies` on other KPIs (kpis spec §26);
``AnalyticsMetadata`` (§31) has no such field -- an ``AnalyticsModel``
never depends on another registered strategy -- so there is no cycle to
detect and adding that machinery here would be an unused abstraction,
not genuine reuse.
"""

from __future__ import annotations

from mineproductivity.registry import Registry

from mineproductivity.analytics.abstractions import AnalyticsModel
from mineproductivity.analytics.exceptions import (
    AnalyticsValidationError,
    AnalyticsVersionConflictError,
)

__all__ = ["REGISTRY", "register"]

REGISTRY: Registry[str, type[AnalyticsModel]] = Registry(name="analytics")


def register(cls: type[AnalyticsModel]) -> type[AnalyticsModel]:
    """Register ``cls`` into :data:`REGISTRY`, keyed by ``cls.meta.code``.

    Raises
    ------
    AnalyticsValidationError
        If ``cls.meta.code`` is empty. In practice ``AnalyticsMetadata.validate()``
        already rejects an empty ``code`` at construction time (§31), so
        this is a defensive, redundant check -- kept anyway for the same
        reason ``kpis.register()`` keeps its own equivalent check: a
        cheap, explicit safety net at the one place every registration
        path funnels through, not reliant on every future caller having
        constructed ``meta`` the normal way.
    AnalyticsVersionConflictError
        If ``cls.meta.code`` is already registered. ``Registry.register()``
        is add-only and rejects *any* re-registration under an existing
        key, identical item or not (design spec AD-RG-04) -- this
        function does not attempt to distinguish "identical metadata,
        harmless re-import" from "materially different, dangerous
        repointing," exactly mirroring ``kpis.register()``'s own
        behavior, since the underlying ``Registry`` primitive draws no
        such distinction either. An ``AnalyticsModel`` code, like a KPI
        code, is a public contract once published (§33); it is never
        silently repointed to new behavior under the same code.
    """
    if not cls.meta.code:
        raise AnalyticsValidationError(f"{cls.__name__}.meta.code must not be empty")

    result = REGISTRY.register(cls.meta.code, cls, metadata=cls.meta)
    if result.is_err:
        raise AnalyticsVersionConflictError(
            f"AnalyticsModel code {cls.meta.code!r} is already registered; changing what it "
            f"means requires a new code or a reviewed version bump, not re-registration"
        )

    return cls
