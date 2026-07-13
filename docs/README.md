# Documentation

## Purpose

Central documentation hub for MineProductivity, structured to mirror the six locked Single Source of Truth (SSOT) documents governing this project's architecture and implementation.

## Scope

Covers architecture rationale, the reference implementation blueprint, developer/cookbook guidance, the learning and benchmark suite, generated API reference material, and supporting images/assets. Does not include the original locked DOCX documents themselves, which remain the canonical, version-controlled artifacts outside this repository's source tree.

## Responsibilities

- Provide a navigable map from each locked SSOT document to the corresponding repository structure.
- Host developer-facing conceptual documentation (mkdocs site source).
- Track documentation-to-code traceability as implementation proceeds.

## Contents

- `architecture/` - Master Architecture Handbook v1.0 companion notes.
- `reference_blueprint/` - Reference Implementation Blueprint v1.0 companion notes.
- `developer_guide/` - Developer & Cookbook Guide, Parts I-III.
- `learning_suite/` - Learning & Benchmark Suite v1.0 companion notes.
- `api/` - Generated/placeholder API reference documentation.
- `images/` - Diagrams, architecture illustrations, and figures referenced by documentation.
- `assets/` - Non-image supporting assets (data samples, downloadable files) referenced by documentation.

## Dependencies

None. This directory contains only documentation; it must never contain or import Python source code.

## Future Work

Populate each subdirectory with content derived from the locked SSOT documents as implementation phases (see ROADMAP.md) proceed. Wire up `mkdocs.yml` to a documentation-build CI workflow.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
- Developer & Cookbook Guide - Parts I, II, III
- Learning & Benchmark Suite v1.0
