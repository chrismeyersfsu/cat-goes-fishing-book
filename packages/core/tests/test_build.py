"""fishguide build writes build/book.html; see cli.build's docstring
for why it currently just republishes the approved mockup."""

from pathlib import Path

import pytest
from fishguide import cli


def test_build_writes_book(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "reference").mkdir()
    (tmp_path / "reference" / "design_preview.html").write_text("<html>mock</html>")

    path = cli.build()

    assert path == Path("build/book.html")
    assert path.read_text() == "<html>mock</html>"


def test_build_requires_mockup(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError):
        cli.build()
