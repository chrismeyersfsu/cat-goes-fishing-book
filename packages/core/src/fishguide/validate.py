"""Build-blocking checks against the fish/group data, independent of
rendering. Two of PLAN.md's validation rules aren't implemented yet
because they need a full 178-fish roster to mean anything (roster
totals reconciling with fish_grouping_scheme.md; index page-number
self-consistency, which needs paginate.py's numbering, not yet built)
-- both are Phase 3 concerns. A third, checking for duplicate marker
colors within a group, no longer applies: every fish shares the same
fixed marker color now (models.MARKER_COLOR), so "duplicate" is the
expected, correct state. What's here already catches the bug class
PLAN.md calls out by name (a marker rendering off the visible map
crop), plus (via terrain.py) whether a marker/path is actually drawn
over water rather than land, and whether a crop truncates a terrain
label -- both found by hand during a Phase 3 content review and worth
catching automatically for every fish added after."""

from __future__ import annotations

from pathlib import Path

from . import terrain
from .models import Group

Y_MIN, Y_MAX = 18, 225
X_MARGIN = 12


class ValidationError(Exception):
    pass


def _view_box(group: Group) -> tuple[float, float, float, float]:
    x, y, w, h = (float(v) for v in group.view_box.split())
    return x, y, w, h


def check_marker_safe_area(group: Group) -> list[str]:
    """Every marker/path point must clear the caption bar (y) and the
    `.map-crop` 1.045x scale-up (x), per PLAN.md -- this is the exact
    bug class that made Underfin's X render off-screen during design."""
    errors = []
    vx, _vy, vw, _vh = _view_box(group)
    x_lo, x_hi = vx + X_MARGIN, vx + vw - X_MARGIN

    def check_point(x: float, y: float, where: str) -> None:
        if not (Y_MIN <= y <= Y_MAX):
            errors.append(f"{group.id}: {where} y={y} outside [{Y_MIN}, {Y_MAX}]")
        if not (x_lo <= x <= x_hi):
            errors.append(f"{group.id}: {where} x={x} outside [{x_lo}, {x_hi}]")

    for f in group.fish:
        for i, (x, y) in enumerate(f.coords):
            check_point(x, y, f"fish {f.key!r} coords[{i}]")
    if group.path:
        for i, (x, y) in enumerate(group.path.points):
            check_point(x, y, f"path point[{i}]")
    return errors


def check_view_box_height(group: Group) -> list[str]:
    _x, _y, _w, h = _view_box(group)
    if h != 251:
        return [f"{group.id}: view_box height {h} != 251"]
    return []


def check_unique_fish(groups: list[Group]) -> list[str]:
    seen: dict[str, str] = {}
    errors = []
    for g in groups:
        for f in g.fish:
            if f.key in seen:
                errors.append(f"fish {f.key!r} appears in both {seen[f.key]!r} and {g.id!r}")
            else:
                seen[f.key] = g.id
    return errors


def check_portrait_shape(group: Group) -> list[str]:
    """`portrait` is optional (see render.make_fish_pic) -- a real wiki
    picture or the generic fallback covers a fish with none. Only
    flag a portrait dict someone started filling in but left broken."""
    return [
        f"{group.id}: fish {f.key!r} has a portrait dict but no body_color"
        for f in group.fish
        if f.portrait and "body_color" not in f.portrait
    ]


def check_fish_in_water(group: Group, mask_path: Path = terrain.WATER_MASK_PATH) -> list[str]:
    """A fish's coords should sit on open water, not land/reef/cave-wall
    art -- an X drawn on top of solid terrain reads as a placement
    mistake to a reader. Set `on_land: true` on a fish whose spot is
    genuinely on land/structure by game design (see models.Fish)."""
    errors = []
    for f in group.fish:
        if f.on_land:
            continue
        for i, (x, y) in enumerate(f.coords):
            if not terrain.is_water(x, y, mask_path):
                errors.append(
                    f"{group.id}: fish {f.key!r} coords[{i}]=({x},{y}) is not on open "
                    f"water -- set on_land: true if this is deliberate"
                )
    return errors


def check_path_in_water(group: Group, mask_path: Path = terrain.WATER_MASK_PATH) -> list[str]:
    """A dashed lure path is drawn as straight segments between
    waypoints -- if any segment cuts across land, the line visibly
    crosses solid ground on the rendered map."""
    if not group.path or group.path_crosses_land_ok:
        return []
    errors = []
    pts = group.path.points
    for i in range(len(pts) - 1):
        if not terrain.segment_in_water(pts[i], pts[i + 1], mask_path=mask_path):
            errors.append(f"{group.id}: path segment [{i}]->[{i + 1}] crosses land")
    return errors


def check_label_crop(group: Group) -> list[str]:
    """A view_box that clips a terrain label mid-word instead of fully
    showing or fully hiding it reads as broken cropping to a reader."""
    if group.label_crop_ok:
        return []
    cropped = terrain.partially_cropped_labels(group.view_box)
    return [
        f"{group.id}: view_box partially crops terrain label {name!r}" for name, _lo, _hi in cropped
    ]


def validate_all(groups: list[Group], assets_dir: Path = Path("assets")) -> list[str]:
    mask_path = assets_dir / "water_mask.png"
    errors = list(check_unique_fish(groups))
    for g in groups:
        errors += check_view_box_height(g)
        errors += check_marker_safe_area(g)
        errors += check_portrait_shape(g)
        errors += check_fish_in_water(g, mask_path)
        errors += check_path_in_water(g, mask_path)
        errors += check_label_crop(g)
    return errors


def validate_or_raise(groups: list[Group], assets_dir: Path = Path("assets")) -> None:
    errors = validate_all(groups, assets_dir)
    if errors:
        raise ValidationError("\n".join(errors))
