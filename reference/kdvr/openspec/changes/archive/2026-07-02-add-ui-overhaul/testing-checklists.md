# Manual testing — add-ui-overhaul (final acceptance)

**Status:** Signed off 2026-07-02

Run: `python -m src.main`

## Display and layout

- [ ] Text is ~2× prior height (readable at default window size)
- [ ] Map shows a **viewport** smaller than the full dungeon; player stays centered while moving
- [ ] Right **sidebar**: your name, `HP nn/nn`, exact bar
- [ ] **Message log**: up to 8 lines at bottom; no name/HP/depth in log area
- [ ] **Status corner** (bottom-right): depth, stunned, engulfed when applicable

## Sidebar NPCs

- [ ] Evil NPCs in FOV listed under player; good NPCs at bottom; neutrals omitted
- [ ] Each NPC: name row, bar row, blank spacer; coarse ~6-wide estimate bar (no numeric HP)
- [ ] NPCs out of FOV not listed; overflow `+N more` when capped

## Options and presets

- [ ] Options → **UI Layout** cycles **Standard** / **Wide**; persists after restart
- [ ] **Standard** vs **Wide** visibly different after **New Game** (map vs sidebar width)
- [ ] Preset change on menu does not alter an in-progress run (N/A until new game)

## Window resize

- [ ] Drag window larger — map viewport grows; sidebar width unchanged
- [ ] Drag smaller — map shrinks first; cannot go below minimum client size (~1360×768)
- [ ] Main menu: title art and options stay aligned (no single-row jitter)

## Modals and menus

- [ ] Vore / digestion / recap / inventory modals centered on **full window**
- [ ] Examine and evoke **cursors** on map only
- [ ] Quit confirm on root console; bare **Shift** does not show invalid-key error
- [ ] Main menu, name entry, options readable at current scale

## Regression

- [ ] New Game → play → Ctrl+Q → Y → main menu
- [ ] Combat, FOV, descent, runes, inventory commands still work
- [ ] `python -m pytest tests/ -q` green