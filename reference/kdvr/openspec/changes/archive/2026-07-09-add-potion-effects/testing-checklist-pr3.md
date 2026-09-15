# Manual testing checklist — PR3 (delayed teleport)

Run: `python -m src.main`

**TEMP starter:** teleportation is in inventory (slot **g** with other test potions).

## Teleportation

- [ ] Quaff **potion of teleportation** — log “You feel unstable.”; status `Tele? N` (3–5)
- [ ] After N turns, teleport fires — reappear elsewhere on land; magical log line
- [ ] Re-quaff while pending **refreshes** countdown
- [ ] Does **not** land on NPCs / walls / deep water (ground player)
- [ ] Can land on runes/items (normal step-on after)

## Escape

- [ ] Drink teleport, get engulfed before it fires (or force countdown) — when it fires, **escape** gut and reappear elsewhere
- [ ] Predator no longer holds you

## Regression

- [ ] Haste 2:1 still works
- [ ] Antacid / might / discovery unchanged
- [ ] Save/load with `Tele?` pending restores countdown

## Automated

- [x] `tests/test_potion_teleport_pr3.py`
