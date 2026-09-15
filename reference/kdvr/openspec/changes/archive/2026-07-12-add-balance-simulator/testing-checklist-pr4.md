# PR4 manual testing checklist — visible loot, equip, upgrade tracking

**Change:** `add-balance-simulator`  
**PR:** visible loot priority, strict-better equip, upgrade spawn/take flags

## Automated (agent)

- [x] `python -m pytest tests/test_sim_equip.py -v -n 4`
- [x] `python -m pytest tests/test_sim_threat.py tests/test_sim_navigation.py tests/test_sim_runner.py -v -n 4` (39 total sim tests passed)

## Designer playtest

- [ ] `python -m src.main` — walk over a visible weapon/armor/potion; pickup and wield/wear still work for human player
- [ ] Smoke: `python tools/_sim_smoke_one.py 23 5000` — note `runes` count (may improve now that bot picks up potions)

## PR4 behavior to spot-check (optional)

- [ ] Bot in sim paths toward visible floor loot before runes when not bailing (watch via debug if needed)
- [ ] Strictly-better club on floor gets wielded over starter dagger in unit tests (automated)

## Regression risks

- [ ] Live inventory wield/wear unchanged (sim calls same `_wield_from_slot` / `_wear_from_slot`)
- [ ] PR3 bail/rest/consumables still pass (`test_sim_threat.py`)
- [ ] PR2 navigation depth smoke still passes (seed 23)

## Notes

- Upgrade flags compare against **floor-entry** loadout, not mid-floor swaps.
- Pinned seeds: `openspec/specs/balance-simulator/spec.md`