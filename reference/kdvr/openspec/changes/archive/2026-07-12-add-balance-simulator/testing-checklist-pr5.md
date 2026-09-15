# PR5 manual testing checklist — scoring, aggregation, traj CSV

**Change:** `add-balance-simulator`  
**PR:** event scoring, trajectory aggregation, loadout bank

## Automated (agent)

- [x] `python -m pytest tests/test_sim_scoring.py tests/test_sim_aggregator.py -v`
- [x] Full sim suite: 50 passed (`test_sim_*`, `-n 4`)
- [x] CLI smoke: `python tools/sim_balance.py --difficulty normal --seconds 5 --trajectory-only --floors-max 3`

## Designer playtest

- [ ] `python tools/sim_balance.py --difficulty normal --seconds 60 --trajectory-only --label pr5_check --output balance_pr5_check.csv`
- [ ] Open CSV in Calc/Excel — `traj.f01.difficulty_mean` and other `traj.f01.*` rows have values (not all zero when bot played floor 1)
- [ ] `traj.f01.digest_when_weapon_spawned` / `not_spawned` rows exist (may be 0 if no weapon upgrades that run)
- [ ] `iso.f01.*` rows are still zero (isolation is PR6)

## Regression risks

- [ ] `python -m src.main` — gameplay unchanged (scoring is sim-only)
- [ ] PR4 loot/equip and PR3 survival tests still pass

## Notes

- Composite weights are v1 placeholders in `src/sim/scoring.py` — tune after CSV review.
- Loadout bank is built but not consumed until PR6 isolation.