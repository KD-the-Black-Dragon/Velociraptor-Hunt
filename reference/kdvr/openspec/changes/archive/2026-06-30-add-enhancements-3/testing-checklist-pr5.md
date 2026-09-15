# PR 5 Manual Testing Checklist — NPC Vore Logs and Headless Engulf

Run `python -m src.main` from the project root.

---

## Automated gate

```bash
python -m pytest tests/test_enhancements_3.py -v
python -m pytest tests/ -q
```

All tests should pass.

---

## NPC vore (log only, no modal)

Use **F2** to weaken knights/rabbits to stunned (0 HP) for easier setup.

- [ ] Stunned **knight** adjacent to **wolf** → wolf may attempt vore; **miss** logs a line (e.g. *"The wolf tries to swallow the knight but fails."*)
- [ ] Same setup on **hit** → **hit** log line (e.g. *"The wolf swallows the knight whole!"*)
- [ ] **No modal** opens for NPC vore (player vore modal unchanged when you are prey)
- [ ] Engulfed knight is **co-located** on wolf tile; knight does **not** move on its turn
- [ ] Wolf holding prey **does not chase** (predator frozen)

## Visibility

- [ ] Off-screen NPC vore attempts do **not** add message-log lines (combat still resolves)

## Regression

- [ ] Player stunned → wolf vore still opens **modal** (unchanged)
- [ ] NPC combat / swap / AI priorities from PR 3–4 unchanged
- [ ] Stunned / regen from PR 2 unchanged

**Pass criteria:** NPC vore logs on visible attempts, headless engulf on hit, no modal; player vore unchanged; pytest green.