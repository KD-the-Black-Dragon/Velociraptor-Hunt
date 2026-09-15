# ui-layout Specification

## Purpose

The **ui-layout** domain defines how the game screen is divided into **regions**, how text is scaled for readability, how the **map camera** shows a subset of the logical dungeon, and how **sidebar**, **message log**, and **status corner** panels present player and NPC information.

Builds on `core-roguelike` and `main-menu`. Preset definitions live in shipped `data/ui_layout.json`; the active preset is chosen in Options and stored in `{user_data}/settings.json` (`ui_preset`, via `src/user_data.py`). Runtime code lives under `src/ui/`.

**Logical dungeon size is unchanged:** `MAP_WIDTH` × `MAP_HEIGHT` (80×44). Only rendering uses a camera and region sub-consoles.

**Terminology:** defeated, stunned, digested — no kill/die/death.

## Requirements

### Requirement: Layout Configuration

The game SHALL load layout geometry from `data/ui_layout.json`. The file SHALL define at least:

- `tile_px` and `tile_scale` (display scale for the CP437 tileset)
- Named **presets** (`standard`, `wide_sidebar`, …), each with:
  - `root_cols` / `root_rows` (design-time root console size)
  - `regions`: `map_viewport`, `sidebar`, `message_log`, `status_corner` (non-overlapping tiling)
  - `map_viewport_tiles` (camera viewport width/height in dungeon cells)
  - `message_log_lines` (visible log rows)
  - `sidebar` tuning: `hp_bar_width`, `npc_hp_bar_width`, `max_evil`, `max_good`, padding fields

Invalid or overlapping regions SHALL fail at load with a clear error.

#### Scenario: Standard preset loads

- GIVEN `ui_layout.json` contains preset `standard`
- WHEN the game loads the default or `standard` preset
- THEN regions tile the root rectangle without gaps
- AND `map_viewport` dimensions match `map_viewport_tiles`

#### Scenario: Developer tunes sidebar width in JSON

- GIVEN a preset's `regions.sidebar.w` is changed from 23 to 25
- WHEN the game restarts with that preset active
- THEN the sidebar region is 25 cells wide without editing render functions

### Requirement: Display Scale

The game SHALL render with `tile_scale` from the active layout (stock: **2**), doubling effective glyph height from the 12×12 tileset. At the design root size, pixel size is `root_cols × tile_px × tile_scale` by `root_rows × tile_px × tile_scale`. **Startup** client size comes from saved `window` settings or first-launch sizing (see **Window Persistence**). `integer_scaling` is enabled on present.

Menu screens (main menu, name entry, options, stubs, quit confirm) SHALL use the same scale as gameplay.

#### Scenario: Text is visibly larger than 1× scale

- GIVEN stock `tile_scale` of 2
- WHEN the application window opens
- THEN menu and gameplay glyphs are approximately twice the prior 1× height

### Requirement: 4K UI scaling option

Options SHALL include a **4K UI scaling** Off/On row (default **Off**). The preference SHALL persist in `{user_data}/settings.json` as `four_k_scaling`. A **missing** key SHALL mean **Off** (past-version safe).

When **On**, the effective layout `tile_scale` SHALL be **2×** the preset value (stock 2 → 4), applied when loading the active layout. Toggle SHALL apply live: reload layout baseline, apply **dual window size-set** geometry (below) when windowed, **enforce the (scaled) minimum client size** so the OS window is not smaller than the console pixel size, resize the console from the resulting client pixels, and reload the proportional log font. The minimum client pixel floor SHALL scale with effective cell size so chrome and minimum map viewport remain usable. The console SHALL NOT be sized larger than the live window client area (which would clip present to the top-left and make menus look uncentered).

**Dual window size sets:** Normal (non-4K) client size lives in `window.client_width` / `window.client_height`. Preferred 4K client size lives in optional `window.four_k_client_width` / `window.four_k_client_height`. Enabling 4K SHALL NOT overwrite the normal `client_*` fields. Missing `four_k_client_*` keys SHALL mean “never enabled” (past-version safe).

**Windowed, not maximized, on toggle:**

1. Persist the live client size into the **outgoing** size set.
2. **First enable** (no 4K size saved): seed `four_k_client_*` as **2×** the current windowed client size, then apply that size.
3. **Later toggles:** apply the incoming size set (swap; do not re-double).
4. Clamp position: if `x < 0` then `x = 0`; if `y < 30` then `y = 30`.

**Fullscreen** and **maximized:** skip size swap and position apply on 4K toggle (layout / tile scale / min-size still update). Resize/move while 4K is On SHALL update only `four_k_client_*` (+ shared `x`/`y`); while Off, only `client_*` (+ shared `x`/`y`).

**Startup** with 4K On SHALL open at the 4K size set (seed `2 × client_*` into `four_k_client_*` if unset).

**F10** SHALL toggle 4K UI scaling at any time while the application event loop is running (menus, options, play, overlays). The same live-apply path as the Options row SHALL run; the preference SHALL persist like the Options toggle.

Menu-like screens (Options, name entry, depth entry, entity entry, and similar) SHALL present via the layout ``tile_scale`` blit path (not bare tileset ``context.present``), and SHALL center the console in the window when letterboxed, so 4K On/Off does not jump content to the upper-left.

#### Scenario: Missing settings key stays Off

- GIVEN an older `settings.json` without `four_k_scaling`
- WHEN settings load
- THEN 4K UI scaling is Off
- AND effective `tile_scale` matches the preset (stock 2)

#### Scenario: Enabling 4K doubles effective tile scale

- GIVEN Options **4K UI scaling** is turned On
- WHEN the layout reloads
- THEN effective `tile_scale` is twice the preset value
- AND menu/gameplay glyphs and log font size increase accordingly

#### Scenario: First enable seeds 4K size without mutating normal size

- GIVEN windowed mode, 4K Off, no `four_k_client_*` saved, client size W×H
- WHEN the player turns 4K On
- THEN the window becomes approximately 2W×2H (clamped to the 4K minimum floor)
- AND stored `client_width` / `client_height` remain W×H

#### Scenario: Disable 4K restores normal window size

- GIVEN windowed mode with a remembered normal size and a remembered 4K size
- WHEN the player turns 4K Off
- THEN the OS window returns to the normal size set
- AND is not left at the oversized 4K frame

#### Scenario: Second enable uses remembered 4K size

- GIVEN `four_k_client_*` were saved from a prior enable (possibly user-resized)
- WHEN the player turns 4K On again
- THEN the window uses that remembered 4K size
- AND does not double the current normal size again

#### Scenario: Toggle clamps off-screen position

- GIVEN windowed non-maximized mode with `x < 0` or `y < 30`
- WHEN the player toggles 4K On or Off
- THEN `x` is at least 0 and `y` is at least 30
- AND the title bar remains reachable

#### Scenario: New Game and Load keep 4K scale

- GIVEN **4K UI scaling** is already On
- WHEN the player starts a New Game or Load Game (including maximized/fullscreen)
- THEN effective play `tile_scale` remains doubled
- AND the console is re-synced to the live window before PLAY (same path as F10 apply)
- AND the map is not presented as a tiny unscaled square

### Requirement: Layout Presets in Options

The Options menu SHALL include a **UI Layout** row cycling named presets (stock labels: **Standard**, **Wide**). The chosen preset id SHALL persist in `{user_data}/settings.json` as `ui_preset`. Changing preset SHALL apply on the **next new game** or **Load Game** (and refresh the live layout template for resize while on menu/options). Saves MAY record a layout preset for diagnostics, but **Load Game** SHALL resolve layout from current `settings.ui_preset`, not the saved snapshot.

Stock presets (geometry at design root 80×44):

| Preset id | Map viewport (cells) | Sidebar width | Player HP bar width |
|-----------|-------------------|---------------|---------------------|
| `standard` | 57×34 | 23 | 9 |
| `wide_sidebar` | 44×34 | 36 | 18 |

#### Scenario: Wide preset on new game

- GIVEN Options has **Wide** selected and saved
- WHEN the player starts a new game
- THEN the sidebar is wider and the map viewport is narrower than **Standard**
- AND player HP bar width matches the wide preset config

#### Scenario: Wide preset on load game

- GIVEN Options has **Wide** selected and saved
- AND an autosave exists from a prior **Standard** run
- WHEN the player chooses **Load Game**
- THEN the loaded run uses the **Wide** sidebar and map viewport from settings

#### Scenario: Preset change before continue

- GIVEN a dungeon run was saved under **Standard**
- WHEN the player returns to menu, selects **Wide**, and chooses **Load Game**
- THEN the resumed run renders with the **Wide** preset from settings

### Requirement: Region Rendering

Gameplay frames SHALL composite four regions onto the root console:

1. **map_viewport** — camera-scoped dungeon tiles, entities, overlays, examine/evoke cursors
2. **sidebar** — player block and FOV-visible NPC list
3. **message_log** — scrolling combat/event text
4. **status_corner** — floor depth and player ailments

Each region SHALL render into a sub-console blitted to its root placement rect.

#### Scenario: Regions blit without overlap

- GIVEN a gameplay frame
- WHEN `Engine.render()` completes
- THEN map, sidebar, message log, and status corner occupy their configured rectangles
- AND no region draws outside its rect except root-level modals

### Requirement: Map Camera Viewport

The visible map SHALL show `map_viewport_tiles.w × map_viewport_tiles.h` dungeon cells centered on the player, clamped so the viewport does not scroll past map edges. Camera offset SHALL apply consistently to map tiles, entities, screen flash, engulfed overlay, and map-local cursors (examine, evoke target).

#### Scenario: Player centered when away from edges

- GIVEN the player is far from all map borders
- WHEN the map region renders
- THEN the player glyph is approximately centered in the viewport

#### Scenario: Camera clamps at west edge

- GIVEN the player is near the west map border
- WHEN the map region renders
- THEN the viewport does not show tiles west of x = 0

### Requirement: Sidebar Player Block

The sidebar upper block SHALL show:

- Player display name
- Numeric HP (`HP current/max`)
- Exact ASCII HP bar (`hp_bar_width` from preset)

Stunned and engulfed flags SHALL **not** appear in the sidebar text; they appear in the status corner.

Vertical padding SHALL follow JSON: `player_top_pad`, `player_bottom_pad`.

#### Scenario: Player name and HP in sidebar

- GIVEN a new game with display name `Alex` and 24/30 HP
- WHEN the sidebar renders
- THEN `Alex` and `HP 24/30` with a bar are visible in the sidebar region
- AND the legacy bottom status line is absent

### Requirement: Sidebar NPC List

The sidebar SHALL list NPCs currently in player FOV (`game_map.visible`), using the same visibility rule as gated log messages.

- **Evil** NPCs: directly below the player block (nearest-first)
- **Good** NPCs: bottom-anchored band (nearest-first)
- **Neutral** NPCs: omitted from sidebar in v1

Each alignment band SHALL fill **one column** first, then add a **second column** when the first column is full (by count cap **or** vertical row budget). When vertical row budget is the limiting factor, entries SHALL use **parallel row pairs** (alternating col0/col1 per row slot) so both columns are populated before shrinking to a single column. Stock per-column caps: `evil_per_column` **5**, `good_per_column` **2**. Total displayed entries SHALL NOT exceed `max_evil` / `max_good` (stock: **10** / **4** = two columns at cap). Evil and good bands SHALL NOT overlap vertically; column height SHALL use `max(col0_entries, col1_entries)` row slots (parallel columns), not stacked column totals.

When only one column is used, NPC names SHALL show in full (sidebar width permitting). When two columns are used, names SHALL truncate per column.

Each listed NPC SHALL use **two lines**: name row, then estimate bar row, then a blank spacer row (`rows_per_npc = 3`). When more NPCs are in FOV than can be drawn, the sidebar SHALL show as many entries as fit at the current window height and **always** reserve a summary line for the remainder (e.g. `+6 evil`, `+3 good`). Overflow summary lines SHALL NOT be dropped to make room for additional NPC rows.

NPC bars SHALL be **coarse estimates** (`npc_hp_bar_width`, stock: 6) with fill count `filled = min(6, round(6 * hp / max_hp))` for `hp > 0`, else `0`. All fill counts 0–6 SHALL be reachable. Numeric NPC HP SHALL NOT appear in the sidebar.

#### Scenario: FOV gates sidebar NPCs

- GIVEN an evil NPC exists but is not visible to the player
- WHEN the sidebar renders
- THEN that NPC is not listed

#### Scenario: NPC estimate bar uses coarse fill

- GIVEN a visible NPC at 50% HP
- WHEN the sidebar renders
- THEN the bar row shows approximately half fill (e.g. 3 of 6 `#` characters)
- AND no `hp/max` numbers appear for that NPC

### Requirement: Message Log Panel

The message log region SHALL show up to `message_log_lines` entries (stock: **8**), newest toward the bottom. It SHALL NOT include player name, HP, or depth.

The game SHALL retain up to **100** logical log entries in memory (`MESSAGE_LOG_CAPACITY`).

#### Scenario: Eight visible log lines

- GIVEN more than eight messages in the log buffer
- WHEN the message log renders
- THEN at most eight lines are visible in the message log region

### Requirement: Full Log Overlay

**Ctrl+P** SHALL toggle a full-screen scrollable log overlay during play. The overlay SHALL be available during gameplay modals and rest animation (meta UI). It SHALL NOT be blocked by inventory, examine, vore, or rest states.

| Input | Action |
|-------|--------|
| **Ctrl+P** | Toggle overlay |
| Arrows / **TYUGHJBNM** / numpad (vertical) | Scroll ±1 wrapped display line |
| **PgUp** / **PgDn** | Scroll ±1 page (viewport height in lines) |
| **Esc** | Close overlay |

On open, the viewport SHALL start at the newest wrapped lines. Footer: `Esc: close | Arrows: line | PgUp/PgDn: page`.

#### Scenario: Overlay during inventory

- GIVEN the inventory modal is open
- WHEN the player presses **Ctrl+P**
- THEN the full log overlay appears over the game UI
- AND **Esc** closes the overlay without closing inventory

### Requirement: Help Overlay

**F1** or **?** (Shift+/) SHALL toggle a full-screen help overlay during play. **Esc** SHALL dismiss it. The overlay is meta UI: available during gameplay modals and rest animation. Content SHALL document movement, actions (including rest **`5`**), and meta keys (**Ctrl+P**, **F1**/**?**, **Ctrl+Q**). Debug keys (R, S, F2–F4) SHALL NOT appear.

When help content exceeds the visible viewport (short window / large proportional font), the overlay SHALL scroll with the **same keys as the Ctrl+P log overlay** (arrows / TYUGHJBNM vertical / numpad line scroll; **PgUp**/**PgDn** page). Scroll capacity SHALL be based on how many help rows the **proportional font** can fit above the footer (not merely console cell count), so clipped Meta lines remain reachable. On open, scroll SHALL start at the **top**. Footer: `Esc: close | Arrows: line | PgUp/PgDn: page`.

When help is open, **Ctrl+P** SHALL close help and open the full log overlay.

#### Scenario: Help during examine

- GIVEN examine mode is active
- WHEN the player presses **F1**
- THEN the help overlay appears
- AND **Esc** returns to examine without cancelling it

#### Scenario: Help scrolls on a short viewport

- GIVEN the help overlay is open and Meta lines are below the viewport
- WHEN the player presses **PgDn** (or line-down) enough times
- THEN previously cut-off help lines become visible

### Requirement: Status Corner

The status corner (stock: **10** cells wide, bottom-right) SHALL show:

- Floor **depth**
- **Stunned** when applicable
- **Engulfed** when applicable

The region SHALL be extensible for future buff/debuff rows. Depth SHALL NOT appear in the message log or sidebar.

#### Scenario: Depth and engulfed in corner

- GIVEN the player is on depth 3 and engulfed
- WHEN the status corner renders
- THEN depth 3 and an engulfed indicator are visible in the corner region

### Requirement: Window Persistence

Window client geometry and mode SHALL persist in `{user_data}/settings.json` under a `window` object:

| Field | Type | Purpose |
|-------|------|---------|
| `client_width` / `client_height` | int | Normal (non-4K) client area pixels (not including OS title bar/borders) |
| `four_k_client_width` / `four_k_client_height` | int (optional) | Preferred client size while **4K UI scaling** is On; absent until first enable |
| `x` / `y` | int | Screen position (shared across 4K On/Off) |
| `maximized` | bool | Last non-fullscreen maximized state |
| `fullscreen` | bool | User fullscreen preference (default **false**) |

**First launch** (no `window` key in settings): windowed mode; client size = primary desktop resolution minus **48 px per edge**, clamped to ≥ **1360×768**; position centered on primary display.

**Restore on launch:** if **4K UI scaling** is On, use the 4K size set (seed `2 × client_*` if unset); otherwise use normal `client_*`. Restore saved position; if `maximized` was true when last closed, open maximized; if `fullscreen` is true, enter borderless desktop fullscreen immediately.

**Persist timing:** on every `WindowResized` and `WindowMoved` event, and on quit — written asynchronously on the `settings-coordinator` daemon thread (not the main thread). While fullscreen is active, do not overwrite stored windowed client dimensions from live resize events. While windowed, live size writes into the **active** scaling set only (4K On → `four_k_client_*`; Off → `client_*`).

Implementation: `src/ui/window_state.py`, `src/ui/window_controller.py`, `src/settings_coordinator.py`, `src/settings_store.py`.

#### Scenario: Second launch restores size and position

- GIVEN the player resized and moved the window, then quit
- WHEN the application launches again
- THEN the window opens at the saved client size for the active scaling mode and screen position

#### Scenario: First launch fits on screen

- GIVEN no prior `window` block in settings
- WHEN the application launches on a large monitor
- THEN the window opens windowed with margin from display edges
- AND client area is at least 1360×768

#### Scenario: Maximized close reopens maximized

- GIVEN the player closed the application while the window was maximized
- WHEN the application launches again
- THEN the window opens maximized

### Requirement: Fullscreen Toggle

The Options menu SHALL include a **Fullscreen: Off | On** row (default **Off**). Toggling SHALL take effect immediately using borderless desktop fullscreen (`tcod.sdl.video.Window.fullscreen`).

Exiting fullscreen SHALL restore the **session** non-fullscreen state from immediately before entering fullscreen (windowed size/position or maximized). Example: windowed → maximized → fullscreen → off → maximized again.

When exiting fullscreen into a **normal windowed** (not maximized) frame, position SHALL be clamped: if `x < 0` then `x = 0`; if `y < 30` then `y = 30` (same floors as the 4K UI scaling toggle). Restoring **maximized** SHALL skip that position apply.

Launching with saved `fullscreen: true` and no session snapshot SHALL restore from persisted `window` fields when fullscreen is turned off.

#### Scenario: Fullscreen toggle is immediate

- GIVEN the options screen is active
- WHEN the player enables fullscreen
- THEN the window enters fullscreen without restart

#### Scenario: Exit fullscreen restores prior mode

- GIVEN the window was maximized before fullscreen
- WHEN the player disables fullscreen in Options
- THEN the window returns to maximized

#### Scenario: Exit fullscreen clamps windowed position

- GIVEN fullscreen was entered from a windowed frame with `x < 0` or `y < 30`
- WHEN the player disables fullscreen
- THEN the restored windowed position has `x ≥ 0` and `y ≥ 30`

### Requirement: Dynamic Window Resize

The application window SHALL be resizable. On resize, move, and at startup, root console cell count SHALL be derived from client pixel size: `floor(pixel / (tile_px * tile_scale))`, clamped to a **minimum client area**. At stock `tile_scale` **2**, the floor is **1360×768** pixels; when effective `tile_scale` differs (e.g. 4K UI scaling On), the floor SHALL scale proportionally with cell size (OS title bar and borders are outside this client floor).

Layout SHALL be **re-resolved** from the active preset:

- **Fixed chrome** (preset widths/heights): sidebar width, message log height, status corner width, message log line count
- **Flexible:** map viewport absorbs shrink and growth first

The live `UILayout` SHALL propagate to `App`, `GameEngine`, and `RegionBundle` after each resize. The OS window SHALL NOT be shrinkable below the minimum client size (SDL minimum size + enforcement on resize events).

#### Scenario: Grow window enlarges map viewport

- GIVEN gameplay at minimum supported width
- WHEN the player enlarges the window
- THEN map viewport cell count increases
- AND sidebar width stays at the preset chrome width

#### Scenario: Shrink hits floor

- GIVEN a large window
- WHEN the player shrinks below the minimum client size
- THEN the window stops at the minimum
- AND layout remains usable (chrome preserved, map at least minimum flex)

### Requirement: Modal Placement

Narrative and inventory modals (vore, digestion, recap, game over, inventory flows, examine description, quit confirm) SHALL center on the **root console** (full playfield), and MAY visually cover sidebar and message log.

Examine and evoke **cursors** SHALL remain on the map viewport sub-console with camera offset (not root-centered modals).

#### Scenario: Vore modal covers full window

- GIVEN an active vore narrative modal
- WHEN the modal renders
- THEN the modal box is centered on the root console width and height

### Requirement: Menu Screen Anchoring

Main menu ASCII title art and option list SHALL use **block-anchored** horizontal placement so all lines shift together when the root console width changes. Per-line independent centering that causes single-row drift at certain widths is not permitted.

#### Scenario: Title rows move together on resize

- GIVEN the main menu at two different root console widths
- WHEN the title banner renders at both widths
- THEN relative horizontal offsets between title rows are identical
- AND only the shared block anchor shifts with width

## Acceptance checklist (summary)

1. ~2× text scale; eight-line message log; no legacy bottom status bar.
2. Map viewport smaller than full dungeon; camera follows player.
3. Sidebar: player HP exact; NPCs FOV-gated, two-line entries, coarse bars; evil under player, good at bottom.
4. Status corner: depth + stunned + engulfed.
5. JSON preset tuning; Options **Standard** / **Wide**; applies on new game.
6. Dynamic resize with 1360×768 client floor; map flexes, chrome fixed.
7. Window size, position, maximized, and fullscreen preference persist in `{user_data}/settings.json`; first launch uses desktop minus 48 px/edge.
8. Options fullscreen toggle (borderless desktop); exit restores prior windowed/maximized session state.
9. Modals on root console; cursors on map viewport.
10. Menu title/options block-anchored at variable widths.