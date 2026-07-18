# core-roguelike Specification

## Purpose

KD's Vore Roguelike is a minimal **turn-based dungeon crawler** built in Python with libtcod. Version 1 delivers procedurally generated dungeon floors, keyboard movement, field-of-view exploration, simple monster AI, bump combat, and a **26-slot inventory** managed through **category commands** (see `openspec/specs/inventory-items/spec.md`).

**Combat outcome model**

- Monsters reduced to 0 HP are **defeated** and removed from the map.
- The player reduced to 0 HP is **stunned** (incapacitated) and remains on the map.
- The player at 0 HP is **stunned** by default. **Player digestion** and game over require the vore + **digestion** domains (`openspec/specs/digestion/spec.md`).

**Terminology (project-wide)**

| Term | Meaning |
|------|---------|
| Defeated | Monster reaches 0 HP and is removed |
| Stunned | Player reaches 0 HP; cannot move or attack; may wait, use items, or pass time via movement/wait keys (see `enhancements-1`) |
| Digested | Player defeat via digestion after engulf (see `digestion` spec) |

Avoid *death*, *kill*, and *die* in specs, UI, and log messages.

**Out of scope for v1**

- Vore attack mechanics (see `vore` spec); digestion and game over (see `digestion` spec)
- Meta-progression beyond run-local save (see `save-load` spec for single-slot autosave)
- Loot tables and procedural item variety beyond stock JSON items
- Meta-progression and scoring

**Dungeon extension (shipped):** multi-floor descent, deep water, mobility, mixed map generation, and stairs are specified in `openspec/specs/dungeon/spec.md`. Core walkability, FOV, and turn loop contracts remain stable.

**Shipped extensions**

Vore mechanics ship in `openspec/specs/vore/spec.md` (`src/systems/vore.py`). Core movement, FOV, and inventory contracts remain stable; vore attaches through optional ECS components, engine modal state, and events. `VORE_ENABLED = False` disables vore **behavior** without removing code.

Enhancements 2 (`openspec/specs/enhancements-2/spec.md`) moved quit to **`Ctrl+Q`** and made **Escape** cancel examine only. **Main menu** (`openspec/specs/main-menu/spec.md`) supersedes immediate quit: the app boots to the menu; **`Ctrl+Q` on the menu is a no-op**; **`Ctrl+Q` during gameplay** opens quit confirmation (`Y` → menu, `n` → resume); **modals** (vore, digestion, recap) treat **Ctrl+Q as no-op** (Enter only).

**Dungeon** (`openspec/specs/dungeon/spec.md`) extends map generation with mixed rooms/caverns/corridors, probabilistic deep water, three downstairs per floor, **`Shift+.` (`>`)** descent, floor depth in the **status corner**, creature mobility (ground/fly/aquatic), aquatic shore combat, and shark spawns on water floors.

**UI layout** (`openspec/specs/ui-layout/spec.md`) replaces the monolithic bottom HUD with region panels: camera map viewport, right sidebar (player + FOV-visible NPCs), eight-line message log, and status corner (depth + ailments). Layout geometry is JSON-driven with Options presets.

**Application entry:** launch shows the **main menu**, not a dungeon. **New Game** (after name entry) starts a run. The player's **display name** and HP appear in the **sidebar**, not a legacy bottom status line.

## Requirements

### Requirement: Turn-Based Game Loop

The game SHALL run in discrete turns. Each valid player action SHALL advance exactly one turn; the world (monsters, FOV, messages) SHALL update only after the player acts.

#### Scenario: Movement advances turn

- GIVEN a new game in progress
- WHEN the player presses a valid movement key
- THEN the player position updates (or an attack resolves if bumping a monster)
- AND monster turns execute
- AND FOV and the message log update

#### Scenario: Invalid input does not advance turn

- GIVEN a new game in progress
- WHEN the player presses an unrecognized or illegal key
- THEN the game state is unchanged
- AND no monster turns execute

#### Scenario: Ctrl+Q opens quit confirmation during play

- GIVEN a new game in progress with no modal active
- WHEN the player presses **Ctrl+Q**
- THEN a quit confirmation prompt is shown
- AND gameplay input is suspended until the prompt is resolved

#### Scenario: Confirm quit returns to menu

- GIVEN the quit confirmation prompt during gameplay
- WHEN the player presses capital **Y**
- THEN the main menu is shown
- AND the previous run state is discarded

### Requirement: Procedural Dungeon Map

The game SHALL generate a bounded rectangular dungeon with walls and floor tiles. The player SHALL spawn on a walkable floor tile. Map variety (organic caves, water, stairs, multi-floor descent) SHALL follow `openspec/specs/dungeon/spec.md`; the core contract requires at least one connected walkable land region and a valid player spawn.

#### Scenario: New game produces walkable layout

- GIVEN the player starts a new game
- WHEN the dungeon is generated
- THEN at least one connected region of walkable floor exists
- AND the player is placed on a walkable tile

#### Scenario: Walls block movement

- GIVEN the player is adjacent to a wall tile
- WHEN the player attempts to move into the wall
- THEN the player position is unchanged

### Requirement: Player Movement

The player SHALL move in eight directions using arrow keys, numpad, or vi-keys. Diagonal movement SHALL be permitted whenever the destination tile is walkable; corner-cutting through wall corners is allowed.

#### Scenario: Valid cardinal move

- GIVEN a walkable floor tile north of the player
- WHEN the player presses the north movement key
- THEN the player moves to that tile

#### Scenario: Diagonal corner cut

- GIVEN a walkable diagonal destination tile
- AND at least one adjacent cardinal tile along that diagonal is a wall
- WHEN the player attempts the diagonal move
- THEN the player moves to the destination tile

### Requirement: Field of View

The game SHALL compute field of view using libtcod. Tiles SHALL remember explored state. Only currently visible tiles SHALL reveal live entities; explored but not visible tiles SHALL render without live entity glyphs.

#### Scenario: Walls block sight

- GIVEN a wall between the player and a floor tile
- WHEN FOV is computed
- THEN the blocked floor tile is not visible

#### Scenario: Explored memory

- GIVEN the player has previously seen a floor tile
- WHEN the player moves so that tile is no longer visible
- THEN the tile remains shown as explored (dimmed)
- AND entities on that tile are not drawn

### Requirement: Map Tile Colors

Visible map terrain in the **map viewport** SHALL use a neutral grey palette for basic tiles:

| Tile | Visible foreground (RGB) | Notes |
|------|--------------------------|-------|
| Floor (`.`) | `(72, 72, 72)` dark grey | |
| Wall (`#`) | `(120, 120, 120)` mid grey | |
| Door (`+` / `-`) | `(120, 120, 120)` mid grey | Same as walls |

**Unchanged from prior palette:**

- **Stairs** (`>`) and **water** (`~`) keep their distinct visible colors (gold and blue respectively).
- **Explored-only** (not currently visible) tiles keep blue-tinted `DARK_*` dim colors for floor, walls, and doors.

Constants live in `src/systems/render.py` (`LIGHT_FLOOR`, `LIGHT_WALL`, `LIGHT_DOOR`); integer tweaks do not require schema changes.

#### Scenario: Visible floor and walls are grey

- GIVEN the player can see floor and wall tiles
- WHEN the map viewport renders
- THEN floor glyphs use dark grey foreground
- AND wall glyphs use mid grey foreground
- AND stairs and water remain visually distinct from grey terrain

#### Scenario: Explored memory dimming unchanged

- GIVEN a tile was explored but is not currently visible
- WHEN the map viewport renders
- THEN the tile uses the blue-tinted explored dim color
- AND not the visible grey palette

### Requirement: Rendering and Playfield UI

The game SHALL render an ASCII-style tilemap in a **map viewport** region (see `ui-layout` spec). The player SHALL appear as `@`, monsters per species glyph, and floor items per item JSON glyph (stock potion: `!`). Camera transform SHALL clip drawing to the viewport; world coordinates in ECS are unchanged.

Playfield chrome SHALL follow `ui-layout`:

- **Sidebar:** player display name, numeric HP, exact HP bar
- **Message log:** up to eight scrolling lines (no name/HP/depth in the log region)
- **Status corner:** floor depth, stunned, engulfed

The UI SHALL NOT show a compact inventory summary line (`i` opens inventory). Stunned and engulfed indicators SHALL appear in the **status corner**, not the sidebar text block.

#### Scenario: Visible entities only

- GIVEN a monster outside the player's current FOV
- WHEN the frame is rendered
- THEN the monster glyph is not drawn in the map viewport

#### Scenario: Sidebar HP reflects combat state

- GIVEN the player takes damage
- WHEN the next frame renders
- THEN the sidebar HP value matches the player's current HP

#### Scenario: Sidebar shows player display name

- GIVEN a new game started with display name `Alex`
- WHEN the playfield renders
- THEN the sidebar shows `Alex`
- AND the static `GAME_TITLE` string does not appear in the playfield chrome

#### Scenario: Stunned indicator in status corner

- GIVEN the player is stunned
- WHEN the playfield renders
- THEN a stunned indicator is visible in the status corner

### Requirement: Monster Spawning and AI

The game SHALL spawn 3–5 monsters on walkable floor tiles away from the player at game start. Each monster SHALL act after the player's turn. When the player is within a monster's FOV, the monster SHALL move one step toward the player; otherwise it SHALL remain idle (standing still is acceptable for v1).

#### Scenario: Chase when player visible

- GIVEN a monster with line of sight to the player
- WHEN the monster's turn executes
- THEN the monster moves one tile closer to the player if a walkable path step exists

#### Scenario: Monsters respect walls

- GIVEN a wall between a monster and the player
- WHEN the monster attempts to move
- THEN the monster does not enter wall tiles

#### Scenario: Monster acts after player

- GIVEN it is the player's turn
- WHEN the player completes a valid action
- THEN each living monster receives a turn before the next player input is processed

### Requirement: Bump Combat

Moving into a monster's tile SHALL perform a melee attack instead of occupying that tile. Combatants SHALL have HP tracked via a `Fighter` component with **`accuracy`, `evade`, `ac`, `min_damage`, `max_damage`** (see `openspec/specs/npc-data/spec.md`). Player defaults remain in code; NPC values come from `entities.json`.

When a monster reaches 0 HP, it SHALL be **defeated**: removed from the map with a log message using *defeated* wording. When the player reaches 0 HP, the player SHALL become **stunned**: unable to move or attack until HP rises above 0, but MAY still use inventory items. The player SHALL NOT be removed from the map.

#### Scenario: Player attacks monster

- GIVEN the player is adjacent to a monster
- WHEN the player moves into the monster's tile
- THEN the monster's HP decreases
- AND the player does not occupy the monster's tile

#### Scenario: Monster defeated

- GIVEN a monster at 1 HP
- WHEN the player attacks it for at least 1 damage
- THEN the monster is removed from the map
- AND the message log reports the monster was defeated

#### Scenario: Player stunned at zero HP

- GIVEN the player at 1 HP
- WHEN a monster attack reduces the player to 0 HP
- THEN the player becomes stunned
- AND the player remains on the map

#### Scenario: Stunned player cannot move or attack

- GIVEN a stunned player
- WHEN the player presses movement or bump-attack keys
- THEN no movement or attack occurs
- AND the world phase advances (see `openspec/specs/enhancements-1/spec.md` — stunned movement passes time)

> **Note:** Direct `try_action` calls while stunned still return false without advancing the world; engine input routing implements turn pass.

#### Scenario: Stunned player may use items

- GIVEN a stunned player with a health potion in an inventory slot
- WHEN the player quaffs the potion via the `q` category modal
- THEN the potion is consumed and HP is restored
- AND a turn advances

#### Scenario: Recovery from stunned

- GIVEN a stunned player
- WHEN the player's HP is restored above 0
- THEN the stunned state is cleared
- AND the player may move and attack on subsequent turns

### Requirement: Items and Inventory

Floor items, pickup, slot letters, category commands (`i`, `d`, `w`, `W`, `q`, `v`, `,`), equip, durability, and data-driven item types SHALL follow `openspec/specs/inventory-items/spec.md`. Global letter-key item use (`a`–`z` outside modals) is **retired**.

#### Scenario: Pickup assigns next free slot

- GIVEN a health potion on the floor
- AND the player has at least one empty inventory slot
- WHEN the player walks onto the potion tile
- THEN the potion is stored in the lowest available letter slot
- AND the floor item glyph is removed from the map

#### Scenario: Full inventory rejects pickup

- GIVEN all 26 inventory slots are occupied with no stackable potion match
- WHEN the player walks onto an item
- THEN the item remains on the floor
- AND the message log reports inventory is full

#### Scenario: Quaff potion from category modal

- GIVEN a health potion in slot `b`
- AND the player is not permanently locked (see stunned recovery note)
- WHEN the player quaffs via `q` and selects slot `b`
- THEN the player's HP increases by the potion amount up to max HP
- AND slot `b` becomes empty or stack count decrements

### Requirement: Modular Vore Boundary

The core-roguelike module SHALL not import vore logic at module load time. Core movement, FOV, inventory, and stunned recovery SHALL remain functional when `VORE_ENABLED` is false. Vore attack and engulfed-state logic lives in `src/systems/vore.py`; digestion in `src/systems/digestion.py` and engine wiring.

#### Scenario: Playable with vore disabled

- GIVEN `VORE_ENABLED` is false
- WHEN the player starts and plays a session
- THEN movement, FOV, combat, inventory, and stunned recovery are fully functional
- AND no vore attempts, modals, or engulfed behavior occur

#### Scenario: Core systems do not load vore

- GIVEN `src/systems/vore.py` exists on disk
- WHEN `src.systems.movement` and `src.systems.inventory` are imported in a fresh interpreter
- THEN `src.systems.vore` is not loaded as a side effect

## Technical Design

> Bootstrap design notes for the first implementation change. Ongoing changes SHOULD capture deltas in `design.md` per OpenSpec workflow.

### Architecture

Use a **lightweight entity-component system** (`tcod.ecs` or a thin custom registry). Systems run in phases each turn:

```text
Input → StunnedGate(movement/attack only) → Movement → BumpCombat → Pickup → MonsterAI → DefeatCleanup → FOV → Render
```

### Components (minimal set)

| Component | Role |
|-----------|------|
| `Position` | Map coordinates |
| `Renderable` | Character glyph and foreground color |
| `Player` | Tag marking the player entity |
| `Fighter` | `hp`, `max_hp`, `accuracy`, `evade`, `ac`, `min_damage`, `max_damage` |
| `Stunned` | Tag applied when player `hp == 0` |
| `AI` | Chase behavior state |
| `Item` | Floor item instance (`item_id`, category, durability, charges) |
| `Inventory` | Fixed mapping of slots `a`–`z` to `InventoryItemInstance` |
| `EquipState` | `wielded_slot`, `worn_slot` (see `inventory-items` spec) |
| `BlocksMovement` | Tag for walls and living monsters |

### Map generation

Base layout uses mixed room/cavern/corridor generation with connectivity validation (`src/map_gen.py`). `GameMap` exposes `width`, `height`, `tiles`, and mobility-aware helpers for walkability and transparency. See `dungeon` spec for water, stairs, and descent.

### Technology stack

- Python 3.11+
- libtcod 16.x (or current stable)
- numpy (libtcod dependency)

### Suggested source layout (first implementation change)

```text
src/
  main.py
  engine.py
  map_gen.py
  components.py
  systems/
    movement.py
    fov.py
    ai.py
    combat.py
    inventory.py
    render.py
```

### Vore extension points

- Event hooks: `on_entity_defeated`, `on_player_stunned`, `on_item_used`, plus vore hooks in `src/events.py`
- Vore domain: `openspec/specs/vore/spec.md` — attempts, modals, engulfed struggle
- Digestion domain: `openspec/specs/digestion/spec.md` — strikes, NPC removal, player game over
- Core systems (`movement`, `inventory`, `fov`) do not import `systems.vore` at load time

## Acceptance Criteria

Manual verification checklist for v1 core implementation:

1. Launching the game opens a libtcod window branded **Gladiavore** at the **main menu**; window size/position restore from `{user_data}/settings.json` (see `ui-layout`). **New Game** currently still starts a dungeon run (KDVR lineage); Gladiavore career/hub/match loop is under `openspec/changes/gladiavore-foundation/`. The sidebar shows the player's display name and HP during play (see `ui-layout`).
2. The player moves in eight directions; walls block movement; diagonal corner cuts are allowed.
3. FOV updates each turn; explored tiles persist visually; off-screen entities are hidden.
4. At least three monsters spawn and chase the player when they have line of sight.
5. Bump combat reduces HP; monsters at 0 HP are defeated and removed; logs use *defeated*, never *killed*.
6. The player at 0 HP becomes stunned and cannot move or attack until HP is restored above 0; item use while stunned works. Digestion game over requires engulf (see `digestion` spec).
7. Floor items pick up into letter slots; category commands manage inventory per `inventory-items` spec; a full 26-slot inventory blocks further pickup.
8. Core gameplay modules do not import vore at load time; disabling `VORE_ENABLED` removes all vore behavior.
9. Every scenario under **Requirements** is demonstrable in a single play session.