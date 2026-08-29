"""fishguide build writes build/book.html by running the real
data-driven renderer (render.build_book) against data/ + templates/ at
the repo root -- ci.sh runs pytest from there, same as manual CLI use.
Content correctness is test_golden.py's job; this just checks the CLI
wiring writes a real file to the right place."""

from pathlib import Path

from fishguide import cli


def test_build_writes_book():
    path = cli.build()

    assert path == Path("build/book.html")
    html = path.read_text()
    assert "Fish Index" in html
    assert "Bitterfish" in html
