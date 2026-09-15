# Manual checklist — PR1 (name introductions)

Run: `python -m src.main`

## Introduction (happy path)

- [ ] Walk adjacent to a knight with no wolves visible → introduction line appears in message log
- [ ] Subsequent logs use the knight's proper name (e.g. "Sir Aldric") instead of "the knight"
- [ ] Introduction happens only once per knight per run

## Gating

- [ ] Knight adjacent but wolf visible to player or knight → no introduction
- [ ] Stunned knight adjacent → no introduction
- [ ] Knight not adjacent → no introduction
- [ ] While player is engulfed, adjacent knight does **not** introduce (even if coast is clear)

## Regression

- [ ] Good AI follow/chase still works
- [ ] PR0 data still loads; game boots

## Automated

- [ ] `pytest tests/test_ally_introduction.py` green