"""Session-scoped fixtures shared by integration tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "plugins"


@pytest.fixture(scope="session")
def registry_fixture_plugins_installed() -> None:
    """Editable-install the healthy and broken registry test fixture
    plugin packages into the current interpreter's environment, so
    ``importlib.metadata.entry_points()`` can discover them for real
    (design spec §29, §30 Category B).

    Installing is idempotent (``pip install -e`` on an already-installed
    editable package is a fast no-op re-link), so this is safe to depend
    on from more than one test in the same session.
    """
    for fixture_name in ("registry_fixture_healthy", "registry_fixture_broken"):
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--quiet",
                "--disable-pip-version-check",
                "--no-deps",
                "-e",
                str(_FIXTURES_DIR / fixture_name),
            ],
            check=True,
        )
