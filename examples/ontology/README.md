# Examples — mineproductivity.ontology

## Purpose

Runnable, minimal, self-contained scripts demonstrating the Ontology Framework: modelling equipment leaf types, building a structural (location + shift) hierarchy with explicit relationship edges, and validating cross-entity references.

## Scope

Example scripts and their direct output. No test assertions live here (see `tests/unit/ontology/` and `tests/integration/test_ontology_model.py` for that); each script is meant to be read and run by a human evaluating the package.

## Responsibilities

- Show idiomatic usage of the Ontology Framework's public API.
- Serve as executable documentation that stays correct because it is actually run.

## Contents

- `01_equipment_modelling.py` — construct `RigidHaulTruck`/`HydraulicShovel`, inspect the shared `OperationalState` machine and declared `supported_kpis`, export a leaf type's shape as JSON Schema.
- `02_structural_modelling.py` — build a `Mine` → `Pit` → `Bench` structure and a `Shift`, connect entities with explicit `Relationship` edges, and project the model through a `KnowledgeGraphProjection`.
- `03_validation.py` — demonstrate `OntologyValidator`'s two reference-checking modes (`*_type_code` against the internal registry, `*_id` against an injected resolver) and its central rule: an unresolved reference is a warning, never a raised exception.

## Dependencies

Only `mineproductivity` itself (editable-installed from this repository). No third-party packages.

## Running the Examples

```bash
pip install -e .
python examples/ontology/01_equipment_modelling.py
python examples/ontology/02_structural_modelling.py
python examples/ontology/03_validation.py
```

Each script exits `0` and prints its own output; there is nothing to configure.

## Future Work

Add an example demonstrating a full multi-family mine model (equipment + organization + cost + safety together) once the Registry Framework exists to motivate a realistic discovery-driven construction path, rather than hand-listing entities.

## References

- Reference Implementation Blueprint v1.0
- [`docs/architecture/02_Ontology_Framework_Design_Specification.md`](../../docs/architecture/02_Ontology_Framework_Design_Specification.md)
- [`src/mineproductivity/ontology/README.md`](../../src/mineproductivity/ontology/README.md)
