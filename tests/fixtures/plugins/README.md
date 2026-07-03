# Registry/Plugin Test Fixtures

## Purpose

Two small, real, independently-buildable Python packages used to prove the Registry Framework's discovery and isolation guarantees end-to-end, against actual installed package metadata rather than mocks (design spec §29, §30 Category B; checklist "A real, independently-built fixture plugin package (installable via `pip install`) used for discovery/integration tests").

## Contents

- `registry_fixture_healthy/` — declares one entry-point in the `mineproductivity.tests.registry_fixture` group; importing its module never raises.
- `registry_fixture_broken/` — declares one entry-point in the same group; importing its module always raises `RuntimeError`, proving `EntryPointDiscovery.discover()` isolates one bad plugin's import failure from every other entry-point discovered in the same call.

Both are consumed by [`tests/integration/test_registry_plugin_discovery.py`](../../integration/test_registry_plugin_discovery.py).

## Installing the Fixtures

```bash
pip install --no-deps -e tests/fixtures/plugins/registry_fixture_healthy
pip install --no-deps -e tests/fixtures/plugins/registry_fixture_broken
```

`tests/integration/conftest.py` installs both automatically (session-scoped fixture) before the integration test that needs them runs, so this manual step is only needed for interactive exploration.

## References

- [`docs/architecture/03_Registry_Framework_Design_Specification.md`](../../../docs/architecture/03_Registry_Framework_Design_Specification.md) §11 (isolation rule), §29 (testing strategy), §30 (Category B — Integration).
