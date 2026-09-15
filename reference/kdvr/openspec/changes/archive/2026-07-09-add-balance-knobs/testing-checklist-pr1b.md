# Manual testing checklist — PR1b (difficulty Options + Past Runs)

Run: `python -m src.main`

Stock profiles still have zero depth curves and no economy overrides — **feel should match Normal stock** for all difficulties until PR5.

## Happy path

- [ ] Options → Difficulty cycles Easy ► Normal ► Hard ► Nightmare (Left/Right)
- [ ] Setting persists after leaving Options / restarting app
- [ ] New Game with Hard selected; play a short run; get game over
- [ ] Past Runs shows difficulty **before** depth (e.g. `Hard - Depth N - …`)
- [ ] No difficulty shown on status corner / in-run HUD

## Economy wiring (optional if you edit JSON)

- [ ] Temporarily set Hard `density_multiplier: 2.0` — more NPCs (then revert)
- [ ] Temporarily set Hard `runes_per_floor_override: 1` — fewer runes (then revert)
- [ ] Temporarily set Hard `rune_pieces_multiplier: 2` — two wardings needed for +1 AC (then revert)

## Save / load

- [ ] Save mid-run; Load Game resumes (difficulty snapshot preserved)
- [ ] Descend floors still works after load

## Regression

- [ ] Mods menu still opens from Options
- [ ] Floor runes / combat / vore unchanged on Normal
- [ ] Legacy Past Runs entries without difficulty still display

## Automated

- [x] `python -m pytest tests/test_balance_pr1b.py tests/test_depth_scaling_pr1.py tests/test_options_*.py tests/test_mods_menu.py -n 6` (green)
