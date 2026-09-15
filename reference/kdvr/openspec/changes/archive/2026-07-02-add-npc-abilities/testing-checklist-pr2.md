# Manual checklist — PR2 Range3

Run: `python -m src.main`

## Range3 wolf (stock `entities.json`)

- [ ] Wolf shoots at **3 tiles** away in LOS
- [ ] Wolf does **not** shoot at **4 tiles** — closes instead
- [ ] Adjacent still melee only (no shoot)
- [ ] Stunned 0 HP prey at range 2–3 — wolf moves in, does not shoot

## Regression (PR1)

- [ ] Shoot at 2 tiles still works
- [ ] Vore/melee unchanged