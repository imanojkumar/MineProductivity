"""A third-party-style ``Twin`` type registered via entry points,
mirroring ``examples/registry/01_register_and_discover.py``'s pattern
-- the exact wiring design spec 08 sec. 28 prescribes:

    [project.entry-points."mineproductivity.digital_twin"]
    sitepack = "mineproductivity_sitepack.digital_twin"

The "discover" step needs a real, importable module whose top-level
code runs ``digital_twin.register`` as a side effect of import --
exactly what happens when a real site-pack package is installed and its
entry-point is scanned. This example writes a small, real ``.py`` file
to a temp directory and discovers it through the exact same
``registry.EntryPointDiscovery`` code path a pip-installed plugin would
go through -- no shortcuts, no faked registration.

Run: python examples/digital_twin/04_plugin_twin_type.py
"""

from __future__ import annotations

import importlib.metadata
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from mineproductivity.digital_twin import REGISTRY, TwinMetadata, TwinState, TwinStatus
from mineproductivity.registry import EntryPointDiscovery, EntryPointSpec

MOMENT = datetime(2026, 7, 8, 6, 0, tzinfo=timezone.utc)

_PLUGIN_SOURCE = '''\
"""A site pack's own ventilation twin type -- importing this module
registers it, exactly as a pip-installed plugin's entry-point scan
would."""

from collections.abc import Sequence
from typing import ClassVar

from mineproductivity.digital_twin import (
    TwinCategory,
    TwinContext,
    TwinMetadata,
    TwinState,
    VentilationTwin,
    register,
)
from mineproductivity.events import BaseEvent


@register
class SitePackVentilationTwin(VentilationTwin):
    """A site pack's underground ventilation-circuit twin, tracking
    airflow and gas readings folded from the event stream."""

    meta: ClassVar[TwinMetadata] = TwinMetadata(
        code="VENTILATION.SitePackCircuit",
        category=TwinCategory.VENTILATION,
        description=(
            "A site pack's underground ventilation-circuit twin, tracking "
            "airflow and gas readings folded from the event stream."
        ),
    )

    def _apply(self, events: Sequence[BaseEvent], *, context: TwinContext) -> TwinState:
        return self.state
'''


def main() -> None:
    print("--- 1. digital_twin ships zero built-in twin types ---")
    print(f"registered before discovery: {sorted(code for code in REGISTRY)}")
    print("(a concrete twin type is a site-specific modeling choice, spec 08 sec. 27)")

    print()
    print("--- 2. A site pack declares its twin type via a pyproject.toml entry-point ---")
    print("(a real, on-disk module -- the same EntryPointDiscovery code path")
    print(" a pip-installed plugin uses)")

    with tempfile.TemporaryDirectory() as tmp_dir:
        plugin_path = Path(tmp_dir) / "_example_sitepack_digital_twin.py"
        plugin_path.write_text(_PLUGIN_SOURCE, encoding="utf-8")
        sys.path.insert(0, tmp_dir)
        try:
            real_entry_points = importlib.metadata.entry_points

            def _fake_entry_points(*, group: str):  # type: ignore[no-untyped-def]
                if group == "mineproductivity.digital_twin":
                    return (
                        importlib.metadata.EntryPoint(
                            name="sitepack", value="_example_sitepack_digital_twin", group=group
                        ),
                    )
                return real_entry_points(group=group)

            importlib.metadata.entry_points = _fake_entry_points  # type: ignore[assignment]
            try:
                discovery = EntryPointDiscovery()
                spec = EntryPointSpec(
                    group="mineproductivity.digital_twin", target_registry="digital_twin"
                )
                discover_result = discovery.discover(spec)
            finally:
                importlib.metadata.entry_points = real_entry_points
        finally:
            sys.path.remove(tmp_dir)
            sys.modules.pop("_example_sitepack_digital_twin", None)

    print(
        f"discover() -> is_ok: {discover_result.is_ok},"
        f" loaded entry-points: {discover_result.value}"
    )
    print(f"registered after discovery: {sorted(code for code in REGISTRY)}")

    print()
    print("--- 3. The discovered twin type is a first-class, introspectable Twin ---")
    twin_cls = REGISTRY.get("VENTILATION.SitePackCircuit")
    metadata = REGISTRY.metadata_for("VENTILATION.SitePackCircuit").unwrap()
    assert isinstance(metadata, TwinMetadata)
    print(f"class={twin_cls.__name__} category={metadata.category}")

    print()
    print("--- 4. ...and provisions/behaves like any built-in would ---")
    twin = twin_cls(
        id="VENT-NORTH-1",
        scope={"circuit_id": "VENT-NORTH-1", "mine": "bingham-west"},
        state=TwinState(attributes={"airflow_m3s": 210.0, "ch4_pct": 0.15}, captured_at=MOMENT),
    )
    print(f"id={twin.id!r} status={twin.status.value!r}")
    print(f"attributes={dict(twin.state.attributes)}")
    assert twin.status is TwinStatus.PROVISIONED


if __name__ == "__main__":
    main()
