# Acceptance Report: add-rest-until-healed-or-danger

**Date:** 2026-07-04  
**Scope:** Main keyboard **`5`** rest-until macro with danger/attack/ally-alarm stops, incremental animation, manual interrupt

## Automated verification

### Targeted gate (change tests)

```bash
python -m pytest tests/test_rest_until_healed.py tests/test_enhancements_1.py -q
```

| Area | Tests | Result |
|------|-------|--------|
| Rest mechanics + interrupts | `test_rest_until_healed.py` | PASS (16) |
| Wait/regen regression | `test_enhancements_1.py` | PASS (11) |
| **Total** | | **27 passed** |

### Full suite

Skipped per prior workflow convention (targeted gate sufficient for this change).

## Manual verification

- [x] PR0 initial playtest — rest pre-checks, stop reasons, ally alarm, numpad 5 unchanged (user sign-off)
- [x] Incremental animation — no Windows hang; HP/NPC updates visible (user sign-off)
- [x] Manual interrupt — any gameplay key cancels rest and runs normal action (user sign-off)

## Requirement coverage

| Requirement | Verified by |
|-------------|-------------|
| Key `5` rest-until | `REST_UNTIL_KEY`, `begin_rest`, spec scenarios |
| Pre-checks (red alerts) | engulfed / full HP / evil in FOV tests |
| Stop: attack (hit/miss) | `fire_player_combat_targeted`, interrupt test |
| Stop: danger / ally alarm | FOV + `_visible_good_evils` tests |
| Stop: healed / 100-turn cap | heal + cap tests |
| Incremental frames + present | `advance_rest_frame`, `main.run_loop` |
| Manual KeyDown interrupt | App `cancel_rest` + engine handler tests |
| Numpad 5 single wait | `test_numpad_five_still_single_wait` |
| Spec | `openspec/specs/enhancements-1/spec.md` |

## Delivered

Single **PR0** — full feature, docs, tests, acceptance.