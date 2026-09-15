# Design: Tutorial page and first-run onboarding

## Resolved decisions

| Decision | Choice |
|----------|--------|
| Tutorial format | **Paginated** — no scrolling; Enter advances to next page |
| Tutorial page count | 2 content pages + 1 reminder page (Yes path only) |
| Vore in tutorial | Primary game-over mechanic; direct tone for vore enthusiasts — **not** framed as a content warning |
| Emphasis color | Light red for important lines (not a separate “warning” treatment for vore) |
| Runes | Brief: permanent stat bonuses |
| Goal | Get as deep as possible |
| Economy | No shops, XP, or levels (one brief mention) |
| Arrow keys | **Emphasize downside**; TYUGHJBNM critical for laptops without numpad |
| Defeat | “If your run ends, you start over.” |
| Potions / wands | Very powerful, single-use |
| Rest (`5`) | Rest in **isolated** areas |
| Downstairs escape | Keep as survival tip (monsters don’t follow) |
| Tutorial vs vore prefs | **Independent** — both are part of first-run; vore prefs always shown if not yet confirmed, whether tutorial was Yes or No |
| Vore prefs timing | Standalone screen after tutorial leg (or after prompt No); before main menu |
| Vore prefs repeat | First launch only; later changes via Options |
| First-run input | **Enter only** to advance (no Esc) through onboarding chain |
| Selection default | **No selection** on choice screens until first arrow key; Enter with no selection = no-op |
| Dismiss reminder | Only after first-run Yes path; not when reopening from Options |
| Options Tutorial | Same paginated Quick Start; returns to Options; no vore screen |
| Persistence | `tutorial_prompt_answered` + `vore_prefs_onboarding_complete` in `settings.json` |
| PR count | PR1 (full onboarding) |

### Hotkeys (tutorial copy vs shipped bindings)

Designer confirmed these belong in the Quick Start. **Shipped bindings:**

| Tutorial mention | Key |
|------------------|-----|
| Save | `Ctrl+S` |
| Quit to main menu | `Ctrl+Q` |
| Quick throw | `f` only (not `F` picker) |
| Wait one turn | `.` or `h` or numpad `5` |
| Close door | `c` |
| Examine | `x` |

*(Designer said “Ctrl+Q for save and quit” — tutorial will list **both** save and quit keys as separate lines matching actual controls.)*

---

## First-launch flow

```
Boot
 ├─ tutorial_prompt_answered == false?
 │    └─ TUTORIAL_PROMPT (Yes / No) — no default selection; Enter no-op until arrow
 │         ├─ No  → decline notice (Enter) ─┐
 │         └─ Yes → page 1 (Enter) → page 2 (Enter) → reminder (Enter) ─┐
 │                                                                      │
 ├─ vore_prefs_onboarding_complete == false?  ←─────────────────────────┘
 │    └─ VORE_PREFS (OV/CV/AV + confirm) — no default selection; Enter no-op until arrow
 │         └─ confirm row selected + Enter → MENU
 │
 └─ else → MENU
```

Tutorial prompt and vore prefs are **independent flags**. A first-time player always hits **both** legs (prompt, then vore prefs) unless they force-quit mid-chain.

- `tutorial_prompt_answered` — set on Yes or No confirm.
- `vore_prefs_onboarding_complete` — set only on **These settings are correct!**

Force-quit before either confirm leaves that flag false and replays that leg next launch.

---

## Persistence

| Field | Default | Set when |
|-------|---------|----------|
| `tutorial_prompt_answered` | `false` | Player confirms Yes or No on tutorial prompt |
| `vore_prefs_onboarding_complete` | `false` | Player confirms **These settings are correct!** on vore screen |

Location: `%LOCALAPPDATA%/KD's Vore Roguelike/settings.json` (additive keys; default false on load if missing).

Vore toggle values themselves use existing `vore_content.enabled` in the same file.

---

## App phases (planned)

| Phase | When |
|-------|------|
| `TUTORIAL_PROMPT` | `tutorial_prompt_answered` is false at boot |
| `TUTORIAL` | Yes on prompt, or Options → Tutorial |
| `VORE_PREFS_ONBOARDING` | `vore_prefs_onboarding_complete` is false after prompt/tutorial leg |
| `MENU` | Onboarding complete |

---

## First-run tutorial prompt

Unchanged from original spec:

- Blank screen; exact copy:
  - `Welcome to K.D.'s Vore Roguelike.`
  - `Would you like a tutorial?`
- `Yes, please!` / `No, I'm good.`
- Nothing selected until Up/Down (or numpad 8/2)
- Selected row: `> ` + soft yellow background
- Hint: `Up/Down to choose, Enter to confirm`

**No:** screen `If you change your mind, select 'Tutorial' in the Options menu.` → **Enter** → vore prefs → menu.

Choice screens (prompt, vore prefs): `highlight` starts `None`; first Up/Down sets highlight; **Enter with no selection is a no-op**.

---

## Quick Start tutorial (paginated)

- Proportional log font when available; CP437 fallback
- **No scroll** — each page fits one screen
- **First-run:** Enter is the **only** way to advance (no Esc). Content pages (1, 2, reminder) advance on Enter without requiring a prior arrow selection.
- **Options replay:** Esc returns to Options from tutorial pages.

### Page 1 (content)

- Title: **Quick Start** (or similar)
- What this is: dungeon RPG; `@` is you; goal is **get as deep as possible**
- No shops, XP, or levels
- Sample ASCII map (`@`, monster letter, `!`, `>`)
- Turn-based; no time limit; if your run ends, you start over
- Footer hint: `Enter: next page`

### Page 2 (content)

- Movement: **numpad best**; **TYUGHJBNM essential** on laptops without numpad
- **Arrows omit up/down** — emphasize this hurts survival
- Walk into monsters to attack
- `x` examine; `.` / `h` / numpad `5` wait one turn; `c` close door
- `q` quaff `!`; `v` evoke `/`; `w` wield; `W` wear; `f` throw
- Numpad `5` — wait one turn (distinct from top-row `5`)
- `5` (key above **T**) — rest in **isolated** areas
- `>` downstairs on `>` glyph
- F1 / `?` for full command list
- `Ctrl+S` save; `Ctrl+Q` quit to menu
- Runes: three per floor; **permanent stat bonuses**
- Potions and wands: very powerful, **single-use**
- **Vore / digestion** — when you are vulnerable, monsters can vore you; **if digested, the run ends** (direct; light red emphasis — not a warning label)
- Survival tips: narrow halls; rest isolated; loot runes/items; potions/wands in trouble; run downstairs (monsters don’t follow)
- Footer: `Enter: next page` (Yes/first-run) or `Enter: next | Esc: back` (Options)

### Page 3 (reminder — first-run Yes path only)

- `You can view the tutorial again anytime from Options → Tutorial.`
- Footer: `Enter: continue`

After Enter → vore prefs screen (if not complete) → main menu.

### Options → Tutorial

- Same page 1 and page 2 only (no page 3 reminder)
- Esc from tutorial returns to Options
- Does not show vore onboarding screen

---

## Vore preferences screen (first launch)

Standalone full screen — **only**:

| Row | Behavior |
|-----|----------|
| Oral Vore | Toggle ON/OFF (existing vore pref codes) |
| Cock Vore | Toggle ON/OFF |
| Anal Vore | Toggle ON/OFF |
| These settings are correct! | Confirm — persists prefs + sets `vore_prefs_onboarding_complete` |

- **No default selection** — `highlight` starts `None`; Enter is no-op until first Up/Down
- Up/Down moves highlight; Left/Right or Enter toggles the highlighted vore row
- **These settings are correct!** is the final row; Enter on that row (when highlighted) finishes onboarding
- At least one type must remain enabled (existing Options rule)
- First-run: Enter only (no Esc)
- Proportional log font; readable, not fixed-width
- Short intro line optional (e.g. “Choose which vore types can appear in your run.”) — keep to one line

---

## Options menu change

New row **Tutorial** between Fullscreen and Mods → opens paginated `TUTORIAL` (pages 1–2).

---

## Explicitly omitted from Quick Start

- HP definition, field of view / walls
- Inventory screen (`i`), drop (`d`), pickup (`,`)
- Throw picker (`F`)
- Good allies / Come here (`1`)
- Message log overlay (`Ctrl+P`)
- Difficulty, UI layout, fullscreen, mods
- Macguffin / victory detail beyond “go deep”

---

## Files (planned)

| File | Role |
|------|------|
| `src/tutorial_prompt.py` | Prompt state, copy, handlers |
| `src/ui/tutorial_screen.py` | Paginated pages, content lines |
| `src/ui/vore_prefs_onboarding.py` | First-run vore screen |
| `src/settings_store.py` | New persistence flags |
| `src/app.py` | Onboarding phase routing |
| `src/options_menu.py` | Tutorial row |
| `openspec/specs/onboarding/spec.md` | Live spec (lands with PR1) |

## Testing

- Prompt selection + persistence
- Paginated Enter flow (Yes path 3 pages)
- No path → notice → vore prefs → menu
- Vore prefs confirm + cannot disable last type
- Options Tutorial: 2 pages, Esc back
- Boot skips onboarding when flags true