# Design: Main Menu

**Note (post-archive):** Settings now persist to `{user_data}/settings.json` via `src/user_data.py` (not `data/settings.json` in the project tree).

## Proposed architecture

```text
main.py
  └─ AppState machine (MENU | NAME_ENTRY | PLAY | OPTIONS | STUB_LOAD | STUB_SCORES | QUIT_CONFIRM | GAME_OVER)
       ├─ MenuController — input + render for non-play states
       ├─ SettingsStore — load/save VoreContentPreferences (+ future keys)
       └─ GameEngine — unchanged dungeon logic; receives player_name + prefs on new_game()
```

Launch → **MENU**. New Game → **NAME_ENTRY** → **PLAY**. Options → **OPTIONS** → MENU. Digestion recap → **GAME_OVER** → Enter → MENU. Ctrl+Q in PLAY → **QUIT_CONFIRM** → `Y` → MENU, `n` → PLAY.

## Resolved decisions

| Topic | Decision |
|-------|----------|
| Menu navigation | Up/Down highlight; Enter activate |
| Name entry keys | Printable ASCII; Backspace; Enter confirm; Escape cancel |
| Name entry layout | Single-line prompt (user had no preference) |
| Max name length | 24 characters |
| Blank name | Trim whitespace; empty → `Anonymous` silently |
| Options navigation | Up/Down between rows; Left/Right or Enter toggles highlighted type |
| Options UI labels | **Oral Vore**, **Cock Vore**, **Anal Vore** (map to OV/CV/AV internally) |
| Options save | Write `{user_data}/settings.json` on every toggle |
| OV toggle | OV may be disabled when CV or AV stays on (supersedes forced-OV rule) |
| Stub back-out | Escape and Enter both return to menu |
| Stub content | Show **"Coming soon"** line (not blank) |
| Ctrl+Q on main menu | **No-op** (does not exit) |
| Ctrl+Q during gameplay | **Quit confirmation** — see below |
| Quit confirmation | Prompt: `Do you want to quit? (Y/n)`; capital `Y` → MENU; lowercase `n` → PLAY; else error message |
| Quit confirm during modals | **No-op** — Enter-only while vore/digestion/recap modal is up |
| Title rendering | Centered title using large CP437-safe text (double-height or padded spacing — not Unicode) |
| HUD player name | **In scope** — replace `GAME_TITLE` in `render_hud` with player display name |
| Recap score | **Out of scope** — do not show turns survived or score |
| Debug keys | Keep **R**, **F2**, **S** during gameplay |
| Window close (X) | Same as **Exit** — terminate process |
| Vore prefs scope | **Global** initiation filter; snapshot on new game into `GameEngine.vore_content_prefs` |
| Vore prefs vs digestion | Prefs gate **new vore attempts** only (`should_attempt_vore`, `pick_narrative_type`). Engulfed follow-through uses `Predator.narrative_type` — **not** live prefs |
| Prefs vs spawn | No spawn-table filtering in v1; disabled types mean predators **skip initiation**, not removal from the dungeon |
| Save/load prefs | Deferred: future saves store run prefs; Load restores save, Options stays global for new games |

### Quit confirmation flow

```text
PLAY (or modal) --Ctrl+Q--> QUIT_CONFIRM
  Y --> MENU (discard run)
  n --> PLAY (resume)
  other --> show "Please type capital 'Y' or lowercase 'n' only." (stay in QUIT_CONFIRM)
```

Rendering: overlay or dedicated sub-state; gameplay input blocked until resolved.

## VoreContentPreferences change

Remove OV forced-on in `is_enabled`. Enforce **at least one of {OV, CV, AV}** in Options UI only (toggle no-op when last enabled). `pick_narrative_type` already returns `None` if pool empty — must not occur if UI enforces rule.

**Initiation only:** `enabled_narrative_types` / `pick_narrative_type` / `should_attempt_vore` consult prefs. Digestion (`player_digestion_modal_line`, NPC complete pools) reads `Predator.narrative_type` set at engulf — never live prefs.

**Run snapshot:** `App` passes `settings.vore_content` into `GameEngine(...)` at new game; engine keeps that copy for the run.

Update `openspec/specs/vore/spec.md` on implementation (PR 5).

## Persistence (settings.json sketch)

```json
{
  "vore_content": { "enabled": ["OV", "CV", "AV"] }
}
```

Default: all three enabled. Missing file → defaults.

## PR plan

| PR | Scope |
|----|--------|
| 1 | App state shell, menu render/nav, Exit, window quit, boot to menu; Ctrl+Q no-op on menu |
| 2 | New Game name entry + `player_name` through engine/recap + HUD title |
| 3 | Options UI (spelled-out labels), prefs persistence, vore hookup, OV toggle rule |
| 4 | Ctrl+Q quit confirmation; digestion recap → menu (no score); stub screens with "Coming soon" |
| 5 | Spec acceptance, vore/digestion/core updates, archive |

## Code touchpoints

| Area | File(s) |
|------|---------|
| App loop / state | `src/main.py` |
| Gameplay / recap | `src/engine.py` |
| HUD title | `src/systems/render.py` (`render_hud`, `GAME_TITLE`) |
| Game over state | `src/systems/digestion.py` (`GameOverState`) |
| Prefs | `src/constants.py` (`VoreContentPreferences`) |