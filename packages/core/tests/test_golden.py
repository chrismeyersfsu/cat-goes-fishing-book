"""Whitespace-normalized diff of the rendered book against the approved
mockup (reference/design_preview.html), page for page.

Not a pixel screenshot diff (PLAN.md's original Phase 1 acceptance
criterion) -- that needs a browser; this compares the actual HTML
Jinja emits against the corresponding `.page` block in the mockup,
which catches every markup/attribute/text regression a screenshot
diff would and doesn't need Playwright installed. Differences accepted
as intentional, not bugs:

- `&` vs `&amp;` in two titles: both parse to the same DOM text node;
  the data model stores plain text and doesn't HTML-escape (nothing
  else in the pipeline does either -- see render.py's docstring).
- The mockup tags Huge-Fish Predators as "Page ★" for its own preview
  framing ("Largest Group in the Book"); the real index uses the
  fish's actual tier letter ("Page D"), which is what generalizes once
  Phase 2 adds real page numbers.
- The book adds a full-map overview page up front and moves the index
  to right after it (the mockup, being a preview of 5 sample pages,
  has neither); index rows are `<a href="#group-...">` instead of
  `<div>` so the index is clickable, which the mockup never needed to
  be for a static 5-page preview.
- The index's page tag shows the destination group's title ("Silo
  Depths I") instead of a tier letter ("Page B") -- more useful once
  the tag is also the link text for a clickable row. The tag's
  *content* is intentionally different; this test still checks that
  every fish, size grouping, and marker color matches.
- Portraits: a fish with a downloaded wiki picture (packages/wiki)
  renders an `<img>` instead of the mockup's procedural `art.fish()`
  SVG -- real art beats a placeholder. Picture markup is blanked out
  before comparing so everything *around* the portrait (name, stats,
  gear, colors, layout) still gets checked exactly.
"""

from __future__ import annotations

import re
from pathlib import Path

from fishguide import render

REPO_ROOT = Path(__file__).resolve().parents[3]
MOCKUP = REPO_ROOT / "reference" / "design_preview.html"


def _pages(html: str) -> list[str]:
    """Top-level `<div class="page" ...>...</div>` blocks, matched by
    tag-depth so nested divs inside a page don't close it early."""
    pages = []
    tag_re = re.compile(r"<div\b|</div>")
    for m in re.finditer(r'<div class="page"[^>]*>', html):
        depth = 0
        for tm in tag_re.finditer(html, m.start()):
            depth += 1 if tm.group() != "</div>" else -1
            if depth == 0:
                pages.append(html[m.start() : tm.end()])
                break
    return pages


def _normalize(html: str) -> str:
    html = html.replace("&amp;", "&").replace("★", "D")
    # Each group's own page carries a `id="group-..."` anchor the
    # mockup has no reason to -- it's a single 5-page preview, not a
    # book with an index that jumps to sections.
    html = re.sub(r'<div class="page" id="group-[^"]*">', '<div class="page">', html)
    # The index's clickable <a class="index-row" href="#..."> is the
    # only anchor tag anywhere in the book -- fold it back to the
    # mockup's plain <div> so the row's *content* still gets compared.
    html = re.sub(r'<a class="index-row" href="[^"]*"', '<div class="index-row"', html)
    html = html.replace("</a>", "</div>")
    # Tag text is title-vs-tier-letter by design (see module docstring);
    # blank it out so the rest of the row still gets compared exactly.
    html = re.sub(r'(<div class="index-page-tag">)[^<]*(</div>)', r"\1\2", html)
    # Portrait markup (procedural SVG vs a real wiki <img>) is exactly
    # as different by design; neither has a nested </div> inside it.
    html = re.sub(r'(<div class="fish-pic"[^>]*>).*?(</div>)', r"\1PIC\2", html)
    html = re.sub(r'(<div class="index-thumb">).*?(</div>)', r"\1PIC\2", html)
    html = re.sub(r">\s+<", "><", html)
    return re.sub(r"\s+", " ", html).strip()


def test_matches_approved_mockup():
    """Book page order is [overview, index, ...groups]; the mockup's is
    [...groups, index] with no overview at all. Compare the index and
    the group pages against their mockup counterparts independently of
    where each one sits in the page list."""
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
    assert len(mockup_pages) == 7
    assert len(book_pages) == 8

    overview, index_page, *group_pages = book_pages
    mockup_group_pages, mockup_index_page = mockup_pages[:-1], mockup_pages[-1]

    assert "<h2>The World</h2>" in overview
    assert 'viewBox="0 0 1450 251"' in overview
    assert index_page == mockup_index_page

    for i, (mock, book) in enumerate(zip(mockup_group_pages, group_pages, strict=True)):
        assert book == mock, f"group page {i} does not match the approved mockup"
