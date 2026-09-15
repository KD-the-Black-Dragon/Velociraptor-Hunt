# PR7 manual testing checklist — final acceptance

**Change:** `add-balance-simulator`  
**PR:** spec finalization, combined checklists, acceptance

## Automated (agent)

- [ ] `python -m pytest tests/test_sim_*.py -v -n 4` — all sim tests pass
- [ ] Full suite `python -m pytest tests/ -v -n 4` per `AGENTS.md` acceptance workflow

## Designer — hybrid analyzer smoke

- [ ] `python tools/sim_balance.py --difficulty normal --seconds 60 --label acceptance --output balance_acceptance.csv` completes without hang
- [ ] Open CSV in Calc/Excel — rows exist for floors 1–20 under both `traj.f*.*` and `iso.f*.*` sections
- [ ] `meta.trajectory_runs` and `meta.isolation_runs_total` are both greater than zero
- [ ] `meta.data_fingerprint` is present (compare validity across runs)

## Designer — time budget and samples

- [ ] Run `--seconds 30` then `--seconds 120` (same `--seed` if desired) — `traj.f01.runs_reached` increases with longer budget

## Designer — policy sanity (trajectory)

- [ ] Bot collects runes and descends on early floors on a viable seed (e.g. `--seed 23`) — not stuck on floor 1
- [ ] `traj.f01.digest_when_weapon_spawned` and `traj.f01.digest_when_weapon_not_spawned` rows exist (values may be 0 if no weapon upgrades that run)
- [ ] Survival behavior visible in metrics: `traj_early_bail_rate`, consumable means, `traj_stunned_events_mean` (not all permanently zero across floors)

## Designer — isolation

- [ ] `iso.f01.runs` greater than zero on default hybrid run
- [ ] `--trajectory-only` — all `iso.f*.*` metric values zero; `meta.isolation_seconds` is 0

## Designer — compare workflow

- [ ] `python tools/sim_balance.py --label baseline --output balance_compare.csv --seconds 30`
- [ ] `python tools/sim_balance.py --label after_dummy --append --output balance_compare.csv --seconds 30` — third column appears
- [ ] Deliberate spawn tweak in `data/` (revert after) + re-run produces visible column diff in Excel

## Designer — gameplay regression

- [ ] `python -m src.main` — normal play unchanged (sim hooks are headless-only)

## Notes

- Stock `normal` is **not** a calibrated absolute baseline — use CSV for **relative** before/after diffs.
- Composite score weights in `src/sim/scoring.py` are v1 placeholders; tune after first CSV review.
- Full combined checklist index: `testing-checklists.md`.