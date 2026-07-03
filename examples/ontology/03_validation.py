"""Demonstrate `OntologyValidator`'s two kinds of cross-entity reference
checking, and its central rule: an unresolved reference is always a
*warning* in the returned `ValidationResult`, never a raised exception --
an orphaned reference must never silently halt ingestion of everything
else (Cookbook Part I, Ch. 8).

Run: python examples/ontology/03_validation.py
"""

from __future__ import annotations

from mineproductivity.ontology import Bench, Fleet, OntologyValidator, Pit


def main() -> None:
    print("--- Structural validation happens at construction, always ---")
    pit = Pit(id="pit-west", mine_id="bingham-west", commodity="copper")
    print(f"constructed {pit.id} (would have raised OntologyValidationError if mine_id were blank)")

    print()
    print("--- OntologyValidator: *_type_code fields resolve against ontology's own registry ---")
    validator = OntologyValidator()
    good_fleet = Fleet(
        id="FL-NORTH", mine_id="bingham-west", equipment_type_code="RIGID_HAUL_TRUCK"
    )
    print(f"good_fleet: is_valid={validator.validate(good_fleet).is_valid}")

    broken_fleet = Fleet(
        id="FL-BROKEN", mine_id="bingham-west", equipment_type_code="NOT_A_REAL_TYPE"
    )
    broken_result = validator.validate(broken_fleet)
    print(f"broken_fleet: is_valid={broken_result.is_valid}")
    print(f"  errors: {broken_result.errors}")

    print()
    print("--- *_id fields need an injected resolver, since ontology doesn't persist instances ---")
    known_ids = {"pit-west", "bingham-west"}
    resolving_validator = OntologyValidator(
        entity_resolver=lambda entity_id: entity_id in known_ids
    )

    good_bench = Bench(id="bench-7", pit_id="pit-west", elevation_m=1820.0)
    print(f"good_bench: is_valid={resolving_validator.validate(good_bench).is_valid}")

    orphaned_bench = Bench(id="bench-orphan", pit_id="pit-does-not-exist", elevation_m=1800.0)
    orphan_result = resolving_validator.validate(orphaned_bench)
    print(f"orphaned_bench: is_valid={orphan_result.is_valid}")
    print(f"  errors: {orphan_result.errors}")

    print()
    print(
        "--- Crucially: validate() never raises. Ingestion of the rest of the batch continues. ---"
    )
    batch = [good_fleet, broken_fleet, good_bench, orphaned_bench]
    results = [(entity.id, resolving_validator.validate(entity).is_valid) for entity in batch]
    for entity_id, is_valid in results:
        status = "OK" if is_valid else "WARNING (orphaned reference)"
        print(f"  {entity_id}: {status}")
    print(f"processed all {len(batch)} entities without a single exception raised")


if __name__ == "__main__":
    main()
