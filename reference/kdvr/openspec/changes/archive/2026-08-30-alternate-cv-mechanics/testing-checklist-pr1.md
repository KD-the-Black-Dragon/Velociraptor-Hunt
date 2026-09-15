# Manual testing checklist — PR1 (Dazed foundation)

**How to run:** `python -m src.main`  
**Automated:** `python -m pytest tests/test_dazed_pr1.py tests/test_save_snapshot.py::test_round_trip_dazed_remaining -v -n 4`

## Automated (agent)

- [x] Dazed unit tests + save round-trip — run by agent

## Happy path (debug / temporary)

PR1 has **no Options wiring** yet — daze is not applied by CV. To smoke visually you can temporarily use a debugger, or wait for PR3. Optional:

- [ ] (Optional) From a debug console / temporary test hook: `apply_daze` on a visible wolf → blue tile BG + “appears dazed.”
- [ ] Wait turns → wolf does not act while dazed; on expire “is no longer dazed.”

## Regression

- [ ] New Game / combat / vore without daze still works as before
- [ ] Engulfed predator still shows dark-red holding BG (unchanged)
- [ ] Save/load an ordinary run (no daze) still works

## Out of scope this PR

- Alternate CV Options, struggle 0 damage, auto-daze on escape/digest (PR2–PR3)
