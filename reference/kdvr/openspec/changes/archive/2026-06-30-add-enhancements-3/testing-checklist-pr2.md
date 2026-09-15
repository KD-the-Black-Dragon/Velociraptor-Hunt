# PR 2 Manual Testing Checklist — NPC Stunned and Regen

Run `python -m src.main` from the project root. Press **F2** to weaken all monsters for easier testing.

---

## Automated gate

```bash
python -m pytest tests/test_enhancements_3.py -v
python -m pytest tests/ -q
```

All tests should pass.

---

## Good/neutral stunned

- [ ] Weaken a knight (`F2`), let a wolf hit it to 0 HP
- [ ] Knight **remains on the map** at 0 HP (not removed)
- [ ] Log shows *"The knight is stunned!"* (or proper name if set)
- [ ] Stunned knight **does not move** on subsequent turns
- [ ] Repeat with a rabbit if convenient

## Evil defeated (unchanged)

- [ ] Weaken a wolf, attack it to 0 HP
- [ ] Wolf is **removed** from the map
- [ ] Log shows *"The wolf was defeated."* (not stunned)

## NPC regen

- [ ] After **8 player turns** (wait with numpad 5), a damaged knight gains +1 HP
- [ ] Stunned knight at 0 HP: after 8 waits, gains 1 HP and log *"The knight is no longer stunned."*
- [ ] Damaged wolf regains +1 HP only after **12 player turns** (slower than knight)

## Regression

- [ ] Player regen still every 8 turns
- [ ] Player stunned/recovery unchanged
- [ ] Wolves still chase and attack

**Pass criteria:** Good/neutral stunned at 0 HP; evil defeated; regen cadences match spec; pytest green.