"""Procedural fish portraits: parameterized flat-cartoon SVGs, always
the fixed 4:3 FISH_VB frame so every entry card matches. `fish(**kwargs)`
takes a species' `portrait:` block from its YAML record verbatim."""

import math

# All fish art uses the same fixed frame so every entry card matches:
FISH_VB = "0 0 160 120"  # 4:3 ratio, fixed for every fish


def _ellipse(cx, cy, rx, ry, color, opacity=1):
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{color}" opacity="{opacity}"/>'


def _poly(pts, color, opacity=1):
    p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return f'<polygon points="{p}" fill="{color}" opacity="{opacity}"/>'


def _path(d, color, opacity=1, stroke=None, sw=0):
    s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return f'<path d="{d}" fill="{color}" opacity="{opacity}"{s}/>'


def fish(
    body_color,
    cx=95,
    cy=60,
    rx=34,
    ry=22,
    shape="oval",
    tail="fan",
    tail_color=None,
    dorsal="triangle",
    pectoral=True,
    stripes=None,
    spots=None,
    glow=False,
    snout=None,
    mouth="smile",
    eye="cute",
    belly=None,
    outline="#1a2a1c",
):
    """Returns a full <svg> fish portrait, viewBox 0 0 160 120, facing right, tail to the left."""
    tail_color = tail_color or body_color
    parts = []

    if glow:
        parts.append(
            f'<circle cx="{cx - 5}" cy="{cy}" r="{rx + 18}" fill="{body_color}" opacity="0.18"/>'
        )

    # ---- Tail fin (behind body, pointing left) ----
    tx = cx - rx + 6
    if tail == "fan":
        parts.append(
            _poly(
                [(tx, cy), (tx - 22, cy - 16), (tx - 14, cy), (tx - 22, cy + 16)], tail_color, 0.95
            )
        )
    elif tail == "fork":
        parts.append(
            _poly(
                [
                    (tx, cy - 3),
                    (tx - 24, cy - 18),
                    (tx - 10, cy - 2),
                    (tx - 24, cy + 18),
                    (tx, cy + 3),
                ],
                tail_color,
                0.95,
            )
        )
    elif tail == "crescent":
        parts.append(
            _path(
                f"M {tx},{cy - 14} Q {tx - 26},{cy} {tx},{cy + 14} Q {tx - 10},{cy} {tx},{cy - 14} Z",
                tail_color,
                0.95,
            )
        )
    elif tail == "small":
        parts.append(_poly([(tx, cy - 8), (tx - 14, cy), (tx, cy + 8)], tail_color, 0.95))

    # ---- Body (all with a thin outline so pale fish stay visible on light cards) ----
    ol = f' stroke="{outline}" stroke-width="1.4" stroke-opacity="0.35"'
    if shape == "elongated":
        rx2, ry2 = rx * 1.3, ry * 0.68
        parts.append(
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx2}" ry="{ry2}" fill="{body_color}"{ol}/>'
        )
    elif shape == "torpedo":
        parts.append(
            f'<path d="M {cx - rx},{cy} Q {cx - rx * 0.6},{cy - ry} {cx + rx * 0.5},{cy - ry * 0.75} '
            f"Q {cx + rx * 1.15},{cy - ry * 0.2} {cx + rx * 1.25},{cy} "
            f"Q {cx + rx * 1.15},{cy + ry * 0.2} {cx + rx * 0.5},{cy + ry * 0.75} "
            f'Q {cx - rx * 0.6},{cy + ry} {cx - rx},{cy} Z" fill="{body_color}"{ol}/>'
        )
    elif shape == "diamond":
        parts.append(
            f'<path d="M {cx - rx},{cy} L {cx - rx * 0.2},{cy - ry} L {cx + rx * 1.1},{cy} L {cx - rx * 0.2},{cy + ry} Z" fill="{body_color}"{ol}/>'
        )
    elif shape == "round":
        parts.append(
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx * 0.85}" ry="{ry * 1.05}" fill="{body_color}"{ol}/>'
        )
    else:  # oval / teardrop
        parts.append(
            f'<path d="M {cx - rx},{cy} Q {cx - rx * 0.5},{cy - ry * 1.15} {cx + rx * 0.3},{cy - ry} '
            f"Q {cx + rx * 1.05},{cy - ry * 0.5} {cx + rx * 1.1},{cy} "
            f"Q {cx + rx * 1.05},{cy + ry * 0.5} {cx + rx * 0.3},{cy + ry} "
            f'Q {cx - rx * 0.5},{cy + ry * 1.15} {cx - rx},{cy} Z" fill="{body_color}"{ol}/>'
        )

    if belly:
        parts.append(_ellipse(cx + rx * 0.15, cy + ry * 0.45, rx * 0.7, ry * 0.42, belly, 0.9))

    if stripes:
        n = stripes.get("n", 3)
        col = stripes["color"]
        for i in range(n):
            sx = cx - rx * 0.5 + i * (rx * 1.1 / n)
            parts.append(
                f'<path d="M {sx},{cy - ry} Q {sx - 4},{cy} {sx},{cy + ry}" stroke="{col}" stroke-width="3.4" fill="none" opacity="0.75"/>'
            )

    if spots:
        col = spots["color"]
        n = spots.get("n", 5)
        for i in range(n):
            ang = i * (2 * math.pi / n) + 0.4
            sx = cx + math.cos(ang) * rx * 0.5
            sy = cy + math.sin(ang) * ry * 0.5
            parts.append(
                f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{rx * 0.09:.1f}" fill="{col}" opacity="0.8"/>'
            )

    # ---- Dorsal fin ----
    if dorsal == "triangle":
        parts.append(
            _poly(
                [
                    (cx - rx * 0.1, cy - ry * 0.85),
                    (cx + rx * 0.25, cy - ry * 1.55),
                    (cx + rx * 0.5, cy - ry * 0.8),
                ],
                tail_color,
                0.9,
            )
        )
    elif dorsal == "spiky":
        base = cy - ry * 0.85
        pts = [(cx - rx * 0.15, base)]
        for i in range(3):
            xx = cx - rx * 0.05 + i * rx * 0.28
            pts.append((xx, base - ry * (0.9 + 0.15 * (i % 2))))
            pts.append((xx + rx * 0.14, base))
        parts.append(_poly(pts, tail_color, 0.9))

    # ---- Pectoral fin ----
    if pectoral:
        parts.append(
            _path(
                f"M {cx - rx * 0.1},{cy + ry * 0.5} Q {cx - rx * 0.05},{cy + ry * 1.3} {cx + rx * 0.35},{cy + ry * 0.95} Z",
                tail_color,
                0.85,
            )
        )

    # ---- Snout add-ons ----
    if snout == "point":
        parts.append(
            _poly(
                [
                    (cx + rx * 1.05, cy - ry * 0.25),
                    (cx + rx * 1.45, cy),
                    (cx + rx * 1.05, cy + ry * 0.25),
                ],
                body_color,
            )
        )
    elif snout == "sword":
        parts.append(
            _path(
                f"M {cx + rx * 1.05},{cy - 2} L {cx + rx * 2.05},{cy} L {cx + rx * 1.05},{cy + 2} Z",
                "#7a8a95",
            )
        )
    elif snout == "dragon":
        parts.append(
            _poly(
                [
                    (cx + rx * 0.85, cy - ry * 0.7),
                    (cx + rx * 1.35, cy - ry * 0.55),
                    (cx + rx * 0.95, cy - ry * 0.25),
                ],
                body_color,
                1,
            )
        )
        parts.append(
            _poly(
                [
                    (cx + rx * 0.85, cy + ry * 0.7),
                    (cx + rx * 1.35, cy + ry * 0.55),
                    (cx + rx * 0.95, cy + ry * 0.25),
                ],
                body_color,
                1,
            )
        )

    # ---- Mouth ----
    mx, my = cx + rx * 0.85, cy + ry * 0.25
    if mouth == "smile":
        parts.append(
            f'<path d="M {mx - 6},{my} Q {mx},{my + 4} {mx + 6},{my - 1}" stroke="{outline}" stroke-width="1.6" fill="none" stroke-linecap="round"/>'
        )
    elif mouth == "open":
        parts.append(
            f'<path d="M {mx - 5},{my - 2} Q {mx},{my + 5} {mx + 5},{my - 2} Q {mx},{my + 1} {mx - 5},{my - 2} Z" fill="#5a3a2e" opacity="0.75"/>'
        )
    elif mouth == "flat":
        parts.append(
            f'<line x1="{mx - 5}" y1="{my}" x2="{mx + 5}" y2="{my}" stroke="{outline}" stroke-width="1.6" stroke-linecap="round"/>'
        )

    # ---- Eye ----
    ex, ey = cx + rx * 0.35, cy - ry * 0.2
    if eye == "cute":
        parts.append(
            f'<circle cx="{ex}" cy="{ey}" r="6.5" fill="white"/><circle cx="{ex + 1.3}" cy="{ey + 0.5}" r="3.6" fill="#17241a"/><circle cx="{ex - 0.8}" cy="{ey - 1.3}" r="1.3" fill="white"/>'
        )
    elif eye == "sharp":
        parts.append(
            f'<ellipse cx="{ex}" cy="{ey}" rx="5" ry="2.6" fill="white"/><ellipse cx="{ex + 0.8}" cy="{ey}" rx="2.2" ry="2.4" fill="#17241a"/>'
        )
    elif eye == "closed":
        parts.append(
            f'<path d="M {ex - 5},{ey} Q {ex},{ey + 3} {ex + 5},{ey}" stroke="{outline}" stroke-width="1.6" fill="none" stroke-linecap="round"/>'
        )
    elif eye == "glow":
        parts.append(
            f'<circle cx="{ex}" cy="{ey}" r="5.5" fill="#eafff0"/><circle cx="{ex}" cy="{ey}" r="2.6" fill="#0c3a20"/>'
        )

    inner = "".join(parts)
    return f'<svg viewBox="{FISH_VB}" width="100%" height="100%" role="img" aria-hidden="true">{inner}</svg>'
