"""Regenerates water_mask.png from map_terrain_defs.html. Run this
again only if the terrain art itself changes -- fishguide.terrain
loads the committed PNG at runtime and never re-renders it, so this
script needs Playwright (`uv run --with playwright==1.62 python
assets/build_water_mask.py`) but the main package doesn't.

The mask is 1568x251 (the map's native coordinate space, 1:1), mode
"1": a pixel is white (water) if its rendered color is close to the
ocean background fill (2,76,0); anything else (land, reef structure,
cave walls) is black. fishguide.terrain.is_water() reads it directly.
"""

import pathlib

from playwright.sync_api import sync_playwright
from PIL import Image

HERE = pathlib.Path(__file__).parent
WATER_RGB = (2, 76, 0)
TOLERANCE = 40  # sum of abs channel differences


def render_terrain_png(out_path: pathlib.Path) -> None:
    html = (
        '<!DOCTYPE html><html><body style="margin:0">'
        '<svg width="1568" height="251" viewBox="0 0 1568 251">'
        + (HERE / "map_terrain_defs.html").read_text()
        + '<use href="#mapTerrain"/></svg></body></html>'
    )
    tmp = HERE / "_terrain_render.html"
    tmp.write_text(html)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1568, "height": 251})
            page.goto(tmp.resolve().as_uri())
            page.screenshot(path=str(out_path))
            browser.close()
    finally:
        tmp.unlink()


def build_mask(png_path: pathlib.Path) -> Image.Image:
    im = Image.open(png_path).convert("RGB")
    mask = Image.new("1", im.size)
    src, dst = im.load(), mask.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b = src[x, y]
            dist = abs(r - WATER_RGB[0]) + abs(g - WATER_RGB[1]) + abs(b - WATER_RGB[2])
            dst[x, y] = 255 if dist < TOLERANCE else 0
    return mask


if __name__ == "__main__":
    rendered = HERE / "_terrain_rendered.png"
    render_terrain_png(rendered)
    build_mask(rendered).save(HERE / "water_mask.png")
    rendered.unlink()
    print(f"wrote {HERE / 'water_mask.png'}")
