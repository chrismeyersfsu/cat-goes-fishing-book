"""Command-line entrypoint, wired via [project.scripts] in pyproject.toml.

`uv run fishguide` is the only invocation anyone types. Keep orchestration
and file I/O here; keep the importable modules pure.
"""

import argparse
import shutil
from pathlib import Path

MOCKUP = Path("reference/design_preview.html")
BOOK = Path("build/book.html")


def build() -> Path:
    """Write build/book.html. Until the data-driven renderer in PLAN.md
    Phase 1 exists, this republishes the approved mockup — the only
    thing that currently qualifies as "the book" — so CI has something
    real to hand back as an artifact. Swap this for render.py's output
    once Phase 1 lands."""
    if not MOCKUP.exists():
        raise FileNotFoundError(f"{MOCKUP} not found; run from the repo root")
    BOOK.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(MOCKUP, BOOK)
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
