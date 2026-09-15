# Manual checklist — PR4 Summon1

Run: `python -m src.main`

## Summon1 wolf (stock `entities.json`)

- [ ] First time wolf sees you in LOS: message log shows **"The wolf summons aid!"** (when wolf in your FOV)
- [ ] One **rabbit** appears on a tile adjacent to the wolf
- [ ] Leaving and re-approaching later: **no second summon**, no duplicate log line

## Regression

- [ ] Wolf still chases / melees / vores normally after summoning
- [ ] Rabbits from summon behave as neutral NPCs (not vore-capable)