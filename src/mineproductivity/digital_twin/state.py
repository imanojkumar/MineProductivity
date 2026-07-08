"""``TwinState``: one twin's condition as of the moment it was last
synchronized (design spec §12).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``core.BaseValueObject`` is reused verbatim as the base, and the
``MappingProxyType``-freezing convention for ``Mapping``-typed fields is
reused exactly as ``decision.result``/``analytics.result`` already
established -- no new value-object base or mapping-freezing mechanism is
introduced. ``attributes`` is deliberately an open ``Mapping[str, Any]``
rather than a large, category-spanning set of typed fields (a
``ConveyorTwin``'s attributes -- belt speed, load -- share nothing
structurally with a ``StockpileTwin``'s -- volume, grade), mirroring
``kpis.KPIMetadata.attributes``' own "documented shape within an open
mapping" convention for fields that do not warrant a first-class typed
slot platform-wide (spec 05 §10.1).
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from datetime import datetime
from types import MappingProxyType
from typing import Any

from mineproductivity.core import BaseValueObject

from mineproductivity.digital_twin.exceptions import TwinValidationError

__all__ = ["TwinState"]


@dataclasses.dataclass(frozen=True, slots=True)
class TwinState(BaseValueObject):
    """One twin's condition as of the moment it was last synchronized.
    A frozen value object, not an entity -- the entity (continuous
    identity over time) is ``Twin`` itself (design spec §8);
    ``TwinState`` is what a ``Twin`` currently points to, exactly the
    identity/value distinction ``core.entity``/``core.value_object``
    already draw platform-wide.

    ``schema_version`` (§21's third versioning axis) is the
    shape-version of ``attributes``' contents, carried with the value
    itself -- never inferred from ``TwinMetadata.version`` at read time
    -- so a future ``_apply`` revision that changes which keys it
    populates can detect and migrate an older ``TwinState`` it reads
    back from a ``TwinRepository``/``TwinSnapshot``.

    Examples
    --------
    >>> from datetime import timezone
    >>> state = TwinState(
    ...     attributes={"belt_speed_mps": 3.1, "load_tph": 850.0},
    ...     captured_at=datetime(2026, 7, 8, tzinfo=timezone.utc),
    ... )
    >>> state.attributes["belt_speed_mps"]
    3.1
    >>> state.schema_version
    '1.0.0'
    >>> TwinState(attributes={}, captured_at=datetime(2026, 7, 8, tzinfo=timezone.utc))
    Traceback (most recent call last):
        ...
    mineproductivity.digital_twin.exceptions.TwinValidationError: TwinState.attributes must not be empty
    """

    attributes: Mapping[str, Any]
    captured_at: datetime
    schema_version: str = "1.0.0"

    def _normalize(self) -> None:
        super(TwinState, self)._normalize()
        object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))

    def validate(self) -> None:
        if not self.attributes:
            raise TwinValidationError("TwinState.attributes must not be empty")
