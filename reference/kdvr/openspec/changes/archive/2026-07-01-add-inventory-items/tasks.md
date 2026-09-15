# Tasks: Inventory and Data-Driven Items

Check off as completed. Implement **one PR at a time**; wait for user playtest sign-off between PRs.

## PR 1: Registries, instances, floor spawn, pickup

- [x] Frozen item registries from four JSON files (incl. `durability_max`, armor `digestion_ac`)
- [x] Replace `ItemType` with item instances (`item_id`, category, durability, charges)
- [x] Weighted floor item spawn (depth filter + potion `spawn_min`); floor items carry durability
- [x] Walkover auto-pickup all + manual `,` pickup (no turn); potion stacking; ground pickup modal
- [x] `tests/test_inventory_items_pr1.py`
- [x] `testing-checklist-pr1.md`

## PR 2: Modals, drop, inventory inspect, retire letter-use

- [x] `InventoryModalState` + render; engine input routing (after digestion modals)
- [x] `i` two-step inspect (list → full detail; Esc back/close); floor examine full reveal
- [x] Escape dismisses inventory modals only (digestion Escape unchanged)
- [x] Remove global `INVENTORY_KEYS` / `use_inventory_slot` letter routing
- [x] Empty-category, engulfed, and manual-pickup messages per `design.md`
- [x] `tests/test_inventory_items_pr2.py`
- [x] `testing-checklist-pr2.md`

## PR 3: Wield and wear + combat stats + durability

- [x] `EquipState` (`wielded_slot`, `worn_slot`) on player
- [x] `w` / `W` modals; already-wielded/worn errors; turn on success
- [x] `effective_fighter()` for player bump combat
- [x] Weapon durability −1 per successful player hit; destroy at 0 (red log)
- [x] Armor `digestion_ac` mitigates player digestion ticks; durability −= mitigated; destroy at 0
- [x] Drop clears equip pointers; dropped items preserve durability on floor
- [x] Remove inventory summary from main HUD (`i` is the inventory UI)
- [x] `tests/test_inventory_items_pr3.py`
- [x] `testing-checklist-pr3.md`

## PR 4: Quaff potions from data

- [x] `q` modal; `effect: heal` from registry; consume item; turn on success
- [x] Stunned player may quaff (preserve AC6 intent)
- [x] Player glyph renders over floor items on the same tile (drop fix)
- [x] `tests/test_inventory_items_pr4.py`
- [x] `testing-checklist-pr4.md`

## PR 5: Evoke wands + targeting

- [x] `v` two-step modal (wand pick → target pick)
- [x] Default target: nearest evil NPC, else player; arrow/direction target cycle; LoS + range
- [x] `magic_missile` effect; charges decrement; remove at 0
- [x] `tests/test_inventory_items_pr5.py`
- [x] `testing-checklist-pr5.md`

## PR 6: Spec and acceptance

- [x] `openspec/specs/inventory-items/spec.md`
- [x] Cross-spec updates (`core-roguelike`, `enhancements-1`, `enhancements-2`, `dungeon`, `vore`, `npc-data`, `digestion`)
- [x] README modding/items section
- [x] `testing-checklists.md`, `acceptance-report.md`, archive
- [x] Full `pytest tests/` green