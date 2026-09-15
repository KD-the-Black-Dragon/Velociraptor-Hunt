# Acceptance Report: add-depth-jump-start

**Date:** 2026-07-12  
**Scope:** PR1 — secret Ctrl+G depth-jump new game with data-driven loadout and `level_warped` past-runs exclusion.

## Automated verification

### Change-scoped suite

```bash
python -m pytest tests/test_depth_jump_pr1.py -v
```

**8/8** passed.

### Full suite (step 1 — parallel, 4 workers)

```bash
python -m pytest tests/ -v -n 4
```

| Result | Count |
|--------|-------|
| **PASS** | **1602** |
| **FAIL** | **3** |
| Skipped | 2 |

### Serial rerun of step-1 failures (step 4)

| Test | Step 1 | Step 4 serial |
|------|--------|---------------|
| `test_initialize_floor_regenerates_on_rune_placement_failure` | FAIL | FAIL |
| `test_engine_post_turn_hook_invokes_coordinator` | FAIL | PASS |
| `test_vore_modal_drawn_on_root_console_over_sidebar` | FAIL | PASS |

Two xdist flakes; one **failed-twice** (`GameEngine.__new__` partial engine lacked `depth_jump_start_depth`).

### Failed-twice fix (step 7)

| Test | Fix |
|------|-----|
| `test_initialize_floor_regenerates_on_rune_placement_failure` | `spawn_player` uses `getattr(engine, "depth_jump_start_depth", None)` |

### Step 9 — serial rerun of step-1 failure set + depth-jump

```bash
python -m pytest <3 failures> tests/test_depth_jump_pr1.py -v
```

**11/11** passed.

## Manual verification

- [x] PR1 — designer sign-off (*"PR1 looks good."*)

## Requirement coverage

| Deliverable | Status |
|-------------|--------|
| Ctrl+G on main menu → name → depth entry | Shipped |
| Depth 1 = normal New Game | Shipped |
| Depth 2–20 with synthesized loadout | Shipped |
| Loot depth = target − 1; data-driven eligibility | Shipped |
| Simulated runes (⅔–100% of `runes_per_floor` per prior floor) | Shipped |
| `level_warped` excludes past-runs append | Shipped |
| `data/depth_jump_start.json` + loader | Shipped |
| `openspec/specs/depth-jump-start/spec.md` | Shipped |

## Spec updates

- `openspec/specs/depth-jump-start/spec.md` (new)
- `openspec/specs/modding/spec.md` — `depth_jump_start.json` whole-file replace (stock loader only until mod pipeline)
- `data/SCHEMA.md` — `depth_jump_start.json` section + modding table

## Notes

- Mod pipeline does not yet layer `depth_jump_start.json` from enabled mods; core `data/` only (documented in modding spec).