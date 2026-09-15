# Acceptance Report: add-dungeon-enhancement

**Date:** 2026-06-30  
**Scope:** `openspec/specs/dungeon/spec.md` and cross-spec updates (`core-roguelike`, `vore`, `enhancements-3`)

## Automated verification

```bash
python -m pytest tests/ -v
```

**Last run:** 318 passed, 0 failed (2026-06-30)

| Area | Tests | Result |
|------|-------|--------|
| Tiles, mobility, render | `test_dungeon_pr1.py` | PASS |
| Map gen, water, stairs, connectivity | `test_dungeon_pr2.py` | PASS |
| Floor depth, descent, ally follow, HUD | `test_dungeon_pr3.py` | PASS |
| Aquatic combat, sharks, mobility escape | `test_dungeon_pr4.py` | PASS |
| Core acceptance | `test_acceptance.py` | PASS |
| Prior enhancements / vore / digestion | full suite | PASS |

## Manual verification

- [x] User playtest sign-off across PRs 1–4
- [x] Descent, depth HUD, engulfed/stairs messages
- [x] Water floors, sharks, shore combat
- [x] Good knight follow on descent

## Requirement coverage (highlights)

| Requirement | Verified by |
|-------------|-------------|
| Tile types + FOV through water | `test_dungeon_pr1.py` |
| Mobility (ground/fly/aquatic) | `test_dungeon_pr1.py`, `test_dungeon_pr4.py` |
| Mixed map gen + connectivity | `test_dungeon_pr2.py` |
| Three reachable downstairs | `test_dungeon_pr2.py` |
| Descend on `Shift+.` | `test_dungeon_pr3.py` |
| Good ally follow | `test_dungeon_pr3.py` |
| Shark spawn on water floors | `test_dungeon_pr4.py` |
| Aquatic shore combat | `test_dungeon_pr4.py` |
| Mobility-aware vore escape | `test_dungeon_pr4.py` |
| Land NPC counts unchanged | `test_dungeon_pr4.py` |

## Spec updates

- `openspec/specs/dungeon/spec.md` — live normative spec (created during change)
- `openspec/specs/core-roguelike/spec.md` — multi-floor + dungeon extension notes
- `openspec/specs/vore/spec.md` — mobility-aware escape scenarios
- `openspec/specs/enhancements-3/spec.md` — sharks, descent follow
- `README.md` — dungeon controls, water, descent, sharks

## Verdict

**DUNGEON ENHANCEMENT: ACCEPTED**