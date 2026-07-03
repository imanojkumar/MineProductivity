"""``mineproductivity.connectors`` -- how MineProductivity meets the real
world.

Defines the single, small contract every data source -- a fleet-
management system, a CSV export, a REST API, a Kafka topic -- must
satisfy to feed the platform, and is the **only** place in the codebase
permitted to know that a specific vendor or file format exists (the
Cookbook's Vendor-Neutrality principle).

Implements ``docs/architecture/04_Connector_Framework_Design_Specification.md``
exactly. ``connectors`` depends on ``core``, ``ontology``, ``events``,
and ``registry`` -- see ``README.md`` for the full set of architectural
rules this package must satisfy.

Everything documented here is part of the public API and can be imported
directly from ``mineproductivity.connectors``, e.g.::

    from mineproductivity.connectors import get_connector, CONNECTORS
"""

from __future__ import annotations

from mineproductivity.connectors._registry import CONNECTORS, get_connector, register_connector
from mineproductivity.connectors.auth import AuthProvider, Credentials
from mineproductivity.connectors.base import FMSConnector, IngestionMode
from mineproductivity.connectors.exceptions import (
    AuthenticationError,
    ConnectorError,
    ContractViolationError,
    MappingError,
    SourceUnavailableError,
)
from mineproductivity.connectors.file import CSVConnector, ExcelConnector
from mineproductivity.connectors.health import ConnectorHealth, HealthStatus
from mineproductivity.connectors.network import GraphQLConnector, RestConnector
from mineproductivity.connectors.normalization import FieldMapper, Normalizer, ReasonCodeMap
from mineproductivity.connectors.retry import BackoffStrategy, RetryPolicy
from mineproductivity.connectors.streaming import KafkaConnector, MqttConnector

__all__ = [
    "AuthProvider",
    "AuthenticationError",
    "BackoffStrategy",
    "CONNECTORS",
    "CSVConnector",
    "ConnectorError",
    "ConnectorHealth",
    "ContractViolationError",
    "Credentials",
    "ExcelConnector",
    "FMSConnector",
    "FieldMapper",
    "GraphQLConnector",
    "HealthStatus",
    "IngestionMode",
    "KafkaConnector",
    "MappingError",
    "MqttConnector",
    "Normalizer",
    "ReasonCodeMap",
    "RestConnector",
    "RetryPolicy",
    "SourceUnavailableError",
    "get_connector",
    "register_connector",
]

for _connector_cls in (
    CSVConnector,
    ExcelConnector,
    RestConnector,
    GraphQLConnector,
    KafkaConnector,
    MqttConnector,
):
    register_connector(_connector_cls)
del _connector_cls
