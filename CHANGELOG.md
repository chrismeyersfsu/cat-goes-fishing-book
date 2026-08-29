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
- New `fishguide-wiki` package: `uv run fishwiki download` pulls a
  picture for every fish in the Cat Goes Fishing wiki's `Category:Fish`
  (197 articles) into `assets/wiki_fish/`, named by the same key style
  the fish records in `data/` use, alongside a `manifest.yaml` recording
  each picture's source page, URL, dimensions and hash. Resumable
  (existing files are skipped; `--force` re-fetches), rate-limited, and
  `--list` shows what it would do without downloading. It reads the
  wiki's MediaWiki API rather than its pages, so it doesn't need a
  browser.
- `assets/wiki_fish/` is tracked in Git LFS — run `git lfs install`
  once, or the pictures clone as pointer files.
- The book now opens with a full map overview page (a wide, mostly
  uncropped view of the world, not a per-group slice) before the group
  pages, cropped to x<=1450 to cut the dead ocean past the map's own
  "furthest distance a tech boat can go" boundary marker.
- The fish index moved to right after the overview page (previously
  last), and its entries are now clickable -- each jumps straight to
  that fish's group page.
- `fishguide pdf` prints `build/book.html` to `build/book.pdf` with a
  headless Chromium (`playwright install chromium` once per machine).
  `base.html.j2` gained `@media print` rules so each `.page` lands on
  its own sheet; the same `book.html` now serves as both the
  interactive web version (open it in a browser, click through the
  index) and the source for the printed one. CI builds and publishes
  the PDF alongside the HTML.
- Index page tags now show the destination group's title ("Silo
  Depths I") instead of a tier letter ("Page B"), since the tag is
  also the clickable row's link text.
- Fish portraits now use the real picture from `assets/wiki_fish/`
  (see the `fishguide-wiki` package) when one was downloaded for that
  fish, embedded as a data URI so `book.html` stays one self-contained
  file. Falls back to the procedural `art.fish()` portrait for the few
  fish with no wiki picture (currently Treat, Underfin, Maw).
