# Manual checklist — PR1 (layout archetypes)

Run: `python -m src.main`

## Debug 100% force modes (F4)

- [ ] Press **F4** until console/log shows **boxy** forced — descend or **R** regen **3+** floors; layouts are clearly **rectangular rooms + corridors**
- [ ] **F4** → **organic** forced — **3+** floors show **large open caverns**, sparse **narrow chokes**, not a uniform tunnel maze
- [ ] **F4** → **hybrid** forced — mix of big open areas and boxy sections visible
- [ ] **F4** back to **default** (no force) — 40/40/20 mix over **10+** floors (variety returns)

## Organic specifics

- [ ] On organic-forced floors: **4–6** distinct large open regions connected by **1-tile** (or similarly narrow) passages
- [ ] Some organic floors include a **large lake** in one cavern (not every floor)

## Regression (PR0)

- [ ] Stairs still spread out; no stair clusters
- [ ] PowerShell discard logging still works if needed
- [ ] Descent, wait, followers unchanged

## Automated

- [ ] `pytest tests/test_dungeon_layout_pr1.py -q`
- [ ] `pytest tests/test_dungeon_pr2.py -q`