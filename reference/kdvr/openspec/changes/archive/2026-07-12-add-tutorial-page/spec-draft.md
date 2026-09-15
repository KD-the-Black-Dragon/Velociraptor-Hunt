# Onboarding (draft — moves to `openspec/specs/onboarding/spec.md` on PR1)

## Purpose

First-run welcome flow, paginated Quick Start tutorial, and vore preference selection for new players.

## Requirements

### First-run tutorial prompt

- WHEN the game starts AND `tutorial_prompt_answered` is false, the application SHALL show the tutorial prompt instead of the main menu.
- The prompt SHALL display exactly:
  - `Welcome to K.D.'s Vore Roguelike.`
  - `Would you like a tutorial?`
- The prompt SHALL offer `Yes, please!` and `No, I'm good.` with no option selected until Up/Down (or numpad 8/2).
- The selected option SHALL use `> ` prefix and soft yellow background highlight.
- A hint SHALL explain Up/Down and Enter.
- Enter with no selection SHALL do nothing.
- WHEN the player confirms **No**, the application SHALL show `If you change your mind, select 'Tutorial' in the Options menu.` then advance on Enter to vore prefs (if not complete) then the main menu.
- The tutorial prompt and vore preferences onboarding SHALL be independent; both SHALL be shown on the overall first-run experience regardless of Yes or No.
- On first-run onboarding screens that require a choice, nothing SHALL be selected until the player uses an arrow key; Enter with no selection SHALL have no effect.
- On first-run onboarding, Enter SHALL be the only way to advance (no Esc).
- WHEN the player confirms **Yes**, the application SHALL open the paginated Quick Start tutorial.
- WHEN the player confirms Yes or No, `tutorial_prompt_answered` SHALL be persisted.
- Force-quit before answering SHALL NOT set `tutorial_prompt_answered`.

### Quick Start tutorial

- The tutorial SHALL use the proportional log font when available.
- The tutorial SHALL NOT scroll; each page SHALL fit one screen.
- Enter SHALL advance to the next page.
- **Page 1** SHALL cover: dungeon RPG premise; `@` player; goal to get as deep as possible; no shops/XP/levels; sample map; turn-based play; no time limit; run ends → start over.
- **Page 2** SHALL cover: numpad and TYUGHJBNM (emphasize laptop/no-numpad need); arrow up/down limitation; melee by moving into monsters; `x` examine; `.`/`h`/numpad `5` wait one turn; `c` close door; potions/wands/items; top-row `5` (above T) rest in isolated areas; downstairs; F1/`?`; Ctrl+S save; Ctrl+Q quit; runes as permanent stat bonuses; single-use potions/wands; vore/digestion as run-ending mechanic; survival tips including running downstairs.
- Important lines MAY use light red emphasis.
- **Page 3** (first-run Yes path only) SHALL remind the tutorial is available from Options → Tutorial.
- WHEN opened from Options, the tutorial SHALL show pages 1–2 only; Esc SHALL return to Options.

### Vore preferences (first launch)

- WHEN `vore_prefs_onboarding_complete` is false after the tutorial leg (or after prompt No), the application SHALL show a standalone vore preferences screen before the main menu.
- The screen SHALL offer only: Oral Vore, Cock Vore, Anal Vore toggles, and `These settings are correct!`
- Nothing SHALL be selected until the player uses an arrow key; Enter with no selection SHALL have no effect.
- Confirm SHALL require highlighting **These settings are correct!** and pressing Enter; it SHALL persist vore content prefs and set `vore_prefs_onboarding_complete`.
- At least one vore type SHALL remain enabled.
- The screen SHALL NOT appear again on later launches (Options vore rows remain for changes).

### Options access

- Options SHALL include a **Tutorial** row opening the same paginated Quick Start (without page 3 or vore onboarding).