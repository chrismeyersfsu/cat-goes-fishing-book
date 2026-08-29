# Changelog

All notable user-facing changes to this project. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Project scaffold from python-monorepo-template.
- `fishguide build` and a CI workflow that runs it and uploads
  `build/` as a downloadable artifact on every push/PR. For now it
  republishes the approved mockup; swaps to the real renderer in
  Phase 1.
- The book is now also published on every push to main as a
  no-zip rolling GitHub Release asset (`latest`) and on GitHub Pages
  (https://chrismeyersfsu.github.io/cat-goes-fishing-book/). Repo made
  public to support Pages.
- Phase 1 engine: `fishguide build` now data-drives the book instead
  of republishing the static mockup. Fish/group models, the ported
  portrait/marker generators, page-splitting + color-assignment
  (`layout.py`), the index builder (`paginate.py`), data-quality
  checks (`validate.py`), and Jinja templates for all four page
  layouts. Seeded with the 5 demo groups from PLAN.md, hand-transcribed
  into `data/`; a golden test confirms the render matches the approved
  mockup page-for-page. The other 173 fish (Phase 3) still aren't in
  `data/` yet.
