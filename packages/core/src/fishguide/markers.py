"""Map marker SVG fragments: the fish-picture marker, numbered pins,
the start dot, and dashed lure paths. Coordinates are in the source map's 1568x251 space;
callers crop a viewBox slice per group."""

import math

# Every fish-picture marker shares one white-outline filter (defined
# once alongside the picture symbols, see render.make_marker_defs) --
# without it a dark fish sits invisibly on the dark-green water.
HALO_FILTER_ID = "fish-marker-halo"


def fish_marker(x, y, symbol_id, pic_w, pic_h, size=26.0, key=None):
    """The fish's own picture as its map marker, fitted inside a `size`
    box on its longest edge and centered on (x, y). Reads as "this
    fish, here" far more directly than the X this replaced. `key`
    tags the marker with the fish it stands for, so a tap can
    find its record."""
    scale = size / max(pic_w, pic_h)
    w, h = pic_w * scale, pic_h * scale
    ident = f' data-fish="{key}"' if key else ""
    return (
        f'<g class="fish-marker"{ident} filter="url(#{HALO_FILTER_ID})">'
        f'<use href="#{symbol_id}" x="{x - w / 2:.1f}" y="{y - h / 2:.1f}" '
        f'width="{w:.1f}" height="{h:.1f}"/>'
        f"</g>"
    )


def numbered_pin(x, y, n, r=6.8, color="#12496b"):
    fs = 8 if r <= 7 else 9
    return (
        f'<g><circle cx="{x}" cy="{y}" r="{r}" fill="{color}" stroke="white" stroke-width="1.4"/>'
        f'<text x="{x}" y="{y + 2.9:.1f}" font-size="{fs}" fill="white" text-anchor="middle" '
        f'font-weight="700" font-family="\'Space Mono\',monospace">{n}</text></g>'
    )


def start_dot(x, y, r=6.5, color="#f2c14e"):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}" stroke="white" stroke-width="2.2"/>'


def trim_polyline(points, start_gap=0, end_gap=0):
    """Trim a polyline's start/end by given pixel gaps so dashed path doesn't run through marker centers."""
    pts = list(points)

    def trim_end(pts, gap):
        if gap <= 0 or len(pts) < 2:
            return pts
        (x1, y1) = pts[-2]
        (x2, y2) = pts[-1]
        dx, dy = x2 - x1, y2 - y1
        dist = math.hypot(dx, dy)
        if dist <= gap:
            return pts[:-1]
        t = (dist - gap) / dist
        new_end = (x1 + dx * t, y1 + dy * t)
        return [*pts[:-1], new_end]

    pts = trim_end(pts, end_gap)
    pts = list(reversed(trim_end(list(reversed(pts)), start_gap)))
    return pts


def dashed_path(points, start_gap=0, end_gap=0):
    pts = trim_polyline(points, start_gap, end_gap)
    d = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
    halo = f'<path d="{d}" fill="none" stroke="white" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" opacity="0.85"/>'
    dash = f'<path d="{d}" fill="none" stroke="#000000" stroke-width="2.1" stroke-dasharray="5 4.5" stroke-linecap="round" stroke-linejoin="round"/>'
    return halo + dash
