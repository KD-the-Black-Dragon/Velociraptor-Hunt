# Digestion — Manual Testing Checklist

Run `python -m src.main` from the project root.

## Automated gate

```bash
python -m pytest tests/test_digestion.py -v
python -m pytest tests/ -q
```

All tests should pass.

---

## PR 1 — Foundation

- [ ] Wolf holding prey does **not move** on its turn
- [ ] Holding wolf **can** bump-attack an adjacent knight
- [ ] Holding wolf does **not** attempt vore on a second adjacent prey
- [ ] Defeat holding wolf → freed prey has mercy; no re-engulf or damage same phase

## PR 2 — NPC digestion

- [ ] Wolf engulfs stunned knight; prey loses 3 HP per world phase until 0
- [ ] At 0 HP: strikes accumulate (no HP + strike same tick)
- [ ] After 3 strikes: knight **removed**; OV/CV/AV completion log when visible
- [ ] Good plea ~10% with LOS; neutral silent on ticks
- [ ] Prey with 1+ strikes does not natural-regen; potions still heal
- [ ] Freed wolf acts normally **next** player turn after digest

## PR 3 — Player digestion

- [ ] Engulfed: HP drops 3/turn until 0; then strikes per consumed turn
- [ ] Each strike logs **"You are being digested!!"** (not on HP-only ticks)
- [ ] Other wolves cannot damage you while engulfed
- [ ] No spurious *"You are no longer stunned."* from regen while engulfed
- [ ] Third strike → digestion modal (not in scroll log)
- [ ] Enter → game over (`Player`, score, `Digested by wolf`); Enter exits

## Regression

- [ ] Player vore modal, struggle, escape, mercy
- [ ] NPC rescue, predator dark-red tile, FOV-gated logs
- [ ] Log hyphens render (CP437 safe)
- [ ] F2, faction AI, stunned good/neutral at 0 HP