"""Turns loaded Group/Fish data into book.html. Jinja templates hold
the structural HTML; every SVG fragment (portraits, markers, paths) is
built here in Python and handed to templates as pre-rendered strings,
so autoescaping is off throughout -- there's no untrusted input, only
our own YAML.
"""

from __future__ import annotations

import base64
import io
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
TOTAL_ROSTER = 203

# The world map's coordinate space runs to x=1568 (PLAN.md's data
# model comment; confirmed against assets/map_terrain_defs.html's own
# path bounds), but everything actually drawn -- including the
# "Furthest distance a tech boat can go" label past the boundary
# arrow -- ends by x~=1410. Past that is solid, undrawn ocean fill, so
# the overview page crops to 1450 instead of the full 1568 to cut that
# dead space (checked visually; see git history for the before/after).
FULL_MAP_VIEW_BOX = "0 0 1450 251"


# Emoji -> the real game icon that replaces it (assets/game_icons/<name>.png,
# see assets/game_icons/fetch_game_icons.py). The wiki only has one clean,
# reusable icon per upgrade -- not per fish-encounter variant -- for these
# five pieces of equipment; everything else (bait, hook, net, hat) only has
# per-variant art, so it stays emoji rather than an approximation. A future
# fish or group record just uses the emoji as always -- no per-record edits
# needed for it to pick up the real icon here.
ICON_MAP = {
    "⚓": "sinker",
    "🧱": "bomb_stack",
    "💣": "detonator",
    "💥": "detonator",
    "🎣": "flick",
    # diving_lure.png is fetched too (see fetch_game_icons.py) but no emoji
    # in data/ currently means "diving lure" unambiguously, so it has no
    # entry here yet -- add one if/when a record needs it.
}


def env(templates_dir: Path = TEMPLATES_DIR, assets_dir: Path = ASSETS_DIR) -> jinja2.Environment:
    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(templates_dir),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    jinja_env.globals["icon_html"] = make_icon_html(assets_dir)
    return jinja_env


def _picture_uri(key: str, assets_dir: Path) -> str | None:
    path = assets_dir / "wiki_fish" / f"{key}.png"
    if not path.exists():
        return None
    raw = path.read_bytes()
    # Fandom serves plenty of its `.png` files as WebP, and `fishwiki
    # download` saves the bytes under the name the wiki gave them --
    # so the extension says nothing about the format. Sniff it, or the
    # data URI advertises a type it isn't and only a browser willing to
    # sniff past the header renders it.
    kind = "webp" if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP" else "png"
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:image/{kind};base64,{b64}"


def make_icon_html(assets_dir: Path = ASSETS_DIR):
    """A Jinja global (registered on the environment in `env()`, not
    passed per-render, so it reaches badges.html.j2's macros regardless
    of how a template imports them) that swaps a badge/gear/stat
    `icon:` emoji for an `<img>` of the real game icon when ICON_MAP
    has one, embedded as a data URI like make_fish_pic's pictures so
    book.html stays self-contained. Anything not in ICON_MAP -- which
    is most icons -- passes through unchanged as the emoji it already
    was."""
    uris = {}
    for emoji, name in ICON_MAP.items():
        if emoji in uris:
            continue
        path = assets_dir / "game_icons" / f"{name}.png"
        if path.exists():
            b64 = base64.b64encode(path.read_bytes()).decode("ascii")
            uris[emoji] = f"data:image/png;base64,{b64}"

    def icon_html(icon: str) -> str:
        uri = uris.get(icon)
        if uri:
            return f'<img class="game-icon" src="{uri}" alt="">'
        return icon

    return icon_html


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
        return art.fish(**f.portrait) if f.portrait else art.fish(body_color="#9aa5ac")

    return fish_pic


# Long edge of a marker picture in the embedded <symbol>, in pixels.
# Markers draw at ~26 map units wide and the page renders the map a few
# times that; 64px keeps them crisp in print without embedding 178 more
# full-size pictures (the portraits already carry those).
MARKER_THUMB_PX = 64


def _marker_symbol(f: Fish, assets_dir: Path) -> tuple[str, int, int]:
    """The fish's picture as an SVG <symbol>, plus the pixel size its
    viewBox uses. A downscaled copy of the wiki picture when there is
    one, otherwise the same procedural portrait its entry card shows --
    so every fish gets a picture on the map, none falls back to a mark."""
    from PIL import Image

    path = assets_dir / "wiki_fish" / f"{f.key}.png"
    if not path.exists():
        svg = art.fish(**f.portrait) if f.portrait else art.fish(body_color="#9aa5ac")
        inner = svg[svg.index(">") + 1 : -len("</svg>")]
        vw, vh = (int(v) for v in art.FISH_VB.split()[2:])
        return f'<symbol id="fm-{f.key}" viewBox="{art.FISH_VB}">{inner}</symbol>', vw, vh

    try:
        im = Image.open(path).convert("RGBA")
    except OSError as e:  # pragma: no cover -- an environment problem, not a data one
        # assets/wiki_fish/ is Git LFS; without `git lfs install` (or
        # `lfs: true` on a CI checkout) these are pointer stubs, and
        # PIL's own "cannot identify image file" says nothing about why.
        raise OSError(f"{path} is not a readable image -- run `git lfs pull`?") from e
    im.thumbnail((MARKER_THUMB_PX, MARKER_THUMB_PX), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=True)
    uri = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    symbol = (
        f'<symbol id="fm-{f.key}" viewBox="0 0 {im.width} {im.height}">'
        f'<image href="{uri}" width="{im.width}" height="{im.height}"/></symbol>'
    )
    return symbol, im.width, im.height


def make_marker_defs(groups: list[Group], assets_dir: Path = ASSETS_DIR):
    """Builds the one <defs> block every map's fish markers reference by
    id, plus a per-fish size lookup the marker builders need to keep
    each picture's aspect ratio. Emitting each picture once and
    `<use>`-ing it keeps a fish marked at several coordinates from
    carrying that many copies of its own art."""
    sizes: dict[str, tuple[int, int]] = {}
    symbols = []
    for g in groups:
        for f in g.fish:
            if f.key in sizes:
                continue
            symbol, w, h = _marker_symbol(f, assets_dir)
            symbols.append(symbol)
            sizes[f.key] = (w, h)
    halo = (
        f'<filter id="{markers.HALO_FILTER_ID}" x="-30%" y="-30%" width="160%" height="160%">'
        '<feMorphology in="SourceAlpha" operator="dilate" radius="1.1" result="thick"/>'
        '<feFlood flood-color="#ffffff" flood-opacity="0.95" result="white"/>'
        '<feComposite in="white" in2="thick" operator="in" result="outline"/>'
        '<feMerge><feMergeNode in="outline"/><feMergeNode in="SourceGraphic"/></feMerge>'
        "</filter>"
    )
    defs = (
        '<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>'
        + halo
        + "".join(symbols)
        + "</defs></svg>"
    )
    return defs, sizes


def _fish_marker(f: Fish, sizes: dict, x: float, y: float, size: float) -> str:
    w, h = sizes[f.key]
    return markers.fish_marker(x, y, f"fm-{f.key}", w, h, size=size)


REFERENCE_VIEW_BOX_WIDTH = 380  # Trick & Treat's; a size-26 marker reads fine at this zoom


def _marker_scale(group: Group) -> float:
    """A duo/feature map's view_box can be much wider than the reference
    (e.g. a cross-map cooldown pair) -- a fixed-size marker becomes
    nearly invisible once zoomed out far enough. Scale it up so a
    marker covers roughly the same fraction of the frame regardless of
    how wide the crop is."""
    _x, _y, w, _h = (float(v) for v in group.view_box.split())
    return max(1.0, w / REFERENCE_VIEW_BOX_WIDTH)


def _duo_map(group: Group, sizes: dict) -> str:
    parts = []
    if group.path:
        parts.append(
            markers.dashed_path(group.path.points, group.path.start_gap, group.path.end_gap)
        )
    scale = _marker_scale(group)
    for f in group.fish:
        for x, y in f.coords:
            parts.append(_fish_marker(f, sizes, x, y, 26 * scale))
    return "".join(parts)


def _feature_map(group: Group, sizes: dict) -> str:
    parts = []
    if group.path:
        parts.append(
            markers.dashed_path(group.path.points, group.path.start_gap, group.path.end_gap)
        )
        parts.append(markers.start_dot(*group.path.points[0]))
    scale = _marker_scale(group)
    f = group.fish[0]
    for x, y in f.coords:
        parts.append(_fish_marker(f, sizes, x, y, 26 * scale))
    return "".join(parts)


def _cluster_map(fish: list[Fish], start_index: int, sizes: dict) -> str:
    # Smaller than a duo/feature marker: a cluster map carries up to a
    # dozen of these plus their numbered pins on one crop.
    parts = []
    for i, f in enumerate(fish, start=start_index):
        x, y = f.coords[0]
        parts.append(_fish_marker(f, sizes, x, y, 20))
        parts.append(markers.numbered_pin(x, y + f.pin_dy, i))
    return "".join(parts)


def _grid_class(cols: int, continuation: bool) -> str:
    # See layout.py's docstring: continuation pages are always the
    # 3-column style regardless of `cols`, per the one observed sample.
    if continuation:
        return "dex-grid entry-grid3"
    return "dex-grid cols4" if cols == 4 else "entry-grid3"


WORLD_WIDTH = 1450.0  # same crop as FULL_MAP_VIEW_BOX -- the drawn world, not the 1568 space


def _context_strip(group: Group) -> str:
    """The whole world drawn as a short band above a group's map, with
    this group's crop marked on it, and two guide lines running from
    the mark's edges down to the edges of the detail map below.

    The band answers "where on the map is this?" without the reader
    scrolling back to the overview page, which is the only way to ask
    that question today. It's static markup on purpose: it costs no
    interaction, and unlike a zoom control it survives into the printed
    PDF. The guide lines are what tie the two together -- without them
    a full-width crop mark sitting above a full-width detail map reads
    as two unrelated pictures."""
    vx, _vy, vw, _vh = (float(v) for v in group.view_box.split())
    lo = max(0.0, min(vx, WORLD_WIDTH))
    hi = max(lo, min(vx + vw, WORLD_WIDTH))
    fl, fr = lo / WORLD_WIDTH * 100, hi / WORLD_WIDTH * 100
    return (
        '<div class="ctx">'
        f'<svg class="ctx-map" viewBox="0 0 {WORLD_WIDTH:g} 251" preserveAspectRatio="xMidYMid meet" '
        'role="img" aria-label="The whole world, with this page\'s slice marked">'
        '<use href="#mapTerrain"/>'
        f'<rect class="ctx-box" x="{lo:.1f}" y="0" width="{hi - lo:.1f}" height="251"/>'
        "</svg>"
        '<svg class="ctx-link" viewBox="0 0 100 10" preserveAspectRatio="none" aria-hidden="true">'
        f'<path d="M{fl:.2f} 0 L0 10"/><path d="M{fr:.2f} 0 L100 10"/>'
        "</svg>"
        "</div>"
    )


def _map_frame_style(group: Group) -> str:
    _x, _y, w, _h = (float(v) for v in group.view_box.split())
    style = f"aspect-ratio:{w:g}/251;"
    if group.map_max_width:
        style += f" max-width:{group.map_max_width}px;"
    return style


def render_group(jinja_env: jinja2.Environment, group: Group, fish_pic, sizes: dict) -> str:
    globals_ = {"fish_pic": fish_pic}
    context_strip = _context_strip(group)
    pages = layout.split_group(group)
    out = []
    for page in pages:
        if group.layout == "duo":
            tmpl = jinja_env.get_template("page_duo.html.j2")
            out.append(
                tmpl.render(
                    group=group,
                    map_markers=_duo_map(group, sizes),
                    map_frame_style=_map_frame_style(group),
                    context_strip=context_strip,
                    **globals_,
                )
            )
        elif group.layout == "feature":
            tmpl = jinja_env.get_template("page_feature.html.j2")
            out.append(
                tmpl.render(
                    group=group,
                    f=group.fish[0],
                    map_markers=_feature_map(group, sizes),
                    map_frame_style=_map_frame_style(group),
                    context_strip=context_strip,
                    **globals_,
                )
            )
        else:  # cluster
            start_index = page.continued_range[0] if page.is_continuation else 1
            cols = layout.grid_cols(page)
            # The map is shared by the whole group, not just this page's
            # chunk -- a continuation page's later fish still have their
            # numbered pins on the one map that sits on the main page.
            map_markers = "" if page.is_continuation else _cluster_map(group.fish, 1, sizes)
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
                        context_strip=context_strip,
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

    validate_or_raise(groups, assets_dir)

    fish_pic = make_fish_pic(assets_dir)
    jinja_env = env(templates_dir, assets_dir)
    content = render_overview(jinja_env)
    content += "\n" + render_index(jinja_env, groups, palette["size_pills"], fish_pic)
    marker_defs, sizes = make_marker_defs(groups, assets_dir)
    content += "\n" + "\n".join(render_group(jinja_env, g, fish_pic, sizes) for g in groups)

    base = jinja_env.get_template("base.html.j2")
    map_defs = (assets_dir / "map_terrain_defs.html").read_text() + marker_defs
    return base.render(content=content, map_defs=map_defs)
