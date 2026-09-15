# Manual checklist — PR1 (macguffin data catalog)

PR1 is data-only — **no in-game macguffins yet**.

Automated: `pytest tests/test_macguffins_pr1.py -q`

## Data file

- [x] `data/macguffins.json` exists with Sword, Shield, Cup
- [x] Depth bands: Sword 1–8, Shield 4–12, Cup 6–16
- [x] `data/SCHEMA.md` documents fields

## In-game (not applicable this PR)

- [ ] Macguffins visible on floors — deferred to PR2
- [ ] Step-on victory prompt — deferred to PR3
- [ ] Victory game over — deferred to PR4

## Regression

- [ ] Game launches and plays normally (no loader wired at startup yet)