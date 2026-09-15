# Manual checklist — PR10 Fast

Run: `python -m src.main`

## Fast wolf (stock `entities.json`)

- [ ] **At range:** wolf moves toward you **twice** in one world phase (two separate steps)
- [ ] **Adjacent full-HP you:** wolf bumps/attacks **twice** if both steps reach you
- [ ] **Adjacent stunned 0 HP you:** vore modal on first step; **no second action** after modal opens

## Regression

- [ ] Slow wolves still skip on odd player turns (if you spawn one with `Slow` in data)
- [ ] Erratic wolves still move-attack-move when given `Erratic` only
- [ ] Vore miss still wastes opener's turn; no second Fast step replays in same phase
- [ ] After vore miss, next player turn Fast wolf runs both steps from the start