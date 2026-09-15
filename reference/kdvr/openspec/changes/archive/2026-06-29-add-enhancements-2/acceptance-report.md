# Acceptance Report: add-enhancements-2

**Date:** 2026-06-29  
**Scope:** `openspec/specs/enhancements-2/spec.md` (NPC identity, alignment, examine, input)

## Automated verification

```bash
python -m pytest tests/ -v
```

**Last run:** 141 passed, 0 failed (2026-06-29)

| Area | Tests | Result |
|------|-------|--------|
| Enhancements 2 identity / AI / swap | `test_enhancements_2.py` | PASS |
| Examine and quit input | `test_examine.py` | PASS |
| Core acceptance (incl. Ctrl+Q) | `test_acceptance.py` | PASS |
| Vore (naming + alignment gate) | `test_vore_ai.py`, `test_vore_*.py` | PASS |
| Enhancements 1 | `test_enhancements_1.py` | PASS |

## Manual verification

- [x] User playtest sign-off across PRs 1–7
- [x] Combat logs use species names; no generic *monster*
- [x] Examine free; engulfed **x** blocked; **Ctrl+Q** quit; **Escape** cancel examine only
- [x] Vore log possessives correct for proper names (no *"the Fang"*)

## Requirement coverage (highlights)

| Requirement | Verified by |
|-------------|-------------|
| Naming resolver | `test_enhancements_2.py` |
| Evil/good/neutral AI | `test_enhancements_2.py` |
| Player swap + skip turn | `test_enhancements_2.py` |
| Vore alignment gate | `test_enhancements_2.py`, `test_vore_ai.py` |
| Log possessives | `test_enhancements_2.py`, `test_vore_ai.py` |
| Examine mode | `test_examine.py` |
| Ctrl+Q / Escape | `test_examine.py`, `test_acceptance.py::test_ac_quit_ctrl_q` |

## Spec updates

- `openspec/specs/core-roguelike/spec.md` — quit key **Ctrl+Q** (Enhancements 2 supersedes Escape-as-quit)
- `openspec/specs/vore/spec.md` — modal quit via **Ctrl+Q** only; Escape no-op during vore modal

## Verdict

**ENHANCEMENTS 2: ACCEPTED**