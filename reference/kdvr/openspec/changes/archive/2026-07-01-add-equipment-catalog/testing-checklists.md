# add-equipment-catalog — Combined manual testing

Run `python -m src.main` from the project root.

## Automated gate (acceptance)

```bash
python -m pytest tests/ -v
```

All tests should pass.

---

## PR 1 — Weapons + unarmed + spawn cap

- [ ] Unarmed bump weak (1–2); wielded dagger clearly stronger
- [ ] Multiple weapon glyphs by depth; floors sparse (not littered)
- [ ] `w` wield still works

## PR 2 — Armor + starter loadout

- [ ] New game: `a` dagger wielded, `b` robes worn; pickup to `c`
- [ ] Armor on floor is `[` with varied colors
- [ ] Shift+w wear upgrades AC; waxed/oiled show digestion tradeoff in `i`

## PR 3 — Wands

- [ ] `/` wands rare; purple tiers by depth
- [ ] `v` evoke still works; stronger wands hurt more

## PR 4 — Potions

- [ ] Health `!` guaranteed shallow; greater (red) depth 3+; power (gold) depth 8+
- [ ] `q` quaff heals 10 / 25 / 50
- [ ] Stacking and stunned quaff still work

## Full regression

- [ ] Main menu, descent, faction combat, vore/digestion
- [ ] Inventory category commands (`,`, `i`, `d`, `w`, `W`, `q`, `v`)
- [ ] Engulfed pack block; worn armor digestion mitigation
- [ ] NPC population unchanged

**Pass criteria:** Behavior matches `openspec/specs/equipment-catalog/spec.md`; pytest green.