"""Where twins are stored (design spec §20) -- the persistence-backend
contract, as distinct from the wire/text-format concern §19 discusses.

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
The strongest reuse in this package's specification: ``TwinRepository``
is not a new ABC, not a structural echo, and not a subclass -- it
**is** ``core.BaseRepository[Twin, str]``, used directly, because
``Twin`` genuinely satisfies ``BaseRepository``'s
``TEntity: BaseEntity[Any]`` bound (design spec §3.4, §8, §20;
ADR-0008's recorded trade-off). The reference implementation is
``core.InMemoryRepository[Twin, str]()``, reused as-is with zero new
persistence code. A production-grade backend (SQL, document store)
implements ``core.BaseRepository[Twin, str]`` directly and MUST
serialize concurrent writes for the same ``id`` (§29); the bare
in-memory reference implementation provides no locking of its own and
is documented as suitable for tests/examples only.
"""

from __future__ import annotations

from mineproductivity.core import BaseRepository

from mineproductivity.digital_twin.abstractions import Twin

__all__ = ["TwinRepository"]

type TwinRepository = BaseRepository[Twin, str]
"""The storage contract for twin instances, keyed by their own
identity -- a literal ``type`` alias over
``core.BaseRepository[Twin, str]``, never a parallel digital-twin
repository ABC (design spec §20, §31's recorded anti-pattern)."""
