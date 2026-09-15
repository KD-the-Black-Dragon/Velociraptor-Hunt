# Acceptance Report: add-thrown-weapons-and-ranged-pathing

**Date:** 2026-07-11  
**Scope:** Smite vs Path ranged targeting, player throwables (`f` / `F`), NPC `RangeN` Path AI, projectile animation, 9-throwable catalog, fox archer `Range5`, live specs (PR1–PR8).

## Automated verification

### Full suite (step 1 — parallel, 4 workers)

```bash
python -m pytest tests/ -v -n 4
```

| Result | Count |
|--------|-------|
| **PASS** | **1442** |
| **FAIL** | **8** |
| Skipped | 2 |

### Failed-twice fixes (steps 4–7)

Four cases failed on both parallel and serial reruns; fixed:

| Test | Fix |
|------|-----|
| `test_engine_comma_manual_pickup` | Starter rocks occupy slot `c`; pickup dagger → slot `d` |
| `test_engine_receives_saved_ui_preset` | Wide preset map 44 / sidebar 36 (sidebar column PR) |
| `test_load_active_layout_uses_settings_preset` | Wide preset map viewport `w == 44` |
| `test_miss_resumes_at_next_monster_index` | `isolate_other_ais` for deterministic wolf ordering |

Four cases recovered on serial rerun (xdist flake): memory pursuit, save coordinator, vore mercy, vore turn after miss.

### Post-fix gate

```bash
python -m pytest tests/test_inventory_items_pr1.py::test_engine_comma_manual_pickup \
  tests/test_options_menu.py::test_engine_receives_saved_ui_preset \
  tests/test_ui_bootstrap.py::test_load_active_layout_uses_settings_preset \
  tests/test_vore_turn_order.py::test_miss_resumes_at_next_monster_index \
  tests/test_memory_pursuit_door_detour.py::test_memory_trail_timeout_gives_up_without_los \
  tests/test_save_coordinator.py::test_engine_post_turn_hook_invokes_coordinator \
  tests/test_vore_struggle.py::test_vore_mercy_cleared_after_world_turn \
  tests/test_vore_turn_order.py::test_after_miss_complete_next_player_turn_starts_from_zero \
  tests/test_ranged_path.py tests/test_player_throw_pr6.py tests/test_throwables_pr5.py \
  tests/test_throwables_pr7.py tests/test_projectile_anim.py \
  tests/test_npc_abilities_range_path.py tests/test_npc_abilities_smite.py \
  tests/test_ability_parser.py -v
```

All targeted cases **PASS**.

### Change-scoped tests (PR1–PR7)

| Area | Files |
|------|-------|
| Parser / Smite | `test_ability_parser.py`, `test_npc_abilities_smite.py` |
| Path core | `test_ranged_path.py` |
| NPC Path AI | `test_npc_abilities_range_path.py` |
| Animation | `test_projectile_anim.py` |
| Throwables | `test_throwables_pr5.py`, `test_throwables_pr7.py` |
| Player throw | `test_player_throw_pr6.py` |

## Manual verification

- [x] PR1–PR7 — user sign-off across session (throw UX, anim timing, content)
- [x] PR8 — final acceptance authorized (*"All looks good. Proceed with next PR."*)

## Requirement coverage

| Deliverable | Status |
|-------------|--------|
| `SmiteN` rename + smite logs | Shipped |
| `RangeN` Path beam + shoot logs | Shipped |
| Player `f` / `F` throw with Path resolve | Shipped |
| Starter 5 rocks slot `c` | Shipped |
| 9 throwables depth 1–20 | Shipped |
| Fox archer `Range5` | Shipped |
| Cyan Path / magenta Smite projectile anim | Shipped |
| Player throw defers world turn until anim ends | Shipped |
| Help overlay `f` / `F` | Shipped |

## Spec updates

- **New:** `openspec/specs/ranged-targeting/spec.md`
- **Updated:** `openspec/specs/inventory-items/spec.md`, `equipment-catalog/spec.md`, `npc-abilities/spec.md`

## Out of scope (confirmed)

- Bows, slings, crossbows, throwable recovery
- Mod aliases for old `RangeN` Smite tokens
- Erratic + ranged combination