# Manual checklist — Main Menu PR 1

Run: `python -m src.main`

## Menu shell (this PR)

- [ ] Application opens to a **black screen** with the title **KD's Vore Roguelike** centered (prominent)
- [ ] Five options appear **near the bottom**: New Game, Load Game, High Scores, Options, Exit
- [ ] **Up / Down** move the `>` highlight between options (wraps at top/bottom)
- [ ] **Enter** on **Exit** closes the application
- [ ] Closing the window (**X**) closes the application (same as Exit)
- [ ] **Ctrl+Q** on the main menu does **nothing** (stays on menu)
- [ ] **Enter** on **New Game** starts a dungeon run (temporary bridge until PR 2 name entry)
- [ ] **Enter** on Load Game / High Scores / Options does not leave the menu yet (no-op)

## Regression (after starting New Game)

- [ ] Movement, FOV, combat, vore, digestion, and message log behave as before
- [ ] **Ctrl+Q** during gameplay still exits the process (quit confirmation arrives in PR 4)
- [ ] Digestion game over **Enter** still exits the process (menu return arrives in PR 4)
- [ ] Debug keys **R**, **F2**, **S** still work in gameplay