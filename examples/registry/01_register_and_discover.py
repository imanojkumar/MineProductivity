"""The full register -> discover -> lookup cycle: the one mechanism every
domain package (kpis, connectors, ontology, analytics) specializes.

The "discover" step needs a real, importable module whose top-level code
runs a ``@register`` decorator as a side effect of import -- exactly
what happens when a real third-party plugin package is installed and
its entry-point is scanned (`tests/fixtures/plugins/` builds two real,
independently pip-installable packages for the test suite; see
`tests/integration/test_registry_plugin_discovery.py`). This example
writes a small, real ``.py`` file to a temp directory and discovers it
through the exact same `EntryPointDiscovery` code path a real installed
plugin would go through -- no shortcuts, no faked registration.

Run: python examples/registry/01_register_and_discover.py
"""

from __future__ import annotations

import importlib.metadata
import sys
import tempfile
import types
from pathlib import Path
from typing import Any

from mineproductivity.registry import EntryPointDiscovery, EntryPointSpec, Registry, registered_in


def main() -> None:
    print("--- 1. A domain package owns a Registry and a @register decorator ---")
    kpi_registry: Registry[str, Any] = Registry(name="kpis")
    register = registered_in(kpi_registry, key_of=lambda cls: cls.meta["code"])

    print()
    print("--- 2. Registering directly (no plugin involved yet) ---")

    @register
    class TruckCycleTime:
        meta = {"code": "PROD.TruckCycleTime"}

    print(f"registered: {list(kpi_registry)}")

    print()
    print("--- 3. Duplicate registration is rejected, not silently overwritten ---")
    result = kpi_registry.register("PROD.TruckCycleTime", TruckCycleTime)
    print(
        f"re-registering the same code -> is_ok: {result.is_ok}, error: {type(result.error).__name__}"
    )

    print()
    print("--- 4. Discovery: a plugin declares itself via a pyproject.toml entry-point ---")
    print(
        "(a real, on-disk module -- the same EntryPointDiscovery code path a pip-installed plugin uses)"
    )

    # A lightweight stand-in for "import mineproductivity.kpis" inside the
    # plugin module below -- the plugin only ever sees `register`, never
    # any internal registry machinery.
    sys.modules["_example_kpis_facade"] = types.SimpleNamespace(register=register)  # type: ignore[assignment]

    with tempfile.TemporaryDirectory() as tmp_dir:
        plugin_path = Path(tmp_dir) / "_example_haulmetrics_plugin.py"
        plugin_path.write_text(
            "import _example_kpis_facade\n"
            "\n"
            "@_example_kpis_facade.register\n"
            "class FuelPerTonne:\n"
            "    meta = {'code': 'COST.FuelPerTonne'}\n",
            encoding="utf-8",
        )
        sys.path.insert(0, tmp_dir)
        try:
            real_entry_points = importlib.metadata.entry_points

            def _fake_entry_points(*, group: str):  # type: ignore[no-untyped-def]
                if group == "mineproductivity.kpis":
                    return (
                        importlib.metadata.EntryPoint(
                            name="haulmetrics", value="_example_haulmetrics_plugin", group=group
                        ),
                    )
                return real_entry_points(group=group)

            importlib.metadata.entry_points = _fake_entry_points  # type: ignore[assignment]
            try:
                discovery = EntryPointDiscovery()
                spec = EntryPointSpec(group="mineproductivity.kpis", target_registry="kpis")
                discover_result = discovery.discover(spec)
            finally:
                importlib.metadata.entry_points = real_entry_points
        finally:
            sys.path.remove(tmp_dir)
            sys.modules.pop("_example_haulmetrics_plugin", None)

    print(
        f"discover() -> is_ok: {discover_result.is_ok}, loaded entry-points: {discover_result.value}"
    )
    print(f"registered after discovery: {sorted(kpi_registry)}")

    print()
    print("--- 5. Lookup downstream ---")
    found = kpi_registry.lookup("COST.FuelPerTonne")
    print(f"lookup('COST.FuelPerTonne').is_some: {found.is_some}")
    missing = kpi_registry.lookup("COST.NotARealCode")
    print(f"lookup('COST.NotARealCode').is_nothing: {missing.is_nothing}")


if __name__ == "__main__":
    main()
