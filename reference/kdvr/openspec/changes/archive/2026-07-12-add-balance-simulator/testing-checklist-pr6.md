# PR6 manual testing checklist — isolation pass, loadout injection, iso CSV

**Change:** `add-balance-simulator`  
**PR:** isolation floor bootstrap, loadout injection, `iso_*` aggregation

## Automated (agent)

- [x] `python -m pytest tests/test_sim_isolation.py -v` — 6 passed
- [x] Full sim suite: 56 passed (`test_sim_*`, `-n 4`)
- [x] CLI smoke: `python tools/sim_balance.py --difficulty normal --seconds 10 --label pr6_smoke --floors-max 3` — `iso.f01.runs = 1`, `meta.isolation_runs_total = 3`

## Designer playtest

- [ ] `python tools/sim_balance.py --difficulty normal --seconds 60 --label pr6_check --output balance_pr6_check.csv`
- [ ] Open CSV in Calc/Excel — `iso.f01.runs` and other `iso.f01.*` rows have values (not all zero)
- [ ] `meta.isolation_runs_total` is greater than zero
- [ ] `meta.isolation_seconds` is roughly 30% of `meta.seconds_budget` (default split)
- [ ] `traj.f01.*` rows still populate as in PR5 (hybrid pass unchanged for trajectory)
- [ ] `python tools/sim_balance.py --difficulty normal --seconds 10 --trajectory-only --label pr6_traj_only` — all `iso.f*.*` rows are zero

## Regression risks

- [ ] `python -m src.main` — gameplay unchanged (isolation hooks are sim-only)
- [ ] PR5 trajectory scoring/aggregation still matches prior CSV shape
- [ ] PR3/PR4 survival and loot behavior still visible in both `traj_*` and `iso_*` columns

## Notes

- Isolation loadout comes from trajectory median `LoadoutBank`; short trajectory budgets may leave floors on starter medians.
- Isolation runs one floor at a time — `iso_descend_rate` measures whether the bot left that floor alive via stairs, not full-run depth.
- `--trajectory-only` skips isolation entirely (PR6 flag).