# Manual testing checklist — PR2 (piece runes) + Past Runs order fix

Run: `python -m src.main`

Stock runes still use `pieces_per_bonus: 1` → **feel should match pre-PR2** (every rune grants full bonus immediately).

## Past Runs order (PR1b fix)

- [ ] Complete a run (any difficulty)
- [ ] Past Runs stats line is **`{Difficulty} - Depth N - …`** (e.g. `Nightmare - Depth 1 - …`)

## Piece runes (stock defaults)

- [ ] Step on vitality / warding / striking runes — full bonuses apply at once
- [ ] Log still shows e.g. `+1 AC` / `+3 max HP` for stock runes
- [ ] Status corner shows completed bonuses (HP / Acc / Dam / AC) when non-zero
- [ ] Bonuses persist after descend / save-load

## Optional piece threshold (JSON edit then revert)

- [ ] Set warding `pieces_per_bonus: 4` in `data/floor_runes.json`
- [ ] First three wardings: no AC gain; log shows `n/4`; status may show `AC n/4`
- [ ] Fourth: `+1 AC`; combat AC increases
- [ ] Revert JSON to default `1` (or omit field)

## Separable damage (optional)

- [ ] Striking rune (`accuracy: 0`, damage +1/+1) only progresses damage, not Acc bank

## Regression

- [ ] Difficulty Options still work
- [ ] Combat / vore / dig unchanged aside from rune progression

## Automated

- [x] `python -m pytest tests/test_floor_runes_pieces_pr2.py tests/test_floor_runes_pr4.py tests/test_balance_pr1b.py -v`
