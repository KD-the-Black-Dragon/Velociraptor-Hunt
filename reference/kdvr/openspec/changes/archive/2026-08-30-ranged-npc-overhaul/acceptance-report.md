# Acceptance Report: ranged-npc-overhaul

**Date:** 2026-08-30  
**Scope:** Good ally ranged damage half (JSON); difficulty `good_ranged_shots` / `evil_ranged_shots`; NPC Path/Smite magazine + silent reload; evil hunger-close AI; good ally top-up when no enemy in sight.

## Automated verification

### Change-scoped

| Suite | Result |
|-------|--------|
| `tests/test_ranged_npc_overhaul_pr1.py` | passed |
| `tests/test_ranged_npc_overhaul_pr2.py` | passed |
| `tests/test_ranged_npc_overhaul_pr3.py` | passed |
| Related smite / path / no-kite regressions | passed (55 green with PR2/PR3 batch) |

### Full suite

**Deferred** — full `pytest tests/` reserved for release-build anticipation; not run at archive.

## Manual verification

- PR1: ally damage + depth_scaling knobs (rolled into combined playtest)
- PR2+PR3: magazine cadence, good top-up, evil hunger, centaur adjacent no-shoot, save/load — designer sign-off **All good**

## Live specs / docs

- `openspec/specs/npc-abilities/spec.md` — NPC Path/Smite magazine requirement  
- `openspec/specs/balance/spec.md` — `good_ranged_shots` / `evil_ranged_shots`  
- `openspec/specs/ranged-targeting/spec.md` — cross-ref (player unchanged)  
- `data/SCHEMA.md` — difficulty fields (PR1)

## Key implementation

| Area | Change |
|------|--------|
| `entities.json` | `ram_crossbow` 4–5; `sheep_cleric` 5–6 |
| `depth_scaling.json` / loader | shot knobs; nightmare evil **3** |
| `RangedMagazine` + `ranged_magazine.py` | spawn, spend, reload |
| `abilities.py` / `visit.py` | gate shots; hunger approach; reload AI |
| `save/codec.py` | persist; soft-fill missing |

## Outcome

**Accepted** (full-suite deferred). Archive to `openspec/changes/archive/2026-08-30-ranged-npc-overhaul/`.
