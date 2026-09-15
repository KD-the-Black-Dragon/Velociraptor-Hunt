# Manual testing — PR7 (throwable catalog + fox archer + help)

Run: `python -m src.main`

## Throwable catalog

- [ ] Depth 1–3 floors can spawn **rocks** (light brown `.` on grey floor)
- [ ] Deeper floors show progressively rarer throwables (brick, dart, knife, etc.)
- [ ] Floor throwables use distinct glyphs/colors from dungeon floor
- [ ] Pickup stacks matching throwables in inventory

## Fox archer

- [ ] Fox archer at depth 5+ **shoots** (Path) — log says *shoots*, not *smites*
- [ ] Projectile animation visible when shot is in FOV
- [ ] Good ally blocking the beam prevents the shot

## Help overlay

- [ ] F1 or `?` lists **`f - throw best throwable`**
- [ ] Help lists **`F - pick throwable to throw`**

## Regression (PR6)

- [ ] Starter slot `c` still has 5 rocks
- [ ] `f` / `Shift+f` throw flow unchanged

Automated: `python -m pytest tests/test_throwables_pr7.py tests/test_player_throw_pr6.py tests/test_help_overlay.py -v`