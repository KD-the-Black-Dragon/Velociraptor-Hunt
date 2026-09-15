# better-npc-exploration — Consolidated Manual Checklist

Run: `python -m src.main` — **F5** toggles debug omniscient player vision (NPC LOS unchanged).

Per-PR detail: `testing-checklist-pr1.md` … `testing-checklist-pr4.md` in this folder.

---

## Automated gate

```bash
python -m pytest tests/test_explore_reachable_goals.py tests/test_explore_frustration.py tests/test_explore_bfs_steps.py tests/test_neutral_explore.py tests/test_chase_pursuit_momentum.py tests/test_debug_omniscient_vision.py tests/test_enhancements_3.py -q
```

---

## PR1 — Reachable explore goals

- [ ] Wolf separated by closed door: explore goal never on far side
- [ ] Open door: goals on connected side remain valid
- [ ] Weighted pick favors farther reachable tiles over time

## PR2 — Explore frustration

- [ ] Blocked explore turns increment frustration; progress resets
- [ ] At limit: farthest-endpoint re-pick once, then resume far weighted picks

## PR3 — BFS explore steps + door behavior

- [ ] L-corridor: explore follows shortest route
- [ ] Single/two wolves at slammed door: brief linger, then wander off (no permanent oscillation)
- [ ] Evil wolves do not swap with each other (bump combat)
- [ ] Visible chase / follow / flee / memory still greedy

## PR4 — Neutral shared path

- [ ] Rabbits explore without two-tile ping-pong or PR10 freeze near player
- [ ] Rabbits may step onto player-adjacent tiles; never onto player tile
- [ ] Good–neutral corridor swap regression

## Regression

- [ ] Pursuit momentum + memory frustration give-up (PR9)
- [ ] Good follow / evil priority unchanged
- [ ] Player door open/close behavior unchanged