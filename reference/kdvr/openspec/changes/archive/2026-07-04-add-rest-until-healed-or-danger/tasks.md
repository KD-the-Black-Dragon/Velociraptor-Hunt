# Tasks: Rest Until Healed or Danger

## PR0 — Rest until healed or danger

- [x] Add `REST_UNTIL_KEY` (`KeySym.N5`) to `input_handlers.py`
- [x] Extract/share `player_has_visible_evil` for rest + ally introduction
- [x] Add `src/systems/rest.py` with pre-checks, loop, ally alarm, end-reason priority
- [x] Add rest messages to `src/messages.py`
- [x] Wire `N5` handler in `engine.py`
- [x] Incremental rest animation + manual interrupt
- [x] Add `tests/test_rest_until_healed.py`
- [x] Update `openspec/specs/enhancements-1/spec.md`
- [x] Update `README.md` controls
- [x] Remove item from `openspec/changes/todo/spec.md`
- [x] Run targeted pytest for PR0
- [x] Deliver manual checklist (`testing-checklist-pr0.md`) to user; playtest sign-off

## Acceptance (after PR0 sign-off)

- [x] Write `acceptance-report.md`
- [x] Archive to `openspec/changes/archive/2026-07-04-add-rest-until-healed-or-danger/`
- [x] Update `openspec/WORKFLOW.md` active change pointer to *(none)*