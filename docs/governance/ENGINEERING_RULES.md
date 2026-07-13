# Repository Engineering Rules — MineProductivity

Persistent, tool-neutral engineering rules for anyone (human or automated
assistant) working in this repository, across all maintenance and future
work. These are **process** rules, not architecture: for the system design
itself, see [`docs/architecture/README.md`](../architecture/README.md) and
the root [`README.md`](../../README.md)'s "Architectural Layering &
Dependency Direction" section. For the per-release merge gate, see
[`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md).

## 1. Architecture Stability

The MineProductivity platform architecture is complete and locked
(`core → ontology → events → kpis → analytics → decision → digital_twin →
simulation → optimization → agents → visualization`, plus the cross-cutting
`registry`/`plugins`/`connectors`). Do not redesign stable architecture
simply because another design is possible. Change architecture only to
correct an actual defect, an internal inconsistency, a violation of the
dependency rules, or a measurable maintainability issue. Favor stability
over novelty. New value ships as plugins (solvers, reasoning backends,
renderers, connector adapters) and applications, evaluated against the
locked specifications — not as changes to the locked packages.

## 2. Single Source of Truth for the Version

Do not hardcode version numbers throughout the repository. The one
authoritative version source is `src/mineproductivity/__init__.py`'s
`__version__`; `pyproject.toml` reads it dynamically via
`[tool.hatch.version]`. Derive version information from it wherever
practical. Tests must compare against installed package metadata
(`importlib.metadata.version("mineproductivity")`) or the authoritative
source itself, never a hardcoded literal (see
`tests/unit/core/test_public_api.py::TestPackageVersion` for the pattern).

Where a format genuinely requires a duplicated literal — `CITATION.cff`,
`docs/citation/*`, and `CHANGELOG.md` entries, none of which can read
`__version__` dynamically — keep it in sync at each version bump rather
than treating the duplication as eliminable. After any `__version__`
change, reinstall the package (`pip install -e .`) before running tests so
the metadata-based version test observes the new value.

## 3. Citation Uses the Concept DOI

Always use the Zenodo **Concept DOI** (`10.5281/zenodo.21172767`) in
repository documentation and citation files (`CITATION.cff`,
`docs/citation/CITATION.md`, `docs/citation/MineProductivity.bib`, README
badges/footer) unless there is an explicit, documented reason to reference
a version-specific DOI instead. The Concept DOI always resolves to the
latest published release.

## 4. End-of-Phase Standard

Every completed phase (a new Design Specification + Implementation Checklist
+ ADR, or a repository-wide synchronization pass) must finish with, in
order:

1. **Architecture QA** — internal consistency, section numbering, layering,
   dependency correctness, naming, cross-document references, public API,
   diagram consistency.
2. **Repository synchronization** — `README.md`, `ROADMAP.md`,
   `CHANGELOG.md`, `docs/architecture/README.md`, citation files, and every
   affected `src/mineproductivity/*/README.md` reflect the new state
   (dependency chains, implementation status, milestone tables).
3. **Documentation validation** — `python scripts/quality/check_docs.py`
   (0 broken links, 0 failed snippets). Run it from an environment with
   `mineproductivity` actually installed (e.g. `pip install -e .` into a
   venv); running it against an environment without the package installed
   produces spurious snippet-execution failures unrelated to the
   documentation itself.
4. **Full CI-quality validation** — `ruff check .`,
   `ruff format --check .`, `mypy --strict src/mineproductivity`, `pytest`
   (full suite), plus `scripts/quality/smoke_test.py` and
   `scripts/quality/perf_smoke.py`.
5. **Version review** — decide MINOR vs. no bump (or MAJOR, if ever
   warranted) per SemVer, with explicit justification tied to what actually
   changed. Under this repository's established convention, one MINOR is
   bumped per completed architecture or implementation milestone.
6. **Release-readiness report** — Files Modified, Files Created, Validation
   Results, Remaining Technical Debt, Architecture Quality Assessment,
   Suggested Improvements, Ready for Merge?

Only after all six steps pass should the phase be considered complete.

## 5. Single Source of Truth is the Implementation

The repository implementation, tests, CI results, and Git history are the
single source of truth. If any document conflicts with the verified
implementation, update the documentation to match the code — never change
correct code to match stale documentation, and do not preserve outdated
documentation for historical reasons.

## References

- [`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md) — the per-release merge gate.
- [`CI_CD_GUIDE.md`](CI_CD_GUIDE.md) — CI/CD pipeline, branch strategy, release flow.
- [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md) — contributor workflow.
