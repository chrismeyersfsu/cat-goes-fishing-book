"""Builds the index model: every fish, grouped by size category in
`SIZE_ORDER`, tagged with where it lives. Each entry links to its
group's page (see the `id="group-..."` anchors in the page_*.html.j2
templates), so the tag shows that group's title -- what the reader
actually lands on -- rather than a page number. The full book (Phase 3,
178 fish across ~64 pages) may want real page numbers too once print
pagination exists; the title tag still works fine alongside that."""

from __future__ import annotations

from dataclasses import dataclass

from . import layout
from .models import SIZE_ORDER, Fish, Group


@dataclass
class IndexEntry:
    fish: Fish
    page_tag: str
    group_id: str  # anchor target: id="group-{group_id}" on that group's first page


def page_tag(group: Group, is_continuation: bool) -> str:
    suffix = " (cont.)" if is_continuation else ""
    return f"{group.title}{suffix}"


def build_index(groups: list[Group]) -> dict[str, list[IndexEntry]]:
    by_size: dict[str, list[IndexEntry]] = {size: [] for size in SIZE_ORDER}
    for g in groups:
        for page in layout.split_group(g):
            tag = page_tag(g, page.is_continuation)
            for f in page.fish:
                by_size[f.size].append(IndexEntry(f, tag, g.id))
    return {size: entries for size, entries in by_size.items() if entries}
