# save-load Specification

## Purpose

The **save-load** domain provides a **single automatic save slot** with **rotating backups**, **background writes**, and **full run fidelity** so players can pause and resume a permadeath run. Saves are wiped on **game over** (digestion defeat) so defeat cannot be undone by loading.

Builds on **core-roguelike**, **main-menu**, and **digestion**. Implementation lives in `src/save/` (`schema`, `codec`, `snapshot`, `store`, `coordinator`), with hooks in `GameEngine` and `App`.

**Terminology:** defeated, stunned, digested — no kill/die/death.

**User data directory** (`KD's Vore Roguelike`, via `src/user_data.py`):

| OS | Path |
|----|------|
| Windows | `%LOCALAPPDATA%\KD's Vore Roguelike\` |
| Linux | `~/.local/share/KD's Vore Roguelike/` |
| macOS | `~/Library/Application Support/KD's Vore Roguelike/` |

## Requirements

### Requirement: Save File Layout

The game SHALL persist one autosave chain under `{user_data}/saves/`:

| File | Role |
|------|------|
| `autosave.json` | Primary (newest successful write) |
| `autosave.bak1.json` … `autosave.bak3.json` | Rotating backups (oldest retained in bak3) |
| `autosave.tmp` | Transient write target (removed after success) |

Each file SHALL be UTF-8 JSON with envelope fields `save_format_version` (v1), `saved_at_unix`, `payload_sha256`, and `run` (full snapshot).

#### Scenario: Successful write rotates chain

- GIVEN a valid snapshot is serialized
- WHEN `SaveStore.save_run` completes
- THEN the previous primary becomes `autosave.bak1.json`
- AND the new bytes are atomically promoted to `autosave.json`

### Requirement: Integrity and Load Fallback

`payload_sha256` SHALL hash the canonical JSON of the `run` object. On load, the store SHALL try primary → bak1 → bak2 → bak3 and use the first file that parses and validates. Corrupt files SHALL be skipped.

### Requirement: Soft-drop unknown content

After a successful structural load, the game SHALL **sanitize** the run against current data:

- Inventory / floor **items** whose `item_id` is not in the item registry SHALL be removed (equip pointers cleared).
- Non-player **NPCs** whose `SpeciesId` is not in the entity registry SHALL be removed (predator links broken).
- Unknown **NpcPrefix** ids SHALL be cleared from entities.

The run SHALL resume. The message log SHALL receive a **caution** notice summarizing that outdated content was dropped. Missing content SHALL NOT be treated as save corruption.

#### Scenario: Removed longsword

- GIVEN a save with inventory slot holding `item_id` no longer in data
- WHEN the save is loaded
- THEN that slot is empty
- AND the player can play
- AND a caution notice mentions removed content

#### Scenario: Corrupt primary falls back

- GIVEN `autosave.json` has an invalid hash
- AND `autosave.bak1.json` is valid
- WHEN `load_best` runs
- THEN the run from bak1 is returned

### Requirement: Additive fields and migration hook

The live format version is **`save_format_version` = 1**. Agents SHALL prefer **additive** snapshot fields with **defaults on load** over format bumps.

Before applying a run snapshot, the game SHALL pass the run through `migrate_run` (`src/save/migrate.py`). For v1, migration is an **identity** transform that normalizes `save_format_version` to the current constant. Future true layout breaks SHALL add steps there after a version bump and designer consult.

#### Scenario: Missing optional run keys still load

- GIVEN a structurally valid run missing optional keys such as `last_come_here_turn`, `close_door_pending`, `run_stats`, `macguffin_discovery`, or `message_log`
- WHEN the snapshot is applied
- THEN the run resumes with safe defaults (e.g. come-here never used, empty stats, empty discovery, empty log)

#### Scenario: Missing PlayerEffects on player

- GIVEN a player entity record without a `PlayerEffects` component
- WHEN the snapshot is applied
- THEN `PlayerEffects` is created with zeroed / inactive defaults

### Requirement: Run field inventory (format v1)

Quick reference (full tables in `src/save/FIELDS.md`):

| Run key | Missing on load |
|---------|-----------------|
| `player_name`, `player_turn_count`, `floor_depth`, `player_entity_id`, `vore_content_prefs`, `game_map`, `entities` | Required (structural fail) |
| `last_come_here_turn` | `-1` |
| `difficulty_id` | default difficulty id |
| `close_door_pending` | `false` |
| `message_log` | empty log |
| `run_stats` | zeros |
| `macguffin_discovery` | inactive |
| `rng_state` | keep engine RNG |
| `game_map.layout_archetype` | `""` |

### Requirement: Agent save-compat checklist

When a change touches persistence or game data that can appear in saves:

1. **New optional state** → encode when present; **default on load** if missing; add/extend a stripped-snapshot test.
2. **New content only** (new entity/item ids) → no save change required.
3. **Removed/renamed id** → soft-drop or dual-read; never hard-fail load as corrupt.
4. **True wire-format break** → bump `SAVE_FORMAT_VERSION`, implement `migrate_run` step, **consult designer** first.
5. Do not pin live balance numbers in save tests.

### Requirement: Snapshot Fidelity

The `run` payload SHALL include everything required to resume at the last stable checkpoint: player and NPC entities (components, tags, stable entity ids, `Predator.prey` via id, floor **`Macguffin`** entities per `macguffins` spec), map tiles and **explored** flags, inventory, rune progression, message log, floor depth, RNG state, frozen `vore_content_prefs`, frozen `ui_preset`, run metadata, **`run_stats`** (`monsters_defeated`, `runes_collected` per `past-runs` spec), and **`macguffin_discovery`** (run-level discovery state per `macguffins` spec).

The snapshot SHALL NOT persist ephemeral UI (modals, overlays, rest session, debug toggles), including **`macguffin_victory_confirm`** (victory prompt resets on load). `visible` FOV SHALL be recomputed on load.

#### Scenario: Round-trip preserves explored map

- GIVEN a run with partial exploration
- WHEN snapshot → restore runs in memory
- THEN `game_map.explored` matches the pre-save state

### Requirement: Idle Command Gate

Quit, manual save, and periodic autosave eligibility SHALL use `GameEngine.can_issue_idle_command()`: true when no blocking modal is active (`modal_blocks_quit()` is false) and rest is not in progress.

#### Scenario: Vore modal blocks save

- GIVEN the vore attempt modal is active
- WHEN the player presses Ctrl+S
- THEN no save is written
- AND no quit confirmation opens

### Requirement: Autosave Cadence

Background autosave SHALL run when the idle gate passes at:

- **Entering PLAY** (new game or load — immediate write)
- **Every 15 player turns** or **30 seconds** since last successful save (whichever first)
- **After successful `descend_floor()`**
- **Every player turn end while the player has the `Engulfed` tag**

Writes SHALL occur on a dedicated worker thread with coalescing (only the latest pending snapshot matters while a write is in flight).

#### Scenario: Engulfed danger save

- GIVEN the player is engulfed and idle between turns
- WHEN a player turn ends
- THEN a background save is queued even if the 15-turn throttle is not met

### Requirement: Quit and Manual Save

When the idle gate passes:

- **Ctrl+Q** SHALL open quit confirmation **and** queue a background save in the same moment (save runs even if the player later presses **n**).
- **Ctrl+S** SHALL perform a synchronous main-thread save. On success the message log SHALL show **"Game saved."** (positive category). On failure it SHALL show **"Save failed."** (danger category) and SHALL NOT crash.

Confirming quit (**capital Y**) returns to the main menu; the run remains resumable via Load Game if the save succeeded.

#### Scenario: Ctrl+Q cancel preserves resumable run

- GIVEN an in-progress game and a successful quit-save
- WHEN the player presses Ctrl+Q then **n**
- THEN gameplay resumes
- AND a valid autosave still exists

### Requirement: Menu Load and New Game

On menu enter, `SaveStore.probe()` SHALL run before rendering options. If no valid save exists, **Load Game SHALL be omitted** from the Up/Down option list (not shown, not selectable).

**Load Game** SHALL restore the newest valid backup into PLAY (skip name entry). Run `vore_content_prefs` and `ui_preset` SHALL come from the save, not live `settings.json`.

**New Game** when a save exists SHALL show overwrite confirmation: *"A saved game exists and will be overwritten. Proceed? (Y/n)"* — capital **Y** only; **n** or Escape returns to menu without deleting. Saves SHALL be deleted only after name entry confirms and `GameEngine` is created for the new run. Canceling name entry SHALL preserve any existing save.

#### Scenario: No save hides Load Game

- GIVEN the save directory has no valid autosave
- WHEN the main menu is shown
- THEN Load Game is not listed (three options minimum: New Game, Options, Exit; Past Runs when history exists)

### Requirement: Game Over Permadeath Wipe

When `GameOverState.open()` runs (player digested or macguffin victory), the game SHALL call `SaveCoordinator.prepare_for_game_over_wipe()` (cancel queued snapshots, wait for in-flight write), then **immediately** delete all autosave slot files (sync, best-effort). After recap → menu, Load Game SHALL NOT appear until a new run creates a fresh save. Past-run recording is handled by `past-runs` spec (independent of autosave).

#### Scenario: Digestion defeat wipes slot

- GIVEN a valid autosave exists
- WHEN player digestion completes and game over opens
- THEN all files in the autosave chain are removed
- AND `probe()` returns false

## Supersedes

| Spec | Change |
|------|--------|
| `main-menu/spec.md` | Load Game stub replaced; overwrite confirm; conditional menu options |
| `core-roguelike/spec.md` | Save/load no longer out of scope |
| `past-runs/spec.md` | Snapshot includes `run_stats`; game-over wipe coordinates with coordinator |
| `macguffins/spec.md` | `macguffin_discovery` snapshot; `Macguffin` entity codec |

## Acceptance Criteria

1. Single slot with primary + 3 backups; SHA256 validation; corrupt-primary fallback.
2. In-memory and file round-trip preserve player, map explored, inventory, AI state, predator links, message log.
3. Autosave cadence (15 turns / 30s / descent / engulfed / PLAY enter) respects idle gate.
4. Ctrl+Q + background save; Ctrl+S sync save with log feedback; save failures do not crash.
5. Menu probe omits Load when absent; load restores run; New Game overwrite flow preserves save until confirmed.
6. Game over deletes all save files immediately.
7. Automated tests cover store rotation, coordinator gating, menu integration, game-over wipe.