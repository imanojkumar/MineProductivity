# Package Tutorial Implementation Standard

> **Status: FROZEN implementation contract.** This is the permanent process every
> Milestone 2 Package Tutorial (2–13) must follow. It captures the workflow
> validated on **Tutorial 1 - Core** and reviewed before adoption. The *structure*
> of a tutorial is **Package Tutorial Template v1.0**
> ([architecture §11](architecture/M02_PACKAGE_TUTORIALS.md)); this document is the
> *process* that produces one to standard.

**Purpose - small prompts.** With this standard frozen, a tutorial can be
commissioned with only two inputs:

- **package** (e.g. `ontology`)
- **tutorial number** (e.g. `2`)

Everything else - verification, structure, coverage, validation, extension,
integration, review, lock, checkpoint - is defined here. No large implementation
prompt is required.

**Reference implementation:** [`../tutorials/packages/01_core.md`](../tutorials/packages/01_core.md).
**Canonical structure:** [`architecture/M02_PACKAGE_TUTORIALS.md` §11](architecture/M02_PACKAGE_TUTORIALS.md).

---

## 1. Repository Verification Standard

**Verification-first is binding. Never write an API from memory.** Before drafting
a single word:

1. **Dump the public surface.** `python -c "import mineproductivity.<pkg> as m; print(len(m.__all__)); print(sorted(m.__all__))"`. This exact set is the *entire* teachable surface - nothing outside `__all__` is public.
2. **Read every source module** the tutorial will touch (`src/mineproductivity/<pkg>/*.py`). Confirm real method names, signatures, return types, error types, and any subtlety (e.g. Core's `eq=False`-must-be-repeated rule, the `_normalize`→`validate` order). Docstrings often name the ADR/design rationale - cite it.
3. **Inventory the examples.** `ls examples/<pkg>/`. If the directory is **absent** (known: `analytics`, `plugins` - Risk R2) or thin, new scripts must be authored to this standard; otherwise reuse.
4. **Execute every reuse script** and **capture real output**: `python examples/<pkg>/<script>.py`. Exit `0` is necessary but not sufficient - read the output critically (a script that runs can still be wrong, e.g. mislabelled units).
5. **Verify every cross-link target exists** before linking it (`api-reference/<pkg>.md`, `packages/<pkg>.md`, the matching M1 lesson, any architecture spec/ADR). Do **not** link a page that does not exist - it breaks `mkdocs --strict`. If a package has no dedicated architecture spec/ADR, link the Handbook README instead.
6. **Build the extension example in the scratchpad** (§5) and run the full gate set on it *before* pasting it into the tutorial.

Record every non-obvious finding in the `LEARNING_PROGRESS.md` **verified-API
carry-forward** table so later tutorials inherit it.

## 2. Template v1.0 Compliance Checklist

Front matter: milestone banner · **Objective** · **Prerequisites** · **Running the examples**.
Body: the **16 numbered sections** below. Footer: **"Next package tutorial"** pointer.

- [ ] 1 · Why this package exists - problem, why-before-how
- [ ] 2 · Architectural role - position in the locked chain; DIP
- [ ] 3 · **Integration with adjacent layers** - see §6 rules (mandatory; "N/A - foundational layer" **only** for Core)
- [ ] 4 · Package structure - module map (abbreviate for < ~15 symbols)
- [ ] 5 · Public APIs - full `__all__`, role-grouped, under the coverage convention (§3)
- [ ] 6 · Conceptual model - the few ideas that explain the package
- [ ] 7 · Real mining examples - full when domain-free/thin; abbreviated for domain packages
- [ ] 8 · Step-by-step walkthroughs - numbered `8.x`; **each ends with verbatim executed output**
- [ ] 9 · Repository example reuse - table: script → APIs → walkthrough
- [ ] 10 · Common mistakes - verified failure modes + fix
- [ ] 11 · Best practices
- [ ] 12 · Performance considerations - full where real; else 1–2 bullets
- [ ] 13 · Extension points - runnable, gate-clean example (§5 rules)
- [ ] 14 · Exercises - 4–5, easy→open, incl. a build-against-the-extension-point task
- [ ] 15 · Reference solutions - collapsed `??? success` per exercise
- [ ] 16 · Further reading - package guide · API ref · Handbook · M1 lesson(s)

**Abbreviation rule:** a section is **never dropped**; sections 7 and 12 may be
abbreviated to a short note *with a one-line reason*. All others are substantive.

**Split rule (large packages):** single tutorial by default; split into `part A /
part B` (same structure, walkthroughs partitioned) only when a **validated draft**
exceeds ~700 rendered lines **or** ~40 `[deep]` symbols. Likely: `ontology` (56),
`analytics` (53), `decision` (49). A split is a length accommodation, not a format
change.

## 3. Coverage Convention

Every symbol in `<pkg>.__all__` belongs to **exactly one** category; **none is left
undocumented**:

- **[deep]** - taught in a §8 walkthrough with an **executed** example and verbatim
  output, or in the §13 extension example.
- **[ref]** - reference coverage: a one-line "what / when to reach for it" in a
  **"Reference coverage"** subsection of §5, plus the API-reference pointer.
  Reserved for cross-cutting / marker / type-alias symbols used mostly *through*
  other packages.

**Acceptance test** (author must run before lock):

```python
import mineproductivity.<pkg> as m, pathlib
text = pathlib.Path("docs/tutorials/packages/NN_<pkg>.md").read_text(encoding="utf-8")
missing = {s for s in m.__all__ if f"`{s}`" not in text}
assert not missing, f"undocumented public symbols: {sorted(missing)}"
```

Bias toward `[deep]`; reserve `[ref]` for genuinely peripheral symbols (Core's ratio
was 30 deep / 8 ref of 38).

## 4. Validation Pipeline

Run with the repo's checked interpreter (`.venv_check/Scripts/python.exe` on the
reference machine). **All must pass before lock:**

| Gate | Command | Bar |
|---|---|---|
| Lint | `python -m ruff check examples/<pkg>/ <extension>` | All checks passed |
| Format | `python -m ruff format --check examples/<pkg>/ <extension>` | Already formatted |
| Types | `python -m mypy --strict examples/<pkg>/ <extension>` | No issues |
| Execute | `python examples/<pkg>/<script>.py` (each) | exit `0`; output pasted **verbatim** into the tutorial |
| Tests | `python -m pytest -q` | No regression (Core baseline: **2986 passed**) |
| Docs build | `python -m mkdocs build --strict` | **0 warnings** |
| Doc check | `python scripts/quality/check_docs.py` | 0 broken / 0 failed |

If a tutorial only edited docs (reuse-only, no `src`/example/test change), `pytest`
cannot regress and the doc gates plus example execution suffice - but state that
explicitly in the lock record.

**Shared infrastructure - LANDED (Tutorial 2):** the automated lesson-execution
test lives at `tests/smoke/test_learning_suite_examples.py`. It runs every M1
lesson and every locked Package Tutorial's example scripts as subprocesses,
asserting exit `0` (architecture §7). **When a tutorial locks, append its example
directory name to `PACKAGE_TUTORIAL_EXAMPLE_DIRS`** in that file - its scripts are
then covered automatically. This retrofits the whole corpus and guards against rot.

## 5. Extension Point Rules

Every package has a seam; §13 must teach it with a **runnable, gate-clean** example.

- **Interface-only packages** (ship zero implementations of the key contract -
  `analytics`, `decision`, `digital_twin`, `simulation`, `optimization`, `agents`,
  `visualization`): §13 **authors a real plugin**, reusing the existing plugin demo
  (`examples/<pkg>/05_plugin_*.py` or `04_plugin_*.py`) where one exists.
- **Concrete-with-a-seam packages** (`kpis`, `connectors`) and **Core**: §13
  implements a custom subclass of the abstract base (Core: a `BaseRepository`), and
  includes the **"not interface-only"** note distinguishing "provide a
  production-grade implementation" from "the platform refuses to choose for you".
- **`registry & plugins`**: the package *is* the mechanism; §13 authors an
  entry-point plugin.
- The example must **preserve the contract's semantics** (e.g. the right errors)
  and may **add** a domain method (extension, not modification). If it is not a
  committed repo script, build and gate it in the scratchpad and paste the
  verified code + output.

## 6. Integration Section Rules (§3)

- **Mandatory and substantive for Tutorials 2–13.** State the exact **public types
  of the layer(s) below** that this package consumes, and show it **consuming
  governed outputs without re-deriving them** - the platform's central discipline
  (e.g. `analytics` reads `KPIResult`s; it never recomputes tonnes ÷ hours).
- Name the direction: what it reads from below, what it hands up.
- **Core is the only package that marks this "N/A - foundational layer"**, because
  it has no lower dependency. No other tutorial may use the N/A escape.

## 7. Review Checklist

Every tutorial gets an independent pass (author ≠ reviewer in spirit) across the
six axes established on Tutorial 1:

- **Educational** - progression, pacing, readability, prerequisite handling, cognitive load; builds on (never repeats) the matching M1 lesson.
- **Engineering** - API coverage complete (§3 partition holds), public APIs only, verification-first evidence present, mining realism.
- **Structure** - all required sections present; conditional sections justified if abbreviated; ordering per Template v1.0.
- **Example quality** - reuse verified-executing; extension example gate-clean; exercises graded with shipped solutions; outputs verbatim.
- **Consistency** - with M1 philosophy, the M02 architecture, the roadmap, and this standard.
- **Scalability** - no template drift; nothing that would not generalise to the remaining packages.

## 8. Definition of Done (per tutorial)

- [ ] Public APIs only; realistic mining domain; builds on the M1 lesson
- [ ] Template v1.0 compliant (§2); coverage convention partition holds (§3)
- [ ] §3 Integration substantive (or "N/A - foundational" for Core only)
- [ ] §13 extension example runnable and gate-clean
- [ ] Every code block executed; **Expected output pasted from a real run**
- [ ] Exercises include a build-against-the-extension-point task **and** ship solutions
- [ ] Full validation pipeline green (§4)
- [ ] Cross-links resolve: script · API reference · package guide · Handbook · next tutorial
- [ ] Navigation updated (nav entry under "Package Tutorials"); index updated
- [ ] Independent review passed (§7)
- [ ] `LEARNING_PROGRESS.md` updated (§9, §10); `src/` unmodified unless a recorded defect

## 9. Lock Procedure

1. Confirm the full **Definition of Done** (§8) and **Validation Pipeline** (§4) are green.
2. Paste **real** outputs into the tutorial; do not paraphrase them.
3. Update `LEARNING_PROGRESS.md`: mark the tutorial **LOCKED** in the Package
   Tutorials progress table, add a **LOCK record** (validation results, files
   changed, lessons learned) and append to the **verified-API carry-forward**.
4. A LOCKED tutorial is **not modified without a recorded defect** (same discipline
   as M1 lessons and the frozen framework).
5. **Git is out of scope for the author.** Do not commit or push - the maintainer
   (Manoj) performs all git operations. End with the working tree updated and the
   checkpoint written.

## 10. Checkpoint Procedure

- The **operative checkpoint unit is one tutorial** (per-tutorial LOCK), giving 13
  natural resume points - not only the M2a/M2b seam.
- At every boundary, `LEARNING_PROGRESS.md` must reflect true state and name the
  **exact next task** (package + number + first verification step).
- Carry the **verified-API notes** forward so no later tutorial re-derives a fact
  already established.
- If context runs short mid-tutorial: finish the current section, update the
  tracker, write a checkpoint naming the precise resumption point. Do **not** leave
  a half-validated tutorial marked complete.

## 11. Lessons Learned from Tutorial 1

Carry these into Tutorials 2–13:

- **Verification caught real errors before.** In M1, guessing APIs produced
  concrete bugs (wrong kwargs, wrong enum members, mislabelled slope units). The
  fix is non-negotiable source-reading + execution. Exit `0` ≠ correct.
- **Reuse-first held for Core** - no new example script was needed; the extension
  example was taught inline (verified in scratchpad), matching M1's snippet style.
  Expect the same for most packages; `analytics`/`plugins` will need new scripts.
- **Coverage must be honest.** "Master the whole package" over-claims if 8 symbols
  are only name-dropped. The `[deep]`/`[ref]` convention (§3) makes the claim true
  and testable.
- **The Integration section is untestable on Core** (base layer) - so Core is a
  perfect template for everything *except* §3. Tutorials 2–13 must give §3 real
  content; do not copy Core's N/A note.
- **Placement & nav:** deep tutorials live at `docs/tutorials/packages/NN_<pkg>.md`
  under the nav "Package Tutorials" group; legacy thin `tutorials/<pkg>.md`
  README-includes stay as relabelled "API walkthroughs (reference)" and are retired
  per-package as each deep tutorial lands.
- **Editing gotcha:** the docs linter normalises em-dashes to hyphens - match on
  hyphens (or re-read) when doing exact-string edits, and prefer a full-file
  rewrite over many fragile renumbering edits when inserting a section.
- **Biggest open infra item:** the automated lesson-execution test (§4) is still
  unbuilt; land it early in M2a.

---

*This standard is frozen. Amend it only via the same governance path used for the
architecture (propose → review → record). It is referenced by the M2 architecture
(§11), the reference tutorial (Tutorial 1), and `LEARNING_PROGRESS.md`.*
