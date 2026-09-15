# Manual checklist — Dungeon Enhancement PR 2

Run: `python -m src.main`

## Map generation (this PR)

- [ ] New Game produces **varied** layouts (rooms, wider/narrow passages — not uniform boxes only)
- [ ] Some floors show **blue `~` deep water** in lake/river shapes (not every floor; probabilistic)
- [ ] Water does **not** block reaching all land areas (detours OK)
- [ ] Exactly **three `>` downstairs** visible on explored floors
- [ ] FOV reveals terrain **through** water tiles
- [ ] Cannot walk into deep water as the player

## Regression

- [ ] PR 1 mobility/render still correct
- [ ] **17** NPCs still spawn (wolves, knights, rabbits)
- [ ] Movement, combat, vore, digestion, menu flow normal
- [ ] Debug **R** / **F2** / **S** still work

## Automated gate

```bash
python -m pytest tests/test_dungeon_pr2.py tests/ -q
```