"""Pure functions over MediaWiki JSON: no network, no filesystem, no clock.

Owns: turning API response dicts into the records download.py works
with, the page-title -> fish-key slug rule, and the rule for picking
which of a page's images is the fish portrait.

Never: makes a request or decides where a file lands on disk.

Callers rely on every function here being deterministic, so the tests
run entirely off the fixture files in tests/fixtures/.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

# Wiki chrome and templates that show up in `prop=images` but are never a fish.
CHROME = ("wiki-wordmark", "site-logo", "favicon", "placeholder", "wiki.png", "vignette")

IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".webp")

# Seasonal/alternate sprites, deprioritized when a page offers several files.
VARIANT_TOKENS = {"hal", "halloween", "xmas", "christmas", "old", "beta", "unused", "icon"}


@dataclass
class FishPage:
    """One fish article, plus the portrait we resolved for it (if any)."""

    title: str
    pageid: int
    key: str
    image_title: str | None = None  # "File:..." form, when resolved that way
    url: str | None = None
    width: int | None = None
    height: int | None = None


def key_for(title: str) -> str:
    """Page title -> the `key` style already used in data/fish/*.yaml.

    "Ancient Kingfish" -> "ancientkingfish". Lowercase alphanumerics only,
    so a downloaded file lands next to the fish record that names it.
    """
    return re.sub(r"[^a-z0-9]", "", title.lower())


def _tokens(name: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9]+", name.lower()) if t]


def fish_pages(responses: Iterable[dict]) -> list[FishPage]:
    """Flatten `generator=categorymembers&prop=pageimages` responses.

    A page whose lead image the API didn't report comes back with
    `url=None`; download.py resolves those in a second pass.
    """
    pages: dict[int, FishPage] = {}
    for resp in responses:
        for raw in resp.get("query", {}).get("pages", {}).values():
            if raw.get("ns") != 0:
                continue
            original = raw.get("original") or {}
            pages[raw["pageid"]] = FishPage(
                title=raw["title"],
                pageid=raw["pageid"],
                key=key_for(raw["title"]),
                image_title=("File:" + raw["pageimage"]) if raw.get("pageimage") else None,
                url=original.get("source"),
                width=original.get("width"),
                height=original.get("height"),
            )
    return sorted(pages.values(), key=lambda p: p.title)


def page_file_titles(responses: Iterable[dict]) -> dict[str, list[str]]:
    """Flatten `prop=images` responses into page title -> file titles."""
    out: dict[str, list[str]] = {}
    for resp in responses:
        for raw in resp.get("query", {}).get("pages", {}).values():
            out.setdefault(raw["title"], []).extend(i["title"] for i in raw.get("images", []))
    return out


def pick_file(page_title: str, file_titles: Iterable[str]) -> str | None:
    """Choose the portrait among a page's files, or None if none qualifies.

    Prefers a filename that names the fish ("Tim Clear.png" on the Tim
    page) over a seasonal sprite ("Spr tim hal 0.png"), and PNG over
    lossy formats. Ties break alphabetically so the choice is stable.
    """
    page_key = key_for(page_title)
    ranked = []
    for title in file_titles:
        name = title.removeprefix("File:")
        low = name.lower()
        if not low.endswith(IMAGE_SUFFIXES) or any(c in low for c in CHROME):
            continue
        tokens = _tokens(name)
        names_the_fish = page_key and page_key in "".join(tokens)
        ranked.append(
            (
                0 if names_the_fish else 1,
                1 if VARIANT_TOKENS.intersection(tokens) else 0,
                0 if low.endswith(".png") else 1,
                name,
                title,
            )
        )
    return min(ranked)[-1] if ranked else None


def file_urls(responses: Iterable[dict]) -> dict[str, dict]:
    """Flatten `prop=imageinfo` responses into file title -> {url,width,height}.

    Titles are normalized to space form, matching what `prop=images` returns.
    """
    out: dict[str, dict] = {}
    for resp in responses:
        for raw in resp.get("query", {}).get("pages", {}).values():
            info = (raw.get("imageinfo") or [None])[0]
            if info:
                out[raw["title"].replace("_", " ")] = {
                    "url": info["url"],
                    "width": info.get("width"),
                    "height": info.get("height"),
                }
    return out


def suffix_for(url: str) -> str:
    """The file extension to save a wiki image URL under, ".png" by default."""
    stem = url.split("/revision/")[0].split("?")[0].lower()
    for suffix in IMAGE_SUFFIXES:
        if stem.endswith(suffix):
            return suffix
    return ".png"
