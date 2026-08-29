#!/usr/bin/env bash
# Per-package CI: run locally or from the workflow, identically.
# The ruff half runs over ALL packages so a cross-cutting break can't
# hide behind CI path filters.
set -euo pipefail
cd "$(dirname "$0")/../.."
uv sync -q
uv run ruff check packages/
uv run ruff format --check packages/
uv sync -q --package fishguide-wiki
uv run --package fishguide-wiki pytest packages/wiki/tests -q
