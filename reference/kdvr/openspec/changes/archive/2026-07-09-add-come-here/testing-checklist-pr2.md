# Manual testing — PR2 (Come here! AI)

**How to run:** `python -m src.main`

## Happy path
- [ ] Find a knight, walk away a few tiles (still in FOV), press **`1`**
- [ ] Knight should path toward you (not chase wolves unless they block the way)
- [ ] When knight becomes adjacent, they resume normal AI (may peel off to fight evil)
- [ ] Cooldown is **4** turns (hoarse message until then)

## Frustration
- [ ] Narrow hallway: knight, wolf between knight and you, press **`1`**
- [ ] Knight attacks the blocking wolf (progress toward you), not ignored forever

## Edge cases
- [ ] Shout then walk out of knight LOS — knight uses last-known pursuit, may give up and drop order
- [ ] Lake standoff: knight staring at wolf across water → **`1`** should pull them toward you
- [ ] Descend stairs with a following ally — come-here flag cleared on floor change
- [ ] Engulfed still fizzles (PR1)

## Automated
```bash
python -m pytest tests/test_come_here_pr1.py tests/test_come_here_pr2.py -v
```
