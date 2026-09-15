# PR2b — NoChase + Wander clarification manual checklist

Run: `python -m src.main`

## NoChase (evil)

- [ ] Wolf with `NoChase` (mod) **chases** while player is visible
- [ ] Duck behind wall / break LOS — wolf **does not** path to last seen tile
- [ ] Wolf resumes explore / idle drift after LOS break (no momentum steps toward old position)
- [ ] Stock wolf **without** `NoChase` still memory-pursues (regression)

## Wander (clarified intent)

- [ ] `Wander` evil (mod) drifts randomly — does not pursue player even when visible
- [ ] Still deals bump damage if it walks into something
- [ ] **Not** assigned to rabbit in stock data

## Automated

- [ ] `python -m pytest tests/test_npc_abilities_no_chase.py tests/test_npc_abilities_wander.py -v`