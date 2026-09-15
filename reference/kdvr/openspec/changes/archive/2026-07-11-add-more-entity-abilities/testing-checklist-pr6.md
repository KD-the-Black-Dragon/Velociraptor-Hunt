# PR6 — Species content assignments manual checklist

Run: `python -m src.main`

## Hands (kobold, gnoll mercenary, owl mage)

- [ ] Kobold on a floor with closed doors opens or breaks doors while exploring
- [ ] Gnoll mercenary with Hands behaves the same near doors
- [ ] Owl mage opens doors without losing ranged combat

## Wander (slime)

- [ ] Slime drifts via explore goals — does not chase player after contact
- [ ] Slime still smites at range 3 when player is weakened in LOS
- [ ] Rabbit still flees/explores normally — **no** `Wander`

## NoChase (tunnel slug, tarantula)

- [ ] Tarantula fights while player is visible; stops pursuing when player breaks LOS
- [ ] Tunnel slug same pattern (stationary — no movement between shots/bumps)

## Stationary (tunnel slug)

- [ ] Tunnel slug does not voluntarily move from spawn tile
- [ ] Adjacent bump attack still works
- [ ] Knockback can still push it (edge case)

## RangedVore + dual tongue (owl mage)

- [ ] Owl mage at depth 12+: weakened player at range 2–5 may get vore modal
- [ ] Player >50% HP at range: damage `Range5` shot, not vore
- [ ] Player ≤50% HP: ranged vore considered before/at alongside damage ranged

## Wolf reverted

- [ ] Stock wolf is **ground** mobility with `Range6` only (playtest stationary/RangedVore removed)
- [ ] Normal spawn weight — not over-saturated on floor 1

## Automated

- [ ] `python -m pytest tests/test_entity_abilities_content_pr6.py tests/test_entity_validation.py tests/test_expand_entity_roster_pr1.py -v -n 4`