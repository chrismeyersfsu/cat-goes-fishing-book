# fishguide

Printed field guide for *Cat Goes Fishing*, built from YAML data +
Jinja2 templates. Read `PLAN.md` first — it has the data model, the
four page layouts, the validation rules, and the phase plan this
project is built in. `reference/` and `src_seed/` are starter
material (approved mockup, fish roster, prototype art/marker code) to
port into `packages/core/src/fishguide/`, not the final shape.

uv workspace monorepo; structure follows the patterns in
`caseworkflow/docs/patterns/` (workspace layout, conventions,
ci-release).

- `./packages/core/ci.sh` is the CI entry; run it before pushing.
  Hooks: `git config core.hooksPath .githooks`.
- One concern per package. A new concern gets a new package under
  `packages/`, not a subdirectory of an existing one.
- Tests fake external HTTP at a module's `_get`/`_post` seam against
  fixture files; parsers stay pure functions.
- Module docstrings state each module's contract: what it owns, what it
  never does, what callers rely on.
- `CHANGELOG.md` entry with every user-facing change, same commit.
- Push independent work out to background subagents on Sonnet rather
  than doing it serially. Give each agent a disjoint set of files —
  `data/` and `templates/` are separate lanes — and tell every one of
  them about the five golden-test-frozen groups.
