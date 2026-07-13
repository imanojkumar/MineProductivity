# Quick Start

The fastest way to see the whole platform work: one truck, one shift, one KPI.

!!! tip "Run it yourself"
    The complete script lives at [`examples/quickstart/01_five_minute_tour.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/quickstart/01_five_minute_tour.py). Install with the analytics extra and run it:

    ```bash
    pip install "mineproductivity[analytics] @ git+https://github.com/imanojkumar/MineProductivity.git"
    python examples/quickstart/01_five_minute_tour.py
    ```

## Compute your first KPI

Every KPI in MineProductivity is a discoverable, versioned, self-describing object — never a formula buried in a script:

```python
from mineproductivity.kpis import REGISTRY

# Look a KPI up by its governed identifier, then compute it.
tph = REGISTRY.get("PROD.TPH")().compute([{"payload_t": 220.0, "operating_h": 12.0}])
print(tph.value, tph.unit)   # 18.33... t/h
```

## Discover what's available

```python
from mineproductivity.kpis import REGISTRY

print(len(REGISTRY), "KPIs in the Standard Library")
for code in sorted(REGISTRY):
    print(code)
```

## Where to go next

<div class="grid cards" markdown>

-   :material-school: __[Tutorials](../tutorials/index.md)__

    Package-by-package, runnable walkthroughs — KPIs, events, ontology, connectors, and the full Intelligence tier.

-   :material-book-open-variant: __[Packages](../packages/index.md)__

    Read the full public API and extension guide for any package.

-   :material-map: __[Next Steps](next-steps.md)__

    A curated route through the platform for first-time users.

</div>
