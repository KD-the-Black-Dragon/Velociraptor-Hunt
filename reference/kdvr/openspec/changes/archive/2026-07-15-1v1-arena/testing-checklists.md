# 1v1-arena — Combined manual testing

## Automated gate (acceptance)

Change-scoped suite:

```bash
python -m pytest tests/test_arena_pr1.py tests/test_arena_pr2.py -v -n 4
```

**27/27** passed (2026-07-15).

Full suite (see `acceptance-report.md` for procedure and unrelated failures).

---

## PR1 — Interactive arena (Ctrl+B)

See `testing-checklist-pr1.md`.

- [x] Designer sign-off (*"all looks good to me"*)

---

## PR2 — Headless arena bot + compare-sheet CSV

See `testing-checklist-pr2.md`.

- [x] Designer sign-off (*"all looks good to me"*)