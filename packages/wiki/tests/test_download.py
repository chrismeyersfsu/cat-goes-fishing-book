"""A whole fetch run with the network faked at api._get -- the one seam
every request in this package goes through. Fixture responses stand in
for the wiki; image bytes are made up, since only their length and hash
reach the manifest."""

import urllib.parse
from pathlib import Path

import pytest
import yaml
from fishguide_wiki import api, download
from fishguide_wiki.parse import FishPage

FIXTURES = Path(__file__).parent / "fixtures"
IMAGE = b"\x89PNG\r\n\x1a\n fake pixels"


def _fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def _fake_get(url: str) -> bytes:
    """Route an API URL to the fixture that answers it."""
    if not url.startswith(api.API):
        return IMAGE  # an image download
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    if q.get("generator") == ["categorymembers"]:
        return _fixture(
            "categorymembers_page2.json" if "gcmcontinue" in q else "categorymembers.json"
        )
    if q.get("prop") == ["images"]:
        return _fixture("page_images_run.json")
    if q.get("prop") == ["imageinfo"]:
        return _fixture("imageinfo_run.json")
    raise AssertionError(f"unexpected request: {url}")


@pytest.fixture
def wiki(monkeypatch):
    monkeypatch.setattr(api, "_get", _fake_get)
    monkeypatch.setattr(api, "DELAY", 0)
    return _fake_get


def test_resolve_walks_both_category_pages(wiki):
    pages = download.resolve()
    assert len(pages) > 5
    assert all(p.key for p in pages)


def test_resolve_backfills_pages_with_no_lead_image(wiki):
    pages = {p.title: p for p in download.resolve()}
    bishop = pages["Bishop"]  # the category listing reports no lead image for it
    assert bishop.image_title == "File:Bishop.png"
    assert bishop.url.endswith("Bishop.png/revision/latest?cb=20230810192646")
    assert (bishop.width, bishop.height) == (426, 102)


def test_save_writes_one_file_per_fish_named_by_key(tmp_path, wiki):
    records = download.save(download.resolve(), tmp_path)
    named = {r["key"]: r for r in records if r["file"]}
    assert named["ancientkingfish"]["file"] == "ancientkingfish.png"
    assert (tmp_path / "ancientkingfish.png").read_bytes() == IMAGE
    assert named["ancientkingfish"]["bytes"] == len(IMAGE)
    assert named["bishop"]["page"] == "https://cat-goes-fishing.fandom.com/wiki/Bishop"


def test_save_records_fish_the_wiki_has_no_picture_for(tmp_path, wiki):
    art_less = FishPage(title="Nofish", pageid=1, key="nofish")
    records = download.save([art_less], tmp_path)
    assert records == [
        {"key": "nofish", "name": "Nofish", "page": api.page_url("Nofish"), "file": None}
    ]
    assert list(tmp_path.iterdir()) == []


def test_save_skips_files_already_on_disk(tmp_path, wiki, monkeypatch):
    pages = download.resolve()
    download.save(pages, tmp_path)

    downloads = []
    monkeypatch.setattr(api, "_get", lambda url: downloads.append(url) or _fake_get(url))
    download.save(pages, tmp_path)
    assert downloads == []

    download.save(pages, tmp_path, force=True)
    assert downloads


def test_manifest_records_provenance(tmp_path, wiki):
    records = download.save(download.resolve(), tmp_path)
    path = download.write_manifest(records, tmp_path)
    text = path.read_text()
    assert "cat-goes-fishing.fandom.com" in text
    loaded = yaml.safe_load(text)
    assert [r["key"] for r in loaded] == [r["key"] for r in records]
