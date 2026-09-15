# Manual checklist — PR8 Erratic

Run: `python -m src.main`

## Erratic wolf (stock `entities.json`)

- [ ] **At range:** one pursuit move toward you, no attack (not adjacent), then one **random** shuffle (not a second chase toward you)
- [ ] **Adjacent stunned 0 HP you:** skips pursuit move; vore modal opens on attack sub-step; no third shuffle after modal
- [ ] **Adjacent full-HP you:** skips pursuit; melee bump on attack sub-step; random shuffle after

## Not allowed (verify absence)

- [ ] No second attack in the same turn
- [ ] No second intentional chase toward you in the same turn
- [ ] No ranged shot from Erratic wolf without RangeN

## Regression

- [ ] Non-Erratic NPCs still act once per turn
- [ ] Vore modal interrupt still works; no extra sub-steps after modal opens