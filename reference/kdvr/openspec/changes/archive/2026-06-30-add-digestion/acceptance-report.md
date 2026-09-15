# Acceptance Report: add-digestion

**Date:** 2026-06-30  
**Scope:** `openspec/specs/digestion/spec.md` (NPC + player digestion, mercy, predator holding)

## Automated verification

```bash
python -m pytest tests/ -v
```

**Last run:** 218 passed, 0 failed (2026-06-30)

| Area | Tests | Result |
|------|-------|--------|
| Digestion (PR 1–3 + playtest fixes) | `test_digestion.py`, `test_text.py` | PASS |
| NPC vore / engulf / rescue | `test_enhancements_3.py`, `test_vore_engulfed.py` | PASS |
| Player vore / struggle | `test_vore_struggle.py`, `test_vore_ai.py` | PASS |
| Core acceptance | `test_acceptance.py` | PASS |
| Full suite | `tests/` | PASS |

## Manual verification

- [x] User playtest sign-off PRs 1–3
- [x] Playtest fixes: engulfed combat immunity, regen order, strike message
- [x] CP437 hyphen rendering in log

## Requirement coverage (highlights)

| Requirement | Verified by |
|-------------|-------------|
| `DigestionStrikes`, `DigestionStats`, `narrative_type` | `test_digestion.py` |
| NPC mercy parity | `test_digestion.py` |
| Predator attack-only | `test_digestion.py` |
| NPC digestion cadence + removal | `test_digestion.py` |
| Regen gate | `test_digestion.py` |
| Player digestion + modal + game over | `test_digestion.py` |
| Engulfed combat immunity | `test_digestion.py` |
| CP437 text | `test_text.py` |

## Spec updates

- `openspec/specs/digestion/spec.md` — new live spec
- `openspec/specs/vore/spec.md` — digestion in scope; attack-only holding; mercy NPCs
- `openspec/specs/enhancements-3/spec.md` — removal via digestion; holding behavior
- `openspec/specs/core-roguelike/spec.md` — game over via digestion
- `README.md` — digestion section

## Verdict

**DIGESTION: ACCEPTED**