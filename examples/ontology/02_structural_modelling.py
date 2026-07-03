"""Model the structural (location + production time) hierarchy and
traverse it with explicit `Relationship` edges.

`Pit`/`Bench` and `Shift` are independent, independently serializable
entities -- `Relationship` is the explicit edge connecting them,
deliberately not an object-graph pointer (design spec AD-ON-02). This
example builds a small pit -> bench structure, a shift, and shows how a
`KnowledgeGraphProjection` traverses the declared edges without ever
holding a direct reference between the entities themselves.

Run: python examples/ontology/02_structural_modelling.py
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timezone

from mineproductivity.ontology import (
    Bench,
    GraphEdge,
    GraphNode,
    KnowledgeGraphProjection,
    Mine,
    Pit,
    Relationship,
    RelationshipKind,
    Shift,
)
from mineproductivity.ontology.entity_type import BaseEntityType


def main() -> None:
    print("--- Build the structural hierarchy: Mine -> Pit -> Bench ---")
    mine = Mine(id="bingham-west", commodity_codes=("copper",), method="open_pit")
    pit = Pit(id="pit-west", mine_id=mine.id, commodity="copper")
    bench = Bench(id="bench-7", pit_id=pit.id, elevation_m=1820.0)
    print(f"{mine.id} -> {pit.id} -> {bench.id} (elevation {bench.elevation_m}m)")

    print()
    print("--- Declare the edges explicitly, rather than nesting objects ---")
    relationships = [
        Relationship(source_id=pit.id, kind=RelationshipKind.BELONGS_TO, target_id=mine.id),
        Relationship(source_id=bench.id, kind=RelationshipKind.BELONGS_TO, target_id=pit.id),
    ]
    for rel in relationships:
        print(f"{rel.source_id} --{rel.kind.value}--> {rel.target_id}")

    print()
    print("--- Production time: a Shift is a UTC half-open interval ---")
    shift = Shift(
        id="A-2026-06-25",
        mine_id=mine.id,
        pattern="2x12",
        start_utc=datetime(2026, 6, 25, 6, tzinfo=timezone.utc),
        end_utc=datetime(2026, 6, 25, 18, tzinfo=timezone.utc),
        scheduled_h=12.0,
    )
    probe = datetime(2026, 6, 25, 14, 30, tzinfo=timezone.utc)
    print(f"shift {shift.id} contains {probe.isoformat()}: {shift.contains(probe)}")

    print()
    print("--- Project the structural graph, computed from the live entities ---")
    entities: list[BaseEntityType] = [mine, pit, bench]

    class StructuralProjection(KnowledgeGraphProjection):
        def nodes(self) -> Iterator[GraphNode]:
            for entity in entities:
                yield GraphNode(
                    node_id=entity.id, node_kind="entity", entity_type_code=type(entity).code
                )

        def edges(self) -> Iterator[GraphEdge]:
            for rel in relationships:
                yield GraphEdge(
                    source_id=rel.source_id, target_id=rel.target_id, edge_kind="relationship"
                )

    projection = StructuralProjection()
    for node in projection.nodes():
        print(f"node: {node.node_id} ({node.entity_type_code})")
    for edge in projection.edges():
        print(f"edge: {edge.source_id} -> {edge.target_id}")


if __name__ == "__main__":
    main()
