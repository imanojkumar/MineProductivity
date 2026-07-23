"""Automated lesson-execution guard for the Learning Suite.

Every Milestone 1 Fundamentals lesson script, and every example script reused by
a *locked* Milestone 2 Package Tutorial, must run to completion (exit ``0``).
This protects a growing corpus of tutorial examples from silently rotting as the
framework evolves -- the single highest-leverage validation investment described
in ``docs/learning/PACKAGE_TUTORIAL_IMPLEMENTATION_STANDARD.md`` (§4) and the
Milestone 2 architecture (§7).

**Reusable by every remaining Package Tutorial.** When a package tutorial locks,
add its example directory name to :data:`PACKAGE_TUTORIAL_EXAMPLE_DIRS`; its
scripts are then covered automatically. No other change is needed.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = REPO_ROOT / "examples"

# Milestone 1 -- the ten Fundamentals lessons (one script per ``NN_*/`` directory).
FUNDAMENTALS_SCRIPTS = sorted((EXAMPLES / "fundamentals").glob("*/*.py"))

# Milestone 2 -- example directories of every LOCKED Package Tutorial.
# Extend this tuple (alphabetically) as each tutorial locks:
#   Tutorial 1 Core -> "core";  Tutorial 2 Ontology -> "ontology";  ...
PACKAGE_TUTORIAL_EXAMPLE_DIRS: tuple[str, ...] = (
    "core",
    "ontology",
    "events",
    "registry",
    "plugins",
    "connectors",
    "kpis",
    "analytics",
    "decision",
    "digital_twin",
    "simulation",
    "optimization",
    "agents",
    "visualization",
)
PACKAGE_TUTORIAL_SCRIPTS = sorted(
    script
    for directory in PACKAGE_TUTORIAL_EXAMPLE_DIRS
    for script in (EXAMPLES / directory).glob("*.py")
)

ALL_SCRIPTS = FUNDAMENTALS_SCRIPTS + PACKAGE_TUTORIAL_SCRIPTS


def _script_id(path: Path) -> str:
    return str(path.relative_to(EXAMPLES)).replace("\\", "/")


def test_learning_suite_corpus_is_discovered() -> None:
    """Guard against a broken glob silently collecting zero scripts."""
    assert len(FUNDAMENTALS_SCRIPTS) == 10, FUNDAMENTALS_SCRIPTS
    assert PACKAGE_TUTORIAL_SCRIPTS, "no Package Tutorial example scripts discovered"


@pytest.mark.parametrize("script", ALL_SCRIPTS, ids=_script_id)
def test_example_script_runs_to_exit_zero(script: Path) -> None:
    """Each Learning Suite example script must run to completion with exit 0."""
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        timeout=180,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, (
        f"{_script_id(script)} exited {result.returncode}\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )
