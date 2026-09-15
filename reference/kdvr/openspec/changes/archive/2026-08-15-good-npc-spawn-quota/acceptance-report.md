# Acceptance Report: good-npc-spawn-quota

**Date:** 2026-08-15  
**Scope:** Difficulty-driven good NPC spawn quota; 10–15 player-path placement band for new goods; per-instance follower descent combat buffs (melee + ranged).

## Automated verification

### Change-scoped

Targeted tests for quota, path band, and follower descent buffs (run during PR1 / addenda) — passed.

### Full suite

**Skipped** — designer did not request full-suite acceptance for this change.

## Manual verification

Designer playtest signed off (2026-08-15): looks good.

## Live specs

- `openspec/specs/npc-data/spec.md` — good spawn quota; placement band
- `openspec/specs/dungeon/spec.md` — followers, quota, descent buffs
- `openspec/specs/balance/spec.md` — `good_spawn_limit`
- `data/SCHEMA.md` — `good_spawn_limit` field

## Key implementation

| Area | Change |
|------|--------|
| `data/depth_scaling.json` | `good_spawn_limit` (Easier 3; others 2) |
| `src/spawn.py` | Good quota pass; density evil/neutral only; path band 10–15 |
| `src/systems/descent.py` | Follower descent buff stacks |
| `src/engine_floor.py` | Pass follower count; apply buffs once per descend |
| `src/constants.py` | Path band + buff deltas |

## Outcome

**Accepted.** Archived to `openspec/changes/archive/2026-08-15-good-npc-spawn-quota/`.
