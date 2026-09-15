# Tasks: Credits Page

**Status:** Accepted (2026-07-06)  
**Change folder:** `openspec/changes/add-credits-page/`

## PR1 — Credits screen module

- [x] Add `src/ui/credits_screen.py` with `credits_display_lines()`, `render_credits_screen()`, `handle_credits_event()`, `CreditsAction`
- [x] Reuse `HelpTextLine` and help color constants from `help_overlay.py` (no duplicate color types)
- [x] Curate attribution copy: K.D. roles, URLs, Source Sans 3 OFL, CP437 tile font via libtcod, pyproject deps + Python PSF
- [x] Unit tests in `tests/test_credits_screen.py` (content, `len(credits_display_lines()) == 21`, Esc→BACK, render footer, title present)
- [x] Run targeted pytest: `pytest tests/test_credits_screen.py -q`
- [x] Deliver manual checklist (`testing-checklist-pr1.md`)

## PR2 — Main menu and app integration

- [x] Extend `build_menu_options()` — append `"Credits"` before `"Exit"` (always visible)
- [x] Add `MenuAction.CREDITS`; wire `handle_main_menu_event()` and `_ALL_MENU_OPTION_LABELS`
- [x] Add `AppPhase.CREDITS`; render/handle branches in `src/app.py` (mirror `PAST_RUNS` Esc-back pattern)
- [x] Add `present_credits_frame()` in `src/ui/log_present.py` (mirror `present_help_overlay_frame()`)
- [x] Wire `App.present()` for `AppPhase.CREDITS` with proportional path when `log_font.enabled`
- [x] Extend `tests/test_main_menu.py` (Credits option order, Enter action)
- [x] Add `tests/test_credits_menu_pr2.py` (app phase transitions, Esc back)
- [x] Add `tests/test_credits_present_pr2.py` (mock: proportional branch when `log_font.enabled`, CP437 fallback otherwise)
- [x] Update `tests/test_past_runs_menu_pr4.py` and `tests/test_save_menu_pr4.py` — insert `"Credits"` before `"Exit"` in all hardcoded `build_menu_options()` tuples (audit: `grep build_menu_options tests/`)
- [x] Run targeted pytest: `pytest tests/test_credits_screen.py tests/test_main_menu.py tests/test_credits_menu_pr2.py tests/test_credits_present_pr2.py tests/test_past_runs_menu_pr4.py tests/test_save_menu_pr4.py -q`
- [x] Deliver manual checklist (`testing-checklist-pr2.md`)

## PR3 — Spec update and acceptance

- [x] Update `openspec/specs/main-menu/spec.md` — Credits requirement and scenarios; revise option-count ranges (three-to-five / four-or-five → four-to-six) in presentation requirement, title/options scenario, and acceptance criterion #1
- [x] Run full pytest suite
- [x] Write `acceptance-report.md` and consolidate `testing-checklists.md`
- [x] Archive to `openspec/changes/archive/2026-07-05-add-credits-page/` when accepted
- [x] Deliver manual checklist (`testing-checklist-pr3.md`)