# Design: add-ally-improvement

Full design document: `openspec/design-work/6c35498a-design-doc.md`

## Summary

Three good-ally features: runtime name introductions (`names.json` + `entities.json` `introduction`), player-engulfed rescue priority in `pick_good_chase()`, and player-only rescue gratitude in `release_npc_engulfed()`.

## Data files

| File | Purpose |
|------|---------|
| `data/names.json` | Per-entity-id proper name pools |
| `data/rescue_gratitude.json` | Shared gratitude line pool (`{name}` placeholder) |
| `data/entities.json` | Optional `introduction` string arrays per entity |

## Hooks

`_consume_player_turn()` order: regen → `_update_fov()` → `try_good_introductions()` → `fire_player_turn_consumed()` → `_run_world_turn()` (skipped when digestion modal).

- `GameEngine._consume_player_turn()` → `try_good_introductions()` (runs even when `skip_world=True`; no introductions while player is `Engulfed`)
- `pick_good_chase()` → top priority: predator from `find_predator_holding_prey(world, player)` when LOS
- `_perform_attack()` / `perform_wand_attack()` → `release_prey_if_defeated_predator(..., rng=, rescuer=)` → gratitude in `release_npc_engulfed()` (good prey only)

## Registry wiring

| Registry | Access |
|----------|--------|
| Names | `get_names_registry()` / `reset_names_registry()` (PR0) |
| Gratitude | `get_rescue_gratitude_registry()` / `reset_rescue_gratitude_registry()` (PR0) |
| Entities | `load_entity_registry()` per call (no global cache) |

Gratitude line picker: `src/data/ally_content.py`. Introduction logic: `src/systems/ally_introduction.py`.

## Evil-clear (introductions)

- Player: `game_map.visible` after `_update_fov()`
- Ally: `_visible_good_evils()` (existing LOS)

## Deferred

Command Allies — see `openspec/changes/deferred-add-command-allies/`.