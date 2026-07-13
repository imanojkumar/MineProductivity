# API Reference

Symbol-level API reference for every package, generated directly from the packages' own docstrings by [mkdocstrings](https://mkdocstrings.github.io/). Private members (leading underscore) are hidden.

This complements the [Packages](../packages/index.md) section: *Packages* gives the narrative overview, dependency rules, and extension guide; *API Reference* gives the exhaustive, always-current symbol list with signatures and docstrings.

## Foundation

- [core](core.md) · [ontology](ontology.md) · [events](events.md) · [registry](registry.md) · [plugins](plugins.md) · [connectors](connectors.md) · [kpis](kpis.md)

## Intelligence

- [analytics](analytics.md) · [decision](decision.md) · [digital_twin](digital_twin.md) · [simulation](simulation.md) · [optimization](optimization.md) · [agents](agents.md) · [visualization](visualization.md)

!!! note "Public API stability"
    As of `v2.0.0` these public APIs are **stable by contract** — they will not change incompatibly without a further MAJOR version bump. Each package's `__all__` is the authoritative public surface and is verified by its `test_public_api.py`.
