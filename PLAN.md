# Cat Goes Fishing Field Guide — Python Build Plan

## What this project is

A printed, Pokémon-handbook-style field guide for the game *Cat Goes Fishing*: 178 fish
organized onto ~64 themed map pages (plus spillover pages), where each page shows a slice of
the world map with an **X** marking each fish, a dashed path for any special approach, per-fish
entries with original portrait art, and a size-organized index at the back.

The design is **already approved** — `reference/design_preview.html` is the visual source of
truth (5 sample pages + index, one per grouping tier). The job now is to turn the ad-hoc
HTML-editing workflow that produced it into a proper Python build system that can generate the
whole book from data files.

## What's in this starter kit

| Path | What it is |
|---|---|
| `reference/design_preview.html` | Approved mockup. All CSS, page layouts, and components live here. Treat as pixel-parity target. |
| `reference/fish_grouping_scheme.md` | The full 178-fish grouping: tiers A–D, every group, every fish, page counts. This is the book's table of contents in data form. |
| `reference/guide_text.txt` | Compiled community-guide text (all 38 pages). Source material for descriptions — **paraphrase, never copy verbatim**. |
| `assets/map_terrain_defs.html` | The world-map SVG as a hidden `<defs><g id="mapTerrain">` block. Pages embed crops via `<use href="#mapTerrain"/>` + a `viewBox`. |
| `src_seed/fish_art.py` | Working procedural fish-portrait generator (flat cartoon SVG, fixed 160×120 / 4:3 frame). 19 species parameterized so far in `fish_params.json`. |
| `src_seed/markers.py` | Working map-marker helpers: `x_mark`, `small_x_mark`, `numbered_pin`, `start_dot`, `dashed_path` (with end-trimming), `legend_x`. |
| `src_seed/color_assign.json` | Marker color assignments for the demo groups (shows the palette cycle in use). |

## Target repo structure

```
fishguide/
├── data/
│   ├── groups.yaml            # ordered list of groups: id, title, tier, layout, viewBox,
│   │                          #   cast line, shared gear, badges, max_entries_with_map
│   ├── fish/                  # one YAML per group, containing that group's fish records
│   │   ├── a_trick_and_treat.yaml
│   │   ├── b_silo_depths_1.yaml
│   │   └── ...
│   └── palette.yaml           # marker color cycle + size-category pill styles
├── assets/
│   └── map_terrain_defs.html
├── src/fishguide/
│   ├── models.py              # dataclasses or Pydantic: Fish, Group, PageSpec, BookSpec
│   ├── art.py                 # ported from src_seed/fish_art.py
│   ├── markers.py             # ported from src_seed/markers.py
│   ├── layout.py              # splits a group into map-page + continuation pages
│   ├── paginate.py            # assigns final page numbers; builds the index model
│   ├── validate.py            # all build-blocking checks (see Validation)
│   ├── render.py              # Jinja2 rendering to HTML
│   ├── pdf.py                 # Playwright print-to-PDF
│   └── cli.py                 # `fishguide build | validate | preview <group> | pdf`
├── templates/
│   ├── base.html.j2           # shell + the full CSS from design_preview.html
│   ├── page_feature.html.j2   # Tier C solo layout   (l1: map left, text right)
│   ├── page_duo.html.j2       # Tier A duo layout    (l2: wide map, duo cards, shared instructions)
│   ├── page_cluster.html.j2   # Tier B/D grid layout (l3: tall map, entry-card grid, gear footer)
│   ├── page_continuation.html.j2  # spillover page (cont-banner, entries, no map)
│   ├── index.html.j2          # size-organized index
│   └── partials/ (entry_card, fish_pic, gear_list, banner, cast_strip)
├── tests/
│   ├── test_validate.py
│   ├── test_layout.py
│   └── test_golden.py         # screenshot-diff the 5 demo pages against reference
├── build/                     # output (gitignored)
└── pyproject.toml
```

Dependencies: `jinja2`, `pyyaml`, `pydantic` (or dataclasses), `playwright` (screenshots + PDF),
`pytest`, `pillow` (golden-image diffing). All pure Python, no Node.

## Data model

```yaml
# data/fish/b_silo_depths_1.yaml  (one fish shown)
- key: bitterfish
  name: Bitterfish
  size: medium          # small | medium | large | huge | secret
  coords: [665, 75]     # in the 1568×251 map space
  about: >
    Pale pink and shaped like a gulper eel, drifting through the
    mid-to-shallow water above the Silo...
  stats:
    - {icon: "🪱", label: "Bait", value: "Any/Small"}
  portrait:             # kwargs passed straight to art.fish()
    body_color: "#e8b6c4"
    shape: elongated
    tail: small
    eye: cute
    mouth: open
```

```yaml
# data/groups.yaml (one group shown)
- id: b_silo_depths_1
  title: "Silo Depths I"
  tier: B                       # A=mechanical duo, B=cluster, C=solo, D=roundup
  layout: cluster               # feature | duo | cluster
  subtitle: "Medium Fish · Five Entries"
  badges: [{text: "Medium Fish", kind: cat}, {text: "Easy", kind: diff-easy}]
  cast: "Position over the Silo and work your line from mid-depth down to the very bottom."
  viewBox: "640 0 200 251"
  map_caption: "Above the Silo — shallow to very deep"
  max_entries_with_map: 5       # beyond this → continuation pages (~6/page)
  shared_gear:
    - {icon: "🪱", text: "Medium bait", required: true}
  # optional for duo/feature pages:
  path: {points: [[400,25],[480,45],[695,20]], start_gap: 11, end_gap: 11}
  special_instructions: "..."
```

Rules already decided in design sessions (encode these in `layout.py` / `models.py`):
- Marker colors are auto-assigned per group from the palette cycle, in fish order:
  `#e8462c, #2b6cd4, #d99a1b, #7a4fb0, #1f9e6d, #d94f96, #1fa7c9`. A fish keeps its color on
  continuation pages even though there's no map there.
- Single-fish maps (Tier C) don't need the multi-color treatment; a signature color per fish is
  fine (Underfin uses `#1a1a1a`).
- **Torby and Cowfish**: one write-up entry each, but two X's on their map (same species, two
  spots).
- Entries live on the same page as the map when they fit; observed threshold is ~5 fuller
  entry-cards alongside a map. 7 fish → 4 with the map + 3 on a continuation page.
- Fish portraits are always the fixed 4:3 frame (`FISH_VB = "0 0 160 120"`); never change the
  ratio.

## Build pipeline (`fishguide build`)

1. Load `groups.yaml` + all `data/fish/*.yaml` → validated models.
2. Auto-assign marker colors per group; render marker SVG per map (via `markers.py`).
3. `layout.py`: split each group into `[MapPage, ContinuationPage...]` using
   `max_entries_with_map` (default 5) and continuation capacity (default 6).
4. `paginate.py`: walk groups in `groups.yaml` order → final page numbers; build the index
   model grouped **by size category in this order: Small, Medium, Large, Huge, Secret**, each
   entry = portrait thumb + name + real page number + marker-color stripe.
5. `render.py`: Jinja2 → `build/book.html` (single scrolling file, one `.page` per book page,
   `map_terrain_defs.html` embedded once at the bottom).
6. `fishguide pdf`: Playwright print-to-PDF at chosen trim size (decide letter vs A5 in Phase 4;
   add `@media print` page-break rules so each `.page` lands on its own sheet).

## Validation (`fishguide validate` — all of these fail the build)

- **Marker safe area** (this was a real bug — Underfin's X rendered off-screen):
  every marker/path point must satisfy `18 ≤ y ≤ 225` in the 251-tall map space, and stay
  ≥ 12 units inside the group's viewBox horizontally. Reason: `.map-crop` applies
  `transform: scale(1.045)` (hides tile seams) which pushes edge content outside the frame, and
  the caption bar covers roughly the bottom 12–14 units. Never rely on eyeballing this again.
- Every one of the 178 fish appears in exactly one group; roster totals reconcile with
  `fish_grouping_scheme.md` (12+17+21+14 groups, 27+68+21+62 fish).
- No duplicate marker colors within one group's map.
- Every fish has portrait params (else build fails listing the missing ones).
- Index page references match `paginate.py`'s computed numbers (self-consistency check).
- `viewBox` heights are always 251 (map content ends at y=251; below is blank in the source).

## Phases (each ends with something runnable)

**Phase 1 — Parity.** Scaffold the repo, port `fish_art.py`/`markers.py`, write models +
loaders, hand-transcribe the 5 demo groups + index into `data/`, and render them.
*Acceptance: Playwright screenshots of the generated pages are visually equivalent to
`reference/design_preview.html` (golden-file test, small pixel tolerance).*

**Phase 2 — Engine.** All four layouts templated, continuation-page splitting, pagination,
index generation, and the full validator suite with pytest coverage.
*Acceptance: `fishguide validate` catches seeded errors (bad y-coord, duplicate fish, missing
portrait); demo book builds with correct auto page numbers.*

**Phase 3 — Content at scale.** Data entry for all 178 fish, working region by region using
`reference/fish_grouping_scheme.md` as the checklist and `reference/guide_text.txt` as source
material (paraphrased). Portrait params authored per fish (~160 new). Expect several sessions;
build in slices so the book always compiles.
*Acceptance: validator passes with the full roster; index shows 178 entries.*

**Phase 4 — Print.** PDF export, trim size decision, `@media print` page breaks, front matter
(cover, "how to read this book" page explaining tiers/markers/colors, credits page).
*Acceptance: a print-ready PDF where every `.page` is one sheet and maps are legible at size.*

## Known open items (Phase 3 status)

Phase 3 is done in the sense that all 178 fish are in `data/` with coordinates, descriptions,
and gear notes — but none of it is verified against the actual game, only against
`fish_grouping_scheme.md` and `guide_text.txt`. Treat every coordinate as provisional until
someone checks it in-game; the specific "8 fish need re-verification" list from the original
plan no longer means anything narrower than that.

- Size categories for the Dragon Area roundup fish (Dragonfish/Carver/Conpas/Ghast) were
  inferred from bait size, not stated by the guide — verify.
- Fish portraits: most fish use a real picture from `assets/wiki_fish/` (the `fishguide-wiki`
  package) instead of `art.fish()` params now — that need is mostly gone. A handful the wiki
  has no picture for (Treat, Underfin, Maw, Kernel, Noxius, Mask Fish, Elder Orwellian, Airy,
  Bird, Josie, Forebearer) got a hand-picked procedural `portrait:` fallback instead.
- Two pin placements inherited from the original 5-group demo sit right at the map's bottom
  edge (Conpas, Maw) — left as-is to match the approved mockup byte-for-byte; every other
  fish's numbered pin was checked to stay on-screen.
