# PR 1 — Weapons catalog + unarmed + spawn cap

Run `python -m src.main` from the project root.

Automated: `python -m pytest tests/test_equipment_catalog_pr1.py tests/test_inventory_items_pr1.py -v`

## Unarmed baseline

- [ ] New game, no weapon wielded — bump combat feels weak (1–2 damage)
- [ ] Pick up and wield dagger — clear upgrade over bare hands

## Weapon variety

- [ ] Descend several floors — see different weapon glyphs on the ground (not only `)`)
- [ ] Depth ~2+: short sword (`/`) can appear
- [ ] Depth ~11+: royal rapier (`'`) can appear on deep floors
- [ ] Shallow floors no longer dominated by one weapon type only

## Rarity

- [ ] Most floors have **few** floor items (not littered everywhere)
- [ ] Finding any weapon feels noteworthy

## Regression

- [ ] `w` wield still works; damage changes with weapon
- [ ] Pickup, `i` inspect shows weapon stats and durability
- [ ] Health potion still appears on depth 1 (spawn_min)