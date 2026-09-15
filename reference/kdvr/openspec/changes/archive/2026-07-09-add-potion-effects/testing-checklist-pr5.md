# Manual testing checklist — PR5 (summon ally)

Run: `python -m src.main`

**TEMP starter:** **potion of alliance** is in inventory with other test potions.

## Alliance

- [ ] Quaff **potion of alliance** — dog knight (or other good at depth) appears nearby
- [ ] Ally fights evil / follows as normal good AI
- [ ] Multiple quaffs can stack allies (no cap)
- [ ] Potion is consumed even if something went wrong (rare fail message)

## Regression

- [ ] Blink / teleport / buffs still work
- [ ] Floor not broken by extra NPCs

## Automated

- [x] `tests/test_potion_summon_pr5.py`
