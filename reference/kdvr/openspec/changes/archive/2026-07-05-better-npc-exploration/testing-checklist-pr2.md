# Manual checklist — PR2 (explore frustration)

Run: `python -m src.main`

## Door growl → give up

- [ ] Drive wolf pack to a closed door after chase give-up (memory frustration finished).
- [ ] Wolves **linger at the door** for several turns (roughly 8–12 failed explore steps).
- [ ] After that band, wolves **re-pick a new wander goal** (often toward the far end of their reachable area).
- [ ] Rear wolves begin moving when space opens behind the front of the pack.

## Progress resets patience

- [ ] A wandering NPC making steady progress toward its explore goal does not constantly swap goals.

## Regression

- [ ] Memory chase frustration (PR9) still gives up independently of explore frustration.
- [ ] Visible chase / follow / flee unchanged.
- [ ] PR1 reachable goals still hold (no goals beyond closed doors).

## Neutral

- [ ] Rabbits still explore; frustration should eventually re-pick if stuck (player-adjacent fix is PR4).