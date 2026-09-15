# Manual checklist — PR3 (BFS explore steps + oscillation + evil no-swap)

Run: `python -m src.main` — **F5** for full-map debug vision.

## Corridor explore (no player contact)

- [ ] Neutral rabbit in long corridor with dead-end wall: does **not** ping-pong two tiles indefinitely.
- [ ] After brief stall, picks a **new goal away** from the blocked end and wanders back.

## Door scenario

- [ ] **Single wolf**, door slammed: still gives up and wanders (PR2 regression).
- [ ] **Two wolves**, door slammed: do **not** swap or ping-pong; eventually disperse (idle pauses help break symmetry).
- [ ] Wolves do **not** memory-chase player position through a **closed** door indefinitely.

## BFS routing

- [ ] NPCs in explore follow corridors (L-junctions) rather than cutting diagonally into walls.

## Regression

- [ ] Visible chase / follow / flee / memory still greedy.
- [ ] Good–neutral corridor swap still works.
- [ ] Good–good and good–neutral swaps unchanged.
- [ ] F5 omniscient vision still works; NPC LOS unchanged.