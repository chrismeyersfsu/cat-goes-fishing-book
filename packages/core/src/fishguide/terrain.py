"""Checks a map coordinate or lure path against the map's actual
terrain art -- not just the abstract safe-area box validate.py already
enforces, but whether a point is really open water, or sits on land,
reef structure, or a cave wall a fish/path has no business being drawn
over.

Backed by assets/water_mask.png, a static 1568x251 1-bit render of
map_terrain_defs.html (see assets/build_water_mask.py to regenerate it
if the terrain art ever changes). Loading a pre-rendered image keeps
this fast and browser-free at check time -- fishguide itself never
launches Chromium to validate data, only to build the PDF.
"""

from __future__ import annotations

import math
from functools import lru_cache
from itertools import pairwise
from pathlib import Path

from PIL import Image

WATER_MASK_PATH = Path("assets/water_mask.png")

# Mirrors validate.py's Y_MIN/Y_MAX (not imported from there to avoid a
# circular import) -- a path the pathfinder finds must itself respect
# the safe-area y-bound, or a later validate_all() run just rejects a
# route this module was supposed to have already fixed.
SAFE_Y_MIN, SAFE_Y_MAX = 18, 225

# A lure path is a 2px line, not a 26-unit marker, so it can run much
# closer to the frame edge without being clipped. Holding it to the
# marker bound cuts the map's water into pieces that don't connect --
# Glacier & Magmer's route is only blocked by that, not by terrain.
PATH_Y_MIN, PATH_Y_MAX = 6, 245


@lru_cache(maxsize=1)
def _mask(path: Path) -> Image.Image:
    return Image.open(path).convert("1")


def is_water(x: float, y: float, mask_path: Path = WATER_MASK_PATH) -> bool:
    m = _mask(mask_path)
    xi, yi = round(x), round(y)
    if not (0 <= xi < m.width and 0 <= yi < m.height):
        return False
    return m.getpixel((xi, yi)) != 0


def segment_in_water(
    p1: tuple[float, float],
    p2: tuple[float, float],
    step: float = 1.0,
    mask_path: Path = WATER_MASK_PATH,
) -> bool:
    """Whether every point sampled along the straight line p1->p2 (at
    roughly `step` map units apart) is water. A dashed lure path is
    drawn as a straight line between waypoints, so this is exactly
    what a reader would see cross land."""
    (x1, y1), (x2, y2) = p1, p2
    dist = math.hypot(x2 - x1, y2 - y1)
    n = max(1, int(dist / step))
    for i in range(n + 1):
        t = i / n
        if not is_water(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, mask_path):
            return False
    return True


# (label text, x-center, estimated half-width) for every static terrain
# label baked into map_terrain_defs.html, in the map's 1568x251 space.
# text-anchor is "middle" for all of them; half-widths are estimated
# from font-size * char-count (the map's own font, Trebuchet-family,
# averages ~0.55px per unit of font-size per character) since the
# labels are baked into the art, not real DOM text this could measure.
# Good enough to catch a word truncated at a crop edge, not pixel-exact.
TERRAIN_LABELS: list[tuple[str, float, float]] = [
    ("Open Ocean", 195, 45),
    ("Reef", 258, 15),
    ("Caves", 205, 20),
    ("Basin", 330, 20),
    ("Reef", 412, 15),
    ("Dragon Area", 573, 52),
    ("The Empty", 490, 30),
    ("Channel", 592, 19),
    ("Con's Place", 590, 30),
    ("Surface/Silo/Area", 705, 32),
    ("SILO", 700, 31),
    ("Very Distant Sea", 1010, 82),
    ("Plateau", 965, 34),
    ("Plateau Caves", 960, 35),
    ("King's Cave", 1032, 30),
    ("Kelp", 1155, 19),
    ("Furthest/distance/tech boat/can go", 1352, 33),
    ("Labyrinth/Caves", 1362, 33),
]


def nearest_water(
    x: float, y: float, max_radius: int = 60, mask_path: Path = WATER_MASK_PATH
) -> tuple[float, float]:
    """The closest point to (x, y) that's open water, searched in
    expanding square rings. For nudging a fish coordinate that landed
    on terrain to the nearest legitimate water spot, not for finding
    the "right" spot narratively -- a human should sanity-check the
    result still makes sense for that fish."""
    if is_water(x, y, mask_path):
        return (x, y)
    best: tuple[float, float] | None = None
    best_d = None
    for r in range(1, max_radius + 1):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if max(abs(dx), abs(dy)) != r:
                    continue
                px, py = x + dx, y + dy
                if is_water(px, py, mask_path):
                    d = dx * dx + dy * dy
                    if best_d is None or d < best_d:
                        best_d, best = d, (float(px), float(py))
        if best is not None:
            return best
    raise ValueError(f"no water found within {max_radius} units of ({x}, {y})")


def nearest_open_water(
    x: float,
    y: float,
    clearance: float = 8,
    max_radius: int = 60,
    mask_path: Path = WATER_MASK_PATH,
    bounds: tuple[float, float, float, float] | None = None,
) -> tuple[float, float]:
    """Like nearest_water, but insists the point have `clearance` units
    of water all around it. A marker centred on a one-pixel seam at the
    edge of a rock passes an is_water() check and still reads, to a
    reader, as sitting on the rock -- the picture drawn there is ~26
    units wide. Falls back to progressively tighter clearances so a
    genuinely narrow cave pocket still gets the best spot available."""

    def clear(cx: float, cy: float, r: float) -> bool:
        # A spot outside the marker safe area is no use however open the
        # water is -- it would just render clipped or off the crop.
        if bounds is not None:
            x_lo, x_hi, y_lo, y_hi = bounds
            if not (x_lo <= cx <= x_hi and y_lo <= cy <= y_hi):
                return False
        if r <= 0:
            return is_water(cx, cy, mask_path)
        steps = 8
        for i in range(steps):
            a = 2 * math.pi * i / steps
            if not is_water(cx + math.cos(a) * r, cy + math.sin(a) * r, mask_path):
                return False
        return is_water(cx, cy, mask_path)

    for r in (clearance, clearance * 0.6, clearance * 0.35, 0):
        if clear(x, y, r):
            return (x, y)
        for ring in range(1, max_radius + 1):
            best = None
            for dx in range(-ring, ring + 1):
                for dy in range(-ring, ring + 1):
                    if max(abs(dx), abs(dy)) != ring:
                        continue
                    px, py = x + dx, y + dy
                    if clear(px, py, r):
                        d = dx * dx + dy * dy
                        if best is None or d < best[0]:
                            best = (d, (float(px), float(py)))
            if best:
                return best[1]
    raise ValueError(f"no open water within {max_radius} units of ({x}, {y})")


def find_water_route(
    p1: tuple[float, float],
    p2: tuple[float, float],
    grid_step: float = 6,
    mask_path: Path = WATER_MASK_PATH,
) -> list[tuple[float, float]]:
    """A polyline from p1 to p2 that stays in open water -- for
    rerouting a lure path currently drawn straight across land. Finds
    a shortest path over an 8-connected water grid (Dijkstra,
    `grid_step` map units apart), then collapses it to the fewest
    waypoints whose straight segments still stay entirely in water
    (same "string pulling" idea as navmesh path simplification), so
    the result is short enough to hand to markers.dashed_path."""
    import heapq

    m = _mask(mask_path)
    w = m.width

    def snap(p: tuple[float, float]) -> tuple[float, float]:
        """The nearest grid-aligned cell that is itself water. Rounding a
        water point to the grid can land it on a rock, and a search that
        starts on a rock never gets going -- every edge out of it fails
        the segment check."""
        x, y = p if is_water(*p, mask_path) else nearest_water(*p, mask_path=mask_path)
        gx, gy = round(x / grid_step) * grid_step, round(y / grid_step) * grid_step
        if is_water(gx, gy, mask_path) and PATH_Y_MIN <= gy <= PATH_Y_MAX:
            return (gx, gy)
        for r in range(1, 12):
            best = None
            for ix in range(-r, r + 1):
                for iy in range(-r, r + 1):
                    if max(abs(ix), abs(iy)) != r:
                        continue
                    cx, cy = gx + ix * grid_step, gy + iy * grid_step
                    if not (PATH_Y_MIN <= cy <= PATH_Y_MAX and is_water(cx, cy, mask_path)):
                        continue
                    d = (cx - x) ** 2 + (cy - y) ** 2
                    if best is None or d < best[0]:
                        best = (d, (cx, cy))
            if best:
                return best[1]
        raise ValueError(f"no grid-aligned water cell near {p}")

    # Route between points that are actually in water: an endpoint left
    # on land makes the first or last segment cross it no matter how good
    # the middle of the route is.
    end1 = p1 if is_water(*p1, mask_path) else nearest_water(*p1, mask_path=mask_path)
    end2 = p2 if is_water(*p2, mask_path) else nearest_water(*p2, mask_path=mask_path)
    start, goal = snap(p1), snap(p2)

    def neighbors(node: tuple[float, float]):
        x, y = node
        for dx in (-grid_step, 0, grid_step):
            for dy in (-grid_step, 0, grid_step):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if not (
                    0 <= nx < w and PATH_Y_MIN <= ny <= PATH_Y_MAX and is_water(nx, ny, mask_path)
                ):
                    continue
                # Two water cells a whole grid step apart can still have
                # land between them, and dashed_path draws the straight
                # line, not the grid. Check the line itself -- that is the
                # thing a reader sees cross a rock.
                if not segment_in_water((x, y), (nx, ny), mask_path=mask_path):
                    continue
                yield (nx, ny), math.hypot(dx, dy)

    dist: dict[tuple[float, float], float] = {start: 0.0}
    prev: dict[tuple[float, float], tuple[float, float]] = {}
    pq: list[tuple[float, tuple[float, float]]] = [(0.0, start)]
    visited: set[tuple[float, float]] = set()
    while pq:
        d, node = heapq.heappop(pq)
        if node in visited:
            continue
        visited.add(node)
        if node == goal:
            break
        for nb, cost in neighbors(node):
            nd = d + cost
            if nb not in dist or nd < dist[nb]:
                dist[nb] = nd
                prev[nb] = node
                heapq.heappush(pq, (nd, nb))

    if goal != start and goal not in prev:
        raise ValueError(f"no water route found from {p1} to {p2}")

    grid_path = [goal]
    while grid_path[-1] != start:
        grid_path.append(prev[grid_path[-1]])
    grid_path.reverse()
    full_path = [end1, *grid_path, end2]

    simplified = [full_path[0]]
    i = 0
    while i < len(full_path) - 1:
        j = len(full_path) - 1
        while j > i + 1 and not segment_in_water(full_path[i], full_path[j], mask_path=mask_path):
            j -= 1
        simplified.append(full_path[j])
        i = j

    # Never hand back a route that isn't actually all water. The
    # simplifier can be forced to accept a bad i->i+1 hop (there is
    # nothing shorter to fall back to), and the snapped endpoints can sit
    # across a rock from the nearest grid cell. A caller that asked for a
    # water route would otherwise get a land crossing and no warning --
    # which is the whole failure this module exists to prevent.
    for a, b in pairwise(simplified):
        if not segment_in_water(a, b, mask_path=mask_path):
            raise ValueError(f"no all-water route from {p1} to {p2} at grid_step={grid_step}")
    return simplified


def partially_cropped_labels(view_box: str) -> list[tuple[str, float, float]]:
    """Terrain labels whose span straddles a view_box edge -- neither
    fully shown nor fully hidden, so a reader sees a word cut in half."""
    vx, _vy, w, _h = (float(v) for v in view_box.split())
    v_end = vx + w
    out = []
    for name, cx, hw in TERRAIN_LABELS:
        lo, hi = cx - hw, cx + hw
        if hi <= vx or lo >= v_end:  # touching but not overlapping counts as fully outside
            continue
        if not (lo >= vx and hi <= v_end):
            out.append((name, lo, hi))
    return out
