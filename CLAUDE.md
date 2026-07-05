# Repository Engineering Rules — MineProductivity

Persistent rules for any Claude Code session working in this repository, across all future architecture phases. These are process rules, not architecture: for the actual system design, see `docs/architecture/README.md` and the root `README.md`'s "Architectural Layering & Dependency Direction" section.

## 1. Architecture Stability Rule

The MineProductivity platform architecture is now mature (Foundation Layer through Simulation, `core → ontology → events → kpis → analytics → decision → digital_twin → simulation`, all locked). Do not redesign stable architecture simply because another design is possible. Only change architecture when correcting an actual defect, an internal inconsistency, a violation of the dependency rules, or a measurable maintainability issue. Favor stability over novelty.

## 2. Single Source of Truth Rule

Avoid hardcoding version numbers throughout the repository. The one authoritative version source is `src/mineproductivity/__init__.py`'s `__version__`; `pyproject.toml` reads it dynamically via `[tool.hatch.version]`. Prefer deriving version information from it wherever practical. Tests must compare against installed package metadata (`importlib.metadata.version("mineproductivity")`) or the authoritative source itself, never a hardcoded literal (see `tests/unit/core/test_public_api.py::TestPackageVersion` for the pattern). Where a format genuinely requires a duplicated literal (e.g. `CITATION.cff`, `docs/citation/*`, `CHANGELOG.md` entries — none of which can read `__version__` dynamically), keep it in sync at each version bump rather than treating the duplication as eliminable.

## 3. Citation Rule

Always use the Zenodo **Concept DOI** (`10.5281/zenodo.21172767`) in repository documentation and citation files (`CITATION.cff`, `docs/citation/CITATION.md`, `docs/citation/MineProductivity.bib`, README badges/footer) unless there is an explicit, documented reason to reference a version-specific DOI instead.

## 4. End-of-Phase Standard

Every completed architecture phase (a new Design Specification + Implementation Checklist + ADR, or a repository-wide synchronization pass like this one) must finish with, in order:

1. **Architecture QA** — internal consistency, section numbering, layering, dependency correctness, naming, cross-document references, public API, diagram consistency.
2. **Repository synchronization** — `README.md`, `ROADMAP.md`, `CHANGELOG.md`, `docs/architecture/README.md`, citation files, and every affected `src/mineproductivity/*/README.md` reflect the new state (dependency chains, implementation status, milestone tables).
3. **Documentation validation** — `python scripts/quality/check_docs.py` (0 broken links, 0 failed snippets). Run it from an environment with `mineproductivity` actually installed (e.g. `pip install -e .` into a venv) — running it against an environment without the package installed produces spurious snippet-execution failures unrelated to the documentation itself.
4. **Full CI-quality validation** — `ruff check .`, `mypy --strict src/mineproductivity`, `pytest` (full suite), plus `scripts/quality/smoke_test.py` and `scripts/quality/perf_smoke.py`.
5. **Version review** — decide MINOR vs. no bump (or MAJOR, if ever warranted) per SemVer, with explicit justification tied to what actually changed (docs-only additive milestones are a MINOR bump under this repository's established convention).
6. **Release readiness report** — Files Modified, Files Created, Validation Results, Remaining Technical Debt, Architecture Quality Assessment, Suggested Improvements, Ready for Merge?

Only after all six steps pass should the phase be considered complete. Do not commit anything unless explicitly asked — leave all edits in the working tree for review.
