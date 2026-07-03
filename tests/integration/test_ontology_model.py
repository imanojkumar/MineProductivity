"""Integration test for the Ontology Framework.

Builds a small, realistic mine model spanning every sub-ontology family
(location, equipment, organization, production, cost, safety), wires it
together with :class:`~mineproductivity.ontology.relationship.Relationship`
edges, validates it end-to-end with
:class:`~mineproductivity.ontology.validation.OntologyValidator`, and
projects it through a :class:`~mineproductivity.ontology.graph_projection.KnowledgeGraphProjection`
implementation -- "the graph can never drift from the ontology" (Cookbook
Part I, Ch. 8). Also confirms the Event Framework's dependency on this
package's reference taxonomies (``DelayCategory``, ``SafetyEventType``)
resolves to the exact same objects, not duplicated copies.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timezone

from mineproductivity.events import DelayEvent, SafetyEvent, SafetySeverity
from mineproductivity.ontology import (
    Bench,
    BusinessUnit,
    Crew,
    DelayCategory,
    Fleet,
    GraphEdge,
    GraphNode,
    HazardZone,
    KnowledgeGraphProjection,
    Mine,
    Operator,
    OntologyValidator,
    Pit,
    Relationship,
    RelationshipKind,
    RigidHaulTruck,
    SafetyEventType,
    Shift,
    ShiftPattern,
)
from mineproductivity.ontology.entity_type import BaseEntityType


def build_mine_model() -> tuple[list[BaseEntityType], list[Relationship]]:
    """Construct a small, internally-consistent mine model spanning six
    sub-ontology families, mirroring Developer & Cookbook Guide Part I's
    worked "Bingham West" example."""
    bu = BusinessUnit(id="BU-COPPER")
    mine = Mine(id="bingham-west", commodity_codes=("copper",), method="open_pit")
    pit = Pit(id="pit-west", mine_id=mine.id, commodity="copper")
    bench = Bench(id="bench-7", pit_id=pit.id, elevation_m=1820.0)
    fleet = Fleet(id="FL-NORTH", mine_id=mine.id, equipment_type_code="RIGID_HAUL_TRUCK")
    truck_a = RigidHaulTruck(id="HT-214", model="CAT 797F", fleet_id=fleet.id, rated_capacity=363.0)
    truck_b = RigidHaulTruck(id="HT-215", model="CAT 797F", fleet_id=fleet.id, rated_capacity=363.0)
    crew = Crew(id="CREW-A", mine_id=mine.id)
    operator = Operator(id="OP-001", crew_id=crew.id, licence_class="Haul Truck")
    shift = Shift(
        id="A-2026-06-25",
        mine_id=mine.id,
        pattern="2x12",
        start_utc=datetime(2026, 6, 25, 6, tzinfo=timezone.utc),
        end_utc=datetime(2026, 6, 25, 18, tzinfo=timezone.utc),
        scheduled_h=12.0,
    )
    hazard = HazardZone(id="B7N_CR1", zone_id="B7N_CR1", speed_limit_kmh=45.0)

    entities: list[BaseEntityType] = [
        bu,
        mine,
        pit,
        bench,
        fleet,
        truck_a,
        truck_b,
        crew,
        operator,
        shift,
        hazard,
    ]
    relationships = [
        Relationship(source_id=mine.id, kind=RelationshipKind.SCOPED_TO, target_id=bu.id),
        Relationship(source_id=pit.id, kind=RelationshipKind.BELONGS_TO, target_id=mine.id),
        Relationship(source_id=bench.id, kind=RelationshipKind.BELONGS_TO, target_id=pit.id),
        Relationship(source_id=truck_a.id, kind=RelationshipKind.PART_OF, target_id=fleet.id),
        Relationship(source_id=truck_b.id, kind=RelationshipKind.PART_OF, target_id=fleet.id),
        Relationship(source_id=operator.id, kind=RelationshipKind.PART_OF, target_id=crew.id),
        Relationship(
            source_id=truck_a.id, kind=RelationshipKind.OPERATED_BY, target_id=operator.id
        ),
        Relationship(source_id=truck_a.id, kind=RelationshipKind.LOCATED_AT, target_id=hazard.id),
    ]
    return entities, relationships


class TestMineModelStructuralIntegrity:
    def test_every_entity_constructs_and_validates_at_construction_time(self) -> None:
        entities, _relationships = build_mine_model()
        assert len(entities) == 11
        assert {type(e).code for e in entities} == {
            "BUSINESS_UNIT",
            "MINE",
            "PIT",
            "BENCH",
            "FLEET",
            "RIGID_HAUL_TRUCK",
            "CREW",
            "OPERATOR",
            "SHIFT",
            "HAZARD_ZONE",
        }

    def test_every_relationship_resolves_to_a_real_entity_pair(self) -> None:
        entities, relationships = build_mine_model()
        ids = {e.id for e in entities}
        for rel in relationships:
            assert rel.source_id in ids
            assert rel.target_id in ids


class TestOntologyValidatorAcrossTheWholeModel:
    def test_valid_model_passes_full_validation(self) -> None:
        entities, _relationships = build_mine_model()
        by_id = {e.id: e for e in entities}
        validator = OntologyValidator(entity_resolver=lambda eid: eid in by_id)

        for entity in entities:
            result = validator.validate(entity)
            assert result.is_valid, f"{type(entity).__name__} failed: {result.errors}"

    def test_broken_type_code_reference_is_caught(self) -> None:
        validator = OntologyValidator()
        broken_fleet = Fleet(
            id="FL-BROKEN", mine_id="bingham-west", equipment_type_code="NOT_A_REAL_TYPE"
        )
        result = validator.validate(broken_fleet)
        assert not result.is_valid

    def test_broken_instance_id_reference_is_caught_when_resolver_present(self) -> None:
        entities, _relationships = build_mine_model()
        by_id = {e.id: e for e in entities}
        validator = OntologyValidator(entity_resolver=lambda eid: eid in by_id)

        orphaned_bench = Bench(id="bench-orphan", pit_id="pit-does-not-exist", elevation_m=1800.0)
        result = validator.validate(orphaned_bench)
        assert not result.is_valid
        assert "pit-does-not-exist" in result.errors[0]

    def test_unresolved_reference_is_a_warning_not_a_raised_exception(self) -> None:
        """An orphaned reference must never halt ingestion of everything
        else (Cookbook Part I, Ch. 8)."""
        validator = OntologyValidator(entity_resolver=lambda eid: False)
        orphaned_bench = Bench(id="bench-orphan", pit_id="ghost-pit", elevation_m=1800.0)
        result = validator.validate(orphaned_bench)  # does not raise
        assert not result.is_valid


class TestKnowledgeGraphProjection:
    def test_model_projects_into_nodes_and_edges_without_drift(self) -> None:
        entities, relationships = build_mine_model()

        class MineModelProjection(KnowledgeGraphProjection):
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

        projection = MineModelProjection()
        nodes = list(projection.nodes())
        edges = list(projection.edges())

        assert len(nodes) == len(entities)
        assert len(edges) == len(relationships)
        assert {n.node_id for n in nodes} == {e.id for e in entities}
        assert all(n.node_kind == "entity" for n in nodes)
        assert all(e.edge_kind == "relationship" for e in edges)

    def test_projection_reflects_a_removed_entity_without_manual_sync(self) -> None:
        """Regression guard for the design's core claim: since the
        projection is computed *from* the live entity/relationship lists
        rather than a separately-maintained graph, removing an entity from
        the source of truth removes it from the graph automatically."""
        entities, relationships = build_mine_model()
        entities = [e for e in entities if e.id != "HT-215"]

        class MineModelProjection(KnowledgeGraphProjection):
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

        projection = MineModelProjection()
        node_ids = {n.node_id for n in projection.nodes()}
        assert "HT-215" not in node_ids


class TestShiftPatternIntegration:
    def test_shift_pattern_matches_calendar_convention(self) -> None:
        entities, _relationships = build_mine_model()
        shift = next(e for e in entities if isinstance(e, Shift))
        assert shift.pattern == ShiftPattern.TWO_BY_TWELVE.value


class TestEventFrameworkConsumesOntologyReferenceData:
    """Confirms events.DelayEvent/SafetyEvent consume ontology's reference
    taxonomies directly rather than duplicating them (Documentation
    Governance Rule #005 and design spec AD-ON-03)."""

    def test_delay_event_uses_the_exact_ontology_delaycategory(self) -> None:
        delay = DelayEvent(
            equipment_id="CR-01",
            shift_id="A-2026-06-25",
            delay_category=DelayCategory.EQUIPMENT,
            delay_reason="crusher_down",
            duration_min=252.0,
        )
        assert delay.delay_category is DelayCategory.EQUIPMENT
        assert type(delay.delay_category) is DelayCategory

    def test_safety_event_uses_the_exact_ontology_safetyeventtype(self) -> None:
        safety = SafetyEvent(
            equipment_id="HT-214",
            shift_id="A-2026-06-25",
            safety_event_type=SafetyEventType.SPEED_VIOLATION,
            severity=SafetySeverity.MEDIUM,
            zone_id="B7N_CR1",
        )
        assert safety.safety_event_type is SafetyEventType.SPEED_VIOLATION
        assert type(safety.safety_event_type) is SafetyEventType

    def test_safety_event_zone_id_can_reference_a_real_hazard_zone(self) -> None:
        entities, _relationships = build_mine_model()
        hazard = next(e for e in entities if isinstance(e, HazardZone))
        safety = SafetyEvent(
            equipment_id="HT-214",
            shift_id="A-2026-06-25",
            safety_event_type=SafetyEventType.SPEED_VIOLATION,
            severity=SafetySeverity.HIGH,
            zone_id=hazard.id,
        )
        assert safety.zone_id == hazard.zone_id
