# PR 2 — Manual checklist: Combat range + generic spawn

Run `python -m src.main` from the project root.

## Automated gate (PR 2 only — not full suite)

```bash
python -m pytest tests/test_npc_data_pr2.py -v
python -m pytest tests/test_dungeon_pr2.py tests/test_dungeon_pr3.py tests/test_vore_constants.py tests/test_enhancements_3.py::test_spawn_fixed_population_counts tests/test_enhancements_3.py::test_wolf_outdamages_knight_at_spawn -v
```

## Combat (bump attacks)

- [ ] Bump a wolf — roughly 1 in 3 swings miss (`player accuracy 2` vs `wolf evade 2`)
- [ ] Bump a rabbit — misses more often than wolves (high evade)
- [ ] Wolf hits feel stronger than knight hits on the same target
- [ ] Rabbit bump does not kill (0 damage band) but can still miss
- [ ] Player attacks show **"You miss …"** when attack fails hit check

## Spawn parity

- [ ] New game: count wolves (6), knights (5), rabbits (6) on land-only floor
- [ ] Floor with water: +2 sharks in deep water tiles
- [ ] Descend with a knight follower: one fewer knight spawns on the new floor (5 → 4 knights)
- [ ] Seeded new game (`seed=12345`) reproduces same monster HP layout as before

## Data wiring

- [ ] `Fighter` has `accuracy`, `evade`, `ac`, `min_damage`, `max_damage` — no `power` / `defense`
- [ ] NPC stats match `data/entities.json` (e.g. wolf min/max damage 6)

## Regression

- [ ] Main menu → new game → play a few turns without crash
- [ ] F2 debug still weakens all monsters to 1 HP
- [ ] Vore, digestion, descent, followers still work