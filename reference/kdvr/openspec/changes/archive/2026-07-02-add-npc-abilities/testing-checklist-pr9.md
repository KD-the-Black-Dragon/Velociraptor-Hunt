# Manual checklist — PR9 Slow

Run: `python -m src.main`

## Slow wolf (stock `entities.json`)

- [ ] **First player move:** wolf does **not** act (odd `player_turn_count` after your action)
- [ ] **Second player move:** wolf chases or wanders normally
- [ ] **Third player move:** wolf idle again
- [ ] Pattern repeats: acts every **other** player turn

## Regression

- [ ] Non-Slow NPCs still act every world phase
- [ ] Stunned monsters still skip entirely (no Slow parity message)
- [ ] Vore modal interrupt still works for wolves that do act
- [ ] Erratic behavior unchanged when testing a wolf with `Erratic` in data (not stock)