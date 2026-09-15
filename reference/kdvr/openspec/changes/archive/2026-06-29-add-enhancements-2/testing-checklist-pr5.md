# PR 5 Manual Testing Checklist — Vore Integration

Run `python -m src.main` from the project root.

---

## Automated gate

```bash
python -m pytest tests/test_enhancements_2.py tests/test_vore_ai.py -v
python -m pytest tests/ -q
```

All tests should pass.

---

## Evil wolves (normal play)

- [ ] **F2** weaken a wolf, let it reduce you to 0 HP — vore modal still opens
- [ ] Dismiss a missed vore attempt — log says *"You evaded the wolf's vore attempt."* (not *"the Fang"* unless you add a proper name in a test spawn)
- [ ] Escape from engulf — log says *"You escape from the wolf."* (or proper name without *"the"*)

## Named wolf (optional dev test)

If you assign `ProperName("Fang")` to a wolf in a shell, vore **log** lines should use *Fang* / *Fang's* without *"the Fang"* (modal narrative text is unchanged).

## Regression

- [ ] Bump combat still uses *"the wolf"* for unnamed wolves
- [ ] Good/neutral swap (PR 4) and faction AI (PR 3) unchanged
- [ ] **Escape** still quits (Ctrl+Q arrives in PR 6)

**Pass criteria:** Evil wolves vore as before; log naming correct for proper names; pytest green.