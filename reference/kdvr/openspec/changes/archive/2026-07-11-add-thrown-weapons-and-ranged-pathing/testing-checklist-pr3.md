# Manual checklist — PR3 RangeN NPC AI + test assignments

Run: `python -m src.main`

## Low-level monster ranged assignments (abilities only)

| Species | Ability | Type | Max distance | Log verb | Notes |
|---------|---------|------|--------------|----------|-------|
| **wolf** | `Range6` | Path | 6 | *shoots* | `ranged_accuracy` 1.0, damage 4 (playtest range) |
| **slime** | `Smite3` | Smite | 3 | *smites* | `ranged_accuracy` 0.5, damage 2–3 |

**As-designed:** `RangeN` / `SmiteN` do **not** work on **Erratic** entities (bat, cave rat) — erratic AI bypasses ranged engagement.

## Happy path

- [ ] Wolf at distance 2–6 with clear line **shoots** (not smites) the player
- [ ] Slime at distance 3 **smites**
- [ ] Wolf/slime at distance 1 **melee** — no ranged shot

## Path blocking

- [ ] Two wolves in a line: rear wolf does **not** shoot when front wolf blocks the beam
- [ ] Wand (`v`) still **smites** through a good ally (Smite ignores intermediates)

## Regression

- [ ] Stock combat, movement, vore unchanged aside from new ranged lines
- [ ] Slime still chases when out of smite range

Automated: `python -m pytest tests/test_npc_abilities_range_path.py tests/test_ranged_path.py tests/test_npc_abilities_smite.py -v`