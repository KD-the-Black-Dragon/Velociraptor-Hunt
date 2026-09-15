# Acceptance Report: add-more-entity-abilities

**Date:** 2026-07-11  
**Scope:** Hands, Wander, NoChase, PreferVore, RangedVoreN, stationary mobility, species content (PR1–PR7).

## Automated verification

### Full suite (step 1 — parallel, 4 workers)

```bash
python -m pytest tests/ -v -n 4
```

| Result | Count |
|--------|-------|
| **PASS** | **1515** |
| **FAIL** | **2** |
| Skipped | 2 |

### Serial rerun of step-1 failures (step 4)

| Test | Step 1 | Step 4 serial |
|------|--------|---------------|
| `test_engine_post_turn_hook_invokes_coordinator` | FAIL | PASS |
| `test_engulf_after_success_modal` | FAIL | PASS |

Both recovered on serial rerun (xdist flake). **No failed-twice cases** — no code changes required for acceptance.

### Change-scoped tests (PR1–PR6)

| Area | Files |
|------|-------|
| PreferVore | `test_npc_abilities_prefer_vore.py` |
| Wander | `test_npc_abilities_wander.py` |
| NoChase | `test_npc_abilities_no_chase.py` |
| Hands | `test_npc_abilities_hands.py`, `test_memory_pursuit_door_detour.py` |
| Stationary | `test_npc_mobility_stationary.py` |
| RangedVoreN | `test_npc_abilities_ranged_vore.py` |
| Content | `test_entity_abilities_content_pr6.py` |
| Parser | `test_ability_parser.py` |

## Manual verification

- [x] PR1–PR6 — user sign-off across session
- [x] PR7 — final acceptance authorized (*"We're good. Proceed with PR7."*)

## Requirement coverage

| Deliverable | Status |
|-------------|--------|
| `PreferVore` | Shipped |
| `Wander` | Shipped |
| `NoChase` | Shipped |
| `Hands` (bump-open, 80/20 break) | Shipped |
| `stationary` mobility | Shipped |
| `RangedVoreN` (pull on hit, dual tongue) | Shipped |
| Save codec `RangedVoreN` round-trip | Shipped |
| Species assignments (PR6) | Shipped |
| Wolf playtest overrides reverted | Shipped |

## Spec updates

- **Updated:** `openspec/specs/npc-abilities/spec.md`, `openspec/specs/vore/spec.md`, `openspec/specs/dungeon/spec.md` (stationary, PR4), `data/SCHEMA.md`

## Deferred

- **Thorns** — `openspec/changes/todo/spec.md`

## Out of scope (confirmed)

- Giant frog entity (RangedVore species fit noted for future content)
- Spore / living fire entities (Wander assigned to slime as mindless hazard stand-in)