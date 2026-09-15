# Manual checklist — PR9 (pursuit momentum)

Run: `python -m src.main`

## Memory chase

- [ ] As a good knight ally, follow the player around a corner until you lose sight; knight continues toward last seen position.
- [ ] As evil wolf, chase a stunned knight around a corner; wolf paths to last known tile after LOS breaks.

## Momentum past memory

- [ ] After reaching the last-known tile without regaining sight, the pursuer keeps moving in the last chase direction for several turns (not instant explore wander).
- [ ] When momentum hits a wall, the pursuer sidesteps instead of reversing into the tile it just left.

## Give-up

- [ ] Wolves in a crowded corridor keep trying to reach the player's last-known tile (bumps do not instantly end the chase).
- [ ] Repeated blocks (e.g. closed door, dense pack) eventually raise frustration (~8–12 failed steps) and the wolf gives up.
- [ ] Only after **standing on** the last-known tile without sight does momentum overshoot begin; after momentum ends, the wolf gives up.
- [ ] Regaining LOS on a viable target resets pursuit (normal chase resumes; visible target beats memory).

## Regression

- [ ] Neutral flee-from-evil behavior unchanged.
- [ ] PR0–PR8 behavior intact.