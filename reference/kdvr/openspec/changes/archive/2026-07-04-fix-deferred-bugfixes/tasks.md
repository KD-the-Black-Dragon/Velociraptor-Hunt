# Tasks: Deferred Bugfixes (UI + AI)

## PR0 — Debug stdout env gate

- [x] Add `src/debug_log.py` helper (`debug_stdout_enabled()` from env)
- [x] Gate prints in `ai.py`, `map_gen.py`, `engine.py`, `floor_prefetch.py`
- [x] Update tests that expect stdout to set env or patch helper
- [x] Run targeted pytest for PR0
- [x] Deliver manual checklist (`testing-checklist-pr0.md`)

## PR1 — Message log word wrap

- [x] Wrap log entries to region width in render path
- [x] Preserve per-entry color on wrapped sub-lines
- [x] Add `tests/test_message_log_wrap.py`
- [x] Run targeted pytest for PR1
- [x] Deliver manual checklist (`testing-checklist-pr1.md`)

## PR2 — Message color categories

- [x] Add `MessageCategory` enum + six RGB constants
- [x] Change `MessageLog.add` to accept `category=`
- [x] Migrate all `message_log.add` call sites to categories
- [x] Align rest messages with danger/caution/positive scheme; update `enhancements-1` spec notes
- [x] Add category tests
- [x] Run targeted pytest for PR2
- [x] Deliver manual checklist (`testing-checklist-pr2.md`)

## PR3 — Per-word JSON colors (experimental)

- [x] Design minimal markup + parser for narrative JSON
- [x] Rich render for log rows (multi-fg segments) OR document revert
- [x] Add opt-in sample line in data for manual verification (`introduction_log_category` on knight)
- [x] Run targeted pytest for PR3
- [x] Deliver manual checklist (`testing-checklist-pr3.md`)

## PR4 — Proportional log font

- [x] Bundle narrow monospace TTF under `data/fonts/`
- [x] Render message log region with TTF; map/sidebar unchanged
- [x] Document fallback if font load fails
- [x] Run targeted pytest for PR4
- [x] Deliver manual checklist (`testing-checklist-pr4.md`)

## PR5 — Full log overlay (Ctrl+P)

- [x] Raise `MESSAGE_LOG_CAPACITY` to 100
- [x] Add `LogOverlayState` + render/input in engine/app
- [x] Scroll: line (arrows/TYUGHJBNM/numpad), page (PgUp/PgDn), Esc close
- [x] Available during modals and rest animation
- [x] Add tests for overlay state + scroll math
- [x] Update `README.md` and `ui-layout` spec
- [x] Run targeted pytest for PR5
- [x] Deliver manual checklist (`testing-checklist-pr5.md`)

## PR6 — Help overlay (F1, ?)

- [x] Add `HelpOverlayState` + static help content (incl. rest `5`, Ctrl+P)
- [x] Bind F1 and Shift+/ (`?`); Esc dismiss
- [x] Exclude debug keys from content
- [x] Update `README.md`
- [x] Run targeted pytest for PR6
- [x] Deliver manual checklist (`testing-checklist-pr6.md`)

## PR7 — Rune effects (status corner)

- [x] Build `extra_rows` from `PlayerProgression` (HP + combat buffs row)
- [x] Update `openspec/specs/floor-runes/spec.md`
- [x] Add tests for row formatting
- [x] Run targeted pytest for PR7
- [x] Deliver manual checklist (`testing-checklist-pr7.md`)

## PR8 — Narrative capitalization

- [x] Add `enforce_sentence_capitalization` in `src/text.py`
- [x] Apply to `{predator}`/`{prey}` template formatters only
- [x] Add unit tests (start, `.?!`, no dash rule)
- [x] Run targeted pytest for PR8
- [x] Deliver manual checklist (`testing-checklist-pr8.md`)

## PR9 — Pursuit momentum

- [x] Extend `AIState` with momentum / blind-turn fields
- [x] Implement reach → momentum → give-up for Good and Evil chase
- [x] Add AI tests for corner pursuit behavior
- [x] Run targeted pytest for PR9
- [x] Deliver manual checklist (`testing-checklist-pr9.md`)

## PR10 — Neutral explore anti-stuck

- [x] Track `recent_positions` on `AIState`
- [x] Clear explore goal + repick on oscillation; hold when boxed
- [x] Add regression test for corner ping-pong
- [x] Run targeted pytest for PR10
- [x] Deliver manual checklist (`testing-checklist-pr10.md`)

## PR11 — Good–neutral corridor swap

- [x] Allow swappable-bump tiles in good chase direction selection
- [x] Verify `try_action` swap on AI step into neutral
- [x] Add corridor follow test (knight past rabbit)
- [x] Run targeted pytest for PR11
- [x] Deliver manual checklist (`testing-checklist-pr11.md`)

## Acceptance (after PR11 sign-off)

- [x] Write `acceptance-report.md` and `testing-checklists.md`
- [x] Run full pytest suite
- [x] Remove completed items from `openspec/changes/todo/spec.md` (Performance item stays)
- [x] Archive to `openspec/changes/archive/YYYY-MM-DD-fix-deferred-bugfixes/`
- [x] Update `openspec/WORKFLOW.md` active change pointer to *(none)*