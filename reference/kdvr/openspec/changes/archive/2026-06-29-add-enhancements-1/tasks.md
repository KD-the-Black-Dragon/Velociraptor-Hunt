# Tasks: Enhancements 1

## PR 1: Turn infrastructure

- [x] Add `player_turn_count` to `GameEngine`; reset in `new_game()`
- [x] Add `_consume_player_turn()` (increment only in PR1; regen in PR3)
- [x] Refactor movement and inventory paths to use helper
- [x] Add `tests/test_enhancements_1.py` with `_press()` harness
- [x] Add `test_new_game_resets_turn_counter`

## PR 2: Wait + TYUGHJBNM movement

- [x] Add `WAIT_KEYS` (`KP_5`, `PERIOD`, `h`)
- [x] Add `KEYBOARD_DIRECTION_KEYS` (TYUGHJBNM) merged into `DIRECTION_KEYS`
- [x] Wait: *"You wait."* conscious; *"You're too tired to move."* stunned
- [x] Tests: wait, stunned wait, keyboard move, 8-dir coverage

## PR 3: Natural regen

- [x] Add regen constants; `_apply_natural_regen()` in `_consume_player_turn()`
- [x] *"You recover 1 HP naturally."*; *"You are no longer stunned."* on wake
- [x] Tests: 8-turn heal, max HP silent, stunned wake message

## PR 4: Stunned movement + hook + spec

- [x] Stunned direction keys → tired message → `_consume_player_turn()`
- [x] `on_player_turn_consumed` in `events.py`
- [x] Update core spec stunned-movement pointer + glossary
- [x] Update `README.md` (TYUGHJBNM layout, wait keys)
- [x] Tests: stunned movement, inventory unchanged while stunned

## Deferred (UX #12)

- [ ] Rest-until-healed macro (`Z`) — future change