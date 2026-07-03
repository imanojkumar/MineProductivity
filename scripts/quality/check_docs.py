"""Documentation validation: broken relative links across every Markdown
file, and execution of every fenced ```python block in the root README
and each implemented package's README.

Run locally or in CI:

    python scripts/quality/check_docs.py

Exits non-zero (and prints every failure found, not just the first) if
any relative link fails to resolve or any code block raises.
"""

from __future__ import annotations

import re
import sys
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Package READMEs contain "recipe" snippets that are sometimes a
# continuation of an earlier block in the same file (sharing imports),
# or illustrative fragments that reference a caller's own domain objects
# by name (e.g. `bench.id`, `MyConnector(...)`) and are not meant to run
# standalone. Blocks are executed in one shared, per-file namespace to
# tolerate the former; the latter still fail here and must be triaged by
# a human (not everything of the form "NameError" is a real bug -- see
# CONTRIBUTING.md).
SNIPPET_FILES = [
    "README.md",
    "src/mineproductivity/core/README.md",
    "src/mineproductivity/events/README.md",
    "src/mineproductivity/ontology/README.md",
    "src/mineproductivity/registry/README.md",
    "src/mineproductivity/plugins/README.md",
    "src/mineproductivity/connectors/README.md",
    "src/mineproductivity/kpis/README.md",
]

# Fragments intentionally left un-runnable by design (illustrative
# continuations referencing a caller's own already-constructed objects).
# Keyed by "path:block_index" as printed on failure; add an entry here
# only after confirming by hand that the block is correct documentation,
# not a real bug.
KNOWN_ILLUSTRATIVE_FRAGMENTS = {
    "src/mineproductivity/ontology/README.md:2",  # bench.id / pit.id
    "src/mineproductivity/ontology/README.md:3",  # candidate / known_ids
    "src/mineproductivity/plugins/README.md:1",  # discovered_manifests
    "src/mineproductivity/connectors/README.md:3",  # since / until / MyConnector
}

LINK_PATTERN = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
CODE_BLOCK_PATTERN = re.compile(r"```python\n(.*?)```", re.DOTALL)


def check_links() -> list[str]:
    failures = []
    all_md = [
        p
        for p in REPO_ROOT.rglob("*.md")
        if ".venv" not in str(p) and "node_modules" not in str(p) and ".pytest_cache" not in str(p)
    ]
    for path in all_md:
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in LINK_PATTERN.finditer(text):
            label, target = match.group(1), match.group(2)
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            target_path_only = target.split("#")[0]
            if not target_path_only:
                continue
            resolved = (path.parent / target_path_only).resolve()
            if not resolved.exists():
                rel = path.relative_to(REPO_ROOT)
                failures.append(f"{rel}: [{label}]({target}) does not resolve")
    return failures


def check_snippets() -> list[str]:
    """Each file's blocks execute in their own fake module, registered
    into ``sys.modules`` under a unique name for the duration of the
    check. This is not just isolation between files -- it is required
    for correctness: every source file in this codebase uses ``from
    __future__ import annotations``, so a snippet's ``ClassVar[str]``
    field annotation is a *string* at class-definition time, and
    ``dataclasses`` resolves such strings via
    ``sys.modules[cls.__module__].__dict__``. Leaving every block's
    ``__module__`` as the literal ``"__main__"`` would make that lookup
    resolve to *this script's own* globals (which never import
    ``ClassVar``), silently misclassifying every ``ClassVar`` field as a
    plain field with a default and breaking dataclass field ordering in
    a way that has nothing to do with the documentation being checked.
    """
    import sys

    failures = []
    for rel_path in SNIPPET_FILES:
        path = REPO_ROOT / rel_path
        blocks = CODE_BLOCK_PATTERN.findall(path.read_text(encoding="utf-8"))
        module_name = f"_check_docs_snippet_{rel_path.replace('/', '_').replace('.', '_')}"
        namespace: dict[str, object] = {"__name__": module_name}
        fake_module = type(sys)(module_name)
        fake_module.__dict__.update(namespace)
        sys.modules[module_name] = fake_module
        try:
            for i, block in enumerate(blocks):
                key = f"{rel_path}:{i}"
                if key in KNOWN_ILLUSTRATIVE_FRAGMENTS:
                    continue
                try:
                    exec(compile(block, key, "exec"), fake_module.__dict__)
                except Exception:
                    failures.append(f"{key}\n{traceback.format_exc()}")
        finally:
            del sys.modules[module_name]
    return failures


def main() -> int:
    link_failures = check_links()
    snippet_failures = check_snippets()

    print(f"checked links across the repository: {len(link_failures)} broken")
    for failure in link_failures:
        print(f"  BROKEN LINK: {failure}")

    print(f"checked README code snippets: {len(snippet_failures)} failed")
    for failure in snippet_failures:
        print(f"  SNIPPET FAILURE: {failure}")

    if link_failures or snippet_failures:
        return 1
    print("documentation validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
