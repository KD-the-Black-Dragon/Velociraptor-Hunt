# Manual testing checklist — PR2 (engulfed flavor emit)

**How to run:** `python -m src.main`  
**Automated:** `python -m pytest tests/test_engulfed_flavor_pr2.py tests/test_engulfed_flavor_pr1.py tests/test_save_snapshot.py::test_round_trip_predator_prey_link -v -n 4`

## Automated (agent)

- [x] Emit / cadence / save tests — run by agent

## Happy path (needs temp content)

Stock entities have **no** `engulfed_flavor` yet. To see lines in play:

- [ ] Add a local mod (or temporary edit) giving a predator e.g. wolf:

```json
"engulfed_flavor": {
  "OV": ["The wolf's belly kneads you.", "Hot slime soaks into your clothes."]
}
```

- [ ] New Game → get **OV**-engulfed → wait/struggle so world phases run
- [ ] On the **3rd** world phase of the hold, a **bright white** flavor line appears; again on the **6th**, etc.
- [ ] Escape / free → no more flavor lines
- [ ] Predator with no / empty flavor → silence (no blank lines)

## Regression

- [ ] Engulfed struggle / digestion / alternate CV still work
- [ ] Save/load mid-engulf preserves flavor phase counter (automated covers codec)

## Out of scope this PR

- Stock entity text fills; live vore spec archive (PR3)
