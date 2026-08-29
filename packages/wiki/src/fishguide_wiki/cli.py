"""Command-line entrypoint, wired via [project.scripts] in pyproject.toml.

`uv run fishwiki` is the only invocation anyone types. Keep orchestration
and argument handling here; keep the importable modules pure.
"""

import argparse
from pathlib import Path

from . import download


def _run(args) -> None:
    out = Path(args.out)
    pages = download.resolve(args.category, progress=print)
    if args.limit:
        pages = pages[: args.limit]

    if args.list:
        for page in pages:
            print(f"{page.key:24} {page.title:28} {page.url or '(no picture)'}")
        return

    records = download.save(pages, out, force=args.force, progress=print)
    manifest = download.write_manifest(records, out)
    have = sum(1 for r in records if r["file"])
    print(f"fishwiki: {have}/{len(records)} pictures in {out}, manifest at {manifest}")
    missing = [r["name"] for r in records if not r["file"]]
    if missing:
        print(f"fishwiki: no picture on the wiki for {len(missing)}: {', '.join(missing)}")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="fishwiki", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="command")
    dl = sub.add_parser("download", help="download every fish picture from the wiki")
    dl.add_argument(
        "--out", default=str(download.OUT_DIR), help=f"output dir (default: {download.OUT_DIR})"
    )
    dl.add_argument(
        "--category",
        default=download.CATEGORY,
        help=f"wiki category (default: {download.CATEGORY})",
    )
    dl.add_argument("--force", action="store_true", help="re-download pictures already on disk")
    dl.add_argument("--limit", type=int, help="stop after N fish (for a quick trial run)")
    dl.add_argument(
        "--list", action="store_true", help="show what would be downloaded, fetch nothing"
    )
    args = p.parse_args(argv)

    if args.command == "download":
        _run(args)
    else:
        p.print_help()
