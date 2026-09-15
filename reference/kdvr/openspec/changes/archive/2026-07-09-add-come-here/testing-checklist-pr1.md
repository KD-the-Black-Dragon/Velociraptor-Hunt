# Manual testing — PR1 (Come here! plumbing)

**How to run:** `python -m src.main`

PR1 only sets flags and messages. Allies will **not** path to you yet (PR2).

## Happy path
- [ ] In game with a knight visible → press main keyboard **`1`** (not numpad)
- [ ] Log: *You shout, "Come here!"*
- [ ] Turn advances (message log / world ticks)
- [ ] Press **`1`** again immediately → *You'll go hoarse if you shout too much.* and **no** turn spent
- [ ] Wait 4+ turns → **`1`** works again

## Edge cases
- [ ] No ally in FOV → still shout + turn (no crash)
- [ ] Numpad **1** still moves southwest (does not shout)
- [ ] While engulfed → *You shout, but you're not sure anyone heard you.* + turn; no special ally behavior yet
- [ ] Inventory / other modal open → **`1`** does not shout

## Automated
```bash
python -m pytest tests/test_come_here_pr1.py -v
```
