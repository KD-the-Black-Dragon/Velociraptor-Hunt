# Acceptance Report: add-balance-knobs

**Date:** 2026-07-09  
**Scope:** Difficulty presets, dual-int depth scaling, density/rune economy, piece-based floor runes, NPC prefixes (Elite), placeholder fillers, Past Runs difficulty (PR0–PR6).

## Automated verification

### Change-scoped

```bash
python -m pytest tests/test_depth_scaling_pr1.py tests/test_balance_pr1b.py tests/test_floor_runes_pieces_pr2.py tests/test_runes_per_floor_pr3.py tests/test_npc_prefixes_pr4.py tests/test_entity_placeholder_pr4b.py tests/test_options_fullscreen.py -v -n 6
```

| Result | Detail |
|--------|--------|
| **PASS** | 70 tests |

### Full suite

```bash
python -m pytest tests/ -n 6 --tb=line -q
```

| Result | Count |
|--------|-------|
| Passed (first run) | 1315 |
| Failed (first run) | 3 |
| Skipped | 2 |
| Duration | ~9m 24s |

**First-run failures (fixed, then re-run only failures):**

| Test | Cause | Fix |
|------|--------|-----|
| `test_engine_take_or_generate_uses_prefetch` | Bare `GameEngine.__new__` lacked `difficulty_id`; `runes_per_floor()` needs it | Set `difficulty_id = "normal"` on stub engine |
| `test_initialize_floor_regenerates_on_rune_placement_failure` | Same | Same |
| `test_coalesces_pending_snapshots_while_save_in_flight` | Default `turn_interval=15` never met by turns 10–14 | Explicit `turn_interval=5` in test |

**Product fix found during acceptance:** `_dungeon_gen_kwargs` now passes `runes_per_floor` so sync map gen matches difficulty overrides (prefetch already did).

Re-run of the three failures + balance suite: **all PASS**.

## Manual verification

Designer signed off PR5 content tune (playtest). Earlier PR checklists (mechanics) covered by cumulative play and PR5 sign-off.

## Live specs

| Spec | Notes |
|------|--------|
| `openspec/specs/balance/spec.md` | **New** — difficulties, depth bake, prefixes, Past Runs |
| `openspec/specs/floor-runes/spec.md` | Pieces banks; `runes_per_floor`; difficulty override |
| `openspec/specs/npc-data/spec.md` | Placeholder flag |
| `openspec/specs/past-runs/spec.md` | Difficulty on board |
| `openspec/specs/modding/spec.md` | Whole-file `depth_scaling.json`, `npc_prefixes.json` |

## Stock content (PR5)

| File | Tune |
|------|------|
| `data/depth_scaling.json` | Easy–Nightmare curves, density, runes, pieces mult, prefix_spawn |
| `data/npc_prefixes.json` | Stock `elite` flats |
| `data/floor_runes.json` | Warding `pieces_per_bonus: 2` |
| `data/entities.json` | Placeholders: cave_rat, giant_spider, kobold, tunnel_slug |
