# Manual checklist — PR9

Run: `python -m src.main`

## Options — UI layout preset

- [ ] Open **Options** from main menu
- [ ] **UI Layout** row shows active preset in brackets, e.g. `[Standard] ► Wide` or `Standard ► [Wide]`
- [ ] Highlight **UI Layout** row (Down from vore toggles)
- [ ] **Right** cycles to Wide; **Left** cycles back to Standard
- [ ] **Enter** on UI Layout row advances preset (same as Right)
- [ ] Escape back to menu; reopen Options — preset choice remembered

## Apply on new run

- [ ] Set preset to **Wide**, back to menu, start **New Game**
- [ ] Sidebar is visibly wider; map viewport narrower (40 vs 48 tiles)
- [ ] Message log, status corner, and sidebar still tile correctly

## Mid-run / menu console note

- [ ] Changing preset in Options does **not** resize the menu window until full relaunch (expected)
- [ ] In-game layout updates only after starting a **new** game (quit to menu → New Game)

## Regression

- [ ] Vore content toggles still work (Left/Right/Enter on vore rows)
- [ ] At least one vore type must stay enabled
- [ ] Main menu options visible; gameplay UI from PR5–PR8 intact