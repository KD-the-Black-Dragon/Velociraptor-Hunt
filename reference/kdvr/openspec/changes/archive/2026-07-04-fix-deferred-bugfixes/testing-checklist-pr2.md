# Manual checklist — PR2 (message color categories)

Run: `python -m src.main`

## Default grey (routine)

- [ ] Welcome message and mundane combat (hits/misses) appear in **light grey**.
- [ ] Item pickup, door open, swap places use grey.

## Danger (red)

- [ ] Getting **stunned** logs in red.
- [ ] *"You cannot reach your pack while engulfed."* is red.
- [ ] Rest pre-check *"It's too dangerous to rest now!"* (evil visible) is red.
- [ ] Rest pre-check while **engulfed** is red.
- [ ] Wand breaks / item destroyed (if triggered) are red.

## Caution (yellow)

- [ ] Rest interrupted by **attack** shows yellow.
- [ ] Rest stopped by **danger approaches** or **ally alarm** shows yellow.
- [ ] Knockback (if observed) shows yellow.

## Positive (green)

- [ ] *"You are fully healed."* after rest ends in green.
- [ ] Recovering from stunned (*"You are no longer stunned."*) in green.
- [ ] Escaping engulfment in green.
- [ ] Potion heal message in green.

## Magical (cyan)

- [ ] Stepping on a floor rune activation message in cyan.

## Regression

- [ ] Word wrap still works (PR1).
- [ ] No debug stdout without `DEBUG_STDOUT=1` (PR0).