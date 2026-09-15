# PR 4 — Manual checklist: Terrain, depth, followers

Run `python -m src.main` from the project root.

## Automated gate (PR 4 only — not full suite)

```bash
python -m pytest tests/test_npc_data_pr4.py -v
python -m pytest tests/test_dungeon_pr4.py tests/test_dungeon_pr3.py::test_followers_reduce_fresh_knight_spawns tests/test_dungeon_pr3.py::test_descend_respawns_monsters_and_items -v
```

## Terrain and water

- [ ] New game on a dry floor: wolves, knights, rabbits on land — **no sharks**
- [ ] Floor with deep water: sharks appear **only** in water tiles (not on land)
- [ ] Land NPC count unchanged when sharks are present (still 17 ground spawns)

## Depth (smoke)

- [ ] HUD depth increments on `Shift+.`
- [ ] Deeper floors still spawn the standard population (stock data uses `min_depth` 1 / `max_depth` 1000)

## Followers on descent

- [ ] Visible knight follows you to the new floor
- [ ] Descend with 1 knight follower → **4** fresh knights on new floor (5 weight − 1 follower)
- [ ] Hidden knight does **not** follow and does **not** reduce spawns

## Regression

- [ ] Sharks can still attack from shore tiles (aquatic combat)
- [ ] Descent still respawns monsters and potions