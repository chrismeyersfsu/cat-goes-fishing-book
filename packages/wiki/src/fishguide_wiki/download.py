"""Orchestrates a fetch run: wiki -> image files on disk + a manifest.

Owns: the two-pass resolve (category listing, then a fallback lookup for
pages whose lead image the API didn't report), where files land, skipping
work already done, and the manifest that records where each picture came
from.

Never: builds a URL or opens a socket itself (api.py), and never
interprets a response body (parse.py).

Callers rely on a run being resumable -- an existing file is left alone
unless `force` -- and on the manifest listing every fish the wiki has,
including the ones with no usable picture.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path

import yaml

from . import api, parse
from .parse import FishPage

CATEGORY = "Category:Fish"
OUT_DIR = Path("assets/wiki_fish")
MANIFEST = "manifest.yaml"

Progress = Callable[[str], None]


def _noop(_: str) -> None:
    pass


def resolve(category: str = CATEGORY, progress: Progress = _noop) -> list[FishPage]:
    """List the category's fish and attach a portrait URL to each."""
    progress(f"listing {category}")
    pages = parse.fish_pages(
        api.query(
            {
                "action": "query",
                "generator": "categorymembers",
                "gcmtitle": category,
                "gcmlimit": "500",
                "prop": "pageimages",
                "piprop": "original|name",
            }
        )
    )
    progress(f"found {len(pages)} pages")

    unresolved = [p for p in pages if not p.url]
    if unresolved:
        progress(f"resolving {len(unresolved)} pages the API gave no lead image for")
        _resolve_fallback(unresolved)
    return pages


def _resolve_fallback(pages: list[FishPage]) -> None:
    """Fill in `url` from `prop=images` + `prop=imageinfo`, in place."""
    by_title = {p.title: p for p in pages}
    listed: dict[str, list[str]] = {}
    for batch in api.batched_titles(sorted(by_title)):
        listed |= parse.page_file_titles(
            api.query(
                {"action": "query", "titles": "|".join(batch), "prop": "images", "imlimit": "50"}
            )
        )

    picked = {t: parse.pick_file(t, files) for t, files in listed.items()}
    wanted = sorted({f for f in picked.values() if f})
    urls: dict[str, dict] = {}
    for batch in api.batched_titles(wanted):
        urls |= parse.file_urls(
            api.query(
                {
                    "action": "query",
                    "titles": "|".join(batch),
                    "prop": "imageinfo",
                    "iiprop": "url|size|mime",
                }
            )
        )

    for title, file_title in picked.items():
        page = by_title.get(title)  # the API can answer with a normalized title
        info = urls.get(file_title) if file_title else None
        if not page or not info:
            continue
        page.image_title = file_title
        page.url = info["url"]
        page.width = info.get("width")
        page.height = info.get("height")


def save(
    pages: list[FishPage], out_dir: Path = OUT_DIR, force: bool = False, progress: Progress = _noop
) -> list[dict]:
    """Download each page's portrait into `out_dir`; return manifest records.

    A page with no picture still gets a record, with `file: null`, so the
    manifest doubles as the list of fish that still need hand-drawn art.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for page in pages:
        record = {"key": page.key, "name": page.title, "page": api.page_url(page.title)}
        if not page.url:
            progress(f"  {page.title}: no picture on the wiki")
            records.append(record | {"file": None})
            continue

        name = page.key + parse.suffix_for(page.url)
        path = out_dir / name
        if path.exists() and not force:
            progress(f"  {page.title}: have it")
            data = path.read_bytes()
        else:
            progress(f"  {page.title}: downloading")
            data = api.fetch(page.url)
            path.write_bytes(data)

        records.append(
            record
            | {
                "file": name,
                "source": page.url,
                "width": page.width,
                "height": page.height,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    return records


def write_manifest(records: list[dict], out_dir: Path = OUT_DIR) -> Path:
    """Record provenance next to the pictures, for attribution and diffing."""
    path = out_dir / MANIFEST
    header = (
        "# Written by `fishwiki download` -- do not hand-edit.\n"
        "# Fish artwork from the Cat Goes Fishing Wiki (cat-goes-fishing.fandom.com),\n"
        "# whose text is CC BY-SA; the sprites themselves are the game's.\n"
        "# `file: null` means the wiki has an article but no usable picture.\n"
    )
    path.write_text(header + yaml.safe_dump(records, sort_keys=False, allow_unicode=True))
    return path
