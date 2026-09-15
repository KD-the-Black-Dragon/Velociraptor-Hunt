# Manual testing checklist — PR3 (`runes_per_floor` in data)

Run: `python -m src.main`

Stock `data/floor_runes.json` has `"runes_per_floor": 3` → **same as before**.

## Happy path

- [ ] New game: exactly **3** floor runes (glyph `0`) on depth 1
- [ ] Descend: new floor also has 3 runes
- [ ] Step-on still activates; pieces / difficulty still work

## Optional JSON tweak (then revert)

- [ ] Set `"runes_per_floor": 1` → floors spawn 1 rune; game still loads
- [ ] Set `"runes_per_floor": 0` → no runes; floors still generate
- [ ] Restore `"runes_per_floor": 3`

## Regression

- [ ] Floor gen does not soft-lock
- [ ] Difficulty Options + Past Runs still fine

## Automated

- [x] `python -m pytest tests/test_runes_per_floor_pr3.py tests/test_floor_runes_pr4.py -v`
