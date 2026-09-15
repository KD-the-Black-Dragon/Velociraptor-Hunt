# Acceptance Report: add-npc-data-driven

**Date:** 2026-07-01  
**Scope:** `openspec/specs/npc-data/spec.md` and cross-spec updates

## Automated verification

```bash
python -m pytest tests/ -v
```

**Last run:** 360 passed, 0 failed (2026-07-01)

| Area | Tests | Result |
|------|-------|--------|
| Entity loaders + ignore-unknown | `test_npc_data_pr1.py` | PASS |
| Combat range + weight spawn | `test_npc_data_pr2.py` | PASS |
| Vore narratives from data | `test_npc_data_pr3.py` | PASS |
| Terrain, depth, followers | `test_npc_data_pr4.py` | PASS |
| Prior acceptance / enhancements | full suite | PASS |

## Manual verification

- [x] User playtest sign-off across PRs 1–5
- [x] Population parity from `entities.json` weights (6/5/6 land, 2 sharks on water)
- [x] Combat misses and damage range observable in play
- [x] Vore/digestion text from JSON; `vore_content.py` removed
- [x] Knight follower reduces fresh knight spawns on descent

## Requirement coverage (highlights)

| Requirement | Verified by |
|-------------|-------------|
| `entities.json` loader | `test_npc_data_pr1.py` |
| Alignment profiles | `test_npc_data_pr1.py`, `test_npc_data_pr3.py` |
| Weight spawn parity | `test_npc_data_pr2.py`, `test_enhancements_3.py` |
| Combat formulas | `test_npc_data_pr2.py` |
| Narrative index by `id` | `test_npc_data_pr3.py` |
| Depth / terrain / water gates | `test_npc_data_pr4.py` |
| Good follower pool deduction | `test_npc_data_pr4.py`, `test_dungeon_pr3.py` |
| Miss message grammar | `test_enhancements_2.py` |

## Spec updates

- `openspec/specs/npc-data/spec.md` — live normative spec
- `openspec/specs/core-roguelike/spec.md` — `Fighter` combat fields
- `openspec/specs/enhancements-3/spec.md` — data-driven spawn weights
- `openspec/specs/dungeon/spec.md` — follower deduction, aquatic spawn
- `openspec/specs/vore/spec.md` — narratives from data
- `openspec/specs/digestion/spec.md` — digestion lines from data
- `README.md` — modding section + combat notes

## Verdict

**add-npc-data-driven: ACCEPTED**