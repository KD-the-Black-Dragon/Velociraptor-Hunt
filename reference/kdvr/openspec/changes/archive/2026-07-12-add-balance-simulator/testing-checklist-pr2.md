# PR2 manual testing checklist — navigation, runes, descend, shark flee

**Change:** `add-balance-simulator`  
**Signed off:** 2026-07-12 (designer)

## Automated (agent)

- [x] `python -m pytest tests/test_sim_navigation.py -v -n 4`
- [x] `python -m pytest tests/test_sim_runner.py -v -n 4`

## Designer playtest

- [x] `python -m src.main` — new game on current stock data feels playable (balance still in flux; not blocking PR2)
- [x] Smoke: normal seed 23 trajectory reaches depth ≥2 (`tools/_sim_smoke_one.py` or integration test)
- [x] Smoke: easy seed 4242 collects ≥1 rune

## Regression risks

- [ ] Player movement / door open unchanged in live game (sim uses same `try_action` path)
- [ ] Floor rune step-on activation still works for human player
- [ ] Shark flee policy does not affect live game (sim-only policy)

## Notes

- Stock “normal” is not a calibrated baseline yet; sim measures current `data/` only.
- Pinned seeds: `openspec/specs/balance-simulator/spec.md`