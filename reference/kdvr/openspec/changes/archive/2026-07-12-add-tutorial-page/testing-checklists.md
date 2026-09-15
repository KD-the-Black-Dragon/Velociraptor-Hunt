# add-tutorial-page — Combined manual testing

## Automated gate (acceptance)

```bash
python -m pytest tests/ -v -n 4
```

Change-scoped onboarding suite:

```bash
python -m pytest tests/test_onboarding_pr1.py -v
```

---

## PR1 — First-run onboarding

See `testing-checklist-pr1.md`.

- [x] Designer sign-off (tutorial copy, vore prefs spacing, all-set screen)