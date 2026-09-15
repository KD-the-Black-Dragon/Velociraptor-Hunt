# Manual checklist — PR3 (registry cache + profile gates)

Run: `python -m src.main`

PR3 is infrastructure only — behavior should match PR2.

## Regression (same as PR2)

- [ ] Move 20+ turns on a normal floor — still responsive
- [ ] Wolf corner chase (memory pursuit) still works
- [ ] Wolf dispersal after chase give-up (near closed door)
- [ ] Good ally introductions when adjacent

## Automated gate (optional local check)

```bash
python -m pytest tests/test_performance_regression.py -v
```