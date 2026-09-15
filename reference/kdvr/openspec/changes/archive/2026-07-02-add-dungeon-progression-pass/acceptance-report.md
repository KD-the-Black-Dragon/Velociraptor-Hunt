# Acceptance Report: add-dungeon-progression-pass

**Date:** 2026-07-02  
**Scope:** Density-driven spawning, floor runes, permanent progression

## Automated verification

```bash
python -m pytest tests/ -q
```

**Last run:** 457 passed, 0 failed (2026-07-02)

| Area | Tests | Result |
|------|-------|--------|
| Dungeon spawn config | `test_dungeon_spawn_config.py` | PASS |
| Density-driven spawn | `test_spawn_density_pr2.py` | PASS |
| Floor rune placement | `test_floor_runes_pr3.py` | PASS |
| Rune activation / progression | `test_floor_runes_pr4.py` | PASS |
| Prior acceptance / regression | full suite | PASS |

## Manual verification

- [x] User playtest sign-off PR2–PR4 (density, runes, activation, localized flash)
- [x] Three `0` runes per floor; color distinguishes effect
- [x] Step-on buffs persist across descent; vitality updates HUD HP
- [x] Good followers reduce fresh spawn total (species-agnostic)

## Requirement coverage (highlights)

| Requirement | Verified by |
|-------------|-------------|
| `dungeon_spawn.json` loader + target count | `test_dungeon_spawn_config.py` |
| Filtered-union density spawn | `test_spawn_density_pr2.py` |
| `good_aligned_weight_at_depth` | `test_spawn_density_pr2.py`, `test_dungeon_pr3.py` |
| Three runes per floor, glyph `0` | `test_floor_runes_pr3.py` |
| Step-on activation + progression | `test_floor_runes_pr4.py` |
| `effective_fighter()` + rune bonuses | `test_floor_runes_pr4.py`, `test_inventory_items_pr3.py` |
| Spawn call-site guard (engine only) | `test_spawn_density_pr2.py` |

## Spec updates

- `openspec/specs/dungeon/spec.md` — density-driven population; rune spawn hook; follower deduction
- `openspec/specs/npc-data/spec.md` — weight = probability; density spawn; species-agnostic follower cap
- `openspec/specs/floor-runes/spec.md` — **new** live normative spec
- `README.md` — population, runes, modding sections
- `data/SCHEMA.md` — `dungeon_spawn.json`, `floor_runes.json`

## Ad-hoc changes folded in

- **3 runes per floor** (`RUNES_PER_FLOOR = 3`)
- **All rune glyphs `0`**; `fg` color by effect
- **Localized one-frame flash** (`RUNE_FLASH_RADIUS = 3`) instead of full-screen

## Verdict

**add-dungeon-progression-pass: ACCEPTED**