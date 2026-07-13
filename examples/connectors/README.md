# Examples - mineproductivity.connectors

## Purpose

Runnable, minimal, self-contained scripts demonstrating the Connector Framework: end-to-end CSV ingestion into the Event Framework, and a REST connector's auth-refresh and retry/backoff behavior against a real local HTTP server.

## Scope

Example scripts and their direct output. No test assertions live here (see `tests/unit/connectors/` and `tests/integration/test_connector_pipeline.py` for that); each script is meant to be read and run by a human evaluating the package.

## Responsibilities

- Show idiomatic usage of the Connector Framework's public API.
- Serve as executable documentation that stays correct because it is actually run.

## Contents

- `01_csv_ingestion.py` - look up `CSVConnector` via `get_connector("csv")`, pull cycle and delay events from the golden fixtures in `tests/fixtures/connectors/`, validate, envelope, append to an `EventStore`, and query back.
- `02_rest_with_retry.py` - `RestConnector` against a real, local `http.server.HTTPServer`: a stale token forces exactly one `AuthProvider.refresh()`, and a transient `503` forces a `RetryPolicy`-governed retry, both before any event is yielded.

## Dependencies

Only `mineproductivity` itself (editable-installed from this repository). No third-party packages, no network access, no pre-existing server -- `02_rest_with_retry.py` starts and tears down its own local HTTP server.

## Running the Examples

```bash
pip install -e .
python examples/connectors/01_csv_ingestion.py
python examples/connectors/02_rest_with_retry.py
```

Each script exits `0` and prints its own output; there is nothing to configure.

## Future Work

Add an OEM-shape walkthrough once a real third-party OEM plugin package exists to demonstrate the `oem/` mapping contract against something more concrete than a `NotImplementedError`.

## References

- Reference Implementation Blueprint v1.0
- [`docs/architecture/04_Connector_Framework_Design_Specification.md`](../../docs/architecture/04_Connector_Framework_Design_Specification.md) §31
- [`src/mineproductivity/connectors/README.md`](../../src/mineproductivity/connectors/README.md)
