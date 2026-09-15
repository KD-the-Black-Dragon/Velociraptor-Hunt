# PR 1 — Registries, spawn, pickup

Run `python -m src.main` from the project root.

Automated: `python -m pytest tests/test_inventory_items_pr1.py -v`

## Data load

- [ ] Game starts without crash (items load from JSON)
- [ ] `data/armor.json` leather armor has `digestion_ac: 1`

## Floor spawn

- [ ] New game floor has items beyond potions (weapons/armor possible from weights)
- [ ] At least one health potion on floor 1
- [ ] Wand of magic missile appears on deeper floors (depth 3+), not floor 1

## Auto-pickup (walkover)

- [ ] Walking onto one item picks it up; log names item and slot letter
- [ ] Walking onto multiple items picks up all (until full)
- [ ] Full inventory: one `Your inventory is full.` per tile entry, not per item

## Potion stacking

- [ ] Picking up two health potions stacks in one slot (HUD shows count)

## Manual pickup (`,`)

- [ ] `,` on empty tile: `There is nothing here to pick up.`
- [ ] `,` on one item: immediate pickup, no modal
- [ ] `,` on multiple items: modal lists choices; letter picks one
- [ ] Full inventory: `Your inventory is full.`

## Regression

- [ ] Movement, combat, examine still work
- [ ] Letter keys `a`–`z` still use potions (removed in PR 2)