# Manual checklist — PR7 Supercoward

Run: `python -m src.main`

## Supercoward wolf (stock `entities.json`)

- [ ] **Full-HP** wolf flees you on sight when a retreat step exists
- [ ] Wolf does **not** close to melee/vore while flee path is open
- [ ] Cornered with no legal flee step: wolf **fights** normally

## Regression (PR6 Coward)

- [ ] Coward-only behavior still at half-HP threshold when tested on other entities (if any in dungeon)
- [ ] Neutral rabbit with only Coward (not Supercoward) still ignores flee above 50% HP