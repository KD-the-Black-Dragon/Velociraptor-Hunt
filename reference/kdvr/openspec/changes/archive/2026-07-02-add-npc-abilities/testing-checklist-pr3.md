# Manual checklist — PR3 RangeN generalization

Run: `python -m src.main`

## Range5 wolf (stock `entities.json`)

- [ ] Wolf shoots at **5 tiles** away in LOS
- [ ] Wolf does **not** shoot at **6 tiles** — closes instead
- [ ] Adjacent still melee only (no shoot)
- [ ] Stunned 0 HP prey at range 2–5 — wolf moves in, does not shoot

## Regression (PR1–PR2)

- [ ] Shoot at 2–3 tiles still works on other NPCs with those tokens (if any in dungeon)
- [ ] Vore/melee unchanged