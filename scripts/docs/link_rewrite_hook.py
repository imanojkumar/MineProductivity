"""MkDocs hook: rewrite repo-relative links that escape the documentation
tree into absolute GitHub URLs.

Much of the site reuses Markdown that lives outside ``docs/`` (package
READMEs, example READMEs, root governance files) via the
include-markdown plugin. Those files legitimately link to repository
paths — source modules, example scripts, notebooks, ``LICENSE`` — that
have no page in the built site. Rather than edit every source document,
this hook resolves each relative link against its page location; if the
target escapes ``docs/`` it is rewritten to an absolute
``github.com/.../blob|tree/main/...`` URL, which is valid both on the
site and on GitHub. Links that resolve *inside* the docs tree are left
untouched so MkDocs still validates them (and ``--strict`` still fails on
a genuinely broken in-site link).
"""

from __future__ import annotations

import posixpath
import re

REPO = "https://github.com/imanojkumar/MineProductivity"
BRANCH = "main"

# Markdown inline links: ](url) — captures the URL up to the closing paren.
_LINK = re.compile(r"\]\(\s*(<?)([^)\s>]+)(>?)\s*\)")


def _github(repo_path: str, fragment: str, *, trailing_slash: bool) -> str:
    kind = "tree" if (trailing_slash or not posixpath.splitext(repo_path)[1]) else "blob"
    absolute = f"{REPO}/{kind}/{BRANCH}/{repo_path}"
    return f"{absolute}#{fragment}" if fragment else absolute


def _rewrite_url(url: str, page_dir: str, built: set[str]) -> str:
    if url.startswith(("http://", "https://", "#", "mailto:", "//")):
        return url

    path, _, fragment = url.partition("#")
    if not path:  # pure in-page anchor
        return url

    trailing_slash = path.endswith("/")
    resolved = posixpath.normpath(posixpath.join(page_dir, path))

    if resolved.startswith(".."):
        # Escapes the docs tree entirely -> a repository file/dir on GitHub.
        return _github(resolved.lstrip("./"), fragment, trailing_slash=trailing_slash)

    if resolved in built or f"{resolved}/README.md" in built or resolved.endswith("/"):
        # A real in-site page (or a directory index) -> let MkDocs validate it.
        return url

    # Resolves inside docs/ but has no built page (excluded or absent) ->
    # point at the source file in the repository so the link still works.
    return _github(f"docs/{resolved}", fragment, trailing_slash=trailing_slash)


def on_page_markdown(markdown: str, *, page, config, files) -> str:  # type: ignore[no-untyped-def]
    page_dir = posixpath.dirname(page.file.src_uri)
    built = {f.src_uri for f in files if f.is_documentation_page()}

    def _sub(match: re.Match[str]) -> str:
        open_angle, url, close_angle = match.groups()
        new_url = _rewrite_url(url, page_dir, built)
        if new_url == url:
            return match.group(0)
        return f"]({open_angle}{new_url}{close_angle})"

    return _LINK.sub(_sub, markdown)
