# PR1 — PreferVore manual checklist

Run: `python -m src.main`

## Parser / load (optional dev)

- [ ] Temporarily add `"PreferVore"` to a wolf in a test mod — no load warning; token retained

## Vore behavior

- [ ] Spawn or encounter a predator with `PreferVore` adjacent to player at **≤50% HP** (debug weaken if needed)
- [ ] Predator **always** opens vore attempt / modal when legal — not skipped by fuzzy decision
- [ ] At **>50% HP**, predator does **not** vore (unchanged eligibility)
- [ ] Without `PreferVore`, same predator at partial HP may **sometimes** melee instead (fuzzy roll)

## Regression

- [ ] Stock wolf (no `PreferVore`) vore behavior unchanged at 0 HP stunned
- [ ] NPC vore on stunned knight still works for normal wolves

## Automated

- [ ] `python -m pytest tests/test_npc_abilities_prefer_vore.py tests/test_ability_parser.py tests/test_vore_ai.py -v`