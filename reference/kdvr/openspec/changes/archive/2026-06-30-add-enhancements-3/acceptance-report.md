# Acceptance Report: add-enhancements-3

**Date:** 2026-06-30  
**Scope:** `openspec/specs/enhancements-3/spec.md` (faction NPCs, AI, stunned/regen, NPC swap, NPC vore, rescue)

## Automated verification

```bash
python -m pytest tests/ -v
```

**Last run:** 190 passed, 0 failed (2026-06-30)

| Area | Tests | Result |
|------|-------|--------|
| Enhancements 3 (spawn, AI, swap, vore, rescue) | `test_enhancements_3.py` | PASS |
| Predator render highlight | `test_vore_render.py` | PASS |
| Player vore modal / engulf | `test_vore_ai.py`, `test_vore_engulfed.py` | PASS |
| Enhancements 2 identity / examine | `test_enhancements_2.py`, `test_examine.py` | PASS |
| Core acceptance | `test_acceptance.py` | PASS |
| Enhancements 1 | `test_enhancements_1.py` | PASS |

## Manual verification

- [x] User playtest sign-off across PRs 1–7
- [x] 17 NPC population (6 wolves, 5 knights, 6 rabbits)
- [x] Visibility-gated NPC combat, regen, and vore logs
- [x] Predator tile render (wolf on dark red; no engulfed prey glyph)
- [x] Player vore modal unchanged

## Requirement coverage (highlights)

| Requirement | Verified by |
|-------------|-------------|
| Static spawn counts | `test_enhancements_3.py` |
| Good/neutral stunned; evil defeated | `test_enhancements_3.py` |
| NPC regen intervals | `test_enhancements_3.py` |
| Evil/good/neutral AI priority | `test_enhancements_3.py` |
| NPC↔NPC swap | `test_enhancements_3.py` |
| NPC vore log-only + engulf | `test_enhancements_3.py`, `test_vore_render.py` |
| Rescue on predator defeat | `test_enhancements_3.py`, `test_vore_engulfed.py` |
| Engulfed prey hidden from AI | `test_enhancements_3.py` |
| Player vore regression | `test_vore_ai.py` |

## Spec updates

- `openspec/specs/enhancements-2/spec.md` — supersession note for E3 behaviors
- `openspec/specs/enhancements-3/spec.md` — live normative spec
- `README.md` — population, factions, NPC vore, visibility notes

## Verdict

**ENHANCEMENTS 3: ACCEPTED**