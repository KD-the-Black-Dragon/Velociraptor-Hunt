# add-npc-abilities — Combined manual testing

Run `python -m src.main` from the project root.

## Automated gate (acceptance)

```bash
python -m pytest tests/ -v
```

All tests should pass.

---

## PR0 — Framework

- [ ] Game boots; unknown ability warns, does not crash
- [ ] `AbilityState` on spawned NPCs

## PR1–PR3 — RangeN

- [ ] Wolf with `Range2` shoots at distance 2, melees adjacent
- [ ] `Range5` generalizes max distance

## PR4–PR5 — Summon

- [ ] `Summon1 rabbit` on first LOS
- [ ] `Summon3 rabbit` spawns up to three

## PR6–PR7 — Coward / Supercoward

- [ ] Coward knight below half flees
- [ ] Supercoward wolf flees at full HP

## PR8 — Erratic

- [ ] Pursuit + attack + random shuffle (not triple chase)

## PR9 — Slow

- [ ] Acts every other player turn

## PR10 — Fast

- [ ] Two moves or attacks per world phase
- [ ] Vore modal aborts second step

## PR11 — Knockback

- [ ] Damage then knockback line; push one tile

## PR12 — Lifedrain

- [ ] Damage then healthier line; HP restores

## PR13 — Acceptance

- [ ] Stock wolf has **no** abilities — baseline evil chase/vore
- [ ] Spot-check one ability via test spawn or JSON edit if desired

## Full regression

- [ ] Main menu, descent, combat, player vore modal
- [ ] `test_vore_turn_order.py` semantics unchanged
- [ ] NPC swap, stunned allies, FOV log gating

**Pass criteria:** `openspec/specs/npc-abilities/spec.md`; pytest green; wolf `abilities: []`.