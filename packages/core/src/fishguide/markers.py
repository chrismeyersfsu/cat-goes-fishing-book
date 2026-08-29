"""Map marker SVG fragments: X marks, numbered pins, the start dot, and
dashed lure paths. Coordinates are in the source map's 1568x251 space;
callers crop a viewBox slice per group."""

import math


def x_mark(x, y, size=7.5, color="#e8462c"):
    """Colored X with white halo, matches established map marker style."""
    d = size
    return (
        f'<g class="fish-x">'
        f'<line x1="{x - d:.1f}" y1="{y - d:.1f}" x2="{x + d:.1f}" y2="{y + d:.1f}" stroke="white" stroke-width="4.2" stroke-linecap="round"/>'
        f'<line x1="{x - d:.1f}" y1="{y + d:.1f}" x2="{x + d:.1f}" y2="{y - d:.1f}" stroke="white" stroke-width="4.2" stroke-linecap="round"/>'
        f'<line x1="{x - d:.1f}" y1="{y - d:.1f}" x2="{x + d:.1f}" y2="{y + d:.1f}" stroke="{color}" stroke-width="2.2" stroke-linecap="round"/>'
        f'<line x1="{x - d:.1f}" y1="{y + d:.1f}" x2="{x + d:.1f}" y2="{y - d:.1f}" stroke="{color}" stroke-width="2.2" stroke-linecap="round"/>'
        f"</g>"
    )


def small_x_mark(x, y, size=6.2, color="#e8462c"):
    """Smaller X for dex-grid style pages with many markers."""
    d = size
    return (
        f'<g class="fish-x">'
        f'<line x1="{x - d:.1f}" y1="{y - d:.1f}" x2="{x + d:.1f}" y2="{y + d:.1f}" stroke="white" stroke-width="3.4" stroke-linecap="round"/>'
        f'<line x1="{x - d:.1f}" y1="{y + d:.1f}" x2="{x + d:.1f}" y2="{y - d:.1f}" stroke="white" stroke-width="3.4" stroke-linecap="round"/>'
        f'<line x1="{x - d:.1f}" y1="{y - d:.1f}" x2="{x + d:.1f}" y2="{y + d:.1f}" stroke="{color}" stroke-width="1.8" stroke-linecap="round"/>'
        f'<line x1="{x - d:.1f}" y1="{y + d:.1f}" x2="{x + d:.1f}" y2="{y - d:.1f}" stroke="{color}" stroke-width="1.8" stroke-linecap="round"/>'
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


def legend_x(color, size=18):
    return (
        f'<svg class="duo-x" viewBox="0 0 20 20" aria-hidden="true">'
        f'<line x1="4" y1="4" x2="16" y2="16" stroke="white" stroke-width="5" stroke-linecap="round"/>'
        f'<line x1="4" y1="16" x2="16" y2="4" stroke="white" stroke-width="5" stroke-linecap="round"/>'
        f'<line x1="4" y1="4" x2="16" y2="16" stroke="{color}" stroke-width="2.6" stroke-linecap="round"/>'
        f'<line x1="4" y1="16" x2="16" y2="4" stroke="{color}" stroke-width="2.6" stroke-linecap="round"/>'
        f"</svg>"
    )
