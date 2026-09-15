# PR 2 — Armor catalog + starter loadout

Run `python -m src.main` from the project root.

Automated: `python -m pytest tests/test_equipment_catalog_pr2.py tests/test_inventory_items_pr3.py -v`

## Starter loadout

- [ ] New game: `i` shows `a) dagger (wielded)` and `b) robes (worn)`
- [ ] Bump combat uses dagger damage (not bare 1–2)
- [ ] First empty pickup slot is `c`

## Armor variety

- [ ] Descend — floor armor appears as `[` with **different colors** (brown leather, grey chain, pink indigestion suit on deep floors)
- [ ] `Shift+w` wear upgrades AC; oiled/waxed variants show lower AC, higher digestion in `i` detail

## Rarity (carry-over from PR 1)

- [ ] Floors still sparse — not littered with `[` everywhere

## Regression

- [ ] `w` / Shift+w still work; descent preserves worn armor
- [ ] Worn armor still mitigates digestion while engulfed (passive)
- [ ] Weapons from PR 1 still spawn and escalate by depth