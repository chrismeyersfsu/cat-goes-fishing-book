"""Turns loaded Group/Fish data into book.html. Jinja templates hold
the structural HTML; every SVG fragment (portraits, markers, paths) is
built here in Python and handed to templates as pre-rendered strings,
so autoescaping is off throughout -- there's no untrusted input, only
our own YAML.
"""

from __future__ import annotations

import base64
from pathlib import Path

import jinja2

from . import art, layout, markers, paginate
from .models import SIZE_ORDER, Fish, Group

TEMPLATES_DIR = Path("templates")
ASSETS_DIR = Path("assets")

SIZE_LABELS = {
    "small": "Small Fish",
    "medium": "Medium Fish",
    "large": "Large Fish",
    "huge": "Huge Fish",
    "secret": "Secret Fish",
}
TOTAL_ROSTER = 178

# The world map's coordinate space runs to x=1568 (PLAN.md's data
# model comment; confirmed against assets/map_terrain_defs.html's own
# path bounds), but everything actually drawn -- including the
# "Furthest distance a tech boat can go" label past the boundary
# arrow -- ends by x~=1410. Past that is solid, undrawn ocean fill, so
# the overview page crops to 1450 instead of the full 1568 to cut that
# dead space (checked visually; see git history for the before/after).
FULL_MAP_VIEW_BOX = "0 0 1450 251"


def env(templates_dir: Path = TEMPLATES_DIR) -> jinja2.Environment:
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(templates_dir),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _picture_uri(key: str, assets_dir: Path) -> str | None:
    path = assets_dir / "wiki_fish" / f"{key}.png"
    if not path.exists():
        return None
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def make_fish_pic(assets_dir: Path = ASSETS_DIR):
    """A real wiki picture (see packages/wiki) beats the procedural
    portrait when one was downloaded for that fish -- embedded as a
    data URI so book.html stays a single self-contained file, same as
    the map defs. Falls back to art.fish() for the few fish the wiki
    had no picture for (e.g. Treat, Underfin, Maw)."""

    def fish_pic(f: Fish) -> str:
        uri = _picture_uri(f.key, assets_dir)
        if uri:
            return f'<img src="{uri}" alt="{f.name}" loading="lazy">'
        return art.fish(**f.portrait)

    return fish_pic


def legend_x(color: str) -> str:
    return markers.legend_x(color)


def _duo_map(group: Group) -> str:
    parts = [markers.dashed_path(group.path.points, group.path.start_gap, group.path.end_gap)]
    for f in group.fish:
        parts.append(markers.x_mark(*f.coords[0], color=f.color))
    return "".join(parts)


def _feature_map(group: Group) -> str:
    parts = []
    if group.path:
        parts.append(
            markers.dashed_path(group.path.points, group.path.start_gap, group.path.end_gap)
        )
        parts.append(markers.start_dot(*group.path.points[0]))
    f = group.fish[0]
    parts.append(markers.x_mark(*f.coords[0], color=f.color))
    return "".join(parts)


def _cluster_map(fish: list[Fish], start_index: int) -> str:
    parts = []
    for i, f in enumerate(fish, start=start_index):
        x, y = f.coords[0]
        parts.append(markers.small_x_mark(x, y, color=f.color))
        parts.append(markers.numbered_pin(x, y + f.pin_dy, i))
    return "".join(parts)


def _grid_class(cols: int, continuation: bool) -> str:
    # See layout.py's docstring: continuation pages are always the
    # 3-column style regardless of `cols`, per the one observed sample.
    if continuation:
        return "dex-grid entry-grid3"
    return "dex-grid cols4" if cols == 4 else "entry-grid3"


def _map_frame_style(group: Group) -> str:
    _x, _y, w, _h = (float(v) for v in group.view_box.split())
    style = f"aspect-ratio:{w:g}/251;"
    if group.map_max_width:
        style += f" max-width:{group.map_max_width}px;"
    return style


def render_group(jinja_env: jinja2.Environment, group: Group, fish_pic) -> str:
    globals_ = {"fish_pic": fish_pic, "legend_x": legend_x}
    pages = layout.split_group(group)
    out = []
    for page in pages:
        if group.layout == "duo":
            tmpl = jinja_env.get_template("page_duo.html.j2")
            out.append(tmpl.render(group=group, map_markers=_duo_map(group), **globals_))
        elif group.layout == "feature":
            tmpl = jinja_env.get_template("page_feature.html.j2")
            out.append(
                tmpl.render(
                    group=group, f=group.fish[0], map_markers=_feature_map(group), **globals_
                )
            )
        else:  # cluster
            start_index = page.continued_range[0] if page.is_continuation else 1
            cols = layout.grid_cols(page)
            # The map is shared by the whole group, not just this page's
            # chunk -- a continuation page's later fish still have their
            # numbered pins on the one map that sits on the main page.
            map_markers = "" if page.is_continuation else _cluster_map(group.fish, 1)
            if page.is_continuation:
                start, end = page.continued_range
                tmpl = jinja_env.get_template("page_continuation.html.j2")
                out.append(
                    tmpl.render(
                        group=group,
                        fish=page.fish,
                        start_index=start,
                        range_text=f"{start}–{end}",  # noqa: RUF001 -- en dash, matches the mockup's own typography
                        total=len(group.fish),
                        grid_class=_grid_class(cols, True),
                        **globals_,
                    )
                )
            else:
                tmpl = jinja_env.get_template("page_cluster.html.j2")
                out.append(
                    tmpl.render(
                        group=group,
                        fish=page.fish,
                        start_index=start_index,
                        map_markers=map_markers,
                        map_frame_style=_map_frame_style(group),
                        grid_class=_grid_class(cols, False),
                        show_gear=len(pages) == 1,
                        **globals_,
                    )
                )
    return "\n".join(out)


def render_overview(jinja_env: jinja2.Environment) -> str:
    _x, _y, w, _h = (float(v) for v in FULL_MAP_VIEW_BOX.split())
    tmpl = jinja_env.get_template("page_overview.html.j2")
    return tmpl.render(view_box=FULL_MAP_VIEW_BOX, view_box_w=f"{w:g}")


def render_index(
    jinja_env: jinja2.Environment, groups: list[Group], size_pills: dict, fish_pic
) -> str:
    by_size = paginate.build_index(groups)
    total = sum(len(v) for v in by_size.values())
    sizes = [
        {"label": SIZE_LABELS[size], "pill": size_pills[size], "entries": by_size[size]}
        for size in SIZE_ORDER
        if size in by_size
    ]
    tmpl = jinja_env.get_template("index.html.j2")
    return tmpl.render(sizes=sizes, total=total, roster=TOTAL_ROSTER, fish_pic=fish_pic)


def build_book(
    data_dir: Path = Path("data"),
    templates_dir: Path = TEMPLATES_DIR,
    assets_dir: Path = ASSETS_DIR,
) -> str:
    from . import data as data_mod
    from .validate import validate_or_raise

    groups = data_mod.load_groups(data_dir)
    palette = data_mod.load_palette(data_dir)
    for g in groups:
        if g.layout == "cluster":
            layout.assign_colors(g.fish, palette["marker_colors"])

    validate_or_raise(groups)

    fish_pic = make_fish_pic(assets_dir)
    jinja_env = env(templates_dir)
    content = render_overview(jinja_env)
    content += "\n" + render_index(jinja_env, groups, palette["size_pills"], fish_pic)
    content += "\n" + "\n".join(render_group(jinja_env, g, fish_pic) for g in groups)

    base = jinja_env.get_template("base.html.j2")
    map_defs = (assets_dir / "map_terrain_defs.html").read_text()
    return base.render(content=content, map_defs=map_defs)
