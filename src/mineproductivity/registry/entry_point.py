"""``EntryPointSpec``/``EntryPointDiscovery``: the runtime mechanism behind
"a plugin declares itself in its pyproject.toml, and on install it
appears in the relevant registry" (Cookbook Part I, Ch. 3 and Ch. 9).
"""

from __future__ import annotations

import dataclasses
import importlib.metadata
import logging
from collections.abc import Sequence

from mineproductivity.core import BaseValueObject, Result, ValidationError

__all__ = ["EntryPointDiscovery", "EntryPointSpec"]

_logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True, slots=True)
class EntryPointSpec(BaseValueObject):
    """One discoverable entry-point group, e.g.
    ``EntryPointSpec(group="mineproductivity.connectors", target_registry="connectors")``.
    """

    group: str
    target_registry: str

    def validate(self) -> None:
        if not self.group.strip():
            raise ValidationError("EntryPointSpec.group must not be empty")
        if not self.target_registry.strip():
            raise ValidationError("EntryPointSpec.target_registry must not be empty")


class EntryPointDiscovery:
    """Scans installed packages' entry-points (via :mod:`importlib.metadata`)
    and imports each one, running whatever ``@register``-decorated side
    effects the imported module contains.

    An exception raised while importing any *one* entry-point's target
    module is caught, logged, and skipped -- it MUST NOT prevent
    discovery of the remaining entry-points in the same group (design
    spec §11, §26, the isolation rule: "a mine with 30 installed KPI
    packs cannot have its whole platform go down because pack #17 has a
    typo").
    """

    def discover(self, spec: EntryPointSpec) -> Result[Sequence[str]]:
        """Import every entry-point in ``spec.group``.

        Returns
        -------
        Result[Sequence[str]]
            ``Result.ok`` wrapping the names of the entry-points that
            imported successfully (in entry-point-name order), or
            ``Result.err`` if the entry-point scan itself failed (e.g. a
            corrupted installed-package metadata database) -- a
            systemic failure distinct from any single entry-point's
            import error, which is isolated rather than propagated.
        """
        try:
            entry_points = importlib.metadata.entry_points(group=spec.group)
        except Exception as exc:  # pragma: no cover - defensive, metadata corruption
            return Result.err(exc)

        loaded: list[str] = []
        for entry_point in sorted(entry_points, key=lambda ep: ep.name):
            try:
                entry_point.load()
            except Exception as exc:
                _logger.warning(
                    "entry point %r in group %r failed to load and was skipped: %s",
                    entry_point.name,
                    spec.group,
                    exc,
                )
                continue
            loaded.append(entry_point.name)
        return Result.ok(tuple(loaded))
