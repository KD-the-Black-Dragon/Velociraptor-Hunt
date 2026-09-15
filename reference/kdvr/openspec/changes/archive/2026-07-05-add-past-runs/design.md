# Design: Game Over Stats + Past Runs

**Note (post-archive):** Past runs now live at `{user_data}/past_runs.json` via `src/user_data.py` (not `data/past_runs.json` in the project tree).

## Design philosophy

A completed run is a **story beat**, not a leaderboard entry. Record it once at game over, show the recap immediately, and keep an append-only local history the player can scroll through later. Abandoned runs (quit-to-menu) are not “completed” and are not recorded.

---

## Resolved decisions

| # | Decision |
|---|----------|
| 1 | **Record trigger** — append a Past Run only inside `GameOverState.open()` (digestion today; future victories use the same hook) |
| 2 | **No abandoned runs** — Ctrl+Q quit-to-menu does **not** create a Past Run |
| 3 | **Monsters defeated** — count only defeats where the **player** dealt the finishing blow (melee via `_perform_attack`, wand via `perform_wand_attack`, struggle while engulfed in `vore.py`). NPC-vs-NPC defeats and digestion removals do **not** count |
| 4 | **Runes collected** — floor runes stepped on and consumed this run (`try_activate_floor_rune` success); increment a run-level counter by 1 per activation |
| 5 | **Depth** — `floor_depth` at the moment game over opens |
| 6 | **Turn count** — drop `GameOverState.score` / `player_turn_count` from recap and Past Runs entirely |
| 7 | **Ending text** — structured `{ending_kind, ending_detail}`; format to display string via a single formatter (today: `digested` + `wolf` → `"Digested by wolf"`; future: `macguffin` → `"Collected the macguffin"`) |
| 8 | **Sort order** — depth descending, then runes descending, then monsters defeated descending, then date ascending (older first). Remaining ties: stable / unconcerned |
| 9 | **Date** — local machine calendar date at record time, `MM/DD/YYYY` (no time-of-day) |
| 10 | **Capacity** — max **65535** entries; when full, drop the **oldest** entry before append |
| 11 | **Storage** — `{user_data}/past_runs.json` (via `src/user_data.py`); per-user like saves |
| 12 | **Menu gating** — `PastRunsStore.probe()` on menu enter; omit **Past Runs** when file has zero entries (same pattern as Load Game) |
| 13 | **Menu label** — **Past Runs** replaces **High Scores** everywhere (menu, tests, specs) |
| 14 | **Past Runs UI** — full-screen scrollable table; scroll keys match extended log overlay (arrows line, PgUp/PgDn page, Escape back) |
| 15 | **Save/load** — run stat counters are part of the autosave snapshot so mid-run load preserves counts |

---

## Run statistics (`RunStats`)

Lightweight counters on `GameEngine`, reset on `new_game()`, restored from save snapshot.

```python
@attrs.define
class RunStats:
    monsters_defeated: int = 0
    runes_collected: int = 0
```

### Increment sites

| Counter | When |
|---------|------|
| `monsters_defeated` | Evil NPC removed after player finishing blow in `_perform_attack` (`Player in attacker.tags`) |
| `monsters_defeated` | Evil NPC removed after `perform_wand_attack` (always player) |
| `monsters_defeated` | Predator removed after player struggle defeat in `vore.py` (`fire_entity_defeated(predator)` path) |
| `runes_collected` | `try_activate_floor_rune` returns `True` (at least one rune entity consumed) |

Do **not** increment on `perform_npc_ranged_attack` defeats unless the attacker is the player (no player ranged path today).

Helper on engine: `engine.run_stats.record_monster_defeated()` / `record_rune_collected()` to keep call sites one-liners.

### Save snapshot fields

Add to `build_run_snapshot` / `apply_run_snapshot`:

```json
"run_stats": {
  "monsters_defeated": 12,
  "runes_collected": 3
}
```

Default `{0, 0}` when key missing (backward-compatible with existing saves).

---

## Game over ending model

```python
@attrs.define(frozen=True)
class GameOverEnding:
    kind: str       # e.g. "digested", "macguffin", "boss"
    detail: str = ""  # predator display name for "digested"; often "" for fixed phrases
```

### Display formatter

```python
def format_game_over_ending(ending: GameOverEnding) -> str:
    match ending.kind:
        case "digested":
            return f"Digested by {ending.detail}"
        case "macguffin":
            return "Collected the macguffin"
        case "boss":
            return "Defeated the boss"
        case _:
            return ending.detail or ending.kind
```

Today’s digestion path sets `GameOverEnding(kind="digested", detail=entity_display_name(predator))`.

Future modules only supply a new `kind` (and optional `detail`); no Past Runs schema change required.

### `GameOverState` shape

Replace `score` and `digested_by` with:

| Field | Type | Notes |
|-------|------|-------|
| `player_name` | `str` | unchanged |
| `ending` | `GameOverEnding` | structured reason |
| `monsters_defeated` | `int` | copied from `RunStats` at open |
| `runes_collected` | `int` | copied from `RunStats` at open |
| `depth` | `int` | `floor_depth` at open |

`open()` signature gains stats + ending; still accepts `save_store` for autosave wipe.

---

## Game over modal (render)

`render_game_over()` lines (centered modal, CP437-safe):

```text
GAME OVER

{player_name}
{format_game_over_ending(ending)}

Monsters defeated: {n}
Runes collected: {n}
Depth: {depth}

Press Enter to return to menu
```

Remove unused `score` parameter and any turn-count display.

---

## Past runs persistence

### File layout

```text
{user_data}/past_runs.json
```

### Document envelope

```json
{
  "past_runs_format_version": 1,
  "runs": [
    {
      "character_name": "Alex",
      "ending_kind": "digested",
      "ending_detail": "wolf",
      "monsters_defeated": 12,
      "runes_collected": 3,
      "depth": 7,
      "date": "07/05/2026"
    }
  ]
}
```

- `runs` is append-only on disk (newest at end).
- Display sort is computed at read/render time (not rewritten on append).
- Invalid / corrupt file: treat as empty history (`probe()` false); optional log diagnostic; do not crash menu.

### `PastRunsStore`

| Method | Behavior |
|--------|----------|
| `probe()` | `True` when file exists and `runs` has ≥1 valid entry |
| `load_runs()` | Parse, validate entries, return list of `PastRunRecord` |
| `append(record)` | Enforce cap 65535 (drop oldest), atomic write via temp + `os.replace` |
| `sorted_for_display(runs)` | Apply sort order from decision #8 |

`GameOverState.open()` calls `past_runs_store.append(...)` after fields are set, **before or after** save wipe (order irrelevant).

`App` owns a `PastRunsStore` instance (like `SaveCoordinator`), passed into engine game-over path or called from `open()` via injected store.

---

## Past Runs screen

Replace `AppPhase.STUB_SCORES` with `AppPhase.PAST_RUNS`.

### List layout (two lines per run)

No column header row. Scroll content:

```text
PAST RUNS

{Name} - {ending} - {date}
Depth {depth} - {runes} Runes - {monsters} Enemies Defeated

{next run...}
```

- Blank line after title before the first entry
- Blank line between runs (not after the last)
- Lines truncate with ellipsis if wider than the console

### Scroll behavior

Reuse `clamp_scroll_offset`, `apply_line_scroll`, `apply_page_scroll` from `src/ui/log_overlay.py`.

`PastRunsOverlayState` (or inline state on `App`):

- `scroll_offset: int`
- On enter: `scroll_offset = 0` (top = deepest run after sort)
- Keys: `LOG_OVERLAY_LINE_*`, `LOG_OVERLAY_PAGE_*`, Escape → menu
- Footer: `Esc: back | Arrows: line | PgUp/PgDn: page` (same spirit as log overlay)

Render via `render_past_runs_screen(console, runs, state)` on root console (like stub screen today).

### Menu integration

```python
def build_menu_options(*, load_available: bool, past_runs_available: bool) -> tuple[str, ...]:
    options = ["New Game"]
    if load_available:
        options.append("Load Game")
    if past_runs_available:
        options.append("Past Runs")
    options.extend(["Options", "Exit"])
    return tuple(options)
```

`_on_menu_enter()` probes both save store and past runs store.

`MenuAction.HIGH_SCORES` → `MenuAction.PAST_RUNS` (rename enum + handler).

---

## Flow diagram

```text
Player digested
  → digestion modal completes
  → GameOverState.open(
        ending=GameOverEnding("digested", predator_name),
        stats from RunStats,
        depth=floor_depth,
        save_store → delete_all(),
        past_runs_store → append(record),
     )
  → render_game_over (extended stats)
  → Enter → App._return_to_menu()
  → menu probe: Past Runs now visible
```

```text
Ctrl+Q → quit → menu
  → no Past Run append
  → Load Game still available if save exists
```

---

## Module layout

```text
src/
  run_stats.py              # RunStats dataclass
  game_over_ending.py       # GameOverEnding + format_game_over_ending
  past_runs/
    schema.py               # PastRunRecord, format version
    store.py                # PastRunsStore read/write/probe/sort
  ui/
    past_runs_screen.py     # scroll state, render, input handler
```

Touch existing:

- `src/systems/digestion.py` — `GameOverState`
- `src/systems/render.py` — `render_game_over`
- `src/systems/combat.py`, `vore.py`, `floor_runes.py` — stat increments
- `src/engine.py` — wire stats, game over open, render args
- `src/menu.py` — Past Runs option + gating
- `src/app.py` — phase, probe, screen
- `src/save/snapshot.py` — persist `run_stats`
- `src/user_data.py` — `PAST_RUNS_PATH` (`{user_data}/past_runs.json`)
- tests — menu gating, store round-trip, sort order, game over render, stat increments

---

## Testing notes

| Area | Automated |
|------|-----------|
| `format_game_over_ending` | unit tests for digested + future kinds |
| `PastRunsStore` | append, cap eviction, probe, corrupt file → empty |
| `sorted_for_display` | multi-field tie-break order |
| `build_menu_options` | past runs omitted when empty |
| `render_game_over` | stats lines present; no score/turn line |
| Stat increments | targeted tests: wand defeat credits player; NPC melee without player does not |

Manual playtest per PR checklist: die once → recap stats → Past Runs row → scroll with many entries.

---

## Risks / mitigations

| Risk | Mitigation |
|------|------------|
| Missed increment site for player defeats | Central `record_monster_defeated()`; grep `fire_entity_defeated` call sites in PR1 review |
| Wide table on narrow console | Truncate columns; header still readable at 80 cols |
| Save format drift | Optional `run_stats` key with defaults on load |