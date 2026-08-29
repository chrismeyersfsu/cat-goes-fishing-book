"""parse.py's pure functions, exercised against the fixture responses in
tests/fixtures/ -- captured from the live wiki once, so these run offline."""

import json
from pathlib import Path

from fishguide_wiki import parse

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_key_matches_the_data_yaml_style():
    assert parse.key_for("Ancient Kingfish") == "ancientkingfish"
    assert parse.key_for("Bitterfish") == "bitterfish"
    assert parse.key_for("Lil' Cheesefin") == "lilcheesefin"


def test_fish_pages_reads_lead_images():
    pages = parse.fish_pages([load("categorymembers.json")])
    by_key = {p.key: p for p in pages}
    assert by_key["anglerfish"].url.endswith(
        "Anglerfish_clear.png/revision/latest?cb=20211121123643"
    )
    assert by_key["anglerfish"].width == 255


def test_fish_pages_merges_continued_responses_and_sorts():
    pages = parse.fish_pages([load("categorymembers.json"), load("categorymembers_page2.json")])
    assert len(pages) == len({p.pageid for p in pages}) > 5
    assert [p.title for p in pages] == sorted(p.title for p in pages)


def test_fish_pages_leaves_url_none_when_the_api_reports_no_lead_image():
    pages = parse.fish_pages([load("categorymembers_page2.json")])
    assert any(p.url is None for p in pages)


def test_page_file_titles_flattens_prop_images():
    listed = parse.page_file_titles([load("page_images.json")])
    assert listed["Bombat"] == ["File:Spr fish s18 0.png"]
    assert set(listed["Tim"]) == {"File:Spr tim hal 0.png", "File:Tim Clear.png.png"}


def test_pick_file_prefers_the_file_named_after_the_fish():
    listed = parse.page_file_titles([load("page_images.json")])
    assert parse.pick_file("Tim", listed["Tim"]) == "File:Tim Clear.png.png"


def test_pick_file_falls_back_to_the_only_sprite():
    assert parse.pick_file("Bombat", ["File:Spr fish s18 0.png"]) == "File:Spr fish s18 0.png"


def test_pick_file_skips_wiki_chrome_and_non_images():
    files = ["File:Wiki-wordmark.png", "File:Site-logo.png", "File:Notes.pdf"]
    assert parse.pick_file("Bombat", files) is None


def test_pick_file_deprioritizes_seasonal_variants():
    files = ["File:Spr tim hal 0.png", "File:Spr tim 0.png"]
    assert parse.pick_file("Tim", files) == "File:Spr tim 0.png"


def test_file_urls_normalizes_underscored_titles():
    urls = parse.file_urls([load("imageinfo.json")])
    assert urls["File:Spr smarty 0.png"]["url"].endswith(
        "Spr_smarty_0.png/revision/latest?cb=20230803190730"
    )
    assert urls["File:Spr smarty 0.png"]["height"] == 119


def test_suffix_for_reads_through_the_revision_suffix():
    assert parse.suffix_for("https://x/Tim.png/revision/latest?cb=1") == ".png"
    assert parse.suffix_for("https://x/Tim.JPG/revision/latest") == ".jpg"
    assert parse.suffix_for("https://x/whatever") == ".png"
