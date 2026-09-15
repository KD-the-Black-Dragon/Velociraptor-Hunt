# Archived: add-vore-mechanics

**Status:** Completed and accepted  
**Archived:** 2026-06-29  
**Sign-off:** User confirmed working in playtest

## Summary

Delivered vore mechanics v1 per `openspec/specs/vore/spec.md` across eight PRs: foundation, headless AI, modal UI, turn-order resume, engulfed state, struggle/escape, blindness rendering, and spec/acceptance wrap-up.

**Post-plan ad-hoc features** (shipped and documented in the live spec):

- Random struggle log messages on each struggle attempt
- No struggling at 0 HP while engulfed (tired message + turn pass)
- Post-escape mercy invincibility (`VoreMercy`) for one world phase
- Dark-red `#` overlay ring around `@` while engulfed

## Verification

- **Automated:** `python -m pytest tests/ -v` — 96 passed (2026-06-29)
- **Manual:** `testing-checklists.md` in this folder
- **Verdict:** VORE MECHANICS V1: ACCEPTED

## Spec merge

- Live vore spec: `openspec/specs/vore/spec.md`
- Core spec updated: modular vore boundary / AC8 (`openspec/specs/core-roguelike/spec.md`)
- README updated with vore controls and status

## Artifacts in this folder

| File | Purpose |
|------|---------|
| `proposal.md` | Change proposal |
| `design.md` | Implementation design (8-PR plan) |
| `tasks.md` | PR checklist (all complete) |
| `testing-checklists.md` | Manual vore playtest checklist |
| `acceptance-report.md` | Acceptance evidence |

## Next work

Start new folders under `openspec/changes/` for future domains (e.g. digestion, content menu, factions). v1 vore intentionally excludes digestion damage and game-over via digestion.