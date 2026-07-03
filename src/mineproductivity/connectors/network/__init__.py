"""Network-based reference connectors: :class:`RestConnector`, :class:`GraphQLConnector`."""

from __future__ import annotations

from mineproductivity.connectors.network.graphql_connector import GraphQLConnector
from mineproductivity.connectors.network.rest_connector import RestConnector

__all__ = ["GraphQLConnector", "RestConnector"]
