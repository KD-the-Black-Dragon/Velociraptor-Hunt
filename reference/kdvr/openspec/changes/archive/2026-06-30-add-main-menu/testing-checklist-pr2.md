# Manual checklist — Main Menu PR 2

Run: `python -m src.main`

## Name entry (this PR)

- [ ] **New Game** opens a black **name entry** screen (not straight into dungeon)
- [ ] Prompt shows **Enter your name:** with a `>` input line and blinking `_` cursor
- [ ] Typing adds printable characters; **Backspace** deletes
- [ ] Name is capped at **24** characters
- [ ] **Enter** with a name starts the run; that name appears in the **HUD** (replaces `KD's Vore Roguelike`)
- [ ] **Enter** with blank or whitespace-only name starts as **Anonymous** in HUD
- [ ] **Escape** cancels and returns to the main menu without starting a game
- [ ] **Ctrl+Q** on name entry does nothing (stays on screen)

## Recap (this PR)

- [ ] After player digestion, recap shows your **display name** and **Digested by …** fate
- [ ] Recap does **not** show score / turns survived
- [ ] Recap **Enter** still exits the process (menu return is PR 4)

## Regression

- [ ] Main menu shell (PR 1): title art, navigation, Exit, window close
- [ ] Gameplay movement, combat, vore, digestion unchanged
- [ ] Debug keys **R**, **F2**, **S** still work