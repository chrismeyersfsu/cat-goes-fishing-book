"""Builds the index model: every fish, grouped by size category in
`SIZE_ORDER`, tagged with where it lives. The full book (Phase 3, all
178 fish across ~64 numbered pages) will tag entries with a real page
number; with only a handful of demo groups there's no numbering worth
computing yet, so entries are tagged by tier letter instead -- the
same "Page A/B/C/D" scheme the approved mockup uses for its preview
index."""

from __future__ import annotations

from dataclasses import dataclass

from . import layout
from .models import SIZE_ORDER, Fish, Group


@dataclass
class IndexEntry:
    fish: Fish
    page_tag: str


def page_tag(group: Group, is_continuation: bool) -> str:
    suffix = " cont." if is_continuation else ""
    return f"Page {group.tier}{suffix}"


def build_index(groups: list[Group]) -> dict[str, list[IndexEntry]]:
    by_size: dict[str, list[IndexEntry]] = {size: [] for size in SIZE_ORDER}
    for g in groups:
        for page in layout.split_group(g):
            tag = page_tag(g, page.is_continuation)
            for f in page.fish:
                by_size[f.size].append(IndexEntry(f, tag))
    return {size: entries for size, entries in by_size.items() if entries}
