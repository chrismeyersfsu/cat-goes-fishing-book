"""Command-line entrypoint, wired via [project.scripts] in pyproject.toml.

`uv run fishguide` is the only invocation anyone types. Keep orchestration
and file I/O here; keep the importable modules pure.
"""

import argparse
from pathlib import Path

from . import render

BOOK = Path("build/book.html")


def build() -> Path:
    """Write build/book.html from data/ + templates/ (see render.py).
    Phase 1 has only the 5 demo groups from PLAN.md; Phase 3 adds the
    rest of the 178-fish roster to data/."""
    html = render.build_book()
    BOOK.parent.mkdir(parents=True, exist_ok=True)
    BOOK.write_text(html)
    return BOOK


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="fishguide", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="command")
    sub.add_parser("build", help="render the book to build/book.html")
    args = p.parse_args(argv)

    if args.command == "build":
        path = build()
        print(f"fishguide: wrote {path}")
    else:
        print("fishguide: replace me with a real command")
