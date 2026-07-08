"""``TwinStatus``: the twin instance's own operational lifecycle
(design spec §10) -- distinct from ``TwinMetadata.version``'s type-level
SemVer (§21).
"""

from __future__ import annotations

from enum import Enum

__all__ = ["TwinStatus"]


class TwinStatus(Enum):
    """The twin INSTANCE's own operational lifecycle -- distinct from
    ``TwinMetadata.version``'s type-level SemVer (design spec §21) and
    from ``Policy``-style governance lifecycles
    (``decision.DecisionStatus``, spec 07 §12) that do not apply here at
    all, since a ``Twin`` instance is not a governed business artifact.

    ``RETIRED`` is terminal -- a retired twin's ``id`` is never reused
    for a different real-world thing, mirroring the "a retired
    identifier is never reused for a new meaning" rule ``kpis`` already
    established for KPI codes (spec 05 §20). :class:`~mineproductivity.digital_twin.synchronization.TwinSynchronizer`
    refuses to fold further events into a retired twin (§10, §24).
    """

    PROVISIONED = "provisioned"
    SYNCHRONIZED = "synchronized"
    STALE = "stale"
    DEGRADED = "degraded"
    RETIRED = "retired"
