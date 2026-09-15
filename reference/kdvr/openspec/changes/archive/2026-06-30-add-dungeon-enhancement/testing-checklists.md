# Dungeon Enhancement — Manual Testing Checklist

Run `python -m src.main` from the project root.

---

## Automated gate

```bash
python -m pytest tests/test_dungeon_pr1.py tests/test_dungeon_pr2.py tests/test_dungeon_pr3.py tests/test_dungeon_pr4.py -v
python -m pytest tests/ -q
```

All tests should pass.

---

## Tiles and mobility (PR 1)

- [ ] Ground player blocked by deep water (`~`); log explains impassable water
- [ ] FOV passes through water tiles
- [ ] Water and stairs glyphs render correctly when present

## Map generation (PR 2)

- [ ] Varied layouts (rooms, organic caves, wide/narrow corridors)
- [ ] Some floors show shaped deep water (lakes/rivers; probabilistic)
- [ ] All land reachable from entrance; water may force detours
- [ ] Three `>` downstairs per floor, each reachable
- [ ] **F3** toggles water-heavy generation; **R** regens with current mode

## Floor depth and descent (PR 3)

- [ ] HUD shows **Depth N** (starts at 1)
- [ ] **`.`** waits; **Shift+`.`** descends on `>`
- [ ] Off stairs: *"There are no stairs here."* (no turn)
- [ ] Engulfed: *"Going deeper won't help you here!"* (no turn)
- [ ] Descent preserves HP, inventory, name, options prefs
- [ ] Good knight in LOS follows to new floor near entrance
- [ ] **R** resets depth to 1

## Aquatic combat and sharks (PR 4)

- [ ] Two sharks (`s`) on water floors; none without water
- [ ] Shark shore bump-attacks from water without entering land
- [ ] Land NPC counts unchanged (6 wolves, 5 knights, 6 rabbits)
- [ ] Ground escape from engulf avoids water tiles

## Regression

- [ ] Main menu, name entry, options, quit confirmation
- [ ] Player vore modal, digestion, recap → menu
- [ ] NPC factions, swap, stunned/regen, rescue
- [ ] Debug **S**, **F2**, **F3**, **R**