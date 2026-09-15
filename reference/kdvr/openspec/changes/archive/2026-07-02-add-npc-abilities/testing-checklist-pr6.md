# Manual checklist — PR6 Coward

Run: `python -m src.main`

## Coward wolf (stock `entities.json`)

- [ ] Weaken wolf below half HP (F2 debug damage)
- [ ] With retreat path open, wolf **moves away** from you instead of closing to melee/vore
- [ ] At **exactly 50% HP** (e.g. 12/24), wolf does **not** coward-flee — still aggressive
- [ ] Cornered with no legal flee step: wolf **fights** (melee/vore as usual)

## Regression

- [ ] Full-HP wolf still chases and vores normally
- [ ] Good knight without Coward unchanged