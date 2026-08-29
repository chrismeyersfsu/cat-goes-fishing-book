"""Splits a group's fish into pages and picks each page's presentation.
One rule encoded here, reverse-engineered from the approved mockup
(reference/design_preview.html) since fish_grouping_scheme.md doesn't
specify it: a cluster/roundup page's entry grid is 4 columns when it
holds 4 or fewer entries, else 3 -- true for all three observed map
pages (Silo Depths I: 5 -> 3 cols; Dragon Area: 4 -> 4 cols; Huge-Fish
Predators' map page: 4 -> 4 cols). Continuation pages are the one case
not covered by that rule: the sole observed continuation (Huge-Fish
Predators, 3 leftover entries) renders 3 columns anyway, so
continuation pages always use 3 here pending a second data point.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import Fish, Group

CONTINUATION_CAPACITY = 6


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
