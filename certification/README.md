# Certification

## Purpose

Top-level conformance/certification suite validating a MineProductivity implementation against the Reference Implementation Blueprint v1.0 before it may be tagged 1.0.0.

## Scope

Certification golden datasets, validation procedures, and reference outputs. Does not include the certification harness code (see `src/mineproductivity/certification/`).

## Responsibilities

- Define the golden datasets and reference outputs that constitute the certification bar.
- Document the validation procedure used to certify a release candidate.

## Contents

- `golden_datasets/` — datasets used specifically for certification (may overlap conceptually with `datasets/golden/` but scoped to certification runs).
- `validation/` — validation procedure definitions and checklists.
- `reference_outputs/` — the authoritative expected outputs a conformant implementation must reproduce.

## Dependencies

`src/mineproductivity/certification/` (harness interfaces, once implemented).

## Future Work

Populate once the full Reference Implementation Blueprint is implemented (see ROADMAP.md, Phase 7).

## References

- Reference Implementation Blueprint v1.0
