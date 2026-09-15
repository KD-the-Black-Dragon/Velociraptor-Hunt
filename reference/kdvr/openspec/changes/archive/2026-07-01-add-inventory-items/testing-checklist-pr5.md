# PR 5 — Evoke wands + targeting

Run `python -m src.main` from the project root.

Automated: `python -m pytest tests/test_inventory_items_pr5.py -v`

## Evoke (`v`)

- [ ] No wands (or all at 0 charges) → `You have no wands.`
- [ ] `v` opens wand-only modal; letter selects wand
- [ ] Second step: **no modal** — only examine-style cursor on target tile (map stays visible)
- [ ] Default target: nearest evil NPC in range/LoS
- [ ] Only evil NPCs are valid targets; self/good/neutral → `Not the best target.` (modal closes, no turn)
- [ ] No evil in range on wand pick → `No valid targets in range.` (no target step)
- [ ] Arrow keys cycle targets; Enter confirms; Esc aborts (no turn)
- [ ] Hit/miss/defeat logs use standard combat messages
- [ ] Charge decrements; at 0 charges wand removed with **red** log: `Your {name} breaks!`
- [ ] Turn consumed on successful evoke

## Range and LoS

- [ ] Targets beyond wand `range` (Chebyshev) not listed
- [ ] Targets behind walls not listed

## Engulfed

- [ ] `v` logs pack blocked while engulfed

## Regression

- [ ] `q`, `w`, Shift+w, `i`, `d`, pickup still work
- [ ] Dropped items render under `@` (player on top) and under NPC glyphs