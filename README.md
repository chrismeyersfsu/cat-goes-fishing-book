# cat-goes-fishing-book

A printed, Pokémon-handbook-style field guide for the game *Cat Goes
Fishing*: 178 fish organized onto themed map pages, each with the
world-map crop marking every fish, per-fish entries with generated
portrait art, and a size-organized index. See `PLAN.md` for the full
build plan (data model, layouts, validation rules, phases).

uv workspace monorepo — one lockfile, one virtualenv, small installable
packages under `packages/`. Structure follows the portable patterns in
`caseworkflow/docs/patterns/` (workspace layout, conventions,
ci-release).

## Layout

| Piece | Where |
|---|---|
| Build plan | `PLAN.md` |
| Approved mockup, fish grouping data, source guide text | `reference/` |
| World-map SVG defs | `assets/` |
| Working prototypes for portrait art + map markers (to be ported into `packages/core/src/fishguide/`) | `src_seed/` |
| The `fishguide` package (build engine + CLI) | `packages/core/` |
| The `fishguide-wiki` package (fish art fetcher + CLI) | `packages/wiki/` |
| Fish pictures fetched from the wiki (Git LFS) | `assets/wiki_fish/` |

## Use it

```
uv sync
./packages/core/ci.sh          # ruff + pytest
./packages/wiki/ci.sh
uv run fishwiki download       # fish pictures from the wiki -> assets/wiki_fish/
uv run fishguide build         # data/ + templates/ -> build/book.html
uv run playwright install chromium  # once per machine, before `fishguide pdf`
uv run fishguide pdf           # build/book.html -> build/book.pdf (one .page per sheet)
```

`build/book.html` doubles as the interactive web version (open it in a
browser; the index links jump to each group's page) and the source for
the printed version (`fishguide pdf` prints it with `@media print`
rules so each page lands on its own sheet).

`assets/wiki_fish/` is stored in [Git LFS](https://git-lfs.com), so
`git lfs install` once before cloning or pulling, or the PNGs arrive as
pointer text files. `fishwiki download` is resumable: it skips pictures
already on disk, so re-running it after the wiki adds a fish costs only
the new ones (`--force` re-fetches everything).

## Conventions baked in

- Test-only dependencies go in `[dependency-groups] dev`, never in
  `dependencies` — runtime metadata stays honest.
- CLIs are `[project.scripts]` entries; `uv run <name>` is the only
  invocation anyone types.
- Module docstrings state the module's contract; a docstring edit is a
  docs edit.
- `CHANGELOG.md` entry for every user-facing feature, same commit.

## Growing the project

Add a package per new concern (`packages/<concern>/`, copy `core`'s
shape, add it to the new package's workflow paths). When the import
graph needs enforcing, add a devtools package with import-linter
contracts; see the pattern docs for storage, telemetry, and deployment
conventions as those needs arise.
