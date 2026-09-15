# add-inventory-items — Combined manual testing

Run `python -m src.main` from the project root.

## Automated gate (acceptance)

```bash
python -m pytest tests/ -v
```

All tests should pass (inventory PR tests + full regression).

---

## PR 1 — Registries, spawn, pickup

- [ ] Game starts; items load from JSON (`digestion_ac` on leather armor)
- [ ] Floor has health potion minimum + weighted weapons/armor/wands
- [ ] Walkover picks all items on tile; full inventory logs once
- [ ] Potion stacking in one slot
- [ ] `,` manual pickup (empty / one / multi modal)

## PR 2 — Modals, drop, inspect

- [ ] `i` list → detail; Esc back/close; no turn
- [ ] `d` drop; wielded durability preserved on floor
- [ ] `x` floor examine shows full stats
- [ ] `a`–`z` outside modals do nothing
- [ ] Engulfed: pack blocked message

## PR 3 — Wield, wear, durability

- [ ] `w` / Shift+w modals; turn on success
- [ ] Wielded damage / worn AC in combat
- [ ] Weapon −1 durability per hit; red destroy at 0
- [ ] Worn armor mitigates digestion; armor degrades per mitigated point
- [ ] HUD has no `Items:` line
- [ ] Descent preserves inventory + equip

## PR 4 — Quaff

- [ ] `q` heals from JSON amount; turn consumed
- [ ] Stunned quaff works
- [ ] `@` renders over dropped item on same tile

## PR 5 — Wand evoke

- [ ] `v` wand pick → cursor targeting (no modal on map step)
- [ ] Evil-only valid targets; `Not the best target.` / `No valid targets in range.`
- [ ] Charges decrement; red `breaks!` at 0; turn on success

## Full regression

- [ ] Main menu, name entry, options, Ctrl+Q quit confirm
- [ ] Examine, descent, depth HUD, faction combat
- [ ] Player vore modal, struggle, digestion, game over → menu
- [ ] NPC swap, stunned allies, rescue, log visibility gating
- [ ] Sharks on water floors; knight followers on descent

**Pass criteria:** Behavior matches `openspec/specs/inventory-items/spec.md`; pytest green.