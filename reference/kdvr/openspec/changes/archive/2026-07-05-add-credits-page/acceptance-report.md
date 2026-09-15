# Acceptance Report: add-credits-page

**Date:** 2026-07-06  
**Scope:** Main-menu Credits option, credits screen module, proportional presentation (PR1–PR3). Mid-stream copy: **K.D. — Curator of Voracious Beasts**; FurAffinity link `furaffinity.net/user/kd`.

## Automated verification

### Change gate (credits)

```bash
python -m pytest tests/test_credits_screen.py tests/test_main_menu.py tests/test_credits_menu_pr2.py tests/test_credits_present_pr2.py tests/test_past_runs_menu_pr4.py tests/test_save_menu_pr4.py -q
```

| Result | Count |
|--------|-------|
| **PASS** | **59** |

### Full suite

```bash
python -m pytest -q --tb=no
```

| Result | Count |
|--------|-------|
| Passed | 953 |
| Failed | 5 |
| Warnings | 110 |
| Duration | ~25m 38s |

**Failures (not introduced by this change):**

- `tests/test_ally_rescue_priority.py::test_good_ignores_predator_without_los`
- `tests/test_dungeon_pr3.py::test_followers_reduce_fresh_knight_spawns`
- `tests/test_dungeon_spawn_config.py::test_load_default_dungeon_spawn_json`
- `tests/test_npc_data_pr1.py::test_load_default_entities_json`
- `tests/test_vore_engulfed.py::test_roaming_wolf_wanders_while_player_engulfed`

No failures in the credits change gate.

## Manual verification

- [x] PR1 module sign-off (user)
- [x] PR2 menu integration sign-off (user)
- [x] Copy tweaks: Curator of Voracious Beasts; `furaffinity.net/user/kd` (user)
- [x] PR3 acceptance sign-off (user)

## Requirement coverage

| PR | Delivered |
|----|-----------|
| PR1 | `src/ui/credits_screen.py`; static content; Esc→BACK; unit tests |
| PR2 | Menu option above Exit; `AppPhase.CREDITS`; `present_credits_frame()`; integration tests |
| PR3 | Live `main-menu` spec; acceptance; archive |

## Spec updates

- `openspec/specs/main-menu/spec.md` — Credits requirement; four-to-six option range; Curator copy and FurAffinity URL

## Files touched (summary)

| Area | Path |
|------|------|
| Credits UI | `src/ui/credits_screen.py` |
| Menu | `src/menu.py` |
| App flow | `src/app.py` |
| Present | `src/ui/log_present.py` |
| Tests | `tests/test_credits_screen.py`, `test_credits_menu_pr2.py`, `test_credits_present_pr2.py`, `test_main_menu.py`, `test_past_runs_menu_pr4.py`, `test_save_menu_pr4.py` |