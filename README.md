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

## Use it

```
uv sync
./packages/core/ci.sh       # ruff + pytest
uv run fishguide            # CLI stub — see PLAN.md for the intended commands
```

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
