# Tasks: Equipment Catalog Expansion

Check off as completed. Implement **one PR at a time**; wait for user playtest sign-off between PRs.

## PR 1: Weapons + unarmed + spawn cap

- [x] Expand `data/weapons.json` (12 weapons; overlap/rotation per `design.md`)
- [x] `PLAYER_MIN_DAMAGE=1`, `PLAYER_MAX_DAMAGE=2`, `PLAYER_ACCURACY=1.5` in `constants.py`
- [x] `MAX_FLOOR_ITEM_PLACEMENTS = 5` in `spawn.py` / `constants.py`
- [x] Tests: ordering smoke, depth introduction table, placement cap
- [x] `testing-checklist-pr1.md`

## PR 2: Armor catalog

- [x] Expand `data/armor.json` — all glyph `[`, colors per `design.md`
- [x] Starter loadout: dagger `a` wielded, robes `b` worn (`apply_starter_loadout`)
- [x] Tests: AC/digestion ordering, waxed/oiled tradeoffs, starter loadout
- [x] `testing-checklist-pr2.md`

## PR 3: Wand catalog

- [x] Expand `data/wands.json` (5 wands, all `magic_missile`)
- [x] Tests: depth unlocks, damage monotonicity
- [x] `testing-checklist-pr3.md`

## PR 4: Potion catalog

- [x] Add `greater_healing`, `power_healing` to `potions.json`; tune health weight down
- [x] Tests: heal tier ordering, depth eligibility
- [x] `testing-checklist-pr4.md`

## PR 5: Spec and acceptance

- [x] `openspec/specs/equipment-catalog/spec.md`
- [x] Cross-spec note in `inventory-items`
- [x] `data/SCHEMA.md` + README
- [x] `testing-checklists.md`, `acceptance-report.md`, archive
- [x] Full `pytest tests/` green