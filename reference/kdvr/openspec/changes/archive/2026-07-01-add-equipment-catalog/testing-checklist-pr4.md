# PR 4 — Potion catalog

Run `python -m src.main` from the project root.

Automated: `python -m pytest tests/test_equipment_catalog_pr4.py tests/test_inventory_items_pr4.py -v`

## Potion variety

- [ ] Depth 1: magenta `!` health potions still guaranteed at least once
- [ ] Depth 3+: red `!` greater healing can appear
- [ ] Depth 8+: gold `!` power healing can appear
- [ ] `q` quaff heals correct amounts (10 / 25 / 50)

## Rarity

- [ ] Potions more common than weapons/armor/wands but not spammed
- [ ] Floors still respect placement cap (5 weighted + spawn_min health)

## Regression

- [ ] Potion stacking still works for duplicate health potions
- [ ] Stunned quaff still works
- [ ] Starter dagger/robes unchanged