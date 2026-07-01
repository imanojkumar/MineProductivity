# Contributing to MineProductivity

Thank you for your interest in contributing. MineProductivity is
documentation-first and architecture-governed: before writing code, please
read the locked Single Source of Truth documents referenced in
[`docs/README.md`](docs/README.md).

## Guiding Rules

1. **Documentation governs structure.** If your change requires a directory,
   package, or module that does not already exist in this skeleton, it must
   first be justified against the Master Architecture Handbook v1.0 or the
   Reference Implementation Blueprint v1.0.
2. **Respect the dependency direction.** See the layering diagram in the root
   [README.md](README.md#architectural-layering--dependency-direction).
   Lower layers (`core`, `ontology`) must never import from higher layers.
3. **Test-first.** New code in `src/mineproductivity/<package>/` must be
   accompanied by tests in the mirrored `tests/unit/<package>/` (and
   `tests/integration/` where applicable) in the same pull request.
4. **Metadata-first.** New KPIs, datasets, or connectors must ship with
   complete metadata (units, provenance, versioning) before behavior.
5. **Plugin-first.** Prefer registering new capabilities through
   `mineproductivity.registry` / `mineproductivity.plugins` rather than
   hard-coding them into `core`.
6. **No shortcuts.** Do not bypass pre-commit hooks, do not merge without
   review, and do not introduce TODO-only or partially-implemented code paths.

## Development Setup

```bash
git clone https://github.com/mineproductivity/MineProductivity.git
cd MineProductivity
python -m venv .venv
source .venv/bin/activate      # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
pre-commit install
```

## Workflow

1. Open or claim an issue describing the change.
2. Create a feature branch: `git checkout -b feat/<short-description>`.
3. Make your change, respecting package boundaries and dependency direction.
4. Add or update tests and package `README.md` files as needed.
5. Ensure `pre-commit run --all-files` passes locally.
6. Open a pull request using the provided template.

## Code Style

- Python 3.12+, formatted and linted per the tooling configured in
  `pyproject.toml` and `.pre-commit-config.yaml`.
- Public APIs must be fully type-annotated.
- Every package must retain an accurate `README.md` describing its purpose,
  scope, responsibilities, contents, dependencies, future work, and
  references.

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):
`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`.

## Code of Conduct

This project adheres to the [Code of Conduct](CODE_OF_CONDUCT.md).
