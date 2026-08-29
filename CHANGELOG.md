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
