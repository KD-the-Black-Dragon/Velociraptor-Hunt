# Manual testing checklist — PR3 (Alternate CV rules)

**How to run:** `python -m src.main`  
**Automated:** `python -m pytest tests/test_alternate_cv_pr3.py tests/test_vore_struggle.py tests/test_dazed_pr1.py -v -n 4`

## Automated (agent)

- [x] PR3 + struggle regression — run by agent

## Happy path

- [ ] Options → **Alternate CV Mechanics** → **Yes** → New Game (snapshot)
- [ ] Get **CV**-engulfed (enable only Cock Vore in prefs if needed to force CV)
- [ ] Struggle: log appears, predator HP does **not** drop from struggle
- [ ] Escape eventually → predator blue BG + “appears dazed.”; predator skips turns then “is no longer dazed.”
- [ ] Options → **No** → New Game → CV struggle **does** damage as before; escape does **not** daze
- [ ] Alternate CV **Yes** → **OV** engulf → struggle damages; escape does **not** daze
- [ ] Alternate CV **Yes** → watch evil **CV**-digest an NPC (rabbit/knight) → predator dazes after finish; **OV** digest does not

## Regression

- [ ] Holding predator dark-red BG still works while engulfed
- [ ] Save/load a run with Alternate CV Yes still uses Yes after load (Options may differ)
- [ ] Digestion / mercy / rescue still work

## Out of scope this PR

- Live OpenSpec/README polish (PR4)
