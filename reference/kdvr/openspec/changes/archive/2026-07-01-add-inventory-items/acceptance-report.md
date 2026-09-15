# Acceptance Report: add-inventory-items

**Date:** 2026-07-01  
**Scope:** `openspec/specs/inventory-items/spec.md` and cross-spec updates

## Automated verification

```bash
python -m pytest tests/ -v
```

**Last run:** 416 passed, 0 failed (2026-07-01)

| Area | Tests | Result |
|------|-------|--------|
| Registries, spawn, pickup | `test_inventory_items_pr1.py` | PASS |
| Modals, drop, inspect | `test_inventory_items_pr2.py` | PASS |
| Wield, wear, durability | `test_inventory_items_pr3.py` | PASS |
| Quaff from data | `test_inventory_items_pr4.py` | PASS |
| Wand evoke + targeting | `test_inventory_items_pr5.py` | PASS |
| Core acceptance (AC6/AC7 updated paths) | `test_acceptance.py` | PASS |
| Prior domains | full suite | PASS |

## Manual verification

- [x] User playtest sign-off across PRs 1–5
- [x] Category commands replace global letter-key use
- [x] Wield/wear/quaff/evoke turn rules; pickup/drop/inspect free
- [x] Wand cursor-only targeting; evil-only valid strikes
- [x] Durability and red destroy/break logs
- [x] Engulfed pack block; passive worn armor digestion mitigation
- [x] Player/NPC glyphs over floor items

## Requirement coverage (highlights)

| Requirement | Verified by |
|-------------|-------------|
| Item registries from JSON | `test_inventory_items_pr1.py` |
| Walkover + `,` pickup | `test_inventory_items_pr1.py`, `test_inventory_items_pr2.py` |
| Category modals + Escape | `test_inventory_items_pr2.py` |
| Wield/wear + `effective_fighter` | `test_inventory_items_pr3.py` |
| Weapon/armor durability | `test_inventory_items_pr3.py` |
| Quaff heal from JSON | `test_inventory_items_pr4.py` |
| Wand evoke + charges | `test_inventory_items_pr5.py` |
| Stunned quaff | `test_acceptance.py` (`test_ac6`) |
| Full inventory rejection | `test_acceptance.py` (`test_ac7`) |

## Spec updates

- `openspec/specs/inventory-items/spec.md` — live normative spec
- `openspec/specs/core-roguelike/spec.md` — inventory requirement, HUD, stunned quaff
- `openspec/specs/enhancements-1/spec.md` — turn rules, controls
- `openspec/specs/enhancements-2/spec.md` — examine full reveal, Escape scope
- `openspec/specs/dungeon/spec.md` — descent preservation, item spawn
- `openspec/specs/vore/spec.md` — pack gating while engulfed
- `openspec/specs/digestion/spec.md` — armor `digestion_ac`
- `openspec/specs/npc-data/spec.md` — item stubs → gameplay wired
- `README.md` — inventory controls + modding items
- `data/SCHEMA.md` — item file field reference

## Verdict

**add-inventory-items: ACCEPTED** (pending final user playtest on combined checklist)