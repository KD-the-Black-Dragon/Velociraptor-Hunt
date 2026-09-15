# Acceptance Report: add-vore-mechanics

**Date:** 2026-06-29  
**Scope:** `openspec/specs/vore/spec.md` (v1 vore domain)

## Automated verification

```bash
python -m pytest tests/ -v
```

**Last run:** 96 passed, 0 failed (2026-06-29)

| Area | Tests | Result |
|------|-------|--------|
| Core acceptance (AC1–AC8) | `test_acceptance.py` | PASS |
| Import boundary | `test_core_systems_no_vore_import` | PASS |
| Vore smoke | `test_vore_smoke_engulf_struggle_escape` | PASS |
| Vore constants / F2 | `test_vore_constants.py` | PASS |
| Vore AI / modal / turns | `test_vore_ai.py`, `test_vore_modal.py`, `test_vore_turn_order.py` | PASS |
| Engulfed state | `test_vore_engulfed.py` | PASS |
| Struggle / mercy | `test_vore_struggle.py` | PASS |
| Blindness / overlay | `test_vore_render.py` | PASS |
| Enhancements 1 | `test_enhancements_1.py` | PASS |

## Manual verification

- [x] User playtest sign-off across PRs 1–7
- [x] Ad-hoc features verified: struggle messages, 0 HP struggle block, mercy invincibility, `#` overlay

## Requirement coverage (highlights)

| Requirement | Verified by |
|-------------|-------------|
| Narrative types / filtering | `test_vore_constants.py` |
| Multi-phase modal | `test_vore_modal.py` |
| Vore eligibility / AI | `test_vore_ai.py` |
| Hit/miss resolution | `test_vore_ai.py`, `test_vore_turn_order.py` |
| Engulfed co-tile / immunity | `test_vore_engulfed.py` |
| Struggle / escape / mercy | `test_vore_struggle.py` |
| Blindness / HUD / overlay | `test_vore_render.py` |
| Modular boundary | `test_ac8_no_top_level_vore_package`, `test_core_systems_no_vore_import` |

## Post-plan additions (documented in spec)

- Random struggle log lines (`pick_struggle_message`)
- No struggle at 0 HP while engulfed
- `VoreMercy` post-escape invincibility (one world phase)
- Dark-red `#` decorative ring while blind

## Verdict

**VORE MECHANICS V1: ACCEPTED**