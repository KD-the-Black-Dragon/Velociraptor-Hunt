# Tasks: Implement Core Roguelike

## 1. Project Scaffold

- [x] 1.1 Create `pyproject.toml` with Python 3.11+, `tcod`, and `numpy` dependencies
- [x] 1.2 Create `src/` package with `main.py` entry point and window title **KD's Vore Roguelike**
- [x] 1.3 Verify `python -m src.main` opens a blank libtcod window and exits on Escape

## 2. Map and Tiles

- [x] 2.1 Implement `Tile` enum and `GameMap` with walkability, transparency, and explored/visible arrays
- [x] 2.2 Implement room-and-corridor generator in `map_gen.py`
- [x] 2.3 Render static map tiles (wall/floor, explored dimming) in `render.py`

## 3. ECS Foundation

- [x] 3.1 Define components in `components.py` (`Position`, `Renderable`, `Player`, `Fighter`, `Stunned`, `AI`, `Item`, `Inventory`, `BlocksMovement`)
- [x] 3.2 Create `GameEngine` with `tcod.ecs.Registry`, spawn player in first room
- [x] 3.3 Add `MessageLog` and `events.py` callback stubs

## 4. Player Movement and Input

- [x] 4.1 Map arrow/numpad/vi keys to 8 directions in `input_handlers.py`
- [x] 4.2 Implement movement with wall blocking and diagonal corner-cutting rule
- [x] 4.3 Ignore movement keys when player has `Stunned` tag (no turn advance)

## 5. Field of View

- [x] 5.1 Implement FOV recompute from player position after each turn
- [x] 5.2 Only draw entity glyphs on visible tiles; keep explored floor visible when hidden

## 6. Monsters and AI

- [x] 6.1 Spawn 3–5 monsters on walkable tiles away from player at game start
- [x] 6.2 Implement chase AI: one step toward player when in FOV, else idle
- [x] 6.3 Run all monster turns after each player turn that consumes an action

## 7. Combat

- [x] 7.1 Implement bump-to-attack when moving into monster tile (player does not occupy tile)
- [x] 7.2 Apply damage formula; defeat monster at 0 HP (delete entity, log "defeated")
- [x] 7.3 Monster bump into player deals damage; at 0 HP add `Stunned` tag, log stunned message
- [x] 7.4 Clear `Stunned` when player HP rises above 0
- [x] 7.5 Fire `on_entity_defeated` and `on_player_stunned` event hooks

## 8. Items and Inventory

- [x] 8.1 Spawn at least one health potion (`!`) on the floor
- [x] 8.2 Pickup on walk-over into lowest free `a`–`z` slot; reject when all 26 full
- [x] 8.3 Letter keys use slot contents; potion restores HP and empties slot
- [x] 8.4 Item use works while stunned and advances a turn
- [x] 8.5 Fire `on_item_used` event hook

## 9. HUD and Polish

- [x] 9.1 Render HP and stunned indicator in HUD
- [x] 9.2 Render message log (last N messages)
- [x] 9.3 Audit all user-facing strings for defeated/stunned terminology (no kill/die)

## 10. Acceptance Verification

- [x] 10.1 Walk through all 9 acceptance criteria in `openspec/specs/core-roguelike/spec.md`
- [x] 10.2 Confirm game is playable with no vore module present