# PR 2 — Inventory modals, drop, inspect

Run `python -m src.main` from the project root.

Automated: `python -m pytest tests/test_inventory_items_pr2.py -v`

## Inspect (`i`)

- [ ] Empty pack → `Your inventory is empty.`
- [ ] `i` opens list of occupied slots with letters
- [ ] Letter selects detail view (damage, AC, durability, charges, heal amount)
- [ ] Esc on detail → back to list; Esc on list → close
- [ ] No turn consumed

## Drop (`d`)

- [ ] Empty pack → `You have nothing to drop.`
- [ ] `d` opens drop modal; letter drops item under player
- [ ] Log: `You drop {name}.`
- [ ] Dropped weapon keeps durability on floor
- [ ] Dropping stacked potion removes one from stack
- [ ] No turn consumed

## Floor examine (`x`)

- [ ] Examine potion/weapon on floor shows full stats (not description only)

## Retired behavior

- [ ] Pressing `a`–`z` outside a modal does **not** quaff/use items

## Engulfed

- [ ] `i` and `d` log pack blocked while engulfed

## Regression (PR 1)

- [ ] `,` pickup still works
- [ ] Walkover auto-pickup still works