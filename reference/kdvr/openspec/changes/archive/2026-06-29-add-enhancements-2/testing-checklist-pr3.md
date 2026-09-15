# PR 3 Manual Testing Checklist — Faction AI

Run `python -m src.main` from the project root.

**Note:** Good/neutral swap with the player arrives in PR 4. This PR only changes NPC AI pathing and targeting. Good and neutral NPCs are not spawned in normal play yet — rely on automated tests for their behavior.

---

## Automated gate

```bash
python -m pytest tests/test_enhancements_2.py -v
python -m pytest tests/ -q
```

All tests should pass.

---

## Evil wolves (default spawn)

- [ ] Wolves still chase and attack the player when they have line of sight
- [ ] Combat logs use *"the wolf"* (no *"monster"*, no *"Fang"* — test spawn removed)

## Regression

- [ ] Vore still triggers when a wolf reduces you to 0 HP
- [ ] **F2** weaken, wait/regen, stunned movement unchanged
- [ ] **Escape** still quits (Ctrl+Q arrives in PR 6)

**Pass criteria:** Evil wolves behave as before toward the player; faction AI tests green; no named *Fang* wolf in spawn.