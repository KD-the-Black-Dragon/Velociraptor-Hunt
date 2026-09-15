# Manual checklist — PR2 (density-driven spawning)

Run: `python -m src.main`

- [ ] New game: monster count feels plausible for map size (not fixed 17 every floor)
- [ ] Water floors: sharks may appear but count is not always exactly 2
- [ ] Descend with a knight follower: total NPCs on new floor is lower (not duplicated knight quota)
- [ ] No monsters respawn mid-level after defeating some
- [ ] Regression: descent, wait key, engulfed block still work