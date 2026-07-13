"""Post-install smoke test: proves a `mineproductivity` install (wheel,
sdist, editable, or straight from GitHub) is actually usable, not just
importable.

Deliberately dependency-light: only the base install (no extras) is
required, matching the "pay only for what you use" packaging philosophy
documented in every package's own README. Run after any install method:

    python scripts/quality/smoke_test.py
"""

from __future__ import annotations

import sys


def main() -> int:
    import mineproductivity

    print(f"mineproductivity {mineproductivity.__version__}")

    import mineproductivity.agents
    import mineproductivity.analytics
    import mineproductivity.connectors
    import mineproductivity.core
    import mineproductivity.decision
    import mineproductivity.digital_twin
    import mineproductivity.events
    import mineproductivity.kpis
    import mineproductivity.ontology
    import mineproductivity.optimization
    import mineproductivity.plugins
    import mineproductivity.registry
    import mineproductivity.simulation
    import mineproductivity.visualization

    print(
        "all 14 implemented subpackages import cleanly on the base install "
        "(numpy/pandas/pyarrow/openpyxl are needed only to execute KPI backends, "
        "Arrow codecs, or the Excel connector -- never merely to import)"
    )

    from mineproductivity.kpis import REGISTRY

    tph_cls = REGISTRY.get("PROD.TPH")
    result = tph_cls().compute([{"payload_t": 220.0, "operating_h": 12.0}])
    assert result.value is not None
    print(f"PROD.TPH smoke computation: {result.value:.4f} {result.unit}")

    print(f"{len(REGISTRY)} KPIs registered in the Standard Library")
    assert len(REGISTRY) == 12, f"expected the 12-KPI Standard Library, found {len(REGISTRY)}"

    print("SMOKE TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
