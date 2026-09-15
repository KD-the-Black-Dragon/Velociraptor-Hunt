# Manual testing checklist — PR4 (NPC prefixes / Elite)

Run: `python -m src.main`

Stock `prefix_spawn` is **zero chance** on all difficulties → **no elites in normal play** until PR5.

## Happy path (stock)

- [ ] New game: enemies still show normal names (`wolf`, `bat`, …) — no `Elite `
- [ ] Combat / vore / dig unchanged
- [ ] Save/load works

## Optional: force elites (then revert)

In `data/depth_scaling.json` under Hard (or Normal):

```json
"prefix_spawn": {
  "base_chance_pct": 100,
  "chance_pct_per_depth_step": 0,
  "max_chance_pct": 100,
  "start_depth": 1
}
```

- [ ] New game on that difficulty: many **Elite wolf** / **Elite bat** etc. (evil only)
- [ ] Elites feel tougher (more HP/AC/damage)
- [ ] Summons (if any) do **not** get Elite names
- [ ] Knights/rabbits never Elite
- [ ] Revert `prefix_spawn` to omit or all zeros

## Regression

- [ ] Difficulty Options + Past Runs still fine
- [ ] Floor runes still 3

## Automated

- [x] `python -m pytest tests/test_npc_prefixes_pr4.py -v`
