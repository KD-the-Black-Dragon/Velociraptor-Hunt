# Manual testing — PR3 (help + acceptance)

**How to run:** `python -m src.main`

## Help
- [ ] **F1** / **?** help lists `1 - shout "Come here!" (good allies in view)`

## Regression (quick)
- [ ] **`1`** still summons good allies; tag clears; cooldown **4** turns
- [ ] Engulfed fizzle still works
- [ ] Numpad 1 still moves SW

## Automated
```bash
python -m pytest tests/test_come_here_pr1.py tests/test_come_here_pr2.py tests/test_help_overlay.py -v
python -m pytest tests/ -n 6 --tb=line -q
```
