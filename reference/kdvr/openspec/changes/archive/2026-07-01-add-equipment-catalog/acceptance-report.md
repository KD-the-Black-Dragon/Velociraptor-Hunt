# Acceptance Report: add-equipment-catalog

**Date:** 2026-07-01  
**Scope:** `openspec/specs/equipment-catalog/spec.md` and cross-spec updates

## Automated verification

```bash
python -m pytest tests/ -v
```

**Last run:** 455 passed, 0 failed (2026-07-01)

| Area | Tests | Result |
|------|-------|--------|
| Weapons + spawn cap | `test_equipment_catalog_pr1.py` | PASS |
| Armor + starter loadout | `test_equipment_catalog_pr2.py` | PASS |
| Wand tiers | `test_equipment_catalog_pr3.py` | PASS |
| Potion tiers | `test_equipment_catalog_pr4.py` | PASS |
| Inventory mechanics | `test_inventory_items_pr*.py` | PASS |
| Prior domains | full suite | PASS |

## Manual verification

- [x] User playtest sign-off across PRs 1–5
- [x] 12 / 9 / 3 / 5 stock catalog entries load and spawn by depth
- [x] Sparse floors (`MAX_FLOOR_ITEM_PLACEMENTS = 5`)
- [x] Starter dagger `a` wielded, robes `b` worn
- [x] Unarmed 1–2 damage @ 1.5 accuracy
- [x] Armor all `[`; potions `!`; wands `/`

## Requirement coverage (highlights)

| Requirement | Verified by |
|-------------|-------------|
| Weapon ordering | `test_equipment_catalog_pr1.py` |
| Placement cap | `test_equipment_catalog_pr1.py` |
| Armor tradeoffs | `test_equipment_catalog_pr2.py` |
| Starter loadout | `test_equipment_catalog_pr2.py` |
| Wand depth tiers | `test_equipment_catalog_pr3.py` |
| Potion heal tiers | `test_equipment_catalog_pr4.py` |
| Health spawn_min | `test_equipment_catalog_pr4.py` |

## Spec updates

- `openspec/specs/equipment-catalog/spec.md` — live normative spec
- `openspec/specs/inventory-items/spec.md` — spawn cap, starter loadout, catalog reference
- `README.md` — catalog summary, starter loadout, spawn rarity
- `data/SCHEMA.md` — spawn policy section

## Verdict

**add-equipment-catalog: ACCEPTED**