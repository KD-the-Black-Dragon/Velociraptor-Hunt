# Archived: add-enhancements-2

**Status:** Completed and accepted  
**Archived:** 2026-06-29  
**Sign-off:** User confirmed working in playtest (PRs 1–7)

## Summary

Delivered NPC identity and faction layer per `openspec/specs/enhancements-2/spec.md` across seven PRs: identity foundation, combat messaging, faction AI, player swap, vore integration, examine/input, and spec acceptance.

**Notable decisions:**

- Wolves spawn **evil** with no default `ProperName` (Fang test spawn removed)
- `entity_log_name` / `entity_log_possessive` centralize message-log naming
- **Ctrl+Q** quits; **Escape** cancels examine only
- Good/neutral swap is player-initiated only; faction AI covered by tests until more NPC species ship

## Verification

- **Automated:** `python -m pytest tests/ -v` — 141 passed (2026-06-29)
- **Manual:** `testing-checklists.md` in this folder
- **Verdict:** ENHANCEMENTS 2: ACCEPTED

## Spec merge

- Live spec: `openspec/specs/enhancements-2/spec.md`
- Core spec updated: quit key (`openspec/specs/core-roguelike/spec.md`)
- Vore spec updated: modal quit binding (`openspec/specs/vore/spec.md`)
- README updated with examine, identity, and input controls

## Artifacts in this folder

| File | Purpose |
|------|---------|
| `proposal.md` | Change proposal |
| `design.md` | Implementation design (7-PR plan) |
| `tasks.md` | PR checklist (all complete) |
| `testing-checklists.md` | Consolidated manual playtest checklist |
| `testing-checklist-pr*.md` | Per-PR manual checklists (historical) |
| `acceptance-report.md` | Acceptance evidence |
| `ARCHIVE.md` | This file |

## Next work

Start new folders under `openspec/changes/` for future content (knights in spawn, shops, quests, digestion, etc.). Alignment and naming components are ready for new NPC species.