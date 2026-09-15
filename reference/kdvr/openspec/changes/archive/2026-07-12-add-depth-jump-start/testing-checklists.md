# add-depth-jump-start — Combined manual testing

## Automated gate (acceptance)

```bash
python -m pytest tests/ -v -n 4
```

Change-scoped suite:

```bash
python -m pytest tests/test_depth_jump_pr1.py -v
```

---

## PR1 — Secret depth-jump new game

See `testing-checklist-pr1.md`.

- [x] Designer sign-off (*"PR1 looks good."*)