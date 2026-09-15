# Manual checklist — PR3 (player rescue gratitude + spec)

Run: `python -m src.main`

## Gratitude (player rescuer)

- [ ] Defeat wolf holding knight as **player** (bump attack) → two log lines: freed message + gratitude
- [ ] Defeat holding wolf with **wand** → same two lines
- [ ] Gratitude uses knight's proper name if introduced earlier

## No gratitude

- [ ] Knight defeats wolf holding another knight → freed line only (no gratitude)
- [ ] Player defeats wolf holding **rabbit** (neutral) → freed line only

## Regression

- [ ] PR1 introductions and PR2 rescue priority still work
- [ ] On-screen/off-screen vore and combat logs unchanged

## Automated

- [ ] `pytest tests/test_ally_rescue_gratitude.py` green
- [ ] Full suite `pytest tests/` green (acceptance PR)