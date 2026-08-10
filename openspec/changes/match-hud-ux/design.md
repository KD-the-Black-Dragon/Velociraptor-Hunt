# Design: Match HUD layout + reaction panel + ally bump no-op

**Change:** `openspec/changes/match-hud-ux/`  
**Parent:** foundation match present (`src/ui/log_present.py` `present_match_frame`, `src/match_session.py` text helpers + `_player_bump`)  
**Canon:** UI fonts, combat log vs modal (DESIGN_CANON §2, reaction modal)

---

## Goals

1. Bottom of screen = **action log only**.
2. Meters and match status sit **to the right of the map**.
3. Incoming attack UI is a **modal panel** in a reserved **low-right** area (not the log stream; not covering map/meters/log).
4. Bump into ally = **no-op** + named message; **no AUT**.

## Non-goals

- Perfect pixel-final layout on first pass (iterate position with designer).
- Reworking dungeon/PLAY sidebar (KDVR) beyond reuse of layout regions.
- Changing reaction *options* or combat resolution (only presentation + ally bump).

---

## Current behavior (code facts)

| Area | Today |
|------|--------|
| Present | `present_match_frame` blits the tile map, then draws **all** `match_text_lines` starting at `y = map_height` (full panel width), with an opaque band under the map only. |
| Content | One list: HP/AUT → card → crowd → AP/Bal → injuries → **INCOMING block** → grapple → talk/ability → **Log** + last 8 messages. |
| Layout JSON | `data/ui_layout.json` already defines `map_viewport`, `sidebar`, `message_log`, `status_corner` — **match fight present ignores these for HUD placement**. |
| Ally bump | `_player_bump` → any blocker → `_player_melee_smart` (full attack AUT). |

---

## Target layout (fight phase)

Use **layout regions** (from active `UILayout`) as the authority for pixel placement when proportional log font is on. Approximate intent:

```text
┌─────────────────────────────┬──────────────────────┐
│                             │  STATUS (sidebar)    │
│         MAP (tiles)         │  HP / AUT            │
│                             │  AP / Balance        │
│                             │  Card / crowd / …    │
│                             │  Injuries / grapple  │
│                             │  (non-modal prompts) │
├─────────────────────────────┴──────────┬───────────┤
│  ACTION LOG (message_log)              │ REACTION  │
│  recent fight lines only               │ (modal;   │
│                                        │  low-right│
│                                        │  when on) │
└────────────────────────────────────────┴───────────┘
  footer keys (centered, bottom edge) — existing footer string
```

### Region mapping

| Content | Region | Notes |
|---------|--------|--------|
| Map + glyphs | Existing tile console draw (map cells) | Unchanged philosophy: tiles only on CP437 layer |
| HP, AUT, AP, balance, card label, patron short line, crowd, diff, injuries, downed recovery, grapple **status** (not full key list if it fights for space), ability/talk **one-line** prompts | `sidebar` (right of map) | Log font; top-down stack; clip/ellipsis if overflow |
| Message log entries only | `message_log` | Prefer full bottom width **except** when reaction panel is active, then leave right strip free |
| INCOMING announce + 1–4 choices / dodge dir | `status_corner` **or** expanded low-right rect | Prefer a dedicated helper `match_reaction_panel_rect(layout)` so we can widen beyond 10×10 cells without renaming JSON in PR1 if needed |
| Footer | Bottom edge of panel (existing) | Keep `match_footer_text` |

**When reaction is inactive:** action log may use the full bottom band (`message_log` + `status_corner` combined) so log width does not shrink permanently.

**CP437 fallback:** same logical split: print status in the right column of the console under/ beside map bounds; log on bottom rows; reaction block in lower-right cells. Accept uglier packing if space is tight.

### Content ownership (split helpers)

Replace the single mixed stream with pure functions (names flexible):

- `match_status_lines(session)` — meters + match meta (no log, no INCOMING body).
- `match_log_lines(session)` — last N message_log entries only (N from layout / constant).
- `match_reaction_modal_lines(session) | None` — INCOMING block when `pending_reaction` and PC not grapple-held.
- Keep `match_footer_text` as today.

Grapple **controls** and talk/ability pick lists: prefer **status column** (or full-screen text modes already used for ability list / recap). Do **not** put them in the action log.

---

## Reaction modal behavior

| Rule | Detail |
|------|--------|
| When | `pending_reaction is not None` and PC is not grappled prey (same as today). |
| Content | “INCOMING!”, announce line, then choices or dodge-direction prompt. |
| Placement | Low-right reserved rect; opaque background so readable; must **not** cover map tiles, primary status meters, or action log lines. |
| Input | Unchanged (`1–4`, dodge dir, Esc cancel dodge pick). |
| Iteration | Rect may be tuned after playtest (padding, width, height). |

This fulfills DESIGN_CANON: **modal** = incoming announce; **log** = impacts/near-misses only.

---

## Ally bump no-op

In `_player_bump` (and crawl path if it would strike):

```text
if target is ally (session.is_ally(target)):
    message_log: "{Name} is standing there."
    return  # no commit_action, no process_npc_until_player
```

| Detail | Choice |
|--------|--------|
| Name | Ally display name via existing match naming (`entity_log_name` / `DisplayName`); sentence-start capitalization as natural: **“Brakus is standing there.”** |
| Message home | Prefer `src/messages.py` helper for the template (project rule). |
| AUT | **None** |
| Balance / AP | Unchanged |
| Bump enemy | Unchanged smart melee |
| Bump wall / void | Existing “can't go that way” |
| Downed crawl into ally | Same no-op + same message (not “too exhausted to strike”) |

Friendly fire is **not** in scope; allies are never valid melee targets via bump.

---

## Implementation notes

- Prefer wiring **layout regions** over hardcoding pixel offsets from `game_map.height` alone. Map height still defines where tiles end; sidebar x starts at `layout.region("sidebar").x` (or map width if arena is smaller than viewport — **status should sit in the empty right gutter**, i.e. max(map drawn width, layout map_viewport) … use layout sidebar rect so empty space right of a 20×20 arena is used even when viewport is wider).
- Arena is ~20×20 today while viewport is ~57×34: **right gutter is large** — that is the intended home for meters.
- Performance: present path already rebuilds a PIL image each frame; splitting draws into 2–3 blits is fine. Avoid O(n) work beyond current.

---

## Testing

| Automated | Manual |
|-----------|--------|
| Ally adjacent bump: world AUT unchanged; message contains ally name; enemy still attackable | Open match: meters right of map; bottom is log |
| Unit/present helper tests if pure rect/split functions are testable without SDL | Trigger reaction: panel low-right; log still visible; map free |
| | Iterate position if clipped |

---

## Resolved decisions

| Topic | Decision | Date |
|-------|----------|------|
| Bottom band | Action log only | 2026-08-04 (designer request) |
| Meters | Right of map | 2026-08-04 |
| Reaction UI | Dedicated low-right modal; not in log; iterate position | 2026-08-04 |
| Ally bump | No-op + `"{name} is standing there."` | 2026-08-04 |

---

## Open (non-blocking)

| Topic | Default if unstated |
|-------|---------------------|
| Exact reaction panel size | Start ~ status_corner widened (~20–28 cells wide, ~8–10 rows); tweak after playtest |
| Talk / ability multi-line menus | Status column first; overflow → temporary expand into lower status |
| Message via messages.py | Yes |
