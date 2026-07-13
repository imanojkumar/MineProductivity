# Examples - mineproductivity.core

## Purpose

Runnable, minimal, self-contained scripts demonstrating each foundational
building block in `mineproductivity.core`, in isolation, with no mining
domain concepts involved.

## Scope

Example scripts and their direct output. No test assertions live here
(see `tests/unit/core/` for that); each script is meant to be read and run
by a human evaluating the package, not executed by CI as a test suite.

## Responsibilities

- Show idiomatic usage of every public `core` base class.
- Serve as executable documentation that stays correct because it is
  actually run (see "Running the examples" below).

## Contents

- `01_entity_and_value_object.py` - `BaseEntity` identity semantics vs.
  `BaseValueObject` structural equality, immutability, and `replace()`.
- `02_repository.py` - `BaseRepository`/`InMemoryRepository`,
  `BaseSpecification` filtering.
- `03_factory_and_builder.py` - `BaseFactory` vs. `BaseBuilder`, and
  `Result[T]`-returning variants that avoid exceptions.
- `04_validation.py` - `BaseValidator`, `ValidationResult`,
  `CompositeValidator`.
- `05_serialization.py` - `BaseSerializer`, `DataclassSerializer`,
  `to_dict`.
- `06_result_and_maybe.py` - `Result[T]` and `Maybe[T]` combinators
  (`map`, `and_then`, `unwrap_or`) as an alternative to exceptions/`None`.

## Dependencies

Only `mineproductivity` itself (editable-installed from this repository).
No third-party packages.

## Running the Examples

```bash
pip install -e .
python examples/core/01_entity_and_value_object.py
python examples/core/02_repository.py
python examples/core/03_factory_and_builder.py
python examples/core/04_validation.py
python examples/core/05_serialization.py
python examples/core/06_result_and_maybe.py
```

Each script exits `0` and prints its own output; there is nothing to
configure.

## Future Work

Add an `examples/core/07_versioning_and_configuration.py` once a concrete
downstream package (e.g. `config`) demonstrates a realistic
`BaseConfiguration` subclass in context.

## References

- Reference Implementation Blueprint v1.0
- Developer & Cookbook Guide - Part I
- [`src/mineproductivity/core/README.md`](../../src/mineproductivity/core/README.md)
