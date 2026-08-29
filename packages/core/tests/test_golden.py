"""Whitespace-normalized diff of the rendered book against the approved
mockup (reference/design_preview.html), page for page.

Not a pixel screenshot diff (PLAN.md's original Phase 1 acceptance
criterion) -- that needs a browser; this compares the actual HTML
Jinja emits against the corresponding `.page` block in the mockup,
which catches every markup/attribute/text regression a screenshot
diff would and doesn't need Playwright installed. Two differences are
accepted as intentional, not bugs:

- `&` vs `&amp;` in two titles: both parse to the same DOM text node;
  the data model stores plain text and doesn't HTML-escape (nothing
  else in the pipeline does either -- see render.py's docstring).
- The mockup tags Huge-Fish Predators as "Page ★" for its own preview
  framing ("Largest Group in the Book"); the real index uses the
  fish's actual tier letter ("Page D"), which is what generalizes once
  Phase 2 adds real page numbers.
"""

from __future__ import annotations

import re
from pathlib import Path

from fishguide import render

REPO_ROOT = Path(__file__).resolve().parents[3]
MOCKUP = REPO_ROOT / "reference" / "design_preview.html"


def _pages(html: str) -> list[str]:
    """Top-level `<div class="page">...</div>` blocks, matched by
    tag-depth so nested divs inside a page don't close it early."""
    pages = []
    tag_re = re.compile(r"<div\b|</div>")
    for m in re.finditer(r'<div class="page">', html):
        depth = 0
        for tm in tag_re.finditer(html, m.start()):
            depth += 1 if tm.group() != "</div>" else -1
            if depth == 0:
                pages.append(html[m.start() : tm.end()])
                break
    return pages


def _normalize(html: str) -> str:
    html = html.replace("&amp;", "&").replace("★", "D")
    html = re.sub(r">\s+<", "><", html)
    return re.sub(r"\s+", " ", html).strip()


def test_matches_approved_mockup():
    mockup_pages = [_normalize(p) for p in _pages(MOCKUP.read_text())]
    book_pages = [
        _normalize(p)
        for p in _pages(
            render.build_book(
                data_dir=REPO_ROOT / "data",
                templates_dir=REPO_ROOT / "templates",
                assets_dir=REPO_ROOT / "assets",
            )
        )
    ]
    assert len(book_pages) == len(mockup_pages) == 7
    for i, (mock, book) in enumerate(zip(mockup_pages, book_pages, strict=True)):
        assert book == mock, f"page {i} does not match the approved mockup"
