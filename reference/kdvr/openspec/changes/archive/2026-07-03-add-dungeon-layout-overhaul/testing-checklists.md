# Manual testing — add-dungeon-layout-overhaul (final acceptance)

Run: `python -m src.main`

Consolidated from `testing-checklist-pr0.md` through `testing-checklist-pr4.md`.

## Map generation (PR0–PR1)

- [ ] Descend many floors — varied boxy / organic / hybrid silhouettes (F4 force modes optional QA)
- [ ] No obvious stair clusters; three `>` spread across the map
- [ ] No tiny two-room floors dominating; occasional `[map_gen] rejected attempt` in PowerShell is OK
- [ ] Giant fallback room only if generation is forced to fail (rare in normal play)

## Doors (PR2)

- [ ] `+` / `-` at corridor mouths only (not room centers)
- [ ] Walk into `+` opens; **`c`** + direction closes
- [ ] Close blocked when entity/item on door tile
- [ ] NPCs do not pass closed doors; FOV blocked by `+`

## Runes & floor init (PR3)

- [ ] Three `0` runes well separated (≥ ~20 steps from start and each other)
- [ ] Descend with knight follower — runes still spread
- [ ] Occasional `[floor_init] rejected attempt` OK; no soft-lock

## Prefetch (PR4)

- [ ] Linger on title 3–5 s → New Game feels snappy (`[prefetch] hit` optional in PowerShell)
- [ ] Explore floor 1 → descend to floor 2 feels snappy when prefetch won
- [ ] **Movement stays responsive** on floor 2 while prefetch runs for floor 3 (no GIL hitch)
- [ ] F3/F4 + **R** invalidates stale prefetch

## Regression

- [ ] Wait, combat, vore, descent followers, UI layout unchanged
- [ ] Debug **R** regen still works

## Automated gate

```bash
python -m pytest tests/test_dungeon_layout_pr0.py tests/test_dungeon_layout_pr1.py tests/test_dungeon_layout_pr2.py tests/test_dungeon_layout_pr3.py tests/test_floor_prefetch.py tests/test_dungeon_pr2.py tests/test_floor_runes_pr3.py tests/test_acceptance.py -q
```

Full suite: `python -m pytest tests/ -q` (user-approved skip: flaky UI/vore render tests if present).