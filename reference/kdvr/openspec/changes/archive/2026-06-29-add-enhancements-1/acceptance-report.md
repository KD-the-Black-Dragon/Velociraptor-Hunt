# Acceptance Report: add-enhancements-1

**Date:** 2026-06-29  
**Scope:** `openspec/specs/enhancements-1/spec.md`

## Automated verification

```bash
python -m pytest tests/ -v
```

**Last run:** 21 passed, 0 failed (2026-06-29)

| Area | Tests | Result |
|------|-------|--------|
| Core acceptance (AC1–AC10) | `test_acceptance.py` | PASS |
| Wait / turn counter | `test_enhancements_1.py` | PASS |
| Natural regen | `test_enhancements_1.py` | PASS |
| Stunned movement/wait | `test_enhancements_1.py` | PASS |
| TYUGHJBNM movement | `test_enhancements_1.py` | PASS |
| `on_player_turn_consumed` | `test_enhancements_1.py` | PASS |
| Inventory while stunned | `test_enhancements_1.py` | PASS |

## Manual verification

- [x] User playtest sign-off — all features working
- [x] Silent wait and silent regen confirmed acceptable

## Requirement coverage

| Requirement | Verified by |
|-------------|-------------|
| Pass turn | `WAIT_KEYS`, engine wait branch |
| Keyboard movement | `KEYBOARD_DIRECTION_KEYS` (Shift+TYUGHJBNM) |
| Natural recovery | `_apply_natural_regen` every 8 turns |
| Stunned movement turn | Engine stunned branch before `try_action` |
| Player turn accounting | `_consume_player_turn` |
| Turn hook | `fire_player_turn_consumed` |

## Verdict

**ENHANCEMENTS 1: ACCEPTED**