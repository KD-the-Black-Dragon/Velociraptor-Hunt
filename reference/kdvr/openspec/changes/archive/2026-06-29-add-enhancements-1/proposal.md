# Proposal: Enhancements 1

## Why

Core v1 works but has three friction points: no way to pass time, no passive recovery, and stunned movement is a silent no-op that soft-locks players without potions. The on-hold vore module deferred full stunned pass-turn behavior; this change ships the **movement and recovery slice** now.

Vore (`openspec/changes/add-vore-mechanics/`) remains on hold. Its design is preserved.

## What Changes

- **Wait/pass turn** via **`H`**, numpad **5**, and **period** (stunned wait uses tired message)
- **`TYUGHJBNM`** keyboard movement (`H` = wait in layout)
- **Natural regen**: 1 HP every 8 player turns; *"You are no longer stunned."* on regen wake
- **Stunned movement** logs *"You're too tired to move."* and consumes a turn
- Central **`_consume_player_turn()`** helper with turn counter
- **`on_player_turn_consumed`** event hook (per-turn extension point for vore timers, etc.)

## Capabilities

### New Capabilities

- `enhancements-1`: Wait, regen, stunned turn pass, turn accounting.

### Modified Capabilities

- `core-roguelike`: Pointer update for stunned movement scenario (movement now passes time via engine; inventory while stunned unchanged).

## Impact

- `src/engine.py`, `src/input_handlers.py`, `src/messages.py`, `src/constants.py`, `src/events.py`
- `tests/test_enhancements_1.py` (new)
- `README.md`

## Success Criteria

All scenarios in `openspec/specs/enhancements-1/spec.md` pass. Core acceptance tests remain green.

## Design Reference

[`design.md`](design.md) — approved 2026-06-29.