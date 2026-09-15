# Archived: add-enhancements-1

**Status:** Completed and accepted  
**Archived:** 2026-06-29  
**Sign-off:** User confirmed working in playtest

## Summary

Delivered Enhancements 1 per `openspec/specs/enhancements-1/spec.md`: wait/pass turn, silent natural regen (+1 HP / 8 turns), stunned movement/wait turn pass, Shift+TYUGHJBNM keyboard movement, and `on_player_turn_consumed` event hook.

Post-ship tweak: removed spammy *"You wait."* and *"You recover 1 HP naturally."* log lines (roguelike-style silent wait/regen).

## Verification

- **Automated:** `python -m pytest tests/ -v` — 21 passed (2026-06-29)
- **Manual:** User sign-off — all working
- **Verdict:** ENHANCEMENTS 1: ACCEPTED

## Spec merge

Live spec at `openspec/specs/enhancements-1/spec.md`. Core spec glossary and stunned-movement scenario updated with pointer to enhancements behavior.

## Artifacts in this folder

| File | Purpose |
|------|---------|
| `proposal.md` | Change proposal |
| `design.md` | Implementation design (reviewed) |
| `tasks.md` | PR checklist (all complete except deferred UX #12) |
| `acceptance-report.md` | Acceptance evidence |

## Next work

Vore mechanics shipped and archived: `openspec/changes/archive/2026-06-29-add-vore-mechanics/`. Start new folders under `openspec/changes/` for future work.