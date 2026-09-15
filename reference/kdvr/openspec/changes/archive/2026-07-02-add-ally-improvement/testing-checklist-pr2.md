# Manual checklist — PR2 (player-engulfed rescue priority)

Run: `python -m src.main`

## Rescue priority

- [ ] Get engulfed by a wolf while a knight and another wolf are visible → knight paths toward the **holding** predator (not the other wolf)
- [ ] Knight bump-attacks holding predator when adjacent (existing rescue behavior)
- [ ] When player escapes engulf, knight reverts to normal chase/follow priority

## Edge cases

- [ ] Holding predator not in knight LOS → knight does not chase predator (falls through to normal AI)
- [ ] Player not engulfed → knight chases nearest visible evil as before

## Regression

- [ ] PR1 introductions still work when eligible
- [ ] Knight freeing engulfed rabbit (`test_knight_rescues_engulfed_rabbit` behavior) unchanged

## Automated

- [ ] `pytest tests/test_ally_rescue_priority.py` green