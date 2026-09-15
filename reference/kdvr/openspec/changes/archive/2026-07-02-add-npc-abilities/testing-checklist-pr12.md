# Manual checklist — PR12 Lifedrain

Run: `python -m src.main`

## Lifedrain wolf (stock `entities.json`)

- [ ] Damage the wolf (melee or wand), then let it hit you on open floor
- [ ] **Damage line first**, then **"The wolf appears healthier."** (or species-appropriate name)
- [ ] Wolf HP increases by damage dealt (capped at max HP)
- [ ] At full HP wolf still damages you but **no** healthier line

## Regression

- [ ] Knockback wolves (if tested separately) still push without healing unless they also have Lifedrain
- [ ] Misses do not heal or log healthier
- [ ] Off-screen lifedrain: no log when combat not visible (optional spot-check)