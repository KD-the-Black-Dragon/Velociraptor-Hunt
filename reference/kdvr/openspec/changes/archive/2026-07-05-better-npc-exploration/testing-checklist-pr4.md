# Manual checklist — PR4 (retire PR10 shim + neutral player avoidance)

Run: `python -m src.main` — **F5** for full-map debug vision.

## Neutral rabbits near player

- [ ] Rabbit with **no evil visible** and player **one tile away**: rabbit **does not freeze** in place indefinitely.
- [ ] Rabbit does **not** path onto the **player tile** while exploring (may step onto adjacent tiles).
- [ ] Rabbit still **wanders** into other parts of the room/corridor over several turns.

## Neutral explore routing (regression)

- [ ] Rabbit in a corridor with a dead end: uses **BFS explore steps** (no two-tile ping-pong).
- [ ] After brief stall at a blocked end, **re-picks** a distant reachable goal and drifts away.

## Evil / good regression

- [ ] Wolf door spite + explore dispersal unchanged (PR3).
- [ ] Visible chase / follow / flee / memory still greedy.
- [ ] Good–neutral corridor swap still works.

## PR10 shim retired

- [ ] No wait-on-recent full stops when player is nearby (old PR10 symptom).