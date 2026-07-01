# mineproductivity.cli

## Purpose

The command-line interface entry point for MineProductivity, composing the outermost layers (agents, visualization, decision) into user-facing commands.

## Scope

**What belongs here:**
- CLI command definitions and argument parsing.

**What must never belong here:**
- Business logic — the CLI only composes and invokes other packages.

## Responsibilities

- Implements the `cli` subsystem as defined in the Reference Implementation Blueprint v1.0.
- Currently contains no implementation — structural placeholder only.

## Contents

- `__init__.py` — package marker (no public API yet).
- `README.md` — this file.

## Dependencies

**Depends on:** `core`, `config`, `decision`, `visualization`, `agents`

**Depended on by:** Not yet consumed by another package.

## Future Work

Implement `cli` per its phase in ROADMAP.md, tests-first, following the metadata-first and plugin-first principles described in the root README.md.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
