# Unit Tests — mineproductivity.core

## Purpose

Unit tests for `src/mineproductivity/core/`, mirroring its structure one-to-one: one `test_*.py` module per source module.

## Scope

Isolated tests for `mineproductivity.core` only — no filesystem, network, or cross-package integration. Cross-package behavior belongs in `tests/integration/`.

## Responsibilities

- Cover every public symbol exported by `mineproductivity.core`.
- Exercise equality/hash semantics, immutability, validation, serialization, generic behavior, ABC enforcement, and edge cases for every base class.
- Maintain >95% line coverage of `src/mineproductivity/core/`.

## Contents

- `test_typing.py` — `Comparable`, `Identifiable`, `JSONValue`/`JSONPrimitive` aliases.
- `test_exceptions.py` — the `MineProductivityError` hierarchy.
- `test_value_object.py` — `BaseValueObject` equality, immutability, `_normalize`/`validate` hooks, `replace`.
- `test_entity.py` — `BaseEntity` identity-based equality/hash, cross-type inequality.
- `test_identifier.py` — `BaseIdentifier`, `UUIDIdentifier`.
- `test_metadata.py` — `BaseMetadata` defensive copying/freezing and validation.
- `test_versioning.py` — `BaseVersionedObject` monotonic versioning.
- `test_specification.py` — `BaseSpecification` and `&`/`|`/`~` composition.
- `test_result.py` — `Result[T]` ok/err semantics and combinators.
- `test_maybe.py` — `Maybe[T]` some/nothing semantics and combinators.
- `test_validator.py` — `BaseValidator`, `ValidationResult`, `CompositeValidator`.
- `test_serialization.py` — `BaseSerializer`, `DataclassSerializer`, `to_dict`.
- `test_configuration.py` — `BaseConfiguration`.
- `test_factory.py` — `BaseFactory`.
- `test_builder.py` — `BaseBuilder`.
- `test_repository.py` — `BaseRepository`, `InMemoryRepository`.
- `test_service.py` — `BaseService`.
- `test_public_api.py` — the `mineproductivity.core` package's exported surface and import structure.

## Dependencies

`pytest` (see root `pyproject.toml`).

## Future Work

Extend as `core` gains new base classes; keep the 1:1 file mapping to `src/mineproductivity/core/`.

## References

- Reference Implementation Blueprint v1.0
- Developer & Cookbook Guide — Part II
