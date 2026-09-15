# PR5 — RangedVoreN manual checklist

Run: `python -m src.main`

Wolf in `entities.json` already has `Range3` + `RangedVore3` for playtest (stationary + dual tongue).

## Ranged vore

- [ ] Weakened player at distance 2–3 with LOS: wolf opens vore modal (not adjacent bump)
- [ ] Ranged vore **hit**: player co-located on wolf tile, engulf flow continues
- [ ] Ranged vore **miss**: player stays at original tile; wolf turn consumed
- [ ] Adjacent weakened player still uses **adjacent** vore path (not ranged shot)

## Dual tongue (RangeN + RangedVoreN)

- [ ] Player **>50% HP** at range: wolf uses damage ranged (`shoots you`), no vore modal
- [ ] Player **≤50% HP** at range: wolf may attempt ranged vore (decision roll) before/at instead of only plinking

## NPC vore

- [ ] Weakened good/neutral NPC at range 2–N: wolf attempts NPC vore log (FOV-gated)
- [ ] Hit pulls prey onto wolf tile and engulf state applies
- [ ] Stunned 0 HP prey at range **can** be ranged-vore targeted (unlike Path plink skip)

## Regression

- [ ] `PreferVore` still forces adjacent/ranged attempts when legal
- [ ] Stationary wolf does not move but can ranged-vore and `Range3` shoot
- [ ] Hands / Wander / NoChase unchanged

## Automated

- [ ] `python -m pytest tests/test_npc_abilities_ranged_vore.py tests/test_ability_parser.py tests/test_npc_abilities_prefer_vore.py tests/test_entity_validation.py -v -n 4`