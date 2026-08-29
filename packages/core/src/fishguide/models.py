"""The book's data model: what a fish and a group are, independent of
how they get laid out on a page or rendered to HTML. Loaders (data.py)
build these from YAML; nothing here reads a file."""

from __future__ import annotations

from dataclasses import dataclass, field

SIZE_ORDER = ["small", "medium", "large", "huge", "secret"]
LAYOUTS = ["duo", "cluster", "feature"]

# Every marker/legend "X" and index accent is this one red -- there is
# no per-fish or per-group color scheme. Numbered pins (cluster
# layout) are what disambiguates multiple fish on one map; color used
# to also vary per fish for that job, but that's redundant with the
# numbers and was dropped.
MARKER_COLOR = "#e8462c"


@dataclass
class Stat:
    icon: str
    value: str
    label: str | None = None


@dataclass
class Fish:
    key: str
    name: str
    size: str  # one of SIZE_ORDER
    coords: list[tuple[float, float]]  # marker point(s); >1 for Torby/Cowfish-style dupes
    about: str
    portrait: dict = field(default_factory=dict)  # only a fallback; see render.make_fish_pic
    stats: list[Stat] = field(default_factory=list)
    color: str = MARKER_COLOR
    pin_dy: float = 16  # cluster layout: numbered pin offset from the X mark


@dataclass
class Badge:
    text: str
    kind: str  # "cat" | "diff-easy" | "diff-mod" | "diff-hard"


@dataclass
class GearItem:
    icon: str
    text: str
    required: bool = False


@dataclass
class Path:
    points: list[tuple[float, float]]
    start_gap: float = 0
    end_gap: float = 0


@dataclass
class Group:
    id: str
    title: str
    tier: str  # "A" | "B" | "C" | "D"
    layout: str  # one of LAYOUTS
    subtitle: str
    badges: list[Badge]
    cast: str
    view_box: str
    map_caption: str
    map_alt: str
    fish: list[Fish]
    max_entries_with_map: int = 5
    shared_gear: list[GearItem] = field(default_factory=list)
    path: Path | None = None
    special_instructions: str | None = None
    about: str | None = None  # duo layout's group-level "About" paragraph
    map_label: str | None = None  # cluster layout's note below the map frame
    map_max_width: int | None = None  # cluster layout only; widens the default 340px frame
