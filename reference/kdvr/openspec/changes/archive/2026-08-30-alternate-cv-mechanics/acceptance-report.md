# Acceptance Report: alternate-cv-mechanics

**Date:** 2026-08-30  
**Scope:** Options **Alternate CV Mechanics** (No/Yes, snapshotted at New Game); per-difficulty `cv_daze_*` in `depth_scaling.json`; NPC **Dazed** status; when On + CV — zero struggle damage, daze on player CV escape and NPC CV digest-complete.

## Automated verification

### Change-scoped

| Suite | Result |
|-------|--------|
| `tests/test_dazed_pr1.py` | passed |
| `tests/test_alternate_cv_pr2.py` | passed |
| `tests/test_alternate_cv_pr3.py` | passed |
| `tests/test_vore_struggle.py` | passed (with PR3) |
| Related Options / depth_scaling / save dazed round-trip | passed during PRs |

### Full suite

**Deferred by designer** — full `pytest tests/` reserved for release-build anticipation; not run at archive for this change.

## Manual verification

Designer playtest / sign-off across PRs:

- PR1: Dazed foundation (automated + regression smoke)
- PR2: Options No/Yes + depth_scaling knobs + run snapshot
- PR3: Alternate CV struggle / escape daze / NPC CV digest daze; sentence capitalization for daze messages
- PR4: live specs + docs

## Live specs / docs

- `openspec/specs/vore/spec.md` — Alternate CV Mechanics
- `openspec/specs/digestion/spec.md` — Dazed; CV digest-complete daze
- `openspec/specs/main-menu/spec.md` — Options row + New Game snapshot
- `README.md` — Options mention
- `data/SCHEMA.md` — `cv_daze_min_turns` / `cv_daze_max_turns`

## Key implementation

| Area | Change |
|------|--------|
| `src/components.py` | `Dazed(remaining)` |
| `src/systems/dazed.py` | apply/tick/roll; sentence-start names |
| `src/systems/vore.py` | Alternate CV struggle + escape daze |
| `src/systems/digestion.py` | CV NPC digest-complete daze |
| `src/settings_store.py` / `options_menu.py` | Settings + Options No/Yes |
| `src/engine.py` / `save/snapshot.py` | Run snapshot flag |
| `data/depth_scaling.json` | 5/5 on all difficulties |

## Outcome

**Accepted** (full-suite deferred). Archive to `openspec/changes/archive/2026-08-30-alternate-cv-mechanics/`.
