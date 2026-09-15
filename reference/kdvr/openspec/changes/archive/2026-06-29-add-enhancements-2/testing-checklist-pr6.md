# PR 6 Manual Testing Checklist — Examine and Input

Run `python -m src.main` from the project root.

---

## Automated gate

```bash
python -m pytest tests/test_examine.py tests/test_acceptance.py::test_ac_quit_ctrl_q -v
python -m pytest tests/ -q
```

All tests should pass.

---

## Examine (normal play)

- [ ] Press **x** — cyan **X** cursor appears on your tile; you do not move; turn does not advance
- [ ] Arrow keys move the cursor only (player stays put)
- [ ] Move cursor onto a wolf, press **Enter** — centered description modal (vicious/ferocious text)
- [ ] Description does **not** appear in the bottom message log
- [ ] Press **Escape** — back to cursor; press **Escape** again — examine ends, normal play
- [ ] **x** on empty floor + **Enter** — *"There is nothing of interest here."* in modal

## Engulfed

- [ ] While engulfed, **x** logs *"You can't see anything!"* — no examine mode, no turn cost

## Quit and cancel

- [ ] **Ctrl+Q** quits from normal gameplay
- [ ] **Ctrl+Q** quits while examine cursor or description modal is open
- [ ] **Escape** alone does **not** quit (during gameplay or examine)
- [ ] During vore modal, **Escape** does nothing; **Ctrl+Q** still quits

## Regression

- [ ] Movement, combat, vore, swap (evil only), **F2**, wait/regen unchanged
- [ ] **R** / **S** debug keys still work outside modals

**Pass criteria:** Free examine works; engulfed block; Ctrl+Q quits; Escape cancels examine only; pytest green.