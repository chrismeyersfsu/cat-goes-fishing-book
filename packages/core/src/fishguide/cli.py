"""Command-line entrypoint, wired via [project.scripts] in pyproject.toml.

`uv run fishguide` is the only invocation anyone types. Keep orchestration
and file I/O here; keep the importable modules pure.
"""

import argparse


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="fishguide", description=__doc__.splitlines()[0])
    p.parse_args(argv)
    print("fishguide: replace me with a real command")
