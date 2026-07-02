# Locked SSOT Source Documents

## Purpose

Verbatim archival copies of the locked Single Source of Truth (SSOT) documents supplied by the project's Chief Software Architect stakeholder, kept in-repository so implementers and AI contributors can always refer back to the original source material without depending on external file paths.

## Contents

- `MineProductivity_Developer_Cookbook_Guide.docx` — Developer & Cookbook Guide, Part I (Getting Started).
- `MineProductivity_Developer_Cookbook_Guide_Part_II.docx` — Developer & Cookbook Guide, Part II (Mining Domain Concepts).
- `MineProductivity_Developer_Cookbook_Guide_Part_III.docx` — Developer & Cookbook Guide, Part III (Mine Productivity KPI Standard Library & Cookbook).
- `MineProductivity_Learning_Benchmark_Suite_v1.0.docx` — Learning & Benchmark Suite v1.0.
- `MineProductivity_Developer_Documentation.html` — the rendered developer documentation website (architecture overview, SDK reference, quick start).

## Status

**Read-only archive.** These files are the governed artifacts referenced throughout `docs/architecture/*_Design_Specification.md` and `docs/design/*_Implementation_Checklist.md`. Do not edit them in place; if a locked document is revised upstream, replace the file wholesale and note the change in `CHANGELOG.md`.

## Known Gap

The Master Architecture Handbook v1.0 and Reference Implementation Blueprint v1.0 — referenced throughout this project as locked SSOT documents — have not yet been supplied as standalone files into this repository. Every design specification that cites them does so based on architectural facts established by (a) the explicit, directive instructions used to build the locked Repository Skeleton (v0.1.0) and Core Foundation Library (v0.2.0), and (b) the architectural principles restated consistently across the documents archived here. If and when the Handbook and Blueprint documents themselves are supplied, they should be added to this folder and any design specification found to conflict with them must be revised.

## References

- Root [README.md](../../../README.md)
- [`docs/architecture/README.md`](../README.md)
