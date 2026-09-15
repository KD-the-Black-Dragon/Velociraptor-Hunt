# PR3 manual testing checklist — threat, consumables, rest, bail

**Change:** `add-balance-simulator`  
**PR:** lethal-risk consumables, rest, stunned heal/teleport, bail-for-stairs

## Automated (agent)

- [x] `python -m pytest tests/test_sim_threat.py -v -n 4`
- [x] `python -m pytest tests/test_sim_navigation.py tests/test_sim_runner.py -v -n 4` (30 passed)

## Designer playtest

- [ ] `python -m src.main` — new game still feels playable (balance in flux; not blocking PR3)
- [ ] Smoke: `python tools/_sim_smoke_one.py 23 5000` — depth ≥ 2 on normal pinned seed
- [ ] Smoke: `python tools/_sim_smoke_easy.py 4242 8000` — depth ≥ 2 and bail latched on ≥1 floor

## PR3 behavior to spot-check (optional black-box)

- [ ] Hurt player with no visible evil can rest between fights (live game; sim uses same rest path)
- [ ] Stunned player with heal/teleport in inventory recovers (unit tests cover sim path)

## Regression risks

- [ ] Live combat / stunned / rest unchanged for human player (sim-only policy layer)
- [ ] PR2 navigation still reaches depth ≥2 on seed 23 (`test_trajectory_run_reaches_depth_two_on_pinned_normal_seed`)
- [ ] Bail does not block live game — sim-only `bail_for_survival` flag

## Notes

- Post-PR3, starter loadout (no heal potions) often triggers bail before rune quota; **valid play** per design. Rune-collection smoke re-checked after PR4 loot.
- Pinned seeds: `openspec/specs/balance-simulator/spec.md`