# Manual testing checklist — PR4 (blink)

Run: `python -m src.main`

**TEMP starter:** **potion of blinking** is in inventory (with other test potions).

## Blink flow

- [ ] `q` → select blinking potion → log “Blink where?…”
- [ ] Cursor moves with arrows / vi-keys; map stays visible
- [ ] **Esc** cancels — potion still in inventory; no turn spent
- [ ] **Enter** on invalid — potion kept; yellow log with specific reason:
  - out of sight → `Invalid - cannot blink outside of sight radius.`
  - wall / deep water → `Invalid - tile is not walkable.`
  - NPC → `Invalid - that tile is occupied.`
- [ ] **Enter** on valid visible floor — move there, potion consumed, turn spent

## Regression

- [ ] Teleport still works
- [ ] Wand evoke targeting still works
- [ ] Other potions unchanged

## Automated

- [x] `tests/test_potion_blink_pr4.py`
