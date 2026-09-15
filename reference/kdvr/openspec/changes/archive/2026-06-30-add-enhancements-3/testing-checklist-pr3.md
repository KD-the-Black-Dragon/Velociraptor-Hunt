# PR 3 Manual Testing Checklist — AI Memory and Exploration

Run `python -m src.main` from the project root.

---

## Automated gate

```bash
python -m pytest tests/test_enhancements_3.py -v
python -m pytest tests/ -q
```

All tests should pass.

---

## Evil AI

- [ ] Wolf with line of sight to **knight and rabbit** pursues the knight (not the rabbit)
- [ ] Wolf loses sight of player/knight, then later moves toward **last known** primary position
- [ ] With no player/knight visible, wolf pursues a visible **rabbit**
- [ ] With nothing visible, wolves **wander** toward random map goals (not idle)

## Good AI

- [ ] With no evil visible, knight **follows** the player (moves closer over several turns)
- [ ] Knight with LOS to **wolf and player** attacks the wolf (not the player)
- [ ] Knight does **not** chase rabbits or other knights
- [ ] Knight adjacent to player: **no swap**, no message-log line (console may log attempt)

## Neutral AI

- [ ] Rabbit **flees** from visible wolf (HP > 0)
- [ ] Stunned rabbit (0 HP) does **not** move
- [ ] Rabbit with no threats **explores** (moves over time)

## Frustration (regression)

- [ ] Wolf → rabbit → knight corridor: wolf attacks rabbit (console snarl only, not message log)

## Regression

- [ ] Player vore modal unchanged when stunned
- [ ] Swap with good/neutral still player-only

**Pass criteria:** Faction AI priorities feel right; memory and explore fill quiet moments; pytest green.