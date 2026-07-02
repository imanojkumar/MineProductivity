# Ontology Framework — Implementation Checklist

**Package:** `mineproductivity.ontology`
**Governing specification:** [`docs/architecture/02_Ontology_Framework_Design_Specification.md`](../architecture/02_Ontology_Framework_Design_Specification.md)
**Status:** Not started

Binding implementation contract for `ontology`. Complete in order; every box must be checked or explicitly deferred with a linked issue and Chief Software Architect sign-off before merge.

## Pre-Implementation Gate

- [ ] Design specification read in full by the implementer.
- [ ] `core` (v0.2.0) available and importable. `ontology` has no other package dependency (design spec §7) — confirm no accidental `events`/`kpis`/`connectors` import creeps in.
- [ ] This checklist reviewed against the design spec's §36/§37 — no drift.

## Package Structure

- [ ] `src/mineproductivity/ontology/` created matching design spec §6 exactly, including all ten sub-ontology subpackages (`equipment/`, `material/`, `location/`, `organization/`, `production/`, `maintenance/`, `cost/`, `quality/`, `safety/`, `environmental/`) plus `reference/` and `graph_projection.py`.
- [ ] `ontology/README.md` written following the `core/README.md` template.
- [ ] No sub-ontology module imports another sub-ontology's concrete leaf types directly (relate via `Relationship`/id-string only — cross-check design spec §15).

## Public API

- [ ] `ontology/__init__.py` exports exactly the symbol list in design spec §8, alphabetized `__all__`.
- [ ] `test_public_api.py` mirrors `tests/unit/core/test_public_api.py`'s completeness/sortedness/no-duplicates checks.

## Interfaces / Object Model

- [ ] `BaseEntityType` (§10.1) + `EntityTypeMetadata` — `to_schema()` implemented and cached.
- [ ] `Relationship` + `RelationshipKind` (§10.2) — all five kinds (`BELONGS_TO`, `PART_OF`, `OPERATED_BY`, `LOCATED_AT`, `SCOPED_TO`).
- [ ] Equipment ontology (§10.3): `EquipmentType` abstract root + `RigidHaulTruck`, `ArticulatedHaulTruck`, `HydraulicShovel`, `WheelLoader`, `LHD`, `BlastholeDrill`, `Dozer`, `Grader`, `WaterTruck`, `Crusher`, `Conveyor`, `Mill`.
- [ ] Material ontology (§10.4): `MaterialType` enum, `Commodity`.
- [ ] Location ontology (§10.5): `Mine`, `Pit`, `Bench`, `Route`, `Zone`, `Level`, `Stope`, `Drive`.
- [ ] Organization ontology (§10.6): `Fleet`, `Operator`, `Crew`, `BusinessUnit`, `Contractor`.
- [ ] Production ontology (§10.7): `Shift` (with `contains()` half-open-interval method), `ShiftPattern`, `ShiftCalendar`.
- [ ] Maintenance ontology (§10.8): `FailureMode`, `MaintenanceWorkOrder` (shape only).
- [ ] Cost ontology (§10.8): `CostCenter`, `CostCategory`.
- [ ] Quality ontology (§10.8): `GradeAttribute`, `QualitySpecification`.
- [ ] Safety ontology (§10.8): `HazardZone`, `SpeedLimitMap`, `SafetyEventType`.
- [ ] Environmental ontology (§10.8): `EmissionFactor`, `MonitoringPoint`.
- [ ] Reference data (§10.9): `DelayCategory` enum with `precedence` property — the six canonical MECE values, exact precedence order.
- [ ] `KnowledgeGraphProjection` ABC + `GraphNode`/`GraphEdge` (§10.10) — interface only, no traversal engine.
- [ ] Every leaf type declares a globally-unique `code` (test: no two leaf types share a `code`, across all ten sub-ontologies).

## Lifecycle & State Machine

- [ ] Entity instance lifecycle (§11): Declared → Validated → (Active | Rejected) → Retired, with the rule that retiring an instance never invalidates historical references.
- [ ] Equipment operational state machine (§12) documented as metadata (`operational_states`), NOT implemented as mutable instance state.

## Validation

- [ ] Structural validation on every leaf type (field invariants, e.g. `Shift.start_utc < Shift.end_utc`).
- [ ] `OntologyValidator` (§19) — contextual/referential checks (`Bench.pit_id` resolves, `Fleet.equipment_type_code` resolves).
- [ ] Orphaned-reference behavior confirmed as a warning, never a crash, never a silent drop.

## Versioning

- [ ] Entity type SemVer discipline documented in `README.md` (MAJOR/MINOR/PATCH per §20).
- [ ] `ontology_version` traceability field wired for Learning & Benchmark Suite Documentation Governance Rule #006 compliance (recorded wherever ontology-derived artifacts are produced).

## Serialization

- [ ] `to_schema()` JSON Schema export implemented for every leaf type.
- [ ] `core.BaseSerializer[BaseEntityType]`/`DataclassSerializer` round-trip verified for a representative type from each of the ten sub-ontologies.

## Performance & Memory

- [ ] Entity type lookup confirmed O(1) via `EntityTypeRegistry`.
- [ ] `to_schema()` caching confirmed (repeated calls do not recompute).

## Thread Safety & Concurrency

- [ ] Registry population confirmed single-threaded/startup-only; no dynamic runtime registration path exists outside plugin discovery.
- [ ] Concurrent read access to entity instances/types confirmed safe (inherited from immutability — smoke test sufficient, not a stress test).

## Error Handling

- [ ] Full exception hierarchy (§26): `OntologyValidationError`, `UnknownEntityTypeError`, `RelationshipError`.

## Logging

- [ ] Orphaned-reference warnings logged at `WARNING` with referencing/target ids.
- [ ] Registry population summary logged at `INFO` once per process start.

## Configuration

- [ ] Confirmed `ontology` performs no environment/file configuration reading itself (site-specific instantiation is a future `config`-package concern).

## Tests

- [ ] `tests/unit/ontology/` mirrors `src/mineproductivity/ontology/` 1:1.
- [ ] Coverage ≥95%.
- [ ] Relationship resolution tests for all five `RelationshipKind`s.
- [ ] Registry duplicate-code rejection test.
- [ ] `KnowledgeGraphProjection` contract test against a small fixed ontology fixture.

## Documentation

- [ ] `ontology/README.md` complete.
- [ ] Every public class has a docstring; equipment leaf types document their `supported_kpis` rationale.

## Examples

- [ ] `examples/ontology/01_equipment_modelling.py` — `RigidHaulTruck`/`HydraulicShovel`, mirrors Cookbook Part I Ch. 8.
- [ ] `examples/ontology/02_structural_modelling.py` — `Pit`/`Bench`/`Shift` + relationship traversal.
- [ ] `examples/ontology/03_validation.py` — orphaned-reference warning demonstration.
- [ ] All examples pass `mypy --strict` + `ruff`.

## Benchmarks

- [ ] Registry lookup and `to_schema()` cache-hit latency recorded in `benchmark/reports/ontology/` (expected: negligible, but recorded as a baseline).

## Certification

- [ ] Categories A, B, C, D, G from design spec §30 pass, using the Learning & Benchmark Suite's five reference mines' master data (`equipment.csv`, `operators.csv`, `shift_calendar.csv`).

## Type Hints, Mypy, Ruff, Coverage

- [ ] 100% type-hinted; `mypy --strict` clean.
- [ ] `ruff check` and `ruff format --check` clean.
- [ ] Coverage report attached; ≥95%.

## Release

- [ ] `CHANGELOG.md` updated.
- [ ] Root README dependency diagram cross-checked.
- [ ] Version bump proposed and reviewed.
- [ ] Design spec §37 re-verified as final merge gate.

---

*Derived from [`02_Ontology_Framework_Design_Specification.md`](../architecture/02_Ontology_Framework_Design_Specification.md). Keep in sync with the governing specification.*
