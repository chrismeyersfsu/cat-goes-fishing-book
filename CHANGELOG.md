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
- Map/legend X's are now a single fixed red for every fish, instead of
  cycling through a 7-color palette per group -- the numbered pins
  already disambiguate multiple fish on one map, so the color no
  longer needed to. `portrait:` is now optional in a fish's YAML
  record (falls back to a real wiki picture, or a plain gray
  placeholder if there's neither).
- Phase 3: the full 178-fish roster is in `data/` now, not just the 5
  demo groups -- every group from `reference/fish_grouping_scheme.md`
  (11 more Tier A, 16 more Tier B, 20 more Tier C, 12 more Tier D),
  each with map coordinates, a paraphrased description, and gear/bait
  notes sourced from `reference/guide_text.txt`. Coordinates are a
  first pass, not verified pixel-for-pixel against the game -- the
  same caveat `fish_grouping_scheme.md` already carried for its 8
  provisionally-placed fish now applies more broadly.
- Duo/feature map frames now compute their own aspect-ratio from the
  group's `view_box` (like cluster layout already did) instead of
  using a fixed CSS ratio that only matched the two original demo
  crops -- a mismatched ratio was cropping some new groups' markers
  off-screen via `preserveAspectRatio="slice"`. Map captions also
  truncate with an ellipsis instead of wrapping and overlapping when
  they're too long for a narrow crop.
- Removed the small colored "X" that sat next to a fish's name on
  duo/entry cards -- it used to match a fish to its map marker's
  color, which stopped meaning anything once every marker became one
  fixed red.
- Every group page now ends with a "↑ Back to top" link back to the
  start of the document.
- Fixed the index overflowing horizontally on narrow/mobile screens:
  a long destination title in the page-tag pill (now full group
  titles, not "Page X") was forcing its CSS Grid row wider than the
  screen, because a bare `1fr` track's implicit minimum is its
  content's width, not 0. `index-list` now uses `minmax(0,1fr)`
  tracks, and the tag/name both truncate with an ellipsis instead of
  forcing the row wider.
- Removed the map's caption bar (`.cap`) -- it covered terrain labels
  at the bottom of some crops and mostly repeated the group's own
  title/cast text.
- New `fishguide.terrain` module + three `validate.py` checks, backed
  by `assets/water_mask.png` (a static render of the terrain art) so
  they run without a browser: a fish's marker must sit on open water,
  not land (`Fish.on_land: true` is the documented exception for a
  spot that's genuinely on land/structure by game design); a lure
  path's straight segments must not cross land; a view_box must not
  crop a terrain label mid-word (`Group.label_crop_ok`/
  `path_crosses_land_ok` are the matching exceptions, used only for
  frozen/approved content that can't be adjusted). `terrain.py` also
  has `find_water_route()` (grid pathfinding + polyline simplification)
  and `nearest_water()`, used to fix every violation these checks
  found across the Phase 3 roster (2 marker-color/placement pairs,
  5 paths rerouted, 41 crops reshaped) and left in place to catch the
  same mistakes automatically for any fish added after.
- Duo/feature map markers now scale up when a group's view_box is far
  wider than the reference crop (e.g. a cross-map cooldown pair like
  Glacier & Magmer) -- otherwise a fixed-size X becomes nearly
  invisible once zoomed out that far.
- Map markers are the fish itself now, not a red X -- each marker draws
  that fish's own wiki picture (or, for the handful the wiki has none
  of, the same procedural portrait its entry card shows), outlined in
  white so it reads against the dark water. The pictures are embedded
  once as `<symbol>`s and `<use>`d per marker, so a fish marked at
  several coordinates doesn't carry several copies of its art.
- The "back to top" link now returns you to wherever you jumped from --
  usually the index row you clicked -- and only falls back to the top
  of the document when there's nowhere to go back to.
- Sinker, Bomb Stacker, Detonator, and Flick badges/gear now show the
  game's own black-and-white icon instead of a generic emoji, fetched
  from the wiki and recolored to the book's ink so they sit with the
  surrounding text rather than as bright colored tiles (see
  `assets/game_icons/fetch_game_icons.py`). A fifth icon, Diving Lure,
  is fetched too but nothing in `data/` uses that emoji yet. These five
  are the only equipment the wiki draws as one clean, reusable icon;
  bait, hook, net, and hat emoji are unchanged because the wiki only
  has per-fish-variant art for those, and an emoji still reads better
  than a guess.
- Fish pictures now declare their real image type in the data URI.
  Fandom serves many of its `.png` files as WebP and `fishwiki
  download` keeps the wiki's own filename, so every embedded picture
  was announcing `image/png` over WebP bytes and relying on the
  browser to sniff past it.

