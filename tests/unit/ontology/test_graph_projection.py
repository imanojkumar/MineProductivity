"""Tests for mineproductivity.ontology.graph_projection."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from mineproductivity.ontology.graph_projection import (
    GraphEdge,
    GraphNode,
    KnowledgeGraphProjection,
)


class TestGraphNode:
    def test_construction(self) -> None:
        node = GraphNode(node_id="HT-214", node_kind="entity", entity_type_code="RIGID_HAUL_TRUCK")
        assert node.node_id == "HT-214"
        assert node.node_kind == "entity"
        assert node.entity_type_code == "RIGID_HAUL_TRUCK"

    def test_entity_type_code_defaults_to_none(self) -> None:
        node = GraphNode(node_id="kpi-1", node_kind="kpi")
        assert node.entity_type_code is None

    def test_structural_equality(self) -> None:
        a = GraphNode(node_id="X", node_kind="entity", entity_type_code="Y")
        b = GraphNode(node_id="X", node_kind="entity", entity_type_code="Y")
        c = GraphNode(node_id="X", node_kind="entity", entity_type_code="Z")
        assert a == b
        assert a != c


class TestGraphEdge:
    def test_construction(self) -> None:
        edge = GraphEdge(source_id="HT-214", target_id="FL-NORTH", edge_kind="relationship")
        assert edge.source_id == "HT-214"
        assert edge.target_id == "FL-NORTH"
        assert edge.edge_kind == "relationship"

    def test_kpi_dependency_edge_kind(self) -> None:
        edge = GraphEdge(source_id="KPI.A", target_id="KPI.B", edge_kind="kpi_dependency")
        assert edge.edge_kind == "kpi_dependency"


class TestKnowledgeGraphProjectionContract:
    def test_cannot_instantiate_abstract_base(self) -> None:
        with pytest.raises(TypeError):
            KnowledgeGraphProjection()  # type: ignore[abstract]

    def test_concrete_subclass_yields_nodes_and_edges(self) -> None:
        node = GraphNode(node_id="X", node_kind="entity", entity_type_code="Y")
        edge = GraphEdge(source_id="X", target_id="Z", edge_kind="relationship")

        class _Projection(KnowledgeGraphProjection):
            def nodes(self) -> Iterator[GraphNode]:
                yield node

            def edges(self) -> Iterator[GraphEdge]:
                yield edge

        projection = _Projection()
        assert list(projection.nodes()) == [node]
        assert list(projection.edges()) == [edge]
