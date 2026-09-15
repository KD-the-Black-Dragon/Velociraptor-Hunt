# Acceptance Report: spawn-requires-vore-types

**Date:** 2026-08-30  
**Scope:** Optional `spawn.requires_vore_types` AND-gate against run vore prefs; density target unchanged when gated; Sample Mod `entities.json` game-owned refresh.

## Automated verification

### Change-scoped

| Suite | Result |
|-------|--------|
| `tests/test_spawn_requires_vore_types_pr1.py` | passed |
| `tests/test_mod_seed_readme.py` (Sample Mod refresh + stock empty arrays) | passed |
| Related spawn / summon / entity load batches (PR1–PR2) | passed |

### Full suite

**Deferred** — full `pytest tests/` reserved for release-build anticipation; not run at archive.

## Manual verification

- PR1: density with restricted prefs, summons/arena/save — designer sign-off before PR2
- PR2: stock empty arrays (no visible gate), Sample Mod template refresh + `mod.state` preserved — designer sign-off before PR3

## Live specs / docs

- `openspec/specs/npc-data/spec.md` — spawn vore-type requirements + density filter step
- `openspec/specs/modding/spec.md` — Sample Mod game-owned `entities.json` refresh; field docs pointer
- `openspec/specs/vore/spec.md` — prefs also drive spawn eligibility (cross-link)
- `data/SCHEMA.md`, README Modding, `MODDING_README.txt`

## Key implementation

| Area | Change |
|------|--------|
| `SpawnConfig` / entity loader | Parse `spawn.requires_vore_types` |
| `meets_vore_type_requirements` + floor pools | Filter candidates; prefs from engine |
| `spawn_from_definition` | Returns `None` when gated |
| Stock `entities.json` | `"requires_vore_types": []` on every spawn |
| `seed_sample` | Refresh Sample Mod entities every launch; preserve `mod.state` |

## Outcome

**Accepted** (full-suite deferred). Archive to `openspec/changes/archive/2026-08-30-spawn-requires-vore-types/`.
