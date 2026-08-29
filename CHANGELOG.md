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
