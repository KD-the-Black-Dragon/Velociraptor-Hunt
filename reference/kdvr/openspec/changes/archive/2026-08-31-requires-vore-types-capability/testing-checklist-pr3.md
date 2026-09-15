# Manual testing — PR3 (GENERIC fallback)

## How to run

`python -m src.main`

## Happy path (stock — should look unchanged)

- [ ] New Game, all three types on — normal OV/CV/AV attempts (stock `[]`; GENERIC should not appear)
- [ ] Engulf + digest — normal typed narratives
- [ ] NPC-vs-NPC vore in FOV — normal typed logs

## GENERIC trigger (optional mod / edge)

To force GENERIC without fighting prefs mid-run, use a mod entity with e.g. `"requires_vore_types": ["CV"]`, start a run with **only OV** enabled so it cannot spawn normally — then either:

- Load an older save that still has that species, **or**
- Temporarily spawn via debug if you use F2 tools

When that predator vores:

- [ ] Player modal shows basic lines like “attempts to swallow you” / “swallows you” (not OV/CV/AV stock prose)
- [ ] Digestion completion uses a basic “digests you” style line
- [ ] NPC-vs-NPC (if applicable) uses basic swallow / fail / digest lines
- [ ] Alternate CV option does **not** change GENERIC digest behavior

## Regression

- [ ] Options still only lists OV / CV / AV (no GENERIC toggle)
- [ ] Save/load still works
- [ ] PR1/PR2 behavior still holds for non-empty capability ∩ prefs

Full automated coverage: `tests/test_vore_generic_fallback_pr3.py`
