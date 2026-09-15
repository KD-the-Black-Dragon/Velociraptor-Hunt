# Manual checklist — Dungeon Enhancement PR 1

Run: `python -m src.main`

PR 1 does **not** add water or stairs to generated maps yet (PR 2). This checklist verifies mobility/render plumbing via automated tests; manual play confirms no regressions.

## Automated gate

```bash
python -m pytest tests/test_dungeon_pr1.py tests/ -q
```

## Regression (manual)

- [ ] New Game still produces a playable dungeon
- [ ] Movement, combat, vore, digestion, menu flow unchanged
- [ ] FOV and explored tiles behave as before
- [ ] Debug keys **R**, **F2**, **S** still work

## PR 2 preview (not this PR)

- [ ] Water `~` and stairs `>` appear on generated floors *(PR 2)*