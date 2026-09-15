# Manual testing — PR6 (inventory multi-column + digestion font)

**How to run:** `python -m src.main`

TEMP full starter pack (25 daggers + robes) is still on for main so you can stress 26 slots.

## Happy path

- [ ] New game → press **i** — inventory shows **all** a–y daggers + z robes without clipping
- [ ] Layout uses **multiple columns** when the window is wide enough (2–3)
- [ ] Reading order is **down the first column, then next** (a under b…, not a then b across)
- [ ] Long names **wrap inside the cell** (resize window if needed to force wrap)
- [ ] Font matches **digestion modal** face/size feel (log font +2), not map tiles
- [ ] Press a letter → detail modal (single column) with stats; **Esc** returns to list
- [ ] **Esc** closes list

## Filtered lists / other surfaces

- [ ] **d** drop list with full pack — multi-column; pick a letter drops
- [ ] **w** wield — few weapons still readable (1 col if few)
- [ ] **W** wear — robes on z
- [ ] **q** / **v** if you have potions/wands — same chrome
- [ ] Ground **,** multi-item pickup list uses same multi-column style when many items

## Window / columns

- [ ] Narrow window → fewer columns (often 1)
- [ ] Wide / fullscreen → 2 or 3 columns when many items
- [ ] Short inventory (drop most items) → single column when ≤8

## Regressions

- [ ] Digestion modal still looks as approved (if you can trigger it)
- [ ] Message log still proportional
- [ ] Map tiles still fixed-width CP437
- [ ] Evoke target cursor mode still works (no list overlay on map cursor)

## TEMP loadout

- [ ] Sign off multi-column UX before we remove the full starter pack  
  (or report bugs first)

## Automated

- [ ] `python -m pytest tests/test_text_ux_pr6_inventory_layout.py tests/test_inventory_items_pr2.py -v`
