# Acceptance Report: improve-text-ux

**Date:** 2026-07-09  
**Scope:** Placeholders, caution logs, dialog chrome, proportional narrative/utilitarian UI, multi-column inventory, sentence confirms, game over, progressive digestion haze (PR0–PR7).

## Automated verification

### Change-scoped

```bash
python -m pytest tests/test_text_ux_pr1.py tests/test_text_ux_pr2_caution.py tests/test_text_ux_pr3_chrome.py tests/test_text_ux_pr4_digestion_font.py tests/test_text_ux_pr5_narrative_font.py tests/test_text_ux_pr6_inventory_layout.py tests/test_text_ux_pr7_remaining.py tests/test_ui_modals.py -q
```

| Result | Detail |
|--------|--------|
| **PASS** | Change-scoped text UX + related modal tests |

### Full suite

```bash
python -m pytest tests/ -n 6 --tb=line -q
```

| Result | Count |
|--------|-------|
| Passed | 1232 |
| Failed (first run) | 4 |
| Duration | ~9m 20s |

**First-run failures (re-run only failures):**

| Test | Re-run | Notes |
|------|--------|--------|
| `test_summon_silent_when_wolf_outside_player_fov` | PASS | Flake / timing |
| `test_default_turn_p95_within_budget` | PASS | Perf budget flake |
| `test_enter_advances_attempt_phases` | PASS | Flake |
| `test_quit_confirm_centered_on_root_console` | **fixed** | Hardcoded row vs shared chrome; test updated to scan console |

After re-run + quit-confirm fix: remaining three flakes **PASS**; quit test **PASS**.

## Manual verification

Designer signed off through play:

- Digestion proportional model (font +2, width/pad)
- Inventory multi-column (content-hugging)
- Vore / examine narrative
- Sentence confirms (centering, errors, mods Proceed line)
- Game over + screen haze
- Progressive digestion-strike haze (max at 5)

## Live specs

- `openspec/specs/text-ux/spec.md` (new)
