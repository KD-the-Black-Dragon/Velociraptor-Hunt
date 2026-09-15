# PR 3 — Wand catalog

Run `python -m src.main` from the project root.

Automated: `python -m pytest tests/test_equipment_catalog_pr3.py tests/test_inventory_items_pr5.py -v`

## Wand variety

- [ ] Descend — `/` wands appear in different purple shades on sparse floors
- [ ] Depth ~3+: wand of double missile possible
- [ ] Depth ~21+: wand of extermination possible on deep floors
- [ ] Shallow floors stop rolling basic magic missile after ~depth 14

## Evoke (regression)

- [ ] `v` still works: pick wand → cursor target → evil-only hits
- [ ] Higher-tier wands hit harder when they land
- [ ] Charges decrement; red break at 0

## Rarity

- [ ] Wands remain rare (weight 1, placement cap 5)

## Regression

- [ ] Starter dagger/robes unchanged
- [ ] Weapons and armor from PR 1–2 still spawn by depth