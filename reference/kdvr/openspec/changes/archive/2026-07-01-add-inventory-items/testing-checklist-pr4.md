# PR 4 — Quaff potions from data

Run `python -m src.main` from the project root.

Automated: `python -m pytest tests/test_inventory_items_pr4.py -v`

## Quaff (`q`)

- [ ] No potions → `You have no potions.`
- [ ] `q` opens potion-only modal; letter quaffs item
- [ ] Heal amount comes from JSON (`health_potion` → 10 HP)
- [ ] Log: `You drink {name} and recover {N} HP.`
- [ ] At full HP: `You drink {name} but are already at full health.` (still consumes item and turn)
- [ ] Stacked potion quaff removes one from stack
- [ ] Turn consumed on successful quaff

## Stunned

- [ ] Stunned player can still `q` quaff (movement still blocked)

## Drop render fix

- [ ] Drop item under player: `@` remains visible (item glyph does not cover player)

## Engulfed

- [ ] `q` logs pack blocked while engulfed

## Regression

- [ ] `w`, Shift+w, `i`, `d`, pickup still work from PR 3