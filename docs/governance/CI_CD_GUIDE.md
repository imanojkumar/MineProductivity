# CI/CD Guide

Everything in `.github/workflows/` explained: what runs, when, why, and what to do when something goes red.

## Workflows

| File | Triggers | Purpose |
|---|---|---|
| `ci.yml` | push to `main`, PR to `main` | The correctness gate: `pytest` + coverage across a `{ubuntu, windows, macos} x {3.12, 3.13}` matrix (plus non-blocking 3.10/3.11 signal), then builds the wheel/sdist, `twine check`s them, and installs from wheel/sdist/editable/GitHub in fresh environments with a real smoke test. |
| `quality.yml` | push to `main`, PR to `main` | The cleanliness gate: `ruff check` + `ruff format --check`, `mypy --strict`, documentation validation (every relative Markdown link, every fenced `python` snippet in the root and package READMEs), and notebook execution. |
| `docs.yml` | push/PR to `main` touching `docs/**`, `mkdocs.yml`, or a `README.md` | Builds the `mkdocs` site and uploads it as an artifact. Not a deploy step (no `gh-pages` push yet — see Future Work). |
| `benchmark.yml` | push to `main`, PR to `main` | A performance *smoke* test (`scripts/quality/perf_smoke.py`) — generous wall-clock ceilings on a handful of representative operations, meant to catch a catastrophic regression (an accidental O(n²), a broken cache), not to track performance over time. |
| `dependency-review.yml` | PR to `main` | GitHub's `dependency-review-action`: flags newly-introduced dependencies with a moderate-or-worse known vulnerability or an unusual license, as a PR comment. |
| `codeql.yml` | push/PR to `main`, weekly (Monday 06:00 UTC) | GitHub CodeQL static analysis (`security-and-quality` query suite) for Python. |
| `security.yml` | push/PR to `main` touching `pyproject.toml`, weekly (Wednesday 06:00 UTC) | `pip-audit` against every installed dependency (`mineproductivity[dev]`) — see [Known Exceptions](#known-exceptions) below. |
| `release.yml` | push of a `v*.*.*` tag | Builds and `twine check`s the wheel/sdist, verifies the tag matches `mineproductivity.__version__`, and creates a GitHub Release with both artifacts attached. **Does not publish to PyPI** (see [Release Flow](#release-flow)). |

All workflows use `actions/setup-python`'s built-in `cache: pip` (keyed on `pyproject.toml`) — no separate `actions/cache` step is needed for the dependency install itself.

## Branch Strategy

Trunk-based: a single long-lived branch, `main`. Contributors work on short-lived `feat/<description>`, `fix/<description>`, etc. branches (per `CONTRIBUTING.md`) and open a PR back into `main`. There is no `develop` branch and no long-lived release branch — every release is cut from a specific commit on `main` via a tag.

## Release Flow

1. Land every change intended for the release on `main` through the normal PR process (`ci.yml` + `quality.yml` green).
2. Bump `src/mineproductivity/__init__.py`'s `__version__`, update `CHANGELOG.md` (see the existing entries for the expected format), update any version references in `README.md`, and update the hardcoded version assertion in `tests/unit/core/test_public_api.py::TestPackageVersion`.
3. Merge that version-bump PR to `main`.
4. Tag the resulting commit: `git tag v<version>` (matching `__version__` exactly — `release.yml` verifies this and fails the release if they disagree) and `git push origin v<version>`.
5. `release.yml` builds the wheel and sdist, runs `twine check --strict`, and creates a GitHub Release for the tag with both artifacts attached and auto-generated release notes (pointing readers at `CHANGELOG.md` for the curated version).
6. **PyPI publishing is intentionally not wired up.** `release.yml` contains a fully commented-out `publish-pypi` job using [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC — no API token to manage or leak). To enable it: register this repository/workflow as a Trusted Publisher on PyPI, then uncomment the job.

Nothing in this guide changes how versions are decided — see `ROADMAP.md` for the phasing and `CHANGELOG.md`'s own header note on software-version-vs-architecture-version independence.

## Developer Workflow

1. `pip install -e ".[dev]"` (see the root README's Getting Started section for the full extras table).
2. Make your change. Run locally before opening a PR: `pytest`, `ruff check .`, `ruff format .`, `mypy`. `pre-commit install` wires the first two into a pre-commit hook automatically.
3. Touching a package README's code snippets, any relative Markdown link, or a notebook? Run `python scripts/quality/check_docs.py` locally — it is exactly what `quality.yml`'s `docs-validation` job runs.
4. Open a PR against `main`. `ci.yml`, `quality.yml`, `docs.yml` (if docs changed), `benchmark.yml`, `dependency-review.yml`, and `codeql.yml` all run automatically.
5. All required checks green + review approval → merge.

## Failure Handling

- **`ci.yml` / `test` matrix fails on one OS only:** almost always a real platform difference (path separators, `tzdata` availability — Windows needs the `tzdata` PyPI package since it has no OS-native IANA database, already handled via `sys_platform == 'win32'` markers in `pyproject.toml`). Reproduce locally with the same OS if possible; do not skip the platform.
- **`ci.yml` / `test` matrix fails on Python 3.10 or 3.11 only:** expected and non-blocking (`continue-on-error: true`) — `pyproject.toml` declares `requires-python = ">=3.12"`, so these two cells are informational only, not a merge gate.
- **`ci.yml` / install-validation fails:** the package installs but something in the smoke test (`scripts/quality/smoke_test.py`) broke — usually a genuinely missing runtime dependency that only `pip install -e .` (editable, pulling the dev environment's already-resolved packages) was hiding.
- **`quality.yml` / `docs-validation` fails on a snippet:** re-run `python scripts/quality/check_docs.py` locally. If the failing block is a deliberately illustrative fragment (references a caller's own variable, e.g. `bench.id`), it belongs in that script's `KNOWN_ILLUSTRATIVE_FRAGMENTS` set, not a real bug — but confirm that by hand before adding it there.
- **`quality.yml` / `notebooks` fails:** run the same command locally: `jupyter nbconvert --to notebook --execute --inplace notebooks/beginner/*.ipynb` (after `python -m ipykernel install --user --name ci-kernel` and passing `--ExecutePreprocessor.kernel_name=ci-kernel`). `nbconvert` fails fast on the first cell that raises.
- **`benchmark.yml` fails:** a wall-clock ceiling in `scripts/quality/perf_smoke.py` was exceeded by a wide margin (the budgets are deliberately generous). Treat this as a real regression to investigate, not noise — but also account for CI runner variance before assuming the worst; re-run once before deep-diving.
- **`security.yml` fails:** a genuinely new vulnerability was found. Check whether a newer version of the flagged package satisfies the existing `pyproject.toml` constraint (often just needs `pip install --upgrade` + a lockstep CI cache bust); if the fix requires crossing a major version, treat it as a dependency-upgrade PR of its own, tested like any other change.
- **`release.yml` fails on the version-match check:** the pushed tag doesn't match `mineproductivity.__version__`. Delete the tag (`git tag -d vX.Y.Z && git push origin :refs/tags/vX.Y.Z`), fix whichever side is wrong, and re-tag.

## Known Exceptions

- **`security.yml` ignores `PYSEC-2026-113`** (a real Apache Arrow C++ Use-After-Free, fixed in `pyarrow>=23.0.1`) because `pyproject.toml`'s `events` extra currently pins `pyarrow>=14,<19`. Bumping across that many major `pyarrow` releases is a dependency-compatibility change requiring `events`' `ArrowEventCodec`/`ParquetEventCodec` to be re-validated against the new API — out of scope for CI/CD tooling work. Tracked here rather than silently ignored; remove the `--ignore-vuln` flag in `security.yml` once the `pyarrow` constraint is actually bumped and re-tested.
- **`docs.yml` does not use `mkdocs build --strict`.** `docs/architecture/*.md` (the locked design specifications) legitimately cross-link to the root `README.md` and to package READMEs under `src/mineproductivity/`, both outside mkdocs' own `docs_dir`. That's correct for GitHub's file browser and unresolvable within a single mkdocs site build; `--strict` would fail on those links permanently, for reasons unrelated to whether the site itself is sound.
- **`ci.yml`'s Python matrix does not fail on 3.10/3.11.** See Failure Handling above.

## Future Work

- Deploy `docs.yml`'s built site to GitHub Pages (`actions/deploy-pages`) once the maintainer decides this repository should have a public docs site.
- Enable the commented-out `publish-pypi` job in `release.yml` once a PyPI Trusted Publisher is registered.
- Revisit the `pyarrow` version constraint (see Known Exceptions) as its own dependency-upgrade change.
- Coverage-percentage badge once a coverage-reporting service (Codecov, Coveralls) is connected — deliberately not added yet to avoid a broken badge pointing at an unconfigured service.

## References

- `.github/workflows/` — the workflow files themselves.
- `CONTRIBUTING.md` — the PR workflow this guide's Developer Workflow section summarizes.
- `docs/governance/RELEASE_CHECKLIST.md` — the per-package Definition of Done this guide's automation enforces mechanically where possible.
- `CHANGELOG.md`, `ROADMAP.md` — release history and phasing.
