# Proposal: Rest Until Healed or Danger

## Why

Waiting one turn at a time (**Shift+H**, numpad **5**, **`.``) is tedious when the player wants to recover HP via natural regen (1 HP every 8 turns) in a safe area. Enhancements 1 deferred a **rest-until** macro; the todo backlog specifies the behavior, messages, and key binding.

Players need a single action that passes turns automatically until healed, a threat appears, they are attacked, or a safety cap is reached.

## What Changes

- Add **`5`** (main keyboard digit, **not** numpad **5**) to start **rest until** — repeated wait turns with automatic stop conditions.
- **Pre-checks** (no turn consumed): engulfed, evil in player FOV, already at full HP — each logs the specified message and is a no-op.
- **Stop conditions** (after at least one rest turn): player reaches full HP, any evil enters player FOV, player HP decreases, or **100** rest turns elapse — log the matching end reason.
- Reuse existing wait/regen/world-phase pipeline (`_consume_player_turn`) per rest iteration.
- Extend **`openspec/specs/enhancements-1/spec.md`** with rest requirements and scenarios.
- Update **`README.md`** controls section.

## Out of Scope

- Rest while engulfed (explicit no-op).
- Changing natural regen cadence or amount.
- Rest key rebinding / options UI.
- Animating or summarizing intermediate rest turns in the log (individual waits stay silent unless stunned rules apply — see design open questions).
- AI or map changes to make resting “safer” beyond existing FOV/danger checks.

## Capabilities

### Modified

- **`enhancements-1`** — new rest-until requirement; controls table gains **`5`**.

## Impact (anticipated)

| Area | Files |
|------|--------|
| Input | `src/input_handlers.py` — `REST_UNTIL_KEY` |
| Rest logic | `src/systems/rest.py` (new) or `src/engine.py` |
| Messages | `src/messages.py` |
| Engine | `src/engine.py` — key handler + loop |
| Visibility helper | Reuse `_player_has_visible_evil` from `src/systems/ally_introduction.py` (extract/share if needed) |
| Tests | `tests/test_rest_until_healed.py` (new) |
| Docs | `README.md`, `openspec/specs/enhancements-1/spec.md` |
| Backlog | Remove item from `openspec/changes/todo/spec.md` |

## Success Criteria

- All scenarios in updated `enhancements-1/spec.md` pass via targeted tests.
- Manual checklist: safe rest heals; evil sight / damage / cap / pre-checks behave per spec.
- Numpad **5** remains single-turn wait only.
- Item removed from todo backlog.

## Design

`openspec/changes/add-rest-until-healed-or-danger/design.md`