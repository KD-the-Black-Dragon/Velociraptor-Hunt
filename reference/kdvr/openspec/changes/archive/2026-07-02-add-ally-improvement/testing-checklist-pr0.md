# Manual checklist — PR0 (ally data layer)

Run: `python -m src.main`

## Boot / regression

- [ ] Game boots with no errors
- [ ] No behavior change — knights still spawn without runtime names
- [ ] Existing knight rescue, good AI chase, and combat logs unchanged

## Data (optional spot-check in REPL or data tests)

- [ ] `data/names.json` loads with knight name pool
- [ ] `data/rescue_gratitude.json` loads with gratitude lines
- [ ] `data/entities.json` knight entry has `introduction` array

## Automated

- [ ] `pytest tests/test_ally_improvement_data.py` green