"""Regenerates the five equipment icon PNGs from the Cat Goes Fishing
wiki. Run this again only if the wiki's copies of these five icons
change, or a sixth unambiguous one shows up worth adding -- render.py
loads the committed PNGs at build time and never touches the network.
Needs `pillow` (already a project dependency, and the one that makes
this script work at all -- see below) plus network access; nothing the
main package doesn't already have otherwise.

The wiki's upgrade icons are the only equipment art in the game that's
unambiguous and reusable (one picture per item, not per fish-encounter
variant) -- see render.py's ICON_MAP for which emoji each one replaces
and why the rest stay emoji. Despite the `.jpg` extension in their
URLs, Fandom actually serves these as WebP; Pillow decodes that fine,
a plain `Image.open` on the response bytes is enough.

Each source image is a 38x37 sprite: a white glyph on a solid
olive-brown square, with ~2px of antialiased cream border baked in
around the edge from the wiki's own thumbnailing (confirmed by eye and
by sampling corner pixels -- it's not part of the icon). This script
crops that border off, then keys the olive-brown fill to transparent
and recolors the white glyph to the book's ink color (`--ink` in
base.html.j2) by luminance: a pixel near the background's own
brightness becomes fully transparent, a pixel near white becomes fully
opaque ink, and the antialiased edge between glyph and fill blends
smoothly in between. Unrecolored, these render as bright olive tiles
that fight the page's parchment palette instead of sitting with the
surrounding badge/gear text -- see the CHANGELOG entry for this
feature for how that looked and why it was rejected.
"""

from __future__ import annotations

import io
import pathlib
import urllib.request

from PIL import Image

HERE = pathlib.Path(__file__).parent
USER_AGENT = "fishguide-art-fetch/0.1 (+https://github.com/chrismeyersfsu/cat-goes-fishing-book)"
INK = (0x17, 0x24, 0x1A)  # base.html.j2's --ink

# name -> wiki source URL.
SOURCES = {
    "sinker": "https://static.wikia.nocookie.net/cat-goes-fishing/images/4/4d/Upgrade_sinker.jpg/revision/latest?cb=20211221220105",
    "bomb_stack": "https://static.wikia.nocookie.net/cat-goes-fishing/images/c/c1/Upgrade_bomb_stack.jpg/revision/latest?cb=20211221220105",
    "detonator": "https://static.wikia.nocookie.net/cat-goes-fishing/images/6/64/Upgrade_detonator.jpg/revision/latest?cb=20211221220104",
    "diving_lure": "https://static.wikia.nocookie.net/cat-goes-fishing/images/6/60/Upgrade_diving_lure.jpg/revision/latest?cb=20211221220104",
    "flick": "https://static.wikia.nocookie.net/cat-goes-fishing/images/1/1a/Upgrade_flick.jpg/revision/latest?cb=20211221220104",
}

BORDER = 3  # px of antialiased cream margin to crop off each edge
BG_LUMA = 140  # at/below this: fully transparent (the olive fill)
GLYPH_LUMA = 225  # at/above this: fully opaque ink (the white glyph)


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def _recolor(im: Image.Image) -> Image.Image:
    """Crop the wiki thumbnail's border, then swap olive-square-plus-white-glyph
    for transparent-plus-ink-glyph, anti-aliasing intact."""
    im = im.convert("RGB")
    w, h = im.size
    im = im.crop((BORDER, BORDER, w - BORDER, h - BORDER))
    out = Image.new("RGBA", im.size)
    src, dst = im.load(), out.load()
    span = GLYPH_LUMA - BG_LUMA
    for y in range(im.height):
        for x in range(im.width):
            r, g, b = src[x, y]
            luma = 0.299 * r + 0.587 * g + 0.114 * b
            alpha = max(0.0, min(1.0, (luma - BG_LUMA) / span))
            dst[x, y] = (*INK, round(alpha * 255))
    return out


def main() -> None:
    for name, url in SOURCES.items():
        raw = _fetch(url)
        im = Image.open(io.BytesIO(raw))
        out_path = HERE / f"{name}.png"
        _recolor(im).save(out_path)
        print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
