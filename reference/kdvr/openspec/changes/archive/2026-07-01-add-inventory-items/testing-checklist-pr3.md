# PR 3 — Wield, wear, combat stats, durability

Run `python -m src.main` from the project root.

Automated: `python -m pytest tests/test_inventory_items_pr3.py -v`

## Wield (`w`)

- [ ] No weapons → `You have no weapons.`
- [ ] `w` opens weapon-only modal; letter wields item
- [ ] Log: `You wield {name}.`
- [ ] Already wielded → `You're already wielding that.` (no turn)
- [ ] Turn consumed on successful wield
- [ ] Wielded weapon changes bump damage (try dagger vs unarmed)

## Wear (`W` / Shift+w)

- [ ] No armor → `You have no armor.`
- [ ] Shift+w opens armor-only modal; letter wears item
- [ ] Log: `You wear {name}.`
- [ ] Already worn → `You're already wearing that.` (no turn)
- [ ] Turn consumed on successful wear
- [ ] Worn armor increases effective AC in combat

## Durability

- [ ] Weapon loses 1 durability per successful player hit (even 0 damage hits)
- [ ] At 0 durability weapon removed; **red** log: `Your {name} falls apart.`
- [ ] While engulfed, worn armor still mitigates digestion (`digestion_ac`)
- [ ] Armor durability −= mitigated digestion per tick; destroys at 0 (red log)

## Inspect / drop

- [ ] `i` list shows `(wielded)` / `(worn)` markers
- [ ] `i` detail shows wielded/worn in title when applicable
- [ ] Dropping wielded/worn item clears equip pointer

## HUD

- [ ] Main HUD no longer shows `Items:` summary (use `i` for inventory)

## Engulfed

- [ ] `w` and Shift+w log pack blocked while engulfed

## Regression

- [ ] `i`, `d`, `,` pickup still work from PR 2
- [ ] Descent preserves inventory, durability, wielded/worn slots