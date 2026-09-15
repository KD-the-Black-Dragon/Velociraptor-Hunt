# Manual checklist — PR11 Knockback

Run: `python -m src.main`

## Knockback wolf (stock `entities.json`)

- [ ] Let wolf bump you on an open floor line: **damage line first**, then **"You are knocked back!"**
- [ ] You land one tile **away from the wolf** along the bump direction
- [ ] With a wall/water directly behind you: damage still applies, **no** knockback line

## Optional (if you add `Range2` + `Knockback` in data)

- [ ] Ranged hit at distance 2 pushes you one tile along the shot axis

## Regression

- [ ] Wolves without Knockback do not push on hit
- [ ] Misses do not push or log knockback
- [ ] Fast / Slow / Erratic cadence unchanged on non-Knockback wolves