# Proposal: UI Overhaul

## Why

The current HUD was built for an 80×44 **full-map** view with a 12×12 pixel tileset. Text is hard to read at normal zoom, the map wastes screen space showing tiles the player cannot act on at once, and player status is crammed into a single bottom status line above a 5-line message log. There is no way to tune panel sizes without editing scattered constants (`MAP_HEIGHT`, `HUD_MESSAGE_LINES`, `HP_BAR_WIDTH`, etc.).

Players need **larger, readable text**, a **player-centered map viewport**, a **dedicated right sidebar** for status and nearby NPCs, up to **8 message-log lines**, and **data-driven layout** so panel proportions can be adjusted in one place (and eventually chosen from presets) without rewiring render code.

## What Changes

### Readable display scale

- Double effective glyph height (~24 px tiles from the existing 12×12 sheet via `tile_scale=2`, or equivalent).
- Recalculate root console dimensions from layout config so the window size matches the designed panel grid.

### Configurable layout regions

- New **`data/ui_layout.json`** (and optional named presets) defining rectangular regions: map viewport, message log, right sidebar, status corner.
- A `UILayout` resolver computes character-cell rectangles from config; render code draws into **region sub-consoles** instead of assuming map origin `(0,0)` and HUD at `y = MAP_HEIGHT`.

### Player-centered map viewport

- **Logical dungeon** remains 80×44 (`MAP_WIDTH` × `MAP_HEIGHT`); generation and pathfinding unchanged.
- **Visible map** shows a smaller viewport (configurable width × height in cells) **centered on the player**, clamped to map bounds.
- Camera offset applied consistently to map tiles, entities, examine cursor, evoke target, engulfed overlay, and rune flash.

### Right sidebar

- **Upper block:** player display name, numeric HP, visual HP bar, stunned/engulfed flags.
- **Below player:** NPCs currently in player FOV (`game_map.visible`), each with name + condition estimate bar (PR11: two-line layout, ~6-wide coarse bar; player keeps exact HP).
  - **Evil** NPCs listed directly under the player block (nearest-first within cap).
  - **Good** NPCs listed at the **bottom** of the sidebar (nearest-first within cap).
  - **Neutral** NPCs in a middle band (see design.md — default proposal).
  - Per-alignment caps with overflow summary (e.g. `+2 more evil`).

### Bottom area rework

- Message log: up to **8 lines** in its own region (no status line above it).
- **Status corner** (bottom-right): floor depth plus player ailments/effects (stunned, engulfed now; buffs/debuffs later).
- Remove player name, HP, and depth from the legacy bottom status bar.

### Layout presets (Options menu)

- At least two named presets (e.g. **Standard**, **Wide sidebar**) selectable in Options and persisted in `{user_data}/settings.json`.
- Developer tuning remains a one-line JSON edit per region dimension.

## Out of Scope

- TrueType / proportional fonts (stay on CP437 tileset for v1).
- In-game drag-to-resize panels (presets + JSON only in v1).
- Minimap, equipment paper-doll, or full stat sheet in sidebar.
- Showing NPCs outside current FOV (explored memory only).
- Changing dungeon generation size, FOV radius formula, or combat rules.
- Touch / gamepad UI.

## Capabilities

### New

- `ui-layout` — region config, presets, camera viewport, sidebar panels

### Modified

- `core-roguelike` — HUD requirements (message log lines, depth placement, sidebar status)
- `main-menu` — readable scale on menu screens (same tile scale)

## Success Criteria

- Text is visibly ~2× prior height at default preset; message log shows 8 lines.
- Map viewport is smaller than full dungeon and stays centered on the player while moving.
- Sidebar shows player HP and capped FOV-visible NPC lists with correct evil/good ordering.
- Depth and player effects appear in bottom-right status corner, not in message-log or sidebar text.
- Layout region sizes changeable via `data/ui_layout.json` without editing render functions.
- Options preset switch changes layout after return to menu / new game (see design.md).
- Targeted tests per PR; full `pytest tests/` green on final acceptance PR.

## Decisions (locked 2026-07-02)

| Topic | Choice |
|-------|--------|
| Monitor space | Presets in v1; JSON structured for future dynamic resize |
| Viewport size | JSON-tunable; `48×34` initial starting point |
| NPC caps | Evil 4, good 3; neutral omitted from sidebar |
| Player effects | Status corner (depth + ailments/buffs), not sidebar flags |

## Decisions (PR11 design, 2026-07-02)

| Topic | Choice |
|-------|--------|
| Window resize | Bidirectional dynamic layout in **PR11** (map viewport flex; chrome floors from preset) |
| Sidebar NPCs | Two lines each (name, then bar); blank row between entities; padding top/bottom |
| NPC HP | ~6-wide estimate bar; fill count `0…6` via `round(6 * hp / max_hp)` (all counts reachable); player keeps exact `HP nn/nn` + full bar |
| Modals | Center on **root console** (full screen), not map viewport only |
| Status corner | **10** cells wide (`message_log.w` 70 to keep 80-col grid) |
| Standard player bar | Shorten `hp_bar_width` so line does not clip in 32-wide sidebar |
| Quit confirm | Modifier-only keys (e.g. bare Shift) do not show invalid-key message |
| Fullscreen toggle | Deferred to **PR13** |