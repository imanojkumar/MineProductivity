# mineproductivity.plugins

## Purpose

The plugin loading and lifecycle mechanism built on top of `registry`, enabling third-party extension of MineProductivity without modifying core packages.

## Scope

**What belongs here:**
- Plugin discovery, loading, and lifecycle interfaces.

**What must never belong here:**
- Specific plugin implementations — this package defines the mechanism, not the plugins.

## Responsibilities

- Implements the `plugins` subsystem as defined in the Reference Implementation Blueprint v1.0.
- Currently contains no implementation — structural placeholder only.

## Contents

- `__init__.py` — package marker (no public API yet).
- `README.md` — this file.

## Dependencies

**Depends on:** `core`, `exceptions`, `registry`, `config`

**Depended on by:** `cli`

## Future Work

Implement `plugins` per its phase in ROADMAP.md, tests-first, following the metadata-first and plugin-first principles described in the root README.md.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
