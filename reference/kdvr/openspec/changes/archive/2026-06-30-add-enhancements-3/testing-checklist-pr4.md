# PR 4 Manual Testing Checklist — NPC Alignment Swap

Run `python -m src.main` from the project root.

---

## Automated gate

```bash
python -m pytest tests/test_enhancements_3.py -v
python -m pytest tests/ -q
```

All tests should pass.

---

## Same-alignment swap (no message log)

Use **F2** to weaken NPCs if you want safer corridor tests.

- [ ] Two **knights** bump in a corridor → they **swap** tiles, no damage
- [ ] **Knight** bumps **rabbit** → swap, no damage
- [ ] Two **wolves** bump → swap, no damage
- [ ] Swapped NPC does **not** act again that world phase

## Cross-alignment (combat)

- [ ] **Wolf** bumps **knight** → **attack** (damage log), no swap
- [ ] **Knight** bumps **wolf** → attack, no swap

## Player rules (unchanged)

- [ ] Player bumps **knight/rabbit** → player swap message, positions exchange
- [ ] Player bumps **wolf** → attack
- [ ] **Knight** moving onto player tile → no swap, no message-log line

## Regression

- [ ] AI priorities from PR 3 unchanged
- [ ] Stunned/regen from PR 2 unchanged

**Pass criteria:** Same-alignment NPCs pass through each other; cross-alignment fights; player swap rules intact; pytest green.