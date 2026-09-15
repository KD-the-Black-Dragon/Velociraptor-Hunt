# convenience-controls — Combined manual testing

## Automated gate (acceptance)

Change-scoped suite:

```bash
python -m pytest tests/test_autoexplore.py tests/test_force_attack.py tests/test_rest_until_healed.py -v -n 4
```

**35/35** passed (2026-07-15).

See `acceptance-report.md` for full-suite procedure.

---

## PR1 — Autoexplore + shared infrastructure

See `testing-checklist-pr1.md`.

- [x] Designer sign-off (PR1 acceptable after animation/diagonal iteration)

---

## PR2 — Force-attack

See `testing-checklist-pr2.md`.

- [x] Designer sign-off (*"Looks good. PR2 is signed off."*)