"""Pulls map geometry onto open water before anything is drawn.

validate.py can only say "this marker is on a rock"; by then the fix is
a hand edit, and the escape hatches (`Fish.on_land`,
`Group.path_crosses_land_ok`) make it far too easy to silence the
complaint instead of moving the marker -- which is exactly what
happened to Underfin and to five of the Huge-Fish Predators. So the
generator now corrects the geometry itself: every fish coordinate is
snapped to the nearest open water, and every lure path that would cross
land is rerouted around it, before validate_all() ever sees the data.

This module owns that correction and nothing else. It never changes
what a fish *is* -- only where its marker sits -- and it reports every
change it makes so a build is auditable rather than quietly rewritten.
`Fish.on_land` still opts a fish out, for a spot that is genuinely on
terrain by game design (a fish resting on the sea floor); it is not a
way to keep a mistake.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from . import terrain, validate
from .models import Group


@dataclass(frozen=True)
class Correction:
    group_id: str
    what: str
    detail: str

    def __str__(self) -> str:
        return f"{self.group_id}: {self.what} {self.detail}"


MIN_MARKER_GAP = 10.0
"""How far apart two markers' centres must be. Markers are ~18 map units
across, so this still lets them overlap and read as a shoal; it only
stops one being hidden underneath another, which also makes it
untappable."""


def _fit_fish(
    group: Group, mask_path: Path, taken: list[tuple[float, float]], slot: int
) -> tuple[list[Correction], int]:
    vx, _vy, vw, _vh = (float(v) for v in group.view_box.split())
    bounds = (
        vx + validate.X_MARGIN,
        vx + vw - validate.X_MARGIN,
        float(validate.Y_MIN),
        float(validate.Y_MAX),
    )
    out = []
    for f in group.fish:
        if f.on_land:
            slot += len(f.coords)
            continue
        for i, (x, y) in enumerate(list(f.coords)):
            # Clearance, not just "is this pixel water" -- see
            # terrain.nearest_open_water. A marker already sitting in
            # open water is left exactly where the author put it.
            # Exclude this marker's own slot, not every marker that
            # happens to share its coordinates -- two fish stacked on one
            # point must each still see the other, or neither moves.
            others = tuple(taken[:slot] + taken[slot + 1 :])
            nx, ny = terrain.nearest_open_water(
                x, y, mask_path=mask_path, bounds=bounds, avoid=others, min_gap=MIN_MARKER_GAP
            )
            if (nx, ny) == (x, y):
                slot += 1
                continue
            taken[slot] = (nx, ny)
            slot += 1
            f.coords[i] = (nx, ny)
            if not terrain.is_water(x, y, mask_path):
                why = "was on terrain"
            elif any(math.hypot(x - ax, y - ay) < MIN_MARKER_GAP for ax, ay in others):
                why = "was under another marker"
            else:
                why = "was too close to terrain"
            out.append(
                Correction(group.id, f"moved {f.key!r}", f"({x},{y}) -> ({nx:g},{ny:g}), {why}")
            )
    return out, slot


def _connected(a: tuple[float, float], b: tuple[float, float], mask_path: Path) -> bool:
    """Whether two points sit on the same body of water. A cave pocket
    sealed off by rock is a different body from the open sea, and no
    amount of pathfinding will join them -- worth saying so plainly
    rather than reporting a generic routing failure."""
    from collections import deque

    m = terrain._mask(mask_path)
    px = m.load()
    sx, sy = (int(v) for v in terrain.nearest_water(*a, mask_path=mask_path))
    gx, gy = (int(v) for v in terrain.nearest_water(*b, mask_path=mask_path))
    seen = {(sx, sy)}
    dq = deque([(sx, sy)])
    while dq:
        x, y = dq.popleft()
        if (x, y) == (gx, gy):
            return True
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if (
                0 <= nx < m.width
                and 0 <= ny < m.height
                and (nx, ny) not in seen
                and px[nx, ny] != 0
            ):
                seen.add((nx, ny))
                dq.append((nx, ny))
    return False


def _fit_path(group: Group, mask_path: Path) -> list[Correction]:
    if not group.path or group.path_crosses_land_ok:
        return []
    pts = group.path.points
    crossing = [
        i
        for i in range(len(pts) - 1)
        if not terrain.segment_in_water(pts[i], pts[i + 1], mask_path=mask_path)
    ]
    if not crossing:
        return []
    # Reroute the whole polyline rather than segment by segment: a
    # detour around one obstacle usually moves the waypoints either side
    # of it too, and stitching per-segment routes together tends to
    # double back on itself.
    # Coarse first, then finer. A 6-unit grid is cheap and handles open
    # water, but it cannot thread a channel narrower than its own step --
    # the corridor along the top of the map is one -- so a failure at one
    # resolution says nothing about whether a route exists at all.
    routed = None
    for step in (6, 3, 2):
        try:
            routed = terrain.find_water_route(pts[0], pts[-1], grid_step=step, mask_path=mask_path)
            break
        except ValueError:
            continue
    if routed is None:
        why = (
            "endpoints are in water bodies that don't connect"
            if not _connected(pts[0], pts[-1], mask_path)
            else "no route found even at the finest grid"
        )
        return [
            Correction(
                group.id,
                "could not reroute path",
                f"{why} -- set path_crosses_land_ok if the crossing is deliberate",
            )
        ]
    group.path.points = routed
    return [
        Correction(
            group.id,
            "rerouted path",
            f"{len(pts)} points -> {len(routed)}, was crossing land at segment(s) "
            + ", ".join(str(i) for i in crossing),
        )
    ]


def fit_groups(groups: list[Group], assets_dir: Path = Path("assets")) -> list[Correction]:
    """Snap every marker onto water and route every path around land.
    Returns what it changed, in the order it changed it."""
    mask_path = assets_dir / "water_mask.png"
    # Separation is global: two fish from different groups land on the
    # same world map, so they have to clear each other too.
    taken = [(x, y) for g in groups for f in g.fish for x, y in f.coords]
    out: list[Correction] = []
    slot = 0
    for g in groups:
        fixed, slot = _fit_fish(g, mask_path, taken, slot)
        out += fixed
        out += _fit_path(g, mask_path)
    return out
