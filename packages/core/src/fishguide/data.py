"""Loads groups.yaml + data/fish/*.yaml into the models in models.py.
The only module that reads YAML; everything downstream works with
dataclasses."""

from __future__ import annotations

from pathlib import Path

import yaml

from .models import MARKER_COLOR, Badge, Fish, GearItem, Group, Stat
from .models import Path as MarkerPath

DATA_DIR = Path("data")


def _stat(d: dict) -> Stat:
    return Stat(icon=d["icon"], value=d["value"], label=d.get("label"))


def _fish(d: dict) -> Fish:
    return Fish(
        key=d["key"],
        name=d["name"],
        size=d["size"],
        coords=[tuple(c) for c in d["coords"]],
        about=d["about"],
        portrait=d.get("portrait", {}),
        stats=[_stat(s) for s in d.get("stats", [])],
        color=d.get("color", MARKER_COLOR),
        pin_dy=d.get("pin_dy", 16),
    )


def load_fish(group_id: str, data_dir: Path = DATA_DIR) -> list[Fish]:
    raw = yaml.safe_load((data_dir / "fish" / f"{group_id}.yaml").read_text())
    return [_fish(d) for d in raw]


def load_groups(data_dir: Path = DATA_DIR) -> list[Group]:
    raw = yaml.safe_load((data_dir / "groups.yaml").read_text())
    groups = []
    for d in raw:
        path = d.get("path")
        groups.append(
            Group(
                id=d["id"],
                title=d["title"],
                tier=d["tier"],
                layout=d["layout"],
                subtitle=d["subtitle"],
                badges=[Badge(**b) for b in d["badges"]],
                cast=d["cast"],
                view_box=d["view_box"],
                map_caption=d["map_caption"],
                map_alt=d["map_alt"],
                fish=load_fish(d["id"], data_dir),
                max_entries_with_map=d.get("max_entries_with_map", 5),
                shared_gear=[GearItem(**g) for g in d.get("shared_gear", [])],
                path=MarkerPath(**path) if path else None,
                special_instructions=d.get("special_instructions"),
                about=d.get("about"),
                map_label=d.get("map_label"),
                map_max_width=d.get("map_max_width"),
            )
        )
    return groups


def load_palette(data_dir: Path = DATA_DIR) -> dict:
    return yaml.safe_load((data_dir / "palette.yaml").read_text())
