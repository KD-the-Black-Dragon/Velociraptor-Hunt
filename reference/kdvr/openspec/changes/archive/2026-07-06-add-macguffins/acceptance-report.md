# Acceptance Report: add-macguffins

**Date:** 2026-07-06  
**Scope:** Victory floor objects (macguffins): data catalog, spawn, step-on activation, Y/n victory modal, discovery persistence, game over, digestion override (PR0–PR5). Cosmetic: blank line between victory prompt sentences.

## Automated verification

### Change gate (macguffins)

```bash
python -m pytest tests/test_macguffins_pr1.py tests/test_macguffins_pr2.py tests/test_macguffins_pr3.py tests/test_macguffins_pr4.py tests/test_game_over_ending.py -q
```

| Result | Count |
|--------|-------|
| **PASS** | **50** |

### Full suite

```bash
python -m pytest tests/ -q --tb=no
```

| Result | Count |
|--------|-------|
| Passed | 1000 |
| Failed | 4 |
| Warnings | 111 |
| Duration | ~31m 50s |

**Failures (pre-existing, not introduced by this change):**

- `tests/test_digestion.py::test_engulfed_player_immune_to_combat_damage`
- `tests/test_dungeon_spawn_config.py::test_load_default_dungeon_spawn_json`
- `tests/test_npc_data_pr1.py::test_load_default_entities_json`
- `tests/test_vore_engulfed.py::test_roaming_wolf_wanders_while_player_engulfed`

No failures in the macguffins change gate.

## Manual verification

- [x] PR1–PR4 playtest sign-off (user)
- [x] Victory prompt blank line between sentences (user)
- [x] PR5 acceptance sign-off (user)

## Requirement coverage

| PR | Delivered |
|----|-----------|
| PR0 | OpenSpec bootstrap; design; task checklists |
| PR1 | `data/macguffins.json`; loader/registry; SCHEMA; tests |
| PR2 | Spawn after runes; movement passthrough; entity codec; map feasibility |
| PR3 | Step-on; Y/n modal; discovery snapshot; deferred turn |
| PR4 | Victory game over; digestion override; formatter; `macguffin_score` |
| PR5 | Live `macguffins` spec; related spec sync; README; archive |

## Spec updates

- `openspec/specs/macguffins/spec.md` — **new**
- `openspec/specs/floor-runs/spec.md` — spawn order; shared placement
- `openspec/specs/past-runs/spec.md` — macguffin ending format; `macguffin_score` field
- `openspec/specs/save-load/spec.md` — `macguffin_discovery` snapshot; ephemeral victory modal
- `openspec/specs/digestion/spec.md` — macguffin override on game over
- `data/SCHEMA.md` — macguffins section (PR1)
- `README.md` — modding macguffins pointer

## Files touched (summary)

| Area | Path |
|------|------|
| Data | `data/macguffins.json` |
| Loader | `src/data/macguffin_loader.py`, `macguffin_registry.py` |
| Systems | `src/systems/macguffins.py` |
| UI / state | `src/macguffin_victory_confirm.py`, `src/macguffin_discovery.py` |
| Engine | `src/engine.py` |
| Endings | `src/game_over_ending.py`, `src/systems/digestion.py` |
| Persistence | `src/save/snapshot.py`, `src/save/codec.py`, `src/past_runs/schema.py` |
| Tests | `tests/test_macguffins_pr1.py` … `pr4.py`, `tests/macguffin_test_helpers.py` |