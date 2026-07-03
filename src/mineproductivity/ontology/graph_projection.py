"""``KnowledgeGraphProjection``: the contract a future Knowledge Graph builder consumes."""

from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Literal

from mineproductivity.core import BaseValueObject

__all__ = ["GraphEdge", "GraphNode", "KnowledgeGraphProjection"]


@dataclasses.dataclass(frozen=True, slots=True)
class GraphNode(BaseValueObject):
    """One node in a Knowledge Graph projection -- either an ontology
    entity or a KPI."""

    node_id: str
    node_kind: Literal["entity", "kpi"]
    entity_type_code: str | None = dataclasses.field(default=None, kw_only=True)


@dataclasses.dataclass(frozen=True, slots=True)
class GraphEdge(BaseValueObject):
    """One edge in a Knowledge Graph projection -- either an ontology
    relationship or a KPI dependency."""

    source_id: str
    target_id: str
    edge_kind: Literal["relationship", "kpi_dependency"]


class KnowledgeGraphProjection(ABC):
    """The contract a future Knowledge Graph builder consumes to project
    this package's declared entities and relationships into nodes and
    edges, so "the graph can never drift from the ontology" (Cookbook
    Part I, Ch. 8, Architecture Insight).

    Traversal (``neighbors``/``path``/``search``) is explicitly NOT part
    of this contract (design spec §4) -- it belongs to a future
    ``graph``-adjacent capability that *consumes* this projection, not to
    ``ontology`` itself.
    """

    @abstractmethod
    def nodes(self) -> Iterator[GraphNode]:
        """Yield every node this projection contributes to the graph."""

    @abstractmethod
    def edges(self) -> Iterator[GraphEdge]:
        """Yield every edge this projection contributes to the graph."""
