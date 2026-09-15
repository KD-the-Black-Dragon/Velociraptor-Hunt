# modding Specification

## Purpose

Official **JSON-only** modding for KD's Vore Roguelike. Players drop content under `{user_data}/mods/`, toggle enable/load order in **Options → Mods**, and extend or override stock `data/*.json` for a session. Core install data always loads first.

Implementation: `src/mods/`, layered loaders under `src/data/` and `src/ui/layout.py`, Options row in `src/options_menu.py` / `src/app.py`.

**Not supported:** Python/code mods, tileset/font asset packs, deep merge of whole-file catalogs (spawn bands, gratitude lines, UI layout, etc.).

**Terminology:** defeated, stunned, digested — no kill/die/death.

**Schemas:** Stock shapes in `data/SCHEMA.md`. Player guide: `README.md` (**Modding**).

## Requirements

### Requirement: Mods directory

Mods SHALL live under `{user_data}/mods/` (`MODS_DIR` via `src/user_data.py`). Each immediate subdirectory is one mod (folder name = mod id). Loose files at the mods root SHALL be ignored.

#### Scenario: Empty mods root

- GIVEN no mod folders
- WHEN the game loads data
- THEN only install `data/` content is used
- AND the game behaves as stock

### Requirement: Per-mod state file

Each mod folder SHALL have a `mod.state` file with one line: `E` or `D` (enabled/disabled, case-insensitive) and an integer load order (lower loads earlier among mods).

Missing, unreadable, malformed, or contradictory state SHALL be discarded and regenerated (default **Enabled**, unique order — append or alphabetical bulk assignment on first discovery). Duplicate orders SHALL be renumbered `1..N` stably by `(order, name)`.

#### Scenario: New folder without mod.state

- GIVEN a new folder `{user_data}/mods/CoolDragons/` with no `mod.state`
- WHEN discovery runs
- THEN `mod.state` is created with `E` and a unique order
- AND the mod is enabled

### Requirement: Core first then enabled mods

Install `data/` SHALL always load first. Enabled mods SHALL apply in ascending load order. Disabled mods SHALL appear in the Mods UI but SHALL NOT contribute content.

#### Scenario: Later mod patches entity id

- GIVEN core defines entity `wolf`
- AND an enabled mod later in order patches `wolf` (any subset of fields)
- WHEN entities are loaded
- THEN the layered definition for that session is core deep-merged with the mod fields
- AND fields omitted by the mod keep the prior layered values

### Requirement: Entity catalog deep merge

For `entities.json`, if a mod provides the file, entries SHALL merge by **id** using **selective deep merge** onto the running layered catalog (core, then each earlier successful mod):

- If the `id` **already exists**, deep-merge the overlay object onto the current entry.
- If the `id` is **new**, insert the overlay object as a full new entry (no inheritance).
- Nested **objects** SHALL merge recursively (e.g. `spawn.weight` keeps other `spawn` keys).
- **Arrays** and scalars (including JSON `null`) SHALL **replace** when the key is present (e.g. `abilities`, `fg`, `vore_narratives.OV`).
- Type mismatch at a key (object vs array, etc.) SHALL replace with the overlay value.
- After each mod’s `entities.json` is applied, the game SHALL validate the **merged** catalog. On failure, skip that mod file’s contribution (see bad-mod rules). New incomplete ids SHALL fail validation.

There is no tombstone / “delete optional field back to absent”; omit a key to inherit; present a key (including `[]` or `null`) to overwrite.

#### Scenario: Turn off wolves with weight only

- GIVEN core defines `wolf` with non-zero `spawn.weight` and other spawn/combat fields
- AND an enabled mod provides only `{ "id": "wolf", "spawn": { "weight": 0 } }`
- WHEN entities are loaded
- THEN `wolf.spawn.weight` is `0`
- AND other `wolf` fields (including other `spawn` keys) match the prior layered values

#### Scenario: Narrative OV patch keeps CV/AV

- GIVEN core `wolf` has `vore_narratives` with `OV`, `CV`, and `AV` arrays
- AND an enabled mod sets only `vore_narratives.OV` to a new non-empty variant array
- WHEN entities are loaded
- THEN `wolf` uses the mod’s `OV` array
- AND `CV` / `AV` remain from the prior layer

#### Scenario: Stacked entity patches

- GIVEN mod A (earlier) sets `wolf.display_name` and `wolf.spawn.weight`
- AND mod B (later) sets only `wolf.spawn.weight`
- WHEN entities are loaded
- THEN `display_name` comes from mod A
- AND `spawn.weight` comes from mod B

#### Scenario: Incomplete new entity id fails

- GIVEN an enabled mod adds a new entity id with mandatory fields missing
- WHEN entities are loaded
- THEN that mod’s `entities.json` contribution is skipped with a player-facing error
- AND prior layered entities remain available

### Requirement: Other id-keyed catalogs (full replace)

For these files, if a mod provides the file, entries SHALL merge by **id** (**full replace** of that entry): `weapons.json`, `armor.json`, `potions.json`, `wands.json`, `throwables.json`, `floor_runes.json`, `macguffins.json`. For `names.json`, later pools SHALL replace by **entity id key**.

Partial mods (subset of files) are valid; omitted files mean no change for that domain.

### Requirement: Whole-file catalogs

If a mod provides any of `dungeon_spawn.json`, `depth_scaling.json`, `global_tuning.json`, `depth_jump_start.json`, `npc_prefixes.json`, `rescue_gratitude.json`, or `ui_layout.json`, that file SHALL **replace** the entire previous layer (not deep-merge).

Stock `depth_jump_start.json` is read from core `data/` until mod pipeline support is added for that filename.

### Requirement: Bad mod data is not silent

Hard failures on **core** stock data remain (e.g. broken core `entities.json` blocks startup).

Bad **mod** JSON or validation errors SHALL:

1. Show a player-facing error dialog naming **mod folder**, **filename**, and a short reason
2. Append the same detail to the startup error log trail
3. Skip that file’s contribution
4. Continue with core + remaining good mod layers

Multiple failures in one load pass SHOULD be listed in one dialog when practical.

#### Scenario: Broken Cool_Dragon_Mod entities

- GIVEN enabled mod `Cool_Dragon_Mod` with invalid `entities.json`
- WHEN data loads
- THEN a dialog identifies `Cool_Dragon_Mod` and `entities.json`
- AND the game still reaches the main menu
- AND core entities remain available

### Requirement: Options → Mods UI

Options SHALL include a **Mods...** row opening a submenu that lists discovered mods, shows Enabled/Disabled, supports toggle (Left/Right or Enter), and reorder (Page Up/Page Down). Escape returns to Options (or main menu if a run was ended) and SHALL trigger a full data reload.

### Requirement: Save wipe gate

When the player opens Mods and an autosave chain exists, the game SHALL require capital **Y** confirmation that entering Mods **deletes** the current saved game. **n** or Escape cancels. On confirm, the full autosave chain SHALL be deleted before Mods opens. If a live PLAY session is active when Mods is entered, that run SHALL end.

#### Scenario: Cancel preserves save

- GIVEN a valid autosave
- WHEN the player opens Mods and presses **n**
- THEN the save remains loadable
- AND Mods does not open

### Requirement: Reload on Mods exit

Leaving the Mods submenu SHALL invalidate caches and reload all moddable JSON domains as if restarting for data (entities, items, runes, macguffins, names, dungeon spawn, rescue gratitude, ui layout).

### Requirement: Save fingerprint

Autosaves SHALL store `mods.enabled_in_order` (list of enabled mod folder names in load order). Missing field (pre-modding saves) SHALL be treated as an empty list.

Load Game SHALL succeed only when the save fingerprint exactly matches the current enabled-in-order list. On mismatch, the game SHALL refuse load, keep the player on the main menu, keep the save file, and show a clear message.

#### Scenario: Explorer disables mod after save

- GIVEN a save fingerprinted with mod `A` enabled
- WHEN the player disables or deletes `A` outside the Mods UI
- AND chooses Load Game
- THEN load is refused
- AND the save files remain on disk

### Requirement: Crash report loaded mods

Crash reports SHALL list enabled mod folder names in load order, or `(none)` when none are enabled (no longer a permanent stub).

### Requirement: Documentation

README SHALL document the user-data `mods/` path and modding rules. `data/SCHEMA.md` SHALL cross-link mod merge rules.

On each game launch, the game SHALL ensure `{user_data}/mods/MODDING_README.txt` exists and matches the shipped guide text (rewrite when missing or contents differ). The Sample Mod `entities.json` SHALL likewise be game-owned: rewritten when missing or contents differ from the shipped template (skip write when identical). An existing Sample Mod `mod.state` (enabled / load order) SHALL be preserved; if `mod.state` is missing when ensuring the folder, it SHALL be created disabled with a default order. Player-created mod folders SHALL NOT be overwritten.

`data/SCHEMA.md`, README, and `MODDING_README.txt` SHALL document optional `spawn.requires_vore_types` (capability list: spawn if **any** listed `OV` / `CV` / `AV` is enabled in run prefs; when non-empty also restricts initiation to capability ∩ prefs; empty/omitted = unrestricted). Docs MAY note the internal `GENERIC` last-resort stub when the attempt pool is empty (not an Options toggle; unlikely under New Game prefs snapshot + spawn OR).

#### Scenario: Stale modding readme refreshes

- GIVEN `{user_data}/mods/MODDING_README.txt` exists with outdated contents
- WHEN the game starts
- THEN the file is rewritten to the current shipped guide text

#### Scenario: Stale Sample Mod entities refreshes

- GIVEN `{user_data}/mods/Sample Mod/entities.json` exists with contents that differ from the shipped template
- AND `mod.state` has the Sample Mod enabled
- WHEN the game starts
- THEN `entities.json` is rewritten to the shipped template
- AND `mod.state` remains enabled with the same order

#### Scenario: Identical Sample Mod entities skips write

- GIVEN Sample Mod `entities.json` already equals the shipped template
- WHEN the game starts
- THEN the game does not rewrite that file
