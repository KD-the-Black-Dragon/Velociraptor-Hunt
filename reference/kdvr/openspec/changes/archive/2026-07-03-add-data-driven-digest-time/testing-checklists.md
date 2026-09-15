# Testing checklists: add-data-driven-digest-time

## PR0 — Mechanics

See `testing-checklist-pr0.md`.

- [x] Default digest_time **6** for evil without JSON field
- [x] Strike threshold read from `DigestionStats.digest_time`
- [x] Fixture-backed tests; no hardcoded production balance assertions

## PR1 — Content and acceptance

See `testing-checklist-pr1.md`.

- [x] Wolf `digest_time: 3` in play
- [x] Shark `digest_time: 10` in play
- [x] `data/SCHEMA.md` documents field
- [x] Full `pytest tests/` skipped (user-approved; targeted gate green)