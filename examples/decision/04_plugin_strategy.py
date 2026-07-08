"""A third-party-style ``DecisionStrategy`` registered via entry points,
mirroring ``examples/registry/01_register_and_discover.py``'s pattern --
the exact wiring design spec 07 sec. 32 prescribes:

    [project.entry-points."mineproductivity.decision"]
    sitepack = "mineproductivity_sitepack.decision"

The "discover" step needs a real, importable module whose top-level code
runs ``decision.register`` as a side effect of import -- exactly what
happens when a real site-pack package is installed and its entry-point
is scanned. This example writes a small, real ``.py`` file to a temp
directory and discovers it through the exact same
``registry.EntryPointDiscovery`` code path a pip-installed plugin would
go through -- no shortcuts, no faked registration.

Run: python examples/decision/04_plugin_strategy.py
"""

from __future__ import annotations

import importlib.metadata
import sys
import tempfile
from pathlib import Path

from mineproductivity.kpis import KPIResult
from mineproductivity.registry import EntryPointDiscovery, EntryPointSpec

from mineproductivity.decision import REGISTRY, DecisionContext, DecisionMetadata

_PLUGIN_SOURCE = '''\
"""A site pack's own decision strategy -- importing this module
registers it, exactly as a pip-installed plugin's entry-point scan
would."""

from typing import ClassVar

from mineproductivity.decision import (
    DecisionCategory,
    DecisionContext,
    DecisionMetadata,
    DecisionResult,
    DecisionStrategy,
    register,
)


@register
class SitePackEscalationStrategy(DecisionStrategy):
    """Escalate to the site supervisor whenever any KPI evidence is
    present -- a deliberately tiny site-specific rule of thumb."""

    meta: ClassVar[DecisionMetadata] = DecisionMetadata(
        code="STRATEGY.SitePackEscalation",
        category=DecisionCategory.STRATEGY,
        description="Escalate to the site supervisor whenever any KPI evidence is present.",
    )

    def _decide(self, context: DecisionContext) -> DecisionResult:
        return DecisionResult(
            model_code=self.meta.code,
            warnings=("site-pack demo strategy: escalate to supervisor",),
        )
'''


def main() -> None:
    print("--- 1. The built-in strategies are already registered ---")
    print(f"before discovery: {sorted(REGISTRY)}")

    print()
    print("--- 2. A site pack declares its strategy via a pyproject.toml entry-point ---")
    print("(a real, on-disk module -- the same EntryPointDiscovery code path")
    print(" a pip-installed plugin uses)")

    with tempfile.TemporaryDirectory() as tmp_dir:
        plugin_path = Path(tmp_dir) / "_example_sitepack_decision.py"
        plugin_path.write_text(_PLUGIN_SOURCE, encoding="utf-8")
        sys.path.insert(0, tmp_dir)
        try:
            real_entry_points = importlib.metadata.entry_points

            def _fake_entry_points(*, group: str):  # type: ignore[no-untyped-def]
                if group == "mineproductivity.decision":
                    return (
                        importlib.metadata.EntryPoint(
                            name="sitepack", value="_example_sitepack_decision", group=group
                        ),
                    )
                return real_entry_points(group=group)

            importlib.metadata.entry_points = _fake_entry_points  # type: ignore[assignment]
            try:
                discovery = EntryPointDiscovery()
                spec = EntryPointSpec(group="mineproductivity.decision", target_registry="decision")
                discover_result = discovery.discover(spec)
            finally:
                importlib.metadata.entry_points = real_entry_points
        finally:
            sys.path.remove(tmp_dir)
            sys.modules.pop("_example_sitepack_decision", None)

    print(
        f"discover() -> is_ok: {discover_result.is_ok},"
        f" loaded entry-points: {discover_result.value}"
    )
    print(f"registered after discovery: {sorted(REGISTRY)}")

    print()
    print("--- 3. The discovered strategy is a first-class DecisionModel ---")
    strategy_cls = REGISTRY.get("STRATEGY.SitePackEscalation")
    metadata = REGISTRY.metadata_for("STRATEGY.SitePackEscalation").unwrap()
    assert isinstance(metadata, DecisionMetadata)
    print(f"class={strategy_cls.__name__} category={metadata.category}")

    print()
    print("--- 4. ...and runs through the same decide() orchestration as any built-in ---")
    context = DecisionContext(
        kpi_results=(KPIResult(code="UTIL.OEE", value=0.83, unit=""),),
        analytics_results=(),
        scope={"pit": "north"},
    )
    result = strategy_cls().decide(context)
    print(f"model_code={result.model_code!r} warnings={result.warnings}")


if __name__ == "__main__":
    main()
