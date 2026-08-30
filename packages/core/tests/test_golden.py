"""Whitespace-normalized diff of the rendered book's 5 original demo
group pages against the approved mockup (reference/design_preview.html),
page for page. The book now has the full 178-fish roster (Phase 3), so
this only checks the pages the mockup actually has an opinion about --
everything else (the other 59 groups, the overview page, the full
index) is unreviewed new content this test doesn't touch.

Not a pixel screenshot diff (PLAN.md's original Phase 1 acceptance
criterion) -- that needs a browser; this compares the actual HTML
Jinja emits against the corresponding `.page` block in the mockup,
which catches every markup/attribute/text regression a screenshot
diff would and doesn't need Playwright installed. Differences accepted
as intentional, not bugs:

- `&` vs `&amp;` in two titles: both parse to the same DOM text node;
  the data model stores plain text and doesn't HTML-escape (nothing
  else in the pipeline does either -- see render.py's docstring).
- Every group's own page now carries a `id="group-..."` anchor (so the
  index can link to it) that the mockup has no reason to have.
- Portraits: a fish with a downloaded wiki picture (packages/wiki)
  renders an `<img>` instead of the mockup's procedural `art.fish()`
  SVG -- real art beats a placeholder. Picture markup is blanked out
  before comparing so everything *around* the portrait (name, stats,
  gear, colors, layout) still gets checked exactly.
- Marker colors: the mockup cycles fish through a 7-color palette per
  group; the book uses one fixed red for every fish (numbered pins do
  the disambiguation the color cycle used to). All 6-hex-digit colors
  in `stroke=`/`border-left-color:` are blanked out before comparing
  for the same reason the portrait markup is -- deliberately different
  content, not a regression in anything structural around it.
- The little colored "X" beside a duo-card's fish name (`legend_x`)
  was a legend matching it to its map marker's color; moot once every
  marker became the same fixed red, so it was removed entirely.
- Map markers are the fish's own picture now, not a red X. Both sides
  collapse to a MARK placeholder so everything else on the map -- the
  dashed lure path, the numbered pins, the crop -- still compares
  exactly.
- The 4.5% inset that hides the map art's ragged edges moved out of a
  CSS transform and into the viewBox, so the numbers in that attribute
  differ from the mockup's while the picture is the same. Blanked on
  both sides.
- Every map is now the same live world map pointed at the group, not a
  flat crop: it uses one shared layer of every fish in the book and
  redraws the group's own fish on top with a ring. The shared layer,
  the rings and the control bar are stripped before comparing, leaving
  one marker per group fish -- exactly what the mockup drew.
- The mockup no longer governs map geometry at all. Marker, pin, path
  and start-dot coordinates are collapsed on both sides; what the mockup
  still proves is how many there are, their pin numbers and order, and
  all the text and layout around them. `terrain_fit` now snaps every marker onto water and reroutes
  every path around land before anything is drawn, so where the traced
  mockup put a marker on a rock, the generator moves it. Affected here:
  `d_huge_fish_predators` (below), Treat by one unit, Underfin's marker,
  and Trick & Treat's lure path, whose mockup `d` was rebased to the
  routed line.
- `d_huge_fish_predators` is the one group whose marker coordinates the
  mockup no longer governs. Five of its seven fish were traced onto the
  land mass (Maw 83 map units inland), which `check_fish_in_water` was
  built to catch and which an `on_land: true` flag was wrongly used to
  silence. They were moved into the open water their own descriptions
  call for and the mockup's pin coordinates for this page were updated
  to match, so the rest of the page still compares byte-for-byte.
- Every group map gained a context strip above it (the whole world with
  this page's slice marked). Stripped before comparing: a 5-page
  mockup preview had no reason to orient the reader.
- Every group page now ends with a "back to top" link (`#top`, back to
  the very start of the document) the mockup has no reason to have.
- The map's caption bar (`.cap`, bottom of the frame) is gone -- it
  covered terrain labels on some Phase 3 crops and mostly repeated the
  group's own title/cast text. Blanked out on both sides.
- Equipment icons that the game itself draws unambiguously (Sinker,
  Flick, etc. -- see render.py's ICON_MAP) now render as the real game
  art instead of a generic emoji; b_silo_depths_i, c_underfin,
  d_dragon_area_the_empty, and d_huge_fish_predators use `⚓`/`🎣` in
  gear/stats and so are affected (a_trick_and_treat's own "Flick
  attachment" line uses `🪝`, which isn't one of the five ICON_MAP
  covers, so it's untouched). Both the mockup's bare emoji and the
  book's `<img class="game-icon">` collapse to an ICON placeholder
  before comparing, since the point being checked here is the
  surrounding text/layout, not which of the two renders the equipment
  picture.

The index itself is no longer byte-compared against the mockup's
19-fish preview at all (see test_matches_approved_mockup) -- only
checked for being internally sane (right total, a known fish present).
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
    html = html.replace("&amp;", "&")
    # Each group's own page carries a `id="group-..."` anchor the
    # mockup has no reason to -- it's a single 5-page preview, not a
    # book with an index that jumps to sections.
    html = re.sub(r'<div class="page" id="group-[^"]*">', '<div class="page">', html)
    # Duo/feature map-frames now get an explicit inline aspect-ratio
    # (computed from the group's own view_box, like cluster layout
    # already did) instead of relying on a fixed CSS class value that
    # only happened to match Trick & Treat's/Underfin's own crops --
    # a real bug an early Phase 3 group (a mismatched aspect ratio
    # crops the map via preserveAspectRatio="slice") exposed. A no-op
    # for these two mockup groups, but still a byte-level attribute
    # difference.
    html = re.sub(r'<div class="map-frame" style="[^"]*">', '<div class="map-frame">', html)
    # The map's little caption bar covered terrain labels at the bottom
    # of some Phase 3 crops (it's `position:absolute; bottom:0`) and
    # was mostly redundant with the group's own title/cast text anyway
    # -- removed everywhere, including from these two mockup pages.
    html = re.sub(r'<div class="cap">[^<]*</div>', "", html)
    # Equipment icons the game itself draws unambiguously (see module
    # docstring) now render as the real game art, not a generic emoji.
    # Both sides collapse to an ICON placeholder -- the mockup's bare
    # emoji and the book's <img class="game-icon"> alike -- since this
    # test cares about the surrounding text/layout, not which of the
    # two renders the equipment picture.
    html = re.sub(r'<img class="game-icon"[^>]*>', "ICON", html)
    html = html.replace("⚓", "ICON").replace("🎣", "ICON")
    # Portrait markup (procedural SVG vs a real wiki <img>) is exactly
    # as different by design; neither has a nested </div> inside it.
    html = re.sub(r'(<div class="fish-pic"[^>]*>).*?(</div>)', r"\1PIC\2", html)
    html = re.sub(r'(<div class="index-thumb">).*?(</div>)', r"\1PIC\2", html)
    # Every group map now carries a context strip above it -- the whole
    # world with this page's slice marked, so a reader can see where
    # the crop sits without scrolling back to the overview. The mockup
    # is a 5-page preview with no such need.
    html = re.sub(r'<div class="ctx">.*?</div>', "", html)
    # The 4.5% inset that hides the map art's ragged edges moved from a
    # CSS transform on the <svg> into the viewBox itself: a CSS transform
    # is not reliably reflected in getScreenCTM() across browsers, and
    # every tap on a map is resolved through that matrix. Same picture,
    # different numbers in the attribute.
    html = re.sub(
        r'<svg class="map-crop" viewBox="[^"]*"', '<svg class="map-crop" viewBox="VB"', html
    )
    # Every map is the same live world map now, pointed at this group:
    # it draws one shared layer holding every fish in the book, then
    # redraws this group's own fish on top of it with a ring. The mockup
    # drew only the group's fish. The shared layer and the rings are
    # stripped; what's left on the book side is one marker per fish in
    # the group, which is what the mockup has too.
    html = html.replace('<use href="#allFish"/>', "")
    html = re.sub(r'<circle class="own-ring"[^>]*/>', "", html)
    html = re.sub(r'<g class="own">(.*?)</g>\s*</svg>', r"\1</svg>", html, flags=re.S)
    # Each map gained a control bar (drag/zoom/full screen) the mockup,
    # a set of flat pictures, had no reason to carry.
    html = re.sub(r'<div class="map-bar">.*?</div>\s*</div>', "</div>", html, flags=re.S)
    # Map geometry -- marker positions, pin positions, the lure path, the
    # start dot -- is no longer the mockup's to decide. terrain_fit moves
    # every marker onto open water with clearance and reroutes every path
    # around land, and validate.py then proves the result. Those checks
    # are strictly stronger than byte-matching a hand-traced mockup, so
    # coordinates are collapsed here while the things the mockup is still
    # authoritative for -- how many markers, which pin numbers, in what
    # order, and every bit of text and layout around them -- keep
    # comparing exactly.
    html = re.sub(
        r'<g><circle cx="[\d.]+" cy="[\d.]+" r="6.8"[^>]*/>'
        r"<text[^>]*>(\d+)</text></g>",
        r"PIN(\1)",
        html,
    )
    html = re.sub(r'<circle cx="[\d.]+" cy="[\d.]+" r="6.5"[^>]*/>', "DOT", html)
    html = re.sub(r'<path d="M [^"]+"', '<path d="PATH"', html)
    # Map markers are the fish's own picture now, not a red X -- an X
    # told you a fish was here, its picture tells you which one. Both
    # sides collapse to a MARK placeholder so the rest of the map
    # (dashed path, numbered pins, crop) still compares exactly.
    html = re.sub(r'<g class="fish-x">.*?</g>', "MARK", html)
    html = re.sub(r'<g class="fish-marker"[^>]*>.*?</g>', "MARK", html)
    # Marker color is uniform-red-by-design now, not per-fish/per-group
    # (see module docstring); neutralize every hex color so the two
    # schemes don't fail the comparison for reasons that aren't bugs.
    html = re.sub(r'stroke="#[0-9a-fA-F]{6}"', 'stroke="#COLOR"', html)
    html = re.sub(r"border-left-color:#[0-9a-fA-F]{6}", "border-left-color:#COLOR", html)
    # The little colored "X" beside a duo-card's name was a legend
    # matching it to its map marker's color -- moot now that every
    # marker is the same fixed red, so it was removed. Strip it from
    # the mockup side (the book never emits it anymore).
    html = re.sub(r'<svg class="duo-x"[^>]*>.*?</svg>', "", html)
    # Every group page now ends with a "back to top" link the mockup
    # has no reason to have (a 5-page preview needs no such nav).
    # Feature layout wraps it to span both grid columns; strip both.
    html = re.sub(r'<div class="back-to-top">.*?</div>', "", html)
    html = re.sub(r'<div style="grid-column:1/-1;"></div>', "", html)
    html = re.sub(r"\s+</svg>", "</svg>", html)
    html = re.sub(r">\s+<", "><", html)
    return re.sub(r"\s+", " ", html).strip()


def test_matches_approved_mockup():
    """The book now has the full 178-fish roster (Phase 3), not just the
    5 demo groups the mockup shows -- so instead of assuming a fixed
    total page count, find each of those 5 groups' pages (plus the
    overview and index) by their known `id="group-..."` anchors and
    compare only those against the mockup's corresponding pages."""
    mockup_pages = [_normalize(p) for p in _pages(MOCKUP.read_text())]
    assert len(mockup_pages) == 7
    mockup_group_pages = mockup_pages[:-1]

    raw_pages = _pages(
        render.build_book(
            data_dir=REPO_ROOT / "data",
            templates_dir=REPO_ROOT / "templates",
            assets_dir=REPO_ROOT / "assets",
        )
    )
    book_pages = [_normalize(p) for p in raw_pages]

    overview = book_pages[0]
    assert "<h2>The World</h2>" in overview
    # The overview shows the whole world, inset by the same 4.5% every
    # other crop is (see crop_view_box); check the real attribute on the
    # un-normalized page, since _normalize blanks viewBox.
    assert f'viewBox="{render.crop_view_box(render.FULL_MAP_VIEW_BOX)}"' in raw_pages[0]

    # The index now covers the full 203-fish roster (178 from Phase 3
    # plus 25 the community guide named that never made it into data/),
    # not the mockup's 19-fish preview -- byte-equality against it
    # stopped meaning anything once real content superseded the demo.
    # Check the index is internally sane instead of matching frozen
    # content.
    index_page = next(p for p in book_pages if "<h2>Fish Index</h2>" in p)
    assert "203 of 203 Entries Shown" in index_page
    assert index_page.count('class="index-row"') == 203
    assert "Bitterfish" in index_page and "Silo Depths I" in index_page

    demo_group_ids = [
        "a_trick_and_treat",
        "b_silo_depths_i",
        "c_underfin",
        "d_dragon_area_the_empty",
        "d_huge_fish_predators",
    ]
    demo_pages = []
    for gid in demo_group_ids:
        i = next(i for i, p in enumerate(book_pages) if f'id="group-{gid}"' in raw_pages[i])
        demo_pages.append(book_pages[i])
        if gid == "d_huge_fish_predators":
            # Its continuation page carries no id -- it's the very next
            # page in document order, right before d_dragon's successor.
            demo_pages.append(book_pages[i + 1])

    for i, (mock, book) in enumerate(zip(mockup_group_pages, demo_pages, strict=True)):
        assert book == mock, f"group page {i} does not match the approved mockup"
