# Acceptance Report: engulfed-flavor-text

**Date:** 2026-08-30  
**Scope:** Optional per-entity `engulfed_flavor` (OV/CV/AV string arrays); every 3rd completed world phase while the player is engulfed, log one random typed line in SPEECH (bright white); missing/empty → silent no-op.

## Automated verification

### Change-scoped

| Suite | Result |
|-------|--------|
| `tests/test_engulfed_flavor_pr1.py` | passed |
| `tests/test_engulfed_flavor_pr2.py` | passed |
| Related data / predator save round-trip | passed during PRs |

### Full suite

**Deferred** — full `pytest tests/` reserved for release-build anticipation; not run at archive.

## Manual verification

- PR1: data load / SCHEMA
- PR2: emit cadence (playtest with temporary mod content; stock entities ship without fills)

## Live specs / docs

- `openspec/specs/vore/spec.md` — Engulfed flavor text requirement
- `data/SCHEMA.md` — `engulfed_flavor` field + shape

## Key implementation

| Area | Change |
|------|--------|
| `entity_loader` / `EntityDefinition` | Parse `engulfed_flavor` (empty OK) |
| `narrative_index` | lines / pick helpers |
| `Predator.engulfed_flavor_phases` | Counter + save |
| `systems/engulfed_flavor.py` | Emit after `run_world_turn` |

## Outcome

**Accepted** (full-suite deferred). Archive to `openspec/changes/archive/2026-08-30-engulfed-flavor-text/`.
