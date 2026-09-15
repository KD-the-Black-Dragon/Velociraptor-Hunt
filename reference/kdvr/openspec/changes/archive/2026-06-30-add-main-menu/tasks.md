# Tasks: Main Menu

Implementation follows PR plan in [`design.md`](design.md). Check off as completed.

## PR 1: Menu shell and boot flow

- [x] App state machine; boot to main menu (not straight into dungeon)
- [x] Black screen, title, five options, highlight navigation
- [x] Exit terminates process; window close (X) same as Exit
- [x] Ctrl+Q on main menu is no-op
- [x] Tests + `testing-checklist-pr1.md`

## PR 2: New Game and player name

- [x] Name entry prompt (single-line, Backspace, max 24); Anonymous default; Escape cancel
- [x] `player_name` on engine; recap shows dynamic name (no score line)
- [x] HUD title shows player name instead of `GAME_TITLE`
- [x] Tests + `testing-checklist-pr2.md`

## PR 3: Options and persistence

- [x] Options screen; Oral Vore / Cock Vore / Anal Vore toggles; at-least-one rule
- [x] `{user_data}/settings.json` auto-save; load on boot (via `src/user_data.py`)
- [x] Remove OV forced-on; wire prefs to vore/digestion
- [x] Tests + `testing-checklist-pr3.md`

## PR 4: Flow integration

- [x] Ctrl+Q gameplay → quit confirmation (`Do you want to quit? (Y/n)`)
- [x] Capital Y → main menu; lowercase n → resume; invalid → error message
- [x] Quit confirmation during vore/digestion modals
- [x] Digestion recap Enter → main menu (not exit)
- [x] Load Game / High Scores stubs with "Coming soon" and back-out
- [x] Debug keys R / F2 / S unchanged in gameplay
- [x] Tests + `testing-checklist-pr4.md`

## PR 5: Spec and acceptance

- [x] Update `vore`, `digestion`, `core-roguelike` spec notes
- [x] `testing-checklists.md`, `acceptance-report.md`
- [x] Update `README.md`
- [x] Archive change; full test suite green