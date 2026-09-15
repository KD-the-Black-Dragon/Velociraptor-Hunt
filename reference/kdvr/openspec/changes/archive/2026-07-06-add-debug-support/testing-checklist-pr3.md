# Manual checklist — PR3 (session milestones)

Run game: `python -m src.main`

Automated: `pytest tests/test_session_log_milestones.py -q`

Open the latest `{user_data}/logs/session_*.log` after each scenario.

## New game

- [ ] Lines appear in order: `Started new game` → `Seed: …` → `Entered floor 1`

## Floor change

- [ ] Descend stairs → `Entered floor N` for each new depth

## Load game

- [ ] Load autosave → `Loaded game` in session log

## Pickup

- [ ] Pick up a floor item → `Collected {name}`

## Defeat

- [ ] Defeat an enemy (melee or wand) → `Defeated {name}`

## Game over

- [ ] Die or digest → `Game over`

## Menu navigation

- [ ] Ctrl+Q confirm to menu → `Quit to menu`
- [ ] Exit game (menu or window X) → `Quit` at end of session file (after PR4 adds conditional Quit; may be absent until PR4)

## Debug noise

- [ ] Press R (debug regen) → `Dungeon regenerated` only (no duplicate Seed/floor 1 spam)

## Regression

- [ ] PR2 validation still works on startup