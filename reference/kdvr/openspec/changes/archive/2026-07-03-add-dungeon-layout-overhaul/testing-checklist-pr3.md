# Manual checklist — PR3 (floor init, runes, acceptance)

Run: `python -m src.main`

## Rune spread fix

- [ ] **New game** — three **`0`** runes are **well separated** (not within ~5 steps of each other)
- [ ] Descend **10+** floors — runes stay spread; no recurring 3-rune blob by entrance
- [ ] Descend with **knight follower in LOS** — runes still spread (todo bug regression)

## Floor init loop

- [ ] Occasional `[floor_init] rejected attempt` in PowerShell is OK
- [ ] No soft-lock on descent; floor always loads

## Full regression

- [ ] **New game** and **R** use same generation quality as descent
- [ ] Doors open/close still work
- [ ] Layout variety (boxy/organic/hybrid) still present
- [ ] Stairs spread; maps not tiny
- [ ] Items on floor do not seem to “pull” runes into corridors

## Automated (final PR — broader suite)

- [ ] `pytest tests/test_dungeon_layout_pr0.py tests/test_dungeon_layout_pr1.py tests/test_dungeon_layout_pr2.py tests/test_dungeon_layout_pr3.py -q`
- [ ] `pytest tests/test_dungeon_pr2.py tests/test_floor_runes_pr3.py -q`
- [ ] Full `pytest tests/` except known flaky UI/render tests (user-approved skip)