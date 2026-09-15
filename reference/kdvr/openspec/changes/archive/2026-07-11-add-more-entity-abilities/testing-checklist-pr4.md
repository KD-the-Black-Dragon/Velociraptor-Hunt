# PR4 — Stationary mobility manual checklist

Run: `python -m src.main`

Requires a species with `"mobility": "stationary"` in `entities.json` or a mod (PR6 may assign content later).

## Movement

- [ ] Stationary evil does **not** walk toward distant player
- [ ] Stationary evil **does** bump-attack when player is adjacent
- [ ] Stationary with `RangeN` still shoots when in range and LOS (no repositioning kite steps)
- [ ] Stationary with `Coward` does **not** flee; attacks adjacent threats when cornered

## Regression

- [ ] Ground / fly / aquatic movement unchanged
- [ ] Knockback can still push a stationary NPC (edge case accepted for v1)

## Automated

- [ ] `python -m pytest tests/test_npc_mobility_stationary.py tests/test_entity_validation.py tests/test_dungeon_pr1.py -v`