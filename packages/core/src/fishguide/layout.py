"""Splits a group's fish into pages and picks each page's presentation.
Two rules encoded here, both reverse-engineered from the approved
mockup (reference/design_preview.html) since fish_grouping_scheme.md
doesn't specify them:

- Marker colors cycle through the palette in fish order, per group
  (confirmed against src_seed/color_assign.json). Duo and feature
  layouts don't cycle -- their fish carry an explicit `color` in YAML
  instead, since a 2-fish or 1-fish map is picked for narrative
  contrast, not auto-assigned.
- A cluster/roundup page's entry grid is 4 columns when it holds 4 or
  fewer entries, else 3 -- true for all three observed map pages
  (Silo Depths I: 5 -> 3 cols; Dragon Area: 4 -> 4 cols; Huge-Fish
  Predators' map page: 4 -> 4 cols). Continuation pages are the one
  layout not covered by that rule: the sole observed continuation
  (Huge-Fish Predators, 3 leftover entries) renders 3 columns anyway,
  so continuation pages always use 3 here pending a second data point.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import Fish, Group

PALETTE = ["#e8462c", "#2b6cd4", "#d99a1b", "#7a4fb0", "#1f9e6d", "#d94f96", "#1fa7c9"]
CONTINUATION_CAPACITY = 6


def assign_colors(fish: list[Fish], palette: list[str] = PALETTE) -> None:
    """Cluster/roundup layouts only -- sets each fish's `color` from the
    palette cycle, in fish order. Mutates in place; a fish with a color
    already set (duo/feature) is left alone."""
    for i, f in enumerate(fish):
        if f.color is None:
            f.color = palette[i % len(palette)]


@dataclass
class PageSpec:
    group: Group
    fish: list[Fish]
    is_continuation: bool
    continued_range: tuple[int, int] | None = None  # 1-based (start, end) of group.fish


def split_group(group: Group) -> list[PageSpec]:
    """A duo/feature group is always one page. A cluster group fits on
    one page up to `max_entries_with_map`; the rest spill onto
    continuation pages of CONTINUATION_CAPACITY each."""
    fish = group.fish
    if group.layout != "cluster" or len(fish) <= group.max_entries_with_map:
        return [PageSpec(group, fish, is_continuation=False)]

    pages = [PageSpec(group, fish[: group.max_entries_with_map], is_continuation=False)]
    rest = fish[group.max_entries_with_map :]
    start = group.max_entries_with_map + 1
    for i in range(0, len(rest), CONTINUATION_CAPACITY):
        chunk = rest[i : i + CONTINUATION_CAPACITY]
        pages.append(
            PageSpec(
                group, chunk, is_continuation=True, continued_range=(start, start + len(chunk) - 1)
            )
        )
        start += len(chunk)
    return pages


def grid_cols(page: PageSpec) -> int:
    if page.is_continuation:
        return 3
    return 4 if len(page.fish) <= 4 else 3
